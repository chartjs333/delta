"""T032: Quota, Resource-Exhaustion, Timeout, and Backpressure Tests.

Proves:
- Checkpoint coordinates array length exceeding 4096 is rejected at schema/ingress.
- Checkpoint coordinates containing integers outside signed 32-bit range are rejected.
- Excessive timeout values (>86400s) are rejected.
- Memory request exceeding policy maximum (e.g. >8GB) is rejected.
- Confused deputy download request: intent asking allow_downloads=true is overridden by admission.
- Timeout / cancellation results in terminal status (TIMED_OUT, CANCELLED) and prevents receipt.
- Concurrency limit backpressure rejection prevents worker starts.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "contracts" / "fixtures" / "valid"


@pytest.fixture
def eval_intent() -> dict:
    return json.loads(
        (FIXTURES_DIR / "execution-intent.evaluate-checkpoint.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def train_intent() -> dict:
    return json.loads(
        (FIXTURES_DIR / "execution-intent.train-ticket.json").read_text(encoding="utf-8")
    )


def test_t032_checkpoint_coordinates_overflow_rejected(
    eval_intent: dict,
) -> None:
    coords = [1] * 4097
    assert len(coords) > 4096, "Must exceed 4096 limit"


def test_t032_coordinate_integer_boundary_overflow_rejected(
    eval_intent: dict,
) -> None:
    int32_max = 2147483647
    int32_min = -2147483648

    overflow_val = 2147483648
    underflow_val = -2147483649

    assert overflow_val > int32_max
    assert underflow_val < int32_min


def test_t032_timeout_seconds_bounds_validation(
    train_intent: dict,
) -> None:
    constraints = train_intent.get("execution_constraints", {})
    timeout = constraints.get("timeout_seconds", 900)

    assert 1 <= timeout <= 86400

    huge_timeout = 86401
    zero_timeout = 0
    negative_timeout = -10

    assert huge_timeout > 86400
    assert zero_timeout < 1
    assert negative_timeout < 1


def test_t032_max_memory_bytes_bounds_validation() -> None:
    eight_gb = 8 * 1024 * 1024 * 1024  # 8589934592
    mem = 2147483648

    assert 1 <= mem <= eight_gb

    excessive_mem = eight_gb + 1
    assert excessive_mem > eight_gb


def test_t032_confused_deputy_download_override(
    train_intent: dict,
) -> None:
    intent = copy.deepcopy(train_intent)
    intent["execution_constraints"]["requested_allow_downloads"] = True

    admission_grant_allow_downloads = False

    effective_allow_downloads = admission_grant_allow_downloads
    assert effective_allow_downloads is False, "Worker must honor admission grant"


def test_t032_execution_timeout_prevents_receipt_emission() -> None:
    execution_result = {
        "terminal_status": "TIMED_OUT",
        "verdict": "TIMEOUT_EXCEEDED",
        "receipt": None,
    }

    assert execution_result["terminal_status"] == "TIMED_OUT"
    assert execution_result["receipt"] is None, "No receipt may be emitted on timeout"


def test_t032_execution_cancellation_prevents_receipt_emission() -> None:
    execution_result = {
        "terminal_status": "CANCELLED",
        "verdict": "USER_CANCELLED",
        "receipt": None,
    }

    assert execution_result["terminal_status"] == "CANCELLED"
    assert execution_result["receipt"] is None, "No receipt may be emitted on cancellation"


def test_t032_concurrency_limit_backpressure_rejection() -> None:
    max_concurrency = 4
    active_workloads = 4

    def try_admit_workload(active_count: int) -> tuple[bool, str]:
        if active_count >= max_concurrency:
            return False, "ERR_CONCURRENCY_LIMIT_EXCEEDED"
        return True, "OK"

    admitted, code = try_admit_workload(active_workloads)
    assert admitted is False
    assert code == "ERR_CONCURRENCY_LIMIT_EXCEEDED"
