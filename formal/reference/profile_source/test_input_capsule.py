"""Composed authority/CONFIG/input/source-cut/W1 reference fixture, not full R2.

Genesis, coarse initial state, unused policy/candidate/anchor placeholders and
phase/durability remain deliberately unqualified. Never a valid import or GO.
"""

import unittest
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import authentication as authentication
from formal.reference.isc_source import finalization as finalization
from formal.reference.isc_source import identity as identity
from formal.reference.isc_source import policy as policy
from formal.reference.isc_source import test_finalization as candidate_fixture
from formal.reference.isc_w1 import codec as w
from formal.reference.profile_source import authority
from formal.reference.profile_source import capsule_binding as c
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import source_prefix as source
from formal.reference.profile_source import test_authority as authority_fixture
from formal.reference.profile_source import test_input_history as input_fixture
from formal.reference.profile_source.test_metadata import frame, ref


class InputCapsuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        input_fixture.InputHistoryTests.setUpClass()
        authority_fixture.AuthorityTests.setUpClass()
        candidate_fixture.CandidateTests.setUpClass()

    def setUp(self):
        self.input = input_fixture.InputHistoryTests()
        self.input.setUp()
        self.a = authority_fixture.AuthorityTests()
        self.a.setUp()
        self.p = self.a.package
        f, body = self.input.f, self.input.body
        self.boot, self.body, self.backend = f.boot, body, f.backend
        self.actor = self.boot.validators[0][0]
        self.events = list(self.input.events)
        registry_id, keys = authentication.registry(self.boot)
        deliveries = []
        for name, _ in self.boot.validators:
            vote = crypto.Vote(
                identity.body_id(body),
                identity.vote_context_id(body.round_id),
                1,
                self.boot.formal_semantics_id,
                body.height,
                body.round_id,
                self.boot.validator_epoch_id,
                name,
                body.view,
            )
            raw = crypto.encode_vote(vote)
            key_id, _ = keys[name]
            signable = crypto.preimage(registry_id, key_id, raw)
            _, sig = self.backend.sign(f.signer.seeds[name], signable)
            g = crypto.encode_artifact(crypto.Artifact(registry_id, key_id, raw, sig))
            delivered = w.Delivery(len(self.events), "original-relay", raw, signable, sig, key_id)
            self.events.append(
                source.Event(
                    len(self.events),
                    self.actor,
                    "ACT-MESSAGE-DELIVER",
                    w.encode_delivery(delivered),
                    (g, identity.body_preimage(body)),
                    (),
                    b"synthetic-original",
                )
            )
            deliveries.append(finalization.DeliverySource(delivered, g, body))
        native = {
            "available_ticket_count": 1,
            "committed_ticket_count": 1,
            "ticket_count": 1,
            "config_id": body.round_config_id,
            "durable_sequence": "0",
            "formal_semantics_id": self.boot.formal_semantics_id,
            "height": str(body.height),
            "parent_checkpoint_id": body.parent_checkpoint_id,
            "phase": "AVAILABLE",
            "round_id": body.round_id,
            "schema_version": "1.0.0",
            "state_root": m.raw_id(b"unqualified-initial-state"),
            "type_name": "ROUND_STATE",
            "view": str(body.view),
        }
        self.initial = c.envelope(5, native)
        state_id = crypto.content_id("deltareduce:003:round-state:v1", self.initial)
        raw_policy, _, _ = candidate_fixture.CandidateTests().source()
        p = policy.decode(raw_policy)
        p.update(
            validator_epoch_id=self.boot.validator_epoch_id,
            validator_ids=[n for n, _ in self.boot.validators],
            local_validator_id=self.actor,
            round_id=body.round_id,
            round_config_id=body.round_config_id,
        )
        p["snapshot"].update(
            parameter_schema_id=body.parameter_schema_id,
            arithmetic_profile_id=body.arithmetic_profile_id,
            state_id=state_id,
            finalized_round_config_ids=[body.round_config_id],
            closed_input_set_ids=[identity.body_id(body)],
            input_set_bodies=[finalization.body_tree(body)],
            # This fresh fixture exercises the first ISC of this generation.
            # It is not a conversion of the template's historical witnesses.
            input_set_certificates=[],
            finalized_input_set_ids=[],
        )
        self.policy = policy.encode(p)
        cut = finalization.Cut(
            state_id,
            body.parent_checkpoint_id,
            body.height,
            body.view,
            7,
            body.tuples,
            tuple(deliveries),
        )
        candidate = finalization.assemble_first(self.boot, self.backend, self.policy, body, cut)
        command = {
            "actor_id": self.actor,
            "body_hash": candidate.consensus_id,
            "command_kind": "FINALIZE_ISC",
            "formal_semantics_id": self.boot.formal_semantics_id,
            "height": str(body.height),
            "logical_tick": "7",
            "request_id": "original-finalize",
            "round_id": body.round_id,
            "schema_version": "1.0.0",
            "type_name": "COMMAND",
            "view": str(body.view),
        }
        raw_command = c.envelope(6, command)
        originals = {raw for _, raw in self.p.artifacts} | {b"", self.initial, self.policy}
        for event in self.events:
            originals.update((event.original, *event.inputs))
        self.p.boot["genesis_ref"] = ref(self.initial)
        self.p.index.update(
            genesis_ref=ref(self.initial),
            events=self.rows(self.events),
            artifacts=self.table(originals),
            original_journal_refs=[self.journal(b"", 0)],
        )
        self.prior_index = m.canonical(self.p.index)
        effects = c.publish_bytes(
            self.boot.formal_semantics_id, command, self.initial, candidate.witness_id
        )
        request = w.RequestSource(
            raw_command,
            0,
            sha256(b"").digest(),
            m.document_id(self.prior_index, "SOURCE_INDEX"),
            len(self.events) - 1,
            self.initial,
            self.policy,
            tuple(deliveries[i].event for i in range(4)),
        )
        self.w1 = w.encode_frame(
            w.Frame(
                1,
                3,
                (
                    w.encode_request_source(request),
                    w.encode_candidate_state(
                        w.CandidateState(candidate.next_policy, candidate.certificate)
                    ),
                    effects,
                    w.encode_receipt(
                        w.Receipt(
                            1,
                            crypto.content_id("deltareduce:003:command:v1", raw_command),
                            candidate.witness_id,
                            crypto.content_id("deltareduce:003:effect-batch:v1", effects),
                            sha256(self.policy).hexdigest(),
                            sha256(candidate.next_policy).hexdigest(),
                        )
                    ),
                ),
            )
        )
        self.consumer = len(self.events)
        self.events.append(
            source.Event(
                self.consumer,
                self.actor,
                "ACT-ISC-FINALIZE",
                self.w1,
                (self.prior_index,),
                (),
                b"original-finalization",
            )
        )
        originals.update((self.prior_index, self.w1))
        self.p.artifacts = tuple(sorted((m.raw_id(raw), raw) for raw in originals))
        table = self.table(originals)
        self.p.index.update(
            events=self.rows(self.events),
            artifacts=table,
            original_journal_refs=[self.journal(self.w1, 1)],
        )
        self.p.index_raw, self.p.boot_raw = m.canonical(self.p.index), m.canonical(self.p.boot)
        bid = m.document_id(self.p.boot_raw, "BOOTSTRAP")
        self.p.record.update(bootstrap_id=bid, journal_cuts=[self.journal(b"", 0)])
        self.p.manifest.update(
            bootstrap_id=bid,
            artifacts=table,
            source_index_ref=ref(self.p.index_raw),
            cut_event_index=str(self.consumer),
            target_event_index=str(self.consumer + 1),
            journals=[
                {
                    "actor_id": self.actor,
                    "journal_id": "consensus",
                    "cut": self.position(b"", 0),
                    "target": self.position(self.w1, 1),
                }
            ],
        )
        self.p.trust = m.PrimitiveTrust(
            m.raw_id(self.p.boot_raw),
            m.raw_id(self.p.index_raw),
            tuple(sorted((k, self.p.boot[k]) for k in m.PINS)),
            self.p.boot_raw,
            frame(self.p.record),
            ((self.actor, "consensus", self.w1),),
        )

    @staticmethod
    def rows(events):
        return [
            {
                "actor_id": e.actor,
                "action_id": e.action,
                "original_ref": ref(e.original),
                "input_refs": list(map(ref, e.inputs)),
                "dependencies": list(map(str, e.dependencies)),
            }
            for e in events
        ]

    @staticmethod
    def table(originals):
        return sorted(map(ref, originals), key=lambda r: r["content_id"])

    @staticmethod
    def position(raw, n):
        return {
            "ref": ref(raw),
            "entry_count": str(n),
            "first_sequence": str(int(n > 0)),
            "last_sequence": str(n),
        }

    def journal(self, raw, n):
        return {"actor_id": self.actor, "journal_id": "consensus", **self.position(raw, n)}

    def check(self, **changes):
        meta = self.p.check()
        authorities = authority.resolve(meta, self.a.keys, self.a.registry, self.a.storage_keys)
        args = dict(
            journal_id="consensus",
            physical_slot=1,
            consumer_index=self.consumer,
            original_prior_index=self.prior_index,
            initial_state=self.initial,
            initial_tick=2,
            original_policy=self.policy,
            logical_tick=7,
            plan=self.input.plan,
            original_config=self.input.config,
            declaration=self.input.f.declaration,
        )
        args.update(changes)
        return c.bind_input_indexed(authorities, self.backend, source.materialize(meta), **args)

    def test_original_full_input_cut_drives_w1_body_and_frozen_tuples(self):
        result = self.check()
        self.assertEqual(result.capsule.bound.original, self.w1)
        self.assertEqual(result.capsule.bound.predecessor.cut.frozen_inputs, self.body.tuples)
        self.assertEqual(result.input_source.closed[0].body, self.body)
        self.assertTrue(result.input_source.producer_edges)  # not whole native origin

    def test_w1_cannot_select_another_plan_or_missing_declaration(self):
        altered = replace(self.input.plan, policies=())
        for changes in ({"plan": altered}, {"declaration": b"different-original"}):
            with self.assertRaises(crypto.CodecError):
                self.check(**changes)


if __name__ == "__main__":
    unittest.main()
