"""Structured audit logging and sensitive credential/secret redaction."""

from __future__ import annotations

import copy
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "private_key",
        "access_token",
        "authorization",
        "credentials",
        "api_key",
        "private_bytes",
    }
)

REDACTED_PLACEHOLDER = "[REDACTED]"


def redact_sensitive_data(obj: Any) -> Any:
    """Recursively traverse a dictionary or list and redact known sensitive keys."""
    if isinstance(obj, dict):
        redacted = {}
        for key, value in obj.items():
            if str(key).lower() in SENSITIVE_KEYS:
                redacted[key] = REDACTED_PLACEHOLDER
            else:
                redacted[key] = redact_sensitive_data(value)
        return redacted
    if isinstance(obj, list):
        return [redact_sensitive_data(item) for item in obj]
    return obj


class AuditLogger:
    """Structured, immutable audit logger with automatic secret redaction."""

    def __init__(
        self, log_path: Path | str | None = None, logger: logging.Logger | None = None
    ) -> None:
        self.log_path = Path(log_path) if log_path else None
        self.logger = logger or logging.getLogger("deltacontroller.audit")

    def log_event(
        self,
        event_type: str,
        subject_id: str | None,
        details: dict[str, Any],
        intent_id: str | None = None,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        """Record an audit event, redacting sensitive fields."""
        safe_details = redact_sensitive_data(copy.deepcopy(details))
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "subject_id": subject_id or "ANONYMOUS",
            "intent_id": intent_id,
            "execution_id": execution_id,
            "details": safe_details,
        }

        # Log via standard logging
        self.logger.info(
            "AUDIT [%s] subject=%s intent=%s exec=%s",
            event_type,
            subject_id,
            intent_id,
            execution_id,
        )

        # Append to audit file if configured
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return event
