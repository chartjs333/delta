"""Candidate composition on synthetic cuts, not producer-origin evidence."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError, decode_artifact, preimage
from formal.reference.isc_source import test_authentication
from formal.reference.isc_source.finalization import (
    Cut,
    DeliverySource,
    assemble_first,
    body_tree,
    certificate_tree,
)
from formal.reference.isc_source.identity import (
    Certificate,
    body_id,
    certificate_id,
    decode_certificate,
)
from formal.reference.isc_source.policy import decode, encode
from formal.reference.isc_source.test_policy import structural_policy
from formal.reference.isc_w1.codec import Delivery


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_authentication.AuthenticationTests.setUpClass()
        cls.auth = test_authentication.AuthenticationTests()
        cls.body = cls.auth.body
        cls.bootstrap, cls.backend = cls.auth.bootstrap, cls.auth.backend

    def delivered(self, signers, first=1):
        result = []
        for index, signer in enumerate(signers, first):
            raw = self.auth.signed(signer)
            artifact = decode_artifact(raw)
            event = Delivery(
                index,
                "relay-peer",
                artifact.vote_bytes,
                preimage(artifact.registry_id, artifact.key_id, artifact.vote_bytes),
                artifact.signature,
                artifact.key_id,
            )
            result.append(DeliverySource(event, raw, self.body))
        return tuple(result)

    def source(self, signers=None):
        names = tuple(self.auth.seeds)
        if signers is None:
            signers = names
        policy = structural_policy()
        policy.update(
            local_validator_id=names[0],
            validator_ids=list(names),
            validator_epoch_id=self.body.validator_epoch_id,
            round_id=self.body.round_id,
            round_config_id=self.body.round_config_id,
            initial_logical_tick=2,
            hard_deadline_tick=20,
        )
        old = Certificate(replace(self.body, round_id="earlier-round", height=6), names[:3])
        snapshot = policy["snapshot"]
        snapshot.update(
            state_id="sha256:" + "9" * 64,
            parameter_schema_id=self.body.parameter_schema_id,
            arithmetic_profile_id=self.body.arithmetic_profile_id,
            finalized_round_config_ids=[self.body.round_config_id],
            closed_input_set_ids=[body_id(self.body)],
            input_set_bodies=[body_tree(self.body)],
            input_set_certificates=[certificate_tree(old)],
            finalized_input_set_ids=[body_id(old.body)],
            abort_requests=[],
        )
        cut = Cut(
            snapshot["state_id"],
            self.body.parent_checkpoint_id,
            self.body.height,
            self.body.view,
            7,
            self.body.tuples,
            self.delivered(signers),
        )
        # Other nonempty collections are opaque sentinel structures: deliberately
        # not a legal full native state. They MUST survive this local delta.
        return encode(policy), cut, old

    def assemble(self, prior, cut):
        return assemble_first(self.bootstrap, self.backend, prior, self.body, cut)

    def test_full_prior_lineage_and_original_delivery_inventory_retained(self):
        prior, cut, old = self.source()
        repeated = self.delivered((next(iter(self.auth.seeds)),), first=5)
        cut = replace(cut, delivered=cut.delivered + repeated)
        result = self.assemble(prior, cut)
        self.assertEqual(result.original_deliveries, cut.delivered)
        self.assertEqual(result.prior_policy, prior)
        before, after = decode(prior), decode(result.next_policy)
        changed = {"input_set_certificates", "finalized_input_set_ids"}
        for key in before:
            if key != "snapshot":
                self.assertEqual(before[key], after[key], key)
        for key in before["snapshot"]:
            if key not in changed:
                self.assertEqual(before["snapshot"][key], after["snapshot"][key], key)
        self.assertIn(certificate_tree(old), after["snapshot"]["input_set_certificates"])
        self.assertEqual(len(after["snapshot"]["input_set_certificates"]), 2)
        self.assertEqual(decode_certificate(result.certificate).signer_ids, tuple(self.auth.seeds))

    def test_different_arrival_cuts_same_b_distinct_c_no_replay_reassembly(self):
        names = tuple(self.auth.seeds)
        prior, early, _ = self.source(names[:3])
        _, late, _ = self.source(names)
        first, second = self.assemble(prior, early), self.assemble(prior, late)
        self.assertEqual(first.consensus_id, second.consensus_id)
        self.assertNotEqual(first.witness_id, second.witness_id)
        with self.assertRaisesRegex(CodecError, "original replay receipt required"):
            self.assemble(first.next_policy, late)
        self.assertEqual(decode_certificate(first.certificate).signer_ids, names[:3])

    def test_repeat_does_not_create_quorum_and_bad_duplicate_material_rejects(self):
        names = tuple(self.auth.seeds)
        prior, cut, _ = self.source((names[0], names[0], names[1]))
        with self.assertRaisesRegex(CodecError, "insufficient distinct"):
            self.assemble(prior, cut)
        prior, cut, _ = self.source()
        changed = replace(cut.delivered[0].event, signature_bytes=bytes(64))
        bad = replace(cut.delivered[0], event=changed)
        with self.assertRaisesRegex(CodecError, "W1 delivery"):
            self.assemble(prior, replace(cut, delivered=(bad, *cut.delivered[1:])))

    def test_exact_parent_closed_list_time_and_identity_roles_required(self):
        prior, cut, old = self.source()
        for changed in (
            replace(cut, parent_checkpoint_id="sha256:" + "f" * 64),
            replace(cut, frozen_inputs=()),
            replace(cut, logical_tick=20),
            replace(cut, view=cut.view + 1),
        ):
            with self.assertRaises(CodecError):
                self.assemble(prior, changed)
        policy = decode(prior)
        policy["snapshot"]["finalized_input_set_ids"] = [certificate_id(old)]
        with self.assertRaisesRegex(CodecError, "missing original witness"):
            self.assemble(encode(policy), cut)
        policy = decode(prior)
        policy["snapshot"]["closed_input_set_ids"] = [
            certificate_id(Certificate(self.body, tuple(self.auth.seeds)))
        ]
        with self.assertRaisesRegex(CodecError, "closed frozen body"):
            self.assemble(encode(policy), cut)


if __name__ == "__main__":
    unittest.main()
