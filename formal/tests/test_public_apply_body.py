"""Cross-source aggregate/APPLY inventories and explicit checkpoint convention."""

import re
import unittest

from test_public_arithmetic_inputs import ROOT
from test_public_authority import production_fields


class PublicApplyBodyTests(unittest.TestCase):
    def test_entire_aggregate_and_apply_field_inventories(self):
        tla = (ROOT / "formal/tla/DeltaReduceReduceApply.tla").read_text(encoding="utf-8")
        lean = (ROOT / "formal/proofs/DeltaReduce/PublicApplyBody.lean").read_text(encoding="utf-8")
        for name, operator, count in [
            ("aggregateFieldNames", "AggregateRootBody(apc, leaves)", 12),
            ("applyFieldNames", "ApplyBody(root, parent, applyProfile", 10),
        ]:
            names = re.findall(r'"(\w+)"', lean.split("def " + name, 1)[1].split("]", 1)[0])
            self.assertEqual(names, production_fields(tla, operator))
            self.assertEqual(len(names), count)
        self.assertNotEqual(
            production_fields(tla, "ApplyBody(root, parent, applyProfile"),
            production_fields(
                tla.replace("nextCheckpoint |->", "unboundCheckpoint |->"),
                "ApplyBody(root, parent, applyProfile",
            ),
        )

    def test_checkpoint_convention_is_existing_runtime_check_not_apply_expected_field(self):
        native = (ROOT / "delta-runtime-cpp/src/certificate_runtime.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("command.next_checkpoint_id == apply_qc.next_model_hash", native)
        proposal = (ROOT / "formal/proposals/native_binding.py").read_text(encoding="utf-8")
        self.assertNotIn('"next_checkpoint"', proposal)
        self.assertNotIn('"nextCheckpoint"', proposal)
        tla = (ROOT / "formal/tla/DeltaReduceReduceApply.tla").read_text(encoding="utf-8")
        self.assertIn("body.nextCheckpoint = ExpectedNextCheckpoint", tla)

    def test_new_modules_imported_and_declarations_audited(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "PublicApplyArithmetic",
            "PublicApplyBody",
            "PublicApplyJoin",
            "PublicApplyBodyVectors",
        ]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            self.assertIn(f"import DeltaReduce.{module}\n", project)
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
