"""Deterministic lifecycle and optimizer-step telemetry."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.worker_state import LocalRoundState, transition
from deltatorrent.training.local_round import TrainingMetric


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    sequence: int
    state: LocalRoundState
    ticket_id: str
    domain_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "domain_id": self.domain_id,
            "schema_version": "1.0.0",
            "sequence": self.sequence,
            "state": self.state.value,
            "ticket_id": self.ticket_id,
        }


@dataclass(frozen=True, slots=True)
class LocalRoundMetric:
    optimizer_step: int
    micro_step: int
    processed_tokens: int
    loss_fp64_bits: str
    learning_rate_nanos: int

    def to_dict(self) -> dict[str, object]:
        return {
            "learning_rate_nanos": self.learning_rate_nanos,
            "loss_fp64_bits": self.loss_fp64_bits,
            "micro_step": self.micro_step,
            "optimizer_step": self.optimizer_step,
            "processed_tokens": self.processed_tokens,
            "schema_version": "1.0.0",
        }


@dataclass(slots=True)
class LocalRoundTelemetry:
    ticket_id: str
    domain_id: str
    state: LocalRoundState = LocalRoundState.RECEIVED
    events: list[LifecycleEvent] = field(default_factory=list)
    metrics: list[LocalRoundMetric] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state is not LocalRoundState.RECEIVED or self.events or self.metrics:
            raise DeltaError(ErrorCode.INVALID_WORKER_TRANSITION, "TELEMETRY_INITIAL_STATE_INVALID")
        self._append_event()

    def move_to(self, target: LocalRoundState) -> None:
        self.state = transition(self.state, target)
        self._append_event()

    def record_optimizer_step(self, metric: TrainingMetric, *, learning_rate_nanos: int) -> None:
        if self.state is not LocalRoundState.RUNNING:
            raise DeltaError(ErrorCode.INVALID_WORKER_TRANSITION, "METRIC_OUTSIDE_RUNNING_STATE")
        self.metrics.append(
            LocalRoundMetric(
                optimizer_step=metric.optimizer_step,
                micro_step=metric.step,
                processed_tokens=metric.processed_tokens,
                loss_fp64_bits=struct.pack(">d", metric.loss).hex(),
                learning_rate_nanos=learning_rate_nanos,
            )
        )

    def _append_event(self) -> None:
        self.events.append(
            LifecycleEvent(
                sequence=len(self.events),
                state=self.state,
                ticket_id=self.ticket_id,
                domain_id=self.domain_id,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "domain_id": self.domain_id,
            "events": [item.to_dict() for item in self.events],
            "metrics": [item.to_dict() for item in self.metrics],
            "schema_version": "1.0.0",
            "ticket_id": self.ticket_id,
        }
