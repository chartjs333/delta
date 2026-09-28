"""Original mixed positions and cache ambiguity, without a new native capture."""

import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_vote_codec_vectors as vectors  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_admission_snapshot import decode_flat  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402

MODULES = [
    "NativeVoteCache",
    "NativeCacheHistory",
    "NativeCacheProjection",
    "NativeVoteCacheVectors",
]


class NativeVoteCacheTests(unittest.TestCase):
    @staticmethod
    def original_entries():
        doc = load_json_strict(
            ROOT / "formal/proposals/evidence/native-proposal-replay/cpp-cross-check.json"
        )
        row = next(r for r in doc["observed"] if r["name"] == "no-snapshot")
        return wal_entries(bytes.fromhex(row["wal_hex"]))

    def test_original_mixed_positions_are_not_vote_ordinals(self):
        entries = self.original_entries()
        self.assertEqual(
            [(e["kind"], e["sequence"]) for e in entries], [(2, 1), (1, 2), (1, 3), (1, 4)]
        )
        votes = [e for e in entries if e["kind"] == 2]
        commands = [e for e in entries if e["kind"] == 1]
        self.assertEqual((len(votes), len(commands), entries[-1]["sequence"]), (1, 3, 4))
        original = decode_flat(votes[0]["command"], 3)
        self.assertEqual((original["kind"], original["durable_sequence"]), ("ISC", "1"))
        self.assertEqual(vectors.envelope(sorted(original.items())), votes[0]["command"])
        # Dropping command records would lose the actual final state and three positions.
        self.assertNotEqual(commands[-1]["state"], votes[0]["state"])
        self.assertNotEqual(len(votes), entries[-1]["sequence"])

    def test_reencoded_conflict_has_same_cache_key_but_different_original_identity(self):
        raw = self.original_entries()[0]["command"]
        original = decode_flat(raw, 3)
        key_fields = ("validator_id", "validator_epoch_id", "context_id")
        key = tuple(original[k] for k in key_fields)
        changed = {**original, "durable_sequence": "2", "view": "9"}
        altered = vectors.envelope(sorted(changed.items()))
        decoded = decode_flat(altered, 3)
        self.assertEqual(tuple(decoded[k] for k in key_fields), key)
        self.assertNotEqual(altered, raw)
        self.assertNotEqual(
            hashlib.sha256(b"deltareduce:003:vote:v1\0" + altered).digest(),
            hashlib.sha256(b"deltareduce:003:vote:v1\0" + raw).digest(),
        )
        # Codec-valid bytes are deliberately not claimed to pass native admission.
        self.assertEqual(decoded["durable_sequence"], "2")

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
