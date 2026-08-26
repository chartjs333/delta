"""Stable domain errors shared by CLI and artifact boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class ErrorCode(StrEnum):
    ARTIFACT_HASH_MISMATCH = "ARTIFACT_HASH_MISMATCH"
    ARTIFACT_IMMUTABLE_CONFLICT = "ARTIFACT_IMMUTABLE_CONFLICT"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    FORMAL_SEMANTICS_MISMATCH = "FORMAL_SEMANTICS_MISMATCH"
    INVALID_CONTENT_ID = "INVALID_CONTENT_ID"
    INVALID_MANIFEST = "INVALID_MANIFEST"
    INVALID_SCHEMA_ID = "INVALID_SCHEMA_ID"
    INVALID_ARTIFACT_LOCATOR = "INVALID_ARTIFACT_LOCATOR"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    UNKNOWN_MEDIA_TYPE = "UNKNOWN_MEDIA_TYPE"
    UNSAFE_SERIALIZATION = "UNSAFE_SERIALIZATION"


class DeltaError(RuntimeError):
    """Error with a stable code and non-secret structured details."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = MappingProxyType(dict(details or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "details": dict(self.details),
            "message": self.message,
        }
