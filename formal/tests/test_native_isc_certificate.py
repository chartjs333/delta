"""Source pins and reproduction for the complete native ISC certificate layer."""

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))

import generate_native_isc_certificate as generator  # noqa: E402
from formal_artifacts import canonical_json_bytes, load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class IscCertificateTests(unittest.TestCase):
    def test_exact_generated_native_certificate_components(self):
        self.assertEqual(generator.generate().encode("utf-8"), generator.TARGET.read_bytes())

    def test_source_and_provenance_substitutions_reject(self):
        original = load_json_strict(generator.native.FOLDER / "cpp-cross-check.json")
        for field in [
            "source_commit",
            "source_sha256",
            "harness_sha256",
            "extracted_definitions",
            "native_export_authenticated",
            "gate_eligible",
        ]:
            changed = copy.deepcopy(original)
            changed[field] = "substituted"
            with (
                self.subTest(field=field),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_rehashed_observed_certificate_substitution_rejects(self):
        original = load_json_strict(generator.native.FOLDER / "cpp-cross-check.json")
        for field in ["certificates", "bodies", "alternate_signer_qc"]:
            changed = copy.deepcopy(original)
            changed["observed"][field] = "substituted"
            changed = json.loads(canonical_json_bytes(changed))
            with (
                self.subTest(field=field),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_original_full_policy_pin_rejects_changed_section(self):
        policy_path = ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        original = load_json_strict(policy_path)
        for suffix in ["", "ff"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == "codec-EC")
            row["policy_hex"] = row["policy_hex"][:-2] + suffix

            def read(path, changed=changed):
                return changed if path == policy_path else load_json_strict(path)

            with self.subTest(suffix=suffix), patch.object(generator, "load_json_strict", read):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_full_canonical_field_and_identity_inventory(self):
        cert, _, _, observed = generator.source()
        source = (ROOT / "formal/proofs/DeltaReduce/NativeIscCertificate.lean").read_text("utf-8")
        fields = source.split("def fields ", 1)[1].split("def json ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', fields), sorted(cert))
        self.assertEqual(len(cert), 14)
        self.assertEqual(content_id(cert), observed["certificates"]["ISC"]["id"])
        self.assertNotEqual(content_id(cert), observed["bodies"]["ISC"])
        self.assertEqual(
            hashlib.sha256(
                generator.native_isc_body.DOMAIN
                + generator.native.isc.cases()["pinned-vote-fixture"].encode()
            ).hexdigest(),
            observed["bodies"]["ISC"].removeprefix("sha256:"),
        )

    def test_all_named_declarations_are_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in [
            "NativeIscCertificate",
            "NativeFinalizedIscSection",
            "NativeIscCertificateVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
