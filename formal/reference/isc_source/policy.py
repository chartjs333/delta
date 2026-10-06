"""DVPOL002 structural codec. Admission and producing origin are separate.

The complete retained layout differs from DVPOL001 only by the approved parent
field after each ISC context. It never accepts or upgrades a legacy policy.
"""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path
from types import MappingProxyType
from typing import Any

from formal.reference.isc_crypto.codec import _require

HEADER = b"DVPOL002\x00\x01\x00\x00\x00\x00\x00\x00"
MAX_BYTES, MAX_TEXT, MAX_ENTRIES = 4194304, 4096, 100000
SCHEMAS = MappingProxyType(
    {
        name: tuple(map(tuple, fields))
        for name, fields in json.loads(Path(__file__).with_name("policy-layout.json").read_text())[
            "schemas"
        ].items()
    }
)
REASONS = (
    "HARD_DEADLINE",
    "INCOMPLETE_INPUT",
    "UNSAFE_COEFFICIENTS",
    "IRRECOVERABLE_AVAILABILITY",
    "PARAMETER_FAILURE",
    "APPLY_FAILURE",
)


def vector_shape(shape: str) -> tuple[str, int] | None:
    if shape == "validators":
        return "text", 4096
    if shape == "candidates":
        return "candidate", 8192
    return (shape[:-2], MAX_ENTRIES) if shape.endswith("[]") else None


class _Writer:
    def __init__(self) -> None:
        self.parts: list[bytes] = []
        self.size = 0

    def append(self, raw: bytes) -> None:
        _require(self.size + len(raw) <= MAX_BYTES, "policy byte bound")
        self.size += len(raw)
        self.parts.append(raw)

    def value(self, shape: str, value: Any) -> None:
        if shape in {"u32", "u64", "i64"}:
            bits = 32 if shape == "u32" else 64
            low, high = (-(2**63), 2**63) if shape == "i64" else (0, 2**bits)
            _require(type(value) is int and low <= value < high, "policy integer")
            self.append((value % (2**bits)).to_bytes(bits // 8, "big"))
        elif shape == "bool":
            _require(type(value) is bool, "policy bool type")
            self.append(bytes([int(value)]))
        elif shape == "text":
            _require(type(value) is str and len(value) <= MAX_TEXT, "policy text bound")
            _require(all(32 <= ord(c) <= 126 for c in value), "policy ASCII")
            self.append(len(value).to_bytes(4, "big") + value.encode("ascii"))
        elif (vector := vector_shape(shape)) is not None:
            item, bound = vector
            _require(type(value) is list and len(value) <= bound, "policy vector bound")
            self.append(len(value).to_bytes(4, "big"))
            for entry in value:
                self.value(item, entry)
        else:
            fields = SCHEMAS[shape]
            _require(type(value) is dict and set(value) == {k for k, _ in fields}, "policy fields")
            for name, kind in fields:
                self.value(kind, value[name])


class _Reader:
    def __init__(self, raw: bytes) -> None:
        _require(type(raw) is bytes and len(raw) <= MAX_BYTES, "policy byte bound")
        self.raw, self.at = raw, 0

    def take(self, size: int) -> bytes:
        _require(0 <= size <= len(self.raw) - self.at, "policy truncated")
        result = self.raw[self.at : self.at + size]
        self.at += size
        return result

    def uint(self, size: int) -> int:
        return int.from_bytes(self.take(size), "big")

    def value(self, shape: str) -> Any:
        if shape in {"u32", "u64", "i64"}:
            number = self.uint(4 if shape == "u32" else 8)
            return number - 2**64 if shape == "i64" and number >= 2**63 else number
        if shape == "bool":
            number = self.uint(1)
            _require(number <= 1, "policy bool")
            return bool(number)
        if shape == "text":
            size = self.uint(4)
            _require(size <= MAX_TEXT, "policy text bound")
            raw = self.take(size)
            _require(all(32 <= c <= 126 for c in raw), "policy ASCII")
            return raw.decode("ascii")
        vector = vector_shape(shape)
        if vector is not None:
            item, bound = vector
            size = self.uint(4)
            _require(size <= bound, "policy vector bound")
            # Every item in this closed grammar occupies at least one byte.
            _require(size <= len(self.raw) - self.at, "policy aggregate truncation")
            return [self.value(item) for _ in range(size)]
        return {name: self.value(kind) for name, kind in SCHEMAS[shape]}


def canonical_shape(policy: dict[str, Any]) -> None:
    # Same structural (not authority) gates as the original native grammar.
    validators, candidates = policy["validator_ids"], policy["candidates"]
    _require(0 < len(validators) <= 4096, "policy validator count")
    _require(validators == sorted(set(validators)), "policy validator order")
    _require(policy["role"] == 1 and policy["configured_abort_reason"] in REASONS, "role/reason")
    _require(0 < len(candidates) <= 8192, "policy candidate count")
    _require(all(1 <= value["action"] <= 9 for value in candidates), "policy action")
    keys = [(c["height"], c["view"], c["action"], c["context_id"]) for c in candidates]
    _require(all(a < b for a, b in pairwise(keys)), "policy candidate order")
    _require(len({c["context_id"] for c in candidates}) == len(candidates), "duplicate context")


def encode(policy: dict[str, Any]) -> bytes:
    writer = _Writer()
    writer.append(HEADER)
    writer.value("policy", policy)
    canonical_shape(policy)
    return b"".join(writer.parts)


def decode(raw: bytes) -> dict[str, Any]:
    reader = _Reader(raw)
    _require(reader.take(len(HEADER)) == HEADER, "successor policy header required")
    policy = reader.value("policy")
    _require(reader.at == len(raw), "policy trailing bytes")
    canonical_shape(policy)
    _require(encode(policy) == raw, "policy canonical bytes")
    return policy
