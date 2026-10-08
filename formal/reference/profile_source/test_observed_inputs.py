"""O complete actual input and lifetime checks, using original 4/8/8/8/8 shape."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import observed_inputs as o
from formal.reference.profile_source import test_configuration as configuration_fixture
from formal.reference.profile_source.availability_ledger import Occurrence
from formal.reference.profile_source.test_manifest_context import synthetic_fixture


class ObservedInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configuration_fixture.ConfigurationTests.setUpClass()
        cls.fixture = configuration_fixture.ConfigurationTests()

    def setUp(self):
        self.store, self.mid, _, _, self.raws = synthetic_fixture(self.fixture)
        self.sigma = self.fixture.boot.formal_semantics_id

    def event(self, index, actor="validator-1"):
        return Occurrence(index, actor, b"original-synthetic-operation-" + str(index).encode())

    def read(self, state=None, index=1, raws=None, actor="validator-1"):
        return o.read_complete(
            o.other_event(o.State(), self.event(0)) if state is None else state,
            self.event(index, actor),
            self.store,
            self.sigma,
            self.mid,
            self.raws if raws is None else raws,
        )

    def test_complete_data_is_owned_in_original_order(self):
        state = self.read()
        buffer = o.at_use(state, "validator-1", 1, self.mid)
        self.assertEqual([len(x.values) for x in buffer.shards], [4, 8, 8, 8, 8])
        self.assertEqual(tuple(x.original_envelope for x in buffer.shards), self.raws)
        self.assertEqual([x.ordinal for x in buffer.shards], list(range(5)))
        self.assertEqual(o.verify_state(state, self.store, self.sigma), state)

    def test_partial_or_corrupt_corpus_never_partially_populates_memory(self):
        for wrong in (
            self.raws[:-1],
            (*self.raws, self.raws[0]),
            tuple(reversed(self.raws)),
            (*self.raws[:-1], self.raws[-1][:-1]),
            (b"authenticated-availability-certificate",),
        ):
            with self.subTest(length=len(wrong)):
                state = self.read(raws=wrong)
                self.assertEqual(state.owned, ())
                self.assertEqual(state.observations[1].original_inputs, wrong)
                self.assertEqual(state.observations[1].disposition, "rejected_bytes")
                self.assertEqual(o.verify_state(state, self.store, self.sigma), state)

    def test_loss_or_later_failure_does_not_mutate_owned_immutable_bytes(self):
        state = self.read()
        original = state.owned[0]
        state = o.external_loss(state, self.event(2), self.mid)
        state = o.failed_read(state, self.event(3), self.mid)
        state = self.read(state, index=4, raws=(b"corrupt",))
        self.assertIs(o.at_use(state, "validator-1", 1, self.mid), original)
        self.assertEqual(len(state.observations), 5)
        self.assertEqual(o.verify_state(state, self.store, self.sigma), state)

    def test_release_or_restart_prevents_old_receipt_reuse(self):
        state = self.read()
        state = self.read(state, index=2, actor="validator-2")
        released = o.release(state, self.event(3), 1)
        crashed = o.process_lost(state, self.event(3))
        for after in (released, crashed):
            with self.assertRaises(CodecError):
                o.at_use(after, "validator-1", 1, self.mid)
            self.assertEqual(o.at_use(after, "validator-2", 2, self.mid).source.index, 2)
            self.assertEqual(o.verify_state(after, self.store, self.sigma), after)
            reread = self.read(after, index=4)
            self.assertEqual(o.at_use(reread, "validator-1", 4, self.mid).source.index, 4)
            with self.assertRaises(CodecError):
                o.at_use(reread, "validator-1", 1, self.mid)

    def test_no_cross_actor_context_or_forged_imported_buffer(self):
        state = self.read()
        for actor, position, manifest in (
            ("validator-2", 1, self.mid),
            ("validator-1", 2, self.mid),
            ("validator-1", 1, state.owned[0].manifest.commitment_id),
        ):
            with self.assertRaises(CodecError):
                o.at_use(state, actor, position, manifest)
        with self.assertRaises(CodecError):
            o.release(state, self.event(2, "validator-2"), 1)
        for forged in (
            replace(state, observations=()),
            replace(state, owned=(replace(state.owned[0], shards=state.owned[0].shards[:-1]),)),
            replace(state, observations=(replace(state.observations[0], disposition="trusted"),)),
        ):
            with self.assertRaises(CodecError):
                o.verify_state(forged, self.store, self.sigma)

    def test_repeated_reads_remain_distinct_original_occurrences(self):
        state = self.read()
        state = self.read(state, index=2)
        self.assertEqual([b.source.index for b in state.owned], [1, 2])
        state = o.release(state, self.event(3), 1)
        self.assertEqual(o.at_use(state, "validator-1", 2, self.mid).source.index, 2)
        self.assertEqual([x.source.index for x in state.observations], [0, 1, 2, 3])
        with self.assertRaises(CodecError):
            self.read(state, index=5)


if __name__ == "__main__":
    unittest.main()
