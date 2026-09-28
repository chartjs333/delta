"""Retained EC/APC parent identities, full weight keys and public field inventories."""

import copy
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_eligibility as ecgen  # noqa: E402
import generate_native_plan as plangen  # noqa: E402
from native_certificate_chain import content_id, voted_body  # noqa: E402

MODULES = [
    "NativePlanningSource",
    "PublicPlanningBody",
    "PublicPlanningHistory",
    "PublicPlanningBodyVectors",
]


class PublicPlanningBodyTests(unittest.TestCase):
    def test_original_parents_members_and_public_shapes(self):
        ec, _, _, _, docs, _, _ = ecgen.source()
        plan, tree, _, _, _, _ = plangen.source()
        self.assertEqual(plan["input_set_certificate_id"], ec["input_set_certificate_id"])
        self.assertEqual(plan["eligibility_certificate_id"], content_id(ec))
        self.assertEqual(plan["seed_transcript_id"], content_id(docs["SEED"]))
        self.assertEqual(ec["norm_evidence_id"], content_id(docs["NORM"]))
        accepted = [e["ticket_id"] for e in ec["entries"] if e["accepted"]]
        self.assertEqual(accepted, [w["ticket_id"] for w in tree["weights"]])
        self.assertEqual(accepted, [w["ticket_id"] for w in tree["bucket_assignments"]])
        self.assertNotEqual(voted_body(plan)["body_id"], content_id(plan))
        self.assertNotEqual(voted_body(ec, content_id(docs["SEED"]))["body_id"], content_id(ec))
        source = (ROOT / "formal/tla/DeltaReduceCertificates.tla").read_text("utf-8")
        for name, expected in [
            (
                "EligibilityBody(isc, seed, members, evidence)",
                ["isc", "seed", "members", "normEvidence"],
            ),
            (
                "AggregationPlanBody(isc, seed, ec, members, profile)",
                ["isc", "seed", "ec", "members", "coefficientProfile"],
            ),
        ]:
            definition = source.split(name + " ==", 1)[1].split("\n\n", 1)[0]
            self.assertEqual(re.findall(r"(\w+)\s*\|->", definition), expected)

    def test_equal_ticket_sets_do_not_bind_full_plan_weights(self):
        plan, _, _, _, _, _ = plangen.source()
        changed = copy.deepcopy(plan)
        changed["weights"][0]["alpha"]["numerator"] = "5"
        self.assertEqual(
            [w["ticket_id"] for w in changed["weights"]],
            [w["ticket_id"] for w in plan["weights"]],
        )
        self.assertNotEqual(voted_body(changed)["body_id"], voted_body(plan)["body_id"])
        self.assertNotEqual(content_id(changed), content_id(plan))
        self.assertNotIn("coefficientProfile", plan)
        # This is a canonical identity countercheck, not native admission or a QC.

    def test_all_declarations_imported_and_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(
                r"^(?:def|abbrev|theorem|structure|inductive) ([\w.]+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
