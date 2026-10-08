"""Full W1 byte join, deliberately without a purported complete producer origin."""

import unittest
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto.codec import CodecError, content_id
from formal.reference.isc_source import finalization as f
from formal.reference.isc_source import test_finalization as fixture
from formal.reference.isc_source.policy import decode, encode
from formal.reference.isc_w1 import codec as w
from formal.reference.isc_w1.test_harness import legacy
from formal.reference.profile_source import capsule_binding as c


class CapsuleBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.CandidateTests.setUpClass()

    def setUp(self):
        self.x = fixture.CandidateTests()
        policy, cut, self.old = self.x.source()
        self.body = self.x.body
        self.native = {
            "available_ticket_count": 1,
            "committed_ticket_count": 1,
            "config_id": self.body.round_config_id,
            "durable_sequence": "1",  # coarse command counter, not s or V_a(s)
            "formal_semantics_id": self.body.formal_semantics_id,
            "height": str(cut.height),
            "parent_checkpoint_id": cut.parent_checkpoint_id,
            "phase": "AVAILABLE",
            "round_id": self.body.round_id,
            "schema_version": "1.0.0",
            "state_root": "sha256:" + "b" * 64,
            "ticket_count": 1,
            "type_name": "ROUND_STATE",
            "view": str(cut.view),
        }
        raw_state = c.envelope(5, self.native)
        sid = content_id("deltareduce:003:round-state:v1", raw_state)
        p = decode(policy)
        p["snapshot"]["state_id"] = sid
        policy, cut = encode(p), replace(cut, state_id=sid)
        # Byte-valid original prefix only; legacy() placeholders do not claim
        # legal commands. The independent producer join is still outstanding.
        prefix = w.encode_frame(legacy(1)) + w.encode_frame(
            w.Frame(2, 2, (cut.delivered[0].event.vote_frame, b"", b"", b"original-policy-digest"))
        )
        self.prior = c.Predecessor(prefix, "sha256:" + "d" * 64, 7, raw_state, policy, cut)
        self.candidate = f.assemble_first(self.x.bootstrap, self.x.backend, policy, self.body, cut)
        self.command = {
            "actor_id": p["local_validator_id"],
            "body_hash": self.candidate.consensus_id,
            "command_kind": "FINALIZE_ISC",
            "formal_semantics_id": self.body.formal_semantics_id,
            "height": str(cut.height),
            "logical_tick": str(cut.logical_tick),
            "request_id": "original-finalize-request",
            "round_id": self.body.round_id,
            "schema_version": "1.0.0",
            "type_name": "COMMAND",
            "view": str(cut.view),
        }
        raw_command = c.envelope(6, self.command)
        effects = c.publish_bytes(
            self.body.formal_semantics_id, self.command, raw_state, self.candidate.witness_id
        )
        self.request = w.RequestSource(
            raw_command,
            len(prefix),
            sha256(prefix).digest(),
            self.prior.source_index_id,
            self.prior.source_cut,
            raw_state,
            policy,
            tuple(r.event for r in cut.delivered),
        )
        self.state = w.CandidateState(self.candidate.next_policy, self.candidate.certificate)
        self.receipt = w.Receipt(
            3,
            content_id("deltareduce:003:command:v1", raw_command),
            self.candidate.witness_id,
            content_id("deltareduce:003:effect-batch:v1", effects),
            sha256(policy).hexdigest(),
            sha256(self.state.policy_bytes).hexdigest(),
        )
        self.frame = w.Frame(
            3,
            3,
            (
                w.encode_request_source(self.request),
                w.encode_candidate_state(self.state),
                effects,
                w.encode_receipt(self.receipt),
            ),
        )

    def check(self, frame=None, prior=None):
        return c.bind(
            self.x.bootstrap,
            self.x.backend,
            w.encode_frame(self.frame if frame is None else frame),
            self.prior if prior is None else prior,
            self.body,
        )

    def section(self, index, raw):
        parts = list(self.frame.sections)
        parts[index] = raw
        return replace(self.frame, sections=tuple(parts))

    def test_complete_original_w1_reconstructed_without_changing_coarse_state(self):
        result = self.check()
        self.assertEqual(result.original, w.encode_frame(self.frame))
        self.assertEqual(result.physical_slot, 3)
        self.assertEqual(result.predecessor.native_state, self.prior.native_state)
        self.assertEqual(
            c.read_state(self.prior.native_state, self.body.formal_semantics_id)[
                "durable_sequence"
            ],
            "1",
        )
        self.assertEqual(result.candidate.original_deliveries, self.prior.cut.delivered)
        self.assertIn(
            f.certificate_tree(self.old),
            decode(result.candidate.next_policy)["snapshot"]["input_set_certificates"],
        )

    def test_no_source_substitution_or_quorum_subset(self):
        for changed in (
            replace(self.request, source_index_id="sha256:" + "e" * 64),
            replace(self.request, source_cut_event_index=8),
            replace(self.request, deliveries=self.request.deliveries[:3]),
            replace(self.request, prior_state_bytes=c.envelope(5, {**self.native, "view": "3"})),
        ):
            with self.assertRaisesRegex(CodecError, "independent predecessor"):
                self.check(self.section(0, w.encode_request_source(changed)))

    def test_b_c_substitution_rejected_even_with_recomputed_integrity(self):
        raw = c.envelope(6, {**self.command, "body_hash": self.candidate.witness_id})
        with self.assertRaisesRegex(CodecError, "consensus b"):
            self.check(
                self.section(0, w.encode_request_source(replace(self.request, command_bytes=raw)))
            )
        with self.assertRaisesRegex(CodecError, "receipt IDs"):
            self.check(
                self.section(
                    3,
                    w.encode_receipt(
                        replace(self.receipt, certificate_id=self.candidate.consensus_id)
                    ),
                )
            )

    def test_lineage_erasure_is_not_a_valid_candidate(self):
        value = decode(self.state.policy_bytes)
        value["snapshot"]["input_set_certificates"] = [
            f.certificate_tree(f.read_certificate_tree(self.body.formal_semantics_id, row))
            for row in value["snapshot"]["input_set_certificates"]
            if row["context"]["round_id"] == self.body.round_id
        ]
        changed = encode(value)
        parts = list(self.frame.sections)
        parts[1] = w.encode_candidate_state(replace(self.state, policy_bytes=changed))
        parts[3] = w.encode_receipt(
            replace(self.receipt, next_policy_digest=sha256(changed).hexdigest())
        )
        with self.assertRaisesRegex(CodecError, "no lineage erasure"):
            self.check(replace(self.frame, sections=tuple(parts)))

    def test_no_implicit_time_advance_resequencing_or_seed_effect(self):
        raw = c.envelope(6, {**self.command, "logical_tick": str(self.prior.cut.logical_tick + 1)})
        with self.assertRaisesRegex(CodecError, "no implicit clock"):
            self.check(
                self.section(0, w.encode_request_source(replace(self.request, command_bytes=raw)))
            )
        parts = list(self.frame.sections)
        parts[3] = w.encode_receipt(replace(self.receipt, sequence=4))
        with self.assertRaisesRegex(CodecError, "next original physical"):
            self.check(replace(self.frame, sequence=4, sections=tuple(parts)))
        # Publish-effect modification plus a correct recomputed batch ID cannot
        # authorize any extra seed effect or another target.
        effects = self.frame.sections[2].replace(b"validators", b"seed-peers")
        parts = list(self.frame.sections)
        parts[2] = effects
        parts[3] = w.encode_receipt(
            replace(
                self.receipt, effect_batch_id=content_id("deltareduce:003:effect-batch:v1", effects)
            )
        )
        with self.assertRaisesRegex(CodecError, "single original witness"):
            self.check(replace(self.frame, sections=tuple(parts)))


if __name__ == "__main__":
    unittest.main()
