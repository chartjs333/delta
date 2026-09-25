"""Complete, rehashed state/metadata substitutions must fail the native binding."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_native_projection as g  # noqa: E402
import public_native_projection as p  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from generate_public_state_vectors import finite_set as ss  # noqa: E402
from generate_public_state_vectors import integer as ii  # noqa: E402
from generate_public_state_vectors import model as m  # noqa: E402
from generate_public_state_vectors import replace_key  # noqa: E402
from generate_public_state_vectors import string as s  # noqa: E402
from public_state_projection import state_root  # noqa: E402
from public_state_storage import unpack  # noqa: E402


class PublicNativeProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = p.PinnedFixtureSources()
        cls.vectors = load_json_strict(g.VECTORS)
        cls.trace = unpack(cls.vectors["positive"])
        cls.projected = load_json_strict(g.TARGET)

    def pair(self, index=0):
        entry = self.projected["bindings"][index]
        before, after = entry["prior_state_index"], entry["next_state_index"]
        return (
            entry["value"]["source_event_index"],
            copy.deepcopy(self.trace["states"][before]),
            copy.deepcopy(self.trace["states"][after]),
            self.trace["actions"][before],
        )

    def rehash(self, observation):
        observation["root"] = state_root(observation["state"], self.sources.identity)

    def changed_pair(self, name, value, index=0):
        event, before, after, action = self.pair(index)
        for observation in (before, after):
            observation["state"]["variables"][name] = value
            self.rehash(observation)
        return event, before, after, action

    def replace_body(self, change, index=0):
        event, before, after, action = self.pair(index)
        prior_votes = p.items(before["state"]["variables"]["durableVotes"])
        added = next(
            v for v in p.items(after["state"]["variables"]["durableVotes"]) if v not in prior_votes
        )
        body = p.field(added, "body")
        changed = change(body)

        def replace(value):
            if value == body:
                return changed
            if isinstance(value, list):
                return [replace(v) for v in value]
            if isinstance(value, dict):
                return {k: replace(v) for k, v in value.items()}
            return value

        before, after = replace(before), replace(after)

        # Replacing a body changes set ordering as well as identities.
        def order(value):
            if not isinstance(value, list):
                return value
            if len(value) == 2 and value[0] == "set":
                return ss(*(order(v) for v in value[1]))
            return [order(v) for v in value]

        for observation in (before, after):
            observation["state"]["variables"] = {
                k: order(v) for k, v in observation["state"]["variables"].items()
            }
            self.rehash(observation)
        return event, before, after, action

    def test_exact_generation_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "generated.json"
            result = g.generate(target)
            self.assertEqual(target.read_bytes(), g.TARGET.read_bytes())
        self.assertEqual(len(result["bindings"]), 9)
        self.assertFalse(result["native_export_authenticated"])
        for row in result["bindings"]:
            value = row["value"]
            event = self.sources.trace["events"][value["source_event_index"]]
            op = self.sources.native.operations[event["durability_witness"]]
            self.assertEqual(value["command_ascii"], event["arithmetic_witness"]["command_ascii"])
            self.assertEqual(value["receipt_ascii"], op["receipt_ascii"])
            self.assertEqual(value["effect_ascii"], op["effect_ascii"])
            self.assertEqual(value["sequence"], event["durable_sequence"])
            self.assertEqual(row["id"], p.projection_id(value))
            self.assertNotEqual(value["complete_prior_root"], event["prior_state_root"])

    def test_legacy_snapshot_cannot_be_loaded_as_v2(self):
        event, before, after, action = self.pair()
        legacy = self.sources.native.snapshots[
            self.sources.trace["events"][event]["arithmetic_witness"]["snapshot_id"]
        ]
        with self.assertRaisesRegex(ValueError, "PROJECTION_VERSION"):
            p.verify_projection(self.sources, legacy, event, before, after, action)

    def test_old_opaque_root_cannot_name_complete_state(self):
        event, before, after, action = self.pair()
        before["root"] = self.sources.trace["events"][event]["prior_state_root"]
        with self.assertRaisesRegex(ValueError, "STATE_ROOT"):
            self.sources.bind_first(event, before, after, action)

    def test_rehashed_wrong_current_and_recovery_reject(self):
        recovery = self.trace["states"][self.projected["bindings"][0]["prior_state_index"]][
            "state"
        ]["variables"]["recoveryState"]
        for name, value, error in [
            ("currentCheckpoint", m("next1"), "PROJECTION_CURRENT"),
            ("recoveryState", replace_key(recovery, m("v1"), s("RECOVERING")), "PROJECTION_READY"),
            ("phase", s("APPLIED"), "PROJECTION_PHASE"),
        ]:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, error):
                self.sources.bind_first(*self.changed_pair(name, value))

    def test_rehashed_clock_and_view_reject(self):
        for name in ["logicalTime", "view"]:
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "PROJECTION_TIME_VIEW"),
            ):
                self.sources.bind_first(*self.changed_pair(name, ii(99)))

    def test_rehashed_false_sequence_reject(self):
        seq = self.pair()[1]["state"]["variables"]["durableSequence"]
        with self.assertRaisesRegex(ValueError, "PROJECTION_SEQUENCE"):
            self.sources.bind_first(
                *self.changed_pair("durableSequence", replace_key(seq, m("v1"), ii(3)))
            )

    def test_wrong_actor_event_and_action_reject(self):
        event, before, after, action = self.pair()
        with self.assertRaisesRegex(ValueError, "PROJECTION_TIME_VIEW"):
            self.sources.bind_first(event + 1, before, after, action)
        with self.assertRaisesRegex(ValueError, "PROJECTION_ACTION"):
            self.sources.bind_first(event, before, after, "VoteApplyAction")

    def test_rehashed_hidden_effect_reject(self):
        event, before, after, action = self.pair()
        after["state"]["variables"]["logicalTime"] = ii(19)
        self.rehash(after)
        with self.assertRaisesRegex(ValueError, "PROJECTION_VOTE_EFFECT_FIELDS"):
            self.sources.bind_first(event, before, after, action)

    def test_rehashed_parameter_result_reject(self):
        with self.assertRaisesRegex(ValueError, "PROJECTION_PARAMETER_NATIVE_BODY"):
            self.sources.bind_first(
                *self.replace_body(lambda b: replace_key(b, s("value"), ii(-2)))
            )

    def test_rehashed_whole_parent_identity_reject(self):
        for name, key, value in [
            ("isc", "canonicalRoot", ss()),
            ("ec", "normEvidence", m("profile1")),
            ("apc", "coefficientProfile", m("profile1")),
        ]:

            def wrong(body, name=name, key=key, value=value):
                parent = replace_key(p.field(body, name), s(key), value)
                return replace_key(body, s(name), parent)

            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "PROJECTION_" + name.upper() + "_BODY"),
            ):
                self.sources.bind_first(*self.replace_body(wrong))

    def test_rehashed_apply_optimizer_reject(self):
        def wrong(body):
            optimizer = p.field(body, "nextOptimizerHash")
            values = replace_key(p.field(optimizer, "values"), m("shard1"), ii(3))
            return replace_key(
                body, s("nextOptimizerHash"), replace_key(optimizer, s("values"), values)
            )

        with self.assertRaisesRegex(ValueError, "PROJECTION_APPLY_NATIVE_BODY"):
            self.sources.bind_first(*self.replace_body(wrong, 6))

    def test_rehashed_bound_model_optimizer_and_inputs_reject(self):
        for name in ["model", "optimizer", "inputs"]:

            def wrong(body, name=name):
                authority = p.field(body, "authority")
                value = p.field(authority, name)
                if name == "inputs":
                    value = replace_key(value, s("lrN"), ii(0))
                else:
                    values = replace_key(p.field(value, "values"), m("shard1"), ii(10))
                    value = replace_key(value, s("values"), values)
                return replace_key(body, s("authority"), replace_key(authority, s(name), value))

            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "PROJECTION_PARAMETER_NATIVE_BODY"),
            ):
                self.sources.bind_first(*self.replace_body(wrong))

    def test_missing_qc_and_undelivered_signer_reject(self):
        with self.assertRaisesRegex(ValueError, "PROJECTION_QC"):
            self.sources.bind_first(*self.changed_pair("aggregationPlanCertificates", ss()))
        prior = self.pair()[1]["state"]["variables"]
        remaining = [
            v
            for v in p.items(prior["receivedVotes"])
            if not (p.field(v, "kind") == s("APC") and p.field(v, "validator") == m("v3"))
        ]
        with self.assertRaisesRegex(ValueError, "PROJECTION_UNDELIVERED_QC"):
            self.sources.bind_first(*self.changed_pair("receivedVotes", ss(*remaining)))

    def test_rehashed_claim_metadata_does_not_override_derivation(self):
        event, before, after, action = self.pair()
        for name, value in [
            ("command_ascii", "{}"),
            ("sequence", 500),
            ("provenance", "AUTHENTICATED"),
            ("receipt_ascii", "{}"),
        ]:
            changed = copy.deepcopy(self.projected["bindings"][0]["value"])
            changed[name] = value
            self.assertNotEqual(p.projection_id(changed), self.projected["bindings"][0]["id"])
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "PROJECTION_DERIVED_FIELDS"),
            ):
                p.verify_projection(self.sources, changed, event, before, after, action)

    def test_incomplete_state_is_not_a_complete_observation(self):
        event, before, after, action = self.pair()
        before["state"]["variables"]["durableVotes"] = None
        with self.assertRaisesRegex(ValueError, "TAGGED_VALUE"):
            self.sources.bind_first(event, before, after, action)

    def test_source_registry_does_not_take_hashes_from_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "trace.json"
            source.write_bytes(p.PUBLIC.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "PROJECTION_PUBLIC_PIN"):
                p.PinnedFixtureSources(public=source)


if __name__ == "__main__":
    unittest.main()
