"""T039: Recovery, idempotency, duplicate submit, timeout/cancel, and terminal semantics tests."""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.canonical import compute_intent_digest
from deltacontroller.dispatch import IntegratedWorkerDispatchPort
from deltacontroller.errors import (
    IntentCollisionDetectedError,
    IntentIdDigestConflictError,
    UnauthorizedCallerError,
)
from deltacontroller.gate import AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger
from deltatorrent.live_execution.dispatch import CancellationToken
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight


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
    private_key = Ed25519PrivateKey.generate()
    pub_hex = private_key.public_key().public_bytes_raw().hex()

    preflight = AuthorizedExecutionPreflight(
        trusted_public_key_hex=pub_hex,
        pinned_key_ids={"step5c-fixture-ed25519"},
    )
    dispatch_port = IntegratedWorkerDispatchPort(preflight=preflight)
    ledger_1 = IdempotencyLedger(persistence_path=ledger_file)
    gate_1 = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger_1,
    )

    intent = _make_intent(intent_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    creds = {"type": "LOCAL_PEER_CREDENTIAL", "subject_id": "operator.alpha", "roles": ["OPERATOR"]}

    res_1 = gate_1.admit_and_dispatch(intent, credentials=creds, current_time=now)
    assert res_1["status"]["state"] == "COMPLETED"
    exec_id = res_1["admission"]["execution_id"]
    receipt_1 = res_1["receipt"]
    assert receipt_1 is not None

    # Simulate Controller Crash / Reboot: Instantiate completely fresh Gate from disk ledger
    ledger_2 = IdempotencyLedger(persistence_path=ledger_file)
    gate_2 = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger_2,
    )

    # 1. Direct query by execution_id recovers exact status & receipt
    status_recovered = gate_2.get_status(exec_id)
    assert status_recovered is not None
    assert status_recovered["state"] == "COMPLETED"
    assert status_recovered["terminal"] is True
    assert status_recovered["execution_id"] == exec_id
    assert status_recovered["intent_id"] == intent["intent_id"]

    rec_recovered = gate_2.idempotency_ledger.get_by_execution_id(exec_id)
    assert rec_recovered is not None
    assert rec_recovered.terminal_receipt == receipt_1

    # 2. Duplicate submission recovers ALREADY_ADMITTED with cached receipt without re-dispatching
    res_dup = gate_2.admit_and_dispatch(intent, credentials=creds, current_time=now)
    assert res_dup["action"] == "ALREADY_ADMITTED"
    assert res_dup["status"]["state"] == "COMPLETED"
    assert res_dup["receipt"] == receipt_1


def test_t039_duplicate_submit_and_conflict_rejection(tmp_path: Path) -> None:
    """Prove fail-closed rejection of conflicting intent duplicates and caller hijacking."""
    private_key = Ed25519PrivateKey.generate()
    pub_hex = private_key.public_key().public_bytes_raw().hex()
    preflight = AuthorizedExecutionPreflight(
        trusted_public_key_hex=pub_hex,
        pinned_key_ids={"step5c-fixture-ed25519"},
    )
    dispatch_port = IntegratedWorkerDispatchPort(preflight=preflight)
    ledger = IdempotencyLedger(persistence_path=tmp_path / "ledger.json")
    gate = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger,
    )

    intent_a = _make_intent(
        intent_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", ticket_id="ticket_orig"
    )
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    creds_alpha = {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": "operator.alpha",
        "roles": ["OPERATOR"],
    }

    res_a = gate.admit_and_dispatch(intent_a, credentials=creds_alpha, current_time=now)
    assert res_a["status"]["state"] == "COMPLETED"

    # Case 1: Same intent_id, modified content (digest conflict) -> ERR_INTENT_ID_DIGEST_CONFLICT
    conflicting_intent = copy.deepcopy(intent_a)
    conflicting_intent["operation_payload"]["ticket_id"] = "ticket_modified"
    conflicting_intent["intent_digest"] = compute_intent_digest(conflicting_intent)

    with pytest.raises(IntentIdDigestConflictError):
        gate.admit_and_dispatch(conflicting_intent, credentials=creds_alpha, current_time=now)

    # Case 2: Same intent_id, different caller (caller hijacking) -> ERR_UNAUTHORIZED_CALLER
    creds_beta = {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": "operator.beta",
        "roles": ["OPERATOR"],
    }
    with pytest.raises(UnauthorizedCallerError):
        gate.admit_and_dispatch(intent_a, credentials=creds_beta, current_time=now)

    # Case 3: Different intent_id, same digest (unauthorized collision)
    with pytest.raises(IntentCollisionDetectedError):
        gate.idempotency_ledger.check_intent(
            intent_id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            intent_digest=intent_a["intent_digest"],
            caller_subject_id="operator.alpha",
        )


def test_t039_cancellation_and_fresh_intent_retry(tmp_path: Path) -> None:
    """Prove cancellation yields terminal CANCELLED state and retry requires fresh intent."""
    private_key = Ed25519PrivateKey.generate()
    pub_hex = private_key.public_key().public_bytes_raw().hex()
    preflight = AuthorizedExecutionPreflight(
        trusted_public_key_hex=pub_hex,
        pinned_key_ids={"step5c-fixture-ed25519"},
    )
    cancel_token = CancellationToken()
    cancel_token.cancel()  # Pre-cancel to simulate cancel signal during dispatch
    dispatch_port = IntegratedWorkerDispatchPort(
        preflight=preflight,
        cancellation_token=cancel_token,
    )
    ledger = IdempotencyLedger(persistence_path=tmp_path / "ledger.json")
    gate = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger,
    )

    intent_1 = _make_intent(intent_id="dddddddd-dddd-4ddd-8ddd-dddddddddddd")
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    creds = {"type": "LOCAL_PEER_CREDENTIAL", "subject_id": "operator.alpha", "roles": ["OPERATOR"]}

    res_cancel = gate.admit_and_dispatch(intent_1, credentials=creds, current_time=now)
    assert res_cancel["status"]["state"] == "CANCELLED"
    assert res_cancel["status"]["terminal"] is True
    assert res_cancel["status"]["error"]["error_code"] == "ERR_CANCELLED"
    assert res_cancel["receipt"] is None

    # Re-submitting cancelled intent returns cached CANCELLED status (terminal is immutable)
    res_re = gate.admit_and_dispatch(intent_1, credentials=creds, current_time=now)
    assert res_re["action"] == "ALREADY_ADMITTED"
    assert res_re["status"]["state"] == "CANCELLED"

    # Retrying requires fresh intent with retry_of_intent_id pointing to cancelled intent
    fresh_cancel_token = CancellationToken()  # Normal non-cancelled token
    dispatch_port.cancellation_token = fresh_cancel_token

    retry_intent = _make_intent(
        intent_id="eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
        retry_of=intent_1["intent_id"],
    )
    res_retry = gate.admit_and_dispatch(retry_intent, credentials=creds, current_time=now)
    assert res_retry["action"] == "ADMITTED"
    assert res_retry["status"]["state"] == "COMPLETED"
    assert res_retry["receipt"] is not None
    assert res_retry["receipt"]["provenance"]["intent_id"] == retry_intent["intent_id"]
