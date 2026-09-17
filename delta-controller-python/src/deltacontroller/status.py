"""ExecutionStatus read model and builder conforming to Step 5C schema."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from deltacontroller.schema import SchemaRegistry

VALID_STATES = frozenset(
    {
        "ADMITTED",
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "TIMED_OUT",
        "CANCELLED",
        "STALE_UNAVAILABLE",
    }
)

TERMINAL_STATES = frozenset(
    {
        "COMPLETED",
        "FAILED",
        "TIMED_OUT",
        "CANCELLED",
    }
)


def build_execution_status(
    execution_id: str,
    intent_id: str,
    intent_digest: str,
    admission_id: str,
    admission_digest: str,
    state: str,
    receipt_digest: str | None = None,
    error: dict[str, Any] | None = None,
    updated_at: str | None = None,
    validate: bool = True,
    schema_registry: SchemaRegistry | None = None,
) -> dict[str, Any]:
    """Build a validated ExecutionStatus document conforming to execution-status.schema.json."""
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state '{state}'. Expected one of {sorted(VALID_STATES)}")

    now_iso = updated_at or datetime.now(UTC).isoformat()
    is_terminal = state in TERMINAL_STATES

    doc: dict[str, Any] = {
        "schema_version": "1.0.0",
        "execution_id": execution_id,
        "intent_id": intent_id,
        "intent_digest": intent_digest,
        "admission_id": admission_id,
        "admission_digest": admission_digest,
        "state": state,
        "updated_at": now_iso,
        "terminal": is_terminal,
    }

    if state == "COMPLETED":
        if not receipt_digest:
            raise ValueError("receipt_digest is required when state is COMPLETED")
        doc["receipt_digest"] = receipt_digest

    if state in {"FAILED", "TIMED_OUT", "CANCELLED"}:
        if not error:
            raise ValueError(f"error descriptor is required when state is {state}")
        doc["error"] = error

    if validate:
        registry = schema_registry or SchemaRegistry()
        registry.validate("execution-status", doc)

    return doc
