"""Pinned seed corpus and complete ISC-edge component reproduction."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))

import generate_native_seed_transcript as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class SeedTranscriptTests(unittest.TestCase):
    def test_exact_generated_bytes_and_proofs(self):
        self.assertEqual(generator.generate().encode("utf-8"), generator.TARGET.read_bytes())

    def test_rehashed_seed_parent_share_profile_substitution_rejects(self):
        anchors = generator.isc.source()
        original = generator.isc.native.fixture()
        for field, value in [
            ("input_set_certificate_id", anchors[3]["bodies"]["ISC"]),
            ("seed_id", "sha256:" + "a" * 64),
            ("seed_profile_id", "sha256:" + "b" * 64),
            ("share_ids", []),
        ]:
            changed = copy.deepcopy(original)
            changed[0]["SEED"][field] = value
            with (
                self.subTest(field=field),
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

    def test_canonical_fields_and_two_distinct_identity_edges(self):
        seed, tree, certificate, _, observed = generator.source()
        text = (ROOT / "formal/proofs/DeltaReduce/NativeSeedTranscript.lean").read_text("utf-8")
        fields = text.split("def fields ", 1)[1].split("def json ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', fields), sorted(seed))
        self.assertEqual(len(seed), 14)
        self.assertEqual(content_id(seed), observed["certificates"]["SEED"]["id"])
        self.assertEqual(seed["input_set_certificate_id"], content_id(certificate))
        self.assertNotEqual(seed["input_set_certificate_id"], observed["bodies"]["ISC"])
        self.assertNotEqual(seed["seed_id"], content_id(seed))
        self.assertEqual(tree["share_ids"], seed["share_ids"])

    def test_all_named_declarations_are_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in ["NativeSeedTranscript", "NativeSeedSection", "NativeSeedTranscriptVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
