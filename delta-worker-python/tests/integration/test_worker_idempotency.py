from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
import torch
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.updates import CompletionReason, CompletionStatus
from deltatorrent.worker.engine import (
    LocalRoundEngine,
    LocalRoundEngineResult,
    LocalRoundReplayResult,
    WorkerDataExhausted,
    WorkerInjectedCrash,
)
from deltatorrent.worker.update_writer import PublishedFailure, PublishedLocalRound

from tests.integration.test_local_round_engine import prepare_round


def _clock() -> Callable[[], int]:
    values = iter((0, 10_000_000))
    return lambda: next(values)


def _assert_terminal_without_candidate(
    result: LocalRoundEngineResult,
    *,
    status: CompletionStatus,
    reason: CompletionReason,
    store_root: Path,
) -> PublishedFailure:
    published = result.published
    assert isinstance(published, PublishedFailure)
    assert published.completion.status is status
    assert published.completion.reason is reason
    assert published.completion.candidate_eligible is False
    assert published.completion.local_delta is None
    assert published.completion.failure_code is not None
    assert published.completion_ref.locator.endswith("completion.json")
    assert not (
        store_root / f"local-round/{published.completion.ticket_id}/candidate.json"
    ).exists()
    return published


def test_exact_retry_returns_original_immutable_outcome(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="exact-replay")
    first = LocalRoundEngine(
        prepared.store,
        worker_id="worker-replay-1",
        clock_ns=_clock(),
    ).run(prepared.resolved)
    replay = LocalRoundEngine(prepared.store, worker_id="worker-replay-2").run(prepared.resolved)
    assert isinstance(first, LocalRoundEngineResult)
    assert isinstance(first.published, PublishedLocalRound)
    assert isinstance(replay, LocalRoundReplayResult)
    assert replay.to_dict() == first.to_dict()


def test_conflicting_ticket_id_reuse_fails_closed(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="conflicting-reuse")
    LocalRoundEngine(
        prepared.store,
        worker_id="worker-conflict-1",
        clock_ns=_clock(),
    ).run(prepared.resolved)
    changed = replace(
        prepared.ticket,
        optimizer_profile_id="sha256:" + "9" * 64,
    )
    conflicting = replace(prepared.resolved, ticket=changed)
    with pytest.raises(DeltaError) as raised:
        LocalRoundEngine(prepared.store, worker_id="worker-conflict-2").run(conflicting)
    assert raised.value.code is ErrorCode.TICKET_ID_CONFLICT


def test_cancellation_discards_partial_accumulation_and_publishes_terminal(
    tmp_path: Path,
) -> None:
    prepared = prepare_round(tmp_path, ticket_id="cancelled-partial")
    calls = 0

    def cancellation_requested() -> bool:
        nonlocal calls
        calls += 1
        return calls == 2

    result = LocalRoundEngine(
        prepared.store,
        worker_id="worker-cancel-1",
        clock_ns=_clock(),
        cancellation_requested=cancellation_requested,
    ).run(prepared.resolved)
    assert isinstance(result, LocalRoundEngineResult)
    failure = _assert_terminal_without_candidate(
        result,
        status=CompletionStatus.CANCELLED,
        reason=CompletionReason.CANCELLED,
        store_root=prepared.store.root,
    )
    assert failure.completion.micro_steps == 1
    assert failure.completion.effective_steps == 0
    assert failure.completion.processed_tokens == 0
    assert failure.completion.cursor_end == prepared.ticket.data_range.start


def test_deadline_is_checked_at_each_microbatch_boundary(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="deadline-partial")
    logical_values = iter((0, 0, prepared.ticket.logical_deadline_ms))
    result = LocalRoundEngine(
        prepared.store,
        worker_id="worker-deadline-1",
        clock_ns=_clock(),
        logical_clock_ms=lambda: next(logical_values),
    ).run(prepared.resolved)
    assert isinstance(result, LocalRoundEngineResult)
    failure = _assert_terminal_without_candidate(
        result,
        status=CompletionStatus.FAILED,
        reason=CompletionReason.DEADLINE,
        store_root=prepared.store.root,
    )
    assert failure.completion.micro_steps == 1
    assert failure.completion.effective_steps == 0


