"""Original seven-list ABORT source contract and checked proof inventory."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_failure as failure  # noqa: E402
import native_policy_codec as codec  # noqa: E402

MODULES = (
    "NativeFinalizedLookup",
    "NativeAbortLineage",
    "PublicAbortAncestors",
    "PublicAbortLineageVectors",
)


class AbortLineageTests(unittest.TestCase):
    def test_original_abort_lists_match_full_snapshot_contract(self):
        policy, body, _, _ = failure.source()[1]
        snapshot_fields = (
            "finalized_round_config_ids",
            "finalized_input_set_ids",
            "finalized_eligibility_ids",
            "finalized_aggregation_plan_ids",
            "finalized_parameter_ids",
            "finalized_aggregate_root_ids",
            "finalized_apply_ids",
        )
        schema = dict(codec.SCHEMAS["snapshot"])
        for body_key, snapshot_key in zip(failure.LIST_FIELDS, snapshot_fields, strict=True):
            self.assertIn(snapshot_key, schema)
            self.assertEqual(body[body_key], policy["snapshot"][snapshot_key])
        self.assertEqual(body["apply_ids"], [])
        self.assertTrue(body["round_config_ids"])
        # The original capture has no nonempty downstream ABORT lineage.
        self.assertTrue(all(body[key] == [] for key in failure.LIST_FIELDS[1:]))
        self.assertNotIn("round_config_certificates", schema)

    def test_general_declarations_audited_and_partial_projection_explicit(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
        source = (ROOT / "formal/proofs/DeltaReduce/PublicAbortAncestors.lean").read_text("utf-8")
        for required in (
            "NativeAbortLineage.load",
            "loadIscBody",
            "loadEcBody",
            "loadApcBody",
            "arithmeticPayloadsRetained",
            "applyAbsenceDerived",
        ):
            self.assertIn(required, source)
        self.assertNotIn("NativeRootSource.loadRoot", source)
        self.assertNotIn("emptyLineageValue", source)
        self.assertNotRegex(source, r"def (?:Image\.)?vote\b")


if __name__ == "__main__":
    unittest.main()
