"""T012: Caller authentication and role-based policy evaluation."""

from __future__ import annotations

import pytest
from deltacontroller.auth import (
    AuthenticatedSubject,
    PolicyEngine,
    StaticAuthenticationPort,
)
from deltacontroller.errors import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    RoleForbiddenError,
)


def test_missing_credentials_raises_auth_required() -> None:
    port = StaticAuthenticationPort()
    with pytest.raises(AuthenticationRequiredError):
        port.authenticate(None)


def test_token_authentication_success() -> None:
    expected_subject = AuthenticatedSubject(
        subject_id="operator.corp",
        authenticated_via="TOKEN",
        effective_roles=["OPERATOR"],
    )
    port = StaticAuthenticationPort(token_map={"valid-secret-token": expected_subject})
    subject = port.authenticate({"type": "TOKEN", "token": "valid-secret-token"})
    assert subject.subject_id == "operator.corp"
    assert "OPERATOR" in subject.effective_roles


def test_invalid_token_raises_auth_failed() -> None:
    port = StaticAuthenticationPort(token_map={})
    with pytest.raises(AuthenticationFailedError):
        port.authenticate({"type": "TOKEN", "token": "wrong-token"})


def test_local_peer_authentication() -> None:
    port = StaticAuthenticationPort(allow_local_peer=True)
    subject = port.authenticate(
        {
            "type": "LOCAL_PEER_CREDENTIAL",
            "subject_id": "operator.local",
            "roles": ["OPERATOR"],
        }
    )
    assert subject.subject_id == "operator.local"
    assert subject.authenticated_via == "LOCAL_PEER_CREDENTIAL"


def test_policy_allows_operator_for_train_ticket() -> None:
    engine = PolicyEngine()
    subject = AuthenticatedSubject("op1", "LOCAL_PEER_CREDENTIAL", ["OPERATOR"])
    intent_doc = {"operation": "TRAIN_TICKET"}
    engine.evaluate_admission(subject, intent_doc)  # Should not raise


def test_policy_forbids_researcher_from_train_ticket() -> None:
    engine = PolicyEngine()
    # RESEARCHER role alone cannot authorize TRAIN_TICKET
    subject = AuthenticatedSubject("res1", "LOCAL_PEER_CREDENTIAL", ["RESEARCHER"])
    intent_doc = {"operation": "TRAIN_TICKET"}
    with pytest.raises(RoleForbiddenError) as exc_info:
        engine.evaluate_admission(subject, intent_doc)
    assert exc_info.value.code == "ERR_ROLE_FORBIDDEN"


def test_policy_allows_researcher_for_evaluate_checkpoint() -> None:
    engine = PolicyEngine()
    subject = AuthenticatedSubject("res1", "LOCAL_PEER_CREDENTIAL", ["RESEARCHER"])
    intent_doc = {"operation": "EVALUATE_CHECKPOINT"}
    engine.evaluate_admission(subject, intent_doc)  # Should not raise
