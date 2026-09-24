"""Adversarial offline journal tests; no assertion of physical durability."""

import copy
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import load_json_strict, write_canonical_json  # noqa: E402
from native_durability_witness import check_durability_trace, observation_id  # noqa: E402
from native_trace_witness import NativeEvidence, n  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "durable_checker", ROOT / "formal/scripts/check-refinement.py"
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
FIXTURES = ROOT / "formal/fixtures/traces"


class NativeDurabilityTests(unittest.TestCase):
    def load(self, name="durability-after-current", category="legal"):
        path = FIXTURES / "native" / (name + ".json")
        return load_json_strict(FIXTURES / category / (name + ".json")), NativeEvidence(
            path, hashlib.sha256(path.read_bytes()).hexdigest()
        )

    def test_recovery_current_and_conflict_do_not_change_receipt(self):
        trace, evidence = self.load()
        result = checker.check_trace(FIXTURES / "legal/durability-after-current.json", evidence)
        self.assertEqual(
            result["native_durability_observations_checked"],
            {
                "persisted": 9,
                "retried": 5,
                "conflicts": 1,
                "recovered": 1,
                "persisted_unexposed": 0,
                "unacknowledged": 0,
            },
        )
        first = next(e for e in trace["events"] if e["action_id"] == "ACT-PARAM-VOTE")
        receipt = evidence.operations[first["durability_witness"]]["receipt_ascii"]
        # Independent facts: 4 earlier votes, PARAMETER allocated sequence 5;
        # the journal later reaches 8, but the old parameter receipt stays at 5.
        self.assertEqual(n.decode(receipt.encode())["sequence"], 5)
        retries = [
            e
            for e in trace["events"]
            if e["action_id"] == "ACT-PARAM-VOTE" and e["outcome"] == "NO_OP"
        ]
        for event in retries:
            observation = evidence.operations[event["durability_witness"]]
            self.assertEqual(observation["sequence_after"], 8)
            self.assertEqual(event["durable_sequence"], 5)
            self.assertEqual(observation["receipt_ascii"], receipt)
            self.assertEqual(observation["journal_before"], observation["journal_after"])

    def test_retry_before_current_advance(self):
        _, evidence = self.load("durability-retry-recovery")
        result = checker.check_trace(FIXTURES / "legal/durability-retry-recovery.json", evidence)
        self.assertEqual(
            result["native_durability_observations_checked"],
            {
                "persisted": 1,
                "retried": 3,
                "conflicts": 1,
                "recovered": 1,
                "persisted_unexposed": 0,
                "unacknowledged": 0,
            },
        )

    def test_observation_cannot_be_replaced_under_old_id(self):
        bundle = load_json_strict(FIXTURES / "native/durability-after-current.json")
        next(iter(bundle["operations"].values()))["sequence_after"] = 900
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native.json"
            write_canonical_json(path, bundle)
            with self.assertRaisesRegex(n.BindingError, "NATIVE_OBSERVATION_ID"):
                NativeEvidence(path, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_observation_required_even_for_noop(self):
        trace, evidence = self.load()
        trace["events"][-1]["durability_witness"] = None
        with self.assertRaisesRegex(n.BindingError, "DURABILITY_WITNESS_REQUIRED"):
            check_durability_trace(trace, evidence)

    def test_public_claim_does_not_override_separately_pinned_observation(self):
        trace, evidence = self.load()
        trace["events"][-1]["request_id"] = "rewritten-request"
        with self.assertRaisesRegex(n.BindingError, "DURABILITY_EVENT_BINDING"):
            check_durability_trace(trace, evidence)

    def test_removed_guards_admit_rehashed_adversarial_observations(self):
        require = n.require
        for name, guard in (
            ("durability-retry-receipt", "DURABILITY_RETRY_BYTES"),
            ("durability-expose-before-barrier", "DURABILITY_EXPOSE_ORDER"),
            ("durability-conflict-append", "DURABILITY_JOURNAL_CHANGED"),
        ):
            with self.subTest(name=name):
                _, evidence = self.load(name, "illegal")
                path = FIXTURES / "illegal" / (name + ".json")
                with self.assertRaises(checker.RefinementError) as caught:
                    checker.check_trace(path, evidence)
                self.assertEqual(caught.exception.reason, guard)
                # Intentional Python guard removal, not a TLA production mutant.
                with patch.object(
                    n,
                    "require",
                    side_effect=lambda ok, reason, disabled=guard: (
                        None if reason == disabled else require(ok, reason)
                    ),
                ):
                    self.assertEqual(checker.check_trace(path, evidence)["status"], "PASS")

    def test_boolean_sequence_is_not_integer(self):
        trace, evidence = self.load()
        event = next(e for e in trace["events"] if e["action_id"] == "ACT-PARAM-VOTE")
        observation = copy.deepcopy(evidence.operations[event["durability_witness"]])
        observation["sequence_before"] = True
        identity = observation_id(observation)
        evidence.operations[identity] = observation
        event["durability_witness"] = identity
        with self.assertRaisesRegex(n.BindingError, "DURABILITY_PRIOR_JOURNAL"):
            check_durability_trace(trace, evidence)

    def test_same_vote_cannot_consume_a_second_sequence(self):
        trace, evidence = self.load()
        event = copy.deepcopy(
            next(e for e in trace["events"] if e["action_id"] == "ACT-CONFIG-VOTE")
        )
        trace["events"] = [event, copy.deepcopy(event)]
        trace["events"][1]["durable_sequence"] = 2
        with self.assertRaisesRegex(n.BindingError, "DURABILITY_DUPLICATE_ENVELOPE"):
            check_durability_trace(trace, evidence)

    def test_checker_does_not_mutate_observations(self):
        trace, evidence = self.load()
        before = copy.deepcopy((trace, evidence.operations))
        check_durability_trace(trace, evidence)
        self.assertEqual((trace, evidence.operations), before)


if __name__ == "__main__":
    unittest.main()
