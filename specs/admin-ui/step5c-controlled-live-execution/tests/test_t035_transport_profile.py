"""T035: Transport Implementation Profile & Security Boundary verification."""

from __future__ import annotations

import json
from pathlib import Path

from deltacontroller.audit import redact_sensitive_data
from deltacontroller.auth import StaticAuthenticationPort
from deltacontroller.errors import QuotaExceededError
from deltacontroller.gate import AuthorizationGate
from deltacontroller.quota import QuotaManager

SPECS_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_ROOT = SPECS_ROOT / "contracts"


def test_t035_transport_profile_document_exists_and_accepted() -> None:
    profile_path = SPECS_ROOT / "transport-profile.md"
    assert profile_path.is_file()
    text = profile_path.read_text(encoding="utf-8")
    assert "Status**: Accepted" in text
    assert "Zero Consensus Mutation" in text
    assert "Untrusted Client Metadata" in text
    assert "10,485,760 bytes" in text


def test_t035_transport_auth_handoff_and_redaction() -> None:
    # 1. Verify credential verification via auth port
    auth_port = StaticAuthenticationPort()
    creds = {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": "operator.alpha",
        "roles": ["OPERATOR"],
    }
    subject = auth_port.authenticate(creds)
    assert subject.subject_id == "operator.alpha"
    assert "OPERATOR" in subject.effective_roles

    # 2. Verify sensitive credentials redaction
    event = {
        "authorization": "Bearer secret-token-xyz-123",
        "nested": {"token": "secret", "peer_cert": "raw-bytes"},
    }
    redacted = redact_sensitive_data(event)
    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"


def test_t035_transport_backpressure_and_quota_rejection() -> None:
    # Set max concurrent = 1
    quota_mgr = QuotaManager(max_concurrency=1)
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        intent = json.load(f)

    # When active_count reaches 1, next admission must raise QuotaExceededError
    try:
        quota_mgr.evaluate_grants(intent, current_active_count=1)
        raise AssertionError("Expected QuotaExceededError")
    except QuotaExceededError as exc:
        assert exc.code == "ERR_QUOTA_EXCEEDED"


def test_t035_transport_zero_consensus_mutation() -> None:
    # Verify that controller gate never touches consensus state or native imports
    gate = AuthorizationGate()
    assert not hasattr(gate, "wal")
    assert not hasattr(gate, "state_root")
    assert not hasattr(gate, "qc")
    assert not hasattr(gate, "bft_round")
