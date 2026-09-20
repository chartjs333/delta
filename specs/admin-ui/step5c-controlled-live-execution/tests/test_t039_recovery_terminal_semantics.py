"""T039: Recovery, idempotency, duplicate submit, timeout/cancel, and terminal semantics tests."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
from deltacontroller.canonical import compute_intent_digest
from deltacontroller.errors import (
    IntentCollisionDetectedError,
    IntentIdDigestConflictError,
    UnauthorizedCallerError,
)
from deltatorrent.live_execution.dispatch import CancellationToken
from deltatorrent.live_execution.errors import WorkerTimeoutError
from e2e_support import (
    CURRENT_TIME,
    build_integrated_gate,
    operator_credentials,
    rebuild_gate,
)


def _make_intent(
    intent_id: str = "11111111-1111-4111-8111-111111111111",
    ticket_id: str = "ticket_001",
    retry_of: str | None = None,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    constraints: dict[str, Any] = {
        "timeout_seconds": timeout_seconds,
        "requested_allow_downloads": False,
    }
    if retry_of:
        constraints["retry_of_intent_id"] = retry_of

    doc = {
        "schema_version": "1.0.0",
        "intent_id": intent_id,
        "created_at": "2026-09-17T14:30:00+00:00",
        "expires_at": "2026-09-17T14:40:00+00:00",
        "declared_operator": {
            "role": "OPERATOR",
            "subject_id": "operator.alpha",
        },
        "workload": {
            "model_plugin_id": "tabular-10gene-phenotype-v1",
            "dataset_id": "synthetic-10gene-cohort-v1",
            "requested_scope": "PLUGIN_BOUNDARY",
            "catalog_backend_ref": "670b58f6458fe84620f4f9f46401f855d04ae05d",
        },
        "operation": "TRAIN_TICKET",
        "operation_payload": {
            "ticket_id": ticket_id,
            "partition_id": "partition_00",
        },
        "execution_constraints": constraints,
    }
    doc["intent_digest"] = compute_intent_digest(doc)
    return doc


def test_t039_restart_recovery_and_cached_terminal_receipt(tmp_path: Path) -> None:
    """Prove restart recovers execution status and cached terminal receipt across reboot."""
    ledger_file = tmp_path / "idempotency_ledger.json"
    harness = build_integrated_gate(ledger_file)
    gate_1 = harness.gate

    intent = _make_intent(intent_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    creds = operator_credentials()

    res_1 = gate_1.admit_and_dispatch(intent, credentials=creds, current_time=CURRENT_TIME)
    assert res_1["status"]["state"] == "COMPLETED"
    exec_id = res_1["admission"]["execution_id"]
    receipt_1 = copy.deepcopy(res_1["receipt"])
    assert receipt_1 is not None
    assert harness.dispatch_port.dispatch_count == 1

    # Returned artifacts are copies: caller mutation cannot alter durable cache.
    res_1["receipt"]["execution"]["verdict"] = "FAILED"
    stored = gate_1.idempotency_ledger.get_by_execution_id(exec_id)
    assert stored is not None
    assert stored.terminal_receipt == receipt_1

    # Simulate Controller Crash / Reboot: Instantiate completely fresh Gate from disk ledger
    gate_2 = rebuild_gate(harness, ledger_file)

    # 1. Direct query by execution_id recovers exact status & receipt
    status_recovered = gate_2.get_status(exec_id, credentials=creds)
    assert status_recovered is not None
    assert status_recovered["state"] == "COMPLETED"
    assert status_recovered["terminal"] is True
    assert status_recovered["execution_id"] == exec_id
    assert status_recovered["intent_id"] == intent["intent_id"]
    assert gate_2.get_receipt(exec_id, credentials=creds) == receipt_1
    with pytest.raises(UnauthorizedCallerError):
        gate_2.get_status(exec_id, credentials=operator_credentials("operator.beta"))
    with pytest.raises(UnauthorizedCallerError):
        gate_2.get_receipt(exec_id, credentials=operator_credentials("operator.beta"))

    rec_recovered = gate_2.idempotency_ledger.get_by_execution_id(exec_id)
    assert rec_recovered is not None
    assert rec_recovered.terminal_receipt == receipt_1

    # 2. Duplicate submission recovers ALREADY_ADMITTED with cached receipt without re-dispatching
    res_dup = gate_2.admit_and_dispatch(
        intent,
        credentials=creds,
        current_time=CURRENT_TIME,
    )
    assert res_dup["action"] == "ALREADY_ADMITTED"
    assert res_dup["status"]["state"] == "COMPLETED"
    assert res_dup["receipt"] == receipt_1
    assert harness.dispatch_port.dispatch_count == 1


def test_t039_duplicate_submit_and_conflict_rejection(tmp_path: Path) -> None:
    """Prove fail-closed rejection of conflicting intent duplicates and caller hijacking."""
    gate = build_integrated_gate(tmp_path / "ledger.json").gate

    intent_a = _make_intent(
        intent_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", ticket_id="ticket_orig"
    )
    creds_alpha = operator_credentials()

    res_a = gate.admit_and_dispatch(
        intent_a,
        credentials=creds_alpha,
        current_time=CURRENT_TIME,
    )
    assert res_a["status"]["state"] == "COMPLETED"

    # Case 1: Same intent_id, modified content (digest conflict) -> ERR_INTENT_ID_DIGEST_CONFLICT
    conflicting_intent = copy.deepcopy(intent_a)
    conflicting_intent["operation_payload"]["ticket_id"] = "ticket_modified"
    conflicting_intent["intent_digest"] = compute_intent_digest(conflicting_intent)

    with pytest.raises(IntentIdDigestConflictError):
        gate.admit_and_dispatch(
            conflicting_intent,
            credentials=creds_alpha,
            current_time=CURRENT_TIME,
        )

    # Case 2: Same intent_id, different caller (caller hijacking) -> ERR_UNAUTHORIZED_CALLER
    creds_beta = operator_credentials("operator.beta")
    with pytest.raises(UnauthorizedCallerError):
        gate.admit_and_dispatch(
            intent_a,
            credentials=creds_beta,
            current_time=CURRENT_TIME,
        )

    # Case 3: Different intent_id, same digest (unauthorized collision)
    with pytest.raises(IntentCollisionDetectedError):
        gate.idempotency_ledger.check_intent(
            intent_id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            intent_digest=intent_a["intent_digest"],
            caller_subject_id="operator.alpha",
        )


def test_t039_cancellation_and_fresh_intent_retry(tmp_path: Path) -> None:
    """Prove cancellation yields terminal CANCELLED state and retry requires fresh intent."""
    cancel_token = CancellationToken()
    cancel_token.cancel()  # Pre-cancel to simulate cancel signal during dispatch
    harness = build_integrated_gate(
        tmp_path / "ledger.json",
        cancellation_token=cancel_token,
    )
    gate = harness.gate
    dispatch_port = harness.dispatch_port

    intent_1 = _make_intent(intent_id="dddddddd-dddd-4ddd-8ddd-dddddddddddd")
    creds = operator_credentials()

    res_cancel = gate.admit_and_dispatch(
        intent_1,
        credentials=creds,
        current_time=CURRENT_TIME,
    )
    assert res_cancel["status"]["state"] == "CANCELLED"
    assert res_cancel["status"]["terminal"] is True
    assert res_cancel["status"]["error"]["error_code"] == "ERR_CANCELLED"
    assert res_cancel["receipt"] is None
    assert dispatch_port.dispatch_count == 1

    # Re-submitting cancelled intent returns cached CANCELLED status (terminal is immutable)
    res_re = gate.admit_and_dispatch(
        intent_1,
        credentials=creds,
        current_time=CURRENT_TIME,
    )
    assert res_re["action"] == "ALREADY_ADMITTED"
    assert res_re["status"]["state"] == "CANCELLED"
    assert dispatch_port.dispatch_count == 1

    # Retrying requires fresh intent with retry_of_intent_id pointing to cancelled intent
    fresh_cancel_token = CancellationToken()  # Normal non-cancelled token
    dispatch_port.cancellation_token = fresh_cancel_token

    retry_intent = _make_intent(
        intent_id="eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
        retry_of=intent_1["intent_id"],
    )
    res_retry = gate.admit_and_dispatch(
        retry_intent,
        credentials=creds,
        current_time=CURRENT_TIME,
    )
    assert res_retry["action"] == "ADMITTED"
    assert res_retry["status"]["state"] == "COMPLETED"
    assert res_retry["receipt"] is not None
    assert res_retry["receipt"]["provenance"]["intent_id"] == retry_intent["intent_id"]
    assert dispatch_port.dispatch_count == 2


def test_t039_timeout_is_terminal_and_restart_safe(tmp_path: Path) -> None:
    """Prove timeout persists without a receipt and is recovered after restart."""

    class TimeoutDispatcher:
        def dispatch(
            self,
            context: Any,
            cancellation_token: Any = None,
            producer_commit: str | None = None,
        ) -> dict[str, Any]:
            raise WorkerTimeoutError(
                "Synthetic bounded timeout",
                details={"execution_id": context.execution_id},
            )

    ledger_path = tmp_path / "timeout-ledger.jsonl"
    harness = build_integrated_gate(ledger_path, dispatcher=TimeoutDispatcher())
    intent = _make_intent(intent_id="ffffffff-ffff-4fff-8fff-ffffffffffff")
    credentials = operator_credentials()

    result = harness.gate.admit_and_dispatch(
        intent,
        credentials=credentials,
        current_time=CURRENT_TIME,
    )
    execution_id = result["status"]["execution_id"]

    assert result["status"]["state"] == "TIMED_OUT"
    assert result["status"]["terminal"] is True
    assert result["status"]["error"]["error_code"] == "ERR_TIMEOUT"
    assert result["receipt"] is None
    assert harness.dispatch_port.dispatch_count == 1

    restarted_gate = rebuild_gate(harness, ledger_path)
    recovered = restarted_gate.get_status(execution_id, credentials=credentials)
    assert recovered is not None
    assert recovered["state"] == "TIMED_OUT"
    assert recovered["error"]["error_code"] == "ERR_TIMEOUT"
