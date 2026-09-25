"""Exact retained DRW1 bytes and fail-closed proposal binding checks."""

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_wal_lean as vectors  # noqa: E402
from native_policy_wal import bind_vote_entry, receipt, wal_entries  # noqa: E402


class NativeWalLeanTests(unittest.TestCase):
    def test_retained_original_and_historical_receipt(self):
        rows = vectors.load()
        original, later = rows["record"], rows["after-state-command-retry"]
        self.assertEqual(original["receipt_hex"], later["receipt_hex"])
        entries = wal_entries(bytes.fromhex(later["wal_hex"]))
        self.assertEqual([e["sequence"] for e in entries], [1, 2])
        self.assertEqual([e["kind"] for e in entries], [2, 1])
        self.assertEqual(receipt(bytes.fromhex(later["receipt_hex"]))["sequence"], 1)
        self.assertEqual(later["recovered_votes"], 1)
        self.assertEqual(later["sequence"], 2)

    def test_unchanged_source_evidence_pin(self):
        self.assertEqual(hashlib.sha256(vectors.SOURCE.read_bytes()).hexdigest(), vectors.PIN)
        with patch.object(vectors, "PIN", "0" * 64):
            with self.assertRaises(ValueError):
                vectors.load()

    def test_corruption_and_truncation(self):
        raw = bytes.fromhex(vectors.load()["record"]["wal_hex"])
        for offset in [0, 4, 6, 8, 12, 20, 21, 24, len(raw) - 1]:
            bad = bytearray(raw)
            bad[offset] ^= 1
            with self.assertRaises(ValueError):
                wal_entries(bytes(bad))
        for end in [1, 11, 12, len(raw) // 2, len(raw) - 1]:
            with self.assertRaises(ValueError):
                wal_entries(raw[:end])

    def test_rehashed_policy_substitution(self):
        row = vectors.load()["record"]
        raw = bytearray.fromhex(row["wal_hex"])
        raw[-33] = ord("0") if raw[-33] != ord("0") else ord("1")
        raw[-32:] = hashlib.sha256(raw[:-32]).digest()
        entry = wal_entries(bytes(raw))[0]
        with self.assertRaises(ValueError):
            bind_vote_entry(entry, bytes.fromhex(row["policy_hex"]))

    def test_rehashed_sequence_substitution(self):
        raw = bytearray.fromhex(vectors.load()["record"]["wal_hex"])
        raw[12:20] = (2).to_bytes(8, "big")
        raw[-32:] = hashlib.sha256(raw[:-32]).digest()
        with self.assertRaises(ValueError):
            wal_entries(bytes(raw))

    def test_missing_receipt_does_not_mean_absent_record(self):
        rows = vectors.load()
        full = rows["crash-durable-uncommitted"]
        self.assertEqual(full["receipt_hex"], "")
        self.assertEqual(len(wal_entries(bytes.fromhex(full["wal_hex"]))), 1)
        partial = rows["crash-partial"]
        self.assertEqual(partial["receipt_hex"], "")
        self.assertTrue(partial["wal_hex"])
        self.assertLess(len(partial["wal_hex"]), len(full["wal_hex"]))
        with self.assertRaises(ValueError):
            wal_entries(bytes.fromhex(partial["wal_hex"]))

    def test_reproduction_and_honest_scope(self):
        paths = [vectors.LEAN, vectors.TARGET]
        before = {p: p.read_bytes() for p in paths}
        vectors.generate()
        self.assertEqual({p: p.read_bytes() for p in paths}, before)
        report = json.loads(vectors.TARGET.read_bytes())
        self.assertFalse(report["new_native_execution"])
        self.assertFalse(report["full_native_recovery"])
        self.assertFalse(report["native_export_authenticated"])
        self.assertFalse(report["gate_eligible"])
        self.assertEqual(len(report["entries"]), 3)

    def test_mandatory_project_and_audit(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeWalBytes", "NativeWalVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|theorem|abbrev) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)


if __name__ == "__main__":
    unittest.main()
