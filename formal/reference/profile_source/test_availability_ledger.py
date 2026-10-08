"""O ledger facet from empty state; synthetic bytes, not a full legal profile import."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import availability_ledger as ledger
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import test_configuration as config_fixture
from formal.reference.storage_source import codec as s
from formal.reference.storage_source import test_codec as storage_fixture


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_fixture.ConfigurationTests.setUpClass()
        cls.f = config_fixture.ConfigurationTests()

    def setUp(self):
        self.raw_config = cfg.encode(self.f.body())
        bound = cfg.bind(self.f.boot, self.f.storage_boot, self.raw_config, self.f.declaration)
        self.storage = storage_fixture.StorageSourceTests()
        self.common = {
            **self.storage.common,
            "round_id": bound.round_id,
            "height": str(bound.height),
            "parent_checkpoint_id": bound.parent,
            "round_config_id": bound.body_id,
            "ticket_id": "ticket-1",
        }
        self.storage.common = self.common
        self.storage.value = replace(self.storage.value, common_bytes=s.canonical(self.common))
        self.context = self.storage.value
        self.ac, self.gs = self.storage.witness()
        self.state = ledger.empty(("ticket-1", "ticket-2", "ticket-3"))
        self.index = 0

    def event(self, raw):
        result = ledger.Occurrence(self.index, "relay-not-storage-signer", raw)
        self.index += 1
        return result

    def commitment(self, ticket="ticket-1"):
        # The component consumes the original native two-field Commitment.
        # Its ticket/manifest producer authority is NOT fabricated by this test.
        value = ledger.Commitment(ticket, self.common["commitment_id"])
        event = self.event(b"synthetic-original-commitment-occurrence:" + ticket.encode())
        result = ledger.record_commitment(self.state, event, value)
        self.state = result.state
        return result

    def deliveries(self, values=None):
        for raw in self.gs if values is None else values:
            self.state = ledger.deliver(self.state, self.event(raw))

    def admit(self, raw=None, context=None):
        result = ledger.record_availability(
            self.state,
            self.event(self.ac if raw is None else raw),
            self.f.boot,
            self.f.storage_boot,
            self.f.backend,
            self.raw_config,
            self.context if context is None else context,
            self.f.declaration,
        )
        self.state = result.state
        return result

    def freeze(self):
        result = ledger.freeze(self.state, self.event(b"original-freeze-attempt"))
        self.state = result.state
        return result

    def test_no_backdating_valid_later_statement(self):
        self.commitment()
        self.deliveries(self.gs[:-1])
        early = self.admit()
        self.assertEqual(early.disposition, "rejected_authenticated_witness")
        self.assertEqual(early.state.availabilities, ())
        self.deliveries(self.gs[-1:])
        self.assertEqual(self.admit().disposition, "recorded")
        self.assertEqual(early.state.availabilities, ())  # immutable original cut
        self.assertIn(early.state.events[-1], self.state.events)

    def test_full_inventory_including_invalid_and_duplicate_deliveries(self):
        self.commitment()
        inventory = (b"invalid-signature-source", *self.gs, self.gs[0], self.gs[0])
        self.deliveries(inventory)
        self.assertEqual(self.admit().disposition, "recorded")
        accepted = self.state.availabilities[0]
        self.assertEqual(accepted.bound.witness.original_inventory, inventory)
        self.assertEqual(tuple(e.original for e in self.state.deliveries), inventory)
        self.assertEqual(len(accepted.bound.witness.witness), len(self.gs))

    def test_alternate_witness_conflict_and_exact_replay_preserve_original(self):
        self.commitment()
        self.deliveries()
        self.assertEqual(self.admit().disposition, "recorded")
        first = self.state.availabilities[0]
        self.assertEqual(self.admit().disposition, "replay")
        pairs = [
            (leaf, f"storage-{n}") for leaf, _ in self.context.required_leaves for n in (1, 2, 4)
        ]
        alternate, gs = self.storage.witness(pairs)
        self.deliveries(gs)
        self.assertEqual(self.admit(alternate).disposition, "availability_conflict")
        self.assertIs(self.state.availabilities[0], first)
        self.assertEqual(self.state.events[-1].original, alternate)

    def test_loss_preserves_ac_freeze_and_late_lineage(self):
        self.commitment()
        self.commitment("ticket-2")
        self.deliveries()
        self.assertEqual(self.admit().disposition, "recorded")
        # No physical-state premise enters this facet. A reported loss stays
        # in source events and cannot remove an accepted certificate.
        self.state = ledger.observed(self.state, self.event(b"original-reported-loss"))
        self.assertEqual(self.freeze().disposition, "recorded")
        original = self.state.frozen
        self.assertEqual(
            original,
            (
                (
                    "ticket-1",
                    self.common["commitment_id"],
                    s.content_id(s.CERTIFICATE_DOMAIN, self.ac),
                ),
            ),
        )
        self.assertEqual(self.freeze().disposition, "replay")
        self.assertIs(self.state.frozen, original)
        self.storage.common = {**self.common, "ticket_id": "ticket-2"}
        self.storage.value = replace(self.context, common_bytes=s.canonical(self.storage.common))
        late, gs = self.storage.witness()
        self.deliveries(gs)
        self.assertEqual(self.admit(late, self.storage.value).disposition, "late")
        self.assertEqual(len(self.state.late_availabilities), 1)
        self.assertIs(self.state.frozen, original)
        self.assertEqual(self.commitment("ticket-3").disposition, "late")
        self.assertEqual(len(self.state.late_commitments), 1)
        self.assertEqual(
            ledger.original_tuples(self.state, {"ticket-1": "domain-1"})[0].ticket_id, "ticket-1"
        )

    def test_no_empty_freeze_or_context_substitution(self):
        self.assertEqual(self.freeze().disposition, "input_set_empty")
        self.commitment()
        self.deliveries()
        self.context = replace(
            self.context,
            common_bytes=s.canonical(
                {**self.common, "parent_checkpoint_id": storage_fixture.identifier(999)}
            ),
        )
        self.assertEqual(self.admit().disposition, "rejected_authenticated_witness")
        self.assertIsNone(self.state.frozen)
        self.assertEqual(self.state.availabilities, ())

    def test_source_occurrences_never_collapsed_or_reordered(self):
        event = self.event(b"raw repeated delivery")
        self.state = ledger.deliver(self.state, event)
        self.state = ledger.deliver(self.state, self.event(event.original))
        self.assertEqual(len(self.state.deliveries), 2)
        with self.assertRaisesRegex(CodecError, "event order"):
            ledger.deliver(self.state, event)


if __name__ == "__main__":
    unittest.main()
