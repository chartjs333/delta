"""Original wire identity and candidate arithmetic proof integration."""

import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_vote_codec_vectors as votes  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_admission_snapshot import decode_flat  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402

MODULES = ["NativeArithmeticVote", "NativeArithmeticPrefix", "NativeArithmeticVoteVectors"]


class NativeArithmeticVoteTests(unittest.TestCase):
    def test_original_signature_view_and_sequence_cannot_be_dropped(self):
        arithmetic = [r for r in votes.original() if r["action"] in (5, 7)]
        self.assertEqual([r["action"] for r in arithmetic], [5, 7])
        for row in arithmetic:
            raw = bytes.fromhex(row["frame_hex"])
            fields = decode_flat(raw, 3)
            self.assertEqual(len(fields), 13)
            self.assertEqual(votes.envelope(sorted(fields.items())), raw)
            self.assertEqual(
                fields["formal_semantics_id"],
                "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
            )
            for key, replacement in [
                ("signature_id", "sha256:" + "0" * 64),
                ("view", "1"),
                ("durable_sequence", "5"),
            ]:
                changed = {**fields, key: replacement}
                encoded = votes.envelope(sorted(changed.items()))
                self.assertNotEqual(encoded, raw)
                self.assertNotEqual(hashlib.sha256(encoded).digest(), hashlib.sha256(raw).digest())

    def test_retained_mixed_prefix_has_command_and_vote_positions(self):
        doc = load_json_strict(
            ROOT / "formal/proposals/evidence/native-proposal-replay/cpp-cross-check.json"
        )
        row = next(r for r in doc["observed"] if r["name"] == "no-snapshot")
        entries = wal_entries(bytes.fromhex(row["wal_hex"]))[:2]
        self.assertEqual([(e["kind"], e["sequence"]) for e in entries], [(2, 1), (1, 2)])
        next_global = entries[-1]["sequence"] + 1
        vote_only = sum(e["kind"] == 2 for e in entries) + 1
        self.assertEqual((next_global, vote_only), (3, 2))

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
