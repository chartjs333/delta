"""Synthetic storage tests only; no payload is consensus evidence."""

import struct
import unittest
from dataclasses import replace
from hashlib import sha256
from unittest.mock import patch

from formal.reference.isc_w1.codec import (
    MAX_ENVELOPE_BYTES,
    MAX_FRAME_BYTES,
    MAX_RESULT_BYTES,
    MAX_VALUE_BYTES,
    MIN_FRAME_BYTES,
    CandidateState,
    CodecError,
    Delivery,
    Frame,
    Receipt,
    RequestSource,
    decode_candidate_state,
    decode_frame,
    decode_receipt,
    decode_request_source,
    encode_candidate_state,
    encode_frame,
    encode_receipt,
    encode_request_source,
)


def synthetic_sections(sequence: int = 1) -> tuple[bytes, bytes, bytes, bytes]:
    source = RequestSource(
        b"synthetic command",
        0,
        sha256(b"").digest(),
        "synthetic-source-index",
        4,
        b"synthetic S0",
        b"synthetic P0",
        (
            Delivery(1, "peer-1", b"vote A", b"payload A", b"signature A", "key-A"),
            Delivery(3, "peer-1", b"vote A", b"payload A", b"signature A", "key-A"),
            Delivery(4, "peer-2", b"conflict", b"payload B", b"signature B", "key-B"),
        ),
    )
    state = CandidateState(b"synthetic P1", b"synthetic opaque ISC")
    receipt = Receipt(
        sequence,
        "sha256:" + "1" * 64,
        "sha256:" + "2" * 64,
        "sha256:" + "3" * 64,
        sha256(source.prior_policy_bytes).hexdigest(),
        sha256(state.policy_bytes).hexdigest(),
    )
    return (
        encode_request_source(source),
        encode_candidate_state(state),
        b"synthetic opaque effects",
        encode_receipt(receipt),
    )


def independently_frame(sequence: int, kind: int, sections: tuple[bytes, ...]) -> bytes:
    """Literal struct layout independent of codec helpers, including mutated frames."""
    body = struct.pack(
        ">4sHHIQB3s", b"DRW1", 1, 0, 72 + sum(map(len, sections)), sequence, kind, b"\0\0\0"
    )
    body += b"".join(struct.pack(">I", len(section)) + section for section in sections)
    return body + sha256(body).digest()


def rehash(data: bytes) -> bytes:
    return data[:-32] + sha256(data[:-32]).digest()


