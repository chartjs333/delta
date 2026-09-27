"""Independent authority JSON encoding and explicit Lean audit inventory."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = [
    "NativeGraphClosure",
    "NativeAuthorityProjection",
    "NativeBindingConstruction",
    "NativeBindingConstructionVectors",
]


class NativeBindingConstructionTests(unittest.TestCase):
    def test_complete_canonical_authority(self):
        source = (
            ROOT / "formal/proofs/DeltaReduce/NativeBindingConstructionVectors.lean"
        ).read_text(encoding="utf-8")
        expected = {
            "context": {
                "round": "r",
                "height": 1,
                "view": 0,
                "epoch": "e",
                "hard_deadline": 100,
                "parent_checkpoint": "parent",
            }
        }
        for name, number, kind in [
            ("schema", 0, "SCHEMA"),
            ("model", 1, "MODEL"),
            ("optimizer", 2, "OPTIMIZER"),
            ("profile", 3, "PROFILE"),
            ("apc", 4, "APC_PROJECTION"),
            ("ec", 5, "EC_PROJECTION"),
            ("plan", 6, "PLAN"),
            ("isc", 7, "ISC_PROJECTION"),
        ]:
            expected[name] = {
                "id": "sha256:" + bytes([number] * 32).hex(),
                "kind": kind,
                "length": 1,
            }
        components = {}
        for name, value in expected.items():
            match = re.search(rf"def {name}Bytes : Bytes := (\[[0-9, ]+\])", source)
            self.assertIsNotNone(match)
            raw = bytes(json.loads(match[1]))
            self.assertEqual(raw, json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
            self.assertIn(f"theorem {name}Canonical", source)
            components[name + "Bytes"] = raw
        expression = source.split("def authorityBytes : Bytes :=", 1)[1].split(
            "theorem authorityCanonical", 1
        )[0]
        segments = [x.strip() for x in expression.strip().split("++")]
        raw = b"".join(
            bytes(json.loads(x)) if x.startswith("[") else components[x] for x in segments
        )
        value = {
            "kind": "AUTHORITY",
            "payload": {
                "context": expected["context"],
                "schema": expected["schema"],
                "model": expected["model"],
                "optimizer": expected["optimizer"],
                "profile": expected["profile"],
                "plan": expected["plan"],
                "parents": {name: expected[name] for name in ["isc", "ec", "apc"]},
            },
        }
        self.assertEqual(raw, json.dumps(value, sort_keys=True, separators=(",", ":")).encode())

    def test_named_declarations_imported_and_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(
                r"^(?:def|abbrev|theorem|structure|inductive) (\w+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
