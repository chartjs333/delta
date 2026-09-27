"""Independent signed64 boundary checks and complete kernel audit inventory."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class NativeCurrentHistoryTests(unittest.TestCase):
    def test_decimal_boundary_cases_against_independent_integer_oracle(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativeCurrentHistoryVectors.lean").read_text(
            encoding="utf-8"
        )
        cases = re.findall(
            r'theorem (\w+) : readNumber \(asciiBytes "([^"]*)"\) = (.+?) := by decide',
            source,
        )
        self.assertEqual(len(cases), 9)
        results = {"some 0": 0, "some (-101)": -101, "some minInput": -(2**63)}
        results["some maxInput"] = 2**63 - 1
        for name, raw, expected in cases:
            with self.subTest(name=name):
                number = int(raw)
                accepted = -(2**63) <= number < 2**63 and str(number) == raw
                self.assertEqual(accepted, expected != "none")
                if accepted:
                    self.assertEqual(number, results[expected])
        # These aliases remain accepted by the old native parser. Canonical
        # round-trip rejection is an additional projection restriction.
        for raw in ("-00", "-01"):
            self.assertNotEqual(str(int(raw)), raw)

    def test_all_named_declarations_imported_and_axiom_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "NativeCurrentValues",
            "NativeCurrentHistory",
            "NativeCurrentHistoryVectors",
        ]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
