"""Synthetic exact-cut tests; no production history or independent attestation."""

import unittest
from copy import deepcopy
from dataclasses import replace

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import identity, policy
from formal.reference.non_isc import codec
from formal.reference.profile_source import ec_finalization as ec
from formal.reference.profile_source.ec_finalization_vectors import fixture
from formal.reference.profile_source.source_prefix import Event


class EcFinalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = fixture()

    def run_candidate(self, *, cut=4, prior=None, rows=None, state=None, body=None, tick=0):
        f = self.f
        return ec.assemble_first(
            f["authority"],
            f["backend"],
            prior or f["prior"],
            state or f["state"],
            body or f["body"],
            f["rows"] if rows is None else rows,
            actor=f["p"]["local_validator_id"],
            cut=cut,
            tick=tick,
        )

    def event(self, candidate, parent=0):
        f = self.f
        return Event(
            candidate.cut + 1,
            candidate.actor,
            "ACT-EC-FINALIZE",
            candidate.certificate,
            (
                candidate.prior_policy,
                candidate.original_state,
                candidate.body,
                identity.certificate_bytes(f["isc_certificates"][parent]),
                f["seed"],
                f["norm"],
            ),
            tuple(sorted({0, *candidate.matching_positions})),
            b"synthetic descriptor",
        )

    def bind(self, candidate, event):
        return ec.bind_event(candidate, event, *event.inputs[3:], (0,))

    def test_three_four_cut_and_distinct_witness_identity(self):
        a, b = self.run_candidate(), self.run_candidate(cut=5)
        self.assertEqual(a.signers, tuple(self.f["p"]["validator_ids"][:3]))
        self.assertEqual(b.signers, tuple(self.f["p"]["validator_ids"]))
        self.assertNotEqual(a.certificate_id, b.certificate_id)
        self.assertEqual(a.original_deliveries, self.f["rows"])
        self.assertEqual(a.matching_positions, (1, 2, 3, 4))
        self.assertEqual(b.matching_positions, (1, 2, 3, 4, 5))
        self.assertEqual(
            len(policy.decode(a.next_policy)["snapshot"]["eligibility_certificates"]), 2
        )
        self.assertEqual(
            len(policy.decode(b.next_policy)["snapshot"]["eligibility_certificates"]), 1
        )

    def test_exact_two_field_footprint_no_delivery_or_candidate_erasure(self):
        c = self.run_candidate()
        before, after = policy.decode(c.prior_policy), policy.decode(c.next_policy)
        for key in before:
            if key != "snapshot":
                self.assertEqual(before[key], after[key])
        for key in before["snapshot"]:
            if key not in ("eligibility_certificates", "finalized_eligibility_ids"):
                self.assertEqual(before["snapshot"][key], after["snapshot"][key])
        self.assertEqual(c.original_state, self.f["state"])
        self.assertEqual(c.original_deliveries, self.f["rows"])

    def test_same_original_vote_delivery_cannot_create_quorum(self):
        r = self.f["rows"][0]
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(rows=tuple(replace(r, position=i) for i in (1, 2, 3)))
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(rows=(r, r, self.f["rows"][1]))

    def test_first_key_blocks_later_witness_and_missing_finalized_reference(self):
        first = self.run_candidate()
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(cut=5, prior=first.next_policy)
        p = deepcopy(self.f["p"])
        p["snapshot"]["finalized_eligibility_ids"] = ["sha256:" + "f" * 64]
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(prior=policy.encode(p))

    def test_seed_collision_and_b_c_substitution(self):
        p = deepcopy(self.f["p"])
        p["snapshot"]["eligibility_certificates"][0]["seed_transcript_id"] = "sha256:" + "f" * 64
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(prior=policy.encode(p), cut=5)
        p = deepcopy(self.f["p"])
        p["snapshot"]["eligibility_bodies"][0]["input_set_certificate_id"] = (
            identity.certificate_id(self.f["isc_certificates"][0])
        )
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(
                prior=policy.encode(p), body=ec.body_bytes(p["snapshot"]["eligibility_bodies"][0])
            )

    def test_quorum_incomplete_hard_deadline_and_abort_do_not_mutate_inputs(self):
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(cut=2)
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(tick=self.f["p"]["hard_deadline_tick"])
        p = deepcopy(self.f["p"])
        state = ec.wire.read_state(self.f["state"], self.f["boot"].formal_semantics_id)
        state["phase"] = "ABORTED"
        raw = ec.wire.envelope(5, state)
        p["snapshot"]["state_id"] = crypto.content_id("deltareduce:003:round-state:v1", raw)
        prior = policy.encode(p)
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(prior=prior, state=raw)
        self.assertEqual(policy.encode(p), prior)
        self.assertEqual(
            p["snapshot"]["eligibility_certificates"],
            self.f["p"]["snapshot"]["eligibility_certificates"],
        )

    def test_valid_signature_wrong_full_context_and_bad_signature_fail_closed(self):
        f = self.f
        vote, artifact, _ = f["signed_values"][2]
        altered = replace(vote, view=vote.view + 1)
        raw_vote = codec.encode_vote(codec.NonIscVote(altered, "EC"))
        from formal.reference.profile_source.test_configuration import ConfigurationTests

        test = ConfigurationTests()
        _, signature = f["backend"].sign(
            test.signer.seeds[vote.validator_id],
            codec.preimage(artifact.registry_id, artifact.key_id, raw_vote),
        )
        g = codec.encode_artifact(replace(artifact, vote_bytes=raw_vote, signature=signature))
        rows = list(f["rows"])
        rows[2] = replace(rows[2], original_g=g)
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(rows=tuple(rows))
        rows[2] = replace(
            rows[2],
            original_g=f["rows"][2].original_g[:-1] + bytes([f["rows"][2].original_g[-1] ^ 1]),
        )
        with self.assertRaises(crypto.CodecError):
            self.run_candidate(rows=tuple(rows))

    def test_original_c_is_preserved_for_either_witness_of_same_b(self):
        c = self.run_candidate()
        self.assertNotEqual(self.event(c, 0).inputs[3], self.event(c, 1).inputs[3])
        for parent in (0, 1):
            self.assertIs(self.bind(c, self.event(c, parent)), c)

    def test_cut_actor_six_refs_and_all_duplicate_dependencies(self):
        c = self.run_candidate(cut=5)
        event = self.event(c)
        self.assertIs(self.bind(c, event), c)
        for bad in (
            replace(event, index=event.index + 1),
            replace(event, actor="different-actor"),
            replace(event, dependencies=tuple(i for i in event.dependencies if i != 4)),
            replace(event, dependencies=tuple(i for i in event.dependencies if i != 5)),
            replace(event, original=b"wrong"),
            replace(event, inputs=event.inputs[::-1]),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(crypto.CodecError):
                    self.bind(c, bad)

    def test_reobserve_original_cut_after_later_delivery_and_abort(self):
        c = self.run_candidate()
        current = policy.decode(c.next_policy)
        state = ec.wire.read_state(c.original_state, c.semantics)
        # This tests byte retention, not authority of a manufactured ABORT.
        state["phase"] = "ABORTED"
        state_raw = ec.wire.envelope(5, state)
        current["snapshot"]["state_id"] = crypto.content_id(
            "deltareduce:003:round-state:v1", state_raw
        )
        raw = policy.encode(current)
        result = ec.reobserve(
            self.f["authority"],
            self.f["backend"],
            self.event(c),
            self.f["rows"],
            0,
            (0,),
            current_policy=raw,
            current_state=state_raw,
            current_rows=self.f["rows"],
        )
        self.assertEqual(result.original, c)
        self.assertEqual(result.original.signers, tuple(self.f["p"]["validator_ids"][:3]))
        self.assertEqual(result.current_policy, raw)
        self.assertEqual(result.current_state, state_raw)
        self.assertEqual(result.current_deliveries, self.f["rows"])
        # A later four-signer witness cannot substitute for the old event.
        altered = replace(self.event(c), original=self.run_candidate(cut=5).certificate)
        with self.assertRaises(crypto.CodecError):
            ec.reobserve(
                self.f["authority"],
                self.f["backend"],
                altered,
                self.f["rows"],
                0,
                (0,),
                current_policy=raw,
                current_state=state_raw,
                current_rows=self.f["rows"],
            )


if __name__ == "__main__":
    unittest.main()
