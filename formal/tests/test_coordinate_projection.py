"""Concrete coordinate binding, independent vector results and guard necessity."""

import copy
import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from coordinate_projection import CoordinateError, native_schema_projection  # noqa: E402
from formal_artifacts import load_json_strict, validate_json_schema  # noqa: E402
from generate_coordinate_fixtures import matrix_contract  # noqa: E402
from native_trace_witness import NativeEvidence, n  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "coordinate_checker", ROOT / "formal/scripts/check-refinement.py"
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
FIXTURES = ROOT / "formal/fixtures/traces"


class CoordinateProjectionTests(unittest.TestCase):
    def evidence(self, name):
        path = FIXTURES / "native" / (name + ".json")
        return NativeEvidence(path, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_full_multidomain_trace_matches_independent_arithmetic(self):
        name = "native-coordinate-matrix"
        trace = load_json_strict(FIXTURES / "legal" / (name + ".json"))
        result = checker.check_trace(FIXTURES / "legal" / (name + ".json"), self.evidence(name))
        self.assertEqual(result["native_arithmetic_votes_checked"], 21)
        # q / 2 per domain rounds before mixture. Domain vectors are
        # (1,-1,2,-2,3), (0,1,-1,2,-2), (1,-1,2,-2,3).
        # Equal mixture rounds to (1,0,1,-1,1). With mu=lr=1/2 and wd=0:
        # m'=(2,-1,2,-2,2), direction=(2,0,2,-2,2), step=(1,0,1,-1,1).
        for event in trace["events"]:
            if event["action_id"] == "ACT-APPLY-VOTE":
                body = n.decode(event["arithmetic_witness"]["command_ascii"].encode())["payload"]
                self.assertEqual(body["next_model"], [19, -20, 19, -19, 19])
                self.assertEqual(body["next_optimizer"], [2, -1, 2, -2, 2])

    def test_guard_removal_admits_self_consistent_schema_substitutions(self):
        require = n.require
        for name in (
            "coordinate-public-rename",
            "coordinate-native-rename",
            "coordinate-native-offsets",
        ):
            with self.subTest(name=name):
                evidence = self.evidence(name)
                path = FIXTURES / "illegal" / (name + ".json")
                with self.assertRaises(checker.RefinementError) as caught:
                    checker.check_trace(path, evidence)
                self.assertEqual(caught.exception.reason, "NATIVE_COORDINATE_SCHEMA_BINDING")
                # Deliberate in-process removal of this production Python guard.
                # All remaining arithmetic, IDs, vote quorums and hashes still pass.
                with patch.object(
                    n,
                    "require",
                    side_effect=lambda ok, reason: (
                        None
                        if reason == "NATIVE_COORDINATE_SCHEMA_BINDING"
                        else require(ok, reason)
                    ),
                ):
                    self.assertEqual(checker.check_trace(path, evidence)["status"], "PASS")

    def test_unequal_layouts_and_boundary_coordinate_count(self):
        for domains, lengths in ((1, (1,)), (2, (3, 1, 2)), (4, (2, 5)), (1, (1, 4095))):
            with self.subTest(domains=domains, lengths=lengths):
                projection = native_schema_projection(matrix_contract(domains, lengths))
                self.assertEqual(len(projection["coordinates"]), sum(lengths))
                for index, shard in enumerate(projection["shards"]):
                    self.assertEqual(
                        (shard["offset"], shard["length"]), (sum(lengths[:index]), lengths[index])
                    )

    def test_coordinate_bound_is_not_silently_widened(self):
        with self.assertRaisesRegex(CoordinateError, "COORDINATE_BOUND"):
            native_schema_projection(matrix_contract(1, (4097,)))

    def test_boolean_range_is_not_an_integer_coordinate(self):
        contract = matrix_contract()
        contract["parameter_schema"]["ranges"][0]["offset"] = False
        with self.assertRaisesRegex(CoordinateError, "COORDINATE_RANGE_BOUNDS"):
            native_schema_projection(contract)
        schema = load_json_strict(ROOT / "formal/schemas/formal-trace.schema.json")
        with self.assertRaises(ValueError):
            validate_json_schema(
                contract, {"$ref": "#/$defs/roundContract", "$defs": schema["$defs"]}
            )

    def test_coordinate_fields_are_mandatory(self):
        schema = load_json_strict(ROOT / "formal/schemas/formal-trace.schema.json")
        for field in ("coordinates", "ranges"):
            contract = matrix_contract()
            del contract["parameter_schema"][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_json_schema(
                    contract, {"$ref": "#/$defs/roundContract", "$defs": schema["$defs"]}
                )

    def test_projection_does_not_mutate_frozen_contract(self):
        contract = matrix_contract()
        before = copy.deepcopy(contract)
        native_schema_projection(contract)
        self.assertEqual(before, contract)


if __name__ == "__main__":
    unittest.main()
