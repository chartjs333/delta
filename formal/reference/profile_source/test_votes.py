"""Original signed/unsigned vote intents across mixed physical WAL slots."""

import unittest
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as c
from formal.reference.isc_w1.codec import Frame, encode_frame
from formal.reference.isc_w1.test_harness import capsule, legacy
from formal.reference.non_isc import codec as n
from formal.reference.profile_source import journals, votes
from formal.reference.profile_source import test_configuration as fixtures


class VoteIntentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ConfigurationTests.setUpClass()
        cls.f = fixtures.ConfigurationTests()

    def setUp(self):
        self.raw_config = fixtures.c.encode(self.f.body())
        self.first_g = self.f.sign(self.raw_config)
        self.first = n.decode_artifact(self.first_g).vote_bytes
        self.actor = self.f.boot.validators[0][0]
        self.policy_digest = (
            sha256(b"original policy supplied to later admission checker").hexdigest().encode()
        )

    def journal(self, last=None):
        first = legacy(1)
        intent = Frame(2, 2, (self.first, b"", b"", self.policy_digest))
        prefix = encode_frame(first) + encode_frame(intent)
        self.prefix = prefix
        raw = prefix + encode_frame(capsule(3, prefix))
        if last is not None:
            raw += encode_frame(Frame(4, 2, (last, b"", b"", self.policy_digest)))
        return journals.inspect(raw, cut_slot=2, required_prefix=prefix)

    def check(self, journal, signatures):
        return votes.bind(self.f.boot, self.f.backend, self.actor, journal, signatures)

    def test_unsigned_durable_cut_is_retained_without_claiming_signature(self):
        journal = self.journal()
        result = self.check(journal, ())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].signed_artifacts, ())
        self.assertEqual(result[0].original_vote, self.first)
        self.assertEqual(result[0].vote.durable_sequence, 1)
        self.assertEqual(result[0].position.decoded.sequence, 2)
        signed = self.check(journal, (self.first_g, self.first_g))
        self.assertEqual(signed[0].signed_artifacts, (self.first_g, self.first_g))
        self.assertEqual(len(signed), 1)

    def test_mixed_slots_keep_two_original_vote_identities(self):
        second_g = self.f.sign(
            self.raw_config, {"durable_sequence": 2, "context_id": "sha256:" + "6" * 64}
        )
        second = n.decode_artifact(second_g).vote_bytes
        result = self.check(self.journal(second), (self.first_g, second_g))
        self.assertEqual([i.position.decoded.sequence for i in result], [2, 4])
        self.assertEqual([i.vote.durable_sequence for i in result], [1, 2])
        self.assertEqual([i.original_vote for i in result], [self.first, second])
        # The arbitrary second context is not claimed valid CONFIG admission.

    def test_physical_slot_as_vote_rank_and_second_context_vote_rejected(self):
        value = n.decode_vote(self.first)
        for changed in (
            replace(value.original, durable_sequence=4),
            replace(value.original, durable_sequence=2),
        ):
            raw = n.encode_vote(n.NonIscVote(changed, value.kind))
            with self.assertRaises(c.CodecError):
                self.check(self.journal(raw), (self.first_g,))

    def test_signature_without_own_intent_or_corrupt_signature_rejected(self):
        other = self.f.sign(self.raw_config, {"context_id": "sha256:" + "7" * 64})
        for signatures in ((other,), (self.first_g[:-1] + bytes([self.first_g[-1] ^ 1]),)):
            with self.assertRaises(c.CodecError):
                self.check(self.journal(), signatures)


if __name__ == "__main__":
    unittest.main()
