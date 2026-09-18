"""T011: Bounded input parsing, schema validation, JCS recomputation, and TTL validation."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from deltacontroller.errors import (
    IntentDigestMismatchError,
    IntentExpiredError,
    SchemaValidationError,
)
from deltacontroller.ingress import IngressParser

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)


@pytest.fixture
def valid_intent() -> dict:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_intent_passes_ingress(valid_intent: dict) -> None:
    parser = IngressParser()
    # Provide current_time before expires_at (2026-09-17T14:40:00.000Z)
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    parsed = parser.parse_intent(valid_intent, current_time=now)
    assert parsed["intent_id"] == valid_intent["intent_id"]


def test_payload_exceeding_max_bytes_rejected(valid_intent: dict) -> None:
    parser = IngressParser(max_bytes=100)
    raw = json.dumps(valid_intent).encode("utf-8")
    with pytest.raises(SchemaValidationError, match="exceeds maximum"):
        parser.parse_intent(raw)


def test_deeply_nested_json_rejected(valid_intent: dict) -> None:
    parser = IngressParser()
    nested = copy.deepcopy(valid_intent)
    curr = nested
    for _ in range(40):
        curr["child"] = {}
        curr = curr["child"]
    with pytest.raises(SchemaValidationError, match="maximum nested depth"):
        parser.parse_intent(nested)


def test_malformed_json_bytes_rejected() -> None:
    parser = IngressParser()
    with pytest.raises(SchemaValidationError, match="Malformed JSON"):
        parser.parse_intent(b'{"intent_id": invalid json}')


def test_digest_mismatch_fails_closed(valid_intent: dict) -> None:
    parser = IngressParser()
    tampered = copy.deepcopy(valid_intent)
    # Modify payload without updating declared intent_digest
    tampered["operation_payload"]["ticket_id"] = "ticket_A-9999"
    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    with pytest.raises(IntentDigestMismatchError) as exc_info:
        parser.parse_intent(tampered, current_time=now)
    assert exc_info.value.code == "ERR_INTENT_DIGEST_MISMATCH"


def test_expired_intent_fails_closed(valid_intent: dict) -> None:
    parser = IngressParser()
    # Current time is after expires_at (2026-09-17T14:40:00.000Z)
    after_expiry = datetime(2026, 9, 17, 14, 45, 0, tzinfo=UTC)
    with pytest.raises(IntentExpiredError) as exc_info:
        parser.parse_intent(valid_intent, current_time=after_expiry)
    assert exc_info.value.code == "ERR_INTENT_EXPIRED"
