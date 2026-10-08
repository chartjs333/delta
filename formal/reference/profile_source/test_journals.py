"""Structural vectors, not fabricated production history or authority."""

import unittest

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.isc_w1.codec import encode_frame
from formal.reference.isc_w1.harness import StorageError
from formal.reference.isc_w1.test_harness import capsule, legacy
from formal.reference.profile_source import journals as j


class JournalTests(unittest.TestCase):
    def setUp(self):
        first = [legacy(1), legacy(2, 2)]
        self.prefix = b"".join(map(encode_frame, first))
        self.frames = [*first, capsule(3, self.prefix), legacy(4, 2)]
        self.raw = b"".join(map(encode_frame, self.frames))

    def test_complete_mixed_projection_and_all_cuts(self):
        for cut in range(5):
            value = j.inspect(self.raw, cut_slot=cut, required_prefix=self.prefix)
            self.assertEqual([p.decoded.sequence for p in value.positions], [1, 2, 3, 4])
            self.assertEqual([p.vote_count for p in value.positions], [0, 1, 1, 2])
            self.assertEqual(b"".join(p.original for p in value.positions), self.raw)
            self.assertEqual(value.cut_bytes, b"".join(map(encode_frame, self.frames[:cut])))
            self.assertEqual(j.finalization_prefix(value, 3), self.prefix)
            self.assertEqual([p.decoded.sequence for p in value.original_votes], [2, 4])
            self.assertIs(
                j.exact_existing(value, 3, encode_frame(self.frames[2])), value.positions[2]
            )

    def test_never_collapse_original_votes_or_drop_finalization(self):
        for missing in (0, 1, 2):
            raw = b"".join(encode_frame(f) for i, f in enumerate(self.frames) if i != missing)
            with self.assertRaises((CodecError, StorageError)):
                j.inspect(raw, cut_slot=0, required_prefix=self.prefix)
        # Even after renumbering a deleted first frame, W1 retains its original
        # preceding prefix commitment. It cannot be silently rewritten away.
        raw = b"".join(map(encode_frame, [legacy(1, 2), capsule(2, self.prefix), legacy(3, 2)]))
        with self.assertRaisesRegex(StorageError, "prefix mismatch"):
            j.inspect(raw, cut_slot=0, required_prefix=b"")

    def test_torn_tail_is_not_a_smaller_source_domain(self):
        for cut in (1, 11, 12, len(self.raw) - 1):
            with self.assertRaises((CodecError, StorageError)):
                j.inspect(self.raw[:cut], cut_slot=0, required_prefix=b"")

    def test_interval_counts_slots_and_retry_does_not_allocate(self):
        value = j.inspect(self.raw, cut_slot=3, required_prefix=self.prefix)
        row = {
            "ref": {"content_id": j.raw_id(self.raw), "byte_length": str(len(self.raw))},
            "entry_count": "4",
            "first_sequence": "1",
            "last_sequence": "4",
        }
        j.verify_inventory_row(value, row)
        for key in ("entry_count", "last_sequence"):
            with self.assertRaises(CodecError):
                j.verify_inventory_row(value, {**row, key: "2"})
        with self.assertRaisesRegex(CodecError, "conflicting replay"):
            j.exact_existing(value, 3, encode_frame(self.frames[1]))
        self.assertEqual(len(value.positions), 4)
        self.assertEqual(value.vote_count, 2)

    def test_missing_floor_or_invalid_cut_rejected(self):
        for floor, cut in ((self.raw + b"x", 0), (self.prefix, 5), (b"", -1)):
            with self.assertRaises((CodecError, StorageError)):
                j.inspect(self.raw, cut_slot=cut, required_prefix=floor)


if __name__ == "__main__":
    unittest.main()
