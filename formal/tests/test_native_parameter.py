"""Pinned complete PARAMETER representation and original assignment guard scope."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_parameter as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class ParameterTests(unittest.TestCase):
    def test_generated_bytes(self):
        self.assertEqual(generator.generate().encode("utf-8"), generator.TARGET.read_bytes())

    def test_original_body_substitutions_reject(self):
        original = generator.plangen.source()
        for field, value in [
            ("denominator", 7),
            ("result_numerators", ["-01"]),
            ("input_leaf_ids", []),
            ("aggregation_plan_certificate_id", "sha256:" + "a" * 64),
            ("eligibility_certificate_id", "sha256:" + "b" * 64),
            ("input_set_certificate_id", "sha256:" + "c" * 64),
            ("domain_id", "domain-b"),
            ("shard_id", "shard-b"),
            ("quorum_threshold", 2),
            ("signer_ids", ["validator-1"]),
        ]:
            changed = copy.deepcopy(original)
            changed[3]["PARAMETER"][field] = value
            with (
                self.subTest(field=field),
                patch.object(generator.plangen, "source", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_original_policy_pin_rejects(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        for name in ["codec-PARAMETER", "codec-AGGREGATE_ROOT"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == name)
            row["policy_hex"] = row["policy_hex"][:-2] + "ff"
            with (
                self.subTest(name=name),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_full_original_fields_and_parents(self):
        doc, tree, proposed, docs, _, observed = generator.source()
        src = (ROOT / "formal/proofs/DeltaReduce/NativeParameter.lean").read_text("utf-8")
        fields = src.split("def fields ", 1)[1].split("def json ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', fields), sorted(doc))
        self.assertEqual(len(doc), 20)
        self.assertEqual(content_id(doc), observed["certificates"]["PARAMETER"]["id"])
        for name, field in [
            ("ISC", "input_set_certificate_id"),
            ("EC", "eligibility_certificate_id"),
            ("APC", "aggregation_plan_certificate_id"),
        ]:
            self.assertEqual(doc[field], content_id(docs[name]))
        self.assertEqual(tree["result_numerators"], doc["result_numerators"])
        self.assertEqual(proposed["result_numerators"], doc["result_numerators"])

    def test_assignment_context_is_retained_but_not_hashed(self):
        doc, _, proposed, _, _, _ = generator.source()
        changed = copy.deepcopy(doc)
        changed["vote_context_id"] = "other-context"
        self.assertEqual(generator.body_bytes(doc), generator.body_bytes(changed))
        self.assertTrue(proposed["vote_context_id"])
        src = (ROOT / "formal/proofs/DeltaReduce/NativeParameter.lean").read_text("utf-8")
        body = src.split("def bodyBytes ", 1)[1].split("def bodyDomain ", 1)[0]
        self.assertNotIn("voteContext", body)
        self.assertIn(
            "b.voteContext", src.split("def bodyValue ", 1)[1].split("def readBody ", 1)[0]
        )
        for name in ["assignmentsDistinct", "distinctAssignment", "contextRetained"]:
            self.assertIn("theorem " + name, src)

    def test_original_signed_spelling_not_normalized(self):
        doc = generator.source()[0]
        raw = copy.deepcopy(doc)
        raw["result_numerators"] = ["-01"]
        normal = copy.deepcopy(raw)
        normal["result_numerators"] = ["-1"]
        self.assertNotEqual(generator.body_bytes(raw), generator.body_bytes(normal))
        self.assertNotEqual(content_id(raw), content_id(normal))
        src = (ROOT / "formal/proofs/DeltaReduce/NativeParameter.lean").read_text("utf-8")
        self.assertIn("NativeCertificateDecimal.Valid false x", src)
        self.assertIn("c.common.numerators.map quoted", src)

    def test_proposed_finalized_scope_and_whole_section(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeParameterLineage.lean").read_text("utf-8")
        for check in [
            "mode = .proposed → ProposedChecks",
            "plan.id ∈ finalizedPlan",
            "plan.certificate.common.isc = parent.qcId",
            "e.accepted ≠ 0 ∧ e.domain = c.domain",
        ]:
            self.assertIn(check, src)
        section = (ROOT / "formal/proofs/DeltaReduce/NativeParameterSection.lean").read_text(
            "utf-8"
        )
        for check in [
            "NativePlanSection.bindSection sha p s",
            '"required_parameter_keys"',
            "NativeParameter.assignments []",
            "NativeParameter.keyLT b.keys",
            "b.certificates.map Edge.id",
        ]:
            self.assertIn(check, section)

    def test_all_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in [
            "NativeParameter",
            "NativeParameterLineage",
            "NativeParameterSection",
            "NativeParameterVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", src, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", src, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
