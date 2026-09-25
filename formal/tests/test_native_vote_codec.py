"""Retained native byte/parser evidence, mutation rejection and proof scope."""

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_vote_codec_vectors as vectors  # noqa: E402


class NativeVoteCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())

    def test_actual_parser_and_sha_cases(self):
        rows = vectors.validate(self.result)
        self.assertEqual(len(rows), 49)
        self.assertEqual(sum(row["accepted"] for row in rows), 12)
        self.assertEqual(sum(not row["accepted"] for row in rows), 37)
        self.assertTrue(self.result["native_codec_execution"])
        self.assertFalse(self.result["native_runtime_execution"])
        self.assertFalse(self.result["arithmetic_execution"])
        self.assertFalse(self.result["native_export_authenticated"])
        self.assertFalse(self.result["gate_eligible"])
        # Protocol parsing permits unknown nonempty kind; receipt action binding does not.
        unknown = next(row for row in rows if row["name"] == "field-26-kind")
        self.assertTrue(unknown["accepted"])

    def test_original_frames_and_receipt_content_ids(self):
        cases = vectors.cases()
        for original, (name, raw, accepted) in zip(vectors.original(), cases[:9], strict=True):
            self.assertEqual(name, "original-" + str(original["action"]))
            self.assertEqual(raw.hex(), original["frame_hex"])
            self.assertTrue(accepted)
            parsed = vectors.previous.receipt(bytes.fromhex(original["receipt_hex"]))
            self.assertEqual(parsed["frame"], raw)
            row = next(row for row in self.result["observed"] if row["name"] == name)
            self.assertEqual(row["vote_id"], parsed["vote_id"])

    def test_native_hash_and_status_mutations_reject(self):
        for key, value in [
            ("accepted", False),
            ("accepted", 1),
            ("name", "other"),
            ("vote_id", "sha256:" + "0" * 64),
            ("extra", 1),
        ]:
            changed = copy.deepcopy(self.result)
            changed["observed"][0][key] = value
            with self.assertRaises(ValueError):
                vectors.validate(changed)
        for rows in [self.result["observed"][:-1], self.result["observed"][::-1]]:
            changed = {**self.result, "observed": rows}
            with self.assertRaises(ValueError):
                vectors.validate(changed)

    def test_exact_source_and_harness(self):
        self.assertEqual(self.result["source_commit"], vectors.SOURCE)
        self.assertEqual(len(self.result["unmodified_translation_units"]), 3)
        self.assertEqual(
            self.result["source_sha256"],
            {
                p: hashlib.sha256(raw).hexdigest()
                for p, raw in vectors.previous.wal.sources().items()
            },
        )
        self.assertEqual((vectors.FOLDER / "harness.cpp").read_text(), vectors.harness())

    def test_reproduction(self):
        paths = [vectors.LEAN, vectors.TARGET]
        before = {p: p.read_bytes() for p in paths}
        vectors.generate()
        self.assertEqual({p: p.read_bytes() for p in paths}, before)

    def test_all_named_declarations_audited(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeVoteBytes", "NativeVoteCodecVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|theorem|abbrev) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)

    def test_native_fields_and_explicit_adapter_scope(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativeVoteBytes.lean").read_text()
        fields = vectors.decode_flat(bytes.fromhex(vectors.original()[0]["frame_hex"]), 3)
        for name in fields:
            self.assertIn('ascii "' + name + '"', source)
        self.assertIn("4*1024*1024", source)
        self.assertIn("16*1024*1024", source)
        self.assertIn(fields["formal_semantics_id"], source)
        report = json.loads(vectors.TARGET.read_bytes())
        self.assertEqual(report["hash_adapter"], "FINITE_EXACT_PREIMAGE_LOOKUP_NOT_SHA_PROOF")
        self.assertFalse(report["native_admission"])
        self.assertFalse(report["gate_eligible"])


if __name__ == "__main__":
    unittest.main()
