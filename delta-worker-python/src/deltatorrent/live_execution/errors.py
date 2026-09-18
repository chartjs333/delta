"""Typed errors for Step 5C Worker Adapter."""

from __future__ import annotations

from typing import Any


class WorkerAdapterError(Exception):
    """Base exception for all Step 5C worker adapter operations."""

    def __init__(
        self,
        code: str,
        message: str,
        category: str = "WORKER",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.category = category
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category,
            "retryable": self.retryable,
            "details": self.details,
        }


class WorkerPreflightError(WorkerAdapterError):
    """Raised when AuthorizedExecution bundle fails preflight checks."""


class WorkerDispatchError(WorkerAdapterError):
    """Raised when operation dispatch or execution fails."""


class WorkerTimeoutError(WorkerAdapterError):
    """Raised when execution exceeds allocated timeout."""

    def __init__(
        self, message: str = "Execution timed out", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__("ERR_TIMEOUT", message, category="WORKER", retryable=True, details=details)


class WorkerCancelledError(WorkerAdapterError):
    """Raised when execution is cancelled."""

    def __init__(
        self, message: str = "Execution was cancelled", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            "ERR_CANCELLED", message, category="WORKER", retryable=False, details=details
        )
