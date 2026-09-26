"""Native spelling counterexamples must remain visible and source-bound."""

import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))

import check_native_certificate_decimal as native  # noqa: E402
import generate_native_certificate_decimal as generator  # noqa: E402
import native_certificate_chain as proposal  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class CertificateDecimalTests(unittest.TestCase):
    def test_retained_source_and_native_outputs(self):
        document = load_json_strict(native.RESULT)
        self.assertEqual(native.verify_document(document), document)
        rows = native.parse_output((native.FOLDER / "native-output.txt").read_text("ascii"))
        self.assertEqual(rows, document["rows"])
        self.assertEqual(len(rows), 62)
        self.assertEqual((native.FOLDER / "harness.cpp").read_bytes(), native.harness().encode())

    def test_complete_lean_regeneration(self):
        self.assertEqual(generator.TARGET.read_bytes(), generator.generate().encode())

    def test_actual_spelling_gap_is_not_silently_normalized(self):
        rows = native.expected_rows()
        gaps = [r for r in rows if r["accepted"] and not r["strict_proposal_accepts"]]
        self.assertEqual(len(gaps), 9)
        for kind in ["NORM", "PARAMETER"]:
            variants = [
                next(r for r in rows if r["kind"] == kind and r["input_hex"] == raw.hex())
                for raw in [b"0", b"-00", b"-000", b"-" + b"0" * 64]
            ]
            self.assertTrue(all(r["accepted"] for r in variants))
            self.assertEqual(len({r["content_id"] for r in variants}), 4)
            for row in variants:
                doc = load_json_strict_bytes(row)
                text = (
                    doc["entries"][0]["squared_norm"]
                    if kind == "NORM"
                    else doc["result_numerators"][0]
                )
                self.assertEqual(text.encode().hex(), row["input_hex"])
                self.assertEqual(int(text), 0)
        for row in gaps:
            with self.assertRaises(ValueError):
                proposal._decimal(bytes.fromhex(row["input_hex"]).decode(), row["kind"] == "NORM")

    def test_outcome_parser_fails_closed(self):
        lines = (native.FOLDER / "native-output.txt").read_text("ascii").splitlines()
        for stop in range(len(lines)):
            with self.subTest(stop=stop), self.assertRaises(ValueError):
                native.parse_output("\n".join(lines[:stop]))
        changed = [*lines]
        changed[0], changed[1] = changed[1], changed[0]
        for mutation in [changed, [*lines, lines[0]], [lines[0] + "\textra", *lines[1:]]]:
            with self.assertRaises(ValueError):
                native.parse_output("\n".join(mutation))
        for index in [0, 4, 30, 35]:
            modified = [*lines]
            modified[index] = (
                modified[index].replace("ACCEPT", "REJECT").replace("REJECT", "UNKNOWN")
            )
            with self.assertRaises(ValueError):
                native.parse_output("\n".join(modified))

    def test_rehashed_evidence_substitutions_reject(self):
        original = load_json_strict(native.RESULT)
        for field, value in [
            ("source_commit", "0" * 40),
            ("harness_sha256", "0" * 64),
            ("gate_eligible", True),
            ("native_export_authenticated", True),
            ("native_runtime_execution", True),
            ("status", "PASS_CANONICAL_DECIMAL"),
        ]:
            changed = copy.deepcopy(original)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                native.verify_document(changed)
        for index in [0, 4, 35]:
            changed = copy.deepcopy(original)
            changed["rows"][index]["json_hex"] += "00"
            changed["rows"][index]["content_id"] = (
                "sha256:"
                + hashlib.sha256(bytes.fromhex(changed["rows"][index]["json_hex"])).hexdigest()
            )
            with self.assertRaises(ValueError):
                native.verify_document(changed)

    def test_all_named_declarations_are_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in ["NativeCertificateDecimal", "NativeCertificateDecimalVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


def load_json_strict_bytes(row):
    import json

    return json.loads(bytes.fromhex(row["json_hex"]))


if __name__ == "__main__":
    unittest.main()
