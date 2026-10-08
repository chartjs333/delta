"""Real signature joins over synthetic original occurrences; no source-origin claim."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_w1.codec import Delivery
from formal.reference.non_isc import codec as votes
from formal.reference.profile_source import configuration as c
from formal.reference.profile_source import configuration_qc as q
from formal.reference.profile_source import test_configuration as fixture


class ConfigQcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ConfigurationTests.setUpClass()
        cls.f = fixture.ConfigurationTests()

    def setUp(self):
        self.body = self.f.body()
        self.raw = c.encode(self.body)
        self.names = [name for name, _ in self.f.boot.validators]
        self.delivered = tuple(self.delivery(i + 1, name) for i, name in enumerate(self.names))
        self.qc = {
            "body_hash": crypto.content_id(c.DOMAIN, self.raw),
            "context_id": c.vote_context(1, self.f.boot.validator_epoch_id),
            "formal_semantics_id": self.f.boot.formal_semantics_id,
            "height": "1",
            "kind": "ROUND_CONFIG",
            "qc_id": "sha256:" + "5" * 64,
            "quorum_threshold": 3,
            "round_id": self.body["round_id"],
            "schema_version": "1.0.0",
            "signer_ids": self.names,
            "type_name": "QUORUM_CERTIFICATE",
            "validator_epoch_id": self.f.boot.validator_epoch_id,
            "view": "0",
            "vote_ids": [
                crypto.content_id(votes.VOTE_DOMAIN, d.event.vote_frame) for d in self.delivered
            ],
        }

    def delivery(self, event_index, name, **changes):
        original = crypto.Vote(
            crypto.content_id(c.DOMAIN, self.raw),
            c.vote_context(1, self.f.boot.validator_epoch_id),
            1,
            self.f.boot.formal_semantics_id,
            1,
            self.body["round_id"],
            self.f.boot.validator_epoch_id,
            name,
            0,
        )
        original = replace(original, **changes)
        raw = votes.encode_vote(votes.NonIscVote(original, "ROUND_CONFIG"))
        key_id, _ = self.f.keys[name]
        preimage = votes.preimage(self.f.registry_id, key_id, raw)
        _, sig = self.f.backend.sign(self.f.signer.seeds[name], preimage)
        artifact = votes.encode_artifact(crypto.Artifact(self.f.registry_id, key_id, raw, sig))
        return q.DeliverySource(
            Delivery(event_index, "relay-is-not-signer", raw, preimage, sig, key_id), artifact
        )

    def check(self, delivered=None, qc=None, cut=20):
        return q.bind(
            self.f.boot,
            self.f.storage_boot,
            self.f.backend,
            self.raw,
            self.f.declaration,
            q.encode(self.qc if qc is None else qc),
            self.delivered if delivered is None else delivered,
            source_cut=cut,
        )

    def test_complete_cut_and_original_witness_identity(self):
        value = self.check()
        self.assertIs(value.deliveries, self.delivered)
        self.assertEqual(value.original_qc_id, self.qc["qc_id"])
        self.assertEqual(value.matching_signers, tuple(self.names))
        self.assertNotEqual(value.original_qc_id, value.config.body_id)
        self.assertEqual(q.decode(value.original), self.qc)

    def test_different_arrival_cuts_not_first_quorum_after_four_deliveries(self):
        earlier = {**self.qc, "signer_ids": self.names[:3], "vote_ids": self.qc["vote_ids"][:3]}
        self.check(self.delivered[:3], earlier, 3)
        with self.assertRaisesRegex(crypto.CodecError, "all matching"):
            self.check(self.delivered, earlier)
        self.check()  # full original cut requires the fourth signer too

    def test_repeated_delivery_retained_and_never_quorum_inflation(self):
        repeated = (
            *self.delivered,
            replace(self.delivered[0], event=replace(self.delivered[0].event, event_index=5)),
        )
        value = self.check(repeated)
        self.assertEqual(len(value.deliveries), 5)
        self.assertEqual(len(value.matching_signers), 4)
        one = self.delivered[0]
        duplicated = tuple(
            replace(one, event=replace(one.event, event_index=i)) for i in range(1, 5)
        )
        with self.assertRaisesRegex(crypto.CodecError, "all matching"):
            self.check(duplicated)

    def test_original_material_order_context_and_vote_identity(self):
        for changed in (
            tuple(reversed(self.delivered)),
            (*self.delivered, self.delivery(5, self.names[0], durable_sequence=2)),
            (
                *self.delivered[:-1],
                replace(
                    self.delivered[-1],
                    event=replace(self.delivered[-1].event, key_id=self.delivered[0].event.key_id),
                ),
            ),
        ):
            with self.assertRaises(crypto.CodecError):
                self.check(changed)
        with self.assertRaises(crypto.CodecError):
            self.check(cut=3)
        for key, value in (
            ("body_hash", self.qc["qc_id"]),
            ("context_id", self.qc["qc_id"]),
            ("quorum_threshold", 2),
            ("vote_ids", list(reversed(self.qc["vote_ids"]))),
        ):
            with self.subTest(key=key), self.assertRaises(crypto.CodecError):
                self.check(qc={**self.qc, key: value})


if __name__ == "__main__":
    unittest.main()
