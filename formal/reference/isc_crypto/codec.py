"""REFERENCE_ONLY_NOT_PRODUCTION: quarantined ISC draft byte conformance.

Implements ADR-0014 production-contract-amendment sections 3--6 as a reference
experiment. Canonical bytes do not establish trust, context/body/parent legality,
source lineage, durable intent, signature validity, or a qualified semantics ID.
No concrete formal_semantics_id is assigned by this module.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any

REFERENCE_ONLY_NOT_PRODUCTION = True
KEY_DOMAIN = "deltareduce.isc-ed25519-key.v1"
EVIDENCE_DOMAIN = "deltareduce.isc-evidence-budget.v1"
REGISTRY_DOMAIN = "deltareduce.isc-epoch-registry.v1"
VOTE_DOMAIN = "deltareduce:003:vote:v2"
ARTIFACT_DOMAIN = "deltareduce.isc-signature.v1"
M_DOMAIN = "deltareduce.isc-vote.ed25519.v1"
MAX_CONTROL_BYTES = 4 * 1024 * 1024
MAX_VOTE_BYTES = 4096
MAX_PREIMAGE_BYTES = 4282
MAX_ARTIFACT_BYTES = 4322
U64_MAX = (1 << 64) - 1
EVIDENCE_LIMITS = MappingProxyType(
    {
        "max_delivery_events": "4096",
        "max_delivery_bytes": "33554432",
        "max_vote_bytes": "4096",
        "max_vote_frame_bytes": "4096",
        "max_signature_artifact_bytes": "4322",
        "max_signed_payload_bytes": "4282",
        "max_peer_id_bytes": "128",
        "signature_bytes": "64",
        "key_id_bytes": "71",
        "max_command_bytes": "65536",
        "max_round_state_bytes": "65536",
        "max_policy_bytes": "4194304",
        "max_isc_bytes": "4194304",
        "max_effect_bytes": "1048576",
        "max_wal_frame_bytes": "67108864",
        "max_output_bytes": "16777216",
        "max_result_metadata_bytes": "8192",
    }
)
VOTE_KEYS = (
    "body_hash",
    "context_id",
    "durable_sequence",
    "formal_semantics_id",
    "height",
    "kind",
    "round_id",
    "schema_version",
    "type_name",
    "validator_epoch_id",
    "validator_id",
    "view",
)
REGISTRY_KEYS = {
    "evidence_budget_id",
    "formal_semantics_id",
    "origin_id",
    "quorum_threshold",
    "schema_version",
    "signature_profile",
    "validator_epoch_id",
    "validators",
}


class CodecError(ValueError):
    """Noncanonical, unsupported or malformed reference bytes."""


@dataclass(frozen=True)
class Vote:
    body_hash: str
    context_id: str
    durable_sequence: int
    formal_semantics_id: str
    height: int
    round_id: str
    validator_epoch_id: str
    validator_id: str
    view: int


@dataclass(frozen=True)
class Artifact:
    registry_id: str
    key_id: str
    vote_bytes: bytes
    signature: bytes


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise CodecError(message)


def _ascii(value: object) -> str:
    _require(type(value) is str, "ASCII string required")
    assert isinstance(value, str)
    _require(
        all(0x20 <= ord(char) <= 0x7E and char not in '\\"' for char in value),
        "ASCII string outside canonical subset",
    )
    return value


def _label(value: object) -> str:
    value = _ascii(value)
    _require(re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value) is not None, "label grammar")
    return value


def _id(value: object) -> str:
    value = _ascii(value)
    _require(re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None, "content ID grammar")
    return value


def _uint(value: int, width: int) -> bytes:
    _require(type(value) is int and 0 <= value < 1 << (width * 8), "unsigned integer range")
    return value.to_bytes(width, "big")


def _decimal(value: object, *, positive: bool = False) -> int:
    value = _ascii(value)
    _require(
        len(value) <= 20 and re.fullmatch(r"0|[1-9][0-9]*", value) is not None,
        "canonical unsigned decimal required",
    )
    number = int(value)
    _require(number <= U64_MAX and (not positive or number > 0), "unsigned integer range")
    return number


def _bytes(value: bytes, limit: int, *, exact: int | None = None) -> bytes:
    _require(type(value) is bytes, "immutable bytes required")
    _require(len(value) <= limit and (exact is None or len(value) == exact), "byte length bound")
    return value


def content_id(domain: str, data: bytes) -> str:
    """Domain-separated byte identity; never an authority or trust assertion."""
    _label(domain)
    _require(type(data) is bytes, "immutable bytes required")
    return "sha256:" + sha256(domain.encode("ascii") + b"\0" + data).hexdigest()


def _validate_json(value: Any) -> None:
    if type(value) is str:
        _ascii(value)
    elif type(value) is list:
        for item in value:
            _validate_json(item)
    elif type(value) is dict:
        for key, item in value.items():
            _ascii(key)
            _validate_json(item)
    else:
        raise CodecError("control JSON permits only string, array and object values")


def _json(document: dict[str, Any]) -> bytes:
    try:
        _validate_json(document)
        data = json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    except RecursionError as error:
        raise CodecError("control JSON recursion") from error
    return _bytes(data.encode("ascii"), MAX_CONTROL_BYTES)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON member")
        result[key] = value
    return result


def _no_number(value: str) -> None:
    raise CodecError("control JSON numeric values must be decimal strings")


def _load(data: bytes) -> dict[str, Any]:
    _bytes(data, MAX_CONTROL_BYTES)
    try:
        document = json.loads(
            data.decode("ascii"),
            object_pairs_hook=_pairs,
            parse_int=_no_number,
            parse_float=_no_number,
            parse_constant=_no_number,
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        raise CodecError("invalid canonical control JSON: " + str(error)) from error
    _require(type(document) is dict, "control JSON object required")
    _require(_json(document) == data, "noncanonical control JSON bytes")
    return document  # type: ignore[no-any-return]


def _closed(document: object, fields: set[str]) -> dict[str, Any]:
    _require(type(document) is dict, "closed object required")
    assert isinstance(document, dict)
    _require(set(document) == fields, "unknown or missing member")
    return document


def encode_key(public_key: bytes) -> bytes:
    _bytes(public_key, 32, exact=32)
    return _json(
        {"algorithm": "Ed25519", "public_key_hex": public_key.hex(), "schema_version": "1.0.0"}
    )


def decode_key(data: bytes) -> bytes:
    document = _closed(_load(data), {"algorithm", "public_key_hex", "schema_version"})
    _require(
        document["algorithm"] == "Ed25519" and document["schema_version"] == "1.0.0",
        "key algorithm/schema mismatch",
    )
    text = _ascii(document["public_key_hex"])
    _require(re.fullmatch(r"[0-9a-f]{64}", text) is not None, "public key hex grammar")
    key = bytes.fromhex(text)
    _require(encode_key(key) == data, "noncanonical key bytes")
    return key


def encode_evidence(formal_semantics_id: str) -> bytes:
    """Instantiate a supplied parameter; does not derive or qualify semantics."""
    return _json(
        {
            **EVIDENCE_LIMITS,
            "formal_semantics_id": _id(formal_semantics_id),
            "profile_id": "ISC-EVIDENCE-BUDGET-v1",
            "schema_version": "1.0.0",
        }
    )


def decode_evidence(data: bytes) -> dict[str, Any]:
    document = _closed(
        _load(data), set(EVIDENCE_LIMITS) | {"formal_semantics_id", "profile_id", "schema_version"}
    )
    _id(document["formal_semantics_id"])
    _require(
        encode_evidence(document["formal_semantics_id"]) == data,
        "fixed evidence profile or budget mismatch",
    )
    return document


def _check_registry(document: object, keys: Mapping[str, bytes], evidence: bytes) -> None:
    registry = _closed(document, REGISTRY_KEYS)
    budget = decode_evidence(evidence)
    _require(
        registry["evidence_budget_id"] == content_id(EVIDENCE_DOMAIN, evidence),
        "registry evidence binding mismatch",
    )
    _require(
        _id(registry["formal_semantics_id"]) == budget["formal_semantics_id"],
        "registry semantics binding mismatch",
    )
    _id(registry["validator_epoch_id"])
    _label(registry["origin_id"])
    _require(
        registry["quorum_threshold"] == "3"
        and registry["schema_version"] == "1.0.0"
        and registry["signature_profile"] == "SIG-ISC-ED25519-v1",
        "registry fixed profile mismatch",
    )
    validators = registry["validators"]
    _require(type(validators) is list and len(validators) == 4, "four validators required")
    previous = ""
    seen_keys: set[bytes] = set()
    for item in validators:
        entry = _closed(item, {"key_ref", "roles", "validator_id"})
        validator = _label(entry["validator_id"])
        _require(previous < validator, "validator order or duplicate")
        previous = validator
        _require(entry["roles"] == ["validator"], "registry role mismatch")
        key_ref = _id(entry["key_ref"])
        _require(key_ref in keys, "unavailable key reference")
        key_bytes = keys[key_ref]
        key = decode_key(key_bytes)
        _require(content_id(KEY_DOMAIN, key_bytes) == key_ref, "key reference mismatch")
        _require(key not in seen_keys, "duplicate validator public key")
        seen_keys.add(key)


def encode_registry(
    document: dict[str, Any], *, keys: Mapping[str, bytes], evidence: bytes
) -> bytes:
    """Validate artifact linkage, not independent bootstrap authorization."""
    _check_registry(document, keys, evidence)
    return _json(document)


def decode_registry(data: bytes, *, keys: Mapping[str, bytes], evidence: bytes) -> dict[str, Any]:
    document = _load(data)
    _check_registry(document, keys, evidence)
    _require(
        encode_registry(document, keys=keys, evidence=evidence) == data,
        "noncanonical registry bytes",
    )
    return document


def _vote_fields(vote: Vote) -> dict[str, str]:
    for value in (vote.durable_sequence, vote.height, vote.view):
        _uint(value, 8)
    _require(vote.durable_sequence > 0, "physical slot must be positive")
    return {
        "body_hash": _id(vote.body_hash),
        "context_id": _label(vote.context_id),
        "durable_sequence": str(vote.durable_sequence),
        "formal_semantics_id": _id(vote.formal_semantics_id),
        "height": str(vote.height),
        "kind": "ISC",
        "round_id": _label(vote.round_id),
        "schema_version": "2.0.0",
        "type_name": "VOTE",
        "validator_epoch_id": _id(vote.validator_epoch_id),
        "validator_id": _label(vote.validator_id),
        "view": str(vote.view),
    }


def _l(data: bytes) -> bytes:
    return _uint(len(data), 4) + data


def _txt(value: str) -> bytes:
    return b"\x21" + _l(value.encode("ascii"))


def encode_vote(vote: Vote) -> bytes:
    fields = _vote_fields(vote)
    payload = b"\x31" + _uint(12, 4)
    payload += b"".join(_txt(key) + _txt(fields[key]) for key in VOTE_KEYS)
    return _bytes(b"DRC1\x01\x00\x00\x03" + _l(payload), MAX_VOTE_BYTES)


class _Reader:
    def __init__(self, data: bytes, limit: int) -> None:
        self.data = memoryview(_bytes(data, limit))
        self.offset = 0

    @property
    def remaining(self) -> int:
        return len(self.data) - self.offset

    def take(self, length: int) -> bytes:
        _require(0 <= length <= self.remaining, "truncated bytes")
        data = self.data[self.offset : self.offset + length].tobytes()
        self.offset += length
        return data

    def u32(self) -> int:
        return int.from_bytes(self.take(4), "big")

    def blob(self, limit: int) -> bytes:
        length = self.u32()
        _require(length <= limit, "length bound")
        return self.take(length)

    def text(self, *, tagged: bool = False, content: bool = False) -> str:
        if tagged:
            _require(self.take(1) == b"\x21", "DRC1 text tag required")
        try:
            text = self.blob(71 if content else 128).decode("ascii")
        except UnicodeError as error:
            raise CodecError("ASCII text required") from error
        return _id(text) if content else _ascii(text)

    def finish(self) -> None:
        _require(self.remaining == 0, "trailing bytes")


def decode_vote(data: bytes) -> Vote:
    reader = _Reader(data, MAX_VOTE_BYTES)
    _require(reader.take(8) == b"DRC1\x01\x00\x00\x03", "vote envelope type/version")
    _require(reader.u32() == reader.remaining, "vote payload length mismatch")
    _require(reader.take(1) == b"\x31" and reader.u32() == 12, "vote map shape")
    fields = {}
    for expected in VOTE_KEYS:
        _require(reader.text(tagged=True) == expected, "vote field order/unknown/duplicate")
        fields[expected] = reader.text(tagged=True)
    reader.finish()
    _require(
        fields["kind"] == "ISC"
        and fields["schema_version"] == "2.0.0"
        and fields["type_name"] == "VOTE",
        "vote profile dispatch mismatch",
    )
    vote = Vote(
        fields["body_hash"],
        fields["context_id"],
        _decimal(fields["durable_sequence"], positive=True),
        fields["formal_semantics_id"],
        _decimal(fields["height"]),
        fields["round_id"],
        fields["validator_epoch_id"],
        fields["validator_id"],
        _decimal(fields["view"]),
    )
    _require(encode_vote(vote) == data, "noncanonical vote bytes")
    return vote


def preimage(registry_id: str, key_id: str, vote_bytes: bytes) -> bytes:
    decode_vote(vote_bytes)
    result = M_DOMAIN.encode("ascii") + b"\0"
    result += _l(_id(registry_id).encode("ascii")) + _l(_id(key_id).encode("ascii"))
    result += _l(vote_bytes)
    return _bytes(result, MAX_PREIMAGE_BYTES)


def decode_preimage(data: bytes) -> tuple[str, str, bytes]:
    reader = _Reader(data, MAX_PREIMAGE_BYTES)
    domain = M_DOMAIN.encode("ascii") + b"\0"
    _require(reader.take(len(domain)) == domain, "preimage domain mismatch")
    registry_id, key_id = reader.text(content=True), reader.text(content=True)
    vote_bytes = reader.blob(MAX_VOTE_BYTES)
    reader.finish()
    _require(preimage(registry_id, key_id, vote_bytes) == data, "preimage canonical mismatch")
    return registry_id, key_id, vote_bytes


def encode_artifact(artifact: Artifact) -> bytes:
    decode_vote(artifact.vote_bytes)
    _bytes(artifact.signature, 64, exact=64)
    result = b"ISG1\x00\x01\x00\x00"
    result += _l(_id(artifact.registry_id).encode("ascii"))
    result += _l(_id(artifact.key_id).encode("ascii")) + _l(artifact.vote_bytes)
    return _bytes(result + artifact.signature, MAX_ARTIFACT_BYTES)


def decode_artifact(data: bytes) -> Artifact:
    reader = _Reader(data, MAX_ARTIFACT_BYTES)
    _require(reader.take(8) == b"ISG1\x00\x01\x00\x00", "artifact header mismatch")
    registry_id, key_id = reader.text(content=True), reader.text(content=True)
    vote_bytes, signature = reader.blob(MAX_VOTE_BYTES), reader.take(64)
    reader.finish()
    artifact = Artifact(registry_id, key_id, vote_bytes, signature)
    _require(encode_artifact(artifact) == data, "artifact canonical mismatch")
    return artifact
