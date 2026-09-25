"""Bounded proposal codec for PR50 ISC *voted bodies*, not admission or a QC.

The native encoder accepts typed strings/lists without deciding validity. This
projection preserves that distinction: order, duplicates and empty lists are
encoded, never silently sorted or certified. The ASCII/resource profile below
is a tooling restriction, not a newly asserted native admission rule.
"""

import hashlib
from dataclasses import asdict, dataclass

from formal_artifacts import canonical_json_bytes

VERSION = "deltareduce.native-isc-body.v1-candidate"
DOMAIN = b"deltareduce.vote.input-set-body.v1\0"
MAX_BYTES = 4 * 1024 * 1024
MAX_ITEMS = 4096
MAX_TEXT = 128


def require(condition, message):
    if not condition:
        raise ValueError(message)


def u64(value):
    require(type(value) is int and 0 <= value < 2**64, "uint64")
    return value.to_bytes(8, "big")


def text(value):
    require(type(value) is str, "text type")
    raw = value.encode("ascii")
    require(len(raw) <= MAX_TEXT, "text length")
    return u64(len(raw)) + raw


@dataclass(frozen=True)
class Context:
    arithmetic_profile_id: str
    height: int
    parameter_schema_id: str
    round_config_id: str
    round_id: str
    validator_epoch_id: str
    view: int

    def encode(self):
        return b"".join(
            [
                text(self.arithmetic_profile_id),
                u64(self.height),
                text(self.parameter_schema_id),
                text(self.round_config_id),
                text(self.round_id),
                text(self.validator_epoch_id),
                u64(self.view),
            ]
        )


@dataclass(frozen=True)
class InputTuple:
    availability_certificate_id: str
    commitment_id: str
    domain_id: str
    ticket_id: str

    def encode(self):
        return b"".join(text(value) for value in asdict(self).values())


@dataclass(frozen=True)
class Body:
    context: Context
    input_root: str
    tuples: tuple[InputTuple, ...]

    def encode(self):
        require(type(self.context) is Context, "context type")
        require(type(self.tuples) is tuple and len(self.tuples) <= MAX_ITEMS, "tuple count/type")
        require(all(type(row) is InputTuple for row in self.tuples), "tuple type")
        result = b"".join(
            [self.context.encode(), text(self.input_root), u64(len(self.tuples))]
            + [row.encode() for row in self.tuples]
        )
        require(len(result) <= MAX_BYTES, "body size")
        return result

    def content_id(self):
        return "sha256:" + hashlib.sha256(DOMAIN + self.encode()).hexdigest()


class Reader:
    def __init__(self, raw):
        require(type(raw) is bytes and len(raw) <= MAX_BYTES, "body size/type")
        self.raw, self.position = raw, 0

    def take(self, length):
        require(0 <= length <= len(self.raw) - self.position, "truncated")
        value = self.raw[self.position : self.position + length]
        self.position += length
        return value

    def uint(self):
        return int.from_bytes(self.take(8), "big")

    def string(self):
        size = self.uint()
        require(size <= MAX_TEXT, "text length")
        return self.take(size).decode("ascii")


def decode(raw):
    reader = Reader(raw)
    context = Context(
        reader.string(),
        reader.uint(),
        reader.string(),
        reader.string(),
        reader.string(),
        reader.string(),
        reader.uint(),
    )
    root, count = reader.string(), reader.uint()
    require(count <= min(MAX_ITEMS, (len(raw) - reader.position) // 32), "tuple count")
    rows = tuple(
        InputTuple(reader.string(), reader.string(), reader.string(), reader.string())
        for _ in range(count)
    )
    require(reader.position == len(raw), "trailing bytes")
    result = Body(context, root, rows)
    require(result.encode() == raw, "noncanonical")
    return result


def from_fields(fields):
    require(
        type(fields) is dict and set(fields) == {"context", "input_root", "tuples"}, "body fields"
    )
    context, rows = fields["context"], fields["tuples"]
    require(
        type(context) is dict and set(context) == set(Context.__annotations__), "context fields"
    )
    require(type(rows) is list and len(rows) <= MAX_ITEMS, "tuple count/type")
    require(
        all(type(row) is dict and set(row) == set(InputTuple.__annotations__) for row in rows),
        "tuple fields",
    )
    result = Body(
        Context(**context), fields["input_root"], tuple(InputTuple(**row) for row in rows)
    )
    result.encode()
    return result


def witness(body):
    raw = body.encode()
    fields = asdict(body)
    fields["tuples"] = list(fields["tuples"])
    return {
        "version": VERSION,
        "fields": fields,
        "body_bytes_hex": raw.hex(),
        "hash_preimage_hex": (DOMAIN + raw).hex(),
        "body_id": body.content_id(),
        "scope": "TYPED_BODY_ENCODING_ONLY_NOT_ADMISSION_OR_QC",
        "native_export_authenticated": False,
        "gate_eligible": False,
    }


def verify_witness(candidate, expected_body):
    """expected_body is independently resolved, not read from the candidate."""
    require(
        type(candidate) is dict
        and canonical_json_bytes(candidate) == canonical_json_bytes(witness(expected_body)),
        "witness mismatch",
    )
    decoded = decode(bytes.fromhex(candidate["body_bytes_hex"]))
    require(decoded == from_fields(candidate["fields"]) == expected_body, "decoded identity")
    return decoded
