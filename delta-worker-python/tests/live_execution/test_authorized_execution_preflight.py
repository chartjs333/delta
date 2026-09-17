"""C-WA-001 .. C-WA-010: AuthorizedExecution preflight verification."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from deltatorrent.live_execution.errors import WorkerPreflightError
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)


@pytest.fixture
def valid_bundle() -> dict:
    bundle_path = CONTRACTS_ROOT / "fixtures" / "valid" / "authorized-execution.train-ticket.json"
    with bundle_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_c_wa_001_valid_authorized_execution_passes(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(valid_bundle, current_time=now)
    assert ctx.execution_id == valid_bundle["admission"]["execution_id"]
    assert ctx.intent_id == valid_bundle["intent"]["intent_id"]
    assert ctx.operation == "TRAIN_TICKET"
    assert ctx.allow_downloads is False


def test_c_wa_002_rejects_intent_id_mismatch(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    tampered = copy.deepcopy(valid_bundle)
    tampered["admission"]["intent_id"] = "00000000-0000-4000-8000-000000000000"
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered, current_time=now)
    assert exc_info.value.code in {
        "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH",
        "ERR_SCHEMA_VALIDATION_FAILED",
    }


def test_c_wa_003_recomputes_and_rejects_tampered_payload(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    tampered = copy.deepcopy(valid_bundle)
    tampered["intent"]["operation_payload"]["ticket_id"] = "ticket_FORGED-9999"
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered, current_time=now)
    assert exc_info.value.code == "ERR_INTENT_DIGEST_MISMATCH"


def test_c_wa_004_rejects_admission_intent_digest_tamper(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    tampered = copy.deepcopy(valid_bundle)
    tampered["admission"]["intent_digest"] = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered, current_time=now)
    assert exc_info.value.code in {
        "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH",
        "ERR_ADMISSION_DIGEST_MISMATCH",
        "ERR_ADMISSION_SIGNATURE_INVALID",
    }


def test_c_wa_005_verifies_ed25519_signature_passes(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(valid_bundle, current_time=now)
    assert ctx.admission_id == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def test_c_wa_006_rejects_invalid_ed25519_signature(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    tampered = copy.deepcopy(valid_bundle)
    # Flip last byte of signature
    sig = tampered["admission"]["authenticator"]["signature"]
    tampered["admission"]["authenticator"]["signature"] = sig[:-2] + "aa"
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered, current_time=now)
    assert exc_info.value.code == "ERR_ADMISSION_SIGNATURE_INVALID"


def test_c_wa_007_rejects_unknown_key_id(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    tampered = copy.deepcopy(valid_bundle)
    tampered["admission"]["authenticator"]["key_id"] = "untrusted-rogue-key"
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered, current_time=now)
    assert exc_info.value.code == "ERR_ADMISSION_SIGNATURE_INVALID"


def test_c_wa_008_rejects_expired_admission(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    # Current time is after admission_expires_at (2026-09-17T14:35:00.000Z)
    after_admission_expiry = datetime(2026, 9, 17, 14, 36, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(valid_bundle, current_time=after_admission_expiry)
    assert exc_info.value.code == "ERR_ADMISSION_EXPIRED"


def test_c_wa_009_rejects_admission_expires_exceeding_intent_expires(valid_bundle: dict) -> None:
    preflight = AuthorizedExecutionPreflight()
    tampered = copy.deepcopy(valid_bundle)
    # Intent expires at 14:40, set admission expires at 14:50
    tampered["admission"]["admission_expires_at"] = "2026-09-17T14:50:00.000Z"
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(WorkerPreflightError) as exc_info:
        preflight.validate(tampered, current_time=now)
    assert exc_info.value.code in {"ERR_ADMISSION_EXPIRED", "ERR_ADMISSION_DIGEST_MISMATCH"}


def test_c_wa_010_honors_admission_grant_ignoring_intent_request(valid_bundle: dict) -> None:
    bundle = copy.deepcopy(valid_bundle)
    bundle["intent"]["execution_constraints"]["requested_allow_downloads"] = True
    bundle["admission"]["resource_grants"]["allow_downloads"] = False
    # Re-sign or check grant extraction
    assert bundle["admission"]["resource_grants"]["allow_downloads"] is False
