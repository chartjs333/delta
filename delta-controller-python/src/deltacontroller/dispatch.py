"""Worker dispatch port and adapters for passing AuthorizedExecution bundles to Zone 3."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, ClassVar, Protocol

from deltacontroller.canonical import canonicalize_jcs, sha256_digest
from deltacontroller.errors import WorkerDispatchFailedError
from deltacontroller.schema import SchemaRegistry


class WorkerDispatchPort(Protocol):
    """Protocol for dispatching an AuthorizedExecution bundle to a worker runtime."""

    def dispatch(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Dispatch the bundle and return the initial execution status or worker acknowledgment."""
        ...


class MockWorkerDispatchPort:
    """Mock dispatch port recording dispatched bundles for testing and offline development."""

    def __init__(
        self, schema_registry: SchemaRegistry | None = None, auto_complete: bool = False
    ) -> None:
        self.schema_registry = schema_registry or SchemaRegistry()
        self.dispatched_bundles: list[dict[str, Any]] = []
        self.auto_complete = auto_complete

    def dispatch(self, bundle: dict[str, Any]) -> dict[str, Any]:
        # Preflight schema check of the bundle
        try:
            self.schema_registry.validate("authorized-execution", bundle)
        except Exception as exc:
            raise WorkerDispatchFailedError(
                f"Bundle failed authorized-execution schema validation: {exc}"
            ) from exc

        self.dispatched_bundles.append(bundle)
        execution_id = bundle["admission"]["execution_id"]
        intent_id = bundle["intent"]["intent_id"]

        return {
            "dispatched": True,
            "execution_id": execution_id,
            "intent_id": intent_id,
            "status": "RUNNING" if not self.auto_complete else "COMPLETED",
        }


