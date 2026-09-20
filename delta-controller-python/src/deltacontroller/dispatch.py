"""Worker dispatch port and adapters for passing AuthorizedExecution bundles to Zone 3."""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, Protocol

from deltacontroller.canonical import canonicalize_jcs, sha256_digest
from deltacontroller.errors import QuotaExceededError, WorkerDispatchFailedError
from deltacontroller.idempotency import (
    NONTERMINAL_STATUSES,
    TERMINAL_STATUSES,
    IdempotencyLedger,
    LedgerRecord,
)
from deltacontroller.schema import SchemaRegistry


class WorkerDispatchPort(Protocol):
    """Protocol for dispatching an AuthorizedExecution bundle to a worker runtime."""

    def reserve_capacity(self, intent_id: str) -> None:
        """Reserve physical dispatch capacity before durable admission."""
        ...

    def release_capacity_reservation(self, intent_id: str) -> None:
        """Release an unused pre-admission capacity reservation."""
        ...

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

    def reserve_capacity(self, intent_id: str) -> None:
        del intent_id

    def release_capacity_reservation(self, intent_id: str) -> None:
        del intent_id

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
        producer_commit: str | None = None,
    ) -> None:
        from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher

        if producer_commit is None or re.fullmatch(r"[0-9a-f]{40}", producer_commit) is None:
            raise ValueError(
                "IntegratedWorkerDispatchPort requires an explicit 40-character build SHA"
            )
        self.schema_registry = schema_registry or SchemaRegistry()
        self.preflight = preflight
        self.dispatcher = dispatcher or ClosedEnumWorkerDispatcher(producer_commit=producer_commit)
        self.cancellation_token = cancellation_token
        self.clock = clock or (lambda: datetime.now(UTC))
        self.producer_commit = producer_commit
        self.dispatch_count = 0

    def reserve_capacity(self, intent_id: str) -> None:
        del intent_id

    def release_capacity_reservation(self, intent_id: str) -> None:
        del intent_id

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
                producer_commit=self.producer_commit,
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
                    "producer_commit": self.producer_commit,
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


class WorkerProcessRunner(Protocol):
    """Injectable one-request process runner used by the async queue."""

    def run(
        self,
        bundle: dict[str, Any],
        cancellation_requested: threading.Event,
    ) -> dict[str, Any]: ...


class _WorkerProcessCancelled(RuntimeError):
    pass


class _WorkerProcessTimedOut(RuntimeError):
    pass


