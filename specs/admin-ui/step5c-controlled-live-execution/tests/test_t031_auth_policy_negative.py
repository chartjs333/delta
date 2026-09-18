"""T031: production authentication and policy negative tests."""

from __future__ import annotations

import copy

import pytest
from deltacontroller.auth import AuthenticatedSubject, PolicyEngine, StaticAuthenticationPort
from deltacontroller.canonical import compute_intent_digest
from deltacontroller.catalog import CatalogValidator
from deltacontroller.errors import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    CatalogRefMismatchError,
    OperationScopeUnsupportedError,
    PolicyDeniedError,
    RoleForbiddenError,
    UnauthorizedCallerError,
)
from security_support import (
    CURRENT_TIME,
    admit_train_ticket,
    build_gate_harness,
    frozen_error_codes,
    load_valid_fixture,
    operator_credentials,
)


@pytest.fixture
def base_intent() -> dict:
    return load_valid_fixture("execution-intent.train-ticket.json")


def assert_frozen_code(code: str) -> None:
    assert code in frozen_error_codes()


def test_t031_declared_operator_cannot_override_authenticated_subject(
    base_intent: dict,
) -> None:
    intent = copy.deepcopy(base_intent)
    intent["declared_operator"] = {
        "subject_id": "attacker.eve",
        "role": "OPERATOR",
    }
    intent["intent_digest"] = compute_intent_digest(intent)

    harness = build_gate_harness()
    result = admit_train_ticket(
        harness,
        intent,
        credentials=operator_credentials("operator.alpha", ["OPERATOR"]),
    )

    subject = result["admission"]["authenticated_subject"]
    assert result["action"] == "ADMITTED"
    assert subject["subject_id"] == "operator.alpha"
    assert subject["subject_id"] != intent["declared_operator"]["subject_id"]
    assert len(harness.dispatch_port.dispatched_bundles) == 1


def test_t031_claimed_role_escalation_rejected_by_production_policy(
    base_intent: dict,
) -> None:
    intent = copy.deepcopy(base_intent)
    intent["declared_operator"] = {
        "subject_id": "attacker.eve",
        "role": "OPERATOR",
    }
    intent["intent_digest"] = compute_intent_digest(intent)

    harness = build_gate_harness()
    with pytest.raises(RoleForbiddenError) as exc_info:
        admit_train_ticket(
            harness,
            intent,
            credentials=operator_credentials("auditor.guest", ["AUDITOR"]),
        )

    assert exc_info.value.code == "ERR_ROLE_FORBIDDEN"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 0


def test_t031_missing_credentials_fail_closed(
    base_intent: dict,
) -> None:
    harness = build_gate_harness()

    with pytest.raises(AuthenticationRequiredError) as exc_info:
        harness.gate.admit_and_dispatch(
            base_intent,
            credentials=None,
            current_time=CURRENT_TIME,
        )

    assert exc_info.value.code == "ERR_AUTHENTICATION_REQUIRED"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 0


def test_t031_invalid_local_peer_role_rejected_before_policy(
    base_intent: dict,
) -> None:
    harness = build_gate_harness()

    with pytest.raises(AuthenticationFailedError) as exc_info:
        admit_train_ticket(
            harness,
            base_intent,
            credentials=operator_credentials("viewer.bob", ["VIEWER"]),
        )

    assert exc_info.value.code == "ERR_AUTHENTICATION_FAILED"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 0


def test_t031_token_credential_mixup_rejected_as_wrong_caller(
    base_intent: dict,
) -> None:
    token_auth = StaticAuthenticationPort(
        token_map={
            "token-alpha": AuthenticatedSubject(
                "operator.alpha",
                "TOKEN",
                ["OPERATOR"],
            ),
            "token-beta": AuthenticatedSubject(
                "operator.beta",
                "TOKEN",
                ["OPERATOR"],
            ),
        },
        allow_local_peer=False,
    )
    harness = build_gate_harness()
    harness.gate.auth_port = token_auth

    first = harness.gate.admit_and_dispatch(
        base_intent,
        credentials={"type": "TOKEN", "token": "token-alpha"},
        current_time=CURRENT_TIME,
    )
    assert first["action"] == "ADMITTED"

    with pytest.raises(UnauthorizedCallerError) as exc_info:
        harness.gate.admit_and_dispatch(
            base_intent,
            credentials={"type": "TOKEN", "token": "token-beta"},
            current_time=CURRENT_TIME,
        )

    assert exc_info.value.code == "ERR_UNAUTHORIZED_CALLER"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 1


def test_t031_invalid_token_rejected(
    base_intent: dict,
) -> None:
    token_auth = StaticAuthenticationPort(token_map={}, allow_local_peer=False)
    harness = build_gate_harness()
    harness.gate.auth_port = token_auth

    with pytest.raises(AuthenticationFailedError) as exc_info:
        harness.gate.admit_and_dispatch(
            base_intent,
            credentials={"type": "TOKEN", "token": "not-valid"},
            current_time=CURRENT_TIME,
        )

    assert exc_info.value.code == "ERR_AUTHENTICATION_FAILED"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 0


def test_t031_policy_engine_rejects_unknown_operation_without_declared_role_trust() -> None:
    engine = PolicyEngine()
    subject = AuthenticatedSubject("operator.alpha", "LOCAL_PEER_CREDENTIAL", ["OPERATOR"])

    with pytest.raises(PolicyDeniedError) as exc_info:
        engine.evaluate_admission(subject, {"operation": "RUN_ARBITRARY_PYTHON"})

    assert exc_info.value.code == "ERR_POLICY_DENIED"
    assert_frozen_code(exc_info.value.code)


def test_t031_stale_catalog_backend_ref_rejected(
    base_intent: dict,
) -> None:
    stale = copy.deepcopy(base_intent)
    stale["workload"]["catalog_backend_ref"] = "0" * 40
    stale["intent_digest"] = compute_intent_digest(stale)

    harness = build_gate_harness()
    with pytest.raises(CatalogRefMismatchError) as exc_info:
        admit_train_ticket(harness, stale)

    assert exc_info.value.code == "ERR_CATALOG_REF_MISMATCH"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 0


def test_t031_unsupported_scope_rejected_by_capability_matrix(
    base_intent: dict,
) -> None:
    harness = build_gate_harness()
    harness.gate.catalog_validator = CatalogValidator(
        capability_matrix={"TRAIN_TICKET": frozenset({"MODEL_DATASET_BINDING_ONLY"})}
    )

    with pytest.raises(OperationScopeUnsupportedError) as exc_info:
        admit_train_ticket(harness, base_intent)

    assert exc_info.value.code == "ERR_OPERATION_SCOPE_UNSUPPORTED"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 0
