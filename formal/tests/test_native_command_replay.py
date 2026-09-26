"""Actual command recovery and strict scope; no mixed-vote admission claim."""

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import check_native_command_replay as check  # noqa: E402
from native_command_replay import replay, retry  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402


def encoded(entries):
    raw = b""
    for e in entries:
        body = e["sequence"].to_bytes(8, "big") + bytes([e["kind"], 0, 0, 0])
        for k in ["command", "state", "effects", "record"]:
            body += len(e[k]).to_bytes(4, "big") + e[k]
        prefix = b"DRW1\x00\x01\x00\x00" + (len(body) + 44).to_bytes(4, "big") + body
        raw += prefix + hashlib.sha256(prefix).digest()
    return raw


class CommandReplayTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((check.FOLDER / "cpp-cross-check.json").read_bytes())
        self.rows = {r["name"]: r for r in self.doc["observed"]}

    def machine(self, name="no-snapshot"):
        r = self.rows[name]
        return replay(
            bytes.fromhex(r["initial_hex"]),
            bytes.fromhex(r["wal_hex"]),
            bytes.fromhex(r["snapshot_hex"]),
            r["clock"],
        )

    def test_native_matrix(self):
        check.verify_document(self.doc)
        self.assertEqual(len(self.rows), 22)
        self.assertEqual(sum(r["status"] == "REJECT" for r in self.rows.values()), 11)

    def test_exact_computed_cache_and_retry(self):
        m = self.machine()
        self.assertEqual(list(m["requests"]), ["freeze", "view", "abort"])
        self.assertEqual([r["sequence"] for r in m["requests"].values()], [1, 2, 3])
        self.assertEqual(m["tick"], 13)
        self.assertTrue(m["invalidated"])
        raw = bytes.fromhex(self.rows["historical-retry"]["command_hex"])
        original = retry(m, raw)
        self.assertEqual(original, self.rows["reopened-retry"]["receipt"])
        m.update(state_hex="", tick=100, sequence=100)
        self.assertEqual(retry(m, raw), original)
        with self.assertRaisesRegex(ValueError, "conflict"):
            retry(m, bytes.fromhex(self.rows["request-conflict"]["command_hex"]))

    def test_rehashed_all_output_substitutions(self):
        r = self.rows["no-snapshot"]
        entries = wal_entries(bytes.fromhex(r["wal_hex"]))
        for key in ["state", "effects", "record"]:
            changed = copy.deepcopy(entries)
            changed[1][key] = entries[0][key]
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(ValueError, "computed journal output"),
            ):
                replay(bytes.fromhex(r["initial_hex"]), encoded(changed), clock=r["clock"])

    def test_sequence_duplicates_and_full_vote_reject(self):
        r = self.rows["no-snapshot"]
        entries = wal_entries(bytes.fromhex(r["wal_hex"]))
        for changed in [[entries[1], entries[0], entries[2]], entries[1:], [*entries, entries[0]]]:
            with self.assertRaisesRegex(ValueError, "sequence"):
                replay(bytes.fromhex(r["initial_hex"]), encoded(changed), clock=r["clock"])
        with self.assertRaisesRegex(ValueError, "duplicate request"):
            self.machine("duplicate-request")
        original = json.loads(
            (ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json").read_bytes()
        )
        old = next(r for r in original["observed"] if r["name"] == "after-state-command-retry")
        with self.assertRaisesRegex(ValueError, "mixed vote"):
            replay(bytes.fromhex(old["initial_state_hex"]), bytes.fromhex(old["wal_hex"]), clock=10)

    def test_snapshot_exact_and_zero_scope(self):
        self.assertEqual(self.machine(), self.machine("matching-middle"))
        self.assertEqual(self.machine(), self.machine("zero-different-snapshot"))
        self.assertEqual(
            self.machine("zero-empty-journal")["state_hex"], self.rows["empty"]["initial_hex"]
        )
        for name in ["wrong-middle", "ahead-snapshot"]:
            with self.assertRaisesRegex(ValueError, "snapshot"):
                self.machine(name)

    def test_clock_and_incomplete_observations(self):
        with self.assertRaisesRegex(ValueError, "clock backwards"):
            self.machine("old-clock-policy")
        self.assertEqual(self.machine("old-clock-submit-only")["tick"], 0)
        r = self.rows["no-snapshot"]
        raw = bytes.fromhex(r["wal_hex"])
        for b in [raw[:-1], raw + b"D", raw[:16]]:
            with self.assertRaises(ValueError):
                replay(bytes.fromhex(r["initial_hex"]), b, clock=10)

    def test_source_scope_and_response_mutations(self):
        for key in [
            "source_commit",
            "source_sha256",
            "harness_sha256",
            "compiler_flags",
            "unmodified_translation_units",
            "compiler",
            "status",
            "native_runtime_execution",
            "native_export_authenticated",
            "gate_eligible",
        ]:
            changed = copy.deepcopy(self.doc)
            changed[key] = "forged"
            with self.subTest(key=key), self.assertRaises(ValueError):
                check.verify_document(changed)
        for key in ["state_hex", "sequence", "receipt", "code", "status"]:
            rows = copy.deepcopy(self.doc["observed"])
            rows[0][key] = "substituted"
            with self.subTest(key=key), self.assertRaises(ValueError):
                check.validate(rows)

    def test_mandatory_audit_and_no_proof_holes(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        for name in ["NativeCommandReplay", "NativeCommandReplayVectors"]:
            self.assertIn("import DeltaReduce." + name, imports)
            code = (ROOT / f"formal/proofs/DeltaReduce/{name}.lean").read_text(encoding="utf-8")
            for declaration in re.findall(r"^(?:def|theorem|abbrev) (\w+)", code, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{name}.{declaration}", audit)
            code = re.sub(r"/-.*?-/|--[^\n]*", "", code, flags=re.S)
            self.assertNotRegex(code, r"\b(sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
