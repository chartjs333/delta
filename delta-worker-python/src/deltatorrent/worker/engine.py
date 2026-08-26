"""Deterministic fixed-ticket local round orchestration."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import torch

from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.delta.builder import build_local_delta, snapshot_fp32_parameters
from deltatorrent.delta.normalization import normalize_local_delta
from deltatorrent.delta.reconstruction import reconstruct_final
from deltatorrent.delta.schema import canonical_parameter_tensors
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.worker_state import LocalRoundState
from deltatorrent.training.baseline import TrainingState
from deltatorrent.training.data import DeterministicSampler
from deltatorrent.training.local_round import train_one_optimizer_step
from deltatorrent.training.token_accounting import OptimizerBoundaryLedger
from deltatorrent.worker.telemetry import LocalRoundTelemetry
from deltatorrent.worker.update_writer import LocalUpdateWriter, PublishedLocalRound
from deltatorrent.worker.validation import ResolvedLocalRound


@dataclass(frozen=True, slots=True)
class LocalRoundEngineResult:
    published: PublishedLocalRound
    telemetry: LocalRoundTelemetry

    def to_dict(self) -> dict[str, object]:
        return {
            **self.published.to_dict(),
            "telemetry": self.telemetry.to_dict(),
        }


class LocalRoundEngine:
    def __init__(
        self,
        store: FilesystemArtifactStore,
        *,
        worker_id: str,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
    ) -> None:
        self.store = store
        self.worker_id = worker_id
        self.clock_ns = clock_ns
        self.writer = LocalUpdateWriter(store)

    def run(self, resolved: ResolvedLocalRound) -> LocalRoundEngineResult:
        ticket = resolved.ticket
        telemetry = LocalRoundTelemetry(ticket.ticket_id, ticket.domain_id)
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
        if any(not torch.equal(parent[name], resolved.parent_parameters[name]) for name in parent):
            raise DeltaError(ErrorCode.INVALID_WORK_TICKET, "PARENT_LOAD_MISMATCH")
        ledger = OptimizerBoundaryLedger(
            range_start=ticket.data_range.start,
            range_end=ticket.data_range.end,
        )
        telemetry.move_to(LocalRoundState.RUNNING)
        started = self.clock_ns()
        for _ in range(ticket.step_budget):
            metric = train_one_optimizer_step(
                state,
                resolved.config,
                resolved.samples,
                ledger=ledger,
            )
            telemetry.record_optimizer_step(
                metric,
                learning_rate_nanos=resolved.config.learning_rate_nanos,
            )
        wall_time_ms = max(0, (self.clock_ns() - started) // 1_000_000)
        accounting = ledger.snapshot()
        if accounting.cursor_end != ticket.data_range.end:
            raise DeltaError(ErrorCode.INVALID_TOKEN_ACCOUNTING, "TICKET_RANGE_NOT_EXHAUSTED")
        final = snapshot_fp32_parameters(state.model, resolved.parameter_schema)
        local_delta = build_local_delta(parent, final, resolved.parameter_schema)
        reconstructed = reconstruct_final(parent, local_delta, resolved.parameter_schema)
        if any(
            not torch.allclose(reconstructed[name], final[name], rtol=1e-6, atol=1e-7)
            for name in final
        ):
            raise DeltaError(ErrorCode.INVALID_DELTA_TENSOR, "LOCAL_DELTA_RECONSTRUCTION_FAILED")
        normalized = normalize_local_delta(
            local_delta,
            resolved.parameter_schema,
            effective_steps=accounting.effective_steps,
            step_budget=ticket.step_budget,
            per_tensor_norm_ceiling=resolved.limits.per_tensor_norm_ceiling,
            global_norm_ceiling=resolved.limits.global_norm_ceiling,
        )
        telemetry.move_to(LocalRoundState.COMPLETED)
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
        )
        self.writer.verify_success(
            published,
            ticket=ticket,
            parameter_schema=resolved.parameter_schema,
            limits=resolved.limits,
        )
        return LocalRoundEngineResult(published=published, telemetry=telemetry)
