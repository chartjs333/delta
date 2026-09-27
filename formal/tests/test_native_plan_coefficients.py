"""Source/component arithmetic cross-check and explicit missing-authority scope."""

import json
import re
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_plan_coefficients as vectors  # noqa: E402
import generate_native_plan_weights as originals  # noqa: E402
from native_plan_weights import resolve_plan_weights  # noqa: E402
from native_source_artifacts import SourceError  # noqa: E402


class NativePlanCoefficientTests(unittest.TestCase):
    def test_exact_fraction_scaling_and_final_alpha(self):
        store, docs = originals.synthetic_case()
        apc, edges = originals.put_graph(store, docs)
        result = resolve_plan_weights(store, apc, edges)
        doc = json.loads(vectors.TARGET.read_bytes())
        self.assertEqual(doc["synthetic_apc"], apc)
        expected = [
            Fraction(int(w["alpha"]["numerator"]), w["alpha"]["denominator"]) * 12
            for w in docs["APC"]["weights"]
        ]
        self.assertEqual(expected, [0, 4, 6])
        self.assertEqual(doc["synthetic_coefficients"], expected)
        self.assertEqual(doc["synthetic_domains"], list(result.domains))
        self.assertEqual(len(docs["EC"]["entries"]), 4)
        self.assertEqual(len(result.rows), 3)
        self.assertEqual(result.rows[1]["ec_gamma"], {"numerator": "1", "denominator": 7})
        self.assertNotEqual(expected[1], expected[1] * Fraction(1, 7))

    def test_missing_original_proof_is_retained(self):
        original = originals.generate()
        doc = json.loads(vectors.TARGET.read_bytes())
        self.assertEqual(doc["original_apc"], original["original_members"]["plan_id"])
        self.assertEqual(
            doc["original_weight_join_failure"], original["original_weight_join_failure"]
        )
        self.assertTrue(doc["original_weight_join_failure"].startswith("MISSING_PREIMAGE:"))
        for key in (
            "formal_go",
            "native_execution",
            "hash_adapter_authenticated",
            "whole_policy_proof_kernel_example",
            "q_values_joined",
        ):
            self.assertFalse(doc[key])

    def test_all_kernel_cases_are_mandatory_and_audited(self):
        doc = json.loads(vectors.TARGET.read_bytes())
        self.assertEqual(len(doc["small_kernel_cases"]), 32)
        src = vectors.LEAN.read_text(encoding="utf-8")
        for name in doc["small_kernel_cases"]:
            self.assertRegex(src, r"theorem " + name + r"\b")
        root = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for mod in ("NativePlanMembers", "NativePlanCoefficients", "NativePlanCoefficientVectors"):
            self.assertIn("import DeltaReduce." + mod, root)
            source = (vectors.LEAN.parent / (mod + ".lean")).read_text(encoding="utf-8")
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure) (\w+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + mod + "." + name, audit)

    def test_generator_byte_exact(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))

    def test_substituted_source_cannot_write_vectors(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        with patch.object(
            vectors.source, "generate", side_effect=SourceError("SOURCE_SUBSTITUTED")
        ):
            with self.assertRaisesRegex(SourceError, "SOURCE_SUBSTITUTED"):
                vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))


if __name__ == "__main__":
    unittest.main()
