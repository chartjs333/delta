"""Original native bytes and closed-mode Lean replay evidence inventory."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))

import generate_native_mixed_policy as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class MixedLeanTests(unittest.TestCase):
    def test_exact_generated_original_policy_and_hash_components(self):
        expected = (ROOT / "formal/proofs/DeltaReduce/NativeMixedPolicyVectors.lean").read_bytes()
        self.assertEqual(generator.generate().encode("utf-8"), expected)

    def test_untrusted_native_document_rejects(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-proposal-replay/cpp-cross-check.json"
        )
        for field in [
            "source_commit",
            "source_sha256",
            "harness_sha256",
            "native_export_authenticated",
        ]:
            changed = copy.deepcopy(original)
            changed[field] = "substituted"
            with (
                self.subTest(field=field),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.generate()

    def test_original_wal_substitutions_reject_before_generation(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-proposal-replay/cpp-cross-check.json"
        )
        for field in ["wal_hex", "policy_hex", "initial_hex"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == "no-snapshot")
            row[field] = row[field][:-2]
            with (
                self.subTest(field=field),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.generate()

    def test_full_audit_inventory_uses_exact_declarations(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in [
            "NativeReplayAdmission",
            "NativeConfigReplay",
            "NativeConfigReplayVectors",
            "NativeProposalAdmission",
            "NativeMixedPolicyVectors",
            "NativeMixedReplayVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
