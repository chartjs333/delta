"""T018-T020: Closed enum worker dispatch and bounded execution."""

from __future__ import annotations

import concurrent.futures
import re
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from deltatorrent.live_execution.errors import (
    WorkerCancelledError,
    WorkerDispatchError,
    WorkerTimeoutError,
)
from deltatorrent.live_execution.preflight import PreflightContext
from deltatorrent.model_plugins.registry import get_default_registry
from deltatorrent.model_plugins.runner import ModelPluginRunner


class CancellationToken:
    """Thread-safe cancellation token for worker operations."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()


class ClosedEnumWorkerDispatcher:
    """Dispatches preflighted operations strictly via a closed enum table."""

    APPROVED_OPERATIONS = frozenset(
        {
            "TRAIN_TICKET",
            "EVALUATE_CHECKPOINT",
            "MATERIALIZE_DATASET",
        }
    )

    def __init__(
        self,
        *,
        producer_commit: str | None = None,
        cache_root: Path | str | None = None,
    ) -> None:
        if producer_commit is not None and re.fullmatch(r"[0-9a-f]{40}", producer_commit) is None:
            raise ValueError("producer_commit must be a 40-character lowercase build SHA")
        self.producer_commit = producer_commit
        self.cache_root = (
            Path(cache_root) if cache_root is not None else Path(".cache/deltatorrent")
        )

    def dispatch(
        self,
        context: PreflightContext,
        cancellation_token: CancellationToken | None = None,
        runner_override: ModelPluginRunner | None = None,
        producer_commit: str | None = None,
    ) -> dict[str, Any]:
        """Execute the preflighted workload within bounded timeout and cancellation."""
        effective_producer_commit = producer_commit or self.producer_commit
        if (
            effective_producer_commit is None
            or re.fullmatch(r"[0-9a-f]{40}", effective_producer_commit) is None
        ):
            raise WorkerDispatchError(
                "ERR_WORKER_DISPATCH_FAILED",
                "An explicit 40-character producer_commit is required",
            )
        if cancellation_token and cancellation_token.is_cancelled:
            raise WorkerCancelledError("Operation was cancelled before start")

        operation = context.operation
        if operation not in self.APPROVED_OPERATIONS:
            raise WorkerDispatchError(
                "ERR_OPERATION_SCOPE_UNSUPPORTED",
                f"Operation '{operation}' is not in approved closed enum table",
                details={"operation": operation, "approved": sorted(self.APPROVED_OPERATIONS)},
            )

        timeout = context.timeout_seconds

        def _run_op() -> dict[str, Any]:
            if cancellation_token and cancellation_token.is_cancelled:
                raise WorkerCancelledError("Operation cancelled during setup")

            # Resolve runner
            runner = runner_override or ModelPluginRunner(
                plugin_id=context.model_plugin_id,
                dataset_id=context.dataset_id,
                execution_scope=context.requested_scope,
            )

            if operation == "TRAIN_TICKET":
                return self._execute_train_ticket(
                    runner, context, cancellation_token, effective_producer_commit
                )
            elif operation == "EVALUATE_CHECKPOINT":
                return self._execute_evaluate_checkpoint(
                    runner, context, cancellation_token, effective_producer_commit
                )
            elif operation == "MATERIALIZE_DATASET":
                return self._execute_materialize_dataset(runner, context, cancellation_token)
            else:
                raise WorkerDispatchError(
                    "ERR_OPERATION_SCOPE_UNSUPPORTED",
                    f"Unsupported operation '{operation}'",
                )

        local_token = cancellation_token or CancellationToken()

        def _timed_run() -> dict[str, Any]:
            if local_token.is_cancelled:
                raise WorkerCancelledError("Operation cancelled before start")

            runner = runner_override or ModelPluginRunner(
                plugin_id=context.model_plugin_id,
                dataset_id=context.dataset_id,
                execution_scope=context.requested_scope,
            )

            if operation == "TRAIN_TICKET":
                return self._execute_train_ticket(
                    runner, context, local_token, effective_producer_commit
                )
            elif operation == "EVALUATE_CHECKPOINT":
                return self._execute_evaluate_checkpoint(
                    runner, context, local_token, effective_producer_commit
                )
            elif operation == "MATERIALIZE_DATASET":
                return self._execute_materialize_dataset(runner, context, local_token)
            else:
                raise WorkerDispatchError(
                    "ERR_OPERATION_SCOPE_UNSUPPORTED",
                    f"Unsupported operation '{operation}'",
                )

        # Execute inside bounded executor with unblocked timeout termination
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_timed_run)
        try:
            result = future.result(timeout=timeout)
            executor.shutdown(wait=False, cancel_futures=True)
            return result
        except concurrent.futures.TimeoutError as exc:
            local_token.cancel()  # Signal cancellation to runner and prevent receipt emission
            future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            raise WorkerTimeoutError(
                f"Execution timed out after {timeout} seconds",
                details={"timeout_seconds": timeout, "execution_id": context.execution_id},
            ) from exc
        except Exception:
            executor.shutdown(wait=False, cancel_futures=True)
            raise

    def _execute_train_ticket(
        self,
        runner: ModelPluginRunner,
        context: PreflightContext,
        token: CancellationToken | None,
        producer_commit: str,
    ) -> dict[str, Any]:
        payload = context.operation_payload
        ticket_id = payload.get("ticket_id")
        partition_id = payload.get("partition_id")

        if not ticket_id or not isinstance(ticket_id, str):
            raise WorkerDispatchError(
                "ERR_SCHEMA_VALIDATION_FAILED", "Missing or invalid ticket_id"
            )
        if not partition_id or not isinstance(partition_id, str):
            raise WorkerDispatchError(
                "ERR_SCHEMA_VALIDATION_FAILED", "Missing or invalid partition_id"
            )

        if token and token.is_cancelled:
            raise WorkerCancelledError("Operation cancelled before ticket training")

        train_result = runner.train_ticket(ticket_id=ticket_id, partition_id=partition_id)

        if token and token.is_cancelled:
            raise WorkerCancelledError("Operation cancelled after ticket training")

        receipt = runner.emit_execution_receipt(
            producer_commit=producer_commit,
            controller_commit=context.controller_commit,
            intent_id=context.intent_id,
            intent_digest=context.intent_digest,
            admission_id=context.admission_id,
            admission_digest=context.admission_digest,
            execution_id=context.execution_id,
        )

        return {
            "status": "COMPLETED",
            "execution_id": context.execution_id,
            "operation": "TRAIN_TICKET",
            "result_metadata": train_result.metadata,
            "receipt": receipt,
        }

    def _execute_evaluate_checkpoint(
        self,
        runner: ModelPluginRunner,
        context: PreflightContext,
        token: CancellationToken | None,
        producer_commit: str,
    ) -> dict[str, Any]:
        payload = context.operation_payload
        coordinates = payload.get("checkpoint_coordinates")

        if coordinates is None or not isinstance(coordinates, Sequence):
            raise WorkerDispatchError(
                "ERR_SCHEMA_VALIDATION_FAILED", "Missing or invalid checkpoint_coordinates"
            )

        # Validate coordinate length against model plugin parameter schema
        registry = get_default_registry()
        descriptor = registry.get_descriptor(context.model_plugin_id)
        if descriptor and hasattr(descriptor, "parameter_schema"):
            schema_len = descriptor.parameter_schema.coordinate_count
            if len(coordinates) != schema_len:
                raise WorkerDispatchError(
                    "ERR_SCHEMA_VALIDATION_FAILED",
                    f"Coordinate length mismatch: expected {schema_len}, got {len(coordinates)}",
                    details={"expected_length": schema_len, "actual_length": len(coordinates)},
                )

        if token and token.is_cancelled:
            raise WorkerCancelledError("Operation cancelled before checkpoint evaluation")

        eval_result = runner.evaluate_checkpoint(coordinates)

        if token and token.is_cancelled:
            raise WorkerCancelledError("Operation cancelled after checkpoint evaluation")

        receipt = runner.emit_execution_receipt(
            producer_commit=producer_commit,
            controller_commit=context.controller_commit,
            intent_id=context.intent_id,
            intent_digest=context.intent_digest,
            admission_id=context.admission_id,
            admission_digest=context.admission_digest,
            execution_id=context.execution_id,
        )

        return {
            "status": "COMPLETED",
            "execution_id": context.execution_id,
            "operation": "EVALUATE_CHECKPOINT",
            "metrics": eval_result.metrics,
            "receipt": receipt,
        }

    def _execute_materialize_dataset(
        self,
        runner: ModelPluginRunner,
        context: PreflightContext,
        token: CancellationToken | None,
    ) -> dict[str, Any]:
        payload = context.operation_payload
        cache_key = payload.get("cache_key")

        cache_dir = None
        if cache_key:
            # Path safety check: forbid path traversal and absolute path injection
            if ".." in cache_key or cache_key.startswith(("/", "\\")) or ":" in cache_key:
                raise WorkerDispatchError(
                    "ERR_SCHEMA_VALIDATION_FAILED",
                    f"Illegal cache_key '{cache_key}': path traversal or absolute path forbidden",
                )
            cache_dir = self.cache_root / cache_key

        if token and token.is_cancelled:
            raise WorkerCancelledError("Operation cancelled before materialization")

        # Honor effective allow_downloads grant from preflight
        materialize_info = runner.materialize_dataset(
            cache_dir=cache_dir,
            allow_download=context.allow_downloads,
        )

        # Status only: MATERIALIZE_DATASET emits NO receipt
        return {
            "status": "COMPLETED",
            "execution_id": context.execution_id,
            "operation": "MATERIALIZE_DATASET",
            "materialize_info": dict(materialize_info),
            "receipt": None,
        }
