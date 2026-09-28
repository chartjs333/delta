"""Original mixed-byte scan risks and audited candidate-history integration."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import load_json_strict  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402

MODULES = ["NativeArithmeticJournal", "NativeArithmeticHistory", "NativeArithmeticHistoryVectors"]


class NativeArithmeticHistoryTests(unittest.TestCase):
    @staticmethod
    def original_frames():
        doc = load_json_strict(
            ROOT / "formal/proposals/evidence/native-proposal-replay/cpp-cross-check.json"
        )
        row = next(r for r in doc["observed"] if r["name"] == "no-snapshot")
        raw = bytes.fromhex(row["wal_hex"])
        frames = []
        while raw:
            size = int.from_bytes(raw[8:12], "big")
            frames.append(raw[:size])
            raw = raw[size:]
        return frames

    def test_complete_original_order_and_invalid_prefixes(self):
        frames = self.original_frames()
        entries = wal_entries(b"".join(frames))
        self.assertEqual([e["sequence"] for e in entries], list(range(1, len(entries) + 1)))
        self.assertEqual([(e["kind"], e["sequence"]) for e in entries[:2]], [(2, 1), (1, 2)])
        for invalid in [
            b"".join(frames[1:]),
            frames[1] + frames[0],
            frames[0] + frames[0],
            b"".join(frames) + frames[-1],
        ]:
            with self.subTest(size=len(invalid)), self.assertRaisesRegex(ValueError, "sequence"):
                wal_entries(invalid)

    def test_incomplete_and_corrupt_observations_do_not_become_empty(self):
        raw = b"".join(self.original_frames())
        for invalid in [raw[:-1], raw[:7], raw + b"D", raw[:-1] + bytes([raw[-1] ^ 1])]:
            with self.subTest(size=len(invalid)), self.assertRaises(ValueError):
                wal_entries(invalid)
        self.assertEqual(wal_entries(b""), [])

    def test_declarations_imported_and_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(
                r"^(?:def|abbrev|theorem|structure|inductive) (\w+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
