"""T047/T053: full original mixed-WAL byte projection, before protocol replay.

The caller supplies independently retained bytes, never a journal synthesized
from public votes. Structural continuity is necessary but is not producer
legality, signature authentication or recovery readiness.
"""

from dataclasses import dataclass
from io import BytesIO

from formal.reference.isc_crypto.codec import _require
from formal.reference.isc_w1.codec import Frame, decode_request_source
from formal.reference.isc_w1.harness import _scan
from formal.reference.profile_source.metadata import MAX_RECORDS, raw_id


@dataclass(frozen=True)
class Position:
    original: bytes
    decoded: Frame
    byte_offset: int
    vote_count: int


@dataclass(frozen=True)
class Journal:
    original: bytes
    positions: tuple[Position, ...]
    # A cut is a physical prefix, not an assertion of finality/durability.
    cut_slot: int
    cut_bytes: bytes

    @property
    def vote_count(self):
        return self.positions[-1].vote_count if self.positions else 0

    @property
    def original_votes(self):
        return tuple(p for p in self.positions if p.decoded.kind == 2)


def inspect(original: bytes, *, cut_slot: int, required_prefix: bytes) -> Journal:
    _require(type(original) is bytes and type(required_prefix) is bytes, "original journal bytes")
    _require(type(cut_slot) is int and cut_slot >= 0, "physical cut slot")
    scan = _scan(BytesIO(original), required_prefix)
    _require(len(scan.records) <= MAX_RECORDS, "approved original record budget")
    _require(cut_slot <= len(scan.records), "cut past original physical tip")
    positions, byte_offset, votes = [], 0, 0
    for stored in scan.records:
        votes += stored.frame.kind == 2
        positions.append(Position(stored.raw, stored.frame, byte_offset, votes))
        byte_offset += len(stored.raw)
    _require(byte_offset == len(original), "no ignored tail")
    cut_end = positions[cut_slot].byte_offset if cut_slot < len(positions) else byte_offset
    return Journal(original, tuple(positions), cut_slot, original[:cut_end])


def exact_existing(journal: Journal, physical_slot: int, original_frame: bytes) -> Position:
    """An exact retry references the original occurrence; it allocates nothing."""
    _require(
        type(physical_slot) is int and 1 <= physical_slot <= len(journal.positions), "existing slot"
    )
    position = journal.positions[physical_slot - 1]
    _require(position.original == original_frame, "conflicting replay at original physical slot")
    return position


def verify_inventory_row(journal: Journal, row: dict) -> None:
    _require(
        row["ref"]["content_id"] == raw_id(journal.original)
        and int(row["ref"]["byte_length"]) == len(journal.original)
        and int(row["entry_count"]) == len(journal.positions)
        and int(row["first_sequence"]) == (1 if journal.positions else 0)
        and int(row["last_sequence"]) == len(journal.positions),
        "manifest interval covers full original journal, not vote count",
    )


def finalization_prefix(journal: Journal, physical_slot: int) -> bytes:
    _require(
        type(physical_slot) is int and 1 <= physical_slot <= len(journal.positions), "existing slot"
    )
    position = journal.positions[physical_slot - 1]
    _require(position.decoded.kind == 3, "original kind-3 finalization")
    request = decode_request_source(position.decoded.sections[0])
    prefix = journal.original[: position.byte_offset]
    # inspect also checks this; keep the dependency explicit for consumers.
    _require(
        request.prior_wal_byte_length == len(prefix)
        and request.prior_wal_sha256.hex() == raw_id(prefix)[7:],
        "exact W1 preceding physical prefix",
    )
    return prefix
