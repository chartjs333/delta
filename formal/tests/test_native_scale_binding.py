"""Retain original scale preimages and the distinction between parsing and trust."""

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
import generate_native_scale_binding as vectors  # noqa: E402
from generate_native_source_artifacts import fixture_store  # noqa: E402
from native_source_artifacts import (  # noqa: E402
    SourceError,
    canonical,
    read_drq1,
    resolve_q_source,
)


class NativeScaleBindingTests(unittest.TestCase):
    def test_original_preimage_quantum_and_every_coordinate(self):
        result = json.loads(vectors.TARGET.read_bytes())
        _, golden, _ = fixture_store()
        raw = bytes.fromhex(golden["scale_table"]["bytes_hex"])
        self.assertEqual(bytes.fromhex(result["scale_bytes_hex"]), raw)
        self.assertEqual(canonical(result["scale_value"]), raw)
        self.assertEqual(len(raw), 643)
        self.assertEqual(
            result["scale_id"],
            "sha256:" + hashlib.sha256(b"deltareduce.004.scale-table.v1\0" + raw).hexdigest(),
        )
        segments = {s["segment_id"]: s for s in result["scale_value"]["segments"]}
        self.assertEqual(len(result["rows"]), 5)
        self.assertEqual(sum(len(row["values"]) for row in result["rows"]), 36)
        for row, original in zip(result["rows"], golden["shards"], strict=True):
            header, values = read_drq1(bytes.fromhex(original["envelope_hex"]))
            segment = segments[header["segment_id"]]
            quantum = segment["quantum"]
            self.assertEqual(row["quantum"], [int(quantum["numerator"]), quantum["denominator"]])
            self.assertEqual(row["values"], list(values))
            self.assertEqual(header["scale_table_id"], result["scale_id"])
            for i in range(len(values)):
                self.assertLess(header["segment_offset"] + i, segment["element_count"])
                self.assertEqual(
                    header["element_start"] + i,
                    segment["element_start"] + header["segment_offset"] + i,
                )

    def test_substituted_scale_preimage_rejects_before_output(self):
        store, golden, other = fixture_store()
        golden["scale_table"]["bytes_hex"] = "7b7d"
        before = {p: p.read_bytes() for p in [vectors.LEAN, vectors.TARGET]}
        with patch.object(vectors, "fixture_store", return_value=(store, golden, other)):
            with self.assertRaisesRegex(SourceError, "ORIGINAL_SCALE_BYTES"):
                vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_source_resolver_requires_original_scale_preimage(self):
        store, golden, _ = fixture_store()
        identity = golden["scale_table"]["content_id"]
        manifest = golden["manifest"]["content_id"]
        del store[identity]
        with self.assertRaises(SourceError):
            resolve_q_source(store, manifest)
        changed = golden["scale_table"]["value"]
        changed["segments"][0]["quantum"]["numerator"] = "3"
        store[identity] = canonical(changed)
        with self.assertRaises(SourceError):
            resolve_q_source(store, manifest)

    def test_parsed_quantum_does_not_authenticate_payload_or_source(self):
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
            "schema_plan_source_binding_proved",
            "loaded_row_composition_proved",
            "native_recovery_proved",
        ]:
            self.assertFalse(result[flag])
        self.assertIn("changedPayloadStillBinds", result["small_kernel_cases"])

    def test_generator_byte_exact(self):
        before = {p: p.read_bytes() for p in [vectors.TARGET, vectors.LEAN]}
        vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_mandatory_build_and_complete_named_axiom_inventory(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeScaleBytes", "NativeScaleBinding", "NativeScaleVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(
                r"^(?:def|theorem|abbrev|structure|inductive) ([\w.]+)", source, re.M
            ):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name + "\n", audit)
            self.assertNotIn("native_decide", source)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)
        self.assertIn("#print axioms DeltaReduce.NativeScaleBinding.Bound.quantum\n", audit)


if __name__ == "__main__":
    unittest.main()
