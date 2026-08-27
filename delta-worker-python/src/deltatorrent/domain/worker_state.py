"""Pure local-round lifecycle transition rules."""

from __future__ import annotations

from enum import StrEnum

from deltatorrent.domain.errors import DeltaError, ErrorCode


class LocalRoundState(StrEnum):
    ACCEPTED = "ACCEPTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RECEIVED = "RECEIVED"
    RUNNING = "RUNNING"


_TRANSITIONS = {
    LocalRoundState.RECEIVED: frozenset({LocalRoundState.ACCEPTED, LocalRoundState.FAILED}),
    LocalRoundState.ACCEPTED: frozenset(
        {LocalRoundState.RUNNING, LocalRoundState.CANCELLED, LocalRoundState.FAILED}
    ),
    LocalRoundState.RUNNING: frozenset(
        {LocalRoundState.COMPLETED, LocalRoundState.CANCELLED, LocalRoundState.FAILED}
    ),
    LocalRoundState.COMPLETED: frozenset(),
    LocalRoundState.CANCELLED: frozenset(),
    LocalRoundState.FAILED: frozenset(),
}


def transition(current: LocalRoundState, target: LocalRoundState) -> LocalRoundState:
    if not isinstance(current, LocalRoundState) or not isinstance(target, LocalRoundState):
        raise DeltaError(ErrorCode.INVALID_WORKER_TRANSITION, "WORKER_STATE_INVALID")
    if target not in _TRANSITIONS[current]:
        raise DeltaError(
            ErrorCode.INVALID_WORKER_TRANSITION,
            "WORKER_TRANSITION_INVALID",
            {"current": current.value, "target": target.value},
        )
    return target