class JsonSubprocessWorkerRunner:
    """Run one fixed-argv Worker process without a shell."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        max_output_bytes: int = 10 * 1024 * 1024,
        startup_grace_seconds: float = 15.0,
        poll_interval_seconds: float = 0.05,
    ) -> None:
        if not command or any(not isinstance(part, str) or not part for part in command):
            raise ValueError("worker command must be a non-empty fixed argv sequence")
        if max_output_bytes < 1:
            raise ValueError("max_output_bytes must be positive")
        self.command = tuple(command)
        self.max_output_bytes = max_output_bytes
        self.startup_grace_seconds = startup_grace_seconds
        self.poll_interval_seconds = poll_interval_seconds

    @staticmethod
    def _sanitized_environment() -> dict[str, str]:
        # Never copy credential/key/config variables into Zone 3. Keep only
        # process-launch, temporary-directory, and locale mechanics needed by
        # the fixed Python worker command.
        allowed_names = (
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "TMPDIR",
            "LANG",
            "LC_ALL",
        )
        environment = {name: os.environ[name] for name in allowed_names if os.environ.get(name)}
        environment.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONNOUSERSITE": "1",
                "PYTHONUTF8": "1",
            }
        )
        return environment

    @staticmethod
    def _execution_timeout(bundle: dict[str, Any]) -> int:
        admission = bundle.get("admission")
        grants = admission.get("resource_grants") if isinstance(admission, dict) else None
        timeout: object = grants.get("timeout_seconds") if isinstance(grants, dict) else None
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            raise WorkerDispatchFailedError("AuthorizedExecution has an invalid timeout grant")
        return timeout

    @staticmethod
    def _terminate(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    def run(
        self,
        bundle: dict[str, Any],
        cancellation_requested: threading.Event,
    ) -> dict[str, Any]:
        payload = canonicalize_jcs(bundle)
        timeout_seconds = self._execution_timeout(bundle)
        # File-backed stdio prevents both unbounded output buffering and a
        # Windows ``communicate(input=...)`` write from blocking before its
        # timeout is armed when a broken Worker never reads stdin.  The input
        # file is complete and positioned before process creation, so the child
        # sees an ordinary bounded stream ending at EOF without a Controller
        # writer thread that could outlive cancellation or shutdown.
        with (
            tempfile.TemporaryFile() as stdin_source,
            tempfile.TemporaryFile() as stdout_sink,
            tempfile.TemporaryFile() as stderr_sink,
        ):
            stdin_source.write(payload)
            stdin_source.seek(0)
            process = subprocess.Popen(
                list(self.command),
                stdin=stdin_source,
                stdout=stdout_sink,
                stderr=stderr_sink,
                env=self._sanitized_environment(),
                shell=False,
            )
            deadline = time.monotonic() + timeout_seconds + self.startup_grace_seconds
            while True:
                if cancellation_requested.is_set():
                    self._terminate(process)
                    raise _WorkerProcessCancelled("Worker process was cancelled")
                if (
                    stdout_sink.seek(0, 2) > self.max_output_bytes
                    or stderr_sink.seek(0, 2) > self.max_output_bytes
                ):
                    self._terminate(process)
                    raise WorkerDispatchFailedError(
                        "Worker process output exceeded its bounded limit"
                    )
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._terminate(process)
                    raise _WorkerProcessTimedOut("Worker process exceeded its bounded deadline")
                try:
                    process.wait(timeout=min(self.poll_interval_seconds, remaining))
                    break
                except subprocess.TimeoutExpired:
                    pass

            stdout_size = stdout_sink.seek(0, 2)
            stderr_size = stderr_sink.seek(0, 2)
            if stdout_size > self.max_output_bytes or stderr_size > self.max_output_bytes:
                raise WorkerDispatchFailedError("Worker process output exceeded its bounded limit")
            stdout_sink.seek(0)
            stdout = stdout_sink.read(self.max_output_bytes + 1)
        if process.returncode != 0:
            raise WorkerDispatchFailedError(
                f"Worker process exited with status {process.returncode}"
            )
        try:
            result = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkerDispatchFailedError(
                "Worker process stdout is not one UTF-8 JSON document"
            ) from exc
        if not isinstance(result, dict):
            raise WorkerDispatchFailedError("Worker process result must be a JSON object")
        return result


@dataclass(slots=True)
class _QueuedExecution:
    execution_id: str
    bundle: dict[str, Any]
    cancellation_requested: threading.Event
    future: Future[None] | None = None


class SubprocessWorkerDispatchPort:
    """Bounded asynchronous Controller -> separate Worker process queue.

    Queue, running, cancellation, and terminal updates are durable CAS
    transitions in the Controller ledger.  Worker output is never exposed or
    persisted until its identity, lineage, receipt, and build binding validate.
    """

    def __init__(
        self,
        *,
        ledger: IdempotencyLedger,
        producer_commit: str,
        worker_command: Sequence[str] | None = None,
        runner: WorkerProcessRunner | None = None,
        schema_registry: SchemaRegistry | None = None,
        max_workers: int = 2,
        max_queue: int = 8,
        recover_on_startup: bool = True,
    ) -> None:
        if re.fullmatch(r"[0-9a-f]{40}", producer_commit) is None:
            raise ValueError("producer_commit must be an explicit 40-character build SHA")
        if max_workers < 1 or max_queue < 0:
            raise ValueError("max_workers must be positive and max_queue must be non-negative")
        if runner is not None and worker_command is not None:
            raise ValueError("configure either runner or worker_command, not both")
        if runner is None:
            if worker_command is None:
                raise ValueError("worker_command is required when no process runner is injected")
            runner = JsonSubprocessWorkerRunner(worker_command)

        self.ledger = ledger
        self.producer_commit = producer_commit
        self.runner = runner
        self.schema_registry = schema_registry or SchemaRegistry()
        self.max_workers = max_workers
        self.max_queue = max_queue
        self._capacity = threading.BoundedSemaphore(max_workers + max_queue)
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="delta-worker-process",
        )
        self._lock = threading.RLock()
        self._state_changed = threading.Condition(self._lock)
        self._jobs: dict[str, _QueuedExecution] = {}
        self._capacity_reservations: set[str] = set()
        self._accepting = True
        self.recovered_orphan_count = self.recover_orphans() if recover_on_startup else 0

    @staticmethod
    def _error(
        error_code: str,
        category: str,
        retryable: bool,
        message: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "error_code": error_code,
            "category": category,
            "retryable": retryable,
            "message": message[:512],
        }

    def reserve_capacity(self, intent_id: str) -> None:
        """Acquire one physical queue slot before an admission is committed."""
        with self._state_changed:
            if not self._accepting:
                raise WorkerDispatchFailedError("Worker queue is shutting down")
            if intent_id in self._capacity_reservations:
                raise WorkerDispatchFailedError("Worker capacity is already reserved for intent")
            if not self._capacity.acquire(blocking=False):
                raise QuotaExceededError("Worker process queue capacity is exhausted")
            self._capacity_reservations.add(intent_id)
            self._state_changed.notify_all()

    def release_capacity_reservation(self, intent_id: str) -> None:
        """Release a reservation only when dispatch has not consumed it."""
        with self._state_changed:
            if intent_id not in self._capacity_reservations:
                return
            self._capacity_reservations.remove(intent_id)
            self._capacity.release()
            self._state_changed.notify_all()

    def dispatch(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Durably queue one bundle and return the agreed QUEUED acknowledgment."""
        self.schema_registry.validate("authorized-execution", bundle)
        execution_id = bundle["admission"]["execution_id"]
        intent_id = bundle["intent"]["intent_id"]

        job = _QueuedExecution(
            execution_id=execution_id,
            bundle=copy.deepcopy(bundle),
            cancellation_requested=threading.Event(),
        )
        capacity_owned = False
        queued_committed = False
        try:
            with self._state_changed:
                if intent_id in self._capacity_reservations:
                    self._capacity_reservations.remove(intent_id)
                    capacity_owned = True
                else:
                    if not self._accepting:
                        raise WorkerDispatchFailedError("Worker queue is shutting down")
                    if not self._capacity.acquire(blocking=False):
                        raise QuotaExceededError("Worker process queue capacity is exhausted")
                    capacity_owned = True

                # A pre-shutdown reservation is allowed to finish publication.
                # Holding the state lock across the durable QUEUED transition and
                # executor submission prevents shutdown from missing this job.
                queued = self.ledger.transition_execution(
                    execution_id,
                    expected_statuses={"ADMITTED"},
                    status="QUEUED",
                )
                if queued is None:
                    raise WorkerDispatchFailedError(
                        "Execution was not ADMITTED when the Worker queue accepted it"
                    )
                queued_committed = True
                self._jobs[execution_id] = job
                job.future = self._executor.submit(self._run_job, job)
                job.future.add_done_callback(lambda _future: self._finish_job(job))
                self._state_changed.notify_all()
        except BaseException:
            with self._state_changed:
                if self._jobs.get(execution_id) is job:
                    self._jobs.pop(execution_id, None)
                if capacity_owned:
                    self._capacity.release()
                    capacity_owned = False
                self._state_changed.notify_all()
            if queued_committed:
                self.ledger.transition_execution(
                    execution_id,
                    expected_statuses={"QUEUED"},
                    status="FAILED",
                    error=self._error(
                        "ERR_WORKER_DISPATCH_FAILED",
                        "DISPATCH",
                        True,
                        "Worker queue submission failed",
                    ),
                )
            raise

        return {
            "dispatched": True,
            "execution_id": execution_id,
            "intent_id": intent_id,
            "status": "QUEUED",
        }

    def _finish_job(self, job: _QueuedExecution) -> None:
        with self._state_changed:
            if self._jobs.get(job.execution_id) is job:
                self._jobs.pop(job.execution_id, None)
                self._capacity.release()
            self._state_changed.notify_all()

    def _run_job(self, job: _QueuedExecution) -> None:
        if job.cancellation_requested.is_set():
            return
        running = self.ledger.transition_execution(
            job.execution_id,
            expected_statuses={"QUEUED"},
            status="RUNNING",
        )
        if running is None:
            return

        try:
            raw_result = self.runner.run(job.bundle, job.cancellation_requested)
            result = self._validate_terminal_result(job.bundle, raw_result)
            self.ledger.transition_execution(
                job.execution_id,
                expected_statuses={"RUNNING"},
                status=result["status"],
                receipt_digest=result.get("receipt_digest"),
                terminal_receipt=result.get("receipt"),
                error=result.get("error"),
            )
        except _WorkerProcessCancelled:
            self.ledger.transition_execution(
                job.execution_id,
                expected_statuses={"RUNNING"},
                status="CANCELLED",
                error=self._error("ERR_CANCELLED", "WORKER", True, "Worker process was cancelled"),
            )
        except _WorkerProcessTimedOut:
            self.ledger.transition_execution(
                job.execution_id,
                expected_statuses={"RUNNING"},
                status="TIMED_OUT",
                error=self._error(
                    "ERR_TIMEOUT", "WORKER", True, "Worker process exceeded its deadline"
                ),
            )
        except Exception as exc:
            self.ledger.transition_execution(
                job.execution_id,
                expected_statuses={"RUNNING"},
                status="FAILED",
                error=self._error(
                    "ERR_WORKER_DISPATCH_FAILED",
                    "DISPATCH",
                    True,
                    f"Worker process failed ({type(exc).__name__})",
                ),
            )

    def _validate_terminal_result(
        self,
        bundle: dict[str, Any],
        result: Any,
    ) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise WorkerDispatchFailedError("Worker terminal result must be an object")
        execution_id = bundle["admission"]["execution_id"]
        intent_id = bundle["intent"]["intent_id"]
        operation = bundle["intent"]["operation"]
        if result.get("execution_id") != execution_id or result.get("intent_id") != intent_id:
            raise WorkerDispatchFailedError("Worker terminal identity mismatch")
        if result.get("operation") != operation:
            raise WorkerDispatchFailedError("Worker terminal operation mismatch")
        if not isinstance(result.get("dispatched"), bool):
            raise WorkerDispatchFailedError("Worker terminal result lacks dispatched boolean")
        status = result.get("status")
        if status not in TERMINAL_STATUSES:
            raise WorkerDispatchFailedError("Worker process did not return a terminal status")

        receipt = result.get("receipt")
        receipt_digest = result.get("receipt_digest")
        error = result.get("error")
        if status == "COMPLETED":
            if result.get("dispatched") is not True or error is not None:
                raise WorkerDispatchFailedError("Completed Worker result is inconsistent")
            if operation == "MATERIALIZE_DATASET":
                if receipt is not None or receipt_digest is not None:
                    raise WorkerDispatchFailedError(
                        "MATERIALIZE_DATASET cannot return a terminal receipt"
                    )
            else:
                if not isinstance(receipt, dict):
                    raise WorkerDispatchFailedError("Completed Worker result lacks a receipt")
                self.schema_registry.validate("receipt-lineage", receipt)
                expected_provenance = {
                    "intent_id": intent_id,
                    "intent_digest": bundle["intent"]["intent_digest"],
                    "admission_id": bundle["admission"]["admission_id"],
                    "admission_digest": bundle["admission"]["admission_digest"],
                    "execution_id": execution_id,
                    "controller_commit": bundle["admission"]["policy_context"]["controller_commit"],
                    "catalog_backend_ref": bundle["intent"]["workload"]["catalog_backend_ref"],
                    "backend_commit": bundle["intent"]["workload"]["catalog_backend_ref"],
                    "producer_commit": self.producer_commit,
                }
                provenance = receipt.get("provenance", {})
                if any(provenance.get(key) != value for key, value in expected_provenance.items()):
                    raise WorkerDispatchFailedError("Worker receipt provenance mismatch")
                workload = receipt.get("workload", {})
                expected_workload = {
                    "model_plugin_id": bundle["intent"]["workload"]["model_plugin_id"],
                    "dataset_id": bundle["intent"]["workload"]["dataset_id"],
                    "executed_scope": bundle["intent"]["workload"]["requested_scope"],
                }
                if any(workload.get(key) != value for key, value in expected_workload.items()):
                    raise WorkerDispatchFailedError("Worker receipt workload mismatch")
                computed_digest = sha256_digest(canonicalize_jcs(receipt))
                if receipt_digest != computed_digest:
                    raise WorkerDispatchFailedError("Worker receipt digest mismatch")
        else:
            if receipt is not None or receipt_digest is not None:
                raise WorkerDispatchFailedError("Failed Worker result contains a receipt")
            if not isinstance(error, dict):
                raise WorkerDispatchFailedError("Failed Worker result lacks an error")
            self.schema_registry.validate("preflight-error", error)
            if status in {"TIMED_OUT", "CANCELLED"} and result.get("dispatched") is not True:
                raise WorkerDispatchFailedError(
                    f"Worker state {status} requires an attempted dispatch"
                )
        return copy.deepcopy(result)

    def cancel(self, execution_id: str) -> LedgerRecord | None:
        """Atomically cancel one queued/running execution and signal its process."""
        current = self.ledger.get_by_execution_id(execution_id)
        if current is None:
            raise KeyError(f"Unknown execution_id '{execution_id}'")
        if current.status in TERMINAL_STATUSES:
            return None

        cancelled = self.ledger.transition_execution(
            execution_id,
            expected_statuses=NONTERMINAL_STATUSES,
            status="CANCELLED",
            error=self._error("ERR_CANCELLED", "WORKER", True, "Execution was cancelled"),
        )
        if cancelled is None:
            winner = self.ledger.get_by_execution_id(execution_id)
            if winner is None:
                raise KeyError(f"Unknown execution_id '{execution_id}'")
            return None

        with self._lock:
            job = self._jobs.get(execution_id)
            if job is not None:
                job.cancellation_requested.set()
                if job.future is not None:
                    job.future.cancel()
        return cancelled

    def recover_orphans(self) -> int:
        """Fail closed durable nonterminal records not owned by this process."""
        with self._lock:
            active_ids = set(self._jobs)
        recovered = 0
        for record in self.ledger.list_nonterminal_records():
            if record.execution_id in active_ids:
                continue
            transitioned = self.ledger.transition_execution(
                record.execution_id,
                expected_statuses={record.status},
                status="FAILED",
                error=self._error(
                    "ERR_WORKER_DISPATCH_FAILED",
                    "DISPATCH",
                    True,
                    "Controller restarted with an orphaned nonterminal execution",
                ),
            )
            if transitioned is not None:
                recovered += 1
        return recovered

    def shutdown(self, timeout_seconds: float) -> None:
        """Stop admission, drain bounded work, then cancel any remaining jobs."""
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        deadline = time.monotonic() + timeout_seconds
        shutdown_error: RuntimeError | None = None
        with self._state_changed:
            self._accepting = False
            while self._capacity_reservations:
                remaining_seconds = deadline - time.monotonic()
                if remaining_seconds <= 0:
                    break
                self._state_changed.wait(timeout=remaining_seconds)
            if self._capacity_reservations:
                shutdown_error = RuntimeError(
                    "Dispatch capacity reservations exceeded the shutdown deadline"
                )
                # A gate may be between its durable admission and dispatch call.
                # Continue holding the process lease until every reservation is
                # consumed or released, rather than racing executor shutdown.
                while self._capacity_reservations:
                    self._state_changed.wait()
            futures = [job.future for job in self._jobs.values() if job.future is not None]
        remaining_seconds = max(0.0, deadline - time.monotonic())
        _done, pending = wait(futures, timeout=remaining_seconds)
        if pending:
            with self._lock:
                remaining_jobs = [
                    job
                    for job in self._jobs.values()
                    if job.future is not None and job.future in pending
                ]
            for job in remaining_jobs:
                try:
                    self.cancel(job.execution_id)
                except Exception:
                    # Even a poisoned ledger must not prevent the process signal
                    # or allow the data-directory lease to be released early.
                    job.cancellation_requested.set()
                    if job.future is not None:
                        job.future.cancel()
            # JsonSubprocessWorkerRunner observes cancellation at a short poll
            # interval and terminates its child. Keep ownership of the durable
            # data directory until those futures have actually returned.
            cancellation_grace = min(5.0, max(1.0, timeout_seconds))
            _cancelled, still_running = wait(pending, timeout=cancellation_grace)
            if still_running:
                shutdown_error = RuntimeError(
                    "Worker processes exceeded bounded cancellation; waited fail-closed for exit"
                )
        # Never return (or raise) while an executor thread/process can still use
        # the durable directory.  If a broken injected runner never exits, the
        # Controller deliberately remains alive holding its cross-process lease.
        self._executor.shutdown(wait=True, cancel_futures=True)
        if shutdown_error is not None:
            raise shutdown_error
