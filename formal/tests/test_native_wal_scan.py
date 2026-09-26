"""Native scan fixtures, original byte boundaries and mandatory proof integration."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_wal_lean as previous  # noqa: E402


class NativeWalScanTests(unittest.TestCase):
    def test_original_complete_stream_and_offsets(self):
        rows = previous.load()
        vectors = json.loads(previous.TARGET.read_bytes())["entries"]
        first = bytes.fromhex(vectors[1]["frame_hex"])
        second = bytes.fromhex(vectors[2]["frame_hex"])
        self.assertEqual(len(first), 823)
        self.assertEqual(len(second), 2723)
        self.assertEqual((first + second).hex(), rows["after-state-command-retry"]["wal_hex"])
        self.assertEqual(
            rows["record"]["receipt_hex"], rows["after-state-command-retry"]["receipt_hex"]
        )

    def test_actual_partial_bytes_are_retained_exactly(self):
        rows = previous.load()
        original = bytes.fromhex(rows["record"]["wal_hex"])
        partial = bytes.fromhex(rows["crash-partial"]["wal_hex"])
        self.assertEqual(partial, original[:411])
        self.assertEqual(rows["crash-partial"]["receipt_hex"], "")
        self.assertEqual(rows["recover-partial"]["wal_hex"], "")
        self.assertEqual(rows["crash-durable-uncommitted"]["wal_hex"], original.hex())
        self.assertEqual(rows["crash-durable-uncommitted"]["receipt_hex"], "")

    def test_mandatory_modules_and_audit(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeWalScan", "NativeWalScanVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|abbrev|theorem) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)


if __name__ == "__main__":
    unittest.main()
