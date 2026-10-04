"""REFERENCE_ONLY_NOT_PRODUCTION: approved W1 byte framing, with opaque payloads.

This module does not parse, authenticate, or construct consensus objects. A
successful decode establishes storage structure and byte integrity only. In
particular it does not establish canonical nested JSON, source completeness,
quorum, parent, signature, semantic identity, or seed authority.
"""

from dataclasses import dataclass
from hashlib import sha256

REFERENCE_ONLY_NOT_PRODUCTION = True
MAX_FRAME_BYTES = 64 * 1024 * 1024
MIN_FRAME_BYTES = 72
MAX_ENVELOPE_BYTES = 16 * 1024 * 1024
MAX_VALUE_BYTES = 4 * 1024 * 1024
MAX_RESULT_BYTES = 16 * 1024 * 1024
U32_MAX = (1 << 32) - 1
U64_MAX = (1 << 64) - 1


class CodecError(ValueError):
    """Malformed, unsupported, or over-bound local storage encoding."""


@dataclass(frozen=True)
class Frame:
    sequence: int
    kind: int
    sections: tuple[bytes, bytes, bytes, bytes]


@dataclass(frozen=True)
class Delivery:
    event_index: int
    peer_id: str
    vote_frame: bytes
    signed_payload: bytes
    signature_bytes: bytes
    key_id: str


@dataclass(frozen=True)
class RequestSource:
    command_bytes: bytes
    prior_wal_byte_length: int
    prior_wal_sha256: bytes
    source_index_id: str
    source_cut_event_index: int
    prior_state_bytes: bytes
    prior_policy_bytes: bytes
    deliveries: tuple[Delivery, ...]


@dataclass(frozen=True)
class CandidateState:
    policy_bytes: bytes
    certificate_bytes: bytes


@dataclass(frozen=True)
class Receipt:
    sequence: int
    command_id: str
    certificate_id: str
    effect_batch_id: str
    prior_policy_digest: str
    next_policy_digest: str


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise CodecError(reason)


def _uint(value: int, width: int) -> bytes:
    _require(type(value) is int and 0 <= value < 1 << (width * 8), "unsigned integer range")
    return value.to_bytes(width, "big")


def _bytes(value: bytes, cap: int, *, nonempty: bool = True) -> bytes:
    _require(type(value) is bytes, "immutable bytes required")
    _require((not nonempty or bool(value)) and len(value) <= cap, "byte length bound")
    return value


def _blob(value: bytes, cap: int, *, nonempty: bool = True) -> bytes:
    value = _bytes(value, cap, nonempty=nonempty)
    return _uint(len(value), 4) + value


def _text(value: str, *, content_id: bool = False, digest: bool = False) -> bytes:
    _require(type(value) is str, "ASCII identifier required")
    try:
        raw = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise CodecError("ASCII identifier required") from error
    _require(0 < len(raw) <= MAX_VALUE_BYTES, "ASCII identifier length")
    _require(all(0x20 <= item <= 0x7E for item in raw), "printable ASCII required")
    if content_id:
        _require(value.startswith("sha256:") and len(value) == 71, "content ID grammar")
        _require(all(item in "0123456789abcdef" for item in value[7:]), "content ID hex")
    if digest:
        _require(len(value) == 64, "policy digest length")
        _require(all(item in "0123456789abcdef" for item in value), "policy digest hex")
    return raw


def _t(value: str, *, content_id: bool = False) -> bytes:
    return _blob(_text(value, content_id=content_id), MAX_VALUE_BYTES)


def _join(parts: list[bytes], limit: int = MAX_FRAME_BYTES) -> bytes:
    _require(sum(map(len, parts)) <= limit, "total byte length bound")
    return b"".join(parts)


def _header(tag: bytes) -> bytes:
    return tag + b"\x00\x01\x00\x00"


class _Reader:
    def __init__(self, data: bytes, cap: int = MAX_FRAME_BYTES) -> None:
        _bytes(data, cap)
        self.data = memoryview(data)
        self.offset = 0

    @property
    def remaining(self) -> int:
        return len(self.data) - self.offset

    def take(self, count: int) -> bytes:
        _require(0 <= count <= self.remaining, "truncated bytes")
        result = self.data[self.offset : self.offset + count].tobytes()
        self.offset += count
        return result

    def uint(self, width: int) -> int:
        return int.from_bytes(self.take(width), "big")

    def blob(self, cap: int, *, nonempty: bool = True) -> bytes:
        count = self.uint(4)
        _require(count <= cap and (not nonempty or count > 0), "byte length bound")
        return self.take(count)

    def text(self, *, content_id: bool = False) -> str:
        raw = self.blob(71 if content_id else MAX_VALUE_BYTES)
        try:
            value = raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise CodecError("ASCII identifier required") from error
        _text(value, content_id=content_id)
        return value

    def header(self, tag: bytes) -> None:
        _require(self.take(8) == _header(tag), "section magic/version/flags mismatch")

    def finish(self) -> None:
        _require(self.remaining == 0, "trailing bytes")


