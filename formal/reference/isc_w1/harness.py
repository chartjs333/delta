"""REFERENCE_ONLY_NOT_PRODUCTION: single-writer byte-storage experiment.

This harness validates framing and physical prefix binding, not source authority,
quorum, signatures, policy transitions, or consensus replay. An intact file is
not authenticated history. Callers must retain their independent prefix floor.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Literal

from formal.reference.isc_w1.codec import (
    MAX_FRAME_BYTES,
    Frame,
    decode_frame,
    decode_request_source,
    encode_frame,
)

Fault = Literal[
    "before_append", "partial_append", "before_barrier", "barrier_failure", "before_expose"
]


class StorageError(ValueError):
    """The reference file cannot be used without a fresh verified scan."""


class InjectedFault(OSError):
    """A test cut; no successful append result was exposed."""


@dataclass(frozen=True)
class StoredFrame:
    frame: Frame
    raw: bytes
    replayed: bool = False


@dataclass(frozen=True)
class Scan:
    records: tuple[StoredFrame, ...]
    byte_length: int
    sha256: bytes

    @property
    def physical_slots(self) -> int:
        return len(self.records)

    @property
    def vote_count(self) -> int:
        return sum(record.frame.kind == 2 for record in self.records)


def _scan(stream: BinaryIO, required_prefix: bytes) -> Scan:
    """Read every frame, without truncation, resynchronization, or kind skipping."""
    stream.seek(0)
    records: list[StoredFrame] = []
    digest = hashlib.sha256()
    length = 0
    floor_offset = 0
    while True:
        header = stream.read(12)
        if not header:
            break
        if len(header) != 12:
            raise StorageError("torn frame header")
        total = int.from_bytes(header[8:12], "big")
        # 24 fixed header bytes + four U32 lengths + 32 checksum bytes.
        if not 72 <= total <= MAX_FRAME_BYTES:
            raise StorageError("frame length outside approved bounds")
        raw = header + stream.read(total - len(header))
        if len(raw) != total:
            raise StorageError("torn frame body; tail retained")
        frame = decode_frame(raw)
        if frame.sequence != len(records) + 1:
            raise StorageError("physical slot gap, duplicate, or rewrite")
        if frame.kind == 3:
            request = decode_request_source(frame.sections[0])
            if (
                request.prior_wal_byte_length != length
                or request.prior_wal_sha256 != digest.digest()
            ):
                raise StorageError("W1 original prefix mismatch")
        count = min(len(raw), len(required_prefix) - floor_offset)
        if raw[:count] != required_prefix[floor_offset : floor_offset + count]:
            raise StorageError("retained prefix floor differs")
        floor_offset += count
        digest.update(raw)
        length += len(raw)
        records.append(StoredFrame(frame, raw))
    if floor_offset != len(required_prefix):
        raise StorageError("retained prefix floor is missing")
    return Scan(tuple(records), length, digest.digest())


def scan_file(path: Path, *, required_prefix: bytes = b"") -> Scan:
    """Structural diagnostics only; success grants no protocol readiness."""
    with path.open("rb") as stream:
        return _scan(stream, required_prefix)


class FileHarness:
    """Append/barrier/reopen test harness; one owner, no concurrent writers.

    File fsync is real. Directory durability, authenticated provenance, malicious
    pathname replacement, process/power-loss guarantees and native recovery are
    outside this experiment. READY here means storage-harness readiness only.
    """

    def __init__(self, path: Path, stream: BinaryIO, scan: Scan) -> None:
        self.path = path
        self._stream = stream
        self._scan = scan
        self.ready = True

    @classmethod
    def create(cls, path: Path) -> FileHarness:
        stream = path.open("x+b", buffering=0)
        try:
            os.fsync(stream.fileno())
            return cls(path, stream, _scan(stream, b""))
        except BaseException:
            stream.close()
            raise

    @classmethod
    def reopen(cls, path: Path, *, required_prefix: bytes = b"") -> FileHarness:
        # Missing file is an error, never proof of absent uncertain append.
        stream = path.open("r+b", buffering=0)
        try:
            scan = _scan(stream, required_prefix)
            os.fsync(stream.fileno())
            return cls(path, stream, scan)
        except BaseException:
            stream.close()
            raise

    @property
    def snapshot(self) -> Scan:
        if not self.ready:
            raise StorageError("unknown physical tip; reopen and scan required")
        return self._scan

    def close(self) -> None:
        self.ready = False
        self._stream.close()

    def __enter__(self) -> FileHarness:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def append(self, frame: Frame, *, fault: Fault | None = None) -> StoredFrame:
        if not self.ready:
            raise StorageError("harness fenced until reopen")
        if fault not in (
            None,
            "before_append",
            "partial_append",
            "before_barrier",
            "barrier_failure",
            "before_expose",
        ):
            raise StorageError("unknown fault injection")
        raw = encode_frame(frame)
        # Detect changes between calls; this is not a concurrent-writer lock.
        try:
            current = _scan(self._stream, b"")
            if current.byte_length != self._scan.byte_length or current.sha256 != self._scan.sha256:
                raise StorageError("file changed since verified scan")
        except (OSError, ValueError):
            self.ready = False
            raise
        if frame.sequence <= current.physical_slots:
            original = current.records[frame.sequence - 1]
            if original.raw != raw:
                raise StorageError("original slot conflict")
            return StoredFrame(original.frame, original.raw, replayed=True)
        if frame.sequence != current.physical_slots + 1:
            raise StorageError("new frame must use next physical slot")
        if frame.kind == 3:
            request = decode_request_source(frame.sections[0])
            if (
                request.prior_wal_byte_length != current.byte_length
                or request.prior_wal_sha256 != current.sha256
            ):
                raise StorageError("candidate binds a different original prefix")
        if fault == "before_append":
            raise InjectedFault("before append; no write")
        # Preallocate the candidate generation before touching the file.
        result = StoredFrame(frame, raw)
        digest = hashlib.sha256()
        for record in current.records:
            digest.update(record.raw)
        digest.update(raw)
        candidate = Scan(
            (*current.records, result), current.byte_length + len(raw), digest.digest()
        )
        self.ready = False
        self._stream.seek(current.byte_length)
        to_write = raw[: len(raw) // 2] if fault == "partial_append" else raw
        written = self._stream.write(to_write)
        if written != len(to_write):
            raise OSError("short write; durability unknown")
        if fault in ("partial_append", "before_barrier", "barrier_failure"):
            raise InjectedFault(str(fault))
        os.fsync(self._stream.fileno())
        self._scan = candidate
        if fault == "before_expose":
            raise InjectedFault("barrier completed; no successful result exposed")
        self.ready = True
        return result
