"""Bounded diagnostic readers for actual DRW1/DRS1/DVREC001 observations."""

import hashlib

from native_admission_snapshot import decode_flat, require


class Reader:
    def __init__(self, raw):
        require(type(raw) is bytes and len(raw) <= 1024 * 1024, "diagnostic size")
        self.raw, self.offset = raw, 0

    def take(self, n):
        require(0 <= n <= len(self.raw) - self.offset, "truncated diagnostic")
        result = self.raw[self.offset : self.offset + n]
        self.offset += n
        return result

    def uint(self, n):
        return int.from_bytes(self.take(n), "big")

    def section(self):
        return self.take(self.uint(4))

    def end(self):
        require(self.offset == len(self.raw), "trailing diagnostic")


def policy_digest(raw):
    require(type(raw) is bytes and 16 <= len(raw) <= 4 * 1024 * 1024, "policy size")
    require(raw[:16] == b"DVPOL001\x00\x01\x00\x00\x00\x00\x00\x00", "policy header")
    # Native parse/unique-reencode validates the full policy. This helper only hashes it.
    return hashlib.sha256(raw).hexdigest().encode("ascii")


def wal_entries(raw):
    """Exact observed frames/checksums. A truncated tail is unresolved here, not absent."""
    stream, result = Reader(raw), []
    while stream.offset < len(raw):
        start = stream.offset
        require(stream.take(8) == b"DRW1\x00\x01\x00\x00", "WAL header")
        size = stream.uint(4)
        require(72 <= size <= 1024 * 1024, "WAL frame size")
        frame = raw[start : start + size]
        require(len(frame) == size, "incomplete WAL observation")
        require(hashlib.sha256(frame[:-32]).digest() == frame[-32:], "WAL checksum")
        reader = Reader(frame[12:-32])
        sequence, kind = reader.uint(8), reader.uint(1)
        require(reader.take(3) == b"\0" * 3 and kind in {1, 2}, "WAL kind/reserved")
        sections = [reader.section() for _ in range(4)]
        reader.end()
        require(sequence == len(result) + 1, "WAL sequence")
        result.append(
            dict(
                sequence=sequence,
                kind=kind,
                command=sections[0],
                state=sections[1],
                effects=sections[2],
                record=sections[3],
            )
        )
        stream.offset = start + size
    return result


def bind_vote_entry(entry, policy):
    require(entry["kind"] == 2, "vote WAL kind")
    require(entry["state"] == entry["effects"] == b"", "vote WAL extra state/effects")
    require(entry["record"] == policy_digest(policy), "WAL exact policy identity")
    vote = decode_flat(entry["command"], 3)
    require(int(vote["durable_sequence"]) == entry["sequence"], "WAL vote sequence")
    return vote


def receipt(raw):
    reader = Reader(raw)
    require(reader.take(16) == b"DVREC001\x00\x01\x00\x00\x00\x00\x00\x00", "receipt header")
    action = reader.uint(4)
    require(1 <= action <= 9, "receipt action")
    require(reader.take(4) == b"\0" * 4, "receipt replay/reserved")
    seq = reader.uint(8)
    frame, vote_id, context = reader.section(), reader.section(), reader.section()
    reader.end()
    vote = decode_flat(frame, 3)
    computed = "sha256:" + hashlib.sha256(b"deltareduce:003:vote:v1\0" + frame).hexdigest()
    require(vote_id.decode("ascii") == computed, "receipt vote ID")
    require(seq > 0 and int(vote["durable_sequence"]) == seq, "receipt sequence")
    require(vote["context_id"].encode("ascii") == context, "receipt context")
    names = [
        "ROUND_CONFIG",
        "ISC",
        "EC",
        "APC",
        "PARAMETER",
        "AGGREGATE_ROOT",
        "APPLY",
        "VIEW_CHANGE",
        "ABORT",
    ]
    require(vote["kind"] == names[action - 1], "receipt action binding")
    return dict(sequence=seq, frame=frame, vote_id=computed, context=context.decode("ascii"))


def snapshot(raw):
    require(len(raw) >= 84, "snapshot size")
    require(hashlib.sha256(raw[:-32]).digest() == raw[-32:], "snapshot checksum")
    reader = Reader(raw[:-32])
    require(reader.take(8) == b"DRS1\x00\x01\x00\x00", "snapshot header")
    seq, length = reader.uint(8), reader.uint(4)
    digest, state = reader.take(32), reader.take(length)
    reader.end()
    require(hashlib.sha256(state).digest() == digest, "snapshot state hash")
    decode_flat(state, 5)
    return dict(sequence=seq, state=state)
