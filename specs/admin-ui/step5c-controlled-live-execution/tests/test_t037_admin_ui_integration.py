"""T037: Admin UI integration and offline adapter independence tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.canonical import compute_intent_digest
from deltacontroller.dispatch import IntegratedWorkerDispatchPort
from deltacontroller.gate import AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger
from deltacontroller.schema import SchemaRegistry
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

CONTRACTS_ROOT = Path("specs/admin-ui/step5c-controlled-live-execution/contracts")


@pytest.fixture
def controller_gate() -> tuple[AuthorizationGate, str]:
    private_key = Ed25519PrivateKey.generate()
    public_key_hex = private_key.public_key().public_bytes_raw().hex()
    preflight = AuthorizedExecutionPreflight(
        trusted_public_key_hex=public_key_hex,
        pinned_key_ids={"step5c-fixture-ed25519"},
    )
    dispatch_port = IntegratedWorkerDispatchPort(preflight=preflight)
    ledger = IdempotencyLedger()
    gate = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_port,
        idempotency_ledger=ledger,
    )
    return gate, public_key_hex


def test_t037_offline_adapter_independence_and_mock_authority() -> None:
    """Validate Admin UI offline mode retains strict zero-egress and presentation mock authority."""
    # Load mock adapter implementation metadata
    mock_adapter_path = Path(
        "tools/admin-ui/src/modules/live-execution/mock-live-execution-adapter.ts"
    )
    assert mock_adapter_path.exists(), "mock-live-execution-adapter.ts must exist"
    content = mock_adapter_path.read_text(encoding="utf-8")

    # Verify adapter properties
    assert 'mode: "MOCK_ONLY"' in content
    assert 'transportProfile: "NONE_PHASE_4"' in content
    assert 'authority: "PRESENTATION_MOCK"' in content
    assert "UNATTESTED_MOCK_STATUS" in content

    # Verify offline boundary test verifies zero network calls
    boundary_test_path = Path(
        "tools/admin-ui/src/modules/live-execution/live-execution-boundary.test.ts"
    )
    assert boundary_test_path.exists(), "live-execution-boundary.test.ts must exist"
    boundary_content = boundary_test_path.read_text(encoding="utf-8")
    assert "expect(fetchSpy).not.toHaveBeenCalled()" in boundary_content


def test_t037_admin_ui_intent_draft_to_controller_live_flow(
    controller_gate: tuple[AuthorizationGate, str],
) -> None:
    """Validate intent drafted by Admin UI intent builder is admitted and executed."""
    gate, _ = controller_gate

    # Simulate intent document produced by Admin UI buildExecutionIntentDocument
    intent_doc = {
        "schema_version": "1.0.0",
        "intent_id": "7a30113c-d38a-4933-bf9c-293ca9feae58",
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
            "ticket_id": "t-alpha-001",
            "partition_id": "p-00",
        },
        "execution_constraints": {
            "timeout_seconds": 60,
            "requested_allow_downloads": False,
        },
    }
    intent_digest = compute_intent_digest(intent_doc)
    intent_doc["intent_digest"] = intent_digest

    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    credentials = {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": "operator.alpha",
        "roles": ["OPERATOR"],
    }

    # Admit and dispatch via AuthorizationGate (Zone 2)
    result = gate.admit_and_dispatch(intent_doc, credentials=credentials, current_time=now)

    assert result["action"] == "ADMITTED"
    status = result["status"]
    assert status["state"] == "COMPLETED"
    assert status["terminal"] is True
    assert status["intent_id"] == intent_doc["intent_id"]
    assert status["intent_digest"] == intent_digest

    # Verify receipt was produced and lineage is intact
    receipt = result["receipt"]
    assert receipt is not None
    prov = receipt["provenance"]
    assert prov["intent_id"] == intent_doc["intent_id"]
    assert prov["intent_digest"] == intent_digest
    assert prov["admission_id"] == result["admission"]["admission_id"]
    assert prov["admission_digest"] == result["admission"]["admission_digest"]
    assert prov["execution_id"] == result["admission"]["execution_id"]


def test_t037_live_receipt_ingestion_and_unattested_plugin_boundary(
    controller_gate: tuple[AuthorizationGate, str],
) -> None:
    """Validate terminal receipt verifies as STRUCTURALLY_VALID_BOUND_RECEIPT."""
    gate, _ = controller_gate

    # 10-gene centroid evaluation: 20 centroid values + 2 presence indicators
    coords = [0] * 20 + [1, 1]
    intent_doc = {
        "schema_version": "1.0.0",
        "intent_id": "8b41224d-e49b-4044-c0ad-304db0afbf69",
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
        "operation": "EVALUATE_CHECKPOINT",
        "operation_payload": {
            "checkpoint_coordinates": coords,
        },
        "execution_constraints": {
            "timeout_seconds": 60,
            "requested_allow_downloads": False,
        },
    }
    intent_digest = compute_intent_digest(intent_doc)
    intent_doc["intent_digest"] = intent_digest

    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    credentials = {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": "operator.alpha",
        "roles": ["OPERATOR"],
    }

    result = gate.admit_and_dispatch(intent_doc, credentials=credentials, current_time=now)
    assert result["status"]["state"] == "COMPLETED"

    receipt = result["receipt"]
    assert receipt is not None
    assert receipt["receipt_type"] == "DELTAREDUCE_EXECUTION_RECEIPT"

    # Validate against frozen schema
    registry = SchemaRegistry()
    registry.validate("receipt-lineage", receipt)

    # Prove no consensus fields (Zone 4 isolation)
    assert "round_id" not in receipt.get("execution", {})
    assert "qc" not in receipt.get("execution", {})
    assert "wal_sequence" not in receipt.get("execution", {})
    assert "round_id" not in receipt.get("provenance", {})
