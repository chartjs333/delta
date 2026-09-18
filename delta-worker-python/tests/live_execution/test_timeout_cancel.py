"""C-WA-020 .. C-WA-022: Timeout, cancellation, and runner exception behavior."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from deltatorrent.live_execution.dispatch import (
    CancellationToken,
    ClosedEnumWorkerDispatcher,
)
from deltatorrent.live_execution.errors import (
    WorkerCancelledError,
    WorkerTimeoutError,
)
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)


@pytest.fixture
def train_bundle() -> dict:
    bundle_path = CONTRACTS_ROOT / "fixtures" / "valid" / "authorized-execution.train-ticket.json"
    with bundle_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_c_wa_020_timeout_prevents_receipt_emission(train_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    # Set timeout to 0 or 1s with a slow mock runner
    import time

    slow_runner = MagicMock()

    def slow_train(*args, **kwargs):
        time.sleep(2)
        return MagicMock()

    slow_runner.train_ticket.side_effect = slow_train

    fast_ctx = replace(ctx, timeout_seconds=1)
    dispatcher = ClosedEnumWorkerDispatcher()

    with pytest.raises(WorkerTimeoutError) as exc_info:
        dispatcher.dispatch(fast_ctx, runner_override=slow_runner)

    assert exc_info.value.code == "ERR_TIMEOUT"
    # Verify emit_execution_receipt was never called
    slow_runner.emit_execution_receipt.assert_not_called()


def test_c_wa_021_cancellation_prevents_receipt_emission(train_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    token = CancellationToken()
    token.cancel()  # Pre-cancelled token

    mock_runner = MagicMock()
    dispatcher = ClosedEnumWorkerDispatcher()

    with pytest.raises(WorkerCancelledError) as exc_info:
        dispatcher.dispatch(ctx, cancellation_token=token, runner_override=mock_runner)

    assert exc_info.value.code == "ERR_CANCELLED"
    mock_runner.train_ticket.assert_not_called()
    mock_runner.emit_execution_receipt.assert_not_called()


def test_c_wa_020_wall_clock_timeout_does_not_block_on_hanging_thread(
    train_bundle: dict,
) -> None:
    """Prove dispatch() unblocks immediately on timeout without waiting on a hanging runner."""
    import time

    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    hanging_runner = MagicMock()

    def hang(*args, **kwargs):
        time.sleep(10)
        return MagicMock()

    hanging_runner.train_ticket.side_effect = hang
    fast_ctx = replace(ctx, timeout_seconds=1)
    dispatcher = ClosedEnumWorkerDispatcher()

    start_time = time.monotonic()
    with pytest.raises(WorkerTimeoutError) as exc_info:
        dispatcher.dispatch(fast_ctx, runner_override=hanging_runner)
    elapsed = time.monotonic() - start_time

    assert exc_info.value.code == "ERR_TIMEOUT"
    assert elapsed < 3.0, f"Dispatch waited {elapsed:.2f}s instead of returning promptly on timeout"
    hanging_runner.emit_execution_receipt.assert_not_called()
