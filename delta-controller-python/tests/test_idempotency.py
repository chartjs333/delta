"""T014: Append-only Idempotency Ledger and collision detection."""

from __future__ import annotations

import copy
import json
import os

import pytest
from deltacontroller.canonical import canonicalize_jcs, sha256_digest
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


def test_full_intent_persists_and_old_records_remain_readable(tmp_path) -> None:
    path = tmp_path / "ledger.jsonl"
    intent = {"schema_version": "1.0.0", "intent_id": "intent-full"}
    ledger = IdempotencyLedger(path)
    ledger.record_admission(
        "intent-full",
        "sha256:" + "a" * 64,
        "operator.alpha",
        "exec-full",
        {"admission_id": "adm-full"},
        intent=intent,
    )

    restored = IdempotencyLedger(path).get_by_execution_id("exec-full")
    assert restored is not None
    assert restored.intent == intent

    old_path = tmp_path / "old-ledger.jsonl"
    old_record = restored.to_dict()
    old_record.pop("intent")
    old_path.write_text(json.dumps(old_record) + "\n", encoding="utf-8")
    backward_compatible = IdempotencyLedger(old_path).get_by_execution_id("exec-full")
    assert backward_compatible is not None
    assert backward_compatible.intent is None


def test_transition_compare_and_set_and_terminal_immutability(tmp_path) -> None:
    ledger = IdempotencyLedger(tmp_path / "cas-ledger.jsonl")
    record = ledger.record_admission(
        "intent-cas",
        "sha256:" + "b" * 64,
        "operator.alpha",
        "exec-cas",
        {"admission_id": "adm-cas"},
    )
    assert record.status == "ADMITTED"
    assert ledger.transition_execution("exec-cas", {"RUNNING"}, "COMPLETED") is None
    running = ledger.transition_execution("exec-cas", {"ADMITTED"}, "RUNNING")
    assert running is not None and running.status == "RUNNING"
    cancelled = ledger.transition_execution(
        "exec-cas",
        {"RUNNING"},
        "CANCELLED",
        error={"error_code": "ERR_CANCELLED"},
    )
    assert cancelled is not None and cancelled.status == "CANCELLED"

    losing_completion = ledger.transition_execution(
        "exec-cas",
        {"RUNNING"},
        "COMPLETED",
        receipt_digest="sha256:" + "c" * 64,
        terminal_receipt={"must_not": "publish"},
    )
    assert losing_completion is None
    stored = ledger.get_by_execution_id("exec-cas")
    assert stored is not None
    assert stored.status == "CANCELLED"
    assert stored.receipt_digest is None
    assert stored.terminal_receipt is None


def test_list_nonterminal_records_is_defensive_snapshot(tmp_path) -> None:
    ledger = IdempotencyLedger(tmp_path / "list-ledger.jsonl")
    ledger.record_admission(
        "intent-list",
        "sha256:" + "d" * 64,
        "operator.alpha",
        "exec-list",
        {"admission_id": "adm-list"},
        intent={"intent_id": "intent-list"},
    )
    records = ledger.list_nonterminal_records()
    assert [record.execution_id for record in records] == ["exec-list"]
    assert records[0].intent is not None
    records[0].intent["intent_id"] = "mutated"
    stored = ledger.get_by_execution_id("exec-list")
    assert stored is not None and stored.intent == {"intent_id": "intent-list"}


def _replay_snapshots(path, *snapshots: dict) -> IdempotencyLedger:
    path.write_text(
        "".join(json.dumps(snapshot) + "\n" for snapshot in snapshots),
        encoding="utf-8",
    )
    return IdempotencyLedger(path)


def _initial_replay_snapshot() -> dict:
    record = IdempotencyLedger().record_admission(
        "intent-replay",
        "sha256:" + "e" * 64,
        "operator.alpha",
        "exec-replay",
        {"admission_id": "adm-replay", "marker": "original"},
        intent={
            "intent_id": "intent-replay",
            "intent_digest": "sha256:" + "e" * 64,
            "operation": "TRAIN_TICKET",
            "workload": {"dataset_id": "dataset-a"},
        },
        operation="TRAIN_TICKET",
    )
    return record.to_dict()


def test_replay_rejects_unknown_status_and_unknown_snapshot_fields(tmp_path) -> None:
    initial = _initial_replay_snapshot()
    unknown_status = copy.deepcopy(initial)
    unknown_status["status"] = "READY"
    with pytest.raises(ValueError, match="Unknown durable ledger status 'READY'"):
        _replay_snapshots(tmp_path / "unknown-status.jsonl", unknown_status)

    unknown_field = copy.deepcopy(initial)
    unknown_field["unreviewed_state"] = True
    with pytest.raises(ValueError, match="exact schema"):
        _replay_snapshots(tmp_path / "unknown-field.jsonl", unknown_field)


