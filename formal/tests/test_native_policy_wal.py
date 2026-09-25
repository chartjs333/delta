"""Pinned native WAL evidence is finite local execution, never full formal authority."""

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_policy_wal_vectors as vectors  # noqa: E402
from formal_artifacts import canonical_json_bytes  # noqa: E402
from native_policy_wal import (  # noqa: E402
    bind_vote_entry,
    decode_flat,
    policy_digest,
    receipt,
    snapshot,
    wal_entries,
)


class NativePolicyWalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        cls.rows = cls.evidence["observed"]
        cls.by = {r["name"]: r for r in cls.rows}

    def raw(self, name, field):
        return bytes.fromhex(self.by[name][field + "_hex"])

    def output(self, rows):
        return "\n".join(canonical_json_bytes(r).decode("ascii") for r in rows)

    def test_complete_native_output_and_honest_execution_scope(self):
        self.assertEqual(len(self.rows), 62)
        self.assertEqual(vectors.parse_output(self.output(self.rows)), self.rows)
        self.assertTrue(self.evidence["native_runtime_execution"])
        self.assertTrue(self.evidence["native_wal_execution"])
        for key in [
            "native_export_authenticated",
            "full_public_recovery_relation",
            "arithmetic_execution",
            "gate_eligible",
        ]:
            self.assertFalse(self.evidence[key])
        self.assertIn("IN_PROCESS", self.evidence["crash_mode"])
        self.assertEqual(self.evidence["execution_platform"], "WINDOWS_MSVC_LOCAL_FILESYSTEM")

    def test_all_snapshot_fields_and_nine_native_codec_fixtures(self):
        fields = vectors.snapshot_inventory(vectors.sources())
        self.assertEqual(len(fields), 33)
        self.assertEqual(len(set(fields)), 33)
        for name in [r["name"] for r in self.rows if r["name"].startswith("codec-")]:
            row = self.by[name]
            self.assertTrue(row["roundtrip"])
            self.assertEqual(policy_digest(self.raw(name, "policy")).decode(), row["sha256"])
        row = self.by["codec-ISC"]
        self.assertEqual(row["truncated_rejections"], len(self.raw("codec-ISC", "policy")))
        for index in range(5):
            self.assertEqual(self.by[f"malformed-{index}"]["outcome"]["status"], "CODEC_REJECT")

    def test_exact_wal_policy_and_receipt_not_just_state_hash(self):
        wal, policy = self.raw("record", "wal"), self.raw("record", "policy")
        entries = wal_entries(wal)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["record"], policy_digest(policy))
        vote = bind_vote_entry(entries[0], policy)
        proof = receipt(self.raw("record", "receipt"))
        self.assertEqual(proof["frame"], entries[0]["command"])
        self.assertEqual(vote["context_id"], proof["context"])
        self.assertEqual(proof["sequence"], 1)
        for name in ["retry", "conflict", "snapshot", "reopen", "reopen-retry", "reopen-no-policy"]:
            self.assertEqual(self.raw(name, "wal"), wal, name)
        for name in ["retry", "reopen-retry"]:
            self.assertEqual(self.raw(name, "receipt"), self.raw("record", "receipt"))
            self.assertTrue(self.by[name]["replay"])
        snap = snapshot(self.raw("snapshot", "snapshot"))
        self.assertEqual(snap["sequence"], 1)
        self.assertEqual(snap["state"], self.raw("record", "initial_state"))

    def test_changed_policy_rejected_on_existing_wal_but_not_authenticated_by_empty_open(self):
        original = self.raw("record", "policy")
        for name, _ in vectors.MUTATIONS:
            rejected, fresh = self.by["changed-reopen-" + name], self.by["changed-empty-" + name]
            self.assertEqual(rejected["outcome"]["status"], "RUNTIME_REJECT")
            self.assertEqual(rejected["outcome"]["code"], "8")
            self.assertEqual(self.raw("changed-reopen-" + name, "wal"), self.raw("record", "wal"))
            changed = bytes.fromhex(rejected["policy_hex"])
            self.assertNotEqual(policy_digest(original), policy_digest(changed))
            with self.assertRaisesRegex(ValueError, "policy identity"):
                bind_vote_entry(wal_entries(self.raw("record", "wal"))[0], changed)
            self.assertEqual(fresh["outcome"]["status"], "ACCEPT")
            self.assertEqual(fresh["wal_hex"], "")
        self.assertEqual(self.by["reopen-no-policy"]["outcome"]["status"], "RUNTIME_REJECT")

    def test_historical_retry_after_state_command_preserves_proof_and_fresh_vote_rejects(self):
        for name in ["after-state-command-retry", "after-state-command-reopen-retry"]:
            row = self.by[name]
            self.assertEqual(row["sequence"], 2)
            self.assertEqual(row["recovered_votes"], 1)
            self.assertTrue(row["replay"])
            self.assertEqual(self.raw(name, "receipt"), self.raw("record", "receipt"))
            entries = wal_entries(self.raw(name, "wal"))
            self.assertEqual([e["kind"] for e in entries], [2, 1])
            next_state = decode_flat(entries[1]["state"], 5)
            self.assertEqual(next_state["phase"], "ELIGIBLE")
            # Native state command sequence and all-entry WAL sequence are distinct.
            self.assertEqual(next_state["durable_sequence"], "1")
        failed = self.by["after-state-command-fresh"]
        self.assertEqual(failed["outcome"]["status"], "ADMISSION_REJECT")
        self.assertEqual(failed["receipt_hex"], "")
        self.assertEqual(
            self.raw("after-state-command-fresh", "wal"),
            self.raw("after-state-command-retry", "wal"),
        )

    def test_known_durable_crash_survival_keeps_exact_original_receipt(self):
        for name, _, expected in vectors.CRASHES:
            cut, recovered, retried = (self.by[p + name] for p in ["crash-", "recover-", "retry-"])
            self.assertEqual(cut["outcome"]["status"], "RUNTIME_REJECT")
            self.assertEqual(cut["outcome"]["code"], "10")
            self.assertEqual(cut["receipt_hex"], "")
            self.assertEqual(recovered["sequence"], expected)
            self.assertEqual(recovered["recovered_votes"], expected)
            self.assertEqual(retried["replay"], bool(expected))
            self.assertEqual(bytes.fromhex(retried["receipt_hex"]), self.raw("record", "receipt"))
            self.assertEqual(len(wal_entries(bytes.fromhex(recovered["wal_hex"]))), expected)
        # After sync, before in-memory commit: no receipt/sequence, but a complete WAL vote.
        cut = self.by["crash-durable-uncommitted"]
        self.assertEqual(cut["sequence"], 0)
        self.assertEqual(len(wal_entries(bytes.fromhex(cut["wal_hex"]))), 1)

    def test_partial_scan_is_not_absence_and_hook_names_do_not_define_real_io(self):
        partial = self.raw("crash-partial", "wal")
        whole = self.raw("record", "wal")
        self.assertEqual(partial, whole[: len(whole) // 2])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            wal_entries(partial)
        self.assertEqual(self.raw("recover-partial", "wal"), b"")
        self.assertEqual(self.raw("crash-before", "wal"), b"")
        # Actual source hook is before append_and_sync, despite its longer name.
        self.assertEqual(self.raw("crash-named-before-barrier", "wal"), b"")
        self.assertFalse(self.by["retry-named-before-barrier"]["replay"])
        # The two names share the same branch; neither is a process kill/power-loss test.
        self.assertEqual(
            self.by["crash-copied-unreturned"]["outcome"],
            self.by["crash-committed-unreturned"]["outcome"],
        )

    def test_guarded_arithmetic_and_corrupt_files_fail_without_receipts(self):
        for action in ["PARAMETER", "APPLY"]:
            row = self.by["guard-" + action]
            self.assertEqual(row["outcome"]["status"], "ADMISSION_REJECT")
            self.assertEqual(row["outcome"]["code"], "18")
            self.assertEqual(row["wal_hex"], "")
            self.assertEqual(row["sequence"], 0)
            self.assertEqual(row["recovered_votes"], 0)
        self.assertNotIn("DELTA_", self.evidence["compiler_flags"])
        self.assertNotIn("#define", vectors.harness())
        for name, code in [("corrupt-wal", "4"), ("corrupt-snapshot", "5")]:
            self.assertEqual(self.by[name]["outcome"]["status"], "RUNTIME_REJECT")
            self.assertEqual(self.by[name]["outcome"]["code"], code)
            self.assertEqual(self.by[name]["receipt_hex"], "")
        with self.assertRaisesRegex(ValueError, "checksum"):
            wal_entries(self.raw("corrupt-wal", "wal"))
        with self.assertRaisesRegex(ValueError, "checksum"):
            snapshot(self.raw("corrupt-snapshot", "snapshot"))

    def test_binary_evidence_mutations_do_not_become_valid_recovery(self):
        wal = self.raw("record", "wal")
        for end in range(1, len(wal)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                wal_entries(wal[:end])
        with self.assertRaises(ValueError):
            wal_entries(wal + b"\0")
        # A recomputed frame checksum does not establish the original policy relation.
        changed = bytearray(wal)
        digest_at = changed.index(policy_digest(self.raw("record", "policy")))
        changed[digest_at] = ord("0") if changed[digest_at] != ord("0") else ord("1")
        changed[-32:] = hashlib.sha256(changed[:-32]).digest()
        with self.assertRaisesRegex(ValueError, "policy identity"):
            bind_vote_entry(wal_entries(bytes(changed))[0], self.raw("record", "policy"))
        proof = self.raw("record", "receipt")
        for bad in [proof[:-1], proof + b"\0", proof[:20] + b"\x01" + proof[21:]]:
            with self.assertRaises(ValueError):
                receipt(bad)

    def test_output_rejects_omission_order_fake_return_and_boolean_sequence(self):
        for rows in [self.rows[:-1], self.rows[::-1], self.rows + self.rows[-1:]]:
            with self.assertRaises(ValueError):
                vectors.parse_output(self.output(rows))
        for name, field, value in [
            ("record", "sequence", True),
            ("crash-durable-uncommitted", "receipt_hex", self.by["record"]["receipt_hex"]),
            ("retry-before", "replay", True),
            ("recover-durable-uncommitted", "sequence", 0),
            ("record", "extra", False),
        ]:
            changed = copy.deepcopy(self.rows)
            next(row for row in changed if row["name"] == name)[field] = value
            with self.assertRaises(ValueError):
                vectors.parse_output(self.output(changed))

    def test_exact_native_source_and_harness_reproduction(self):
        self.assertEqual(
            self.evidence["source_sha256"],
            {p: hashlib.sha256(b).hexdigest() for p, b in vectors.sources().items()},
        )
        self.assertEqual(self.evidence["unmodified_translation_units"], vectors.UNITS)
        self.assertEqual(len(vectors.UNITS), 12)
        self.assertEqual((vectors.FOLDER / "harness.cpp").read_bytes(), vectors.harness().encode())
        self.assertEqual(
            self.evidence["harness_sha256"], hashlib.sha256(vectors.harness().encode()).hexdigest()
        )
        self.assertEqual(vectors.TARGET.read_bytes(), canonical_json_bytes(vectors.document()))


if __name__ == "__main__":
    unittest.main()