def encode_request_source(value: RequestSource) -> bytes:
    _require(len(value.prior_wal_sha256) == 32, "prior WAL digest length")
    _bytes(value.prior_wal_sha256, 32)
    _require(type(value.deliveries) is tuple, "immutable delivery tuple required")
    _uint(len(value.deliveries), 4)
    _uint(value.prior_wal_byte_length, 8)
    _uint(value.source_cut_event_index, 8)
    # Check the complete size before making length-prefixed payload copies.
    total = (
        76
        + len(_bytes(value.command_bytes, MAX_ENVELOPE_BYTES))
        + len(_text(value.source_index_id))
        + len(_bytes(value.prior_state_bytes, MAX_ENVELOPE_BYTES))
        + len(_bytes(value.prior_policy_bytes, MAX_VALUE_BYTES))
    )
    _require(total <= MAX_FRAME_BYTES, "total byte length bound")
    prior = -1
    for delivery in value.deliveries:
        _uint(delivery.event_index, 8)
        _require(prior < delivery.event_index <= value.source_cut_event_index, "source event order")
        prior = delivery.event_index
        total += (
            28
            + len(_text(delivery.peer_id))
            + len(_bytes(delivery.vote_frame, MAX_ENVELOPE_BYTES))
            + len(_bytes(delivery.signed_payload, MAX_FRAME_BYTES))
            + len(_bytes(delivery.signature_bytes, MAX_FRAME_BYTES))
            + len(_text(delivery.key_id))
        )
        _require(total <= MAX_FRAME_BYTES, "total byte length bound")
    parts = [
        _header(b"IFQ1"),
        _blob(value.command_bytes, MAX_ENVELOPE_BYTES),
        _uint(value.prior_wal_byte_length, 8),
        value.prior_wal_sha256,
        _t(value.source_index_id),
        _uint(value.source_cut_event_index, 8),
        _blob(value.prior_state_bytes, MAX_ENVELOPE_BYTES),
        _blob(value.prior_policy_bytes, MAX_VALUE_BYTES),
        _uint(len(value.deliveries), 4),
    ]
    for delivery in value.deliveries:
        parts.extend(
            [
                _uint(delivery.event_index, 8),
                _t(delivery.peer_id),
                _blob(delivery.vote_frame, MAX_ENVELOPE_BYTES),
                _blob(delivery.signed_payload, MAX_FRAME_BYTES),
                _blob(delivery.signature_bytes, MAX_FRAME_BYTES),
                _t(delivery.key_id),
            ]
        )
    return _join(parts)


