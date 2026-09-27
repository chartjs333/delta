"""Complete manifest corpus checks and explicitly unauthenticated hash fixtures."""

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_manifest as vectors  # noqa: E402
from generate_native_source_artifacts import fixture_store  # noqa: E402
from native_source_artifacts import Resolver, SourceError, canonical, resolve_q_source  # noqa: E402


class NativeManifestTests(unittest.TestCase):
    def test_complete_original_manifest_corpus_and_totals(self):
        store, golden, _ = fixture_store()
        doc = json.loads(vectors.TARGET.read_bytes())
        raw = store[golden["manifest"]["content_id"]]
        self.assertEqual(len(raw), 2198)
        self.assertEqual(bytes.fromhex(doc["manifest_bytes_hex"]), raw)
        self.assertEqual(canonical(doc["manifest"]), raw)
        manifest = doc["manifest"]
        self.assertEqual(len(manifest), 18)
        self.assertEqual(len(manifest["shards"]), 5)
        self.assertEqual(sum(len(store[r["leaf_id"]]) for r in manifest["shards"]), 4798)
        self.assertEqual(sum(r["payload_bytes"] for r in manifest["shards"]), 72)
        self.assertEqual(sum(r["element_count"] for r in manifest["shards"]), 36)
        expected = "sha256:" + hashlib.sha256(b"deltareduce.004.manifest.v1\0" + raw).hexdigest()
        self.assertEqual(doc["manifest_id"], expected)

    def test_every_finite_hash_preimage_matches_real_sha_but_is_not_authority(self):
        doc = json.loads(vectors.TARGET.read_bytes())
        for row in doc["synthetic_hash_preimages"]:
            self.assertEqual(
                "sha256:" + hashlib.sha256(bytes.fromhex(row["bytes_hex"])).hexdigest(),
                row["content_id"],
            )
        for key in [
            "formal_go",
            "native_execution",
            "native_recovery_proved",
            "hash_adapter_authenticated",
            "manifest_authority_proved",
        ]:
            self.assertFalse(doc[key])
        self.assertTrue(doc["missing_parent_preimage"])

    def test_merkle_uses_raw_ordered_digests_and_duplicates_odd_tail(self):
        doc = json.loads(vectors.TARGET.read_bytes())
        leaves = [bytes.fromhex(r["leaf_id"][7:]) for r in doc["manifest"]["shards"]]

        def merkle(nodes):
            while len(nodes) > 1:
                if len(nodes) % 2:
                    nodes = [*nodes, nodes[-1]]
                nodes = [
                    hashlib.sha256(b"deltareduce.004.merkle-node.v1\0" + a + b).digest()
                    for a, b in zip(nodes[::2], nodes[1::2], strict=True)
                ]
            return "sha256:" + nodes[0].hex()

        self.assertEqual(merkle(leaves), doc["manifest"]["commitment_root"])
        self.assertNotEqual(merkle(leaves[::-1]), doc["manifest"]["commitment_root"])
        self.assertNotEqual(
            merkle([r["leaf_id"].encode() for r in doc["manifest"]["shards"]]),
            doc["manifest"]["commitment_root"],
        )

    def test_manifest_mutations_after_document_resolution(self):
        # Bypass ONLY the resolved document to reach structural checks; these
        # substitutions are not claimed to preserve the original content ID.
        store, golden, _ = fixture_store()
        original = Resolver.document
        mutations = [
            (lambda d: d["shards"].pop(), "LEAF_COVERAGE"),
            (lambda d: d["shards"].append(copy.deepcopy(d["shards"][0])), "LEAF_COVERAGE"),
            (lambda d: d["shards"].reverse(), "MANIFEST_RANGE"),
            (lambda d: d["shards"][0].update(element_start=1), "MANIFEST_RANGE"),
            (lambda d: d["shards"][0].update(envelope_bytes=950), "LEAF_LENGTH"),
            (lambda d: d.update(total_envelope_bytes=4799), "BYTE_TOTALS"),
            (lambda d: d.update(total_payload_bytes=73), "BYTE_TOTALS"),
            (lambda d: d.update(total_elements=35), "ELEMENT_TOTAL"),
            (lambda d: d.update(ticket_id="wrong"), "HEADER_CONTEXT"),
            (lambda d: d.update(commitment_root=d["parent_checkpoint_id"]), "MERKLE_ROOT"),
            (lambda d: d.update(aggregation_steps=0), "INTEGER_RANGE"),
        ]
        for mutate, code in mutations:

            def substituted(resolver, identity, kind, mutate=mutate):
                value = original(resolver, identity, kind)
                if kind == "manifest":
                    value = copy.deepcopy(value)
                    mutate(value)
                return value

            with patch.object(Resolver, "document", substituted):
                with self.assertRaisesRegex(SourceError, code):
                    resolve_q_source(store, golden["manifest"]["content_id"])

    def test_missing_and_substituted_leaf_never_become_complete(self):
        store, golden, _ = fixture_store()
        leaf = golden["manifest"]["value"]["shards"][0]["leaf_id"]
        for replacement in [None, store[leaf][:-1] + b"\x01"]:
            changed = dict(store)
            if replacement is None:
                del changed[leaf]
            else:
                changed[leaf] = replacement
            with self.assertRaisesRegex(SourceError, "MISSING_PREIMAGE|SOURCE_HASH"):
                resolve_q_source(changed, golden["manifest"]["content_id"])

    def test_original_substitution_rejects_before_generator_writes(self):
        store, golden, other = fixture_store()
        identity = golden["manifest"]["content_id"]
        changed = json.loads(store[identity])
        changed["shards"].reverse()
        store[identity] = canonical(changed)
        before = {p: p.read_bytes() for p in [vectors.LEAN, vectors.TARGET]}
        with patch.object(vectors, "fixture_store", return_value=(store, golden, other)):
            with self.assertRaisesRegex(SourceError, "SOURCE_HASH"):
                vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_generator_byte_exact(self):
        before = {p: p.read_bytes() for p in [vectors.LEAN, vectors.TARGET]}
        vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_mandatory_modules_and_axiom_inventory(self):
        root = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for name in [
            "NativeManifestBytes",
            "NativeManifestMerkle",
            "NativeManifestBinding",
            "NativeManifestVectors",
        ]:
            self.assertIn("import DeltaReduce." + name, root)
            source = (ROOT / f"formal/proofs/DeltaReduce/{name}.lean").read_text(encoding="utf-8")
            for decl in re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + name + "." + decl + "\n", audit)
            self.assertNotIn("native_decide", source)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)


if __name__ == "__main__":
    unittest.main()
