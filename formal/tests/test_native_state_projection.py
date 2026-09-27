"""Independent complete state/profile JSON encodings and kernel audit inventory."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class NativeStateProjectionTests(unittest.TestCase):
    def test_complete_canonical_encodings(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativeStateProjectionVectors.lean").read_text(
            encoding="utf-8"
        )
        schema = {"id": "sha256:", "kind": "SCHEMA", "length": 1}
        values = {
            "profile": {
                "kind": "PROFILE",
                "payload": {
                    "accumulator_bits": 64,
                    "apply_quantum": [1, 4],
                    "domain_weights": [{"domain": "d1", "weight": [1, 1]}],
                    "learning_rate": [1, 2],
                    "momentum": [1, 2],
                    "nesterov": True,
                    "output_range": "FULL_SIGNED_INT64",
                    "rounding": "HALF_TOWARD_POSITIVE",
                    "weight_decay": [0, 1],
                },
            },
            "model": {
                "kind": "MODEL",
                "payload": {"quantum": [1, 4], "schema": schema, "values": [19, -19]},
            },
            "optimizer": {
                "kind": "OPTIMIZER",
                "payload": {"quantum": [1, 4], "schema": schema, "values": [2, -2]},
            },
        }
        for name, value in values.items():
            with self.subTest(name=name):
                match = re.search(rf"def {name}Bytes : Bytes := (\[[0-9, ]+\])", source)
                self.assertIsNotNone(match)
                self.assertEqual(
                    bytes(json.loads(match[1])),
                    json.dumps(value, sort_keys=True, separators=(",", ":")).encode(),
                )
                self.assertIn(f"theorem {name}Encoding", source)

    def test_all_named_declarations_imported_and_axiom_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "NativeStateArtifacts",
            "NativeStateProjection",
            "NativeStateProjectionVectors",
        ]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(
                r"^(?:def|abbrev|theorem|structure|inductive) (\w+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
