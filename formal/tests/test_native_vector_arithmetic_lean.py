"""Independent coordinate sums, source linkage, and reproducible kernel inventory."""

import json
import re
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "formal/scripts"))
import generate_native_vector_arithmetic_lean as vectors
from formal_artifacts import sha256_file
from native_source_artifacts import SourceError


class NativeVectorArithmeticLeanTests(unittest.TestCase):
    def document(self):
        return json.loads(vectors.TARGET.read_bytes())

    def test_all_coordinates_against_rational_arithmetic(self):
        doc = self.document()
        self.assertEqual(doc["denominator"], 12)
        self.assertEqual(len(doc["cases"]), 10)
        for case in doc["cases"]:
            width = len(case["numerators"])
            for k in range(width):
                total = Fraction(0)
                for term, prefix in zip(case["terms"], case["prefixes"], strict=True):
                    self.assertEqual(len(term["values"]), width)
                    total += Fraction(*term["weight"]) * term["values"][k]
                    self.assertEqual(total * 12, prefix[k])
                self.assertEqual(total * 12, case["numerators"][k])
        self.assertEqual(sum(len(c["numerators"]) for c in doc["cases"]), 72)

    def test_zero_weight_and_specific_denominator_retained(self):
        cases = self.document()["cases"]
        for case in cases[:5]:
            self.assertEqual([t["weight"] for t in case["terms"]], [[1, 3], [1, 2]])
            q = case["terms"][0]["values"]
            self.assertEqual(case["numerators"], [-2 * v for v in q])
            self.assertNotEqual(case["numerators"], [-v for v in q])
        for case in cases[5:]:
            self.assertEqual(len(case["terms"]), 1)
            self.assertEqual(case["terms"][0]["weight"], [0, 1])
            self.assertTrue(any(case["terms"][0]["values"]))
            self.assertEqual(case["numerators"], [0] * len(case["numerators"]))

    def test_pinned_cross_source_scope(self):
        doc = self.document()
        self.assertEqual(
            doc["source_fixture_sha256"],
            sha256_file(vectors.ROOT / "formal/proposals/native-vector-projection-vectors.json"),
        )
        for field in (
            "formal_go",
            "native_execution",
            "native_export_authenticated",
            "whole_source_kernel_example",
            "draft_schema_q_bytes_joined",
        ):
            self.assertFalse(doc[field])

    def test_mandatory_kernel_inventory(self):
        doc = self.document()
        root = (vectors.ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (vectors.LEAN.parent / "AxiomAudit.lean").read_text(encoding="utf-8")
        for mod in (
            "NativeVectorContext",
            "NativeVectorArithmetic",
            "NativeVectorArithmeticVectors",
        ):
            self.assertIn("import DeltaReduce." + mod, root)
            source = (vectors.LEAN.parent / (mod + ".lean")).read_text(encoding="utf-8")
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            names = re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M)
            for name in names:
                self.assertIn("#print axioms DeltaReduce." + mod + "." + name, audit)
        source = vectors.LEAN.read_text(encoding="utf-8")
        self.assertEqual(doc["kernel_theorems"], re.findall(r"^theorem (\w+)", source, re.M))

    def test_generator_byte_exact(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))

    def test_substituted_original_sources_cannot_generate(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        with patch.object(
            vectors.original, "source_blobs", side_effect=SourceError("SOURCE_CHANGED")
        ):
            with self.assertRaisesRegex(SourceError, "SOURCE_CHANGED"):
                vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))


if __name__ == "__main__":
    unittest.main()
