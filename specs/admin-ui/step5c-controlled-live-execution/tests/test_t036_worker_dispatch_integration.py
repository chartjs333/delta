"""T036: Controller -> Worker AuthorizedExecution dispatch & status integration tests."""

from __future__ import annotations

import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from e2e_support import (
    CURRENT_TIME,
    build_integrated_gate,
    operator_credentials,
    rebuild_gate,
)

CONTRACTS_ROOT = Path(__file__).resolve().parents[1] / "contracts"


def test_t036_integrated_worker_dispatch_train_ticket(tmp_path: Path) -> None:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        intent_doc = json.load(f)

    db_path = tmp_path / "idempotency.jsonl"
    harness = build_integrated_gate(db_path)
    gate = harness.gate

    result = gate.admit_and_dispatch(
        intent_doc,
        credentials=operator_credentials(),
        current_time=CURRENT_TIME,
    )
    assert result["action"] == "ADMITTED"
    assert result["status"]["state"] == "COMPLETED"
    assert result["status"]["terminal"] is True
    assert "receipt_digest" in result["status"]
    assert harness.dispatch_port.dispatch_count == 1

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

    db_path = tmp_path / "idempotency_restart.jsonl"
    harness = build_integrated_gate(db_path)
    res1 = harness.gate.admit_and_dispatch(
        intent_doc,
        credentials=operator_credentials(),
        current_time=CURRENT_TIME,
    )
    assert res1["action"] == "ADMITTED"
    assert res1["status"]["state"] == "COMPLETED"

    # Simulate Controller restart by creating fresh gate pointing to same persisted ledger
    gate2 = rebuild_gate(harness, db_path)

    res2 = gate2.admit_and_dispatch(
        intent_doc,
        credentials=operator_credentials(),
        current_time=CURRENT_TIME,
    )
    assert res2["action"] == "ALREADY_ADMITTED"
    assert res2["status"]["state"] == "COMPLETED"
    assert res2["receipt"] == res1["receipt"]
    assert res2["status"]["execution_id"] == res1["status"]["execution_id"]
    assert harness.dispatch_port.dispatch_count == 1


def test_t036_tampered_bundle_fails_at_worker_preflight(tmp_path: Path) -> None:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        intent_doc = json.load(f)

    # Controller uses key A
    key_a = Ed25519PrivateKey.generate()
    # Worker expects key B (untrusted controller simulation)
    key_b = Ed25519PrivateKey.generate()
    harness = build_integrated_gate(
        tmp_path / "tampered-signature.jsonl",
        private_key=key_a,
        worker_public_key_hex=key_b.public_key().public_bytes_raw().hex(),
    )
    res = harness.gate.admit_and_dispatch(
        intent_doc,
        credentials=operator_credentials(),
        current_time=CURRENT_TIME,
    )

    # Admission succeeds in Zone 2, but Zone 3 rejects untrusted signature fail-closed
    assert res["status"]["state"] == "FAILED"
    assert res["status"]["error"]["error_code"] == "ERR_ADMISSION_SIGNATURE_INVALID"
    assert res["receipt"] is None
    assert harness.dispatch_port.dispatch_count == 0
