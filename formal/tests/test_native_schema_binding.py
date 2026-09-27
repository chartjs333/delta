"""Original schema/source identity and honest kernel projection boundaries."""

import copy
import hashlib
import json
import re
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_schema_binding as vectors  # noqa: E402
from generate_native_source_artifacts import fixture_store  # noqa: E402
from native_source_artifacts import (  # noqa: E402
    SourceError,
    canonical,
    read_drq1,
    resolve_q_source,
    schema_segments,
)


class NativeSchemaBindingTests(unittest.TestCase):
    def test_original_schema_preimage_and_included_segments(self):
        result = json.loads(vectors.TARGET.read_bytes())
        store, golden, _ = fixture_store()
        identity = golden["manifest"]["value"]["parameter_schema_id"]
        raw = store[identity]
        self.assertEqual(len(raw), 376)
        self.assertEqual(bytes.fromhex(result["schema_bytes_hex"]), raw)
        self.assertEqual(result["schema_id"], "sha256:" + hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(
            result["schema_id"], "sha256:" + hashlib.sha256(b"\0" + raw).hexdigest()
        )
        self.assertEqual(canonical(result["schema_value"]), raw)
        self.assertEqual(schema_segments(result["schema_value"]), result["segments"])
        self.assertEqual(len(result["schema_value"]["parameters"]), 3)
        self.assertEqual(len(result["segments"]), 2)
        self.assertEqual(
            result["schema_value"]["tied_aliases"], {"lm_head.weight": "embedding.weight"}
        )
        self.assertEqual(sum(len(row["values"]) for row in result["rows"]), 36)

    def test_policy_shapes_aliases_and_name_boundary(self):
        doc = json.loads(vectors.TARGET.read_bytes())["schema_value"]
        include = copy.deepcopy(doc)
        include["frozen_omission_policy"] = "INCLUDE_ALL"
        self.assertEqual(
            schema_segments(include)[-1],
            {
                "segment_id": "frozen.scale",
                "element_start": 36,
                "element_count": 1,
                "segment_ordinal": 2,
            },
        )
        for mutate in [
            lambda d: d["parameters"][0].update(shape=[0]),
            lambda d: d["parameters"][0].update(shape=[1073741824, 2]),
            lambda d: d["tied_aliases"].update({"head": "absent"}),
            lambda d: d["tied_aliases"].update({"decoder.bias": "embedding.weight"}),
            lambda d: d["parameters"].reverse(),
        ]:
            changed = copy.deepcopy(doc)
            mutate(changed)
            with self.assertRaises(SourceError):
                schema_segments(changed)
        boundary = copy.deepcopy(doc)
        boundary["parameters"][0].update(name="A" * 256)
        with self.assertRaisesRegex(SourceError, "ASCII_TOKEN"):
            schema_segments(boundary)
        boundary["parameters"][0]["trainable"] = False
        self.assertEqual(len(schema_segments(boundary)), 1)

    def test_source_substitution_rejects_before_generator_output(self):
        store, golden, other = fixture_store()
        identity = golden["manifest"]["value"]["parameter_schema_id"]
        changed = json.loads(store[identity])
        changed["parameters"][0]["shape"] = [2, 2]
        store[identity] = canonical(changed)
        before = {p: p.read_bytes() for p in [vectors.LEAN, vectors.TARGET]}
        with patch.object(vectors, "fixture_store", return_value=(store, golden, other)):
            with self.assertRaisesRegex(SourceError, "SOURCE_HASH"):
                vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_missing_schema_is_not_inferred_from_scale_counts(self):
        store, golden, _ = fixture_store()
        del store[golden["manifest"]["value"]["parameter_schema_id"]]
        with self.assertRaisesRegex(SourceError, "MISSING_PREIMAGE"):
            resolve_q_source(store, golden["manifest"]["content_id"])

    def test_complete_schema_does_not_authenticate_q_payload(self):
        _, golden, _ = fixture_store()
        raw = bytearray.fromhex(golden["shards"][0]["envelope_hex"])
        size = struct.unpack("<I", raw[8:12])[0]
        raw[16 + size] = 2
        with self.assertRaisesRegex(SourceError, "PAYLOAD_HASH"):
            read_drq1(bytes(raw))
        result = json.loads(vectors.TARGET.read_bytes())
        for flag in [
            "formal_go",
            "native_execution",
            "sha_implementation_proved",
            "hash_adapter_authenticated",
            "plan_manifest_admission_proved",
            "loaded_row_composition_proved",
            "native_recovery_proved",
        ]:
            self.assertFalse(result[flag])
        self.assertIn("changedPayloadStillJoins", result["small_kernel_cases"])

    def test_generator_byte_exact(self):
        before = {p: p.read_bytes() for p in [vectors.TARGET, vectors.LEAN]}
        vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_mandatory_build_and_dotted_declaration_audit(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in [
            "NativeJsonSequence",
            "NativeSchemaBytes",
            "NativeSchemaBinding",
            "NativeSchemaVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(
                r"^(?:def|theorem|abbrev|structure|inductive) ([\w.]+)", source, re.M
            ):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name + "\n", audit)
            self.assertNotIn("native_decide", source)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)
        self.assertIn("#print axioms DeltaReduce.NativeSchemaBinding.Tensor.count\n", audit)


if __name__ == "__main__":
    unittest.main()
