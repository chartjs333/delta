"""First original CONFIG cut, late/repeated/invalid deliveries and no backdating."""

import unittest
from dataclasses import replace

from formal.reference.profile_source import configuration_history as h
from formal.reference.profile_source import configuration_qc as q
from formal.reference.profile_source import test_configuration_qc as fixture
from formal.reference.profile_source.availability_ledger import Occurrence


class ConfigurationHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ConfigQcTests.setUpClass()

    def setUp(self):
        self.x = fixture.ConfigQcTests()
        self.x.setUp()
        self.f = self.x.f
        self.state, self.index = h.History(), 0

    def event(self, raw):
        event = Occurrence(self.index, "original-relay-identity", raw)
        self.index += 1
        return event

    def propose(self):
        result = h.propose(
            self.state, self.event(self.x.raw), self.f.boot, self.f.storage_boot, self.f.declaration
        )
        self.state = result.state
        return result.disposition

    def deliver(self, raw):
        result = h.deliver(self.state, self.event(raw), self.f.boot, self.f.backend)
        self.state = result.state
        return result.disposition

    def finalize(self, value):
        result = h.finalize(
            self.state,
            self.event(q.encode(value)),
            self.f.boot,
            self.f.storage_boot,
            self.f.backend,
        )
        self.state = result.state
        return result.disposition

    def test_full_first_cut_and_no_signature_as_finality(self):
        self.assertEqual(self.propose(), "recorded")
        self.assertEqual(self.deliver(b"invalid-original"), "rejected_signature_or_encoding")
        for delivery in self.x.delivered:
            self.assertEqual(self.deliver(delivery.original_artifact), "recorded")
        self.assertEqual(self.state.finalized, ())
        original = self.x.delivered[0].original_artifact
        self.deliver(original)
        self.assertEqual(self.finalize(self.x.qc), "recorded")
        selected = h.finalized_config(self.state, self.x.qc["body_hash"])
        self.assertEqual(selected.bound.original_qc_id, self.x.qc["qc_id"])
        self.assertEqual(len(selected.bound.deliveries), 5)
        self.assertEqual(self.state.events[1].original, b"invalid-original")
        self.assertEqual(selected.source.index, 7)

    def test_later_valid_delivery_cannot_backdate_a_finalization(self):
        self.propose()
        for delivery in self.x.delivered[:2]:
            self.deliver(delivery.original_artifact)
        early = {**self.x.qc, "signer_ids": self.x.names[:3], "vote_ids": self.x.qc["vote_ids"][:3]}
        self.assertEqual(self.finalize(early), "rejected_configuration_quorum")
        earlier = self.state
        self.deliver(self.x.delivered[2].original_artifact)
        self.assertEqual(self.finalize(early), "recorded")
        self.assertEqual(earlier.finalized, ())
        self.assertIn(earlier.events[-1], self.state.events)

    def test_actual_original_witness_not_reassembled_at_a_later_cut(self):
        self.propose()
        for delivery in self.x.delivered[:3]:
            self.deliver(delivery.original_artifact)
        early = {**self.x.qc, "signer_ids": self.x.names[:3], "vote_ids": self.x.qc["vote_ids"][:3]}
        self.assertEqual(self.finalize(early), "recorded")
        selected = self.state.finalized[0]
        self.deliver(self.x.delivered[3].original_artifact)
        self.assertEqual(self.finalize(self.x.qc), "already_finalized")
        self.assertEqual(self.finalize(early), "replay")
        self.assertIs(self.state.finalized[0], selected)
        self.assertEqual(len(self.state.finalized), 1)

    def test_cannot_import_qc_as_initial_state_or_inflate_quorum(self):
        self.assertEqual(self.finalize(self.x.qc), "rejected_configuration_quorum")
        self.propose()
        for _ in range(4):
            self.deliver(self.x.delivered[0].original_artifact)
        self.assertEqual(self.finalize(self.x.qc), "rejected_configuration_quorum")
        self.assertEqual(len(self.state.received), 4)
        self.assertEqual(self.state.finalized, ())

    def test_different_receivers_cannot_pool_a_local_finalizers_quorum(self):
        self.propose()
        for i, delivery in enumerate(self.x.delivered):
            event = replace(self.event(delivery.original_artifact), actor=f"receiver-{i}")
            self.state = h.deliver(self.state, event, self.f.boot, self.f.backend).state
        self.assertEqual(self.finalize(self.x.qc), "rejected_configuration_quorum")
        self.assertEqual(len(self.state.received), 4)
        self.assertEqual(self.state.finalized, ())
        for delivery in self.x.delivered:
            self.deliver(delivery.original_artifact)
        self.assertEqual(self.finalize(self.x.qc), "recorded")
        self.assertEqual(len(self.state.received), 8)
        self.assertEqual(len(self.state.finalized[0].bound.deliveries), 4)


if __name__ == "__main__":
    unittest.main()
