"""Mixed CONFIG/command replay, original caches and snapshot-position regressions."""

import copy
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import check_native_config_replay as check  # noqa: E402
import native_config_replay as mixed  # noqa: E402
import native_policy_codec as codec  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402
from test_native_command_replay import encoded  # noqa: E402


class ConfigReplayTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((check.FOLDER / "cpp-cross-check.json").read_bytes())
        self.rows = {r["name"]: r for r in self.doc["observed"]}

    def machine(self, name="no-snapshot", wal=None):
        r = self.rows[name]
        return mixed.replay(
            bytes.fromhex(r["policy_hex"]),
            bytes.fromhex(r["initial_hex"]),
            bytes.fromhex(r["wal_hex"]) if wal is None else wal,
            bytes.fromhex(r["snapshot_hex"]),
        )

    def test_native_matrix(self):
        check.verify_document(self.doc)
        self.assertEqual(len(self.rows), 32)
        self.assertEqual(sum(r["status"] == "REJECT" for r in self.rows.values()), 18)

    def test_exact_disjoint_caches_and_outer_sequences(self):
        m = self.machine()
        self.assertEqual(m["sequence"], 4)
        self.assertEqual([v["sequence"] for v in m["votes"].values()], [1])
        self.assertEqual([v["sequence"] for v in m["requests"].values()], [2, 3, 4])
        self.assertEqual(list(m["requests"]), ["config", "view", "abort"])
        self.assertEqual(m["tick"], 13)
        self.assertTrue(m["invalidated"])

    def test_historical_receipts_after_movement(self):
        m = self.machine()
        vote = bytes.fromhex(self.rows["historical-vote"]["command_hex"])
        command = bytes.fromhex(self.rows["historical-command"]["command_hex"])
        a, b = mixed.retry_vote(m, vote), mixed.retry_command(m, command)
        self.assertEqual(a["receipt_hex"], self.rows["live-vote"]["vote_receipt_hex"])
        self.assertEqual(a["receipt_hex"], self.rows["reopened-vote"]["vote_receipt_hex"])
        self.assertEqual(b, self.rows["reopened-command"]["receipt"])
        m.update(state_hex="", sequence=100, tick=1000)
        self.assertEqual(mixed.retry_vote(m, vote), a)
        self.assertEqual(mixed.retry_command(m, command), b)
        with self.assertRaisesRegex(ValueError, "conflicting"):
            mixed.retry_vote(m, bytes.fromhex(self.rows["vote-conflict"]["command_hex"]))

    def test_snapshot_at_vote_uses_current_not_empty_section(self):
        self.assertEqual(self.machine(), self.machine("snapshot-at-vote"))
        self.assertEqual(self.machine(), self.machine("snapshot-at-command"))
        self.assertEqual(self.machine(), self.machine("zero-different-snapshot"))
        self.assertEqual(
            self.machine("vote-only")["state_hex"], self.rows["vote-only"]["initial_hex"]
        )
        for name in ["wrong-vote-snapshot", "wrong-command-snapshot", "ahead-snapshot"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.machine(name)

    def test_rehashed_output_policy_and_shape_substitutions(self):
        entries = wal_entries(bytes.fromhex(self.rows["no-snapshot"]["wal_hex"]))
        for index, field, value in [
            (0, "state", entries[1]["state"]),
            (0, "effects", entries[1]["effects"]),
            (0, "record", b"0" * 64),
            *[(2, k, entries[1][k]) for k in ["state", "effects", "record"]],
        ]:
            changed = copy.deepcopy(entries)
            changed[index][field] = value
            with self.subTest(index=index, field=field), self.assertRaises(ValueError):
                self.machine(wal=encoded(changed))

    def test_order_duplicates_and_authority_invalidation(self):
        for name in [
            "outer-gap",
            "vote-sequence",
            "reordered",
            "duplicate-vote",
            "duplicate-command",
            "vote-after-command",
            "changed-startup-policy",
            "backwards-clock",
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.machine(name)
        entries = wal_entries(bytes.fromhex(self.rows["no-snapshot"]["wal_hex"]))
        with self.assertRaisesRegex(ValueError, "sequence"):
            self.machine(wal=encoded(entries[1:]))

    def test_incomplete_and_corrupt_observation_rejects(self):
        raw = bytes.fromhex(self.rows["no-snapshot"]["wal_hex"])
        for data in [raw[:-1], raw + b"D", raw[:16], raw[:-1] + bytes([raw[-1] ^ 1])]:
            with self.assertRaises(ValueError):
                self.machine(wal=data)

    def test_unsupported_old_isc_is_not_filtered(self):
        doc = json.loads(
            (ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json").read_bytes()
        )
        row = next(r for r in doc["observed"] if r["name"] == "after-state-command-retry")
        with self.assertRaises(ValueError):
            mixed.replay(
                bytes.fromhex(row["policy_hex"]),
                bytes.fromhex(row["initial_state_hex"]),
                bytes.fromhex(row["wal_hex"]),
            )
        entries = wal_entries(bytes.fromhex(row["wal_hex"]))
        self.assertEqual([e["sequence"] for e in entries], [1, 2])

    def test_startup_empty_log_still_requires_computed_authority(self):
        r = self.rows["empty"]
        p = codec.decode(bytes.fromhex(r["policy_hex"]))
        p["snapshot"]["state_id"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "exact state bytes"):
            mixed.replay(codec.encode(p), bytes.fromhex(r["initial_hex"]), b"")

    def test_evidence_substitutions_reject(self):
        for field in [
            "native_export_authenticated",
            "gate_eligible",
            "source_commit",
            "harness_sha256",
            "compiler_flags",
            "source_sha256",
            "mixed_vote_command_recovery",
        ]:
            doc = copy.deepcopy(self.doc)
            doc[field] = "forged"
            with self.subTest(field=field), self.assertRaises(ValueError):
                check.verify_document(doc)
        for field in ["vote_receipt_hex", "state_hex", "sequence", "status", "code", "vote_replay"]:
            rows = copy.deepcopy(self.doc["observed"])
            rows[0][field] = "forged"
            with self.subTest(field=field), self.assertRaises(ValueError):
                check.validate(rows)

    def test_complete_mandatory_audit_inventory(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        for module in ["NativeConfigReplay", "NativeConfigReplayVectors"]:
            code = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            names = re.findall(r"^(?:def|theorem) (\w+)", code, re.M)
            for name in names:
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit.splitlines())
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", code, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
