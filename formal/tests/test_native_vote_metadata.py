"""Original wire fields cannot be discarded by a draft metadata projection."""

import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_vote_codec_vectors as vectors  # noqa: E402
from native_admission_snapshot import decode_flat  # noqa: E402
from native_policy_wal import receipt  # noqa: E402

MODULES = ["NativeVoteMetadata", "NativeVoteMetadataVectors"]


class NativeVoteMetadataTests(unittest.TestCase):
    def test_draft_visible_identity_does_not_retain_original_signature_or_position(self):
        for row in vectors.original():
            if row["action"] not in (5, 7):
                continue
            raw = bytes.fromhex(row["frame_hex"])
            fields = decode_flat(raw, 3)
            visible = {k: fields[k] for k in ["validator_id", "kind", "context_id"]}
            for key, value in [
                ("signature_id", "sha256:" + "0" * 64),
                ("view", "9"),
                ("durable_sequence", "3"),
            ]:
                changed = {**fields, key: value}
                self.assertEqual({k: changed[k] for k in visible}, visible)
                altered = vectors.envelope(sorted(changed.items()))
                self.assertNotEqual(altered, raw)
                self.assertNotEqual(hashlib.sha256(altered).digest(), hashlib.sha256(raw).digest())

    def test_original_receipts_keep_exact_frames_and_historical_semantics(self):
        for row in vectors.original():
            if row["action"] not in (5, 7):
                continue
            parsed = receipt(bytes.fromhex(row["receipt_hex"]))
            raw = bytes.fromhex(row["frame_hex"])
            self.assertEqual(parsed["frame"], raw)
            fields = decode_flat(raw, 3)
            self.assertEqual(parsed["sequence"], int(fields["durable_sequence"]))
            self.assertEqual(
                fields["formal_semantics_id"],
                "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
            )
            self.assertEqual(len(fields), 13)
            self.assertEqual(vectors.envelope(sorted(fields.items())), raw)

    def test_declarations_imported_and_audited(self):
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
