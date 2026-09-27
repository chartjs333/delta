"""Original source pinning and the boundary between framing and authenticated Q."""

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
import generate_native_q_bytes as vectors  # noqa: E402
from generate_native_source_artifacts import fixture_store  # noqa: E402
from native_source_artifacts import SourceError, read_drq1  # noqa: E402


class NativeQBytesTests(unittest.TestCase):
    def test_original_full_byte_splits_and_coordinate_order(self):
        result = json.loads(vectors.TARGET.read_bytes())
        _, golden, _ = fixture_store()
        self.assertEqual(len(result["rows"]), 5)
        values = []
        for row, source in zip(result["rows"], golden["shards"], strict=True):
            raw = bytes.fromhex(row["source_frame_hex"])
            self.assertEqual(raw.hex(), source["envelope_hex"])
            self.assertEqual(row["source_leaf_id"], source["leaf_id"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["source_frame_sha256"])
            header = bytes.fromhex(row["header_hex"])
            payload = bytes.fromhex(row["payload_hex"])
            self.assertEqual(raw[16:], header + payload)
            self.assertEqual(
                struct.unpack("<4sHHII", raw[:16]), (b"DRQ1", 1, 0, len(header), len(payload))
            )
            self.assertEqual(list(read_drq1(raw)[1]), row["values"])
            values.extend(row["values"])
        self.assertEqual(values, golden["q_values"])
        self.assertEqual(len(values), 36)

    def test_generator_retains_source_preimage_pin(self):
        _, golden, other = fixture_store()
        golden["shards"][0]["payload_hex"] = "0200"
        with patch.object(vectors, "fixture_store", return_value=({}, golden, other)):
            with self.assertRaisesRegex(SourceError, "SOURCE_FRAME_SPLIT"):
                vectors.generate()

    def test_old_header_payload_countercheck_requires_separate_hash(self):
        _, golden, _ = fixture_store()
        raw = bytearray.fromhex(golden["shards"][0]["envelope_hex"])
        size = struct.unpack("<I", raw[8:12])[0]
        raw[16 + size] = 2
        with self.assertRaisesRegex(SourceError, "PAYLOAD_HASH"):
            read_drq1(bytes(raw))
        lean = vectors.LEAN.read_text(encoding="utf-8")
        self.assertIn("changedPayloadWithOldHeaderAccepted", lean)
        self.assertIn("opaqueHeaderNotJson", lean)
        result = json.loads(vectors.TARGET.read_bytes())
        for key in [
            "formal_go",
            "native_execution",
            "native_export_authenticated",
            "header_json_sha_admission_proved",
            "full_native_recovery_proved",
        ]:
            self.assertFalse(result[key])

    def test_generator_byte_exact(self):
        before = {p: p.read_bytes() for p in [vectors.TARGET, vectors.LEAN]}
        vectors.generate()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_mandatory_build_and_axiom_inventory(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeQBytes", "NativeQBytesVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            text = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(
                r"^(?:def|theorem|abbrev|structure|inductive) (\w+)", text, re.M
            ):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)
            self.assertNotIn("native_decide", text)
            self.assertNotIn("nativeArithmeticRecoveryRefines", text)


if __name__ == "__main__":
    unittest.main()
