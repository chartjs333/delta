"""Durable append-only idempotency ledger keyed by intent_id with atomic reservation."""

from __future__ import annotations

import copy
import json
import os
import re
import threading
import time
from collections.abc import Collection
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deltacontroller.canonical import canonicalize_jcs, sha256_digest
from deltacontroller.errors import (
    IntentCollisionDetectedError,
    IntentIdDigestConflictError,
    UnauthorizedCallerError,
)
from deltacontroller.schema import SchemaRegistry

NONTERMINAL_STATUSES = frozenset({"ADMITTED", "QUEUED", "RUNNING"})
TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"})
KNOWN_STATUSES = NONTERMINAL_STATUSES | TERMINAL_STATUSES

_LEDGER_FIELDS = frozenset(
    {
        "intent_id",
        "intent_digest",
        "authenticated_subject_id",
        "execution_id",
        "status",
        "created_at",
        "updated_at",
        "admission_record",
        "receipt_digest",
        "terminal_receipt",
        "error",
        "retry_of_intent_id",
        "operation",
        "intent",
    }
)
# ``intent`` was added when the working-version runtime began retaining the
# complete dispatch document.  That single omission remains readable; all
# other fields were present in the original ledger shape.
_REQUIRED_LEDGER_FIELDS = _LEDGER_FIELDS - {"intent"}
_LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    "ADMITTED": frozenset({"QUEUED", "RUNNING", "COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}),
    "QUEUED": frozenset({"RUNNING", "FAILED", "TIMED_OUT", "CANCELLED"}),
    "RUNNING": TERMINAL_STATUSES,
}


def _reject_non_finite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number '{value}' is not permitted")


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Ledger field '{field}' must be a non-empty string")
    return value


def _validate_snapshot_schema(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Ledger snapshot must be a JSON object")
    unknown = set(data) - _LEDGER_FIELDS
    missing = _REQUIRED_LEDGER_FIELDS - set(data)
    if unknown or missing:
        raise ValueError(
            "Ledger snapshot does not match the exact schema "
            f"(unknown={sorted(unknown)}, missing={sorted(missing)})"
        )

    for field in (
        "intent_id",
        "intent_digest",
        "authenticated_subject_id",
        "execution_id",
        "created_at",
        "updated_at",
    ):
        _require_nonempty_string(data[field], field)
    status = _require_nonempty_string(data["status"], "status")
    if status not in KNOWN_STATUSES:
        raise ValueError(f"Unknown durable ledger status '{status}'")

    admission = data["admission_record"]
    if not isinstance(admission, dict):
        raise ValueError("Ledger field 'admission_record' must be a JSON object")
    for field in ("receipt_digest", "retry_of_intent_id", "operation"):
        value = data[field]
        if value is not None:
            _require_nonempty_string(value, field)
    for field in ("terminal_receipt", "error", "intent"):
        value = data.get(field)
        if value is not None and not isinstance(value, dict):
            raise ValueError(f"Ledger field '{field}' must be a JSON object or null")

    linked_fields = {
        "intent_id": data["intent_id"],
        "intent_digest": data["intent_digest"],
        "execution_id": data["execution_id"],
    }
    for field, expected in linked_fields.items():
        if field in admission and admission[field] != expected:
            raise ValueError(f"Ledger admission_record.{field} does not match '{field}'")
    admission_subject = admission.get("authenticated_subject")
    if admission_subject is not None:
        if not isinstance(admission_subject, dict):
            raise ValueError("Ledger admission_record.authenticated_subject must be an object")
        if (
            "subject_id" in admission_subject
            and admission_subject["subject_id"] != data["authenticated_subject_id"]
        ):
            raise ValueError(
                "Ledger admission_record authenticated subject does not match "
                "'authenticated_subject_id'"
            )

    intent = data.get("intent")
    if intent is not None:
        for field in ("intent_id", "intent_digest", "operation"):
            expected = data[field]
            if field in intent and intent[field] != expected:
                raise ValueError(f"Ledger intent.{field} does not match '{field}'")
    return data


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
    intent: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerRecord:
        data = _validate_snapshot_schema(data)
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
            # Records written before the working-version runtime did not retain
            # the full intent.  Keep those logs readable and fail closed only if
            # a later operation actually needs the missing document.
            intent=data.get("intent"),
        )


def _validate_terminal_invariants(
    record: LedgerRecord,
    *,
    expected_producer_commit: str | None = None,
) -> None:
    if record.status in NONTERMINAL_STATUSES:
        if (
            record.receipt_digest is not None
            or record.terminal_receipt is not None
            or record.error is not None
        ):
            raise ValueError(
                f"Nonterminal ledger status '{record.status}' cannot contain terminal artifacts"
            )
        return

    if record.status == "COMPLETED":
        if record.error is not None:
            raise ValueError("COMPLETED ledger snapshot cannot contain an error")
        if record.operation == "MATERIALIZE_DATASET":
            if record.receipt_digest is not None or record.terminal_receipt is not None:
                raise ValueError("MATERIALIZE_DATASET completion cannot contain a receipt")
            return
        if record.receipt_digest is None or record.terminal_receipt is None:
            raise ValueError("COMPLETED ledger snapshot requires a receipt and receipt_digest")
        try:
            computed_digest = sha256_digest(canonicalize_jcs(record.terminal_receipt))
        except (TypeError, ValueError) as exc:
            raise ValueError("COMPLETED ledger receipt is not canonical JSON") from exc
        if record.receipt_digest != computed_digest:
            raise ValueError("COMPLETED ledger receipt_digest does not match the receipt")
        try:
            SchemaRegistry().validate("receipt-lineage", record.terminal_receipt)
        except Exception as exc:
            raise ValueError("COMPLETED ledger receipt fails the frozen receipt schema") from exc

        provenance = record.terminal_receipt["provenance"]
        admission = record.admission_record
        assert admission is not None
        expected_lineage = {
            "intent_id": record.intent_id,
            "intent_digest": record.intent_digest,
            "execution_id": record.execution_id,
            "admission_id": admission.get("admission_id"),
            "admission_digest": admission.get("admission_digest"),
        }
        policy_context = admission.get("policy_context")
        if isinstance(policy_context, dict):
            expected_lineage["controller_commit"] = policy_context.get("controller_commit")
        if expected_producer_commit is not None:
            expected_lineage["producer_commit"] = expected_producer_commit
        if any(
            not isinstance(expected, str) or provenance.get(field) != expected
            for field, expected in expected_lineage.items()
        ):
            raise ValueError("COMPLETED ledger receipt provenance does not match admission lineage")

        if record.intent is not None:
            workload = record.intent.get("workload")
            if not isinstance(workload, dict):
                raise ValueError("COMPLETED ledger intent lacks workload lineage")
            expected_workload = {
                "catalog_backend_ref": workload.get("catalog_backend_ref"),
                "backend_commit": workload.get("catalog_backend_ref"),
                "model_plugin_id": workload.get("model_plugin_id"),
                "dataset_id": workload.get("dataset_id"),
                "executed_scope": workload.get("requested_scope"),
            }
            if any(
                not isinstance(expected, str)
                or (
                    provenance.get(field)
                    if field in {"catalog_backend_ref", "backend_commit"}
                    else record.terminal_receipt["workload"].get(field)
                )
                != expected
                for field, expected in expected_workload.items()
            ):
                raise ValueError("COMPLETED ledger receipt does not match intent workload lineage")
        return

    if record.status in {"FAILED", "TIMED_OUT", "CANCELLED"}:
        if record.receipt_digest is not None or record.terminal_receipt is not None:
            raise ValueError(f"{record.status} ledger snapshot cannot contain a receipt")
        if not record.error:
            raise ValueError(f"{record.status} ledger snapshot requires an error")
        return

    raise ValueError(f"Unknown durable ledger status '{record.status}'")


def _validate_history_transition(previous: LedgerRecord, current: LedgerRecord) -> None:
    immutable_fields = (
        "intent_digest",
        "authenticated_subject_id",
        "execution_id",
        "created_at",
        "admission_record",
        "retry_of_intent_id",
        "operation",
        "intent",
    )
    for field in immutable_fields:
        if getattr(previous, field) != getattr(current, field):
            raise ValueError(
                f"Immutable ledger field '{field}' changed for intent_id '{current.intent_id}'"
            )

    if previous.status in TERMINAL_STATUSES:
        if previous != current:
            raise ValueError(
                f"Terminal ledger history for intent_id '{current.intent_id}' was modified"
            )
        return
    if previous.status == current.status:
        if previous != current:
            raise ValueError(f"Ledger status '{current.status}' was rewritten without a transition")
        return
    if current.status not in _LEGAL_TRANSITIONS[previous.status]:
        raise ValueError(
            f"Illegal ledger status transition {previous.status} -> {current.status} "
            f"for intent_id '{current.intent_id}'"
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

    def __init__(
        self,
        persistence_path: Path | str | None = None,
        *,
        expected_producer_commit: str | None = None,
    ) -> None:
        if (
            expected_producer_commit is not None
            and re.fullmatch(r"[0-9a-f]{40}", expected_producer_commit) is None
        ):
            raise ValueError("expected_producer_commit must be a 40-character lowercase build SHA")
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.expected_producer_commit = expected_producer_commit
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
        # Any append/fsync failure makes the process-local view ambiguous. Keep the
        # ledger fail-closed until it is reconstructed from its durable log.
        self._poisoned_reason: str | None = None

        if self.persistence_path and self.persistence_path.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        with self._lock:
            assert self.persistence_path is not None
            with self.persistence_path.open("r", encoding="utf-8") as f:
                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(
                            line,
                            parse_constant=_reject_non_finite_json_constant,
                        )
                        rec = LedgerRecord.from_dict(_validate_snapshot_schema(data))
                        _validate_terminal_invariants(
                            rec,
                            expected_producer_commit=self.expected_producer_commit,
                        )
                    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                        raise ValueError(
                            f"Invalid idempotency ledger snapshot at line {line_number}: {exc}"
                        ) from exc
                    previous = self._by_intent_id.get(rec.intent_id)
                    if previous is None:
                        if rec.status != "ADMITTED":
                            raise ValueError(
                                "Invalid idempotency ledger snapshot at line "
                                f"{line_number}: first status for intent_id "
                                f"'{rec.intent_id}' must be ADMITTED"
                            )
                    else:
                        try:
                            _validate_history_transition(previous, rec)
                        except ValueError as exc:
                            raise ValueError(
                                f"Invalid idempotency ledger snapshot at line {line_number}: {exc}"
                            ) from exc
                    digest_owner = self._by_digest.get(rec.intent_digest)
                    if digest_owner is not None and digest_owner != rec.intent_id:
                        raise ValueError(
                            f"Ledger digest '{rec.intent_digest}' is owned by multiple intents"
                        )
                    execution_owner = self._by_execution_id.get(rec.execution_id)
                    if execution_owner is not None and execution_owner != rec.intent_id:
                        raise ValueError(
                            f"Ledger execution_id '{rec.execution_id}' is owned by multiple intents"
                        )
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
            os.fsync(f.fileno())

    def _raise_if_poisoned(self) -> None:
        if self._poisoned_reason is not None:
            raise RuntimeError(
                "Idempotency ledger is fail-closed because its durable state is uncertain: "
                f"{self._poisoned_reason}"
            )

    def _persist_or_poison(
        self, record: LedgerRecord, *, reservation_intent_id: str | None = None
    ) -> None:
        try:
            self._persist_append(record)
        except BaseException as exc:
            self._poisoned_reason = f"{type(exc).__name__}: {exc}"
            if reservation_intent_id is not None:
                reservation = self._reservations.get(reservation_intent_id)
                if reservation is not None:
                    reservation.failed = True
            self._cond.notify_all()
            raise

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
                self._raise_if_poisoned()
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
        intent: dict[str, Any] | None = None,
        retry_of_intent_id: str | None = None,
        operation: str | None = None,
        status: str = "ADMITTED",
    ) -> LedgerRecord:
        """Atomically record and commit a new admitted execution in the ledger."""
        if status != "ADMITTED":
            raise ValueError("A durable ledger history must begin with status 'ADMITTED'")
        with self._lock:
            self._raise_if_poisoned()
            reservation = self._reservations.get(intent_id)
            if reservation is None:
                raise RuntimeError(f"No active reservation for intent '{intent_id}'")
            if (
                reservation.intent_digest != intent_digest
                or reservation.caller_subject_id != caller_subject_id
            ):
                raise RuntimeError(f"Reservation identity mismatch for intent '{intent_id}'")
            if intent_id in self._by_intent_id:
                raise RuntimeError(f"Intent '{intent_id}' was committed while reserved")

            now_str = datetime.now(UTC).isoformat()
            record = LedgerRecord(
                intent_id=intent_id,
                intent_digest=intent_digest,
                authenticated_subject_id=caller_subject_id,
                execution_id=execution_id,
                status=status,
                created_at=now_str,
                updated_at=now_str,
                admission_record=copy.deepcopy(admission_record),
                retry_of_intent_id=retry_of_intent_id,
                operation=operation,
                intent=copy.deepcopy(intent),
            )
            _validate_snapshot_schema(record.to_dict())
            _validate_terminal_invariants(record)
            self._persist_or_poison(record, reservation_intent_id=intent_id)
            self._by_intent_id[intent_id] = record
            self._by_digest[intent_digest] = intent_id
            self._by_execution_id[execution_id] = intent_id
            self._reservations.pop(intent_id, None)
            self._cond.notify_all()
            return record

    def release_reservation(self, intent_id: str) -> None:
        """Release an in-flight reservation if admission preflight fails or aborts."""
        with self._lock:
            if self._poisoned_reason is not None:
                # The append may have reached storage before its barrier failed.
                # Retaining the reservation prevents a second execution identity.
                return
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
            self._raise_if_poisoned()
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
        intent: dict[str, Any] | None = None,
        retry_of_intent_id: str | None = None,
        operation: str | None = None,
    ) -> LedgerRecord:
        """Compatibility helper that acquires and commits an admission atomically."""
        state, existing = self.acquire_or_check(
            intent_id=intent_id,
            intent_digest=intent_digest,
            caller_subject_id=caller_subject_id,
        )
        if state == "COMMITTED":
            assert existing is not None
            return existing
        try:
            return self.commit_admission(
                intent_id=intent_id,
                intent_digest=intent_digest,
                caller_subject_id=caller_subject_id,
                execution_id=execution_id,
                admission_record=admission_record,
                intent=intent,
                retry_of_intent_id=retry_of_intent_id,
                operation=operation,
            )
        except BaseException:
            self.release_reservation(intent_id)
            raise

    def update_execution(
        self,
        execution_id: str,
        status: str,
        receipt_digest: str | None = None,
        terminal_receipt: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
    ) -> LedgerRecord:
        """Compatibility wrapper around the terminal-safe compare-and-set API.

        A caller racing a terminal transition receives the already-committed
        terminal record.  In particular, a late successful worker result can
        never attach a receipt after cancellation won the durable CAS.
        """
        transitioned = self.transition_execution(
            execution_id,
            expected_statuses=NONTERMINAL_STATUSES | {status},
            status=status,
            receipt_digest=receipt_digest,
            terminal_receipt=terminal_receipt,
            error=error,
        )
        if transitioned is not None:
            return transitioned
        existing = self.get_by_execution_id(execution_id)
        if existing is None:
            raise KeyError(f"Unknown execution_id '{execution_id}'")
        return existing

    def transition_execution(
        self,
        execution_id: str,
        expected_statuses: Collection[str],
        status: str,
        receipt_digest: str | None = None,
        terminal_receipt: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
    ) -> LedgerRecord | None:
        """Atomically transition an execution iff its current status is expected.

        Terminal records are immutable.  A failed comparison returns ``None``
        without appending to the durable log.  Repeating the exact same status
        with no new artifacts is an idempotent successful read.
        """
        if status not in KNOWN_STATUSES:
            raise ValueError(f"Unknown execution status '{status}'")
        expected = frozenset(expected_statuses)
        if not expected or not expected.issubset(KNOWN_STATUSES):
            raise ValueError("expected_statuses must contain only known execution statuses")

        with self._lock:
            self._raise_if_poisoned()
            intent_id = self._by_execution_id.get(execution_id)
            if not intent_id:
                raise KeyError(f"Unknown execution_id '{execution_id}'")
            record = self._by_intent_id[intent_id]

            if record.status not in expected:
                return None
            if record.status in TERMINAL_STATUSES:
                if (
                    record.status == status
                    and receipt_digest is None
                    and terminal_receipt is None
                    and error is None
                ):
                    return record
                return None

            if (
                record.status == status
                and receipt_digest is None
                and terminal_receipt is None
                and error is None
            ):
                return record

            if status not in _LEGAL_TRANSITIONS.get(record.status, frozenset()):
                raise ValueError(f"Illegal execution status transition {record.status} -> {status}")

            if status == "COMPLETED":
                next_receipt_digest = receipt_digest
                next_terminal_receipt = copy.deepcopy(terminal_receipt)
                next_error = None
            elif status in {"FAILED", "TIMED_OUT", "CANCELLED"}:
                if error is None:
                    raise ValueError(f"error is required for terminal status '{status}'")
                next_receipt_digest = None
                next_terminal_receipt = None
                next_error = copy.deepcopy(error)
            else:
                if receipt_digest is not None or terminal_receipt is not None or error is not None:
                    raise ValueError(
                        f"Nonterminal status '{status}' cannot contain terminal artifacts"
                    )
                next_receipt_digest = None
                next_terminal_receipt = None
                next_error = None

            next_record = replace(
                record,
                status=status,
                updated_at=datetime.now(UTC).isoformat(),
                receipt_digest=next_receipt_digest,
                terminal_receipt=next_terminal_receipt,
                error=next_error,
            )
            _validate_snapshot_schema(next_record.to_dict())
            _validate_terminal_invariants(
                next_record,
                expected_producer_commit=self.expected_producer_commit,
            )
            _validate_history_transition(record, next_record)
            self._persist_or_poison(next_record)
            self._by_intent_id[intent_id] = next_record
            return next_record

    def get_by_intent_id(self, intent_id: str) -> LedgerRecord | None:
        with self._lock:
            return self._by_intent_id.get(intent_id)

    def get_by_execution_id(self, execution_id: str) -> LedgerRecord | None:
        with self._lock:
            intent_id = self._by_execution_id.get(execution_id)
            if not intent_id:
                return None
            return self._by_intent_id.get(intent_id)

    def get_receipt_for_subject(
        self,
        execution_id: str,
        authenticated_subject_id: str,
    ) -> dict[str, Any] | None:
        """Return a defensive copy of a receipt only to its authenticated owner."""
        with self._lock:
            record = self.get_by_execution_id(execution_id)
            if record is None:
                return None
            if record.authenticated_subject_id != authenticated_subject_id:
                raise UnauthorizedCallerError(
                    f"Subject '{authenticated_subject_id}' cannot read execution '{execution_id}'",
                    details={
                        "execution_id": execution_id,
                        "caller_subject_id": authenticated_subject_id,
                    },
                )
            return copy.deepcopy(record.terminal_receipt)

    def list_records(self) -> tuple[LedgerRecord, ...]:
        """Return a stable defensive snapshot for startup recovery/diagnostics."""
        with self._lock:
            self._raise_if_poisoned()
            return tuple(copy.deepcopy(record) for record in self._by_intent_id.values())

    def list_nonterminal_records(self) -> tuple[LedgerRecord, ...]:
        """Return the durable executions that cannot be resumed implicitly."""
        return tuple(
            record for record in self.list_records() if record.status in NONTERMINAL_STATUSES
        )

    def active_count(self, reservation_intent_id: str | None = None) -> int:
        """Count active executions and reservations ordered before the caller.

        A gate holding ``reservation_intent_id`` excludes its own reservation but
        includes every earlier in-flight reservation. This gives concurrent new
        intents a deterministic admission order without allowing each caller to
        observe the same stale active count.
        """
        with self._lock:
            self._raise_if_poisoned()
            count = sum(1 for r in self._by_intent_id.values() if r.status in NONTERMINAL_STATUSES)
            if reservation_intent_id is None:
                return count + len(self._reservations)

            for intent_id in self._reservations:
                if intent_id == reservation_intent_id:
                    return count
                count += 1

            raise KeyError(f"Unknown reservation intent_id '{reservation_intent_id}'")
