"""REFERENCE_ONLY_NOT_PRODUCTION: file cuts, exact replay and mixed slots."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from formal.reference.isc_w1.codec import (
    CandidateState,
    Frame,
    Receipt,
    RequestSource,
    encode_candidate_state,
    encode_frame,
    encode_receipt,
    encode_request_source,
)
from formal.reference.isc_w1.harness import FileHarness, InjectedFault, StorageError, scan_file


def legacy(sequence, kind=1):
    payload = f"original-{sequence}".encode()
    digest = hashlib.sha256(b"original opaque policy").hexdigest().encode("ascii")
    sections = (
        (payload, b"", b"", digest) if kind == 2 else (payload, b"state", b"effect", b"receipt")
    )
    return Frame(sequence, kind, sections)


def capsule(sequence, prefix):
    p0, p1 = b"opaque-policy-0", b"opaque-policy-1"
    request = RequestSource(
        b"opaque-command",
        len(prefix),
        hashlib.sha256(prefix).digest(),
        "sha256:" + "1" * 64,
        1,
        b"opaque-state",
        p0,
        (),
    )
    receipt = Receipt(
        sequence,
        "sha256:" + "2" * 64,
        "sha256:" + "3" * 64,
        "sha256:" + "4" * 64,
        hashlib.sha256(p0).hexdigest(),
        hashlib.sha256(p1).hexdigest(),
    )
    return Frame(
        sequence,
        3,
        (
            encode_request_source(request),
            encode_candidate_state(CandidateState(p1, b"opaque-ISC")),
            b"opaque-effect",
            encode_receipt(receipt),
        ),
    )


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "reference.wal"

    def open(self):
        harness = FileHarness.create(self.path)
        self.addCleanup(harness.close)
        return harness

    def test_mixed_slots_and_exact_replay_across_reopen(self):
        harness = self.open()
        first, vote = legacy(1), legacy(2, 2)
        harness.append(first)
        harness.append(vote)
        prefix = self.path.read_bytes()
        finalization = capsule(3, prefix)
        stored = harness.append(finalization)
        harness.append(legacy(4, 2))
        full = self.path.read_bytes()
        self.assertEqual(harness.snapshot.physical_slots, 4)
        self.assertEqual(harness.snapshot.vote_count, 2)
        self.assertEqual([r.frame.sequence for r in harness.snapshot.records], [1, 2, 3, 4])
        self.assertEqual([r.frame.kind for r in harness.snapshot.records], [1, 2, 3, 2])
        result = harness.append(finalization)
        self.assertTrue(result.replayed)
        self.assertEqual(result.raw, stored.raw)
        self.assertEqual(result.frame.sections, finalization.sections)
        self.assertEqual(self.path.read_bytes(), full)
        harness.close()
        with FileHarness.reopen(self.path, required_prefix=full) as reopened:
            self.assertEqual(reopened.snapshot.physical_slots, 4)
            self.assertEqual(reopened.snapshot.vote_count, 2)
            self.assertEqual(reopened.append(vote).raw, encode_frame(vote))
            self.assertTrue(reopened.append(finalization).replayed)
        self.assertEqual(self.path.read_bytes(), full)

    def test_before_append_preserves_ready_prefix(self):
        harness = self.open()
        with self.assertRaises(InjectedFault):
            harness.append(legacy(1), fault="before_append")
        self.assertTrue(harness.ready)
        self.assertEqual(self.path.read_bytes(), b"")
        self.assertFalse(harness.append(legacy(1)).replayed)

    def test_complete_unacknowledged_survives_without_second_append(self):
        for fault in ("before_barrier", "barrier_failure", "before_expose"):
            with self.subTest(fault=fault):
                path = self.path.with_name(fault)
                with FileHarness.create(path) as harness:
                    frame = capsule(1, b"")
                    with self.assertRaises(InjectedFault):
                        harness.append(frame, fault=fault)
                    saved = path.read_bytes()
                    self.assertFalse(harness.ready)
                    with self.assertRaises(StorageError):
                        _ = harness.snapshot
                    with self.assertRaises(StorageError):
                        harness.append(frame)
                with FileHarness.reopen(path, required_prefix=saved) as reopened:
                    result = reopened.append(frame)
                    self.assertTrue(result.replayed)
                    self.assertEqual(result.raw, saved)
                    self.assertEqual(reopened.snapshot.physical_slots, 1)
                    self.assertEqual(reopened.snapshot.vote_count, 0)
                self.assertEqual(path.read_bytes(), saved)

    def test_partial_append_blocks_scan_and_never_repairs_tail(self):
        harness = self.open()
        harness.append(legacy(1))
        floor = self.path.read_bytes()
        with self.assertRaises(InjectedFault):
            harness.append(capsule(2, floor), fault="partial_append")
        damaged = self.path.read_bytes()
        self.assertGreater(len(damaged), len(floor))
        harness.close()
        for operation in (scan_file, FileHarness.reopen):
            with self.assertRaises(ValueError):
                operation(self.path, required_prefix=floor)
            self.assertEqual(self.path.read_bytes(), damaged)

    def test_corruption_unknown_kind_and_sequence_gap_are_not_skipped(self):
        harness = self.open()
        harness.append(legacy(1))
        harness.close()
        original = self.path.read_bytes()
        bad_checksum = bytearray(encode_frame(legacy(2, 2)))
        bad_checksum[-1] ^= 1
        unknown = bytearray(encode_frame(legacy(2, 2)))
        unknown[20] = 4
        unknown[-32:] = hashlib.sha256(unknown[:-32]).digest()
        for tail in (bytes(bad_checksum), bytes(unknown), encode_frame(legacy(3)), b"DRW"):
            with self.subTest(tail=tail[:24]):
                damaged = original + tail
                self.path.write_bytes(damaged)
                with self.assertRaises(ValueError):
                    FileHarness.reopen(self.path)
                self.assertEqual(self.path.read_bytes(), damaged)

    def test_floor_cannot_be_downgraded_to_missing_or_changed_bytes(self):
        harness = self.open()
        harness.append(legacy(1))
        floor = self.path.read_bytes()
        harness.close()
        self.path.write_bytes(b"")
        with self.assertRaises(StorageError):
            FileHarness.reopen(self.path, required_prefix=floor)
        self.path.write_bytes(
            encode_frame(Frame(1, 1, (b"different", b"state", b"effect", b"receipt")))
        )
        with self.assertRaises(StorageError):
            FileHarness.reopen(self.path, required_prefix=floor)
        with self.assertRaises(FileNotFoundError):
            FileHarness.reopen(self.path.with_name("missing"))

    def test_slot_conflict_gap_and_prefix_mismatch_do_not_write(self):
        harness = self.open()
        harness.append(legacy(1))
        before = self.path.read_bytes()
        for frame in (legacy(1, 2), legacy(3), capsule(2, b"")):
            with self.subTest(frame=frame.kind):
                with self.assertRaises(StorageError):
                    harness.append(frame)
                self.assertEqual(self.path.read_bytes(), before)
                self.assertTrue(harness.ready)

    def test_fsync_exception_fences_handle_and_reopen_requires_barrier(self):
        harness = self.open()
        with patch("formal.reference.isc_w1.harness.os.fsync", side_effect=OSError("injected")):
            with self.assertRaises(OSError):
                harness.append(legacy(1))
        self.assertFalse(harness.ready)
        saved = self.path.read_bytes()
        harness.close()
        with patch("formal.reference.isc_w1.harness.os.fsync", side_effect=OSError("injected")):
            with self.assertRaises(OSError):
                FileHarness.reopen(self.path, required_prefix=saved)
        self.assertEqual(self.path.read_bytes(), saved)
        with FileHarness.reopen(self.path, required_prefix=saved) as reopened:
            self.assertTrue(reopened.append(legacy(1)).replayed)

    def test_external_change_fences_handle(self):
        harness = self.open()
        self.path.write_bytes(encode_frame(legacy(1)))
        with self.assertRaises(StorageError):
            harness.append(legacy(1))
        self.assertFalse(harness.ready)

    def test_short_write_fences_and_retains_partial_bytes(self):
        from unittest.mock import Mock

        harness = self.open()
        stream = harness._stream
        wrapped = Mock(wraps=stream)
        wrapped.write.side_effect = lambda data: stream.write(data[:7])
        harness._stream = wrapped
        with self.assertRaises(OSError):
            harness.append(legacy(1))
        self.assertFalse(harness.ready)
        partial = self.path.read_bytes()
        self.assertEqual(len(partial), 7)
        harness.close()
        with self.assertRaises(StorageError):
            FileHarness.reopen(self.path)
        self.assertEqual(self.path.read_bytes(), partial)

    def test_reopen_rejects_self_consistent_frame_with_wrong_prefix(self):
        with self.open() as harness:
            harness.append(legacy(1))
        wrong = self.path.read_bytes() + encode_frame(capsule(2, b"wrong prefix"))
        self.path.write_bytes(wrong)
        with self.assertRaises(StorageError):
            FileHarness.reopen(self.path)
        self.assertEqual(self.path.read_bytes(), wrong)

    def test_bad_total_length_is_rejected_without_allocating_body(self):
        from formal.reference.isc_w1.codec import MAX_FRAME_BYTES

        for size in (0, 71, MAX_FRAME_BYTES + 1, (1 << 32) - 1):
            with self.subTest(size=size):
                data = b"DRW1\x00\x01\x00\x00" + size.to_bytes(4, "big")
                self.path.write_bytes(data)
                with self.assertRaises(StorageError):
                    scan_file(self.path)
                self.assertEqual(self.path.read_bytes(), data)

    def test_create_does_not_overwrite(self):
        harness = self.open()
        harness.append(legacy(1))
        saved = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            FileHarness.create(self.path)
        self.assertEqual(self.path.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
