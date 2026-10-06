"""Approved scope-3 successor ISC B/b and C/c bytes, with symbolic sigma.

These constructors do not assert source legality, signatures, quorum delivery,
durability or complete profile admission. They cannot decode/relabel legacy C.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256

from formal.reference.isc_crypto.codec import (
    CodecError,
    _id,
    _label,
    _require,
    _uint,
    content_id,
)

BODY_DOMAIN = "deltareduce.vote.input-set-body.v2"
CERTIFICATE_DOMAIN = "deltareduce.008.input-set-certificate.v2"
LEAF_DOMAIN = b"deltareduce.008.isc-input-leaf.v1\0"
NODE_DOMAIN = b"deltareduce.004.merkle-node.v1\0"
MAX_CERTIFICATE_BYTES = 4194304
MAX_TUPLES = 100000


@dataclass(frozen=True)
class InputTuple:
    availability_certificate_id: str
    commitment_id: str
    domain_id: str
    ticket_id: str


@dataclass(frozen=True)
class Body:
    formal_semantics_id: str
    arithmetic_profile_id: str
    height: int
    parameter_schema_id: str
    round_config_id: str
    round_id: str
    validator_epoch_id: str
    view: int
    parent_checkpoint_id: str
    input_root: str
    tuples: tuple[InputTuple, ...]


@dataclass(frozen=True)
class Certificate:
    body: Body
    signer_ids: tuple[str, ...]
    quorum_threshold: int = 3


def _json(value: object) -> bytes:
    # All string fields have first passed ContentId/Label grammar.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        _require(key not in result, "REJECT_DUPLICATE_JSON_MEMBER")
        result[key] = value
    return result


def _reject_number(_: str) -> None:
    raise CodecError("only unsigned JSON integer fields are supported")


def _integer(text: str) -> int:
    _require(len(text) <= 20 and text.isascii() and text.isdecimal(), "unsigned integer")
    value = int(text)
    _uint(value, 8)
    return value


def _load(raw: bytes) -> object:
    _require(type(raw) is bytes and len(raw) <= MAX_CERTIFICATE_BYTES, "JSON byte bound")
    try:
        return json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_pairs,
            parse_int=_integer,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise CodecError("malformed canonical JSON") from error


def _closed(value: object, names: set[str]) -> dict[str, object]:
    _require(type(value) is dict and set(value) == names, "exact fields required")
    return value


def tuple_bytes(value: InputTuple) -> bytes:
    _id(value.availability_certificate_id)
    _id(value.commitment_id)
    _label(value.domain_id)
    _label(value.ticket_id)
    return _json(asdict(value))


def _read_tuple(document: object) -> InputTuple:
    fields = _closed(document, set(InputTuple.__dataclass_fields__))
    result = InputTuple(**fields)
    tuple_bytes(result)
    return result


def decode_tuple(raw: bytes) -> InputTuple:
    result = _read_tuple(_load(raw))
    _require(tuple_bytes(result) == raw, "noncanonical tuple bytes")
    return result


def validate_tuples(values: tuple[InputTuple, ...]) -> None:
    _require(type(values) is tuple and 0 < len(values) <= MAX_TUPLES, "tuple count")
    previous = None
    tickets: set[str] = set()
    for value in values:
        tuple_bytes(value)
        key = (value.ticket_id, value.commitment_id)
        _require(previous is None or previous < key, "strict tuple order")
        _require(value.ticket_id not in tickets, "repeated ticket")
        previous = key
        tickets.add(value.ticket_id)


def input_root(values: tuple[InputTuple, ...]) -> str:
    validate_tuples(values)
    level = [sha256(LEAF_DOMAIN + tuple_bytes(value)).digest() for value in values]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [
            sha256(NODE_DOMAIN + level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)
        ]
    return "sha256:" + level[0].hex()


def _text64(value: str) -> bytes:
    raw = value.encode("ascii")
    return _uint(len(raw), 8) + raw


def body_preimage(body: Body) -> bytes:
    for value in (
        body.formal_semantics_id,
        body.arithmetic_profile_id,
        body.parameter_schema_id,
        body.round_config_id,
        body.validator_epoch_id,
        body.parent_checkpoint_id,
        body.input_root,
    ):
        _id(value)
    _label(body.round_id)
    height, view = _uint(body.height, 8), _uint(body.view, 8)
    _require(body.height > 0, "positive native context height")
    _require(body.input_root == input_root(body.tuples), "input root mismatch")
    prefix = b"".join(
        (
            _text64(body.formal_semantics_id),
            _text64("2.0.0"),
            _text64(body.arithmetic_profile_id),
            height,
            _text64(body.parameter_schema_id),
            _text64(body.round_config_id),
            _text64(body.round_id),
            _text64(body.validator_epoch_id),
            view,
            _text64(body.parent_checkpoint_id),
            _text64(body.input_root),
            _uint(len(body.tuples), 8),
        )
    )
    rows = b"".join(
        _text64(value.availability_certificate_id)
        + _text64(value.commitment_id)
        + _text64(value.domain_id)
        + _text64(value.ticket_id)
        for value in body.tuples
    )
    return prefix + rows


def body_id(body: Body) -> str:
    return content_id(BODY_DOMAIN, body_preimage(body))


def vote_context_id(round_id: str) -> str:
    """Existing native ISC round context; parent/body/view cannot split it."""
    _label(round_id)
    return content_id("deltareduce.vote-context.isc.v1", _text64(round_id))


def certificate_bytes(certificate: Certificate) -> bytes:
    body = certificate.body
    body_preimage(body)
    _require(
        type(certificate.quorum_threshold) is int and certificate.quorum_threshold == 3,
        "profile quorum is three",
    )
    signers = certificate.signer_ids
    _require(type(signers) is tuple and 3 <= len(signers) <= 4, "profile signer count")
    for signer in signers:
        _label(signer)
    _require(tuple(sorted(set(signers))) == signers, "sorted unique original signers")
    fields = asdict(body)
    fields.update(
        schema_version="2.0.0",
        type_name="INPUT_SET_CERTIFICATE",
        quorum_threshold=certificate.quorum_threshold,
        signer_ids=signers,
    )
    raw = _json(fields)
    _require(len(raw) <= MAX_CERTIFICATE_BYTES, "certificate byte bound")
    return raw


def decode_certificate(raw: bytes) -> Certificate:
    fields = _closed(
        _load(raw),
        set(Body.__dataclass_fields__)
        | {"schema_version", "type_name", "quorum_threshold", "signer_ids"},
    )
    _require(fields["schema_version"] == "2.0.0", "successor schema required")
    _require(fields["type_name"] == "INPUT_SET_CERTIFICATE", "certificate kind")
    _require(type(fields["tuples"]) is list, "tuple array")
    _require(type(fields["signer_ids"]) is list, "signer array")
    body_fields = {key: fields[key] for key in Body.__dataclass_fields__}
    body_fields["tuples"] = tuple(_read_tuple(value) for value in fields["tuples"])
    result = Certificate(
        Body(**body_fields), tuple(fields["signer_ids"]), fields["quorum_threshold"]
    )
    _require(certificate_bytes(result) == raw, "noncanonical certificate bytes")
    return result


def certificate_id(certificate: Certificate) -> str:
    return content_id(CERTIFICATE_DOMAIN, certificate_bytes(certificate))


def resolve_body(reference: str, certificates: tuple[Certificate, ...]) -> Body:
    """Typed b lookup. A signer-dependent c never acts as a fallback."""
    _id(reference)
    matches = [value.body for value in certificates if body_id(value.body) == reference]
    _require(bool(matches), "unknown consensus body identity")
    _require(all(value == matches[0] for value in matches), "body identity collision")
    return matches[0]


def resolve_witness(reference: str, certificates: tuple[Certificate, ...]) -> Certificate:
    """Typed c lookup. Multiple witnesses for B are retained independently."""
    _id(reference)
    matches = [value for value in certificates if certificate_id(value) == reference]
    _require(bool(matches), "unknown certificate witness identity")
    _require(all(value == matches[0] for value in matches), "certificate identity collision")
    return matches[0]