def decode_request_source(data: bytes) -> RequestSource:
    reader = _Reader(data)
    reader.header(b"IFQ1")
    command = reader.blob(MAX_ENVELOPE_BYTES)
    length, digest = reader.uint(8), reader.take(32)
    source, cut = reader.text(), reader.uint(8)
    state, policy = reader.blob(MAX_ENVELOPE_BYTES), reader.blob(MAX_VALUE_BYTES)
    count = reader.uint(4)
    # Each delivery needs U64 plus five U32 lengths. Bound before looping or allocation.
    _require(count <= reader.remaining // 28, "delivery count cannot fit section")
    deliveries = []
    prior = -1
    for _ in range(count):
        event = reader.uint(8)
        _require(prior < event <= cut, "source event order")
        prior = event
        deliveries.append(
            Delivery(
                event,
                reader.text(),
                reader.blob(MAX_ENVELOPE_BYTES),
                reader.blob(MAX_FRAME_BYTES),
                reader.blob(MAX_FRAME_BYTES),
                reader.text(),
            )
        )
    reader.finish()
    return RequestSource(command, length, digest, source, cut, state, policy, tuple(deliveries))


def encode_candidate_state(value: CandidateState) -> bytes:
    return _join(
        [
            _header(b"IFS1"),
            _blob(value.policy_bytes, MAX_VALUE_BYTES),
            _blob(value.certificate_bytes, MAX_VALUE_BYTES),
        ]
    )


def decode_candidate_state(data: bytes) -> CandidateState:
    reader = _Reader(data)
    reader.header(b"IFS1")
    result = CandidateState(reader.blob(MAX_VALUE_BYTES), reader.blob(MAX_VALUE_BYTES))
    reader.finish()
    return result


def encode_receipt(value: Receipt) -> bytes:
    return _join(
        [
            _header(b"IFR1"),
            _uint(value.sequence, 8),
            _t(value.command_id, content_id=True),
            _t(value.certificate_id, content_id=True),
            _t(value.effect_batch_id, content_id=True),
            _text(value.prior_policy_digest, digest=True),
            _text(value.next_policy_digest, digest=True),
        ]
    )


def decode_receipt(data: bytes) -> Receipt:
    reader = _Reader(data, 369)
    reader.header(b"IFR1")
    sequence = reader.uint(8)
    ids = [reader.text(content_id=True) for _ in range(3)]
    try:
        digests = [reader.take(64).decode("ascii") for _ in range(2)]
    except UnicodeDecodeError as error:
        raise CodecError("policy digest ASCII") from error
    for digest in digests:
        _text(digest, digest=True)
    reader.finish()
    return Receipt(sequence, ids[0], ids[1], ids[2], digests[0], digests[1])


def _validate_frame(frame: Frame) -> None:
    _uint(frame.sequence, 8)
    _require(frame.sequence > 0, "physical sequence starts at one")
    _require(type(frame.kind) is int and frame.kind in (1, 2, 3), "unknown journal kind")
    _require(type(frame.sections) is tuple and len(frame.sections) == 4, "four sections required")
    for section in frame.sections:
        _bytes(section, MAX_FRAME_BYTES, nonempty=False)
    _require(MIN_FRAME_BYTES + sum(map(len, frame.sections)) <= MAX_FRAME_BYTES, "frame bound")
    first, second, effect, fourth = frame.sections
    if frame.kind == 1:
        _require(all(frame.sections), "legacy transition sections required")
    elif frame.kind == 2:
        _require(bool(first) and not any(frame.sections[1:]), "legacy vote section shape")
    else:
        source = decode_request_source(first)
        state = decode_candidate_state(second)
        receipt = decode_receipt(fourth)
        _bytes(effect, MAX_ENVELOPE_BYTES)
        _require(receipt.sequence == frame.sequence, "receipt physical sequence mismatch")
        _require(
            receipt.prior_policy_digest == sha256(source.prior_policy_bytes).hexdigest(),
            "prior policy digest mismatch",
        )
        _require(
            receipt.next_policy_digest == sha256(state.policy_bytes).hexdigest(),
            "next policy digest mismatch",
        )
        # Necessary content-size bound only: no unapproved dedicated-result wire codec.
        _require(
            len(fourth) + len(effect) + len(state.certificate_bytes) <= MAX_RESULT_BYTES,
            "opaque result content exceeds existing bound",
        )


def encode_frame(frame: Frame) -> bytes:
    _validate_frame(frame)
    size = MIN_FRAME_BYTES + sum(map(len, frame.sections))
    prefix = _join(
        [
            _header(b"DRW1"),
            _uint(size, 4),
            _uint(frame.sequence, 8),
            _uint(frame.kind, 1),
            b"\x00\x00\x00",
            *[_blob(section, MAX_FRAME_BYTES, nonempty=False) for section in frame.sections],
        ]
    )
    return prefix + sha256(prefix).digest()


def decode_frame(data: bytes) -> Frame:
    _bytes(data, MAX_FRAME_BYTES)
    _require(len(data) >= MIN_FRAME_BYTES, "frame too short")
    _require(sha256(data[:-32]).digest() == data[-32:], "frame checksum mismatch")
    reader = _Reader(data[:-32])
    reader.header(b"DRW1")
    _require(reader.uint(4) == len(data), "frame length mismatch")
    sequence, kind = reader.uint(8), reader.uint(1)
    _require(kind in (1, 2, 3), "unknown journal kind")
    _require(reader.take(3) == b"\x00\x00\x00", "nonzero frame reserved bytes")
    sections = (
        reader.blob(MAX_FRAME_BYTES, nonempty=False),
        reader.blob(MAX_FRAME_BYTES, nonempty=False),
        reader.blob(MAX_FRAME_BYTES, nonempty=False),
        reader.blob(MAX_FRAME_BYTES, nonempty=False),
    )
    reader.finish()
    frame = Frame(sequence, kind, sections)
    _validate_frame(frame)
    return frame
