"""Original ROOT parent payloads and general source/primitive agreement audit."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_aggregate as aggregate  # noqa: E402
import generate_native_eligibility as eligibility  # noqa: E402
import generate_native_plan as plan  # noqa: E402
import native_policy_codec as codec  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402

MODULES = (
    "NativeRootParents",
    "PublicParentNames",
    "PublicRootParents",
    "PublicRootParentsVectors",
)


class RootParentTests(unittest.TestCase):
    def test_actual_root_snapshot_contains_same_complete_plan(self):
        capture = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        row = next(r for r in capture["observed"] if r["name"] == "codec-AGGREGATE_ROOT")
        raw = bytes.fromhex(row["policy_hex"])
        policy = codec.decode(raw)
        self.assertEqual(codec.HEADER + codec.encode_value("policy", policy), raw)
        snapshot = policy["snapshot"]
        _, _, root, docs, _, _ = aggregate.source()
        _, original_plan, _, _, _, _ = plan.source()
        self.assertEqual(snapshot["aggregation_plan_certificates"], [original_plan])
        self.assertEqual(root["aggregation_plan_certificate_id"], content_id(docs["APC"]))
        for key, name in (
            ("input_set_certificate_id", "ISC"),
            ("eligibility_certificate_id", "EC"),
        ):
            self.assertEqual(root[key], original_plan[key])
            self.assertEqual(root[key], content_id(docs[name]))
        original_isc = snapshot["input_set_certificates"][0]
        original_ec = snapshot["eligibility_certificates"][0]["certificate"]
        self.assertEqual(original_isc["tuples"], docs["ISC"]["tuples"])
        self.assertEqual(original_ec, eligibility.source()[1])
        self.assertEqual(original_plan["context"], original_isc["context"])
        self.assertEqual(original_plan["context"], original_ec["context"])
        self.assertNotIn("coefficientProfile", original_plan)
        self.assertNotIn("config", original_isc)
        self.assertEqual(snapshot["aggregate_root_qcs"], [])
        self.assertEqual(snapshot["apply_qcs"], [])

    def test_general_source_and_primitive_checks_are_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
        native = (ROOT / "formal/proofs/DeltaReduce/NativeRootParents.lean").read_text("utf-8")
        self.assertIn("NativePlanSection.preparedSource", native)
        self.assertIn("NativeIscProjection.check adapter.sha256 codec store", native)
        self.assertNotIn("NativeIscProjection.join", native)
        self.assertNotIn("NativeVectorAuthority.verify", native)
        public = (ROOT / "formal/proofs/DeltaReduce/PublicRootParents.lean").read_text("utf-8")
        self.assertIn(
            "PublicPlanningBody.loadApcBody original loaded.original root.original.plan", public
        )
        self.assertIn("PublicParentNames.completeEntries authority.entryOrigin", public)
        self.assertIn("PublicParentNames.completeMembers authority.eligible", public)


if __name__ == "__main__":
    unittest.main()
