"""Source-backed original bounds examples and kernel/audit coverage inventory."""

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_accumulator_lean as vectors  # noqa: E402
from generate_native_source_artifacts import fixture_store  # noqa: E402
from native_accumulator_source import resolve_bound_q_source, theorem_metadata  # noqa: E402
from native_source_artifacts import SourceError, canonical  # noqa: E402


class NativeAccumulatorLeanTests(unittest.TestCase):
    def test_original_documents_full_fields_and_bytes(self):
        store, golden, _ = fixture_store()
        doc = json.loads(vectors.TARGET.read_bytes())
        resolved = resolve_bound_q_source(store, golden["manifest"]["content_id"])
        self.assertEqual(len(doc["original_documents"]), 2)
        for row, count in zip(doc["original_documents"], [12, 18], strict=True):
            self.assertEqual(len(row["value"]), count)
            self.assertEqual(bytes.fromhex(row["bytes_hex"]), store[row["id"]])
            self.assertEqual(canonical(row["value"]), store[row["id"]])
        p = doc["original_documents"][1]["value"]
        self.assertEqual(p["theorems"], theorem_metadata())
        self.assertEqual(resolved.accumulator.product, 32767 * int(p["coefficient_abs_max"]))
        self.assertEqual(resolved.accumulator.prefix, 9223372026117357570)
        self.assertEqual(
            bytes.fromhex(doc["original_profile_bytes_hex"]), store[doc["original_profile_id"]]
        )
        self.assertTrue(doc["missing_base_preimage"])

    def test_hashes_are_exact_preimages_but_not_authority(self):
        doc = json.loads(vectors.TARGET.read_bytes())
        for row in doc["synthetic_hash_preimages"]:
            self.assertEqual(
                row["id"], "sha256:" + hashlib.sha256(bytes.fromhex(row["bytes_hex"])).hexdigest()
            )
        for key in [
            "formal_go",
            "native_execution",
            "native_export_authenticated",
            "hash_adapter_authenticated",
            "native_recovery_proved",
            "full_corpus_kernel_example",
        ]:
            self.assertFalse(doc[key])
        self.assertEqual(
            doc["headroom_scope"], "UNIQUE_ADMISSIBLE_VALUE_NOT_SERIALIZED_OBSERVATION"
        )

    def test_every_named_case_and_general_declaration_is_audited(self):
        doc = json.loads(vectors.TARGET.read_bytes())
        source = vectors.LEAN.read_text(encoding="utf-8")
        self.assertEqual(len(doc["small_kernel_cases"]), 29)
        for name in doc["small_kernel_cases"]:
            self.assertRegex(source, r"theorem " + name + r"\b")
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "NativeAccumulatorBytes",
            "NativeAccumulatorBinding",
            "NativeAccumulatorVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            text = (vectors.LEAN.parent / (module + ".lean")).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) (\w+)", text, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)

    def test_generator_is_byte_exact(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))

    def test_source_boundary_substitution_stops_before_output(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        with patch.object(vectors, "originals", side_effect=SourceError("SOURCE_SUBSTITUTED")):
            with self.assertRaisesRegex(SourceError, "SOURCE_SUBSTITUTED"):
                vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))


if __name__ == "__main__":
    unittest.main()
