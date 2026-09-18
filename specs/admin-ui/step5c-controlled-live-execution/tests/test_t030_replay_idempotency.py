"""T030: production replay/idempotency verification.

These tests exercise the real AuthorizationGate and IdempotencyLedger rather
than a security-local simulation.
"""

from __future__ import annotations

import copy
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from deltacontroller.canonical import compute_intent_digest
from deltacontroller.dispatch import MockWorkerDispatchPort
from deltacontroller.errors import (
    IntentCollisionDetectedError,
    IntentDigestMismatchError,
    IntentIdDigestConflictError,
    UnauthorizedCallerError,
)
from deltacontroller.idempotency import IdempotencyLedger
from security_support import (
    admit_train_ticket,
    build_gate_harness,
    frozen_error_codes,
    load_valid_fixture,
    operator_credentials,
)


class BlockingDispatchPort(MockWorkerDispatchPort):
    """Hold the first dispatch after its execution identity is durably committed."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def dispatch(self, bundle: dict) -> dict:
        self.entered.set()
        if not self.release.wait(timeout=5):
            raise AssertionError("Timed out waiting to release security-test dispatch")
        return super().dispatch(bundle)


@pytest.fixture
def base_intent() -> dict:
    return load_valid_fixture("execution-intent.train-ticket.json")


def assert_frozen_code(code: str) -> None:
    assert code in frozen_error_codes()


def test_t030_gate_exact_duplicate_is_idempotent_zero_new_worker_starts(
    base_intent: dict,
) -> None:
    harness = build_gate_harness()

    first = admit_train_ticket(harness, base_intent)
    second = admit_train_ticket(harness, base_intent)

    assert first["action"] == "ADMITTED"
    assert second["action"] == "ALREADY_ADMITTED"
    assert second["admission"] == first["admission"]
    assert second["status"]["execution_id"] == first["status"]["execution_id"]
    assert len(harness.dispatch_port.dispatched_bundles) == 1


def test_t030_gate_concurrent_duplicates_serialize_to_single_execution(
    base_intent: dict,
) -> None:
    dispatch_port = BlockingDispatchPort()
    harness = build_gate_harness(dispatch_port=dispatch_port)

    def submit() -> dict:
        return admit_train_ticket(harness, base_intent)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(submit)
        assert dispatch_port.entered.wait(timeout=5)
        second = executor.submit(submit)
        try:
            replay = second.result(timeout=5)
        finally:
            dispatch_port.release.set()
        results = [first.result(timeout=5), replay]

    admitted = [r for r in results if r["action"] == "ADMITTED"]
    replayed = [r for r in results if r["action"] == "ALREADY_ADMITTED"]
    execution_ids = {r["status"]["execution_id"] for r in results}

    assert len(admitted) == 1
    assert len(replayed) == 1
    assert len(execution_ids) == 1
    assert len(harness.dispatch_port.dispatched_bundles) == 1


def test_t030_gate_modified_payload_same_intent_id_uses_frozen_conflict_code(
    base_intent: dict,
) -> None:
    harness = build_gate_harness()
    admit_train_ticket(harness, base_intent)

    tampered = copy.deepcopy(base_intent)
    tampered["operation_payload"]["ticket_id"] = "ticket-TAMPERED-001"
    tampered["intent_digest"] = compute_intent_digest(tampered)

    with pytest.raises(IntentIdDigestConflictError) as exc_info:
        admit_train_ticket(harness, tampered)

    assert exc_info.value.code == "ERR_INTENT_ID_DIGEST_CONFLICT"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 1


def test_t030_ledger_rejects_distinct_intent_id_with_same_digest_collision(
    base_intent: dict,
) -> None:
    ledger = IdempotencyLedger()
    shared_digest = base_intent["intent_digest"]
    ledger.record_admission(
        base_intent["intent_id"],
        shared_digest,
        "operator.alpha",
        "55555555-5555-4555-8555-555555555555",
        {"admission_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"},
    )

    with pytest.raises(IntentCollisionDetectedError) as exc_info:
        ledger.acquire_or_check(
            "99999999-9999-4999-8999-999999999999",
            shared_digest,
            "operator.alpha",
        )

    assert exc_info.value.code == "ERR_INTENT_COLLISION_DETECTED"
    assert_frozen_code(exc_info.value.code)


def test_t030_gate_mismatched_caller_fails_unauthorized(
    base_intent: dict,
) -> None:
    harness = build_gate_harness()
    admit_train_ticket(harness, base_intent)

    with pytest.raises(UnauthorizedCallerError) as exc_info:
        admit_train_ticket(
            harness,
            base_intent,
            credentials=operator_credentials("operator.beta", ["OPERATOR"]),
        )

    assert exc_info.value.code == "ERR_UNAUTHORIZED_CALLER"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 1


def test_t030_controller_restart_preserves_production_ledger(
    base_intent: dict,
    tmp_path,
) -> None:
    ledger_path = tmp_path / "idempotency.jsonl"
    first_harness = build_gate_harness(ledger=IdempotencyLedger(persistence_path=ledger_path))
    first = admit_train_ticket(first_harness, base_intent)
    assert len(first_harness.dispatch_port.dispatched_bundles) == 1

    restarted_harness = build_gate_harness(ledger=IdempotencyLedger(persistence_path=ledger_path))
    replay = admit_train_ticket(restarted_harness, base_intent)

    assert replay["action"] == "ALREADY_ADMITTED"
    assert replay["status"]["execution_id"] == first["status"]["execution_id"]
    assert len(restarted_harness.dispatch_port.dispatched_bundles) == 0


def test_t030_tampered_intent_digest_rejected_before_ledger(
    base_intent: dict,
) -> None:
    harness = build_gate_harness()
    tampered = copy.deepcopy(base_intent)
    tampered["intent_digest"] = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )

    with pytest.raises(IntentDigestMismatchError) as exc_info:
        admit_train_ticket(harness, tampered)

    assert exc_info.value.code == "ERR_INTENT_DIGEST_MISMATCH"
    assert_frozen_code(exc_info.value.code)
    assert len(harness.dispatch_port.dispatched_bundles) == 0
    assert harness.ledger.get_by_intent_id(base_intent["intent_id"]) is None
