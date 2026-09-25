"""Pinned graph inputs, full action correspondence and lossless evidence storage."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import derive_public_arithmetic_inputs as d  # noqa: E402
import generate_public_arithmetic_vectors as g  # noqa: E402
import generate_public_state_vectors as basic  # noqa: E402
import public_state_projection as p  # noqa: E402
from public_state_storage import pack, unpack  # noqa: E402


class PublicArithmeticProjectionTests(unittest.TestCase):
    def test_checked_inputs_bind_each_pinned_coordinate(self):
        binding = d.derive()
        self.assertEqual([b["numerators"] for b in binding["parameters"]], [[1], [-2]])
        self.assertEqual(binding["apply"]["next_model"], [19, -19])
        self.assertEqual(binding["apply"]["next_optimizer"], [2, -2])
        q = g.field(binding["inputs"], "q")[1][0][1]
        self.assertEqual([v for _, v in q[1]], [basic.integer(1), basic.integer(-2)])
        self.assertEqual(binding["native_accumulator_bits"], 64)
        self.assertEqual(binding["tlc_signed_limit"], 127)

    def test_module_config_and_binding_reproduce(self):
        with tempfile.TemporaryDirectory() as directory:
            target, module, config = [
                Path(directory) / name for name in ["inputs.json", "inputs.tla", "inputs.cfg"]
            ]
            d.generate(target=target, module=module, config=config)
            self.assertEqual(target.read_bytes(), d.TARGET.read_bytes())
            self.assertEqual(
                module.read_bytes(), (ROOT / "formal/tla/DeltaReduceFixtureInputs.tla").read_bytes()
            )
            self.assertEqual(
                config.read_bytes(),
                (ROOT / "formal/proposals/public-arithmetic-replay.cfg").read_bytes(),
            )

    def test_substituted_bundle_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target, module, config = [
                Path(directory) / name
                for name in ["source.json", "inputs.json", "inputs.tla", "inputs.cfg"]
            ]
            source.write_bytes(d.SOURCE.read_bytes().replace(b"[20,-20]", b"[21,-20]"))
            self.assertTrue(source.read_bytes() != d.SOURCE.read_bytes())
            with self.assertRaisesRegex(ValueError, "PINNED_NATIVE_SOURCE"):
                d.generate(source, target, module, config)
            self.assertFalse(any(path.exists() for path in [target, module, config]))

    def test_original_sequences_and_extra_production_steps(self):
        states, actions, mapping = g.candidate_path(d.derive())
        self.assertEqual(len(states), 132)
        self.assertEqual(len(mapping), 36)
        for actor in ["validator-1", "validator-2", "validator-3"]:
            votes = [
                e for e in mapping if e["actor_id"] == actor and e["durable_sequence"] is not None
            ]
            self.assertEqual([e["durable_sequence"] for e in votes], list(range(1, 9)))
            arithmetic = [
                e["durable_sequence"]
                for e in votes
                if e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
            ]
            self.assertEqual(arithmetic, [5, 6, 8])
        self.assertEqual(actions.count("SendVoteEnvelopeAction"), 24)
        self.assertEqual(actions.count("DeliverVoteEnvelopeAction"), 24)
        self.assertEqual(actions.count("AdvanceLogicalTime"), 35)
        self.assertEqual(states[-1]["phase"], basic.string("APPLIED"))
        self.assertEqual(states[-1]["currentCheckpoint"], basic.model("next1"))
        for e in mapping:
            self.assertEqual(
                int(states[e["prior_state_index"]]["logicalTime"][1]), e["legacy_event_index"]
            )

    def test_pooled_storage_preserves_full_preimages(self):
        states, actions = basic.candidate_path()
        trace = basic.package(states, actions)
        self.assertEqual(unpack(pack(trace)), trace)
        self.assertEqual(p.replay_sources(unpack(pack(trace))), p.replay_sources(trace))

    def test_pooled_storage_substitution_and_omission_rejected(self):
        states, actions = basic.candidate_path()
        stored = pack(basic.package(states, actions))
        altered = copy.deepcopy(stored)
        altered["pool"][next(iter(altered["pool"]))] = basic.string("substitution")
        with self.assertRaisesRegex(ValueError, "STORAGE_FIELD_HASH"):
            unpack(altered)
        missing = copy.deepcopy(stored)
        del missing["pool"][next(iter(missing["pool"]))]
        with self.assertRaisesRegex(ValueError, "STORAGE_MISSING_FIELD"):
            unpack(missing)
        partial = copy.deepcopy(stored)
        del partial["trace"]["states"][0]["state"]["variables"]["durableVotes"]
        with self.assertRaisesRegex(ValueError, "STATE_COMPLETENESS"):
            unpack(partial)

    def test_unused_storage_values_are_not_hidden_state(self):
        states, actions = basic.candidate_path()
        stored = pack(basic.package(states, actions))
        extra = pack(basic.package([{**states[0], "phase": basic.string("unused")}], []))
        stored["pool"].update(extra["pool"])
        with self.assertRaisesRegex(ValueError, "STORAGE_UNUSED_FIELD"):
            unpack(stored)

    def test_configuration_selection_cannot_come_from_unchecked_trace(self):
        self.assertNotEqual(p.model_identity(), p.model_identity("native-arithmetic"))
        with self.assertRaisesRegex(ValueError, "CONFIGURATION_PROFILE"):
            p.configuration_sources("arbitrary.cfg")


if __name__ == "__main__":
    unittest.main()
