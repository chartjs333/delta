"""T047/T053: exact ADR0016 bytes, with the approved ADR0018 AC claim.

No physical-presence assertion, producer-history oracle, new source cap or
consensus vote/WAL identity is introduced. The caller must separately establish
independent bootstrap/configuration provenance and the original event prefix.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from formal.reference.isc_crypto.codec import (
    CodecError,
    _closed,
    _decimal,
    _id,
    _label,
    _no_number,
    _pairs,
    _require,
    _uint,
    _validate_json,
    content_id,
    decode_key,
    encode_key,
)
from formal.reference.isc_crypto.sodium_reference import SodiumReference

KEY_DOMAIN = "deltareduce.storage-ed25519-key.v1"
REGISTRY_DOMAIN = "deltareduce.storage-epoch-registry.v1"
BODY_DOMAIN = "deltareduce.storage-attestation-body.v1"
SIGN_DOMAIN = "deltareduce.storage-attestation.ed25519.v1"
ARTIFACT_DOMAIN = "deltareduce.storage-attestation-signature.v1"
CERTIFICATE_DOMAIN = "deltareduce.storage-availability-certificate.v1"
COMMON = {
    "commitment_id",
    "formal_semantics_id",
    "height",
    "origin_id",
    "parent_checkpoint_id",
    "retention_epoch_id",
    "round_config_id",
    "round_id",
    "schema_version",
    "storage_epoch_id",
    "storage_registry_id",
    "ticket_id",
}
ATTESTATION = COMMON | {"envelope_bytes", "key_id", "leaf_id", "storage_id", "type_name"}
CERTIFICATE = COMMON | {"attestation_ids", "threshold", "type_name"}
REGISTRY = {
    "formal_semantics_id",
    "members",
    "origin_id",
    "schema_version",
    "signature_profile",
    "storage_epoch_id",
    "type_name",
}


def canonical(document: dict[str, Any]) -> bytes:
    """J without borrowing ISC's unrelated 4 MiB control-message cap.

    The complete source/W1 budget is a separate enclosing admission check. The
    closed scalar grammars and SAG1 U32 framing are enforced below.
    """
    try:
        _require(type(document) is dict, "canonical object required")
        _validate_json(document)
        return json.dumps(
            document, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("ascii")
    except (UnicodeError, RecursionError) as exc:
        raise CodecError("canonical source JSON") from exc


def load(raw: bytes) -> dict[str, Any]:
    _require(type(raw) is bytes, "original immutable bytes required")
    try:
        obj = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_pairs,
            parse_int=_no_number,
            parse_float=_no_number,
            parse_constant=_no_number,
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise CodecError("canonical source JSON: " + str(exc)) from exc
    _require(type(obj) is dict and canonical(obj) == raw, "noncanonical source JSON")
    return obj


def common(obj: dict[str, Any]) -> None:
    _require(obj["schema_version"] == "1.0.0", "source schema")
    for key in (
        "commitment_id",
        "formal_semantics_id",
        "origin_id",
        "parent_checkpoint_id",
        "round_config_id",
        "storage_registry_id",
    ):
        _id(obj[key])
    for key in ("round_id", "retention_epoch_id", "storage_epoch_id"):
        _label(obj[key])
    _decimal(obj["height"])
    _require(
        type(obj["ticket_id"]) is str
        and re.fullmatch(r"[A-Za-z0-9._:/-]{1,255}", obj["ticket_id"]) is not None,
        "source ticket lexical envelope",
    )


def attestation(raw: bytes) -> dict[str, Any]:
    obj = _closed(load(raw), ATTESTATION)
    common(obj)
    _require(obj["type_name"] == "STORAGE_AVAILABILITY_ATTESTATION", "attestation type")
    _label(obj["storage_id"])
    _id(obj["key_id"])
    _id(obj["leaf_id"])
    _decimal(obj["envelope_bytes"], positive=True)
    return obj


def signable(raw: bytes) -> bytes:
    attestation(raw)
    return SIGN_DOMAIN.encode("ascii") + b"\0" + _uint(len(raw), 4) + raw


def artifact(raw: bytes, signature: bytes) -> bytes:
    attestation(raw)
    _require(type(signature) is bytes and len(signature) == 64, "Ed25519 signature length")
    return b"SAG1\0\1\0\0" + _uint(len(raw), 4) + raw + signature


def split_artifact(raw: bytes) -> tuple[bytes, bytes]:
    _require(type(raw) is bytes and len(raw) >= 76, "SAG1 length")
    _require(raw[:8] == b"SAG1\0\1\0\0", "SAG1 magic/version")
    length = int.from_bytes(raw[8:12], "big")
    _require(len(raw) == 12 + length + 64, "SAG1 exact length/trailing bytes")
    body, signature = raw[12 : 12 + length], raw[12 + length :]
    attestation(body)
    return body, signature


@dataclass(frozen=True)
class Bootstrap:
    """Independent primitive provisioned inputs, not snapshot-selected trust."""

    formal_semantics_id: str
    origin_id: str
    storage_epoch_id: str
    storage_keys: tuple[tuple[str, bytes], ...]


def registry(bootstrap: Bootstrap) -> tuple[bytes, dict[str, tuple[str, bytes]]]:
    _id(bootstrap.formal_semantics_id)
    _id(bootstrap.origin_id)
    _label(bootstrap.storage_epoch_id)
    _require(
        type(bootstrap.storage_keys) is tuple and bool(bootstrap.storage_keys), "storage enrollment"
    )
    names, public_keys, members, resolved = [], [], [], {}
    for storage_id, key in bootstrap.storage_keys:
        _label(storage_id)
        key_bytes = encode_key(key)
        _require(decode_key(key_bytes) == key, "storage key codec")
        key_id = content_id(KEY_DOMAIN, key_bytes)
        names.append(storage_id)
        public_keys.append(key)
        members.append({"key_id": key_id, "roles": ["storage"], "storage_id": storage_id})
        resolved[storage_id] = (key_id, key)
    _require(names == sorted(set(names)), "storage ID uniqueness/order")
    _require(len(set(public_keys)) == len(public_keys), "storage key uniqueness")
    raw = canonical(
        {
            "formal_semantics_id": bootstrap.formal_semantics_id,
            "members": members,
            "origin_id": bootstrap.origin_id,
            "schema_version": "1.0.0",
            "signature_profile": "SIG-STORAGE-ED25519-v1",
            "storage_epoch_id": bootstrap.storage_epoch_id,
            "type_name": "STORAGE_EPOCH_REGISTRY",
        }
    )
    return raw, resolved


def bind_registry(bootstrap: Bootstrap, raw: bytes, key_objects: tuple[bytes, ...]) -> str:
    """Every imported Rs/Ks must equal the independent enrollment, not elect it."""
    expected, resolved = registry(bootstrap)
    _closed(load(raw), REGISTRY)
    _require(raw == expected, "independent storage registry binding")
    _require(type(key_objects) is tuple, "original immutable key inventory")
    decoded = tuple(decode_key(k) for k in key_objects)
    _require(len(set(decoded)) == len(decoded), "duplicate key object")
    _require(set(decoded) == {k for _, k in resolved.values()}, "complete enrolled key inventory")
    return content_id(REGISTRY_DOMAIN, raw)


@dataclass(frozen=True)
class Context:
    """Component input derived later from independently verified original sources.

    This value by itself proves neither source provenance nor legal production.
    required_leaves retains original full envelope lengths, never observed subsets.
    """

    common_bytes: bytes
    threshold: int
    required_leaves: tuple[tuple[str, int], ...]


def context(bootstrap: Bootstrap, value: Context) -> dict[str, Any]:
    obj = _closed(load(value.common_bytes), COMMON)
    common(obj)
    raw, keys = registry(bootstrap)
    _require(
        obj["formal_semantics_id"] == bootstrap.formal_semantics_id
        and obj["origin_id"] == bootstrap.origin_id
        and obj["storage_epoch_id"] == bootstrap.storage_epoch_id
        and obj["storage_registry_id"] == content_id(REGISTRY_DOMAIN, raw),
        "independent storage context",
    )
    _require(
        type(value.threshold) is int
        and 1 <= value.threshold <= len(keys)
        and value.threshold < 2**32,
        "original storage threshold",
    )
    _require(
        type(value.required_leaves) is tuple and bool(value.required_leaves),
        "complete required leaves",
    )
    leaves = []
    for leaf, length in value.required_leaves:
        _id(leaf)
        _require(type(length) is int and 0 < length < 2**64, "full envelope length")
        leaves.append(leaf)
    _require(len(set(leaves)) == len(leaves), "original leaf uniqueness")
    return obj


@dataclass(frozen=True)
class AuthenticatedStatement:
    original_artifact: bytes
    artifact_id: str
    body_id: str
    leaf_id: str
    storage_id: str


def authenticate(
    bootstrap: Bootstrap, backend: SodiumReference, value: Context, original: bytes
) -> AuthenticatedStatement:
    expected = context(bootstrap, value)
    _require(type(backend) is SodiumReference, "concrete pinned Ed25519 backend required")
    body, signature = split_artifact(original)
    obj = attestation(body)
    _require({k: obj[k] for k in COMMON} == expected, "original complete statement context")
    _, keys = registry(bootstrap)
    _require(obj["storage_id"] in keys, "enrolled storage ID")
    key_id, public_key = keys[obj["storage_id"]]
    _require(obj["key_id"] == key_id, "original role/key binding")
    lengths = dict(value.required_leaves)
    _require(
        obj["leaf_id"] in lengths and int(obj["envelope_bytes"]) == lengths[obj["leaf_id"]],
        "original committed leaf/full envelope length",
    )
    _require(backend.verify(public_key, signable(body), signature), "strict storage Ed25519")
    return AuthenticatedStatement(
        original,
        content_id(ARTIFACT_DOMAIN, original),
        content_id(BODY_DOMAIN, body),
        obj["leaf_id"],
        obj["storage_id"],
    )


@dataclass(frozen=True)
class Witness:
    original_certificate: bytes
    certificate_id: str
    # Complete input inventory preserves each occurrence, including unused/alternate evidence.
    original_inventory: tuple[bytes, ...]
    witness: tuple[AuthenticatedStatement, ...]
    covered_leaf_ids: tuple[str, ...]
    attester_ids: tuple[str, ...]
    threshold: int


def authenticate_witness(
    bootstrap: Bootstrap,
    backend: SodiumReference,
    value: Context,
    original_certificate: bytes,
    original_inventory: tuple[bytes, ...],
) -> Witness:
    expected = context(bootstrap, value)
    obj = _closed(load(original_certificate), CERTIFICATE)
    common(obj)
    _require(obj["type_name"] == "STORAGE_AVAILABILITY_CERTIFICATE", "AC type")
    _require({k: obj[k] for k in COMMON} == expected, "original complete AC context")
    _require(_decimal(obj["threshold"], positive=True) == value.threshold, "original AC threshold")
    references = obj["attestation_ids"]
    _require(type(references) is list, "AC references")
    for ref in references:
        _id(ref)
    _require(type(original_inventory) is tuple, "complete immutable delivery inventory")
    artifacts = {}
    for raw in original_inventory:
        _require(type(raw) is bytes, "original inventory bytes")
        identifier = content_id(ARTIFACT_DOMAIN, raw)
        if identifier in artifacts:
            _require(artifacts[identifier] == raw, "content identity conflict")
        artifacts[identifier] = raw
    # Only the actual witness is authenticated here. Invalid/unrelated deliveries
    # remain in the complete source inventory for the independent history replay.
    _require(all(ref in artifacts for ref in references), "missing original witness bytes")
    statements = tuple(
        authenticate(bootstrap, backend, value, artifacts[ref]) for ref in references
    )
    pairs = [(s.leaf_id, s.storage_id) for s in statements]
    _require(pairs == sorted(set(pairs)), "AC pair uniqueness/order")
    leaves = sorted(leaf for leaf, _ in value.required_leaves)
    _require(sorted({s.leaf_id for s in statements}) == leaves, "AC complete leaf coverage")
    for leaf in leaves:
        _require(
            sum(s.leaf_id == leaf for s in statements) >= value.threshold, "per-leaf storage quorum"
        )
    return Witness(
        original_certificate,
        content_id(CERTIFICATE_DOMAIN, original_certificate),
        original_inventory,
        statements,
        tuple(leaves),
        tuple(sorted({s.storage_id for s in statements})),
        value.threshold,
    )
