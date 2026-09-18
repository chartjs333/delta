"""T014: Append-only Idempotency Ledger and collision detection."""

from __future__ import annotations

import os

import pytest
from deltacontroller.errors import (
    IntentCollisionDetectedError,
    IntentIdDigestConflictError,
    UnauthorizedCallerError,
)
from deltacontroller.idempotency import IdempotencyLedger


def test_first_submission_returns_none() -> None:
    ledger = IdempotencyLedger()
    result = ledger.check_intent(
        intent_id="11111111-1111-4111-8111-111111111111",
        intent_digest="sha256:aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000",
        caller_subject_id="operator.alpha",
    )
    assert result is None


def test_identical_resubmission_returns_existing_record() -> None:
    ledger = IdempotencyLedger()
    intent_id = "11111111-1111-4111-8111-111111111111"
    digest = "sha256:aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000"
    subject = "operator.alpha"
    exec_id = "55555555-5555-4555-8555-555555555555"

    ledger.record_admission(intent_id, digest, subject, exec_id, {"admission_id": "adm-1"})

    # Check identical re-submission
    existing = ledger.check_intent(intent_id, digest, subject)
    assert existing is not None
    assert existing.intent_id == intent_id
    assert existing.execution_id == exec_id


def test_intent_id_digest_conflict_rejected() -> None:
    ledger = IdempotencyLedger()
    intent_id = "11111111-1111-4111-8111-111111111111"
    digest1 = "sha256:aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000"
    digest2 = "sha256:bbbb0000bbbb0000bbbb0000bbbb0000bbbb0000bbbb0000bbbb0000bbbb0000"
    subject = "operator.alpha"

    ledger.record_admission(intent_id, digest1, subject, "exec-1", {})

    # Re-submitting same intent_id with modified payload (different digest)
    with pytest.raises(IntentIdDigestConflictError) as exc_info:
        ledger.check_intent(intent_id, digest2, subject)
    assert exc_info.value.code == "ERR_INTENT_ID_DIGEST_CONFLICT"


def test_cross_subject_access_rejected() -> None:
    ledger = IdempotencyLedger()
    intent_id = "11111111-1111-4111-8111-111111111111"
    digest = "sha256:aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000"

    ledger.record_admission(intent_id, digest, "operator.alpha", "exec-1", {})

    # Different caller attempts to replay or query the same intent_id
    with pytest.raises(UnauthorizedCallerError) as exc_info:
        ledger.check_intent(intent_id, digest, "operator.beta")
    assert exc_info.value.code == "ERR_UNAUTHORIZED_CALLER"


def test_fail_closed_intent_collision_rejected() -> None:
    ledger = IdempotencyLedger()
    intent_id1 = "11111111-1111-4111-8111-111111111111"
    intent_id2 = "22222222-2222-4222-8222-222222222222"
    shared_digest = "sha256:cccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc0000"

    ledger.record_admission(intent_id1, shared_digest, "operator.alpha", "exec-1", {})

    # Submitting identical digest under a DIFFERENT intent_id must fail closed
    with pytest.raises(IntentCollisionDetectedError) as exc_info:
        ledger.check_intent(intent_id2, shared_digest, "operator.alpha")
    assert exc_info.value.code == "ERR_INTENT_COLLISION_DETECTED"


def test_persistence_reload_across_restart(tmp_path) -> None:
    file_path = tmp_path / "idempotency.jsonl"
    ledger1 = IdempotencyLedger(persistence_path=file_path)

    intent_id = "11111111-1111-4111-8111-111111111111"
    digest = "sha256:aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000"
    ledger1.record_admission(
        intent_id, digest, "operator.alpha", "exec-1", {"admission_id": "adm-1"}
    )

    # Create new instance pointing to same file
    ledger2 = IdempotencyLedger(persistence_path=file_path)
    existing = ledger2.check_intent(intent_id, digest, "operator.alpha")
    assert existing is not None
    assert existing.execution_id == "exec-1"


def test_commit_durability_failure_does_not_publish_indexes(tmp_path, monkeypatch) -> None:
    file_path = tmp_path / "idempotency.jsonl"
    ledger = IdempotencyLedger(persistence_path=file_path)
    intent_id = "11111111-1111-4111-8111-111111111111"
    digest = "sha256:aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000"
    subject = "operator.alpha"

    state, _ = ledger.acquire_or_check(intent_id, digest, subject)
    assert state == "RESERVED"

    def fail_fsync(_fd: int) -> None:
        raise OSError("synthetic durability barrier failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="durability barrier failure"):
        ledger.commit_admission(
            intent_id,
            digest,
            subject,
            "exec-1",
            {"admission_id": "adm-1"},
        )

    assert ledger.get_by_intent_id(intent_id) is None
    assert ledger.get_by_execution_id("exec-1") is None
    ledger.release_reservation(intent_id)
    with pytest.raises(RuntimeError, match="fail-closed"):
        ledger.acquire_or_check(intent_id, digest, subject, timeout=0.01)

    restarted = IdempotencyLedger(persistence_path=file_path)
    state, existing = restarted.acquire_or_check(intent_id, digest, subject)
    assert state == "COMMITTED"
    assert existing is not None
    assert existing.execution_id == "exec-1"


def test_update_durability_failure_does_not_publish_status(tmp_path, monkeypatch) -> None:
    file_path = tmp_path / "idempotency.jsonl"
    ledger = IdempotencyLedger(persistence_path=file_path)
    intent_id = "11111111-1111-4111-8111-111111111111"
    digest = "sha256:aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000"
    record = ledger.record_admission(
        intent_id,
        digest,
        "operator.alpha",
        "exec-1",
        {"admission_id": "adm-1"},
    )

    def fail_fsync(_fd: int) -> None:
        raise OSError("synthetic status durability barrier failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="status durability barrier failure"):
        ledger.update_execution("exec-1", "RUNNING")

    assert record.status == "ADMITTED"
    assert ledger.get_by_execution_id("exec-1") is record
    with pytest.raises(RuntimeError, match="fail-closed"):
        ledger.acquire_or_check(intent_id, digest, "operator.alpha", timeout=0.01)
