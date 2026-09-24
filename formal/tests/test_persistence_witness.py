"""Persisted-but-unexposed votes cannot acquire quorum power before recovery/replay."""

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
from native_durability_witness import check_durability_trace, n, observation_id  # noqa: E402
from native_trace_witness import NativeEvidence  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "persistence_checker", ROOT / "formal/scripts/check-refinement.py"
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
FIXTURES = ROOT / "formal/fixtures/traces"


class PersistenceWitnessTests(unittest.TestCase):
    def load(self, name, category="legal"):
        path = FIXTURES / "native" / (name + ".json")
        return FIXTURES / category / (name + ".json"), NativeEvidence(
            path, hashlib.sha256(path.read_bytes()).hexdigest()
        )

    def test_complete_surviving_records_replay_without_another_append(self):
        for kind, action, sequence in (
            ("parameter", "ACT-PARAM-VOTE", 5),
            ("apply", "ACT-APPLY-VOTE", 8),
        ):
            for cut in ("durable", "committed", "append-survived", "barrier-failed-survived"):
                with self.subTest(kind=kind, cut=cut):
                    path, evidence = self.load(f"cut-{kind}-{cut}")
                    result = checker.check_trace(path, evidence)
                    counts = result["native_durability_observations_checked"]
                    self.assertEqual(counts["persisted_unexposed"], 1)
                    self.assertEqual(counts["unacknowledged"], int(cut.endswith("survived")))
                    self.assertEqual(counts["recovered"], 1)
                    self.assertEqual(counts["retried"], 1)
                    events = load_json_strict(path)["events"]
                    first = next(e for e in events if e["action_id"] == action)
                    replay = next(e for e in events if e["outcome"] == "NO_OP")
                    before = evidence.operations[first["durability_witness"]]
                    after = evidence.operations[replay["durability_witness"]]
                    self.assertIsNone(before["receipt_ascii"])
                    self.assertIsNone(before["effect_ascii"])
                    receipt = n.decode(after["receipt_ascii"].encode("ascii"))
                    self.assertEqual(receipt["sequence"], sequence)
                    self.assertEqual(after["sequence_before"], sequence)
                    self.assertEqual(after["sequence_after"], sequence)
                    self.assertEqual(before["journal_after"], after["journal_after"])
                    self.assertEqual(events[-1]["action_id"], action.replace("VOTE", "FINALIZE"))

    def test_unexposed_record_must_not_count_toward_qc(self):
        path, evidence = self.load("cut-qc-before-exposure", "illegal")
        with self.assertRaises(checker.RefinementError) as caught:
            checker.check_trace(path, evidence)
        self.assertEqual(caught.exception.reason, "QC_QUORUM_MISSING")
        # Intentional removal of the production Python visibility guard. The
        # same self-consistent arithmetic/journal witness then wrongly passes.
        with patch.object(checker, "vote_exposed", return_value=True):
            self.assertEqual(checker.check_trace(path, evidence)["status"], "PASS")

    def test_removed_guards_admit_early_output_and_unverified_presence(self):
        require = n.require
        for name, guard in (
            ("cut-early-receipt", "DURABILITY_PERSISTED_BYTES"),
            ("cut-unacknowledged-unverified", "DURABILITY_UNACKNOWLEDGED_UNVERIFIED"),
        ):
            with self.subTest(name=name):
                path, evidence = self.load(name, "illegal")
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

    def test_incomplete_acknowledged_prefix_is_not_assumed_absent(self):
        path, evidence = self.load("cut-parameter-durable")
        trace = load_json_strict(path)
        index = next(i for i, e in enumerate(trace["events"]) if e["action_id"] == "ACT-PARAM-VOTE")
        trace["events"] = trace["events"][: index + 1]
        counts = check_durability_trace(trace, evidence)
        self.assertEqual(counts["persisted"], 1)
        self.assertEqual(counts["persisted_unexposed"], 1)
        self.assertEqual(counts["retried"], 0)

    def test_no_observation_mutation(self):
        path, evidence = self.load("cut-apply-barrier-failed-survived")
        before = copy.deepcopy(evidence.operations)
        checker.check_trace(path, evidence)
        self.assertEqual(evidence.operations, before)

    def test_malformed_observation_is_rejected_without_projection_crash(self):
        path, evidence = self.load("cut-parameter-durable")
        trace = load_json_strict(path)
        first = next(e for e in trace["events"] if e["action_id"] == "ACT-PARAM-VOTE")
        identity = observation_id([])
        evidence.operations[identity] = []
        first["durability_witness"] = identity
        self.assertTrue(checker.vote_exposed(first, evidence))
        with self.assertRaises(n.BindingError):
            check_durability_trace(trace, evidence)


if __name__ == "__main__":
    unittest.main()
