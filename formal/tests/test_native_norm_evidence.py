"""Original norm wire/JSON and finalized ISC edge, without spelling normalization."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))

import generate_native_norm_evidence as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class NormEvidenceTests(unittest.TestCase):
    def test_exact_generated_bytes_and_proofs(self):
        self.assertEqual(generator.generate().encode("utf-8"), generator.TARGET.read_bytes())

    def test_rehashed_norm_substitution_rejects(self):
        anchors = generator.isc.source()
        original = generator.isc.native.fixture()
        for field, value in [
            ("input_set_certificate_id", anchors[3]["bodies"]["ISC"]),
            ("norm_root", "sha256:" + "a" * 64),
            ("entries", []),
            ("entries", [{"scale_denominator": 2, "squared_norm": "1", "ticket_id": "ticket-a"}]),
            ("entries", [{"scale_denominator": 1, "squared_norm": "-00", "ticket_id": "ticket-a"}]),
            ("entries", [{"scale_denominator": 1, "squared_norm": "1", "ticket_id": "ticket-b"}]),
        ]:
            changed = copy.deepcopy(original)
            changed[0]["NORM"][field] = value
            with (
                self.subTest(field=field, value=value),
                patch.object(generator.isc, "source", return_value=anchors),
                patch.object(generator.isc.native, "fixture", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_full_original_policy_pin_rejects_substitution(self):
        path = ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        original = load_json_strict(path)
        for suffix in ["", "ff"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == "codec-EC")
            row["policy_hex"] = row["policy_hex"][:-2] + suffix
            with (
                self.subTest(suffix=suffix),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_complete_canonical_field_inventory(self):
        norm, tree, certificate, _, observed = generator.source()
        text = (ROOT / "formal/proofs/DeltaReduce/NativeNormEvidence.lean").read_text("utf-8")
        fields = text.split("def fields ", 1)[1].split("def json ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', fields), sorted(norm))
        self.assertEqual(len(norm), 13)
        entry = text.split("def entryJSON ", 1)[1].split("def fields ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', entry), sorted(norm["entries"][0]))
        self.assertEqual(content_id(norm), observed["certificates"]["NORM"]["id"])
        self.assertEqual(norm["input_set_certificate_id"], content_id(certificate))
        self.assertNotEqual(norm["input_set_certificate_id"], observed["bodies"]["ISC"])
        self.assertEqual(tree["entries"], norm["entries"])

    def test_source_projection_does_not_normalize_decimal_spelling(self):
        text = (ROOT / "formal/proofs/DeltaReduce/NativeNormEvidence.lean").read_text("utf-8")
        check = text.split("def EntryValid", 1)[1].split("instance (e)", 1)[0]
        self.assertIn("NativeCertificateDecimal.Valid true e.squared", check)
        entry = text.split("def entryJSON", 1)[1].split("def fields", 1)[0]
        self.assertIn('("squared_norm",quoted e.squared)', entry)
        self.assertNotIn("Int.repr", entry)
        self.assertNotIn("Canonical", check)

    def test_all_named_declarations_are_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in ["NativeNormEvidence", "NativeNormSection", "NativeNormEvidenceVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
