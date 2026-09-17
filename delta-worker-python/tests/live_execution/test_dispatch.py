"""C-WA-011 .. C-WA-019: Closed enum dispatch and operation adapters."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher
from deltatorrent.live_execution.errors import WorkerDispatchError, WorkerPreflightError
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


def test_c_wa_011_dispatch_table_contains_only_approved_operations() -> None:
    dispatcher = ClosedEnumWorkerDispatcher()
    assert dispatcher.APPROVED_OPERATIONS == {
        "TRAIN_TICKET",
        "EVALUATE_CHECKPOINT",
        "MATERIALIZE_DATASET",
    }


def test_c_wa_014_train_ticket_dispatch_produces_receipt(train_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    dispatcher = ClosedEnumWorkerDispatcher()
    result = dispatcher.dispatch(ctx)

    assert result["status"] == "COMPLETED"
    assert result["operation"] == "TRAIN_TICKET"
    receipt = result["receipt"]
    assert receipt is not None
    assert receipt["receipt_type"] == "DELTAREDUCE_EXECUTION_RECEIPT"
    assert receipt["provenance"]["intent_id"] == ctx.intent_id
    assert receipt["provenance"]["execution_id"] == ctx.execution_id


def test_c_wa_015_train_ticket_rejects_non_plugin_boundary_scope(train_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    tampered = copy.deepcopy(train_bundle)
    tampered["intent"]["workload"]["requested_scope"] = "MODEL_DATASET_BINDING_ONLY"
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered, current_time=now)
    assert exc_info.value.code in {
        "ERR_OPERATION_SCOPE_UNSUPPORTED",
        "ERR_INTENT_DIGEST_MISMATCH",
        "ERR_SCHEMA_VALIDATION_FAILED",
    }


def test_c_wa_018_materialize_dataset_produces_status_only(train_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    # Convert context to MATERIALIZE_DATASET for execution
    from dataclasses import replace

    mat_ctx = replace(ctx, operation="MATERIALIZE_DATASET", operation_payload={})

    dispatcher = ClosedEnumWorkerDispatcher()
    result = dispatcher.dispatch(mat_ctx)

    assert result["status"] == "COMPLETED"
    assert result["operation"] == "MATERIALIZE_DATASET"
    # MATERIALIZE_DATASET emits NO receipt
    assert result["receipt"] is None


def test_c_wa_019_materialize_path_traversal_rejected(train_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    from dataclasses import replace

    bad_ctx = replace(
        ctx, operation="MATERIALIZE_DATASET", operation_payload={"cache_key": "../../escaped_path"}
    )

    dispatcher = ClosedEnumWorkerDispatcher()
    with pytest.raises(WorkerDispatchError, match="Illegal cache_key"):
        dispatcher.dispatch(bad_ctx)
