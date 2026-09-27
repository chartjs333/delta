"""Pin original header bytes and retain the separate payload/source authority boundary."""

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
import generate_native_q_header as vectors  # noqa: E402
from generate_native_source_artifacts import fixture_store  # noqa: E402
from native_source_artifacts import SourceError, canonical, read_drq1  # noqa: E402


class NativeQHeaderTests(unittest.TestCase):
    def test_all_original_fields_and_payload_coordinates(self):
        result = json.loads(vectors.TARGET.read_bytes())
        _, golden, _ = fixture_store()
        self.assertEqual(len(result["rows"]), 5)
        for row, original in zip(result["rows"], golden["shards"], strict=True):
            raw = bytes.fromhex(original["envelope_hex"])
            header, values = read_drq1(raw)
            self.assertEqual(row["header"], header)
            self.assertEqual(len(header), 16)
            self.assertEqual(canonical(header).hex(), original["header_bytes_hex"])
            self.assertEqual(row["header_sha256"], hashlib.sha256(canonical(header)).hexdigest())
            self.assertEqual(row["source_frame_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(row["source_leaf_id"], original["leaf_id"])
            self.assertEqual(row["values"], list(values))
            self.assertEqual(header["element_count"], len(values))

    def test_substituted_header_preimage_rejects_before_output(self):
        _, golden, other = fixture_store()
        golden["shards"][0]["header_bytes_hex"] = "7b7d"
        with patch.object(vectors, "fixture_store", return_value=({}, golden, other)):
            with self.assertRaisesRegex(SourceError, "ORIGINAL_HEADER_PREIMAGE"):
                vectors.generate()

    def test_native_declaration_pin_rejects_substitution(self):
        with patch.object(vectors, "DECL_SHA", "0" * 64):
            with self.assertRaisesRegex(SourceError, "NATIVE_HEADER_DECLARATION"):
                vectors.generate()

    def test_header_parsing_is_not_payload_sha_admission(self):
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
            "native_export_authenticated",
            "payload_sha_proved",
            "source_graph_admission_proved",
            "full_native_recovery_proved",
        ]:
            self.assertFalse(result[flag])
        self.assertIn("changedPayloadWithOldShaStillAccepted", result["small_kernel_cases"])
        self.assertIn("nonJsonHeaderRejected", result["small_kernel_cases"])

    def test_generator_byte_exact(self):
        before = {p: p.read_bytes() for p in [vectors.TARGET, vectors.LEAN]}
        vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_mandatory_build_and_axiom_inventory(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeQJson", "NativeQHeader", "NativeQHeaderVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(
                r"^(?:def|theorem|abbrev|structure|inductive) (\w+)", source, re.M
            ):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)
            self.assertNotIn("native_decide", source)
            self.assertNotIn("nativeArithmeticRecoveryRefines", source)


if __name__ == "__main__":
    unittest.main()
