"""Retained unchanged-native size observations and mandatory bound-layer coverage."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import check_native_contract_size as size  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class NativeContractSizeTests(unittest.TestCase):
    def test_retained_cpp_boundary(self):
        doc = load_json_strict(size.RESULT)
        self.assertEqual(size.verify_document(doc), doc)
        self.assertEqual(
            size.parse_output((size.FOLDER / "native-output.txt").read_text("ascii")),
            size.expected_rows(),
        )
        self.assertEqual([r["content_id_accepted"] for r in doc["rows"]], [True] * 3 + [False])

    def test_json_and_wire_are_different_bounds(self):
        rows = size.expected_rows()
        self.assertEqual(
            [r["canonical_json_bytes"] for r in rows[1:]],
            [size.LIMIT - 1, size.LIMIT, size.LIMIT + 1],
        )
        for row in rows:
            self.assertLess(row["component_policy_wire_bytes"], size.LIMIT)
            self.assertLess(row["count"], 100000)
        self.assertEqual(rows[-1]["error_code"], 16)

    def test_rehashed_changed_outcome_rejects(self):
        original = load_json_strict(size.RESULT)
        for key, value in [
            ("content_id_accepted", True),
            ("canonical_json_bytes", size.LIMIT),
            ("canonical_json_sha256", "0" * 64),
            ("component_policy_wire_sha256", "0" * 64),
            ("count", 65522),
        ]:
            changed = copy.deepcopy(original)
            changed["rows"][-1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                size.verify_document(changed)

    def test_native_output_is_complete_and_ordered(self):
        raw = (size.FOLDER / "native-output.txt").read_text("ascii")
        lines = raw.splitlines()
        for changed in [lines[:-1], lines[::-1], [*lines, lines[0]]]:
            with self.assertRaises(ValueError):
                size.parse_output("\n".join(changed))

    def test_source_substitution_rejects(self):
        blobs = size.pinned.sources()
        key = "delta-core-cpp/src/certificates/contracts.cpp"
        altered = {**blobs, key: blobs[key] + b"\n"}
        with patch.object(size.pinned, "sources", return_value=altered):
            with self.assertRaises(ValueError):
                size.verify_document(load_json_strict(size.RESULT))

    def test_no_runtime_or_authentication_promotion(self):
        for key in ["native_runtime_execution", "native_export_authenticated", "gate_eligible"]:
            doc = load_json_strict(size.RESULT)
            doc[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                size.verify_document(doc)

    def test_source_constant_and_all_prior_certificate_families(self):
        blobs = size.pinned.sources()
        header = blobs["delta-core-cpp/include/delta/certificates/contracts.hpp"].decode()
        source = blobs["delta-core-cpp/src/certificates/contracts.cpp"].decode()
        self.assertIn("max_contract_bytes = 4U * 1024U * 1024U", header)
        self.assertIn("encoded.size() <= max_contract_bytes", source)
        for name in [
            "InputSetCertificate",
            "SeedTranscript",
            "NormEvidence",
            "EligibilityCertificate",
            "AggregationPlanCertificate",
            "ParameterShardQc",
        ]:
            self.assertRegex(source, r"DELTA_CERTIFICATE_ID\(\s*" + name + r"\s*,")
        lean = (ROOT / "formal/proofs/DeltaReduce/NativeSizedParameterSection.lean").read_text()
        for name in ["ISC", "NORM", "SEED", "EC", "APC", "PARAMETER"]:
            self.assertIn('"' + name, lean)
        self.assertIn("theorem groupLengths", lean)
        self.assertIn("NativeParameterSection.bindSection sha p s", lean)

    def test_all_new_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        for module in [
            "NativeContractSize",
            "NativeSizedParameterSection",
            "NativeContractSizeExamples",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|theorem) (\w+)", src, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", src, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
