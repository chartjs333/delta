"""Independent PLAN/APC canonical encodings and explicit kernel audit inventory."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class NativePlanProjectionTests(unittest.TestCase):
    def test_canonical_encoding_expectations_checked_by_kernel(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativePlanProjectionVectors.lean").read_text(
            encoding="utf-8"
        )

        def ref(kind):
            # Deliberately invalid short IDs: byte-encoding cases, not admission.
            return {"id": "sha256:", "kind": kind, "length": 1}

        contribution = {"q": ref("Q_SHARD"), "ticket": "t", "weight": [1, 2]}
        assignment = {
            "context": "c",
            "contributions": [contribution],
            "denominator": 2,
            "domain": "d",
            "quantum": [1, 16],
            "shard": "s",
        }
        expected = {
            "contribution": contribution,
            "assignment": assignment,
            "plan": {
                "kind": "PLAN",
                "payload": {
                    "assignments": [assignment],
                    "profile": ref("PROFILE"),
                    "schema": ref("SCHEMA"),
                    "tickets": [{"domain": "d", "id": "t"}],
                },
            },
            "apc": {
                "kind": "APC_PROJECTION",
                "payload": {"ec": ref("EC_PROJECTION"), "plan": ref("PLAN")},
            },
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                match = re.search(rf"def {name}Bytes : Bytes := (\[[0-9, ]+\])", source)
                self.assertIsNotNone(match)
                self.assertEqual(
                    bytes(json.loads(match[1])), canonical_json_bytes(value).rstrip(b"\n")
                )
                self.assertRegex(source, rf"theorem {name}Encoding\b.*= {name}Bytes := by decide")

    def test_all_named_declarations_imported_and_axiom_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "NativePlanAssignments",
            "NativePlanProjection",
            "NativePlanProjectionVectors",
        ]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
