"""Unknown append outcomes are neither durable absence nor permission to retry."""

import copy
import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import load_json_strict  # noqa: E402
from native_durability_witness import check_durability_trace, n  # noqa: E402
from native_trace_witness import NativeEvidence  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "uncertain_checker", ROOT / "formal/scripts/check-refinement.py"
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
FIXTURES = ROOT / "formal/fixtures/traces"


class UncertainWitnessTests(unittest.TestCase):
    def load(self, name, category="legal"):
        path = FIXTURES / "native" / (name + ".json")
        return FIXTURES / category / (name + ".json"), NativeEvidence(
            path, hashlib.sha256(path.read_bytes()).hexdigest()
        )

    def test_rejection_does_not_allocate_or_poison_first_admission(self):
        for kind, action, sequence in (
            ("parameter", "ACT-PARAM-VOTE", 5),
            ("apply", "ACT-APPLY-VOTE", 8),
        ):
            with self.subTest(kind=kind):
                path, evidence = self.load(f"uncertain-{kind}-rejected")
                counts = checker.check_trace(path, evidence)[
                    "native_durability_observations_checked"
                ]
                self.assertEqual(counts["admission_rejected"], 1)
                self.assertEqual(counts["uncertain"], 0)
                votes = [e for e in load_json_strict(path)["events"] if e["action_id"] == action]
                first, accepted = votes[:2]
                self.assertEqual(first["durable_sequence"], sequence - 1)
                self.assertEqual(accepted["durable_sequence"], sequence)
                rejected = evidence.operations[first["durability_witness"]]
                self.assertIsNone(rejected["receipt_ascii"])
                self.assertIsNone(rejected["effect_ascii"])
                self.assertEqual(rejected["journal_before"], rejected["journal_after"])
                self.assertEqual(rejected["sequence_before"], rejected["sequence_after"])

    def test_only_verified_absence_permits_fresh_allocation(self):
        for kind in ("parameter", "apply"):
            for mode in ("append-absent", "barrier-absent"):
                with self.subTest(kind=kind, mode=mode):
                    path, evidence = self.load(f"uncertain-{kind}-{mode}")
                    counts = checker.check_trace(path, evidence)[
                        "native_durability_observations_checked"
                    ]
                    self.assertEqual(counts["uncertain"], 1)
                    self.assertEqual(counts["absence_confirmed"], 1)
                    self.assertEqual(counts["unresolved"], 0)
                    self.assertEqual(counts["retried"], 0)
                    events = load_json_strict(path)["events"]
                    first = next(
                        e
                        for e in events
                        if e["action_id"].endswith("-VOTE") and e["outcome"] == "FAULT"
                    )
                    initial = evidence.operations[first["durability_witness"]]
                    self.assertIsNone(first["durable_sequence"])
                    self.assertIsNone(initial["sequence_after"])
                    self.assertIsNone(initial["journal_after"])
                    scan = next(e for e in events if e["action_id"] == "ACT-JOURNAL-RECOVER")
                    observed = evidence.operations[scan["durability_witness"]]
                    self.assertEqual(observed["journal_after"], initial["journal_before"])
                    self.assertEqual(observed["sequence_after"], initial["sequence_before"])

    def test_incomplete_and_blocked_prefixes_remain_explicitly_unresolved(self):
        for kind in ("parameter", "apply"):
            for mode in ("torn", "ambiguous", "incomplete"):
                with self.subTest(kind=kind, mode=mode):
                    path, evidence = self.load(f"uncertain-{kind}-{mode}")
                    result = checker.check_trace(path, evidence)
                    counts = result["native_durability_observations_checked"]
                    self.assertEqual(result["terminal_outcome"], "IN_PROGRESS")
                    self.assertEqual(counts["unresolved"], 1)
                    self.assertEqual(counts["absence_confirmed"], 0)
                    self.assertEqual(counts["blocked_scans"], int(mode != "incomplete"))

    def test_removed_guards_admit_false_rejection_absence_and_readiness(self):
        require = n.require
        for name, guard in (
            ("valid-command-rejected", "NATIVE_REJECTION_NOT_JUSTIFIED"),
            ("unknown-claims-prefix", "DURABILITY_UNKNOWN_ASSERTS_JOURNAL"),
            ("blocked-becomes-ready", "DURABILITY_BLOCKED_SCAN_UNRESOLVED"),
        ):
            with self.subTest(name=name):
                path, evidence = self.load("uncertain-" + name, "illegal")
                with self.assertRaises(checker.RefinementError) as caught:
                    checker.check_trace(path, evidence)
                self.assertEqual(caught.exception.reason, guard)
                with patch.object(
                    n,
                    "require",
                    side_effect=lambda ok, reason, disabled=guard: (
                        None if reason == disabled else require(ok, reason)
                    ),
                ):
                    self.assertEqual(checker.check_trace(path, evidence)["status"], "PASS")

    def test_blocked_owner_cannot_take_an_unrelated_operation(self):
        path, evidence = self.load("uncertain-apply-torn")
        trace = load_json_strict(path)
        event = copy.deepcopy(trace["events"][-1])
        event["action_id"] = "ACT-CONFIG-VOTE"
        event["outcome"] = "NO_OP"
        trace["events"].append(event)
        with self.assertRaisesRegex(n.BindingError, "DURABILITY_UNRESOLVED_OPERATION"):
            check_durability_trace(trace, evidence)

    def test_observation_and_anchor_are_not_mutated(self):
        path, evidence = self.load("uncertain-apply-barrier-absent")
        before = copy.deepcopy((evidence.operations, evidence.snapshots))
        checker.check_trace(path, evidence)
        self.assertEqual((evidence.operations, evidence.snapshots), before)


if __name__ == "__main__":
    unittest.main()
