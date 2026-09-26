"""Exact original native EC components and source-scoped membership guards."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_eligibility as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class EligibilityTests(unittest.TestCase):
    def test_generated_bytes(self):
        self.assertEqual(generator.generate().encode("utf-8"), generator.TARGET.read_bytes())

    def test_rehashed_original_ec_substitutions_reject(self):
        anchors = generator.normgen.source()
        original = generator.normgen.isc.native.fixture()
        for field, value in [
            ("entries", []),
            ("norm_evidence_id", "sha256:" + "a" * 64),
            ("input_set_certificate_id", anchors[4]["bodies"]["ISC"]),
            ("robust_profile_id", "sha256:" + "b" * 64),
            ("quorum_threshold", 2),
            ("signer_ids", ["validator-1"]),
            (
                "entries",
                [
                    {
                        "accepted": False,
                        "domain_id": "domain-a",
                        "gamma": {"denominator": 1, "numerator": "1"},
                        "reason_code": "ACCEPTED",
                        "ticket_id": "ticket-a",
                    }
                ],
            ),
            (
                "entries",
                [
                    {
                        "accepted": True,
                        "domain_id": "domain-a",
                        "gamma": {"denominator": 1, "numerator": "-1"},
                        "reason_code": "ACCEPTED",
                        "ticket_id": "ticket-a",
                    }
                ],
            ),
        ]:
            changed = copy.deepcopy(original)
            changed[0]["EC"][field] = value
            with (
                self.subTest(field=field, value=value),
                patch.object(generator.normgen, "source", return_value=anchors),
                patch.object(generator.normgen.isc.native, "fixture", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_original_policy_pin_rejects(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        for name in ["codec-EC", "codec-APC"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == name)
            row["policy_hex"] = row["policy_hex"][:-2] + "ff"
            with (
                self.subTest(name=name),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_complete_field_inventory_and_native_ids(self):
        doc, tree, proposed, final, docs, _, observed = generator.source()
        text = (ROOT / "formal/proofs/DeltaReduce/NativeEligibility.lean").read_text("utf-8")
        fields = text.split("def fields ", 1)[1].split("def json ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', fields), sorted(doc))
        self.assertEqual(len(doc), 16)
        self.assertNotIn("seed_transcript_id", doc)
        self.assertEqual(content_id(doc), observed["certificates"]["EC"]["id"])
        self.assertEqual(proposed["seed_transcript_id"], content_id(docs["SEED"]))
        self.assertEqual(final["seed_transcript_id"], proposed["seed_transcript_id"])
        self.assertEqual(tree["entries"][0]["gamma"]["numerator"], 1)
        self.assertEqual(doc["entries"][0]["gamma"]["numerator"], "1")

    def test_native_parent_asymmetry_is_explicit(self):
        text = (ROOT / "formal/proofs/DeltaReduce/NativeEligibilityLineage.lean").read_text("utf-8")
        guard = text.split("def NativeParentChecks ", 1)[1].split("instance ", 1)[0]
        self.assertIn("mode = .proposed → norm.evidence.isc = parent.qcId", guard)
        self.assertIn("seed.transcript.isc = parent.qcId", guard)
        vectors = generator.TARGET.read_text("utf-8")
        self.assertIn("finalizedDoesNotRepeatNormEquality", vectors)
        self.assertIn("proposedNormEqualityRequired", vectors)
        self.assertIn("decisionsNotDerived", vectors)

    def test_integer_gamma_preserves_wire_type(self):
        text = (ROOT / "formal/proofs/DeltaReduce/NativeEligibility.lean").read_text("utf-8")
        guard = text.split("def EntryValid ", 1)[1].split("instance ", 1)[0]
        self.assertIn("e.numerator < 2^63", guard)
        self.assertIn("Nat.gcd e.numerator e.denominator = 1", guard)
        self.assertNotIn("NativeCertificateDecimal", guard)
        self.assertIn('("numerator",quoted (number e.numerator))', text)
        self.assertIn("be 8 e.numerator ++ be 8 e.denominator", text)

    def test_all_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in [
            "NativeEligibility",
            "NativeEligibilityLineage",
            "NativeEligibilitySection",
            "NativeEligibilityVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            text = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", text, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
