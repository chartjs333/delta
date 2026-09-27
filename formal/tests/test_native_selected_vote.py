"""Original native admission boundary, phase inventory and proposal integration."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_policy_wal_vectors as native  # noqa: E402
import generate_native_selected_vote as g  # noqa: E402


class NativeSelectedVoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blobs = native.sources()
        cls.admission = cls.blobs["delta-core-cpp/src/certificates/vote_admission.cpp"].decode()
        cls.runtime = cls.blobs["delta-runtime-cpp/src/runtime.cpp"].decode()

    def test_reproduction(self):
        self.assertEqual(g.generate().encode(), g.TARGET.read_bytes())

    def test_native_arithmetic_guard_is_unconditional_in_normal_build(self):
        fn = self.admission.split("VoteAdmission validate_vote_admission(", 1)[1]
        guard = fn.split("#if !defined(DELTA_RECORD_VOTE_MUTANT_SKIP_ARITHMETIC_INPUT_GUARD)", 1)[
            1
        ].split("#endif", 1)[0]
        self.assertIn("action != VoteAction::parameter && action != VoteAction::apply", guard)
        order = [
            "validate_vote_admission_policy(policy, state)",
            "require_vote(vote)",
            "parse_vote_action(vote.kind)",
            "arithmetic vote lacks authoritative native recomputation inputs",
            "vote.validator_id == policy.local_validator_id",
            "for (const auto& candidate : policy.candidates)",
            "vote.body_hash == binding->body_hash",
            "vote.durable_sequence == expected_durable_sequence",
            "mode == VoteAdmissionMode::live",
            "!admission_state.authority_invalidated",
            "phase_allows(action, state.phase)",
        ]
        self.assertEqual(sorted(fn.index(x) for x in order), [fn.index(x) for x in order])
        self.assertIn("binding->parents.parent_checkpoint_id == state.parent_checkpoint_id", fn)

    def test_native_phase_inventory(self):
        fn = self.admission.split("bool phase_allows(", 1)[1].split(
            "void validate_candidate_shape(", 1
        )[0]
        cases = re.findall(r"case VoteAction::(\w+):", fn)
        self.assertEqual(
            cases,
            [
                "round_config",
                "input_set",
                "eligibility",
                "aggregation_plan",
                "parameter",
                "aggregate_root",
                "apply",
                "view_change",
                "abort",
            ],
        )
        self.assertEqual(fn.count("return phase =="), 3)
        for phase in ["ticketing_open", "available", "eligible", "aggregated", "aborted"]:
            self.assertIn("protocol::RoundPhase::" + phase, fn)
        vectors = g.TARGET.read_text()
        self.assertIn("theorem exactPhaseTable", vectors)
        self.assertIn("theorem inventedPhase", vectors)

    def test_native_deadline_and_exact_request_guards(self):
        fn = self.admission.split("VoteAdmission validate_vote_admission(", 1)[1]
        self.assertEqual(fn.count("policy.snapshot.abort_requests.empty()"), 2)
        self.assertIn("admission_state.logical_tick >= policy.soft_deadline_tick", fn)
        self.assertEqual(fn.count("admission_state.logical_tick < policy.hard_deadline_tick"), 2)
        self.assertIn("body->reason_code == policy.configured_abort_reason", fn)
        self.assertIn("policy.snapshot, policy.round_id, policy.configured_abort_reason", fn)

    def test_historical_retry_precedes_fresh_admission(self):
        fn = self.runtime.split("VoteReceipt process_vote(", 1)[1].split(
            "const detail::JournalEntry entry", 1
        )[0]
        order = [
            "core::protocol::parse_vote(work.vote_bytes)",
            "candidate.record(vote)",
            "Disposition::replay",
            "return VoteReceipt{",
            "checked_next_journal_sequence(sequence_.load())",
            "core::consensus::validate_vote_admission(",
        ]
        self.assertEqual(sorted(fn.index(x) for x in order), [fn.index(x) for x in order])
        self.assertIn("vote_admissions_.find(vote_id)", fn)

    def test_scan_recovery_rechecks_then_rejects_duplicate(self):
        fn = self.runtime.split("durable vote exists on a submit-only runtime handle", 1)[1]
        fn = fn.split("vote_admissions_.emplace", 1)[0]
        self.assertIn("entry.wal_record_bytes == vote_policy_identity_", fn)
        self.assertIn("VoteAdmissionState{", fn)
        self.assertIn("logical_tick_, false, vote_authority_invalidated_", fn)
        self.assertIn("VoteAdmissionMode::recovery", fn)
        self.assertLess(
            fn.index("validate_vote_admission("), fn.index("vote_journal_.record(vote)")
        )
        self.assertIn("Disposition::recorded", fn)
        self.assertIn("durable vote journal contains an exact duplicate", fn)

    def test_whole_policy_selection_and_scope(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeSelectedVote.lean").read_text()
        for marker in [
            "NativeCandidateAuthority.bindPolicy sha p s",
            "b.entries.find? (fun e => matching s v e.original)",
            "checkVote p s b.snapshot.prior.tail e r v",
            "NativePolicyBytes.decodePolicy policyRaw",
            "NativeVoteBytes.decodeFrame voteRaw",
            "originalByteAuthority",
            "sharedFailureTail",
            "byteGuardRetained",
            "recoveryStillChecks",
        ]:
            self.assertIn(marker, src)
        for bad in [
            "with candidates :=",
            "graphEmpty",
            "otherAuthorized",
            "nativeArithmeticRecoveryRefines",
        ]:
            self.assertNotIn(bad, src)
        vectors = g.TARGET.read_text()
        for name in [
            "wholeOriginalConfigBytes",
            "guardedRecovery5",
            "guardedRecovery7",
            "noncurrentParent",
            "foreignRequestBlocksOrdinary",
            "exactRequestEarly",
            "foreignRequestNotEnough",
            "expiredRecovery",
            "signatureIsOnlySyntactic",
        ]:
            self.assertIn("theorem " + name, vectors)
        self.assertIn("No full original nonempty mixed-policy wrapper", vectors)

    def test_all_names_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text().splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text().splitlines()
        for module in ["NativeSelectedVote", "NativeSelectedVoteVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|theorem) (\w+)", src, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
