"""Exact codec scope and evidence integrity; never certify protocol admission."""

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_receipt_vectors as vectors  # noqa: E402
from native_policy_wal import receipt  # noqa: E402


class NativeReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        cls.rows = cls.result["observed"]

    def test_native_codec_all_actions_not_admission(self):
        self.assertEqual(vectors.validate(self.rows), self.rows)
        self.assertEqual(len(self.result["unmodified_translation_units"]), 9)
        self.assertTrue(self.result["native_codec_execution"])
        for k in [
            "native_runtime_execution",
            "arithmetic_execution",
            "native_export_authenticated",
            "gate_eligible",
        ]:
            self.assertFalse(self.result[k])
        self.assertEqual(sum(r["rejected"] + r["hash_mismatch_rejected"] for r in self.rows), 27)

    def test_native_original_frames_retain_context_sequence_id(self):
        original = json.loads(
            (
                ROOT / "formal/proposals/evidence/native-admission-snapshot/cpp-cross-check.json"
            ).read_bytes()
        )
        prior = {
            row["vote_hex"]
            for row in original["observed"]
            if row["name"].startswith("original-")
            or row["name"] in {"parameter-guard-live", "apply-guard-live"}
        }
        for r in self.rows:
            raw = bytes.fromhex(r["receipt_hex"])
            parsed = receipt(raw)
            self.assertIn(r["frame_hex"], prior)
            self.assertEqual(parsed["frame"].hex(), r["frame_hex"])
            self.assertEqual(raw[20:24], b"\0" * 4)
            self.assertTrue(r["replay_equal"])

    def test_native_hash_counterchecks_are_distinct_from_container_shape(self):
        for r in self.rows:
            raw = bytes.fromhex(r["hash_mismatch_hex"])
            with self.assertRaisesRegex(ValueError, "receipt vote ID"):
                receipt(raw)
            original = bytes.fromhex(r["receipt_hex"])
            self.assertEqual(sum(a != b for a, b in zip(raw, original, strict=True)), 1)
            self.assertEqual(raw[:36], original[:36])
            self.assertEqual(len(raw), len(original))
        lean = vectors.LEAN.read_text(encoding="utf-8")
        self.assertIn("structuralDoesNotAuthenticate", lean)
        self.assertNotIn("nativeArithmeticRecoveryRefines", lean)

    def test_observation_mutations_reject(self):
        for rows in [self.rows[:-1], self.rows[::-1], self.rows + self.rows[:1]]:
            with self.assertRaises(ValueError):
                vectors.validate(rows)
        for key, value in [
            ("action", True),
            ("rejected", True),
            ("replay_equal", False),
            ("hash_mismatch_rejected", False),
            ("extra", 1),
        ]:
            rows = copy.deepcopy(self.rows)
            rows[0][key] = value
            with self.assertRaises(ValueError):
                vectors.validate(rows)
        rows = copy.deepcopy(self.rows)
        rows[0]["receipt_hex"] = rows[1]["receipt_hex"]
        with self.assertRaises(ValueError):
            vectors.validate(rows)

    def test_exact_generator_and_source_pins(self):
        paths = [vectors.TARGET, vectors.LEAN]
        before = {p: p.read_bytes() for p in paths}
        vectors.generate()
        self.assertEqual({p: p.read_bytes() for p in paths}, before)
        self.assertEqual((vectors.FOLDER / "harness.cpp").read_text(), vectors.HARNESS)
        self.assertEqual(
            self.result["source_sha256"],
            {p: hashlib.sha256(b).hexdigest() for p, b in vectors.wal.sources().items()},
        )

    def test_every_decl_in_mandatory_import_and_axiom_audit(self):
        import re

        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeReceiptBytes", "NativeReceiptVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            text = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            names = re.findall(r"^(?:def|theorem|abbrev) ([\w.]+)", text, re.M)
            for name in names:
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
