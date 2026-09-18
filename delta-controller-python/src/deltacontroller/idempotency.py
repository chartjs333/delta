"""Durable append-only idempotency ledger keyed by intent_id with atomic reservation."""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deltacontroller.errors import (
    IntentCollisionDetectedError,
    IntentIdDigestConflictError,
    UnauthorizedCallerError,
)


@dataclass
class LedgerRecord:
    """An entry in the Idempotency Ledger."""

    intent_id: str
    intent_digest: str
    authenticated_subject_id: str
    execution_id: str
    status: str  # ADMITTED, QUEUED, RUNNING, COMPLETED, FAILED, TIMED_OUT, CANCELLED
    created_at: str
    updated_at: str
    admission_record: dict[str, Any] | None = None
    receipt_digest: str | None = None
    terminal_receipt: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    retry_of_intent_id: str | None = None
    operation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerRecord:
        return cls(
            intent_id=data["intent_id"],
            intent_digest=data["intent_digest"],
            authenticated_subject_id=data["authenticated_subject_id"],
            execution_id=data["execution_id"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            admission_record=data.get("admission_record"),
            receipt_digest=data.get("receipt_digest"),
            terminal_receipt=data.get("terminal_receipt"),
            error=data.get("error"),
            retry_of_intent_id=data.get("retry_of_intent_id"),
            operation=data.get("operation"),
        )


@dataclass
class Reservation:
    """An in-flight reservation protecting against race conditions during preflight."""

    intent_id: str
    intent_digest: str
    caller_subject_id: str
    created_at: str
    committed_record: LedgerRecord | None = None
    failed: bool = False


class IdempotencyLedger:
    """Append-only idempotency ledger with collision detection,
    atomic reservation, and durable backing.
    """

    def __init__(self, persistence_path: Path | str | None = None) -> None:
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self._lock = threading.RLock()
        self._cond = threading.Condition(self._lock)
        # Primary index: intent_id -> LedgerRecord
        self._by_intent_id: dict[str, LedgerRecord] = {}
        # Reverse index: intent_digest -> intent_id (for fail-closed collision detection)
        self._by_digest: dict[str, str] = {}
        # Execution index: execution_id -> intent_id
        self._by_execution_id: dict[str, str] = {}
        # In-flight reservations: intent_id -> Reservation
        self._reservations: dict[str, Reservation] = {}

        if self.persistence_path and self.persistence_path.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        with self._lock:
            assert self.persistence_path is not None
            with self.persistence_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    rec = LedgerRecord.from_dict(data)
                    self._by_intent_id[rec.intent_id] = rec
                    self._by_digest[rec.intent_digest] = rec.intent_id
                    self._by_execution_id[rec.execution_id] = rec.intent_id

    def _persist_append(self, record: LedgerRecord) -> None:
        if not self.persistence_path:
            return
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with self.persistence_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass

    def acquire_or_check(
        self,
        intent_id: str,
        intent_digest: str,
        caller_subject_id: str,
        timeout: float = 30.0,
    ) -> tuple[str, LedgerRecord | None]:
        """Atomically check existing records or acquire reservation for preflight admission.

        Returns:
            ("COMMITTED", existing_record) if already committed and identical.
            ("RESERVED", None) if reservation was successfully acquired.

        Raises:
            UnauthorizedCallerError (ERR_UNAUTHORIZED_CALLER)
            IntentIdDigestConflictError (ERR_INTENT_ID_DIGEST_CONFLICT)
            IntentCollisionDetectedError (ERR_INTENT_COLLISION_DETECTED)
            TimeoutError if waiting for in-flight reservation times out.
        """
        deadline = time.monotonic() + timeout
        with self._lock:
            while True:
                # 1. Check committed records
                existing = self._by_intent_id.get(intent_id)
                if existing is not None:
                    if existing.authenticated_subject_id != caller_subject_id:
                        msg = (
                            f"Caller subject '{caller_subject_id}' is not authorized to "
                            f"query or replay intent '{intent_id}' belonging to "
                            f"'{existing.authenticated_subject_id}'"
                        )
                        raise UnauthorizedCallerError(
                            msg,
                            details={
                                "intent_id": intent_id,
                                "caller_subject_id": caller_subject_id,
                                "existing_subject_id": existing.authenticated_subject_id,
                            },
                        )
                    if existing.intent_digest != intent_digest:
                        msg = (
                            f"Payload digest '{intent_digest}' conflicts with previously "
                            f"admitted digest '{existing.intent_digest}' under "
                            f"intent_id '{intent_id}'"
                        )
                        raise IntentIdDigestConflictError(
                            msg,
                            details={
                                "intent_id": intent_id,
                                "declared_digest": intent_digest,
                                "recorded_digest": existing.intent_digest,
                            },
                        )
                    return ("COMMITTED", existing)

                # 2. Check collision against committed digests
                prior_intent_id = self._by_digest.get(intent_digest)
                if prior_intent_id is not None and prior_intent_id != intent_id:
                    msg = (
                        f"Digest '{intent_digest}' was already submitted under "
                        f"intent_id '{prior_intent_id}'. "
                        "Submitting the same payload under a new intent_id is rejected fail-closed."
                    )
                    raise IntentCollisionDetectedError(
                        msg,
                        details={
                            "intent_id": intent_id,
                            "prior_intent_id": prior_intent_id,
                            "intent_digest": intent_digest,
                        },
                    )

                # 3. Check in-flight reservations
                res = self._reservations.get(intent_id)
                if res is not None:
                    if res.caller_subject_id != caller_subject_id:
                        msg = (
                            f"Caller subject '{caller_subject_id}' is not authorized to access "
                            f"in-flight intent '{intent_id}' belonging to '{res.caller_subject_id}'"
                        )
                        raise UnauthorizedCallerError(
                            msg,
                            details={
                                "intent_id": intent_id,
                                "caller_subject_id": caller_subject_id,
                                "existing_subject_id": res.caller_subject_id,
                            },
                        )
                    if res.intent_digest != intent_digest:
                        msg = (
                            f"Payload digest '{intent_digest}' conflicts with in-flight digest "
                            f"'{res.intent_digest}' under intent_id '{intent_id}'"
                        )
                        raise IntentIdDigestConflictError(
                            msg,
                            details={
                                "intent_id": intent_id,
                                "declared_digest": intent_digest,
                                "recorded_digest": res.intent_digest,
                            },
                        )
                    # Identical in-flight submission: wait for resolution
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError(f"Timed out waiting for in-flight intent '{intent_id}'")
                    self._cond.wait(timeout=min(remaining, 0.5))
                    continue

                # 4. Check collision against other in-flight reservations
                for r in self._reservations.values():
                    if r.intent_digest == intent_digest and r.intent_id != intent_id:
                        msg = (
                            f"Digest '{intent_digest}' is currently reserved under "
                            f"intent_id '{r.intent_id}'. Submitting the same payload "
                            "under a new intent_id is rejected fail-closed."
                        )
                        raise IntentCollisionDetectedError(
                            msg,
                            details={
                                "intent_id": intent_id,
                                "prior_intent_id": r.intent_id,
                                "intent_digest": intent_digest,
                            },
                        )

                # 5. Acquire reservation
                now_str = datetime.now(UTC).isoformat()
                self._reservations[intent_id] = Reservation(
                    intent_id=intent_id,
                    intent_digest=intent_digest,
                    caller_subject_id=caller_subject_id,
                    created_at=now_str,
                )
                return ("RESERVED", None)

    def commit_admission(
        self,
        intent_id: str,
        intent_digest: str,
        caller_subject_id: str,
        execution_id: str,
        admission_record: dict[str, Any],
        retry_of_intent_id: str | None = None,
        operation: str | None = None,
    ) -> LedgerRecord:
        """Atomically record and commit a new admitted execution in the ledger."""
        with self._lock:
            now_str = datetime.now(UTC).isoformat()
            record = LedgerRecord(
                intent_id=intent_id,
                intent_digest=intent_digest,
                authenticated_subject_id=caller_subject_id,
                execution_id=execution_id,
                status="ADMITTED",
                created_at=now_str,
                updated_at=now_str,
                admission_record=admission_record,
                retry_of_intent_id=retry_of_intent_id,
                operation=operation,
            )
            self._by_intent_id[intent_id] = record
            self._by_digest[intent_digest] = intent_id
            self._by_execution_id[execution_id] = intent_id
            self._reservations.pop(intent_id, None)
            self._persist_append(record)
            self._cond.notify_all()
            return record

    def release_reservation(self, intent_id: str) -> None:
        """Release an in-flight reservation if admission preflight fails or aborts."""
        with self._lock:
            res = self._reservations.pop(intent_id, None)
            if res is not None:
                res.failed = True
                self._cond.notify_all()

    def check_intent(
        self,
        intent_id: str,
        intent_digest: str,
        caller_subject_id: str,
    ) -> LedgerRecord | None:
        """Check for existing intent, enforcing conflict, authorization, and collision rules.

        Returns existing LedgerRecord if this is an identical re-submission.
        Returns None if intent_id is new and safe to admit.
        """
        with self._lock:
            existing = self._by_intent_id.get(intent_id)
            if existing is not None:
                if existing.authenticated_subject_id != caller_subject_id:
                    msg = (
                        f"Caller subject '{caller_subject_id}' is not authorized to "
                        f"query or replay intent '{intent_id}' belonging to "
                        f"'{existing.authenticated_subject_id}'"
                    )
                    raise UnauthorizedCallerError(
                        msg,
                        details={
                            "intent_id": intent_id,
                            "caller_subject_id": caller_subject_id,
                            "existing_subject_id": existing.authenticated_subject_id,
                        },
                    )
                if existing.intent_digest != intent_digest:
                    msg = (
                        f"Payload digest '{intent_digest}' conflicts with previously "
                        f"admitted digest '{existing.intent_digest}' under "
                        f"intent_id '{intent_id}'"
                    )
                    raise IntentIdDigestConflictError(
                        msg,
                        details={
                            "intent_id": intent_id,
                            "declared_digest": intent_digest,
                            "recorded_digest": existing.intent_digest,
                        },
                    )
                return existing

            prior_intent_id = self._by_digest.get(intent_digest)
            if prior_intent_id is not None and prior_intent_id != intent_id:
                msg = (
                    f"Digest '{intent_digest}' was already submitted under "
                    f"intent_id '{prior_intent_id}'. "
                    "Submitting the same payload under a new intent_id is rejected fail-closed."
                )
                raise IntentCollisionDetectedError(
                    msg,
                    details={
                        "intent_id": intent_id,
                        "prior_intent_id": prior_intent_id,
                        "intent_digest": intent_digest,
                    },
                )

            return None

    def record_admission(
        self,
        intent_id: str,
        intent_digest: str,
        caller_subject_id: str,
        execution_id: str,
        admission_record: dict[str, Any],
        retry_of_intent_id: str | None = None,
        operation: str | None = None,
    ) -> LedgerRecord:
        """Atomically record a new admitted execution in the ledger."""
        return self.commit_admission(
            intent_id=intent_id,
            intent_digest=intent_digest,
            caller_subject_id=caller_subject_id,
            execution_id=execution_id,
            admission_record=admission_record,
            retry_of_intent_id=retry_of_intent_id,
            operation=operation,
        )

    def update_execution(
        self,
        execution_id: str,
        status: str,
        receipt_digest: str | None = None,
        terminal_receipt: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
    ) -> LedgerRecord:
        """Update status and results for an active execution."""
        with self._lock:
            intent_id = self._by_execution_id.get(execution_id)
            if not intent_id:
                raise KeyError(f"Unknown execution_id '{execution_id}'")
            record = self._by_intent_id[intent_id]
            record.status = status
            record.updated_at = datetime.now(UTC).isoformat()
            if receipt_digest is not None:
                record.receipt_digest = receipt_digest
            if terminal_receipt is not None:
                record.terminal_receipt = terminal_receipt
            if error is not None:
                record.error = error
            self._persist_append(record)
            return record

    def get_by_intent_id(self, intent_id: str) -> LedgerRecord | None:
        with self._lock:
            return self._by_intent_id.get(intent_id)

    def get_by_execution_id(self, execution_id: str) -> LedgerRecord | None:
        with self._lock:
            intent_id = self._by_execution_id.get(execution_id)
            if not intent_id:
                return None
            return self._by_intent_id.get(intent_id)

    def active_count(self) -> int:
        """Count executions currently in ADMITTED, QUEUED, or RUNNING state."""
        with self._lock:
            return sum(
                1
                for r in self._by_intent_id.values()
                if r.status in {"ADMITTED", "QUEUED", "RUNNING"}
            )
