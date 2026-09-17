"""T016: AuthorizationGate end-to-end admission, Ed25519 signing, status, and audit redaction."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.audit import redact_sensitive_data
from deltacontroller.canonical import verify_admission_signature
from deltacontroller.dispatch import MockWorkerDispatchPort
from deltacontroller.gate import AuthorizationGate

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)


def test_full_authorization_pipeline_success() -> None:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        intent_doc = json.load(f)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    dispatch_mock = MockWorkerDispatchPort()

    gate = AuthorizationGate(
        private_key=private_key,
        dispatch_port=dispatch_mock,
    )

    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    credentials = {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": "operator.alpha",
        "roles": ["OPERATOR"],
    }

    result = gate.admit_and_dispatch(intent_doc, credentials=credentials, current_time=now)
    assert result["action"] == "ADMITTED"

    admission = result["admission"]
    assert admission["schema_version"] == "1.0.0"
    assert admission["intent_id"] == intent_doc["intent_id"]
    assert admission["intent_digest"] == intent_doc["intent_digest"]
    assert admission["policy_context"]["verdict"] == "ADMITTED"

    # Verify Ed25519 signature over admission
    assert verify_admission_signature(admission, public_key) is True

    # Verify deadline invariants
    admitted_at = datetime.fromisoformat(admission["admitted_at"].replace("Z", "+00:00"))
    admission_expires_at = datetime.fromisoformat(
        admission["admission_expires_at"].replace("Z", "+00:00")
    )
    intent_expires_at = datetime.fromisoformat(intent_doc["expires_at"].replace("Z", "+00:00"))

    assert admitted_at <= admission_expires_at
    assert admission_expires_at <= intent_expires_at

    # Verify AuthorizedExecution bundle in dispatch port
    assert len(dispatch_mock.dispatched_bundles) == 1
    bundle = dispatch_mock.dispatched_bundles[0]
    assert bundle["schema_version"] == "1.0.0"
    assert bundle["admission"]["execution_id"] == admission["execution_id"]
    assert bundle["intent"]["intent_id"] == intent_doc["intent_id"]

    # Verify initial status read model
    status = result["status"]
    assert status["schema_version"] == "1.0.0"
    assert status["execution_id"] == admission["execution_id"]
    assert status["state"] == "RUNNING"


def test_audit_sensitive_data_redaction() -> None:
    raw_event = {
        "user": "operator1",
        "token": "secret-bearer-token-12345",
        "password": "super-secret-password",
        "private_key": "raw-key-bytes",
        "nested": {
            "api_key": "key-99999",
            "safe_metric": 42,
        },
    }
    redacted = redact_sensitive_data(raw_event)
    assert redacted["token"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["private_key"] == "[REDACTED]"
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["safe_metric"] == 42
