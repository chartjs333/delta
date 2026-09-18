"""T032: production quota, resource-exhaustion, timeout and cancellation tests."""

from __future__ import annotations

import copy
import time
from dataclasses import replace
from unittest.mock import MagicMock

import pytest
from deltacontroller.canonical import compute_intent_digest
from deltacontroller.errors import QuotaExceededError, SchemaValidationError
from deltacontroller.ingress import IngressParser
from deltacontroller.quota import CEILING_MAX_MEMORY_BYTES, QuotaManager
from deltatorrent.live_execution.dispatch import CancellationToken, ClosedEnumWorkerDispatcher
from deltatorrent.live_execution.errors import WorkerCancelledError, WorkerTimeoutError
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight
from security_support import (
    CURRENT_TIME,
    admit_train_ticket,
    build_gate_harness,
    load_valid_fixture,
)


@pytest.fixture
def eval_intent() -> dict:
    return load_valid_fixture("execution-intent.evaluate-checkpoint.json")


@pytest.fixture
def train_intent() -> dict:
    return load_valid_fixture("execution-intent.train-ticket.json")


def test_t032_checkpoint_coordinates_length_rejected_by_production_schema(
    eval_intent: dict,
) -> None:
    intent = copy.deepcopy(eval_intent)
    intent["operation_payload"]["checkpoint_coordinates"] = [0] * 4097

    with pytest.raises(SchemaValidationError) as exc_info:
        IngressParser().parse_intent(intent, current_time=CURRENT_TIME)

    assert exc_info.value.code == "ERR_SCHEMA_VALIDATION_FAILED"
    assert "checkpoint_coordinates" in str(exc_info.value)


def test_t032_coordinate_int32_overflow_rejected_by_production_schema(
    eval_intent: dict,
) -> None:
    parser = IngressParser()
    for bad_value in (2147483648, -2147483649):
        intent = copy.deepcopy(eval_intent)
        intent["operation_payload"]["checkpoint_coordinates"] = [bad_value]
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.parse_intent(intent, current_time=CURRENT_TIME)
        assert exc_info.value.code == "ERR_SCHEMA_VALIDATION_FAILED"


def test_t032_timeout_seconds_max_3600_enforced_by_schema_and_quota(
    train_intent: dict,
) -> None:
    parser = IngressParser()
    too_large = copy.deepcopy(train_intent)
    too_large["execution_constraints"]["timeout_seconds"] = 3601

    with pytest.raises(SchemaValidationError) as schema_exc:
        parser.parse_intent(too_large, current_time=CURRENT_TIME)
    assert schema_exc.value.code == "ERR_SCHEMA_VALIDATION_FAILED"

    with pytest.raises(QuotaExceededError) as quota_exc:
        QuotaManager().evaluate_grants(
            {"execution_constraints": {"timeout_seconds": 3601}},
            current_active_count=0,
        )
    assert quota_exc.value.code == "ERR_QUOTA_EXCEEDED"


def test_t032_memory_grant_above_eight_gb_rejected_by_quota(
    train_intent: dict,
) -> None:
    manager = QuotaManager(default_memory_bytes=CEILING_MAX_MEMORY_BYTES + 1)

    with pytest.raises(QuotaExceededError) as exc_info:
        manager.evaluate_grants(train_intent, current_active_count=0)

    assert exc_info.value.code == "ERR_QUOTA_EXCEEDED"
    assert exc_info.value.details["max_memory"] == CEILING_MAX_MEMORY_BYTES


def test_t032_concurrency_backpressure_rejection_starts_no_worker(
    train_intent: dict,
) -> None:
    harness = build_gate_harness(quota_manager=QuotaManager(max_concurrency=0))

    with pytest.raises(QuotaExceededError) as exc_info:
        admit_train_ticket(harness, train_intent)

    assert exc_info.value.code == "ERR_QUOTA_EXCEEDED"
    assert len(harness.dispatch_port.dispatched_bundles) == 0
    assert harness.ledger.get_by_intent_id(train_intent["intent_id"]) is None


def test_t032_confused_deputy_download_request_uses_admission_grant(
    train_intent: dict,
) -> None:
    intent = copy.deepcopy(train_intent)
    intent["execution_constraints"]["requested_allow_downloads"] = True
    intent["intent_digest"] = compute_intent_digest(intent)
    harness = build_gate_harness()

    result = admit_train_ticket(harness, intent)
    bundle = result["bundle"]
    preflight = AuthorizedExecutionPreflight(
        trusted_keys={bundle["admission"]["authenticator"]["key_id"]: harness.public_key_hex}
    )
    ctx = preflight.validate(bundle, current_time=CURRENT_TIME)

    assert bundle["intent"]["execution_constraints"]["requested_allow_downloads"] is True
    assert bundle["admission"]["resource_grants"]["allow_downloads"] is False
    assert ctx.allow_downloads is False


def test_t032_worker_timeout_prevents_success_receipt_emission(
    train_intent: dict,
) -> None:
    harness = build_gate_harness()
    bundle = admit_train_ticket(harness, train_intent)["bundle"]
    preflight = AuthorizedExecutionPreflight(
        trusted_keys={bundle["admission"]["authenticator"]["key_id"]: harness.public_key_hex}
    )
    ctx = preflight.validate(bundle, current_time=CURRENT_TIME)
    fast_ctx = replace(ctx, timeout_seconds=1)

    slow_runner = MagicMock()

    def slow_train(*args, **kwargs):
        time.sleep(2)
        return MagicMock(metadata={})

    slow_runner.train_ticket.side_effect = slow_train

    with pytest.raises(WorkerTimeoutError) as exc_info:
        ClosedEnumWorkerDispatcher().dispatch(fast_ctx, runner_override=slow_runner)

    assert exc_info.value.code == "ERR_TIMEOUT"
    slow_runner.emit_execution_receipt.assert_not_called()


def test_t032_worker_cancellation_prevents_success_receipt_emission(
    train_intent: dict,
) -> None:
    harness = build_gate_harness()
    bundle = admit_train_ticket(harness, train_intent)["bundle"]
    preflight = AuthorizedExecutionPreflight(
        trusted_keys={bundle["admission"]["authenticator"]["key_id"]: harness.public_key_hex}
    )
    ctx = preflight.validate(bundle, current_time=CURRENT_TIME)

    token = CancellationToken()
    token.cancel()
    mock_runner = MagicMock()

    with pytest.raises(WorkerCancelledError) as exc_info:
        ClosedEnumWorkerDispatcher().dispatch(
            ctx,
            cancellation_token=token,
            runner_override=mock_runner,
        )

    assert exc_info.value.code == "ERR_CANCELLED"
    mock_runner.train_ticket.assert_not_called()
    mock_runner.emit_execution_receipt.assert_not_called()
