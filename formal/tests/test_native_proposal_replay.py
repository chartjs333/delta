"""Original two-candidate policy, computed admission and mixed WAL regressions."""

import copy
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import check_native_proposal_replay as check  # noqa: E402
import native_config_replay as mixed  # noqa: E402
import native_policy_codec as codec  # noqa: E402
import native_proposal_admission as admission  # noqa: E402
from generate_native_state_vectors import envelope  # noqa: E402
from native_admission_snapshot import decode_flat  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402
from test_native_command_replay import encoded  # noqa: E402


class ProposalReplayTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((check.FOLDER / "cpp-cross-check.json").read_bytes())
        self.rows = {r["name"]: r for r in self.doc["observed"]}

    def machine(self, name="no-snapshot", wal=None):
        r = self.rows[name]
        return mixed.replay_proposals(
            bytes.fromhex(r["policy_hex"]),
            bytes.fromhex(r["initial_hex"]),
            bytes.fromhex(r["wal_hex"]) if wal is None else wal,
            bytes.fromhex(r["snapshot_hex"]),
        )

    def test_fresh_unchanged_native_matrix(self):
        check.verify_document(self.doc)
        self.assertEqual(len(self.rows), 32)
        self.assertEqual(sum(r["status"] == "REJECT" for r in self.rows.values()), 18)

    def test_original_isc_freeze_policy_and_wal_are_exact(self):
        prior = json.loads(
            (ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json").read_bytes()
        )
        old = next(r for r in prior["observed"] if r["name"] == "after-state-command-retry")
        fresh = self.rows["live-freeze-after-isc"]
        for field in ["policy_hex", "wal_hex"]:
            self.assertEqual(old[field], fresh[field])
        self.assertEqual(old["initial_state_hex"], fresh["initial_hex"])
        self.assertEqual(old["receipt_hex"], self.rows["historical-vote"]["vote_receipt_hex"])
        p = codec.decode(bytes.fromhex(fresh["policy_hex"]))
        self.assertEqual([c["action"] for c in p["candidates"]], [1, 2])
        self.assertEqual(
            [e["sequence"] for e in wal_entries(bytes.fromhex(fresh["wal_hex"]))], [1, 2]
        )
        m = self.machine("live-freeze-after-isc")
        self.assertEqual([v["sequence"] for v in m["votes"].values()], [1])
        self.assertEqual([v["sequence"] for v in m["requests"].values()], [2])
        # The older strict API deliberately keeps its old rejection scope.
        with self.assertRaises(ValueError):
            mixed.replay(
                bytes.fromhex(fresh["policy_hex"]), bytes.fromhex(fresh["initial_hex"]), b""
            )

    def test_both_original_receipts_survive_reopen_and_movement(self):
        m = self.machine()
        vote = bytes.fromhex(self.rows["live-vote"]["command_hex"])
        command = bytes.fromhex(self.rows["live-freeze-after-isc"]["command_hex"])
        a, b = mixed.retry_vote(m, vote), mixed.retry_command(m, command)
        self.assertEqual(a["receipt_hex"], self.rows["live-vote"]["vote_receipt_hex"])
        self.assertEqual(a["receipt_hex"], self.rows["reopened-vote"]["vote_receipt_hex"])
        self.assertEqual(b, self.rows["reopened-command"]["receipt"])
        self.assertEqual((a["sequence"], b["sequence"]), (1, 2))
        m.update(state_hex="", tick=1000, sequence=100)
        self.assertEqual(mixed.retry_vote(m, vote), a)
        self.assertEqual(mixed.retry_command(m, command), b)

    def test_unselected_candidate_is_not_skipped(self):
        r = self.rows["live-vote"]
        for field, value in [
            ("body_hash", "sha256:" + "f" * 64),
            ("context_id", "sha256:" + "a" * 64),
            ("height", 2),
        ]:
            p = codec.decode(bytes.fromhex(r["policy_hex"]))
            p["candidates"][0][field] = value
            # Empty WAL still checks every original candidate at startup.
            with self.subTest(field=field), self.assertRaises(ValueError):
                mixed.replay_proposals(
                    codec.HEADER + codec.encode_value("policy", p),
                    bytes.fromhex(r["initial_hex"]),
                    b"",
                )

    def test_missing_unselected_body_and_other_action_fail_closed(self):
        r = self.rows["live-vote"]
        p = codec.decode(bytes.fromhex(r["policy_hex"]))
        for edit in [
            lambda p: p["snapshot"].update(input_set_bodies=[]),
            lambda p: p["candidates"][0].update(action=3),
            lambda p: p["candidates"].reverse(),
            lambda p: p["candidates"].append(copy.deepcopy(p["candidates"][-1])),
            lambda p: p.update(candidates=[]),
        ]:
            altered = copy.deepcopy(p)
            edit(altered)
            with self.assertRaises(ValueError):
                admission.prepare(
                    codec.HEADER + codec.encode_value("policy", altered),
                    bytes.fromhex(r["initial_hex"]),
                )

    def test_fresh_state_guards_and_historical_cache_are_distinct(self):
        r = self.rows["live-vote"]
        args = [bytes.fromhex(r[k]) for k in ["policy_hex", "initial_hex", "command_hex"]]
        facts = dict(tick=10, ready=True, invalidated=False, recovery=False, expected=1)
        v, candidate = admission.check_selected(*args, facts)
        self.assertEqual(candidate["action"], 2)
        self.assertEqual(candidate["body_hash"], v["body_hash"])
        for change in [dict(ready=False), dict(invalidated=True), dict(expected=2), dict(tick=100)]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                admission.check(*args, {**facts, **change})
        self.assertEqual(admission.check(*args, {**facts, "ready": False, "recovery": True}), v)

    def test_wrong_actor_epoch_body_phase_and_candidate(self):
        r = self.rows["live-vote"]
        facts = dict(tick=10, ready=True, invalidated=False, recovery=False, expected=1)
        v = decode_flat(bytes.fromhex(r["command_hex"]), 3)
        for field, value in [
            ("kind", "ROUND_CONFIG"),
            ("body_hash", "sha256:" + "a" * 64),
            ("validator_id", "validator-2"),
            ("validator_epoch_id", "sha256:" + "a" * 64),
        ]:
            changed = {**v, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                admission.check(
                    bytes.fromhex(r["policy_hex"]),
                    bytes.fromhex(r["initial_hex"]),
                    envelope(3, sorted(changed.items())),
                    facts,
                )
        policy = codec.decode(bytes.fromhex(r["policy_hex"]))
        config = policy["candidates"][0]
        config_vote = {
            **v,
            "kind": "ROUND_CONFIG",
            "context_id": config["context_id"],
            "body_hash": config["body_hash"],
        }
        with self.assertRaisesRegex(ValueError, "vote phase"):
            admission.check(
                bytes.fromhex(r["policy_hex"]),
                bytes.fromhex(r["initial_hex"]),
                envelope(3, sorted(config_vote.items())),
                facts,
            )

    def test_snapshots_compare_actual_position(self):
        for name in ["snapshot-at-vote", "snapshot-at-command", "zero-different-snapshot"]:
            self.assertEqual(self.machine(), self.machine(name))
        for name in ["wrong-vote-snapshot", "wrong-command-snapshot", "ahead-snapshot"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.machine(name)

    def test_corruption_truncation_reorder_and_duplicates(self):
        raw = bytes.fromhex(self.rows["no-snapshot"]["wal_hex"])
        for value in [raw[:-1], raw + b"D", raw[:16], raw[:-1] + bytes([raw[-1] ^ 1])]:
            with self.assertRaises(ValueError):
                self.machine(wal=value)
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

    def test_rehashed_record_fields_reject(self):
        entries = wal_entries(bytes.fromhex(self.rows["no-snapshot"]["wal_hex"]))
        for index, field, value in [
            (0, "record", b"0" * 64),
            (0, "state", entries[1]["state"]),
            *[(2, k, entries[1][k]) for k in ["state", "effects", "record"]],
        ]:
            changed = copy.deepcopy(entries)
            changed[index][field] = value
            with self.assertRaises(ValueError):
                self.machine(wal=encoded(changed))

    def test_native_evidence_substitutions_reject(self):
        for field in [
            "native_export_authenticated",
            "gate_eligible",
            "source_commit",
            "harness_sha256",
            "source_sha256",
        ]:
            doc = copy.deepcopy(self.doc)
            doc[field] = "forged"
            with self.subTest(field=field), self.assertRaises(ValueError):
                check.verify_document(doc)
        rows = copy.deepcopy(self.doc["observed"])
        rows[1]["receipt"]["sequence"] = 1
        with self.assertRaises(ValueError):
            check.validate(rows)

    def test_complete_lean_inventory(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        for module in ["NativeProposalAdmission", "NativeProposalAdmissionVectors"]:
            code = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            for name in re.findall(r"^(?:def|theorem) (\w+)", code, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit.splitlines())
            stripped = re.sub(r"/\-.*?\-/|--[^\n]*", "", code, flags=re.S)
            self.assertNotRegex(stripped, r"\b(?:sorry|admit|native_decide)\b|^axiom\b")


if __name__ == "__main__":
    unittest.main()
