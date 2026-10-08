"""Joined original source facets; not a complete profile or native capture.

Synthetic keys/objects exercise original widths 4/8/8/8/8. Lease/phase/control
and genesis provenance remain explicit outer obligations, not positive fixtures.
"""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import identity as isc
from formal.reference.non_isc import codec as non_isc
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import configuration_qc as qc
from formal.reference.profile_source import input_history as h
from formal.reference.profile_source import manifest_context as manifests
from formal.reference.profile_source import scheduling as scheduling
from formal.reference.profile_source import source_prefix as source
from formal.reference.profile_source import test_configuration_qc as config_fixture
from formal.reference.profile_source import test_manifest_context as manifest_fixture
from formal.reference.storage_source import codec as storage
from formal.reference.storage_source import test_codec as storage_fixture


class InputHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_fixture.ConfigQcTests.setUpClass()

    def setUp(self):
        self.x = config_fixture.ConfigQcTests()
        self.x.setUp()
        self.f = self.x.f
        self.actor = self.f.boot.validators[0][0]
        self.ticket_id = "ticket-domain-text-en-000"
        self.artifacts, self.mid, self.config, self.commit, self.raws = (
            manifest_fixture.synthetic_fixture(self.f, ticket_id=self.ticket_id)
        )
        self.manifest = manifests.resolve(self.artifacts, self.f.boot.formal_semantics_id, self.mid)
        value = cfg.decode(self.config)
        self.config_id = cfg.content_id(cfg.DOMAIN, self.config)
        context = {
            "arithmetic_profile_id": self.manifest.profile_id,
            "parameter_schema_id": self.manifest.schema_id,
            "parent_checkpoint_id": self.manifest.parent_id,
            "round_config_id": self.config_id,
        }
        policy = {
            **context,
            **scheduling.envelope("DOMAIN_TICKET_POLICY", self.f.boot.formal_semantics_id),
            "allocation_policy": "CONTIGUOUS_NO_OVERLAP",
            "batch_budget": value["batch_budget"],
            "dataset_manifest_id": value["dataset_manifest_id"],
            "domain_id": self.manifest.domain_id,
            "eligibility_policy_id": "sha256:" + "2" * 64,
            "mixture_coefficient_id": "sha256:" + "3" * 64,
            "region_ids": ["region-1"],
            "step_budget": value["step_budget"],
            "ticket_count": 1,
            "token_cursor_start": 0,
            "token_cursor_end": 16,
        }
        self.plan = scheduling.plan(
            (scheduling.canonical(policy),),
            context,
            "sha256:" + "4" * 64,
            "sha256:" + "5" * 64,
            [("worker-1", "sha256:" + "6" * 64)],
            {
                "hard_deadline_tick": int(value["hard_deadline_tick"]),
                "lease_duration_ticks": 5,
                "maximum_lease_epochs": 3,
                "maximum_renewals": 1,
            },
            self.f.boot.formal_semantics_id,
        )
        self.x.raw, self.x.body = self.config, value
        deliveries = tuple(self.x.delivery(i + 1, name) for i, name in enumerate(self.x.names))
        original_qc = {
            **self.x.qc,
            "body_hash": self.config_id,
            "vote_ids": [
                crypto.content_id(non_isc.VOTE_DOMAIN, d.event.vote_frame) for d in deliveries
            ],
        }
        self.events = []
        self.add("ACT-CONFIG-PROPOSE", self.config, (self.f.declaration,))
        for d in deliveries:
            self.add("ACT-MESSAGE-DELIVER", d.original_artifact)
        self.add("ACT-CONFIG-FINALIZE", qc.encode(original_qc))
        self.add(
            "ACT-TICKET-ISSUE", self.plan.tickets[0], (self.plan.original, *self.plan.policies)
        )
        self.commit_index = len(self.events)
        self.add(
            "ACT-COMMIT",
            self.manifest.original_manifest,
            (*self.artifacts.values(), self.plan.tickets[0]),
            actor="worker-1",
        )
        _, context = manifests.bind_context(
            self.f.boot,
            self.f.storage_boot,
            self.config,
            self.f.declaration,
            self.artifacts,
            self.mid,
            self.commit,
        )
        original_storage = storage_fixture.StorageSourceTests()
        original_storage.common = storage.load(context.common_bytes)
        original_storage.value = context
        self.ac, self.gs = original_storage.witness(
            sorted((leaf, f"storage-{n}") for leaf, _ in context.required_leaves for n in (1, 2, 3))
        )
        for g in self.gs:
            self.add("ACT-MESSAGE-DELIVER", g)
        self.ac_index = len(self.events)
        self.add("ACT-AVAIL-FINALIZE", self.ac, tuple(self.artifacts.values()))
        tuples = (
            isc.InputTuple(
                storage.content_id(storage.CERTIFICATE_DOMAIN, self.ac),
                self.commit.commitment_id,
                self.manifest.domain_id,
                self.ticket_id,
            ),
        )
        self.body = isc.Body(
            self.f.boot.formal_semantics_id,
            self.manifest.profile_id,
            int(value["height"]),
            self.manifest.schema_id,
            self.config_id,
            value["round_id"],
            self.f.boot.validator_epoch_id,
            int(value["view"]),
            self.manifest.parent_id,
            isc.input_root(tuples),
            tuples,
        )
        self.add("ACT-INPUT-CLOSE", isc.body_preimage(self.body))

    def add(self, action, raw, inputs=(), actor=None):
        self.events.append(
            source.Event(
                len(self.events),
                actor or self.actor,
                action,
                raw,
                inputs,
                (),
                b"synthetic-original-descriptor",
            )
        )

    def reconstruct(self, events=None):
        return h.reconstruct(
            tuple(self.events if events is None else events),
            self.f.boot,
            self.f.storage_boot,
            self.f.backend,
            self.plan,
            self.config,
            self.f.declaration,
            actor=self.actor,
        )

    def test_closed_body_is_derived_from_original_complete_source_facets(self):
        result = self.reconstruct()
        self.assertFalse(result.unresolved, result.dispositions)
        self.assertEqual(result.closed[0].body, self.body)
        self.assertEqual(result.closed[0].original.original, isc.body_preimage(self.body))
        self.assertEqual(
            tuple(e.original for e in result.ledger.events), tuple(e.original for e in self.events)
        )
        self.assertEqual(
            [n for _, n in self.manifest.required_leaves], [len(raw) for raw in self.raws]
        )
        self.assertEqual(len(result.closed[0].body.tuples), 1)
        self.assertTrue(result.producer_edges)  # not full source validity/closure

    def test_source_cut_does_not_borrow_later_attestations_or_other_receiver(self):
        events = list(self.events)
        for i in range(self.commit_index + 1, self.ac_index):
            events[i] = replace(events[i], actor="another-receiver")
        result = self.reconstruct(events)
        self.assertEqual(result.ledger.availabilities, ())
        self.assertEqual(result.closed, ())
        # Retain the old failed attempt; only a later new attempt can use Gs.
        for g in self.gs:
            events.append(
                source.Event(
                    len(events), self.actor, "ACT-MESSAGE-DELIVER", g, (), (), b"later-original"
                )
            )
        result = self.reconstruct(events)
        self.assertEqual(result.closed, ())
        self.assertEqual(result.ledger.availabilities, ())

    def test_original_ticket_manifest_and_full_body_cannot_be_substituted(self):
        for index, altered in (
            (6, replace(self.events[6], inputs=())),
            (self.commit_index, replace(self.events[self.commit_index], inputs=())),
            (
                len(self.events) - 1,
                replace(
                    self.events[-1],
                    original=isc.body_preimage(
                        replace(self.body, parent_checkpoint_id="sha256:" + "9" * 64)
                    ),
                ),
            ),
        ):
            with self.subTest(index=index):
                events = list(self.events)
                events[index] = altered
                result = self.reconstruct(events)
                self.assertTrue(result.unresolved)
                self.assertEqual(result.closed, ())

    def test_loss_and_repeated_close_preserve_first_frozen_inputs_and_source_multiplicity(self):
        self.add("ACT-ARTIFACT-LOSE", b"original-hidden-physical-event")
        self.add("ACT-INPUT-CLOSE", isc.body_preimage(self.body))
        result = self.reconstruct()
        self.assertFalse(result.unresolved)
        self.assertEqual(len(result.closed), 2)
        self.assertEqual(result.closed[0].body, result.closed[1].body)
        self.assertEqual(len(result.ledger.availabilities), 1)
        self.assertEqual(len(result.ledger.events), len(self.events))


if __name__ == "__main__":
    unittest.main()
