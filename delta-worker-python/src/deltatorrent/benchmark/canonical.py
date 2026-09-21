"""Strict canonical bytes and domain-separated Feature 010 signing messages."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any, Final

from deltatorrent.protocol.canonical import canonical_json_bytes


class ContractEncodingError(ValueError):
    """Stable fail-closed error for benchmark contract encodings."""


_SIGNING_CONTEXTS: Final[dict[str, bytes]] = {
    "BENCHMARK_DEFINITION_VOTE": b"deltareduce.feature010.definition-vote.v1",
    "BENCHMARK_RESULT_VOTE": b"deltareduce.feature010.result-vote.v1",
}


def _reject_constant(value: str) -> None:
    raise ContractEncodingError(f"NON_FINITE_NUMBER:{value}")


def _unique_object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractEncodingError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def load_json_bytes(value: bytes, *, require_canonical: bool = True) -> dict[str, Any]:
    """Load one strict JSON object, rejecting duplicate keys and alternate bytes."""

    if value.startswith(b"\xef\xbb\xbf"):
        raise ContractEncodingError("JSON_BOM_FORBIDDEN")
    try:
        text = value.decode("utf-8", errors="strict")
        document = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractEncodingError("JSON_INVALID") from exc
    if not isinstance(document, dict):
        raise ContractEncodingError("JSON_ROOT_NOT_OBJECT")
    try:
        canonical = canonical_json_bytes(document)
    except (TypeError, UnicodeEncodeError) as exc:
        raise ContractEncodingError("JSON_NOT_CANONICALIZABLE") from exc
    if require_canonical and canonical != value:
        raise ContractEncodingError("JSON_BYTES_NOT_CANONICAL")
    return document


def canonical_bytes(document: object) -> bytes:
    """Return repository canonical JSON and normalize its error surface."""

    try:
        return canonical_json_bytes(document)
    except (TypeError, UnicodeEncodeError) as exc:
        raise ContractEncodingError("JSON_NOT_CANONICALIZABLE") from exc


def content_id(value: bytes) -> str:
    """Return the raw-byte CAS identity used by FilesystemArtifactStore."""

    return "sha256:" + hashlib.sha256(value).hexdigest()


def document_id(document: object) -> str:
    return content_id(canonical_bytes(document))


def signing_message(purpose: str, body_id: str) -> bytes:
    """Build a non-caller-selectable signature message for an exact body ID."""

    try:
        context = _SIGNING_CONTEXTS[purpose]
    except KeyError as exc:
        raise ContractEncodingError("SIGNING_PURPOSE_INVALID") from exc
    if (
        not isinstance(body_id, str)
        or len(body_id) != 71
        or not body_id.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in body_id[7:])
    ):
        raise ContractEncodingError("SIGNING_BODY_ID_INVALID")
    return context + b"\x00" + body_id.encode("ascii")


def signing_message_id(purpose: str, body_id: str) -> str:
    return content_id(signing_message(purpose, body_id))


def signing_payload(purpose: str, payload: object) -> bytes:
    """Domain-separate a complete canonical vote payload."""

    try:
        context = _SIGNING_CONTEXTS[purpose]
    except KeyError as exc:
        raise ContractEncodingError("SIGNING_PURPOSE_INVALID") from exc
    return context + b"\x00" + canonical_bytes(payload)
