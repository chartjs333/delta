"""Bounded ingress parsing and preflight checks."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from deltacontroller.canonical import compute_intent_digest
from deltacontroller.errors import (
    IntentDigestMismatchError,
    IntentExpiredError,
    SchemaValidationError,
)
from deltacontroller.schema import SchemaRegistry

MAX_INGRESS_BYTES = 1024 * 1024  # 1 MiB max raw payload
MAX_JSON_DEPTH = 32


def _check_depth(val: Any, current_depth: int = 1) -> None:
    if current_depth > MAX_JSON_DEPTH:
        raise SchemaValidationError(f"Payload exceeds maximum nested depth of {MAX_JSON_DEPTH}")
    if isinstance(val, dict):
        for item in val.values():
            _check_depth(item, current_depth + 1)
    elif isinstance(val, list):
        for item in val:
            _check_depth(item, current_depth + 1)


class IngressParser:
    """Parses raw request bytes with strict resource bounds, verifies schema and digest."""

    def __init__(
        self,
        schema_registry: SchemaRegistry | None = None,
        max_bytes: int = MAX_INGRESS_BYTES,
    ) -> None:
        self.schema_registry = schema_registry or SchemaRegistry()
        self.max_bytes = max_bytes

    def parse_intent(
        self,
        raw_input: bytes | str | dict[str, Any],
        current_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Bounded parse, schema validate, JCS recompute, and TTL check for ExecutionIntent."""
        if isinstance(raw_input, (bytes, bytearray)):
            if len(raw_input) > self.max_bytes:
                raise SchemaValidationError(
                    f"Payload size {len(raw_input)} bytes exceeds maximum {self.max_bytes}"
                )
            try:
                text = raw_input.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SchemaValidationError(f"Payload is not valid UTF-8: {exc}") from exc
            try:
                data = json.loads(text)
            except Exception as exc:
                raise SchemaValidationError(f"Malformed JSON payload: {exc}") from exc
        elif isinstance(raw_input, str):
            encoded = raw_input.encode("utf-8")
            if len(encoded) > self.max_bytes:
                raise SchemaValidationError(
                    f"Payload size {len(encoded)} bytes exceeds maximum {self.max_bytes}"
                )
            try:
                data = json.loads(raw_input)
            except Exception as exc:
                raise SchemaValidationError(f"Malformed JSON payload: {exc}") from exc
        elif isinstance(raw_input, dict):
            data = raw_input
        else:
            raise SchemaValidationError(f"Unsupported input type: {type(raw_input)}")

        if not isinstance(data, dict):
            raise SchemaValidationError("Top-level JSON payload must be an object")

        # 1. Depth check
        _check_depth(data)

        # 2. Schema validation
        self.schema_registry.validate("execution-intent", data)

        # 3. JCS digest recomputation and verification
        recomputed = compute_intent_digest(data)
        declared = data.get("intent_digest")
        if recomputed != declared:
            msg = (
                f"Declared digest '{declared}' does not match "
                f"recomputed RFC 8785 digest '{recomputed}'"
            )
            raise IntentDigestMismatchError(
                msg,
                details={"declared_digest": declared, "recomputed_digest": recomputed},
            )

        # 4. TTL validation (expires_at > now)
        expires_at_str = data.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            except Exception as exc:
                raise SchemaValidationError(
                    f"Invalid ISO-8601 date-time format for expires_at: {expires_at_str}"
                ) from exc
            now = current_time or datetime.now(UTC)
            if expires_at <= now:
                raise IntentExpiredError(
                    f"Intent expired at {expires_at_str} (current time: {now.isoformat()})",
                    details={"expires_at": expires_at_str, "now": now.isoformat()},
                )

        return data
