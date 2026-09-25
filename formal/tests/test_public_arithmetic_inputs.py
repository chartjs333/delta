"""Checked-source reproduction and field inventory; not a TLA refinement proof."""

import copy
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_arithmetic_inputs_lean as g  # noqa: E402
from formal_artifacts import load_json_strict, write_canonical_json  # noqa: E402


def record_fields(source):
    body = source.split("ZeroArithmeticInputs ==", 1)[1]
    start = body.index("[")
    depth, names = 0, []
    for index in range(start, len(body)):
        char = body[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return names
        if depth == 1 and (index == start + 1 or body[index - 1] in ",\n "):
            match = re.match(r"([A-Za-z][A-Za-z0-9]*)\s*\|->", body[index:])
            if match:
                names.append(match[1])
    raise ValueError("INCOMPLETE_INPUT_RECORD")


class PublicArithmeticInputsTests(unittest.TestCase):
    def test_exact_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "Inputs.lean"
            g.generate(target)
            self.assertEqual(target.read_bytes(), g.TARGET.read_bytes())
            self.assertNotIn(b"\r", target.read_bytes())

    def test_substituted_native_source_rejected_before_output(self):
        document = copy.deepcopy(load_json_strict(g.SOURCE))
        artifact = next(iter(document["artifacts"]))
        document["artifacts"][artifact] += " "
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "source.json", Path(directory) / "out.lean"
            write_canonical_json(source, document)
            with self.assertRaises(ValueError):
                g.generate(target, source)
            self.assertFalse(target.exists())

    def test_complete_production_input_inventory(self):
        tla = (ROOT / "formal/tla/DeltaReduceArithmetic.tla").read_text(encoding="utf-8")
        production = record_fields(tla)
        lean = (ROOT / "formal/proofs/DeltaReduce/PublicArithmeticInputs.lean").read_text(
            encoding="utf-8"
        )
        names = re.findall(r'"(\w+)"', lean.split("def fieldNames", 1)[1].split("]", 1)[0])
        fixture = list(g.fields(g.derive(g.SOURCE)["inputs"]))
        self.assertEqual(len(production), 23)
        self.assertEqual(names, sorted(production))
        self.assertEqual(names, fixture)
        self.assertNotEqual(names, sorted(record_fields(tla.replace("weightD |->", "wrongD |->"))))

    def test_every_new_declaration_is_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "NativeInputProjection",
            "NativeInputProjectionVectors",
            "PublicArithmeticInputs",
            "PublicArithmeticInputsVectors",
        ]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(
                r"^(?:noncomputable )?(?:def|abbrev|theorem) ([\w.]+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
