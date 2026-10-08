"""Source-index -> command/delivery -> W1 composition, not a complete native origin.

Fresh synthetic objects use a symbolic generation. Opaque other policy/anchor
fields deliberately remain unqualified; success here cannot close full R2.3.
"""

import copy
import unittest
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import authentication as authentication
from formal.reference.isc_source import finalization as finalization
from formal.reference.isc_source import identity as identity
from formal.reference.isc_source import policy as policy
from formal.reference.isc_source import test_authentication as auth_fixture
from formal.reference.isc_source import test_finalization as fixture
from formal.reference.isc_w1 import codec as w
from formal.reference.profile_source import capsule_binding as c
from formal.reference.profile_source import commands as commands
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import source_prefix as source
from formal.reference.profile_source.test_metadata import Package, frame, ref


class IndexedCapsuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.CandidateTests.setUpClass()

    def setUp(self):
        self.p = Package()
        self.x = fixture.CandidateTests()
        self.x.auth = auth_fixture.AuthenticationTests()
        self.x.auth.bootstrap = replace(self.x.bootstrap, origin_id=m.raw_id(b"test-origin"))
        self.x.bootstrap = self.x.auth.bootstrap
        boot = self.x.bootstrap
        self.body = self.x.body
        local = boot.validators[0][0]
        raw_policy, old_cut, _ = self.x.source()
        native = {
            "available_ticket_count": 0,
            "committed_ticket_count": 1,
            "config_id": self.body.round_config_id,
            "durable_sequence": "0",
            "formal_semantics_id": boot.formal_semantics_id,
            "height": str(self.body.height),
            "parent_checkpoint_id": self.body.parent_checkpoint_id,
            "phase": "COMMITTED",
            "round_id": self.body.round_id,
            "schema_version": "1.0.0",
            "state_root": m.raw_id(b"test-state"),
            "ticket_count": 1,
            "type_name": "ROUND_STATE",
            "view": str(self.body.view),
        }
        self.initial = c.envelope(5, native)
        command = {
            "actor_id": local,
            "body_hash": m.raw_id(b"test-original-ac-command"),
            "command_kind": "ACCEPT_AVAILABILITY",
            "formal_semantics_id": boot.formal_semantics_id,
            "height": str(self.body.height),
            "logical_tick": "7",
            "request_id": "native-command",
            "round_id": self.body.round_id,
            "schema_version": "1.0.0",
            "type_name": "COMMAND",
            "view": str(self.body.view),
        }
        computed = commands.execute(boot.formal_semantics_id, self.initial, c.envelope(6, command))
        self.prefix_wal = w.encode_frame(
            w.Frame(
                1,
                1,
                (
                    computed.original_command,
                    computed.next_state,
                    computed.effects,
                    computed.record,
                ),
            )
        )
        value = policy.decode(raw_policy)
        value["snapshot"]["state_id"] = computed.next_id
        self.policy = policy.encode(value)
        self.cut = replace(old_cut, state_id=computed.next_id)
        events = [
            {
                "actor_id": local,
                "action_id": "ACT-AVAIL-FINALIZE",
                "original_ref": ref(self.prefix_wal),
                "input_refs": [],
                "dependencies": [],
            }
        ]
        originals = {raw for _, raw in self.p.artifacts}
        originals.update((self.initial, self.prefix_wal, self.policy))
        for delivered in self.cut.delivered:
            inline = w.encode_delivery(delivered.event)
            inputs = (delivered.original_g, identity.body_preimage(delivered.original_body))
            events.append(
                {
                    "actor_id": local,
                    "action_id": "ACT-MESSAGE-DELIVER",
                    "original_ref": ref(inline),
                    "input_refs": list(map(ref, inputs)),
                    "dependencies": [],
                }
            )
            originals.update((inline, *inputs))
        _, keys = authentication.registry(boot)
        common = {
            "origin_id": boot.origin_id,
            "validator_epoch_id": boot.validator_epoch_id,
            "local_validator_id": local,
        }
        self.p.boot.update(
            common,
            formal_semantics_id=boot.formal_semantics_id,
            genesis_ref=ref(self.initial),
            validators=[
                {"validator_id": name, "key_ref": key, "roles": ["validator"]}
                for name, (key, _) in keys.items()
            ],
        )
        self.p.index.update(
            common,
            genesis_ref=ref(self.initial),
            events=events,
            artifacts=self.table(originals),
            original_journal_refs=[self.journal(self.prefix_wal, 1)],
        )
        self.prior_index = m.canonical(self.p.index)
        candidate = finalization.assemble_first(
            boot, self.x.backend, self.policy, self.body, self.cut
        )
        request_command = {
            **command,
            "command_kind": "FINALIZE_ISC",
            "body_hash": candidate.consensus_id,
            "request_id": "isc-finalize",
        }
        raw_command = c.envelope(6, request_command)
        effects = c.publish_bytes(
            boot.formal_semantics_id, request_command, computed.next_state, candidate.witness_id
        )
        self.request = w.RequestSource(
            raw_command,
            len(self.prefix_wal),
            sha256(self.prefix_wal).digest(),
            m.document_id(self.prior_index, "SOURCE_INDEX"),
            len(events) - 1,
            computed.next_state,
            self.policy,
            tuple(r.event for r in self.cut.delivered),
        )
        self.w1 = w.Frame(
            2,
            3,
            (
                w.encode_request_source(self.request),
                w.encode_candidate_state(
                    w.CandidateState(candidate.next_policy, candidate.certificate)
                ),
                effects,
                w.encode_receipt(
                    w.Receipt(
                        2,
                        crypto.content_id("deltareduce:003:command:v1", raw_command),
                        candidate.witness_id,
                        crypto.content_id("deltareduce:003:effect-batch:v1", effects),
                        sha256(self.policy).hexdigest(),
                        sha256(candidate.next_policy).hexdigest(),
                    )
                ),
            ),
        )
        self.originals = originals | {self.prior_index}
        self.p.manifest.update(common, formal_semantics_id=boot.formal_semantics_id)
        self.p.record.update(journal_cuts=[self.journal(self.prefix_wal, 1)])
        self.rebind(self.w1)

    def table(self, originals):
        return sorted(map(ref, originals), key=lambda row: row["content_id"])

    def journal(self, raw, n):
        return {
            "actor_id": self.x.bootstrap.validators[0][0],
            "journal_id": "consensus",
            "ref": ref(raw),
            "entry_count": str(n),
            "first_sequence": "1",
            "last_sequence": str(n),
        }

    def rebind(self, value):
        raw = w.encode_frame(value)
        own = self.prefix_wal + raw
        rows = copy.deepcopy(m.load(self.prior_index)["events"])
        rows.append(
            {
                "actor_id": self.x.bootstrap.validators[0][0],
                "action_id": "ACT-ISC-FINALIZE",
                "original_ref": ref(raw),
                "input_refs": [ref(self.prior_index)],
                "dependencies": list(map(str, range(5))),
            }
        )
        originals = self.originals | {raw, own}
        self.p.artifacts = tuple(sorted((m.raw_id(v), v) for v in originals))
        table = self.table(originals)
        self.p.index.update(
            events=rows, artifacts=table, original_journal_refs=[self.journal(own, 2)]
        )
        self.p.index_raw = m.canonical(self.p.index)
        self.p.boot_raw = m.canonical(self.p.boot)
        bid = m.document_id(self.p.boot_raw, "BOOTSTRAP")
        self.p.record["bootstrap_id"] = bid
        self.p.manifest.update(
            bootstrap_id=bid,
            artifacts=table,
            source_index_ref=ref(self.p.index_raw),
            cut_event_index="5",
            target_event_index="6",
            journals=[
                {
                    "actor_id": self.x.bootstrap.validators[0][0],
                    "journal_id": "consensus",
                    "cut": {
                        k: v
                        for k, v in self.journal(self.prefix_wal, 1).items()
                        if k not in ("actor_id", "journal_id")
                    },
                    "target": {
                        k: v
                        for k, v in self.journal(own, 2).items()
                        if k not in ("actor_id", "journal_id")
                    },
                }
            ],
        )
        self.p.trust = m.PrimitiveTrust(
            m.raw_id(self.p.boot_raw),
            m.raw_id(self.p.index_raw),
            tuple(sorted((k, self.p.boot[k]) for k in m.PINS)),
            self.p.boot_raw,
            frame(self.p.record),
            ((self.x.bootstrap.validators[0][0], "consensus", own),),
        )

    def check(self, **changed):
        args = dict(
            journal_id="consensus",
            physical_slot=2,
            consumer_index=5,
            original_prior_index=self.prior_index,
            initial_state=self.initial,
            initial_tick=2,
            original_policy=self.policy,
            logical_tick=7,
            frozen_inputs=self.body.tuples,
            body=self.body,
        )
        args.update(changed)
        return c.bind_indexed(
            self.x.bootstrap, self.x.backend, source.materialize(self.p.check()), **args
        )

    def test_indexed_original_command_and_full_deliveries_supply_w1_predecessor(self):
        result = self.check()
        self.assertEqual(result.bound.original, w.encode_frame(self.w1))
        self.assertEqual(result.bound.predecessor.native_state, result.command_prefix.target.state)
        self.assertEqual(result.original_source_cut.original_index, self.prior_index)
        self.assertEqual(result.bound.predecessor.cut.delivered, self.cut.delivered)
        self.assertEqual(result.original_deliveries.unresolved, ())
        self.assertEqual(result.command_prefix.pending_protocol, ())
        self.assertNotEqual(result.original_source_cut.original_index, self.p.index_raw)

    def test_recomputed_w1_cannot_substitute_a_peer_or_delete_an_original_delivery(self):
        for deliveries in (
            (
                replace(self.request.deliveries[0], peer_id="invented-peer"),
                *self.request.deliveries[1:],
            ),
            self.request.deliveries[:3],
        ):
            request = replace(self.request, deliveries=tuple(deliveries))
            changed = replace(
                self.w1, sections=(w.encode_request_source(request), *self.w1.sections[1:])
            )
            self.rebind(changed)
            with self.assertRaisesRegex(crypto.CodecError, "independent predecessor"):
                self.check()

    def test_supplied_coarse_state_cannot_replace_original_command_computation(self):
        native = c.read_state(self.initial, self.body.formal_semantics_id)
        native["durable_sequence"] = "10"
        with self.assertRaisesRegex(crypto.CodecError, "whole original command output differs"):
            self.check(initial_state=c.envelope(5, native))


if __name__ == "__main__":
    unittest.main()
