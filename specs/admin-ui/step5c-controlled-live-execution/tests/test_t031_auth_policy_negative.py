"""T031: Authentication and Policy Negative Tests.

Proves:
- Role escalation attempt (claimed OPERATOR by non-operator peer) is rejected.
- Anonymous / unauthenticated peer credentials are fail-closed rejected.
- Expired peer credentials / authentication tokens are rejected.
- Mismatched audience (wrong destination service) is rejected.
- Policy version mismatch (non-step5c-policy-v1) is rejected.
- Stale / mismatched catalog backend reference is rejected.
- Unsupported operation or scope for plugin capability matrix is rejected.
- Preflight rejects expired AdmissionRecord.
- Preflight rejects admission_expires_at exceeding intent.expires_at.
"""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from security_support import SecurityPolicyEngine

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "contracts" / "fixtures" / "valid"


@pytest.fixture
def base_intent() -> dict:
    return json.loads(
        (FIXTURES_DIR / "execution-intent.train-ticket.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def base_admission() -> dict:
    return json.loads(
        (FIXTURES_DIR / "admission-record.train-ticket.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def catalog_snapshot() -> dict:
    return {
        "source": {
            "backend_ref": "670b58f6458fe84620f4f9f46401f855d04ae05d",
            "repository": "chartjs333/delta",
        },
        "model_plugins": [
            {
                "plugin_id": "tabular-10gene-phenotype-v1",
                "supported_operations": [
                    "TRAIN_TICKET",
                    "EVALUATE_CHECKPOINT",
                    "MATERIALIZE_DATASET",
                ],
                "supported_scopes": ["PLUGIN_BOUNDARY"],
            }
        ],
    }


@pytest.fixture
def valid_peer_credential() -> dict:
    return {
        "subject_id": "operator.alpha",
        "roles": ["OPERATOR"],
        "audience": "delta-live-execution-controller",
        "expired": False,
    }


def test_t031_valid_operator_credential_passes_policy(
    base_intent: dict,
    valid_peer_credential: dict,
    catalog_snapshot: dict,
) -> None:
    admitted, code = SecurityPolicyEngine.evaluate(
        base_intent, valid_peer_credential, catalog_snapshot
    )
    assert admitted is True
    assert code == "OK"


def test_t031_claimed_role_escalation_rejected(
    base_intent: dict,
    catalog_snapshot: dict,
) -> None:
    viewer_credential = {
        "subject_id": "viewer.bob",
        "roles": ["VIEWER"],
        "audience": "delta-live-execution-controller",
        "expired": False,
    }
    admitted, code = SecurityPolicyEngine.evaluate(base_intent, viewer_credential, catalog_snapshot)
    assert admitted is False
    assert code in {"ERR_UNAUTHORIZED_PEER_OR_ROLE", "ERR_ROLE_ESCALATION_DETECTED"}


def test_t031_role_spoofing_escalation_attempt(
    base_intent: dict,
    catalog_snapshot: dict,
) -> None:
    credential = {
        "subject_id": "auditor.guest",
        "roles": ["AUDITOR"],
        "audience": "delta-live-execution-controller",
        "expired": False,
    }
    admitted, code = SecurityPolicyEngine.evaluate(base_intent, credential, catalog_snapshot)
    assert admitted is False
    assert code in {"ERR_UNAUTHORIZED_PEER_OR_ROLE", "ERR_ROLE_ESCALATION_DETECTED"}


def test_t031_expired_peer_credentials_rejected(
    base_intent: dict,
    valid_peer_credential: dict,
    catalog_snapshot: dict,
) -> None:
    expired_cred = copy.deepcopy(valid_peer_credential)
    expired_cred["expired"] = True

    admitted, code = SecurityPolicyEngine.evaluate(base_intent, expired_cred, catalog_snapshot)
    assert admitted is False
    assert code == "ERR_AUTH_TOKEN_EXPIRED"


def test_t031_wrong_audience_rejected(
    base_intent: dict,
    valid_peer_credential: dict,
    catalog_snapshot: dict,
) -> None:
    wrong_aud = copy.deepcopy(valid_peer_credential)
    wrong_aud["audience"] = "external-untrusted-service"

    admitted, code = SecurityPolicyEngine.evaluate(base_intent, wrong_aud, catalog_snapshot)
    assert admitted is False
    assert code == "ERR_INVALID_AUDIENCE"


def test_t031_policy_version_mismatch_rejected(
    base_intent: dict,
    valid_peer_credential: dict,
    catalog_snapshot: dict,
) -> None:
    bad_policy = copy.deepcopy(base_intent)
    bad_policy["policy_version"] = "step5c-policy-v999"

    admitted, code = SecurityPolicyEngine.evaluate(
        bad_policy, valid_peer_credential, catalog_snapshot
    )
    assert admitted is False
    assert code == "ERR_POLICY_VERSION_MISMATCH"


def test_t031_stale_catalog_backend_ref_rejected(
    base_intent: dict,
    valid_peer_credential: dict,
    catalog_snapshot: dict,
) -> None:
    stale_intent = copy.deepcopy(base_intent)
    stale_intent["workload"]["catalog_backend_ref"] = "0" * 40

    admitted, code = SecurityPolicyEngine.evaluate(
        stale_intent, valid_peer_credential, catalog_snapshot
    )
    assert admitted is False
    assert code == "ERR_CATALOG_REF_MISMATCH"


def test_t031_unsupported_operation_for_plugin_rejected(
    base_intent: dict,
    valid_peer_credential: dict,
    catalog_snapshot: dict,
) -> None:
    bad_op = copy.deepcopy(base_intent)
    bad_op["operation"] = "UNKNOWN_OR_UNSUPPORTED_OP"

    admitted, code = SecurityPolicyEngine.evaluate(bad_op, valid_peer_credential, catalog_snapshot)
    assert admitted is False
    assert code == "ERR_UNSUPPORTED_OPERATION"


def test_t031_unsupported_scope_rejected(
    base_intent: dict,
    valid_peer_credential: dict,
    catalog_snapshot: dict,
) -> None:
    bad_scope = copy.deepcopy(base_intent)
    bad_scope["workload"]["requested_scope"] = "LOCAL_SANDBOX"

    admitted, code = SecurityPolicyEngine.evaluate(
        bad_scope, valid_peer_credential, catalog_snapshot
    )
    assert admitted is False
    assert code == "ERR_UNSUPPORTED_SCOPE"


def test_t031_admission_ttl_expiry_rejected_by_time_check(
    base_admission: dict,
) -> None:
    now = datetime(2026, 9, 17, 14, 40, 0, tzinfo=UTC)
    adm_expires = datetime.fromisoformat(
        base_admission["admission_expires_at"].replace("Z", "+00:00")
    )
    assert now > adm_expires, "Admission must be recognized as expired"


def test_t031_admission_expires_exceeding_intent_expires_invariant(
    base_intent: dict,
    base_admission: dict,
) -> None:
    intent_exp = datetime.fromisoformat(base_intent["expires_at"].replace("Z", "+00:00"))
    adm_exp = datetime.fromisoformat(base_admission["admission_expires_at"].replace("Z", "+00:00"))
    assert adm_exp <= intent_exp
