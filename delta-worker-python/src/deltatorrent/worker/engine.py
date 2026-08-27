"""Deterministic fixed-ticket local round orchestration."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import torch

from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.delta.builder import build_local_delta, snapshot_fp32_parameters
from deltatorrent.delta.normalization import normalize_local_delta
from deltatorrent.delta.reconstruction import reconstruct_final
from deltatorrent.delta.schema import canonical_parameter_tensors
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.updates import CompletionReason, CompletionStatus
from deltatorrent.domain.worker_state import LocalRoundState
from deltatorrent.training.baseline import TrainingState
from deltatorrent.training.data import DeterministicSampler
from deltatorrent.training.local_round import train_one_optimizer_step
from deltatorrent.training.token_accounting import OptimizerBoundaryLedger
from deltatorrent.worker.repository import ClaimDisposition, TicketResultRepository
from deltatorrent.worker.telemetry import LocalRoundTelemetry
from deltatorrent.worker.update_writer import (
    LocalUpdateWriter,
    PublishedFailure,
    PublishedLocalRound,
)
from deltatorrent.worker.validation import ResolvedLocalRound


class WorkerCancellationRequested(RuntimeError):
    pass


class WorkerDataExhausted(RuntimeError):
    pass


class WorkerDeadlineExceeded(RuntimeError):
    pass


class WorkerInjectedCrash(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LocalRoundEngineResult:
    published: PublishedLocalRound | PublishedFailure
    telemetry: LocalRoundTelemetry

    def to_dict(self) -> dict[str, object]:
        return {
            **self.published.to_dict(),
            "telemetry": self.telemetry.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class LocalRoundReplayResult:
    outcome: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.outcome)


class LocalRoundEngine:
    def __init__(
        self,
        store: FilesystemArtifactStore,
        *,
        worker_id: str,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
        logical_clock_ms: Callable[[], int] = lambda: time.monotonic_ns() // 1_000_000,
        cancellation_requested: Callable[[], bool] = lambda: False,
        fault_injector: Callable[[str], None] | None = None,
        repository: TicketResultRepository | None = None,
        recover_incomplete: bool = False,
    ) -> None:
        self.store = store
        self.worker_id = worker_id
        self.clock_ns = clock_ns
        self.logical_clock_ms = logical_clock_ms
        self.cancellation_requested = cancellation_requested
        self.fault_injector = fault_injector
        self.writer = LocalUpdateWriter(store)
        self.repository = repository or TicketResultRepository(store.root / "local-round-state")
        self.recover_incomplete = recover_incomplete

    def run(self, resolved: ResolvedLocalRound) -> LocalRoundEngineResult | LocalRoundReplayResult:
        ticket = resolved.ticket
        claim = self.repository.claim(ticket, recover_incomplete=self.recover_incomplete)
        if claim.disposition is ClaimDisposition.REPLAY:
            assert claim.outcome is not None
            return LocalRoundReplayResult(claim.outcome)

        telemetry = LocalRoundTelemetry(ticket.ticket_id, ticket.domain_id)
        ledger = OptimizerBoundaryLedger(
            range_start=ticket.data_range.start,
            range_end=ticket.data_range.end,
        )
        started = self.clock_ns()
        logical_started = self.logical_clock_ms()
        wall_time_ms: int | None = None
        try:
            self._inject("AFTER_CLAIM")
            telemetry.move_to(LocalRoundState.ACCEPTED)
            state = TrainingState.create(resolved.config, len(resolved.samples))
            state.sampler = DeterministicSampler(
                len(resolved.samples),
                ticket.deterministic_seed,
                cursor=ticket.data_range.start,
            )
            actual_parameters = canonical_parameter_tensors(state.model, resolved.parameter_schema)
            with torch.no_grad():
                for name, parameter in actual_parameters.items():
                    parameter.copy_(resolved.parent_parameters[name])
            parent = snapshot_fp32_parameters(state.model, resolved.parameter_schema)
            if any(
                not torch.equal(parent[name], resolved.parent_parameters[name]) for name in parent
            ):
                raise DeltaError(ErrorCode.INVALID_WORK_TICKET, "PARENT_LOAD_MISMATCH")

            telemetry.move_to(LocalRoundState.RUNNING)
            for _ in range(ticket.step_budget):
                metric = train_one_optimizer_step(
                    state,
                    resolved.config,
                    resolved.samples,
                    ledger=ledger,
                    before_microbatch=lambda: self._check_boundary(
                        logical_started,
                        ticket.logical_deadline_ms,
                    ),
                )
                telemetry.record_optimizer_step(
                    metric,
                    learning_rate_nanos=resolved.config.learning_rate_nanos,
                )
                self._inject("AFTER_OPTIMIZER_STEP")
            accounting = ledger.snapshot()
            if accounting.cursor_end != ticket.data_range.end:
                raise WorkerDataExhausted("TICKET_RANGE_NOT_EXHAUSTED")

            final = snapshot_fp32_parameters(state.model, resolved.parameter_schema)
            local_delta = build_local_delta(parent, final, resolved.parameter_schema)
            reconstructed = reconstruct_final(parent, local_delta, resolved.parameter_schema)
            if any(
                not torch.allclose(reconstructed[name], final[name], rtol=1e-6, atol=1e-7)
                for name in final
            ):
                raise DeltaError(
                    ErrorCode.INVALID_DELTA_TENSOR,
                    "LOCAL_DELTA_RECONSTRUCTION_FAILED",
                )
            normalized = normalize_local_delta(
                local_delta,
                resolved.parameter_schema,
                effective_steps=accounting.effective_steps,
                step_budget=ticket.step_budget,
                per_tensor_norm_ceiling=resolved.limits.per_tensor_norm_ceiling,
                global_norm_ceiling=resolved.limits.global_norm_ceiling,
            )
            self._inject("BEFORE_PUBLICATION")
            wall_time_ms = max(0, (self.clock_ns() - started) // 1_000_000)
            published = self.writer.publish_success(
                ticket=ticket,
                worker_id=self.worker_id,
                parameter_schema=resolved.parameter_schema,
                accounting=accounting,
                local_delta=local_delta,
                normalized_delta=normalized,
                limits=resolved.limits,
                wall_time_ms=wall_time_ms,
                peak_memory_bytes=0,
                after_stage=self._inject,
            )
            self.writer.verify_success(
                published,
                ticket=ticket,
                parameter_schema=resolved.parameter_schema,
                limits=resolved.limits,
            )
            telemetry.move_to(LocalRoundState.COMPLETED)
        except Exception as exc:
            status, reason, failure_code = self._classify_failure(exc)
            target = (
                LocalRoundState.CANCELLED
                if status is CompletionStatus.CANCELLED
                else LocalRoundState.FAILED
            )
            telemetry.move_to(target)
            if wall_time_ms is None:
                wall_time_ms = max(0, (self.clock_ns() - started) // 1_000_000)
            failed = self.writer.publish_failure(
                ticket=ticket,
                worker_id=self.worker_id,
                parameter_schema=resolved.parameter_schema,
                accounting=ledger.snapshot(),
                status=status,
                reason=reason,
                failure_code=failure_code,
                wall_time_ms=wall_time_ms,
                peak_memory_bytes=0,
            )
            result = LocalRoundEngineResult(published=failed, telemetry=telemetry)
            self.repository.complete(ticket, result.to_dict())
            return result

        result = LocalRoundEngineResult(published=published, telemetry=telemetry)
        self.repository.complete(ticket, result.to_dict())
        return result

    def _check_boundary(self, logical_started: int, deadline_ms: int) -> None:
        self._inject("BEFORE_MICROBATCH")
        if self.cancellation_requested():
            raise WorkerCancellationRequested("WORKER_CANCELLED")
        if self.logical_clock_ms() - logical_started >= deadline_ms:
            raise WorkerDeadlineExceeded("WORKER_DEADLINE_EXCEEDED")

    def _inject(self, stage: str) -> None:
        if self.fault_injector is not None:
            self.fault_injector(stage)

    @staticmethod
    def _classify_failure(
        exc: Exception,
    ) -> tuple[CompletionStatus, CompletionReason, str]:
        if isinstance(exc, WorkerCancellationRequested):
            return (
                CompletionStatus.CANCELLED,
                CompletionReason.CANCELLED,
                ErrorCode.WORKER_CANCELLED.value,
            )
        if isinstance(exc, WorkerDeadlineExceeded):
            return (
                CompletionStatus.FAILED,
                CompletionReason.DEADLINE,
                ErrorCode.WORKER_DEADLINE_EXCEEDED.value,
            )
        if isinstance(exc, WorkerDataExhausted):
            return (
                CompletionStatus.FAILED,
                CompletionReason.DATA_EXHAUSTED,
                ErrorCode.WORKER_DATA_EXHAUSTED.value,
            )
        if isinstance(exc, torch.OutOfMemoryError):
            return CompletionStatus.FAILED, CompletionReason.OOM, ErrorCode.WORKER_OOM.value
        if isinstance(exc, WorkerInjectedCrash):
            return (
                CompletionStatus.FAILED,
                CompletionReason.INTERNAL_FAILURE,
                ErrorCode.WORKER_CRASH.value,
            )
        if isinstance(exc, DeltaError) and exc.message in {
            "NON_FINITE_GRADIENT",
            "NON_FINITE_LOSS",
            "NON_FINITE_OPTIMIZER_STATE",
            "DELTA_TENSOR_NON_FINITE",
        }:
            return (
                CompletionStatus.FAILED,
                CompletionReason.NON_FINITE,
                "NON_FINITE_STATE",
            )
        raise exc
