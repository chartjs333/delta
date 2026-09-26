"""Original APC source pins, full field coverage and kernel audit inventory."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_plan as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class PlanTests(unittest.TestCase):
    def test_generated_bytes(self):
        self.assertEqual(generator.generate().encode("utf-8"), generator.TARGET.read_bytes())

    def test_rehashed_original_apc_substitutions_reject(self):
        original = generator.ecgen.source()
        for field, value in [
            ("bucket_assignments", []),
            ("weights", []),
            ("iteration_count", 2),
            ("input_set_certificate_id", original[6]["bodies"]["ISC"]),
            ("eligibility_certificate_id", original[6]["bodies"]["EC"]),
            ("seed_transcript_id", "sha256:" + "a" * 64),
            ("accumulator_proof_id", "sha256:" + "b" * 64),
            ("transcript_root", "sha256:" + "c" * 64),
            ("quorum_threshold", 2),
            ("signer_ids", ["validator-1"]),
            ("weights", [{"alpha": {"numerator": "2", "denominator": 1}, "ticket_id": "ticket-a"}]),
        ]:
            changed = copy.deepcopy(original)
            changed[4]["APC"][field] = value
            with (
                self.subTest(field=field),
                patch.object(generator.ecgen, "source", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_original_policy_pin_rejects(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        for name in ["codec-APC", "codec-PARAMETER"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == name)
            row["policy_hex"] = row["policy_hex"][:-2] + "ff"
            with (
                self.subTest(name=name),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_complete_fields_and_original_parent_ids(self):
        doc, tree, proposed, docs, _, observed = generator.source()
        text = (ROOT / "formal/proofs/DeltaReduce/NativePlan.lean").read_text("utf-8")
        fields = text.split("def fields ", 1)[1].split("def json ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', fields), sorted(doc))
        self.assertEqual(len(doc), 20)
        self.assertEqual(content_id(doc), observed["certificates"]["APC"]["id"])
        self.assertEqual(doc["eligibility_certificate_id"], content_id(docs["EC"]))
        self.assertEqual(doc["seed_transcript_id"], content_id(docs["SEED"]))
        self.assertEqual(
            proposed, {k: v for k, v in tree.items() if k not in ["quorum_threshold", "signer_ids"]}
        )
        self.assertIsInstance(tree["weights"][0]["alpha"]["numerator"], int)
        self.assertIsInstance(doc["weights"][0]["alpha"]["numerator"], str)

    def test_actual_parent_guard_scope_is_explicit(self):
        text = (ROOT / "formal/proofs/DeltaReduce/NativePlanLineage.lean").read_text("utf-8")
        guard = text.split("def NativeParentChecks ", 1)[1].split("instance ", 1)[0]
        for check in [
            "parent.qcId ∈ finalizedIsc",
            "ec.id ∈ finalizedEc",
            "ec.seedId = seed.id",
            "c.common.accumulator = required",
            "Coverage c.common ec.certificate",
        ]:
            self.assertIn(check, guard)
        self.assertNotIn("seed.transcript.isc", guard)
        self.assertNotIn("ec.certificate.common.isc", guard)
        vector = generator.TARGET.read_text("utf-8")
        for name in [
            "noRepeatedCrossIscCheck",
            "crossIscActuallyDifferent",
            "bucketAndAlphaNotDerived",
        ]:
            self.assertIn(name, vector)

    def test_ordered_coverage_and_iteration_wire_width(self):
        text = (ROOT / "formal/proofs/DeltaReduce/NativePlan.lean").read_text("utf-8")
        self.assertIn("sortTickets (c.buckets.map Bucket.ticket)", text)
        self.assertIn("c.iterations < 256^4", text)
        self.assertIn("be 8 c.iterations", text)
        self.assertIn("w.numerator < 2^63", text)
        for name in ["selectedCoverage", "reversedAssignmentsInvalid", "rejectedCannotBuildPlan"]:
            self.assertIn(name, generator.TARGET.read_text("utf-8"))
        section = (ROOT / "formal/proofs/DeltaReduce/NativePlanSection.lean").read_text("utf-8")
        self.assertIn("b.bodyTrees ≠ [] \u2228 b.certificateTrees ≠ []", section)
        self.assertIn("NativeEligibilitySection.bindSection sha p s", section)

    def test_all_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in ["NativePlan", "NativePlanLineage", "NativePlanSection", "NativePlanVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            text = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", text, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