def test_replay_rejects_mutation_of_immutable_execution_context(tmp_path) -> None:
    initial = _initial_replay_snapshot()

    def mutate_subject(snapshot: dict) -> None:
        snapshot["authenticated_subject_id"] = "operator.beta"

    def mutate_operation(snapshot: dict) -> None:
        snapshot["operation"] = "EVALUATE_MODEL"
        snapshot["intent"]["operation"] = "EVALUATE_MODEL"

    def mutate_intent(snapshot: dict) -> None:
        snapshot["intent"]["workload"]["dataset_id"] = "dataset-b"

    def mutate_admission(snapshot: dict) -> None:
        snapshot["admission_record"]["marker"] = "changed"

    for name, mutation in {
        "subject": mutate_subject,
        "operation": mutate_operation,
        "intent": mutate_intent,
        "admission": mutate_admission,
    }.items():
        next_snapshot = copy.deepcopy(initial)
        next_snapshot["status"] = "RUNNING"
        next_snapshot["updated_at"] = "2099-01-01T00:00:00+00:00"
        mutation(next_snapshot)
        with pytest.raises(ValueError, match="Immutable ledger field"):
            _replay_snapshots(tmp_path / f"mutated-{name}.jsonl", initial, next_snapshot)


def test_replay_rejects_illegal_transition_and_terminal_resurrection(tmp_path) -> None:
    initial = _initial_replay_snapshot()
    queued = copy.deepcopy(initial)
    queued["status"] = "QUEUED"
    queued["updated_at"] = "2099-01-01T00:00:00+00:00"
    resurrected_admission = copy.deepcopy(queued)
    resurrected_admission["status"] = "ADMITTED"
    resurrected_admission["updated_at"] = "2099-01-01T00:00:01+00:00"
    with pytest.raises(ValueError, match="Illegal ledger status transition QUEUED -> ADMITTED"):
        _replay_snapshots(
            tmp_path / "illegal-transition.jsonl",
            initial,
            queued,
            resurrected_admission,
        )

    running = copy.deepcopy(initial)
    running["status"] = "RUNNING"
    running["updated_at"] = "2099-01-01T00:00:00+00:00"
    completed = copy.deepcopy(running)
    completed["status"] = "CANCELLED"
    completed["updated_at"] = "2099-01-01T00:00:01+00:00"
    completed["error"] = {"error_code": "ERR_CANCELLED"}
    resurrected_running = copy.deepcopy(running)
    resurrected_running["updated_at"] = "2099-01-01T00:00:02+00:00"
    with pytest.raises(ValueError, match="Terminal ledger history"):
        _replay_snapshots(
            tmp_path / "terminal-resurrection.jsonl",
            initial,
            running,
            completed,
            resurrected_running,
        )


def test_replay_rejects_forged_completed_receipt_and_digest(tmp_path) -> None:
    initial = _initial_replay_snapshot()
    forged = copy.deepcopy(initial)
    forged["status"] = "COMPLETED"
    forged["updated_at"] = "2099-01-01T00:00:00+00:00"
    forged["terminal_receipt"] = {"forged": True}
    forged["receipt_digest"] = "sha256:" + "f" * 64
    with pytest.raises(ValueError, match="receipt_digest does not match"):
        _replay_snapshots(tmp_path / "forged-digest.jsonl", initial, forged)

    forged["receipt_digest"] = sha256_digest(canonicalize_jcs(forged["terminal_receipt"]))
    with pytest.raises(ValueError, match="frozen receipt schema"):
        _replay_snapshots(tmp_path / "forged-shape.jsonl", initial, forged)


@pytest.mark.parametrize(
    ("status", "receipt_digest", "terminal_receipt", "error", "message"),
    [
        ("COMPLETED", None, None, None, "requires a receipt"),
        ("FAILED", None, None, None, "requires an error"),
        ("RUNNING", None, None, {"error_code": "ERR_CORRUPT"}, "terminal artifacts"),
    ],
)
def test_replay_rejects_terminal_invariant_violations(
    tmp_path,
    status,
    receipt_digest,
    terminal_receipt,
    error,
    message,
) -> None:
    initial = _initial_replay_snapshot()
    invalid = copy.deepcopy(initial)
    invalid["status"] = status
    invalid["updated_at"] = "2099-01-01T00:00:00+00:00"
    invalid["receipt_digest"] = receipt_digest
    invalid["terminal_receipt"] = terminal_receipt
    invalid["error"] = error
    with pytest.raises(ValueError, match=message):
        _replay_snapshots(tmp_path / f"invalid-{status}.jsonl", initial, invalid)
