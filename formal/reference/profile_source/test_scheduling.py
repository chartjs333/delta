"""Original 007 cross-language bytes plus producer/static-state regressions."""

import copy
import json
import unittest
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import scheduling as s

ROOT = Path(__file__).resolve().parents[3]


def fixture():
    data = json.loads(
        (ROOT / "delta-protocol/fixtures/007/cross-language/golden-v1.json").read_text()
    )
    p = data["plan"]["value"]
    context = {k: data["domain_policies"][0]["value"][k] for k in s.CONTEXT}
    policies = tuple(bytes.fromhex(r["bytes_hex"]) for r in data["domain_policies"])
    result = s.plan(
        policies,
        context,
        p["assignment_policy_id"],
        p["capability_snapshot_root"],
        [(d["worker_id"], d["decision_id"]) for d in p["decisions"]],
        p["lease_policy"],
        data["formal_semantics_id"],
    )
    workers = tuple(
        (d["value"], c["value"]["complete_ticket_throughput_milli"])
        for d, c in zip(data["eligibility_decisions"], data["capability_profiles"], strict=True)
    )
    leases = s.allocate(result, workers, data["ticket_leases"][0]["value"]["issue_tick"])
    return data, result, workers, leases


def eligibility_policy(data):
    p = data["capability_profiles"][0]["value"]
    return {
        "allowed_domain_ids": ["code", "text"],
        "allowed_region_ids": ["eu", "us"],
        "allowed_software_build_ids": [p["software_build_id"]],
        "arithmetic_profile_id": p["arithmetic_profile_id"],
        "decision_tick": 12,
        "eligibility_policy_id": data["eligibility_decisions"][0]["value"]["eligibility_policy_id"],
        "identity_epoch": 7,
        "minimum_memory_bytes": 8589934592,
        "minimum_sample_count": 8,
        "model_mode": "QLORA-8GB",
        "parameter_schema_id": p["parameter_schema_id"],
        "round_config_id": p["round_config_id"],
        "trusted_signature_ids": sorted(
            row["value"]["signature_id"] for row in data["capability_profiles"]
        ),
    }


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.data, self.plan, self.workers, self.leases = fixture()
        self.ticket = "ticket-code-000"
        self.initial = s.initialize(self.plan, self.leases)

    def test_full_original_cross_language_plan_ticket_lease_timer_bytes(self):
        self.assertEqual(self.plan.original, bytes.fromhex(self.data["plan"]["bytes_hex"]))
        self.assertEqual(self.plan.id, self.data["plan"]["content_id"])
        for raw, row in zip(self.plan.tickets, self.data["work_tickets"], strict=True):
            self.assertEqual(raw, bytes.fromhex(row["bytes_hex"]))
            self.assertEqual(s.identifier("work-ticket", raw), row["content_id"])
        for raw, row in zip(self.leases, self.data["ticket_leases"], strict=True):
            self.assertEqual(raw, bytes.fromhex(row["bytes_hex"]))
            self.assertEqual(s.lease_id(raw), row["content_id"])
        for row in self.data["lease_timer_tokens"]:
            raw = s.timer(self.initial, row["value"]["ticket_id"])
            self.assertEqual(raw, bytes.fromhex(row["bytes_hex"]))
            self.assertEqual(s.identifier("lease-timer-token", raw), row["content_id"])

    def test_original_capability_to_decision_not_supplied_eligible_boolean(self):
        policy = eligibility_policy(self.data)
        for profile, decision in zip(
            self.data["capability_profiles"], self.data["eligibility_decisions"], strict=True
        ):
            result = s.evaluate_capability(
                bytes.fromhex(profile["bytes_hex"]), policy, self.plan.semantics
            )
            self.assertEqual(result, bytes.fromhex(decision["bytes_hex"]))
            self.assertEqual(s.identifier("eligibility-decision", result), decision["content_id"])
        changed = copy.deepcopy(self.data["capability_profiles"][0]["value"])
        changed.update(
            memory_bytes=0,
            signature_id="sha256:" + "0" * 64,
            expires_at_tick=0,
            complete_ticket_throughput_milli=0,
            worker_id="invalid worker",
        )
        bad = s.decode(s.evaluate_capability(s.canonical(changed), policy, self.plan.semantics))
        self.assertFalse(bad["eligible"])
        self.assertEqual(bad["allowed_domain_ids"], [])
        self.assertEqual(bad["max_concurrent_leases"], 0)
        self.assertEqual(
            bad["reason_codes"],
            sorted(
                [
                    "MEMORY_INSUFFICIENT",
                    "PROFILE_EXPIRED",
                    "SIGNATURE_NOT_TRUSTED",
                    "THROUGHPUT_EVIDENCE_MISSING",
                    "WORKER_ID_INVALID",
                ]
            ),
        )

    def test_full_plan_reconstruction_rejects_forged_ticket_prefix(self):
        with self.assertRaises(CodecError):
            s.verify_plan(replace(self.plan, tickets=self.plan.tickets[:-1]))
        with self.assertRaises(CodecError):
            s.initialize(self.plan, self.leases[:-1])
        with self.assertRaises(CodecError):
            s.initialize(self.plan, tuple(reversed(self.leases)))

    def test_same_worker_reassign_keeps_original_ticket_and_static_identity(self):
        prior = s.decode(s.current(self.initial, self.ticket))
        token = s.timer(self.initial, self.ticket)
        expired = s.invoke(
            self.initial, "expire", self.ticket, tick=prior["expiry_tick"], token=token
        )
        old = s.current(expired.state, self.ticket)
        reassigned = s.invoke(
            expired.state,
            "reassign",
            self.ticket,
            tick=prior["expiry_tick"] + 1,
            prior=s.lease_id(old),
            worker=prior["worker_id"],
            region=prior["region_route"],
        )
        value = s.decode(s.current(reassigned.state, self.ticket))
        self.assertEqual(value["worker_id"], prior["worker_id"])
        self.assertEqual(value["lease_epoch"], 1)
        self.assertEqual(value["ticket_content_id"], prior["ticket_content_id"])
        self.assertEqual(value["prior_lease_id"], s.lease_id(old))
        self.assertEqual(len(reassigned.state.frames), 5)
        public = s.public_lease_fields(reassigned.state)
        self.assertEqual(public["leaseOwner"][self.ticket], prior["worker_id"])
        self.assertEqual(public["leaseEpoch"][self.ticket], 1)
        self.assertIn(self.ticket, public["leaseActive"])
        self.assertEqual(reassigned.state.frames[:3], self.initial.frames)

    def test_exact_executed_native_dsj1_prefix_and_recovered_identity(self):
        evidence = json.loads(
            (
                ROOT / "formal/proposals/evidence/profile-source-components/native-lease-probe.json"
            ).read_text()
        )
        state = s.invoke(
            self.initial, "expire", self.ticket, tick=35, token=s.timer(self.initial, self.ticket)
        ).state
        state = s.invoke(
            state,
            "reassign",
            self.ticket,
            tick=36,
            prior=s.lease_id(s.current(state, self.ticket)),
            worker="worker-a",
            region="eu",
        ).state
        original = bytes.fromhex(evidence["original_dsj1"]["hex"])
        self.assertEqual(sha256(original).hexdigest(), evidence["original_dsj1"]["sha256"])
        self.assertEqual(len(original), evidence["original_dsj1"]["byte_length"])
        self.assertEqual(b"".join(state.frames), original)
        self.assertEqual(
            s.lease_id(s.current(state, self.ticket)), evidence["observed"]["new_lease"]
        )
        self.assertTrue(evidence["observed"]["same_recovered_identity"])
        self.assertTrue(evidence["observed"]["same_recovered_sequence"])

    def test_commit_projection_preserves_native_active_bytes_and_full_lineage(self):
        raw = s.current(self.initial, self.ticket)
        v = s.decode(raw)
        committed = s.invoke(
            self.initial,
            "commit",
            self.ticket,
            tick=v["issue_tick"],
            worker=v["worker_id"],
            epoch=0,
            commitment="sha256:" + "e" * 64,
        )
        self.assertEqual(s.current(committed.state, self.ticket), raw)
        public = s.public_lease_fields(committed.state)
        self.assertNotIn(self.ticket, public["leaseActive"])
        self.assertEqual(
            public["commitments"], ((self.ticket, v["worker_id"], 0, "sha256:" + "e" * 64),)
        )
        retried = s.invoke(
            committed.state,
            "commit",
            self.ticket,
            tick=99,
            worker="unrelated",
            epoch=999,
            commitment="sha256:" + "e" * 64,
        )
        self.assertEqual(retried.state, committed.state)
        self.assertEqual(retried.receipt_sequence, 4)
        self.assertEqual(retried.disposition, "replay")
        with self.assertRaises(CodecError):
            s.invoke(
                committed.state,
                "renew",
                self.ticket,
                tick=20,
                worker=v["worker_id"],
                epoch=0,
                renewal=0,
            )
        no_op = s.invoke(
            committed.state,
            "expire",
            self.ticket,
            tick=99,
            token=s.timer(self.initial, self.ticket),
        )
        self.assertEqual(no_op.state, committed.state)
        self.assertEqual(no_op.disposition, "committed_noop")

    def test_renew_stale_timer_and_original_receipt(self):
        old = s.timer(self.initial, self.ticket)
        v = s.decode(s.current(self.initial, self.ticket))
        renewed = s.invoke(
            self.initial,
            "renew",
            self.ticket,
            tick=v["issue_tick"],
            worker=v["worker_id"],
            epoch=0,
            renewal=0,
        )
        stale = s.invoke(renewed.state, "expire", self.ticket, tick=99, token=old)
        self.assertEqual(stale.state, renewed.state)
        self.assertEqual(stale.disposition, "stale_noop")
        replay = s.invoke(
            renewed.state,
            "renew",
            self.ticket,
            tick=v["issue_tick"],
            worker=v["worker_id"],
            epoch=0,
            renewal=0,
        )
        self.assertEqual(replay.receipt_sequence, 4)
        self.assertEqual(replay.state, renewed.state)

    def test_infeasibility_does_not_publish_partial_leases(self):
        self.assertIsNone(s.allocate(self.plan, self.workers[:1], 15))

    def test_original_bounds_and_no_hidden_json_safe_integer_narrowing(self):
        context = {k: self.data["domain_policies"][0]["value"][k] for k in s.CONTEXT}
        policy = copy.deepcopy(self.data["domain_policies"][0]["value"])
        policy.update(token_cursor_start=2**53, token_cursor_end=2**53 + 4096)
        self.assertEqual(s.policy(s.canonical(policy), context, self.plan.semantics), policy)
        policy["token_cursor_end"] = 2**64
        with self.assertRaises(CodecError):
            s.canonical(policy)

    def test_order_and_duplicate_members_are_not_reinterpreted(self):
        raw = self.plan.policies[0]
        with self.assertRaises(CodecError):
            s.decode(b'{"x":1,"x":2}')
        with self.assertRaises(CodecError):
            s.decode(raw + b" ")
        with self.assertRaises(CodecError):
            s.decode(b'{"x":1.0}')


if __name__ == "__main__":
    unittest.main()
