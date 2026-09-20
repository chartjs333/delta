"""T038: Complete end-to-end lineage proof and tamper rejection across all boundaries."""

from __future__ import annotations

import copy
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from deltacontroller.canonical import (
    compute_admission_digest,
    compute_intent_digest,
    sign_admission,
)
from deltacontroller.gate import AuthorizationGate
from deltacontroller.schema import SchemaRegistry
from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher
from deltatorrent.live_execution.errors import WorkerPreflightError
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight
from e2e_support import CURRENT_TIME, build_integrated_gate, operator_credentials

CONTRACTS_ROOT = Path("specs/admin-ui/step5c-controlled-live-execution/contracts")


@pytest.fixture
def lineage_gate(
    tmp_path: Path,
) -> tuple[AuthorizationGate, AuthorizedExecutionPreflight, str]:
    harness = build_integrated_gate(tmp_path / "lineage.jsonl")
    return harness.gate, harness.preflight, harness.public_key_hex


def _sample_valid_intent() -> dict[str, Any]:
    doc = {
        "schema_version": "1.0.0",
        "intent_id": "33333333-3333-4333-8333-333333333333",
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
            "ticket_id": "ticket_001",
            "partition_id": "partition_00",
        },
        "execution_constraints": {
            "timeout_seconds": 60,
            "requested_allow_downloads": False,
        },
    }
    doc["intent_digest"] = compute_intent_digest(doc)
    return doc


def test_t038_complete_lineage_chain(
    lineage_gate: tuple[AuthorizationGate, AuthorizedExecutionPreflight, str],
) -> None:
    """Prove unbroken intent -> admission -> execution -> receipt lineage chain."""
    gate, _, _ = lineage_gate
    intent = _sample_valid_intent()
    res = gate.admit_and_dispatch(
        intent,
        credentials=operator_credentials(),
        current_time=CURRENT_TIME,
    )
    assert res["status"]["state"] == "COMPLETED"

    admission = res["admission"]
    receipt = res["receipt"]
    status = res["status"]

    # 1. Intent to Admission linkage
    assert admission["intent_id"] == intent["intent_id"]
    assert admission["intent_digest"] == intent["intent_digest"]

    # 2. Admission to Status linkage
    assert status["intent_id"] == intent["intent_id"]
    assert status["intent_digest"] == intent["intent_digest"]
    assert status["admission_id"] == admission["admission_id"]
    assert status["admission_digest"] == admission["admission_digest"]
    assert status["execution_id"] == admission["execution_id"]

    # 3. Receipt Provenance exact lineage linkage
    prov = receipt["provenance"]
    assert prov["intent_id"] == intent["intent_id"]
    assert prov["intent_digest"] == intent["intent_digest"]
    assert prov["admission_id"] == admission["admission_id"]
    assert prov["admission_digest"] == admission["admission_digest"]
    assert prov["execution_id"] == admission["execution_id"]

    # 4. Schema verification of terminal receipt
    registry = SchemaRegistry()
    registry.validate("receipt-lineage", receipt)


def test_t038_tamper_rejection_at_all_boundaries(
    lineage_gate: tuple[AuthorizationGate, AuthorizedExecutionPreflight, str],
) -> None:
    """Prove tamper rejection at every boundary with typed errors and fail-closed isolation."""
    gate, preflight, _ = lineage_gate
    intent = _sample_valid_intent()
    # Create valid bundle without dispatching
    parsed_intent = gate.ingress_parser.parse_intent(intent, current_time=CURRENT_TIME)
    subject = gate.auth_port.authenticate(operator_credentials())
    grants = gate.quota_manager.evaluate_grants(parsed_intent, 0)

    admission_doc = {
        "schema_version": "1.0.0",
        "admission_id": "44444444-4444-4444-8444-444444444444",
        "intent_id": parsed_intent["intent_id"],
        "intent_digest": parsed_intent["intent_digest"],
        "execution_id": "55555555-5555-4555-8555-555555555555",
        "authenticated_subject": subject.to_dict(),
        "policy_context": {
            "policy_version": gate.policy_version,
            "controller_commit": gate.controller_commit,
            "verdict": "ADMITTED",
        },
        "resource_grants": grants.to_dict(),
        "admitted_at": CURRENT_TIME.isoformat(),
        "admission_expires_at": (CURRENT_TIME + timedelta(seconds=300)).isoformat(),
    }
    admission_digest = compute_admission_digest(admission_doc)
    admission_doc["admission_digest"] = admission_digest
    admission_doc["authenticator"] = {
        "algorithm": "ED25519",
        "issuer_id": gate.signing_identity.issuer_id,
        "key_id": gate.signing_identity.key_id,
    }
    admission_doc["authenticator"]["signature"] = sign_admission(
        admission_doc, gate.signing_identity.private_key
    )

    base_bundle = {
        "schema_version": "1.0.0",
        "intent": parsed_intent,
        "admission": admission_doc,
    }

    # Boundary 1: Parity mismatch (intent_id changed in bundle)
    tampered_1 = copy.deepcopy(base_bundle)
    tampered_1["intent"]["intent_id"] = "99999999-9999-4999-8999-999999999999"
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered_1, current_time=CURRENT_TIME)
    assert exc_info.value.code == "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH"

    # Boundary 2: Intent payload tampered (digest mismatch)
    tampered_2 = copy.deepcopy(base_bundle)
    tampered_2["intent"]["operation_payload"]["ticket_id"] = "tampered_ticket"
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered_2, current_time=CURRENT_TIME)
    assert exc_info.value.code == "ERR_INTENT_DIGEST_MISMATCH"

    # Boundary 3: Admission payload tampered (grant elevated, admission digest mismatch)
    tampered_3 = copy.deepcopy(base_bundle)
    tampered_3["admission"]["resource_grants"]["allow_downloads"] = True
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered_3, current_time=CURRENT_TIME)
    assert exc_info.value.code == "ERR_ADMISSION_DIGEST_MISMATCH"

    # Boundary 4: Admission signature tampered / forged
    tampered_4 = copy.deepcopy(base_bundle)
    tampered_4["admission"]["authenticator"]["signature"] = "00" * 64
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered_4, current_time=CURRENT_TIME)
    assert exc_info.value.code == "ERR_ADMISSION_SIGNATURE_INVALID"


def test_t038_tampered_worker_receipt_is_not_published(tmp_path: Path) -> None:
    """Reject a terminal receipt whose provenance diverges after worker execution."""

    class TamperingDispatcher:
        def __init__(self) -> None:
            self._inner = ClosedEnumWorkerDispatcher()

        def dispatch(
            self,
            context: Any,
            cancellation_token: Any = None,
            producer_commit: str | None = None,
        ) -> dict[str, Any]:
            result = copy.deepcopy(
                self._inner.dispatch(
                    context,
                    cancellation_token=cancellation_token,
                    producer_commit=producer_commit,
                )
            )
            result["receipt"]["provenance"]["execution_id"] = "99999999-9999-4999-8999-999999999999"
            return result

    harness = build_integrated_gate(
        tmp_path / "tampered-receipt.jsonl",
        dispatcher=TamperingDispatcher(),
    )
    result = harness.gate.admit_and_dispatch(
        _sample_valid_intent(),
        credentials=operator_credentials(),
        current_time=CURRENT_TIME,
    )

    assert result["status"]["state"] == "FAILED"
    assert result["status"]["error"]["error_code"] == "ERR_RECEIPT_LINEAGE_MISMATCH"
    assert result["receipt"] is None
    assert harness.dispatch_port.dispatch_count == 1