@pytest.mark.parametrize(
    ("ticket_id", "exception", "reason", "failure_code"),
    [
        (
            "oom-terminal",
            torch.OutOfMemoryError("injected"),
            CompletionReason.OOM,
            ErrorCode.WORKER_OOM.value,
        ),
        (
            "data-exhausted-terminal",
            WorkerDataExhausted("injected"),
            CompletionReason.DATA_EXHAUSTED,
            ErrorCode.WORKER_DATA_EXHAUSTED.value,
        ),
        (
            "nonfinite-terminal",
            DeltaError(ErrorCode.INVALID_MANIFEST, "NON_FINITE_LOSS"),
            CompletionReason.NON_FINITE,
            "NON_FINITE_STATE",
        ),
    ],
)
def test_injected_failures_publish_terminal_evidence_only(
    tmp_path: Path,
    ticket_id: str,
    exception: Exception,
    reason: CompletionReason,
    failure_code: str,
) -> None:
    prepared = prepare_round(tmp_path / ticket_id, ticket_id=ticket_id)

    def fail_first_boundary(stage: str) -> None:
        if stage == "BEFORE_MICROBATCH":
            raise exception

    result = LocalRoundEngine(
        prepared.store,
        worker_id="worker-failure-1",
        clock_ns=_clock(),
        fault_injector=fail_first_boundary,
    ).run(prepared.resolved)
    assert isinstance(result, LocalRoundEngineResult)
    failure = _assert_terminal_without_candidate(
        result,
        status=CompletionStatus.FAILED,
        reason=reason,
        store_root=prepared.store.root,
    )
    assert failure.completion.failure_code == failure_code


@pytest.mark.parametrize(
    "stage",
    ["BEFORE_PUBLICATION", "AFTER_NORMALIZED_DELTA_ARTIFACT"],
)
def test_injected_crash_before_or_after_tensor_staging_has_no_candidate(
    tmp_path: Path,
    stage: str,
) -> None:
    prepared = prepare_round(tmp_path / stage, ticket_id=f"crash-{stage.lower()}")

    def crash_at_stage(actual: str) -> None:
        if actual == stage:
            raise WorkerInjectedCrash(stage)

    result = LocalRoundEngine(
        prepared.store,
        worker_id="worker-crash-1",
        clock_ns=_clock(),
        fault_injector=crash_at_stage,
    ).run(prepared.resolved)
    assert isinstance(result, LocalRoundEngineResult)
    failure = _assert_terminal_without_candidate(
        result,
        status=CompletionStatus.FAILED,
        reason=CompletionReason.INTERNAL_FAILURE,
        store_root=prepared.store.root,
    )
    assert failure.completion.failure_code == ErrorCode.WORKER_CRASH.value


def test_recovery_reclaims_exact_orphaned_claim_after_process_death(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="crash-recovery")

    class SimulatedProcessDeath(BaseException):
        pass

    def die_after_staging(stage: str) -> None:
        if stage == "AFTER_NORMALIZED_DELTA_ARTIFACT":
            raise SimulatedProcessDeath()

    with pytest.raises(SimulatedProcessDeath):
        LocalRoundEngine(
            prepared.store,
            worker_id="worker-dead-1",
            clock_ns=_clock(),
            fault_injector=die_after_staging,
        ).run(prepared.resolved)
    assert not (prepared.store.root / "local-round/crash-recovery/candidate.json").exists()

    with pytest.raises(DeltaError) as in_progress:
        LocalRoundEngine(prepared.store, worker_id="worker-retry-without-recovery").run(
            prepared.resolved
        )
    assert in_progress.value.code is ErrorCode.TICKET_ALREADY_IN_PROGRESS

    recovered = LocalRoundEngine(
        prepared.store,
        worker_id="worker-recovery-1",
        clock_ns=_clock(),
        recover_incomplete=True,
    ).run(prepared.resolved)
    assert isinstance(recovered, LocalRoundEngineResult)
    assert isinstance(recovered.published, PublishedLocalRound)
    assert recovered.published.completion.candidate_eligible is True
    assert (prepared.store.root / "local-round/crash-recovery/candidate.json").is_file()
