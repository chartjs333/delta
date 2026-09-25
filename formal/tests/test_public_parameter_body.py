"""Cross-source body inventory and kernel-audit coverage, not TLA admission."""

import re
import unittest

from test_public_arithmetic_inputs import ROOT
from test_public_authority import production_fields


class PublicParameterBodyTests(unittest.TestCase):
    def test_complete_parameter_inventory_against_production(self):
        tla = (ROOT / "formal/tla/DeltaReduceReduceApply.tla").read_text(encoding="utf-8")
        lean = (ROOT / "formal/proofs/DeltaReduce/PublicParameterBody.lean").read_text(
            encoding="utf-8"
        )
        names = re.findall(r'"(\w+)"', lean.split("def parameterFieldNames", 1)[1].split("]", 1)[0])
        self.assertEqual(names, production_fields(tla, "ParameterResultBody(apc, domain, shard"))
        self.assertEqual(len(names), 15)
        self.assertNotEqual(
            names,
            production_fields(
                tla.replace("authority |->", "omittedAuthority |->"),
                "ParameterResultBody(apc, domain, shard",
            ),
        )

    def test_both_production_bound_conventions_are_distinct(self):
        arithmetic = (ROOT / "formal/tla/DeltaReduceArithmetic.tla").read_text(encoding="utf-8")
        reduce = (ROOT / "formal/tla/DeltaReduceReduceApply.tla").read_text(encoding="utf-8")
        arithmetic_guard = arithmetic.split("ABInRange(value) ==", 1)[1].split("RECURSIVE", 1)[0]
        result_guard = reduce.split("CheckedParameterValue(value) ==", 1)[1].split(
            "TicketMatchesParameterContext", 1
        )[0]
        self.assertIn("-NativeArithmeticInputs.limit - 1 <= value", arithmetic_guard)
        self.assertIn("-AccumulatorBound <= value", result_guard)
        self.assertNotIn("-AccumulatorBound - 1", result_guard)

    def test_new_modules_imported_and_every_declaration_audited(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in ["PublicParameterBody", "PublicParameterJoin", "PublicParameterBodyVectors"]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            self.assertIn(f"import DeltaReduce.{module}\n", project)
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
