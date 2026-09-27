"""Retained native observations, coverage counterexamples, mandatory proof audit."""

import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_available_q_lean as vectors  # noqa: E402
from native_source_artifacts import SourceError  # noqa: E402


class NativeAvailableQLeanTests(unittest.TestCase):
    def document(self):
        return json.loads(vectors.TARGET.read_bytes())

    def test_prior_native_component_observations(self):
        observed = json.loads(
            (
                ROOT / "formal/proposals/evidence/native-available-q/cpp-cross-check.json"
            ).read_bytes()
        )["observed"]
        cases = {c["name"]: c for c in self.document()["primitive_cases"]}
        self.assertEqual(len(observed), 17)
        for name, result in observed.items():
            self.assertEqual(cases[name]["primitive"], result["status"] == "ACCEPT", name)

    def test_complete_source_coverage_and_authority_gap(self):
        cases = {c["name"]: c for c in self.document()["primitive_cases"]}
        incomplete = cases["native-accepts-incomplete-caller-leaf-set"]
        self.assertTrue(incomplete["primitive"])
        self.assertFalse(incomplete["coverage"])
        for name in ("both-duplicate", "extra-leaf"):
            self.assertFalse(cases[name]["coverage"])
        self.assertFalse(cases["both-reversed"]["primitive"])
        self.assertTrue(cases["both-reversed"]["coverage"])
        for name in (
            "native-accepts-unrelated-opaque-ac-id",
            "native-accepts-unrelated-opaque-commitment",
        ):
            self.assertTrue(cases[name]["primitive"] and cases[name]["coverage"])
        doc = self.document()
        for key in (
            "formal_go",
            "gate_eligible",
            "native_execution",
            "native_export_authenticated",
            "commitment_manifest_identity_authenticated",
            "availability_signatures_verified",
            "new_whole_policy_corpus_kernel_example",
        ):
            self.assertFalse(doc[key])

    def test_kernel_inventory_and_actual_byte_loader(self):
        doc = self.document()
        src = vectors.LEAN.read_text(encoding="utf-8")
        self.assertEqual(len(doc["kernel_theorems"]), 55)
        for name in doc["kernel_theorems"]:
            self.assertRegex(src, r"theorem " + name + r"\b")
        root = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for mod in ("NativeAvailableQ", "NativePlanQCorpus", "NativeAvailableQVectors"):
            self.assertIn("import DeltaReduce." + mod, root)
            source = (vectors.LEAN.parent / (mod + ".lean")).read_text(encoding="utf-8")
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) (\w+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + mod + "." + name, audit)
        source = (vectors.LEAN.parent / "NativePlanQCorpus.lean").read_text(encoding="utf-8")
        statement = source.split("theorem boundDomainPrefixFits", 1)[1].split(":= by", 1)[0]
        self.assertIn("NativeAvailableQ.coordinate", statement)
        self.assertNotIn("32767", statement)  # range must be derived, not assumed

    def test_generator_byte_exact(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))

    def test_substituted_native_boundary_cannot_write(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        with patch.object(
            vectors.source, "source_blobs", side_effect=SourceError("SOURCE_SUBSTITUTED")
        ):
            with self.assertRaisesRegex(SourceError, "SOURCE_SUBSTITUTED"):
                vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))


if __name__ == "__main__":
    unittest.main()
