"""Complete preimage identity, alias rejection and source-bound replay generation."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_state_vectors as g  # noqa: E402
import public_state_projection as p  # noqa: E402
from check_public_state_replay import validate_success  # noqa: E402


class PublicStateProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity = p.model_identity()
        states, actions = g.candidate_path()
        cls.trace = g.package(states, actions, cls.identity)

    def test_exact_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "vectors.json"
            g.generate(output)
            self.assertEqual(output.read_bytes(), g.TARGET.read_bytes())

    def test_complete_inventory(self):
        self.assertEqual(len(p.inventory()), 64)
        module, cfg = p.replay_sources(self.trace)
        for name in p.inventory():
            self.assertIn(f"{name}' = ReplayStates[witnessIndex + 1].{name}", module)
        self.assertIn("WitnessAllowed == [][Next]_ProtocolVariables", module)
        self.assertIn("WitnessInitialOK == witnessIndex # 1 \\/ Init", module)
        self.assertNotIn("SYMMETRY", cfg)

    def test_every_variable_changes_preimage(self):
        original = self.trace["states"][0]
        for name in p.inventory():
            mutated = copy.deepcopy(original["state"])
            mutated["variables"][name] = ["bool", False]
            with self.subTest(name=name):
                self.assertNotEqual(p.state_root(mutated, self.identity), original["root"])

    def test_every_omission_rejected(self):
        for name in p.inventory():
            mutated = copy.deepcopy(self.trace["states"][0]["state"])
            del mutated["variables"][name]
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "COMPLETENESS"):
                p.state_root(mutated, self.identity)

    def test_summary_or_extra_field_rejected(self):
        for variables in [
            {"phase": ["str", "ACTIVE"]},
            {**g.initial_state(), "unknown": ["int", "0"]},
        ]:
            state = {"profile": p.PROFILE, "model": self.identity, "variables": variables}
            with self.assertRaisesRegex(ValueError, "COMPLETENESS"):
                p.state_root(state, self.identity)

    def test_opaque_relabelled_root_rejected(self):
        changed = copy.deepcopy(self.trace)
        changed["states"][0]["root"] = "sha256:" + "1" * 64
        with self.assertRaisesRegex(ValueError, "STATE_ROOT"):
            p.replay_sources(changed)

    def test_model_config_and_sources_bound(self):
        for field in ["formal_semantics_id", "configuration_sha256", "modules"]:
            changed = copy.deepcopy(self.trace)
            changed["states"][0]["state"]["model"][field] = "substitution"
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "MODEL_IDENTITY"):
                p.replay_sources(changed)

    def test_tagged_values_have_no_kind_aliases(self):
        values = [
            g.model("v1"),
            g.string("v1"),
            ["bool", True],
            g.integer(1),
            g.finite_set(),
            g.function([]),
        ]
        self.assertEqual(
            len({p.canonical_json_bytes(p.canonical_value(v)) for v in values}), len(values)
        )
        self.assertNotEqual(p.tla_value(g.model("v1")), p.tla_value(g.string("v1")))
        for value in [
            ["record", []],
            ["seq", []],
            ["unknown", "..."],
            None,
            1.0,
            ["int", 1],
            ["bool", 1],
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                p.canonical_value(value)

    def test_duplicate_or_noncanonical_set_and_function_rejected(self):
        a, b = g.integer(1), g.integer(2)
        for value in [
            ["set", [a, a]],
            ["set", [b, a]],
            ["fun", [[a, a], [a, b]]],
            ["fun", [[b, a], [a, b]]],
        ]:
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "DUPLICATE_OR_UNORDERED"),
            ):
                p.canonical_value(value)

    def test_function_codomain_and_sequence_order_not_erased(self):
        first = g.function([[g.integer(1), g.model("v1")], [g.integer(2), g.model("v2")]])
        swapped = g.function([[g.integer(1), g.model("v2")], [g.integer(2), g.model("v1")]])
        self.assertNotEqual(p.tla_value(first), p.tla_value(swapped))
        self.assertNotEqual(p.canonical_json_bytes(first), p.canonical_json_bytes(swapped))

    def test_decimal_aliases_and_unsupported_text_rejected(self):
        for number in ["-0", "+1", "01", "1.0", "1e2", "", " 1"]:
            with self.subTest(number=number), self.assertRaisesRegex(ValueError, "INTEGER"):
                p.canonical_value(["int", number])
        for value in [["str", "\n"], ["str", "я"], ["model", "TRUE"], ["model", "v1) \\/ TRUE"]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                p.canonical_value(value)

    def test_resource_bounds_reject(self):
        value = g.integer(0)
        for _ in range(p.MAX_DEPTH + 1):
            value = ["set", [value]]
        with self.assertRaisesRegex(ValueError, "VALUE_LIMIT"):
            p.canonical_value(value)
        with self.assertRaisesRegex(ValueError, "VALUE_LIMIT"):
            p.canonical_value(g.integer(0), budget=[0])
        with self.assertRaisesRegex(ValueError, "TLC_INTEGER_RANGE"):
            p.tla_value(g.integer(2**31))

    def test_action_count_and_vocabulary_rejected(self):
        for actions in [[], ["TRUE"] * 15, ["Next"] * 15]:
            changed = copy.deepcopy(self.trace)
            changed["actions"] = actions
            with self.subTest(actions=actions[:1]), self.assertRaises(ValueError):
                p.replay_sources(changed)

    def test_missing_native_durability_is_not_complete_state(self):
        changed = copy.deepcopy(self.trace)
        changed["states"][0]["state"]["variables"]["durableVotes"] = None
        with self.assertRaisesRegex(ValueError, "TAGGED_VALUE"):
            p.replay_sources(changed)

    def test_inventory_detects_model_or_projection_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "formal/tla"
            target.mkdir(parents=True)
            for name in ["DeltaReduceTypes", "DeltaReducePublicState"]:
                (target / f"{name}.tla").write_bytes((ROOT / f"formal/tla/{name}.tla").read_bytes())
            projection = target / "DeltaReducePublicState.tla"
            projection.write_text(
                projection.read_text().replace("view |-> view", "view |-> logicalTime")
            )
            with self.assertRaisesRegex(ValueError, "PROJECTION_VARIABLE_SUBSTITUTION"):
                p.inventory(root)

    def test_tlc_success_requires_exact_full_path_and_complete_transcript(self):
        output = (
            ROOT / "formal/proposals/evidence/public-state/replay/positive/tlc.txt"
        ).read_text(encoding="utf-8")
        self.assertEqual(validate_success(output, 0, 16)["distinct_states"], 16)
        for changed in [
            output.replace("16 distinct states found", "116 distinct states found"),
            output.replace("1 distinct state generated", "0 distinct states generated"),
            output.split("Finished in ")[0],
            output.replace("seed 1", "seed 2"),
            output + "\nError: omitted failure\n",
        ]:
            with self.subTest(changed=changed[-70:]), self.assertRaises(ValueError):
                validate_success(changed, 0, 16)
        with self.assertRaisesRegex(ValueError, "TLC_REPLAY_FAILED"):
            validate_success(output, 1, 16)


if __name__ == "__main__":
    unittest.main()