class CodecTests(unittest.TestCase):
    def test_exact_legacy_layout_and_round_trip(self) -> None:
        # Fixed hex bytes/checksum are a second, literal framing oracle.
        wire = bytes.fromhex(
            "445257310001000000000049000000000000000202000000"
            "0000000176000000000000000000000000"
            "52af66a97f684cfa2fce062b8443929b4742ebc516da90772ce8573ea7fa9ef7"
        )
        frame = Frame(2, 2, (b"v", b"", b"", b""))
        self.assertEqual(encode_frame(frame), wire)
        self.assertEqual(decode_frame(wire), frame)
        transition = Frame(1, 1, (b"c", b"s", b"e", b"r"))
        self.assertEqual(encode_frame(transition), independently_frame(1, 1, transition.sections))
        self.assertEqual(decode_frame(encode_frame(transition)), transition)

    def test_exact_w1_layout_and_round_trip(self) -> None:
        sections = synthetic_sections(3)
        frame = Frame(3, 3, sections)
        self.assertEqual(encode_frame(frame), independently_frame(3, 3, sections))
        self.assertEqual(decode_frame(encode_frame(frame)), frame)
        self.assertEqual(len(sections[3]), 369)
        self.assertEqual(sections[0][:8], bytes.fromhex("4946513100010000"))
        self.assertEqual(sections[1][:8], bytes.fromhex("4946533100010000"))
        self.assertEqual(sections[3][:8], bytes.fromhex("4946523100010000"))

    def test_sections_match_independent_literal_layout(self) -> None:
        source_bytes, state_bytes, _, receipt_bytes = synthetic_sections(3)
        source = decode_request_source(source_bytes)
        state = decode_candidate_state(state_bytes)
        receipt = decode_receipt(receipt_bytes)

        def blob(value: bytes) -> bytes:
            return struct.pack(">I", len(value)) + value

        expected = b"IFQ1\x00\x01\x00\x00" + blob(source.command_bytes)
        expected += struct.pack(">Q", source.prior_wal_byte_length) + source.prior_wal_sha256
        expected += blob(source.source_index_id.encode("ascii"))
        expected += struct.pack(">Q", source.source_cut_event_index)
        expected += blob(source.prior_state_bytes) + blob(source.prior_policy_bytes)
        expected += struct.pack(">I", len(source.deliveries))
        for delivery in source.deliveries:
            expected += struct.pack(">Q", delivery.event_index)
            expected += blob(delivery.peer_id.encode("ascii")) + blob(delivery.vote_frame)
            expected += blob(delivery.signed_payload) + blob(delivery.signature_bytes)
            expected += blob(delivery.key_id.encode("ascii"))
        self.assertEqual(source_bytes, expected)
        self.assertEqual(
            state_bytes,
            b"IFS1\x00\x01\x00\x00" + blob(state.policy_bytes) + blob(state.certificate_bytes),
        )
        expected = b"IFR1\x00\x01\x00\x00" + struct.pack(">Q", 3)
        expected += blob(receipt.command_id.encode("ascii"))
        expected += blob(receipt.certificate_id.encode("ascii"))
        expected += blob(receipt.effect_batch_id.encode("ascii"))
        expected += receipt.prior_policy_digest.encode("ascii")
        expected += receipt.next_policy_digest.encode("ascii")
        self.assertEqual(receipt_bytes, expected)

    def test_section_round_trips_preserve_repeats_and_conflicts(self) -> None:
        source_bytes, state_bytes, _, receipt_bytes = synthetic_sections()
        source = decode_request_source(source_bytes)
        self.assertEqual(encode_request_source(source), source_bytes)
        self.assertEqual(source.deliveries[0].vote_frame, source.deliveries[1].vote_frame)
        self.assertNotEqual(source.deliveries[1].vote_frame, source.deliveries[2].vote_frame)
        self.assertEqual([value.event_index for value in source.deliveries], [1, 3, 4])
        self.assertEqual(encode_candidate_state(decode_candidate_state(state_bytes)), state_bytes)
        self.assertEqual(encode_receipt(decode_receipt(receipt_bytes)), receipt_bytes)

    def test_unknown_magic_version_flags_kind_and_reserved_rejected_with_valid_hash(self) -> None:
        original = encode_frame(Frame(1, 3, synthetic_sections()))
        for offset, value in (
            (0, 0),
            (4, 1),
            (5, 2),
            (6, 1),
            (7, 1),
            (20, 0),
            (20, 4),
            (21, 1),
            (22, 1),
            (23, 1),
        ):
            with self.subTest(offset=offset, value=value):
                changed = bytearray(original)
                changed[offset] = value
                with self.assertRaises(CodecError):
                    decode_frame(rehash(bytes(changed)))

    def test_checksum_and_every_truncation_rejected(self) -> None:
        wire = encode_frame(Frame(1, 3, synthetic_sections()))
        changed = bytearray(wire)
        changed[50] ^= 1
        with self.assertRaisesRegex(CodecError, "checksum"):
            decode_frame(bytes(changed))
        for cut in range(len(wire)):
            with self.subTest(cut=cut), self.assertRaises(CodecError):
                decode_frame(wire[:cut])

    def test_outer_lengths_and_trailing_bytes_rejected(self) -> None:
        original = encode_frame(Frame(1, 3, synthetic_sections()))
        for offset, size in ((8, len(original) - 1), (8, len(original) + 1), (24, (1 << 32) - 1)):
            changed = bytearray(original)
            changed[offset : offset + 4] = struct.pack(">I", size)
            with self.subTest(offset=offset, size=size), self.assertRaises(CodecError):
                decode_frame(rehash(bytes(changed)))
        changed = bytearray(original[:-32] + b"x" + original[-32:])
        changed[8:12] = struct.pack(">I", len(changed))
        with self.assertRaisesRegex(CodecError, "trailing"):
            decode_frame(rehash(bytes(changed)))

    def test_legacy_section_shapes_and_unknown_kind_rejected(self) -> None:
        cases = [
            (1, (b"c", b"", b"e", b"r")),
            (2, (b"v", b"s", b"", b"")),
            (2, (b"", b"", b"", b"")),
            (4, (b"a", b"b", b"c", b"d")),
        ]
        for kind, sections in cases:
            with self.subTest(kind=kind, sections=sections):
                with self.assertRaises(CodecError):
                    encode_frame(Frame(1, kind, sections))
                with self.assertRaises(CodecError):
                    decode_frame(independently_frame(1, kind, sections))

    def test_checked_u64_sequence_and_request_fields(self) -> None:
        for sequence in (-1, 0, 1 << 64, True):
            with self.subTest(sequence=sequence), self.assertRaises(CodecError):
                encode_frame(Frame(sequence, 2, (b"v", b"", b"", b"")))
        largest = Frame((1 << 64) - 1, 2, (b"v", b"", b"", b""))
        self.assertEqual(decode_frame(encode_frame(largest)), largest)
        source = decode_request_source(synthetic_sections()[0])
        for field in ("prior_wal_byte_length", "source_cut_event_index"):
            for value in (-1, 1 << 64):
                with self.subTest(field=field, value=value), self.assertRaises(CodecError):
                    encode_request_source(replace(source, **{field: value}))

    def test_receipt_sequence_and_policy_digest_mismatch_rejected(self) -> None:
        first, second, effect, fourth = synthetic_sections()
        receipt = decode_receipt(fourth)
        for changed in (
            replace(receipt, sequence=2),
            replace(receipt, prior_policy_digest="0" * 64),
            replace(receipt, next_policy_digest="0" * 64),
        ):
            wire = independently_frame(1, 3, (first, second, effect, encode_receipt(changed)))
            with self.subTest(changed=changed), self.assertRaises(CodecError):
                decode_frame(wire)

    def test_nested_section_tag_version_flags_trailing_and_truncation(self) -> None:
        first, second, _, fourth = synthetic_sections()
        for data, decoder in (
            (first, decode_request_source),
            (second, decode_candidate_state),
            (fourth, decode_receipt),
        ):
            for offset in (0, 4, 5, 6, 7):
                changed = bytearray(data)
                changed[offset] ^= 1
                with self.subTest(decoder=decoder.__name__, offset=offset):
                    with self.assertRaises(CodecError):
                        decoder(bytes(changed))
            with self.assertRaises(CodecError):
                decoder(data + b"x")
            for length in (0, 7, len(data) - 1):
                with self.assertRaises(CodecError):
                    decoder(data[:length])
        with self.assertRaises(CodecError):
            decode_frame(independently_frame(1, 3, (second, first, b"e", fourth)))

    def test_delivery_count_is_checked_before_allocation(self) -> None:
        data = synthetic_sections()[0]
        source = decode_request_source(data)
        empty = encode_request_source(replace(source, deliveries=()))
        impossible = empty[:-4] + struct.pack(">I", (1 << 32) - 1)
        with self.assertRaisesRegex(CodecError, "count"):
            decode_request_source(impossible)
        # Count that drops retained entries is rejected as trailing bytes.
        offset = len(empty) - 4
        with self.assertRaisesRegex(CodecError, "trailing"):
            decode_request_source(data[:offset] + struct.pack(">I", 2) + data[offset + 4 :])

    def test_encoder_rejects_aggregate_overflow_before_blob_copies(self) -> None:
        source = decode_request_source(synthetic_sections()[0])
        shared = b"s" * (MAX_FRAME_BYTES // 2)
        deliveries = tuple(
            replace(source.deliveries[0], event_index=index, signed_payload=shared)
            for index in (1, 2, 3)
        )
        with patch("formal.reference.isc_w1.codec._blob") as copy_blob:
            with self.assertRaisesRegex(CodecError, "total byte length"):
                encode_request_source(replace(source, deliveries=deliveries))
            copy_blob.assert_not_called()

    def test_source_event_order_and_cut_rejected(self) -> None:
        source = decode_request_source(synthetic_sections()[0])
        for deliveries in (
            source.deliveries[::-1],
            (source.deliveries[0], source.deliveries[0]),
            (replace(source.deliveries[0], event_index=5),),
        ):
            with self.subTest(deliveries=deliveries), self.assertRaises(CodecError):
                encode_request_source(replace(source, deliveries=deliveries))
        zero = replace(source, source_cut_event_index=0, deliveries=())
        self.assertEqual(decode_request_source(encode_request_source(zero)), zero)

    def test_ascii_content_ids_and_policy_digest_grammar(self) -> None:
        source = decode_request_source(synthetic_sections()[0])
        for text in ("", "bad\n", "é", "null\0"):
            with self.subTest(text=text), self.assertRaises(CodecError):
                encode_request_source(replace(source, source_index_id=text))
        receipt = decode_receipt(synthetic_sections()[3])
        for text in ("sha256:" + "A" * 64, "sha256:" + "a" * 63, "a" * 71):
            with self.subTest(text=text), self.assertRaises(CodecError):
                encode_receipt(replace(receipt, certificate_id=text))
        for text in ("sha256:" + "a" * 64, "A" * 64, "a" * 63):
            with self.subTest(text=text), self.assertRaises(CodecError):
                encode_receipt(replace(receipt, next_policy_digest=text))
        # Opaque key/source IDs do not gain an invented content-address grammar.
        delivery = replace(source.deliveries[0], key_id="old-key:Case-Sensitive")
        edited = replace(source, deliveries=(delivery,))
        self.assertEqual(decode_request_source(encode_request_source(edited)), edited)

    def test_policy_and_isc_boundaries(self) -> None:
        for size in (MAX_VALUE_BYTES - 1, MAX_VALUE_BYTES):
            candidate = CandidateState(b"p" * size, b"c" * size)
            self.assertEqual(decode_candidate_state(encode_candidate_state(candidate)), candidate)
        for candidate in (
            CandidateState(b"p" * (MAX_VALUE_BYTES + 1), b"c"),
            CandidateState(b"p", b"c" * (MAX_VALUE_BYTES + 1)),
        ):
            with self.assertRaises(CodecError):
                encode_candidate_state(candidate)
        bad = b"IFS1\0\1\0\0" + struct.pack(">I", MAX_VALUE_BYTES + 1)
        with self.assertRaises(CodecError):
            decode_candidate_state(bad)

    def test_command_envelope_boundaries(self) -> None:
        source = replace(decode_request_source(synthetic_sections()[0]), deliveries=())
        for size in (MAX_ENVELOPE_BYTES - 1, MAX_ENVELOPE_BYTES):
            candidate = replace(source, command_bytes=b"c" * size)
            self.assertEqual(decode_request_source(encode_request_source(candidate)), candidate)
        with self.assertRaises(CodecError):
            encode_request_source(replace(source, command_bytes=b"c" * (MAX_ENVELOPE_BYTES + 1)))

    def test_frame_boundaries(self) -> None:
        for size in (MAX_FRAME_BYTES - 1, MAX_FRAME_BYTES):
            frame = Frame(1, 2, (b"v" * (size - MIN_FRAME_BYTES), b"", b"", b""))
            wire = encode_frame(frame)
            self.assertEqual(len(wire), size)
            self.assertEqual(decode_frame(wire), frame)
        with self.assertRaises(CodecError):
            encode_frame(
                Frame(1, 2, (b"v" * (MAX_FRAME_BYTES - MIN_FRAME_BYTES + 1), b"", b"", b""))
            )
        with self.assertRaises(CodecError):
            decode_frame(b"x" * (MAX_FRAME_BYTES + 1))

    def test_output_content_boundaries_without_draft_result_codec(self) -> None:
        first, second, _, fourth = synthetic_sections()
        certificate = decode_candidate_state(second).certificate_bytes
        for size in (MAX_RESULT_BYTES - 1, MAX_RESULT_BYTES, MAX_RESULT_BYTES + 1):
            effect = b"e" * (size - len(certificate) - len(fourth))
            frame = Frame(1, 3, (first, second, effect, fourth))
            if size <= MAX_RESULT_BYTES:
                self.assertEqual(decode_frame(encode_frame(frame)), frame)
            else:
                with self.assertRaises(CodecError):
                    encode_frame(frame)

    def test_payload_authority_is_intentionally_absent(self) -> None:
        # Nested bodies are deliberately not canonical protocol objects. Structural
        # acceptance must never be described as semantic/canonical ISC validation.
        frame = Frame(1, 3, synthetic_sections())
        self.assertEqual(decode_frame(encode_frame(frame)), frame)


if __name__ == "__main__":
    unittest.main()
