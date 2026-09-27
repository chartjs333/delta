"""Original plan provenance and partition checks, separate from hash proofs."""

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
import generate_native_shard_plan as vectors  # noqa: E402
from generate_native_source_artifacts import fixture_store  # noqa: E402
from native_source_artifacts import (  # noqa: E402
    Resolver,
    SourceError,
    canonical,
    resolve_q_source,
)


class NativeShardPlanTests(unittest.TestCase):
    def test_original_bytes_domain_and_five_slots(self):
        store, golden, _ = fixture_store()
        doc = json.loads(vectors.TARGET.read_bytes())
        raw = store[golden["manifest"]["value"]["shard_plan_id"]]
        self.assertEqual(len(raw), 1079)
        self.assertEqual(bytes.fromhex(doc["plan_bytes_hex"]), raw)
        self.assertEqual(canonical(doc["plan"]), raw)
        expected = "sha256:" + hashlib.sha256(b"deltareduce.004.shard-plan.v1\0" + raw).hexdigest()
        self.assertEqual(doc["plan_id"], expected)
        self.assertNotEqual(expected, "sha256:" + hashlib.sha256(raw).hexdigest())
        rows = doc["plan"]["entries"]
        self.assertEqual([e["element_start"] for e in rows], [0, 4, 12, 20, 28])
        self.assertEqual([e["element_count"] for e in rows], [4, 8, 8, 8, 8])
        self.assertEqual(sum(e["payload_bytes"] for e in rows), 72)

    def test_original_plan_substitution_rejected_before_generation(self):
        store, golden, other = fixture_store()
        identity = golden["manifest"]["value"]["shard_plan_id"]
        doc = json.loads(store[identity])
        doc["entries"][1]["element_start"] += 1
        store[identity] = canonical(doc)
        before = {p: p.read_bytes() for p in [vectors.LEAN, vectors.TARGET]}
        with patch.object(vectors, "fixture_store", return_value=(store, golden, other)):
            with self.assertRaisesRegex(SourceError, "SOURCE_HASH"):
                vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_full_partition_mutations_after_document_resolution(self):
        # Deliberately bypass only plan document resolution, to exercise the
        # subsequent partition relation independently of content-ID rejection.
        store, golden, _ = fixture_store()
        identity = golden["manifest"]["content_id"]
        original = Resolver.document
        mutations = [
            lambda d: d["entries"].pop(),
            lambda d: d["entries"].append(copy.deepcopy(d["entries"][0])),
            lambda d: d["entries"].reverse(),
        ]
        for key in ["element_start", "element_count", "ordinal", "payload_bytes", "segment_offset"]:
            mutations.append(lambda d, k=key: d["entries"][1].update({k: d["entries"][1][k] + 1}))
        mutations.append(lambda d: d["entries"][1].update(segment_id="wrong"))
        for mutate in mutations:

            def substituted(resolver, content_id, kind, mutate=mutate):
                doc = original(resolver, content_id, kind)
                if kind == "plan":
                    doc = copy.deepcopy(doc)
                    mutate(doc)
                return doc

            with patch.object(Resolver, "document", substituted):
                with self.assertRaisesRegex(SourceError, "PLAN_PARTITION"):
                    resolve_q_source(store, identity)

    def test_missing_plan_not_reconstructed_as_original(self):
        store, golden, _ = fixture_store()
        del store[golden["manifest"]["value"]["shard_plan_id"]]
        with self.assertRaisesRegex(SourceError, "MISSING_PREIMAGE"):
            resolve_q_source(store, golden["manifest"]["content_id"])

    def test_generator_is_byte_exact(self):
        before = {p: p.read_bytes() for p in [vectors.LEAN, vectors.TARGET]}
        vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_kernel_limits_are_not_authority(self):
        doc = json.loads(vectors.TARGET.read_bytes())
        for key in [
            "formal_go",
            "native_execution",
            "native_recovery_proved",
            "hash_adapter_authenticated",
            "manifest_admission_proved",
        ]:
            self.assertFalse(doc[key])
        self.assertIn("changedPayloadStillJoins", doc["small_kernel_cases"])
        self.assertEqual(len(doc["small_kernel_cases"]), 23)

    def test_mandatory_modules_and_axiom_inventory(self):
        root = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for name in [
            "NativeShardPartition",
            "NativeShardPlanBytes",
            "NativeShardPlanBinding",
            "NativeShardPlanVectors",
        ]:
            self.assertIn("import DeltaReduce." + name, root)
            source = (ROOT / f"formal/proofs/DeltaReduce/{name}.lean").read_text(encoding="utf-8")
            for decl in re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + name + "." + decl + "\n", audit)
            self.assertNotIn("native_decide", source)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)


if __name__ == "__main__":
    unittest.main()
