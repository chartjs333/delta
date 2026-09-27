"""Full original coordinate/byte inventory and independently hashed draft images."""

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "formal/scripts"))
import generate_native_vector_artifacts_lean as vectors
from formal_artifacts import sha256_file
from native_source_artifacts import SourceError


class NativeVectorArtifactsLeanTests(unittest.TestCase):
    def document(self):
        return json.loads(vectors.TARGET.read_bytes())

    def test_full_bytes_and_hash_domain(self):
        doc = self.document()
        entries = [(doc["schema_bytes"], doc["schema_ref"], "SCHEMA", doc["schema"])]
        entries += [(c["bytes"], c["ref"], "Q_SHARD", c["payload"]) for c in doc["q_cases"]]
        for encoded, ref, kind, payload in entries:
            raw = bytes.fromhex(encoded)
            expected = json.dumps(
                {"kind": kind, "payload": payload}, sort_keys=True, separators=(",", ":")
            ).encode("ascii")
            self.assertEqual(raw, expected)
            self.assertEqual(ref["length"], len(raw))
            self.assertEqual(ref["kind"], kind)
            self.assertEqual(
                ref["id"],
                "sha256:"
                + hashlib.sha256(b"deltareduce.000.arithmetic-binding.draft1\0" + raw).hexdigest(),
            )
            self.assertNotEqual(ref["id"], "sha256:" + hashlib.sha256(raw).hexdigest())

    def test_every_original_coordinate_and_range(self):
        doc = self.document()
        locations = doc["locations"]
        self.assertEqual([r["global_offset"] for r in locations], list(range(36)))
        self.assertEqual([r["flat_offset"] for r in locations], list(range(4)) + list(range(32)))
        self.assertEqual(
            [r["parameter"] for r in locations], ["decoder.bias"] * 4 + ["embedding.weight"] * 32
        )
        covered = []
        for s, case in zip(doc["schema"]["shards"], doc["q_cases"], strict=True):
            covered.extend(range(s["offset"], s["offset"] + s["length"]))
            self.assertEqual(len(case["payload"]["values"]), s["length"])
            self.assertEqual(case["payload"]["shard"], s["id"])
            self.assertEqual(case["payload"]["schema"], doc["schema_ref"])
        self.assertEqual(covered, list(range(36)))
        self.assertEqual(doc["q_cases"][0]["payload"]["values"], [1, -2, 0, 4])
        self.assertEqual(
            [v for c in doc["q_cases"][1:] for v in c["payload"]["values"]], list(range(-16, 16))
        )

    def test_mandatory_kernel_inventory_and_source_entry(self):
        root = (vectors.ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        audit = (vectors.LEAN.parent / "AxiomAudit.lean").read_text(encoding="utf-8")
        for mod in (
            "NativeVectorLayout",
            "NativeVectorArtifacts",
            "NativeVectorJoin",
            "NativeVectorArtifactVectors",
        ):
            self.assertIn("import DeltaReduce." + mod, root)
            source = (vectors.LEAN.parent / (mod + ".lean")).read_text(encoding="utf-8")
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + mod + "." + name, audit)
        join = (vectors.LEAN.parent / "NativeVectorJoin.lean").read_text(encoding="utf-8")
        self.assertIn("let b ← NativeVectorContext.bind", join)
        self.assertIn("match hd : deriveParameter binding", join)
        checks = join.split("def Checks", 1)[1].split("instance", 1)[0]
        self.assertNotIn("numerators", checks)
        self.assertIn("rw [numeratorsDerived r]", join)

    def test_scope_and_component_kernel_inventory(self):
        doc = self.document()
        self.assertEqual(
            doc["source_fixture_sha256"],
            sha256_file(vectors.ROOT / "formal/proposals/native-vector-projection-vectors.json"),
        )
        for field in (
            "formal_go",
            "native_execution",
            "native_export_authenticated",
            "whole_source_join_kernel_example",
        ):
            self.assertFalse(doc[field])
        self.assertEqual(
            doc["kernel_theorems"],
            re.findall(r"^theorem (\w+)", vectors.LEAN.read_text(encoding="utf-8"), re.M),
        )

    def test_generator_byte_exact(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))

    def test_substituted_original_bytes_block_generation(self):
        before = vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()
        with patch.object(
            vectors.original, "source_blobs", side_effect=SourceError("SOURCE_CHANGED")
        ):
            with self.assertRaisesRegex(SourceError, "SOURCE_CHANGED"):
                vectors.generate()
        self.assertEqual(before, (vectors.LEAN.read_bytes(), vectors.TARGET.read_bytes()))


if __name__ == "__main__":
    unittest.main()
