"""Independent canonical JSON expectations and mandatory Lean audit coverage."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class NativeIscProjectionTests(unittest.TestCase):
    def test_canonical_encoding_expectations_checked_by_kernel(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativeIscProjectionVectors.lean").read_text(
            encoding="utf-8"
        )
        # Deliberately invalid short IDs: encoding tests, never admitted certificates.
        ref = {"id": "sha256:", "kind": "Q_SHARD", "length": 1}
        leaf = {"q": ref, "shard": "s"}
        commitment = {"domain": "d", "leaves": [leaf], "ticket": "t"}
        expected = {
            "leafEncoding": leaf,
            "commitmentEncoding": commitment,
            "iscEncoding": {
                "kind": "ISC_PROJECTION",
                "payload": {"commitments": [commitment], "members": ["t"]},
            },
            "ecEncoding": {
                "kind": "EC_PROJECTION",
                "payload": {
                    "eligible": ["t"],
                    "isc": {"id": "sha256:", "kind": "ISC_PROJECTION", "length": 2},
                },
            },
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                match = re.search(
                    rf'theorem {name}\b.*?= asciiBytes\s+("(?:\\.|[^"\\])*")',
                    source,
                    re.S,
                )
                self.assertIsNotNone(match)
                literal = json.loads(match[1]).encode()
                self.assertEqual(literal, canonical_json_bytes(value).rstrip(b"\n"))

    def test_all_named_declarations_imported_and_axiom_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in ["NativeIscCorpus", "NativeIscProjection", "NativeIscProjectionVectors"]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
