"""Worker dispatch port and adapters for passing AuthorizedExecution bundles to Zone 3."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from deltacontroller.errors import WorkerDispatchFailedError
from deltacontroller.schema import SchemaRegistry


class WorkerDispatchPort(Protocol):
    """Protocol for dispatching an AuthorizedExecution bundle to a worker runtime."""

    def dispatch(
        self, bundle: dict[str, Any], current_time: datetime | None = None
    ) -> dict[str, Any]:
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

    def dispatch(
        self, bundle: dict[str, Any], current_time: datetime | None = None
    ) -> dict[str, Any]:
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
    """Integrated worker dispatch port directly bridging Zone 2 Controller to Zone 3 Worker.

    Enforces AuthorizedExecution preflight (Ed25519 signature verification, dispatch deadline,
    intent digest parity, execution ID authority) and executes via closed enum worker dispatch.
    """

    def __init__(
        self,
        schema_registry: SchemaRegistry | None = None,
        preflight: Any | None = None,
        dispatcher: Any | None = None,
        cancellation_token: Any | None = None,
    ) -> None:
        from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher
        from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

        self.schema_registry = schema_registry or SchemaRegistry()
        self.preflight = preflight or AuthorizedExecutionPreflight()
        self.dispatcher = dispatcher or ClosedEnumWorkerDispatcher()
        self.cancellation_token = cancellation_token

    def dispatch(
        self, bundle: dict[str, Any], token: Any | None = None, current_time: Any | None = None
    ) -> dict[str, Any]:
        from deltatorrent.live_execution.errors import (
            WorkerCancelledError,
            WorkerPreflightError,
            WorkerTimeoutError,
        )

        from deltacontroller.canonical import canonicalize_jcs, sha256_digest

        # 1. Schema check
        try:
            self.schema_registry.validate("authorized-execution", bundle)
        except Exception as exc:
            raise WorkerDispatchFailedError(
                f"Bundle failed authorized-execution schema validation: {exc}"
            ) from exc

        # 2. Worker boundary preflight validation
        try:
            ctx = self.preflight.validate(bundle, current_time=current_time)
        except WorkerPreflightError as exc:
            err_code = (
                exc.code
                if exc.code
                in {
                    "ERR_ADMISSION_SIGNATURE_INVALID",
                    "ERR_ADMISSION_EXPIRED",
                    "ERR_OPERATION_SCOPE_UNSUPPORTED",
                    "ERR_SCHEMA_VALIDATION_FAILED",
                    "ERR_INTENT_DIGEST_MISMATCH",
                }
                else "ERR_WORKER_DISPATCH_FAILED"
            )
            cat = "AUTHZ" if "SIGNATURE" in err_code else "DISPATCH"
            return {
                "dispatched": False,
                "execution_id": bundle["admission"]["execution_id"],
                "intent_id": bundle["intent"]["intent_id"],
                "status": "FAILED",
                "error": {
                    "schema_version": "1.0.0",
                    "error_code": err_code,
                    "category": cat,
                    "retryable": False,
                    "message": str(exc.message)[:512],
                },
                "receipt": None,
            }

        # 3. Closed enum execution
        effective_token = token or self.cancellation_token
        try:
            worker_result = self.dispatcher.dispatch(ctx, cancellation_token=effective_token)
            receipt = worker_result.get("receipt")
            receipt_digest = None
            if receipt:
                receipt_digest = sha256_digest(canonicalize_jcs(receipt))
            elif worker_result.get("status") == "COMPLETED":
                mat_info = worker_result.get("materialize_info", {})
                receipt_digest = sha256_digest(canonicalize_jcs(mat_info))

            return {
                "dispatched": True,
                "execution_id": ctx.execution_id,
                "intent_id": ctx.intent_id,
                "status": worker_result.get("status", "COMPLETED"),
                "receipt": receipt,
                "receipt_digest": receipt_digest,
                "metrics": worker_result.get("metrics"),
                "materialize_info": worker_result.get("materialize_info"),
            }
        except WorkerTimeoutError as exc:
            return {
                "dispatched": True,
                "execution_id": ctx.execution_id,
                "intent_id": ctx.intent_id,
                "status": "TIMED_OUT",
                "error": {
                    "schema_version": "1.0.0",
                    "error_code": "ERR_TIMEOUT",
                    "category": "RESOURCE",
                    "retryable": True,
                    "message": str(exc)[:512],
                },
                "receipt": None,
            }
        except WorkerCancelledError as exc:
            return {
                "dispatched": True,
                "execution_id": ctx.execution_id,
                "intent_id": ctx.intent_id,
                "status": "CANCELLED",
                "error": {
                    "schema_version": "1.0.0",
                    "error_code": "ERR_CANCELLED",
                    "category": "WORKER",
                    "retryable": False,
                    "message": str(exc)[:512],
                },
                "receipt": None,
            }
        except Exception as exc:
            return {
                "dispatched": True,
                "execution_id": ctx.execution_id,
                "intent_id": ctx.intent_id,
                "status": "FAILED",
                "error": {
                    "schema_version": "1.0.0",
                    "error_code": "ERR_WORKER_DISPATCH_FAILED",
                    "category": "WORKER",
                    "retryable": False,
                    "message": str(exc)[:512],
                },
                "receipt": None,
            }
