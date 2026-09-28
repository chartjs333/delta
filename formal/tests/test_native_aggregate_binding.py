"""Independent complete aggregate encoding and explicit Lean audit inventory."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = ["NativeCertifiedCorpus", "NativeAggregateBinding", "NativeAggregateBindingVectors"]


class NativeAggregateBindingTests(unittest.TestCase):
    def test_complete_canonical_aggregate(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativeAggregateBindingVectors.lean").read_text(
            encoding="utf-8"
        )
        parts = {}
        for name in ["parameterBytes", "headerBytes", "authorityBytes", "parameterField"]:
            match = re.search(rf"def {name} : Bytes := (\[[0-9, ]+\])", source)
            self.assertIsNotNone(match)
            parts[name] = bytes(json.loads(match[1]))
        body = {
            "kind": "PARAMETER_EXPECTED",
            "authority_id": "sha256:" + "00" * 32,
            "context": "c",
            "domain": "d",
            "shard": "s0000000000",
            "denominator": 2,
            "numerators": [3, -1],
            "input_leaf_ids": ["sha256:" + "01" * 32],
        }
        self.assertEqual(
            parts["parameterBytes"],
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode(),
        )
        expression = source.split("def aggregateBytes : Bytes :=", 1)[1].split(
            "theorem aggregateCanonical", 1
        )[0]
        raw = b"".join(
            bytes(json.loads(x.strip())) if x.strip().startswith("[") else parts[x.strip()]
            for x in expression.strip().split("++")
        )
        value = {
            "kind": "AGGREGATE_PROJECTION",
            "payload": {"authority_id": body["authority_id"], "parameters": [body]},
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
