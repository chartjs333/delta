"""T030: Replay and Idempotency Verification under Concurrent Submission and Restart.

Proves:
- Duplicate submission of identical intent produces idempotent result, 0 extra worker starts.
- Re-submission of intent_id with altered payload/digest -> ERR_INTENT_COLLISION_DETECTED.
- Submission of different intent_id with collision on existing intent_digest is rejected.
- Submission of existing intent_id by unauthorized subject -> ERR_UNAUTHORIZED_PEER_OR_ROLE.
- Controller restart preserves idempotency ledger and prevents duplicate executions.
- Tampered intent digests fail validation before ledger entry.
"""

from __future__ import annotations

import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from security_support import (
    SecurityIdempotencyLedger,
    jcs_bytes,
    sha256_prefixed,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "contracts" / "fixtures" / "valid"


@pytest.fixture
def base_intent() -> dict:
    path = FIXTURES_DIR / "execution-intent.train-ticket.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_t030_replay_exact_duplicate_is_idempotent_zero_new_worker_starts(
    base_intent: dict,
) -> None:
    ledger = SecurityIdempotencyLedger()
    caller = "operator.alpha"

    # First submission
    outcome1, code1, adm1 = ledger.submit_intent(base_intent, caller)
    assert outcome1 == "ADMITTED"
    assert code1 == "OK"
    assert adm1 is not None
    assert ledger.worker_start_count == 1

    # Exact duplicate submission (same intent_id, same digest, same caller)
    outcome2, code2, adm2 = ledger.submit_intent(base_intent, caller)
    assert outcome2 == "REPLAY_IDEMPOTENT"
    assert code2 == "OK"
    assert adm2 == adm1
    assert ledger.worker_start_count == 1  # No duplicate worker started!


def test_t030_replay_concurrent_submissions_serialize_to_single_execution(
    base_intent: dict,
) -> None:
    ledger = SecurityIdempotencyLedger()
    caller = "operator.alpha"

    def submit() -> tuple[str, str, dict | None]:
        return ledger.submit_intent(base_intent, caller)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(submit) for _ in range(16)]
        results = [f.result() for f in futures]

    admitted = [r for r in results if r[0] == "ADMITTED"]
    replayed = [r for r in results if r[0] == "REPLAY_IDEMPOTENT"]

    assert len(admitted) == 1
    assert len(replayed) == 15
    assert ledger.worker_start_count == 1

    # All returned admissions must share identical execution_id
    execution_ids = {r[2]["execution_id"] for r in results if r[2]}
    assert len(execution_ids) == 1


def test_t030_replay_modified_payload_same_intent_id_fails_collision(
    base_intent: dict,
) -> None:
    ledger = SecurityIdempotencyLedger()
    caller = "operator.alpha"

    # Admit original
    outcome1, _, _ = ledger.submit_intent(base_intent, caller)
    assert outcome1 == "ADMITTED"

    # Alter payload but keep same intent_id
    tampered = copy.deepcopy(base_intent)
    tampered["operation_payload"]["ticket_id"] = "ticket-TAMPERED-001"
    t_copy = copy.deepcopy(tampered)
    t_copy.pop("intent_digest", None)
    tampered["intent_digest"] = sha256_prefixed(jcs_bytes(t_copy))

    # Re-submit with same intent_id
    outcome2, code2, adm2 = ledger.submit_intent(tampered, caller)
    assert outcome2 == "REJECTED"
    assert code2 == "ERR_INTENT_COLLISION_DETECTED"
    assert adm2 is None
    assert ledger.worker_start_count == 1


def test_t030_replay_different_intent_id_same_digest_fails_collision(
    base_intent: dict,
) -> None:
    ledger = SecurityIdempotencyLedger()
    caller = "operator.alpha"

    # Admit original
    outcome1, _, _ = ledger.submit_intent(base_intent, caller)
    assert outcome1 == "ADMITTED"

    # Create distinct intent_id with identical body/digest
    colliding = copy.deepcopy(base_intent)
    colliding["intent_id"] = "99999999-9999-4999-8999-999999999999"
    outcome2, code2, adm2 = ledger.submit_intent(colliding, caller)
    assert outcome2 == "REJECTED"
    assert code2 in {"ERR_INTENT_COLLISION_DETECTED", "ERR_INTENT_DIGEST_MISMATCH"}
    assert adm2 is None
    assert ledger.worker_start_count == 1


def test_t030_replay_mismatched_caller_fails_unauthorized(
    base_intent: dict,
) -> None:
    ledger = SecurityIdempotencyLedger()
    legitimate_caller = "operator.alpha"
    hostile_caller = "attacker.eve"

    outcome1, _, _ = ledger.submit_intent(base_intent, legitimate_caller)
    assert outcome1 == "ADMITTED"

    outcome2, code2, adm2 = ledger.submit_intent(base_intent, hostile_caller)
    assert outcome2 == "REJECTED"
    assert code2 == "ERR_UNAUTHORIZED_PEER_OR_ROLE"
    assert adm2 is None
    assert ledger.worker_start_count == 1


def test_t030_controller_restart_preserves_idempotency_ledger(
    base_intent: dict,
) -> None:
    ledger1 = SecurityIdempotencyLedger()
    caller = "operator.alpha"

    outcome1, _, adm1 = ledger1.submit_intent(base_intent, caller)
    assert outcome1 == "ADMITTED"
    assert ledger1.worker_start_count == 1

    # Snapshot to simulated durable storage
    snapshot_json = ledger1.snapshot()

    # Simulate Controller crash & reboot
    del ledger1
    ledger2 = SecurityIdempotencyLedger.restore(snapshot_json)

    assert ledger2.worker_start_count == 1

    # Replay after reboot
    outcome2, code2, adm2 = ledger2.submit_intent(base_intent, caller)
    assert outcome2 == "REPLAY_IDEMPOTENT"
    assert code2 == "OK"
    assert adm2 == adm1
    assert ledger2.worker_start_count == 1


def test_t030_tampered_intent_digest_rejected_before_ledger(
    base_intent: dict,
) -> None:
    ledger = SecurityIdempotencyLedger()
    caller = "operator.alpha"

    tampered = copy.deepcopy(base_intent)
    tampered["intent_digest"] = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )

    outcome, code, adm = ledger.submit_intent(tampered, caller)
    assert outcome == "REJECTED"
    assert code == "ERR_INTENT_DIGEST_MISMATCH"
    assert adm is None
    assert ledger.worker_start_count == 0
