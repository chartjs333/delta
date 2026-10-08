"""Original W1 inline inputs/cuts, with synthetic keys, not full producer history."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import authentication as auth
from formal.reference.isc_source import identity as identity
from formal.reference.isc_source import test_authentication as fixture
from formal.reference.isc_w1 import codec as wal
from formal.reference.profile_source import source_prefix as s
from formal.reference.profile_source import test_configuration_qc as config_fixture
from formal.reference.storage_source import test_codec as storage_fixture


class OriginalDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.AuthenticationTests.setUpClass()
        cls.fixture = fixture.AuthenticationTests()
        cls.bootstrap, cls.backend = cls.fixture.bootstrap, cls.fixture.backend
        cls.body = cls.fixture.body
        cls.names = tuple(cls.fixture.seeds)

    def event(self, index, name, *, body=None, actor="original-validator-receiver"):
        body = self.body if body is None else body
        g = self.fixture.signed(name, body)
        artifact = crypto.decode_artifact(g)
        delivery = wal.Delivery(
            index,
            "original-relay",
            artifact.vote_bytes,
            crypto.preimage(artifact.registry_id, artifact.key_id, artifact.vote_bytes),
            artifact.signature,
            artifact.key_id,
        )
        return s.Event(
            index,
            actor,
            "ACT-MESSAGE-DELIVER",
            wal.encode_delivery(delivery),
            (g, identity.body_preimage(body)),
            (),
            b"synthetic-event-descriptor",
        )

    def inventory(self, events):
        # The complete metadata -> retained_cut binding is qualified separately.
        # This typed fixture intentionally asserts no production capture/origin.
        cut = s.RetainedCut(
            b"synthetic-index",
            "sha256:" + "1" * 64,
            len(events) - 1,
            len(events),
            tuple(events),
            (),
        )
        return s.isc_inventory(
            cut, self.bootstrap, self.backend, "original-validator-receiver", self.body.round_id
        )

    def test_source_receivers_relays_signers_and_repeated_cuts_remain_distinct(self):
        events = [self.event(i, name) for i, name in enumerate(self.names)]
        early = self.inventory(events[:3])
        late = self.inventory(events)
        self.assertFalse(early.unresolved)
        self.assertEqual([r.event.event_index for r in early.admitted], [0, 1, 2])
        self.assertEqual([r.event.event_index for r in late.admitted], [0, 1, 2, 3])
        repeat = self.event(4, self.names[0])
        other = replace(self.body, parent_checkpoint_id="sha256:" + "8" * 64)
        conflict = self.event(5, self.names[3], body=other)
        full = self.inventory([*events, repeat, conflict])
        self.assertEqual(len(full.admitted), 6)
        self.assertEqual(full.admitted[0].original_g, full.admitted[4].original_g)
        self.assertNotEqual(full.admitted[0].event.event_index, full.admitted[4].event.event_index)
        self.assertEqual(full.admitted[-1].original_body, other)
        verified = tuple(
            auth.authenticate(self.bootstrap, self.backend, r.original_g, r.original_body)
            for r in full.admitted
        )
        self.assertEqual(auth.delivered_signers(self.body, verified), self.names)
        self.assertTrue(all(r.event.peer_id == "original-relay" for r in full.admitted))
        self.assertNotEqual(events[0].actor, full.admitted[0].event.peer_id)
        self.assertNotEqual(events[0].actor, verified[0].vote.validator_id)

    def test_original_dependency_preimage_is_used_but_later_bytes_are_not_borrowed(self):
        body = identity.body_preimage(self.body)
        close = s.Event(
            0,
            "original-validator-receiver",
            "ACT-INPUT-CLOSE",
            body,
            (),
            (),
            b"synthetic-close-descriptor",
        )
        delivered = self.event(1, self.names[0])
        delivered = replace(delivered, inputs=delivered.inputs[:1], dependencies=(0,))
        result = self.inventory([close, delivered])
        self.assertEqual(len(result.admitted), 1)
        missing = replace(delivered, dependencies=())
        future = replace(close, index=2)
        result = self.inventory([close, missing, future])
        self.assertEqual(result.admitted, ())
        self.assertEqual(result.unresolved, (missing,))
        self.assertEqual(result.outcomes[1], (1, "missing_original_input"))

    def test_valid_signature_without_original_g_is_not_silently_rejected_or_dropped(self):
        event = self.event(0, self.names[0])
        missing = replace(event, inputs=event.inputs[1:])
        result = self.inventory([missing])
        self.assertEqual(result.admitted, ())
        self.assertEqual(result.unresolved, (missing,))
        self.assertEqual(result.source.events, (missing,))

    def test_disjoint_original_protocol_containers_share_one_complete_source_prefix(self):
        config_fixture.ConfigQcTests.setUpClass()
        config = config_fixture.ConfigQcTests()
        config.setUp()
        storage_fixture.StorageSourceTests.setUpClass()
        storage = storage_fixture.StorageSourceTests()
        originals = (config.delivered[0].original_artifact, storage.signed())
        events = [
            replace(self.event(i, self.names[0]), original=raw, inputs=())
            for i, raw in enumerate(originals)
        ]
        events += [self.event(i + 2, name) for i, name in enumerate(self.names)]
        result = self.inventory(events)
        self.assertFalse(result.unresolved)
        self.assertEqual(len(result.source.events), 6)
        self.assertEqual([r.event.event_index for r in result.admitted], [2, 3, 4, 5])
        self.assertEqual(
            result.outcomes[:2],
            (
                (0, "non_isc_delivery_requires_its_own_handler"),
                (1, "storage_delivery_requires_its_own_handler"),
            ),
        )
        # A malformed advertised container is not a parsed foreign kind and
        # cannot hide an unresolved original behind an unrelated magic prefix.
        malformed = replace(events[0], original=originals[0][:-1])
        self.assertEqual(self.inventory([malformed]).unresolved, (malformed,))

    def test_original_position_mismatch_and_unknown_encoding_stay_unresolved(self):
        event = self.event(1, self.names[0])
        changed = replace(event, index=0)
        result = self.inventory([changed])
        self.assertEqual(result.unresolved, (changed,))
        unknown = replace(changed, original=b"other-original-transport-format")
        self.assertEqual(self.inventory([unknown]).unresolved, (unknown,))

    def test_invalid_signature_stays_as_failed_original_occurrence(self):
        event = self.event(0, self.names[0])
        delivery = wal.decode_delivery(event.original)
        invalid = replace(delivery, signature_bytes=bytes(64))
        event = replace(event, original=wal.encode_delivery(invalid))
        result = self.inventory([event])
        self.assertEqual(result.source.events, (event,))
        self.assertEqual(result.unresolved, ())
        self.assertEqual(result.admitted, ())
        self.assertEqual(result.outcomes, ((0, "rejected_isc_bytes_or_signature"),))

    def test_other_receivers_do_not_supply_local_quorum(self):
        events = [self.event(i, name, actor=f"receiver-{i}") for i, name in enumerate(self.names)]
        result = self.inventory(events)
        self.assertEqual(result.admitted, ())
        self.assertEqual(result.source.events, tuple(events))
        self.assertEqual(len(result.outcomes), 4)

    def test_original_body_and_inline_bytes_roundtrip_without_new_wrapper(self):
        raw = identity.body_preimage(self.body)
        self.assertEqual(identity.decode_body_preimage(raw), self.body)
        for bad in (raw[:-1], raw + b"ignored", bytes(8) + raw[8:]):
            with self.assertRaises(crypto.CodecError):
                identity.decode_body_preimage(bad)
        event = self.event(0, self.names[0])
        self.assertEqual(wal.encode_delivery(wal.decode_delivery(event.original)), event.original)
        for bad in (event.original[:-1], event.original + b"ignored"):
            with self.assertRaises(wal.CodecError):
                wal.decode_delivery(bad)


if __name__ == "__main__":
    unittest.main()
