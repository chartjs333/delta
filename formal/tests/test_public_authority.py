"""Cross-source field inventory and audit coverage, not admission/refinement."""

import re
import unittest

from test_public_arithmetic_inputs import ROOT, record_fields


def production_fields(source, operator):
    body = source.split(operator, 1)[1].split("==", 1)[1]
    return sorted(record_fields("ZeroArithmeticInputs ==" + body))


class PublicAuthorityTests(unittest.TestCase):
    def test_complete_authority_inventory_against_production(self):
        tla = (ROOT / "formal/tla/DeltaReduceReduceApply.tla").read_text(encoding="utf-8")
        lean = (ROOT / "formal/proofs/DeltaReduce/PublicAuthority.lean").read_text(encoding="utf-8")
        names = re.findall(r'"(\w+)"', lean.split("def authorityFieldNames", 1)[1].split("]", 1)[0])
        self.assertEqual(names, production_fields(tla, "NativeArithmeticAuthority(apc)"))
        self.assertEqual(len(names), 10)
        self.assertNotEqual(
            names,
            production_fields(
                tla.replace("optimizer |->", "wrong |->"), "NativeArithmeticAuthority(apc)"
            ),
        )

    def test_complete_parent_constructor_inventories(self):
        tla = (ROOT / "formal/tla/DeltaReduceCertificates.tla").read_text(encoding="utf-8")
        lean = (ROOT / "formal/proofs/DeltaReduce/PublicAuthority.lean").read_text(encoding="utf-8")
        for constructor, operator in [
            ("iscValue", "InputBody(round, config, entries)"),
            ("seedValue", "SeedRecord(isc, value)"),
            ("ecValue", "EligibilityBody(isc, seed, members, evidence)"),
            ("apcValue", "AggregationPlanBody(isc, seed, ec, members, profile)"),
        ]:
            body = lean.split("def " + constructor, 1)[1].split("\ndef ", 1)[0]
            names = re.findall(r'\("(\w+)"\s*,', body)
            self.assertEqual(names, production_fields(tla, operator), constructor)

    def test_all_public_authority_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in ["PublicAuthority", "PublicAuthorityVectors"]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