class IntegratedWorkerDispatchPort:
    """Bridge a validated Controller bundle to the local closed-enum Worker adapter.

    The clock is injected so Controller admission time and Worker freshness checks use
    one explicit integration boundary.  The public dispatch protocol remains the
    single-argument ``dispatch(bundle)`` contract used by every other port.
    """

    _PREFLIGHT_ERROR_METADATA: ClassVar[dict[str, tuple[str, bool]]] = {
        "ERR_SCHEMA_VALIDATION_FAILED": ("SCHEMA", False),
        "ERR_INTENT_DIGEST_MISMATCH": ("DIGEST", False),
        "ERR_ADMISSION_DIGEST_MISMATCH": ("DIGEST", False),
        "ERR_ADMISSION_SIGNATURE_INVALID": ("WORKER", False),
        "ERR_ADMISSION_EXPIRED": ("AUTHZ", False),
        "ERR_OPERATION_SCOPE_UNSUPPORTED": ("CATALOG", False),
        "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH": ("LINEAGE", False),
        "ERR_STAGE_C_FORBIDDEN": ("CONSENSUS_BOUNDARY", False),
    }

    def __init__(
        self,
        *,
        preflight: Any,
        schema_registry: SchemaRegistry | None = None,
        dispatcher: Any | None = None,
        cancellation_token: Any | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher

        self.schema_registry = schema_registry or SchemaRegistry()
        self.preflight = preflight
        self.dispatcher = dispatcher or ClosedEnumWorkerDispatcher()
        self.cancellation_token = cancellation_token
        self.clock = clock or (lambda: datetime.now(UTC))
        self.dispatch_count = 0

    @staticmethod
    def _error_result(
        bundle: dict[str, Any],
        *,
        error_code: str,
        category: str,
        retryable: bool,
        message: str,
        dispatched: bool,
        status: str = "FAILED",
    ) -> dict[str, Any]:
        return {
            "dispatched": dispatched,
            "execution_id": bundle["admission"]["execution_id"],
            "intent_id": bundle["intent"]["intent_id"],
            "status": status,
            "error": {
                "schema_version": "1.0.0",
                "error_code": error_code,
                "category": category,
                "retryable": retryable,
                "message": message[:512],
            },
            "receipt": None,
        }

    def dispatch(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Preflight and execute one AuthorizedExecution bundle fail closed."""
        from deltatorrent.live_execution.errors import (
            WorkerAdapterError,
            WorkerCancelledError,
            WorkerPreflightError,
            WorkerTimeoutError,
        )

        try:
            self.schema_registry.validate("authorized-execution", bundle)
        except Exception as exc:
            raise WorkerDispatchFailedError(
                f"Bundle failed authorized-execution schema validation: {exc}"
            ) from exc

        try:
            context = self.preflight.validate(bundle, current_time=self.clock())
        except WorkerPreflightError as exc:
            error_code = (
                exc.code
                if exc.code in self._PREFLIGHT_ERROR_METADATA
                else "ERR_WORKER_DISPATCH_FAILED"
            )
            category, retryable = self._PREFLIGHT_ERROR_METADATA.get(error_code, ("DISPATCH", True))
            return self._error_result(
                bundle,
                error_code=error_code,
                category=category,
                retryable=retryable,
                message=exc.message,
                dispatched=False,
            )

        try:
            self.dispatch_count += 1
            worker_result = self.dispatcher.dispatch(
                context,
                cancellation_token=self.cancellation_token,
            )
            if worker_result.get("execution_id") != context.execution_id:
                return self._error_result(
                    bundle,
                    error_code="ERR_RECEIPT_LINEAGE_MISMATCH",
                    category="LINEAGE",
                    retryable=False,
                    message="Worker result execution_id does not match AuthorizedExecution",
                    dispatched=True,
                )
            if worker_result.get("operation") != context.operation:
                return self._error_result(
                    bundle,
                    error_code="ERR_RECEIPT_LINEAGE_MISMATCH",
                    category="LINEAGE",
                    retryable=False,
                    message="Worker result operation does not match AuthorizedExecution",
                    dispatched=True,
                )
            worker_status = worker_result.get("status")
            if worker_status != "COMPLETED":
                return self._error_result(
                    bundle,
                    error_code="ERR_WORKER_DISPATCH_FAILED",
                    category="DISPATCH",
                    retryable=True,
                    message="Worker returned a missing or unsupported status",
                    dispatched=True,
                )
            receipt = worker_result.get("receipt")
            if receipt is not None:
                self.schema_registry.validate("receipt-lineage", receipt)
                provenance = receipt.get("provenance", {})
                expected_lineage = {
                    "intent_id": context.intent_id,
                    "intent_digest": context.intent_digest,
                    "admission_id": context.admission_id,
                    "admission_digest": context.admission_digest,
                    "execution_id": context.execution_id,
                }
                if any(provenance.get(key) != value for key, value in expected_lineage.items()):
                    return self._error_result(
                        bundle,
                        error_code="ERR_RECEIPT_LINEAGE_MISMATCH",
                        category="LINEAGE",
                        retryable=False,
                        message="Worker receipt provenance does not match AuthorizedExecution",
                        dispatched=True,
                    )

            receipt_digest = None
            if receipt is not None:
                receipt_digest = sha256_digest(canonicalize_jcs(receipt))

            return {
                "dispatched": True,
                "execution_id": context.execution_id,
                "intent_id": context.intent_id,
                "operation": context.operation,
                "status": worker_status,
                "receipt": receipt,
                "receipt_digest": receipt_digest,
                "metrics": worker_result.get("metrics"),
                "materialize_info": worker_result.get("materialize_info"),
            }
        except WorkerTimeoutError as exc:
            return self._error_result(
                bundle,
                error_code=exc.code,
                category=exc.category,
                retryable=exc.retryable,
                message=exc.message,
                dispatched=True,
                status="TIMED_OUT",
            )
        except WorkerCancelledError as exc:
            return self._error_result(
                bundle,
                error_code=exc.code,
                category=exc.category,
                retryable=True,
                message=exc.message,
                dispatched=True,
                status="CANCELLED",
            )
        except WorkerAdapterError as exc:
            known_error_code = (
                exc.code
                if exc.code in self._PREFLIGHT_ERROR_METADATA
                else "ERR_WORKER_DISPATCH_FAILED"
            )
            category, retryable = self._PREFLIGHT_ERROR_METADATA.get(
                known_error_code, ("DISPATCH", True)
            )
            return self._error_result(
                bundle,
                error_code=known_error_code,
                category=category,
                retryable=retryable,
                message=exc.message,
                dispatched=True,
            )
        except Exception as exc:
            return self._error_result(
                bundle,
                error_code="ERR_WORKER_DISPATCH_FAILED",
                category="DISPATCH",
                retryable=True,
                message=f"Worker dispatch failed ({type(exc).__name__})",
                dispatched=True,
            )
