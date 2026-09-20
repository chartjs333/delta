"""C-WA-023 .. C-WA-026: Terminal receipt lineage extension verification."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher
from tests.live_execution_fixture_trust import fixture_authorized_execution_preflight

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)
TEST_PRODUCER_COMMIT = "4992d9eca319da21b5a2c7b94593f3668b92329c"


@pytest.fixture
def train_bundle() -> dict:
    bundle_path = CONTRACTS_ROOT / "fixtures" / "valid" / "authorized-execution.train-ticket.json"
    with bundle_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_c_wa_023_receipt_includes_complete_lineage(train_bundle: dict) -> None:
    preflight = fixture_authorized_execution_preflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    dispatcher = ClosedEnumWorkerDispatcher(producer_commit=TEST_PRODUCER_COMMIT)
    result = dispatcher.dispatch(ctx)

    receipt = result["receipt"]
    assert receipt is not None
    prov = receipt["provenance"]

    assert prov["intent_id"] == ctx.intent_id
    assert prov["intent_digest"] == ctx.intent_digest
    assert prov["admission_id"] == ctx.admission_id
    assert prov["admission_digest"] == ctx.admission_digest
    assert prov["execution_id"] == ctx.execution_id
    assert prov["controller_commit"] == ctx.controller_commit


def test_c_wa_024_receipt_validates_against_lineage_schema_and_forbids_consensus(
    train_bundle: dict,
) -> None:
    preflight = fixture_authorized_execution_preflight()
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    ctx = preflight.validate(train_bundle, current_time=now)

    dispatcher = ClosedEnumWorkerDispatcher(producer_commit=TEST_PRODUCER_COMMIT)
    result = dispatcher.dispatch(ctx)
    receipt = result["receipt"]

    # Validate lineage extension fields per schema
    prov = receipt.get("provenance", {})
    assert prov.get("intent_id") == ctx.intent_id
    assert prov.get("intent_digest") == ctx.intent_digest
    assert prov.get("admission_id") == ctx.admission_id
    assert prov.get("admission_digest") == ctx.admission_digest
    assert prov.get("execution_id") == ctx.execution_id
    assert prov.get("controller_commit") == ctx.controller_commit

    # Forbid consensus fields
    for field in ("round_id", "state_root", "wal_sequence", "qc", "apply_qc"):
        assert field not in receipt["provenance"]
        assert field not in receipt["execution"]
