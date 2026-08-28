"""Independent exact-integer oracle for the ``int16-fixed-v1`` golden corpus.

This module does not participate in consensus acceptance.  The authoritative implementation is
the portable C++ core.  Keeping this oracle in the worker package gives the two implementations
different parsing, state and error-handling designs while sharing only the frozen wire contract.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

FORMAL_SEMANTICS_ID: Final = (
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
)
Q_MIN: Final = -32767
Q_MAX: Final = 32767
I64_MAX: Final = (1 << 63) - 1
I64_MIN: Final = -(1 << 63)
MAX_HEADER_BYTES: Final = 65_536
MAX_PAYLOAD_BYTES: Final = 1_048_576
ENVELOPE_MAGIC: Final = b"DRQ1"
ENVELOPE_PREFIX_BYTES: Final = 16


class ContractError(ValueError):
    """A deterministic rejection with a protocol status code."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class Rational:
    """A canonical reduced rational accepted by the fixture oracle."""

    numerator: int
    denominator: int

    @classmethod
    def parse(cls, value: Mapping[str, object], *, positive: bool = False) -> Rational:
        if set(value) != {"denominator", "numerator"}:
            raise ContractError("RATIONAL_FIELDS_INVALID", "expected numerator and denominator")
        numerator = _parse_i64_decimal(value["numerator"], "numerator")
        denominator = _parse_u32(value["denominator"], "denominator")
        if denominator == 0:
            raise ContractError("RATIONAL_ZERO_DENOMINATOR", "denominator must be positive")
        if positive and numerator <= 0:
            raise ContractError("SCALE_NOT_POSITIVE", "scale numerator must be positive")
        if positive and numerator > 0xFFFFFFFF:
            raise ContractError("SCALE_NUMERATOR_OUT_OF_RANGE", "scale numerator exceeds UINT32")
        if numerator == 0 and denominator != 1:
            raise ContractError("RATIONAL_ZERO_NOT_CANONICAL", "zero is exactly 0/1")
        if math.gcd(abs(numerator), denominator) != 1:
            raise ContractError("RATIONAL_NOT_REDUCED", "fraction must be in lowest terms")
        return cls(numerator=numerator, denominator=denominator)

    def to_json(self) -> dict[str, object]:
        return {"denominator": self.denominator, "numerator": str(self.numerator)}


def _parse_i64_decimal(value: object, field: str) -> int:
    if not isinstance(value, str) or not value:
        raise ContractError("DECIMAL_INVALID", f"{field} must be a decimal string")
    if value == "-0" or value.startswith("+") or (value.startswith("0") and value != "0"):
        raise ContractError("DECIMAL_NOT_CANONICAL", f"{field} is not canonical")
    if value.startswith("-0") or not value.removeprefix("-").isdigit():
        raise ContractError("DECIMAL_NOT_CANONICAL", f"{field} is not canonical")
    parsed = int(value)
    if parsed < I64_MIN or parsed > I64_MAX:
        raise ContractError("DECIMAL_OUT_OF_RANGE", f"{field} exceeds signed INT64")
    return parsed


def _parse_u32(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 0xFFFFFFFF:
        raise ContractError("U32_INVALID", f"{field} must be an unsigned 32-bit integer")
    return value


def canonical_json_bytes(value: object) -> bytes:
    """Return the feature-004 canonical JSON representation."""

    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("CANONICAL_JSON_INVALID", str(exc)) from exc
    return text.encode("utf-8")


def content_id(domain: str, payload: bytes) -> str:
    """Hash one immutable artifact using the named feature-004 domain."""

    if not domain.isascii() or not domain.startswith("deltareduce.004."):
        raise ContractError("HASH_DOMAIN_INVALID", domain)
    digest = hashlib.sha256(domain.encode("ascii") + b"\x00" + payload).hexdigest()
    return f"sha256:{digest}"


def _checked_positive_product(left: int, right: int) -> int:
    product = left * right
    if product > I64_MAX:
        raise ContractError(
            "QUANTIZATION_INTERMEDIATE_OVERFLOW", "scaled rational exceeds signed INT64"
        )
    return product


def quantize(source: Rational, quantum: Rational) -> int:
    """Quantize ``source / quantum`` with signed nearest-ties-to-even."""

    if quantum.numerator <= 0:
        raise ContractError("SCALE_NOT_POSITIVE", "quantum must be positive")
    magnitude = _checked_positive_product(abs(source.numerator), quantum.denominator)
    divisor = _checked_positive_product(source.denominator, quantum.numerator)
    quotient, remainder = divmod(magnitude, divisor)
    twice_remainder = remainder * 2
    if twice_remainder > divisor or (twice_remainder == divisor and quotient % 2 == 1):
        quotient += 1
    result = -quotient if source.numerator < 0 else quotient
    if result < Q_MIN or result > Q_MAX:
        raise ContractError("QUANTIZATION_RANGE_EXCEEDED", str(result))
    return result


def encode_payload(values: Iterable[int]) -> bytes:
    """Encode canonical q values as signed two's-complement INT16 little-endian."""

    encoded = bytearray()
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int) or value < Q_MIN or value > Q_MAX:
            raise ContractError("Q_VALUE_OUT_OF_RANGE", str(value))
        encoded.extend(struct.pack("<h", value))
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ContractError("SHARD_PAYLOAD_TOO_LARGE", str(len(encoded)))
    return bytes(encoded)


def encode_envelope(header: Mapping[str, object], payload: bytes) -> bytes:
    """Encode the bounded DRQ1 envelope without raw-memory struct serialization."""

    header_bytes = canonical_json_bytes(dict(header))
    if len(header_bytes) > MAX_HEADER_BYTES:
        raise ContractError("SHARD_HEADER_TOO_LARGE", str(len(header_bytes)))
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ContractError("SHARD_PAYLOAD_TOO_LARGE", str(len(payload)))
    prefix = ENVELOPE_MAGIC + struct.pack("<HHII", 1, 0, len(header_bytes), len(payload))
    if len(prefix) != ENVELOPE_PREFIX_BYTES:
        raise AssertionError("DRQ1 prefix size changed")
    return prefix + header_bytes + payload


def leaf_id(envelope: bytes) -> str:
    return content_id("deltareduce.004.shard-leaf.v1", envelope)


def merkle_root(leaves: Sequence[str]) -> str:
    """Compute the ordered binary root; an odd final node is duplicated."""

    if not leaves:
        raise ContractError("EMPTY_SHARD_TABLE", "at least one shard is required")
    nodes: list[bytes] = []
    for leaf in leaves:
        if not leaf.startswith("sha256:") or len(leaf) != 71:
            raise ContractError("CONTENT_ID_INVALID", leaf)
        try:
            nodes.append(bytes.fromhex(leaf[7:]))
        except ValueError as exc:
            raise ContractError("CONTENT_ID_INVALID", leaf) from exc
    domain = b"deltareduce.004.merkle-node.v1\x00"
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        nodes = [
            hashlib.sha256(domain + nodes[index] + nodes[index + 1]).digest()
            for index in range(0, len(nodes), 2)
        ]
    return f"sha256:{nodes[0].hex()}"
