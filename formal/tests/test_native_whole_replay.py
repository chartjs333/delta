"""Original mixed WAL source boundaries and whole-policy proof integration."""

import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_policy_wal_vectors as native  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_policy_codec import decode  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402


class NativeWholeReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = native.sources()["delta-runtime-cpp/src/runtime.cpp"].decode()
        cls.proofs = ROOT / "formal/proofs/DeltaReduce"

    def test_original_nonempty_policy_and_exact_two_record_prefix(self):
        path = ROOT / "formal/proposals/evidence/native-proposal-replay/cpp-cross-check.json"
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "ccf04cc701410b20c122116ad006f5194f471380849c4d1beeb0fc348077eef6",
        )
        doc = load_json_strict(path)
        row = next(r for r in doc["observed"] if r["name"] == "no-snapshot")
        policy = decode(bytes.fromhex(row["policy_hex"]))
        self.assertEqual([c["action"] for c in policy["candidates"]], [1, 2])
        self.assertEqual(len(policy["snapshot"]["input_set_bodies"]), 1)
        capture = bytes.fromhex(row["wal_hex"])
        entries = wal_entries(capture)
        self.assertEqual(
            [(e["sequence"], e["kind"]) for e in entries], [(1, 2), (2, 1), (3, 1), (4, 1)]
        )
        vectors = load_json_strict(ROOT / "formal/proposals/native-wal-vectors.json")
        frames = [bytes.fromhex(v["frame_hex"]) for v in vectors["entries"]]
        self.assertEqual(wal_entries(frames[1] + frames[2]), entries[:2])
        self.assertTrue(capture.startswith(frames[1] + frames[2]))
        self.assertGreater(len(capture), len(frames[1] + frames[2]))

    def test_actual_initial_tick_and_scan_facts(self):
        self.assertIn("logical_tick_ = config_.vote_policy->initial_logical_tick", self.runtime)
        scan = self.runtime.split("for (const auto& entry : recovered.entries)", 1)[1]
        ordered = [
            "entry.sequence == expected_sequence",
            "entry.wal_record_bytes == vote_policy_identity_",
            "validate_vote_admission(",
            "VoteAdmissionMode::recovery",
            "vote_journal_.record(vote)",
        ]
        self.assertEqual([scan.index(x) for x in ordered], sorted(scan.index(x) for x in ordered))
        self.assertIn("logical_tick_, false, vote_authority_invalidated_", scan)

    def test_command_recompute_before_state_and_invalidation(self):
        scan = self.runtime.split("for (const auto& entry : recovered.entries)", 1)[1]
        ordered = [
            "command.logical_tick >= logical_tick_",
            "core::transition::apply(recovered_state",
            "result.next_state_bytes == entry.next_state_bytes",
            "recovered_state = entry.next_state_bytes",
            "logical_tick_ = command.logical_tick",
            "vote_authority_invalidated_ = true",
        ]
        self.assertEqual([scan.index(x) for x in ordered], sorted(scan.index(x) for x in ordered))

    def test_original_cache_retry_is_before_fresh_admission(self):
        live = self.runtime.split("VoteReceipt process_vote(", 1)[1]
        ordered = [
            "candidate.record(vote)",
            "Disposition::replay",
            "vote_admissions_.find(vote_id)",
            "return VoteReceipt{",
            "validate_vote_admission(",
        ]
        self.assertEqual([live.index(x) for x in ordered], sorted(live.index(x) for x in ordered))

    def test_snapshot_and_torn_scope_are_explicit(self):
        self.assertIn("snapshot->journal_sequence == 0U", self.runtime)
        self.assertIn("recovered_state == snapshot->state_bytes", self.runtime)
        self.assertIn("wal_.truncate(recovered.durable_prefix_bytes)", self.runtime)
        scope = (ROOT / "formal/proposals/native-whole-replay-proof.md").read_text()
        for marker in [
            "two-record prefix",
            "narrower complete-scan domain",
            "Eleven finite SHA",
            "not a general SHA proof",
            "does not newly compose",
            "sequence-zero snapshot",
        ]:
            self.assertIn(marker, scope)

    def test_closed_mode_computes_original_policy(self):
        src = (self.proofs / "NativeReplayAdmission.lean").read_text()
        for marker in [
            "NativeCandidateAuthority.bindPolicy sha p s",
            "NativePolicyBytes.decodePolicy policy",
            "NativeSelectedVote.fromBytes sha policy state raw facts",
            "| .whole => prepareWhole",
            "restricted : mode = .config \u2228 mode = .proposals",
            "wholeChecks",
            "guardedActionMatches",
        ]:
            self.assertIn(marker, src)
        for forbidden in [
            "otherAuthorized",
            "with candidates :=",
            "graphEmpty",
            "nativeArithmeticRecoveryRefines",
        ]:
            self.assertNotIn(forbidden, src)

    def test_recovery_uses_executed_prefix_and_historical_cache(self):
        src = (self.proofs / "NativeWholeReplay.lean").read_text()
        vectors = (self.proofs / "NativeWholeReplayVectors.lean").read_text()
        for name in [
            "historyVotePosition",
            "recoveredPosition",
            "globalPosition",
            "entryWholeAuthority",
            "duplicateScanRejected",
            "arithmeticScanRejected",
            "observedWhole",
            "retryWholeOrigin",
        ]:
            self.assertIn("theorem " + name, src)
        for name in [
            "wholePolicyComputed",
            "wholeOriginalVote",
            "originalRecovery",
            "identicalPreviousResult",
            "exactRetry",
            "actualCommandRetry",
            "duplicateOriginalRejected",
            "originalNonemptyInput",
        ]:
            self.assertIn("theorem " + name, vectors)
        self.assertNotIn("NativeCandidateAuthorityVectors.mixed", vectors)

    def test_named_declarations_in_axiom_audit(self):
        audit = (self.proofs / "AxiomAudit.lean").read_text().splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text().splitlines()
        for mod in ["NativeReplayAdmission", "NativeWholeReplay", "NativeWholeReplayVectors"]:
            self.assertIn("import DeltaReduce." + mod, imports)
            for name in re.findall(
                r"^(?:def|theorem) (\w+)", (self.proofs / (mod + ".lean")).read_text(), re.M
            ):
                self.assertIn("#print axioms DeltaReduce." + mod + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
