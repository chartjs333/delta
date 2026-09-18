"""T036: Controller -> Worker AuthorizedExecution dispatch & status integration tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.dispatch import IntegratedWorkerDispatchPort
from deltacontroller.gate import AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

CONTRACTS_ROOT = Path(__file__).resolve().parents[1] / "contracts"


def test_t036_integrated_worker_dispatch_train_ticket(tmp_path: Path) -> None:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        intent_doc = json.load(f)

    private_key = Ed25519PrivateKey.generate()
    public_key_hex = private_key.public_key().public_bytes_raw().hex()

    preflight = AuthorizedExecutionPreflight(
        trusted_public_key_hex=public_key_hex,
        pinned_key_ids={"step5c-fixture-ed25519"},
    )
    dispatch_port = IntegratedWorkerDispatchPort(preflight=preflight)

    db_path = tmp_path / "idempotency.jsonl"
    ledger = IdempotencyLedger(persistence_path=db_path)

    gate = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger,
    )

    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    credentials = {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": "operator.alpha",
        "roles": ["OPERATOR"],
    }

    result = gate.admit_and_dispatch(intent_doc, credentials=credentials, current_time=now)
    assert result["action"] == "ADMITTED"
    assert result["status"]["state"] == "COMPLETED"
    assert result["status"]["terminal"] is True
    assert "receipt_digest" in result["status"]

    receipt = result["receipt"]
    assert receipt is not None
    prov = receipt["provenance"]
    assert prov["intent_id"] == intent_doc["intent_id"]
    assert prov["intent_digest"] == intent_doc["intent_digest"]
    assert prov["admission_id"] == result["admission"]["admission_id"]
    assert prov["admission_digest"] == result["admission"]["admission_digest"]
    assert prov["execution_id"] == result["admission"]["execution_id"]


def test_t036_integrated_worker_dispatch_restart_safe_retrieval(tmp_path: Path) -> None:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        intent_doc = json.load(f)

    private_key = Ed25519PrivateKey.generate()
    public_key_hex = private_key.public_key().public_bytes_raw().hex()

    db_path = tmp_path / "idempotency_restart.jsonl"
    ledger1 = IdempotencyLedger(persistence_path=db_path)
    preflight = AuthorizedExecutionPreflight(trusted_public_key_hex=public_key_hex)
    dispatch_port = IntegratedWorkerDispatchPort(preflight=preflight)

    gate1 = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger1,
    )

    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    creds = {"type": "LOCAL_PEER_CREDENTIAL", "subject_id": "operator.alpha", "roles": ["OPERATOR"]}
    res1 = gate1.admit_and_dispatch(intent_doc, credentials=creds, current_time=now)
    assert res1["action"] == "ADMITTED"
    assert res1["status"]["state"] == "COMPLETED"

    # Simulate Controller restart by creating fresh gate pointing to same persisted ledger
    ledger2 = IdempotencyLedger(persistence_path=db_path)
    gate2 = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger2,
    )

    res2 = gate2.admit_and_dispatch(intent_doc, credentials=creds, current_time=now)
    assert res2["action"] == "ALREADY_ADMITTED"
    assert res2["status"]["state"] == "COMPLETED"
    assert res2["receipt"] == res1["receipt"]
    assert res2["status"]["execution_id"] == res1["status"]["execution_id"]


def test_t036_tampered_bundle_fails_at_worker_preflight() -> None:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        intent_doc = json.load(f)

    # Controller uses key A
    key_a = Ed25519PrivateKey.generate()
    # Worker expects key B (untrusted controller simulation)
    key_b = Ed25519PrivateKey.generate()
    pub_b_hex = key_b.public_key().public_bytes_raw().hex()

    preflight = AuthorizedExecutionPreflight(trusted_public_key_hex=pub_b_hex)
    dispatch_port = IntegratedWorkerDispatchPort(preflight=preflight)

    gate = AuthorizationGate(
        private_key=key_a,
        dispatch_port=dispatch_port,
    )

    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    creds = {"type": "LOCAL_PEER_CREDENTIAL", "subject_id": "operator.alpha", "roles": ["OPERATOR"]}
    res = gate.admit_and_dispatch(intent_doc, credentials=creds, current_time=now)

    # Admission succeeds in Zone 2, but Zone 3 rejects untrusted signature fail-closed
    assert res["status"]["state"] == "FAILED"
    assert res["status"]["error"]["error_code"] == "ERR_ADMISSION_SIGNATURE_INVALID"
    assert res["receipt"] is None
