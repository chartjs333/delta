"""Behavior regressions for QC context and validator recovery admission."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import load_json_strict, write_canonical_json  # noqa: E402
from generate_trace_fixtures import (  # noqa: E402
    ROUND_CONFIG_HASH,
    cid,
    make_event,
    qc_events,
    trace,
)
from native_trace_fixture import attach_fixture_witnesses  # noqa: E402
from native_trace_witness import NativeEvidence  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "check_refinement", ROOT / "formal" / "scripts" / "check-refinement.py"
)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

NON_TRANSITION_OUTCOMES = ("REJECTED", "STUTTER", "NO_OP", "BLOCKED", "FAULT")


class RefinementAdmissionTests(unittest.TestCase):
    def check(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            document = trace("TRACE-ADMISSION-REGRESSION", events)
            evidence = attach_fixture_witnesses(document)
            native_path = Path(directory) / "native.json"
            write_canonical_json(native_path, evidence)
            native = NativeEvidence(
                native_path, hashlib.sha256(native_path.read_bytes()).hexdigest()
            )
            write_canonical_json(path, document)
            return checker.check_trace(path, native)

    def reject(self, events: list[dict[str, Any]], reason: str) -> None:
        with self.assertRaises(checker.RefinementError) as caught:
            self.check(events)
        self.assertEqual(caught.exception.reason, reason)

    def config(self) -> list[dict[str, Any]]:
        return qc_events(
            "ACT-CONFIG-VOTE",
            "ACT-CONFIG-FINALIZE",
            "admission",
            body_hash=ROUND_CONFIG_HASH,
        )[0]

    def crash(self) -> dict[str, Any]:
        return make_event("ACT-CRASH", outcome="FAULT", error="CRASH_AFTER_PERSIST")

    def test_every_qc_rejects_vote_from_another_height_or_epoch(self) -> None:
        for final_action, vote_action in checker.FINALIZE_TO_VOTE.items():
            fixture = {
                "ACT-VIEW-FINALIZE": "view-change",
                "ACT-ABORT-FINALIZE": "certified-abort",
            }.get(final_action, "normal-apply")
            base = load_json_strict(
                ROOT / "formal" / "fixtures" / "traces" / "legal" / f"{fixture}.json"
            )["events"]
            end = next(i for i, event in enumerate(base) if event["action_id"] == final_action)
            base = base[: end + 1]
            self.assertEqual(self.check(copy.deepcopy(base))["status"], "PASS")
            for field, value in (("height", 2), ("validator_epoch", "epoch-2")):
                with self.subTest(action=final_action, field=field):
                    events = copy.deepcopy(base)
                    vote = next(event for event in events if event["action_id"] == vote_action)
                    vote[field] = value
                    self.reject(events, "QC_QUORUM_MISSING")

    def test_finalizer_cannot_relabel_existing_quorum_height_or_epoch(self) -> None:
        for field, value in (("height", 2), ("validator_epoch", "epoch-2")):
            with self.subTest(field=field):
                events = self.config()
                events[-1][field] = value
                self.reject(events, "QC_QUORUM_MISSING")

    def test_matching_context_can_finalize_in_later_leader_view(self) -> None:
        # ConfigContext has height/epoch, not view. View changes preserve votes.
        events = self.config()
        events[-1]["view"] = 1
        self.assertEqual(self.check(events)["status"], "PASS")

    def test_duplicate_actor_does_not_make_quorum(self) -> None:
        events = self.config()
        events[2] = copy.deepcopy(events[1])
        self.reject(events, "QC_QUORUM_MISSING")

    def test_rejected_vote_does_not_make_quorum(self) -> None:
        events = self.config()
        events[2]["outcome"] = "REJECTED"
        self.reject(events, "QC_QUORUM_MISSING")

    def test_crashed_validator_cannot_vote(self) -> None:
        self.reject([self.crash(), self.config()[0]], "VOTE_BEFORE_JOURNAL_RECOVERY")

    def test_unsuccessful_recovery_never_enables_vote(self) -> None:
        for outcome in NON_TRANSITION_OUTCOMES:
            with self.subTest(outcome=outcome):
                self.reject(
                    [
                        self.crash(),
                        make_event("ACT-RESTART"),
                        make_event("ACT-JOURNAL-RECOVER", outcome=outcome),
                        self.config()[0],
                    ],
                    "VOTE_BEFORE_JOURNAL_RECOVERY",
                )

    def test_unsuccessful_restart_never_enables_recovery(self) -> None:
        for outcome in NON_TRANSITION_OUTCOMES:
            with self.subTest(outcome=outcome):
                self.reject(
                    [
                        self.crash(),
                        make_event("ACT-RESTART", outcome=outcome),
                        make_event("ACT-JOURNAL-RECOVER"),
                    ],
                    "JOURNAL_RECOVERY_OUT_OF_ORDER",
                )

    def test_unsuccessful_crash_does_not_disable_validator(self) -> None:
        for outcome in ("REJECTED", "STUTTER", "NO_OP", "BLOCKED"):
            with self.subTest(outcome=outcome):
                self.assertEqual(
                    self.check(
                        [
                            make_event("ACT-CRASH", outcome=outcome),
                            *self.config(),
                        ]
                    )["status"],
                    "PASS",
                )

    def test_successful_retry_of_recovery_enables_vote(self) -> None:
        self.assertEqual(
            self.check(
                [
                    self.crash(),
                    make_event("ACT-RESTART"),
                    make_event("ACT-JOURNAL-RECOVER", outcome="REJECTED"),
                    make_event("ACT-JOURNAL-RECOVER"),
                    *self.config(),
                ]
            )["status"],
            "PASS",
        )

    def test_recovery_does_not_erase_durable_conflict(self) -> None:
        first_vote = self.config()[0]
        conflicting_vote = copy.deepcopy(first_vote)
        conflicting_vote["body_hash"] = cid("conflicting-recovered-body")
        conflicting_vote["durable_sequence"] = 2
        self.reject(
            [
                first_vote,
                self.crash(),
                make_event("ACT-RESTART"),
                make_event("ACT-JOURNAL-RECOVER"),
                conflicting_vote,
            ],
            "CONFLICTING_DURABLE_VOTE",
        )


if __name__ == "__main__":
    unittest.main()
