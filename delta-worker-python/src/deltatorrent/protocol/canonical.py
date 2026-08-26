"""Canonical JSON for shared contracts; language memory layout is never serialized."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

type JsonScalar = str | int | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


def _normalize(value: object, location: str = "$") -> JsonValue:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise TypeError(f"FLOAT_NOT_CANONICAL:{location}")
    if isinstance(value, Mapping):
        normalized: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"NON_STRING_KEY:{location}")
            normalized[key] = _normalize(item, f"{location}.{key}")
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, memoryview)):
        return [_normalize(item, f"{location}[{index}]") for index, item in enumerate(value)]
    raise TypeError(f"UNSAFE_SERIALIZATION_TYPE:{location}:{type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_content_id(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"
