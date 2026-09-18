"""Shared production-backed fixtures for Step 5C security tests."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]
STEP5C_DIR = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = STEP5C_DIR / "contracts"
EVIDENCE_DIR = STEP5C_DIR / "evidence"
FIXTURES_DIR = CONTRACTS_DIR / "fixtures"
VALID_FIXTURES_DIR = FIXTURES_DIR / "valid"
INVALID_FIXTURES_DIR = FIXTURES_DIR / "invalid"
CURRENT_TIME = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
CONTRACT_FREEZE_SHA = "66e3e7e5bb07a48aadbee8d9c4683144b812d229"


for src in (
    ROOT_DIR / "delta-controller-python" / "src",
    ROOT_DIR / "delta-worker-python" / "src",
):
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.canonical import compute_intent_digest, get_public_key_hex
from deltacontroller.dispatch import MockWorkerDispatchPort
from deltacontroller.gate import AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger
from deltacontroller.quota import QuotaManager


@dataclass(frozen=True)
class GateHarness:
    gate: AuthorizationGate
    public_key_hex: str
    dispatch_port: MockWorkerDispatchPort
    ledger: IdempotencyLedger


def load_valid_fixture(name: str) -> dict[str, Any]:
    return json.loads((VALID_FIXTURES_DIR / name).read_text(encoding="utf-8"))


def load_invalid_fixture(name: str) -> dict[str, Any]:
    return json.loads((INVALID_FIXTURES_DIR / name).read_text(encoding="utf-8"))


def clone_with_recomputed_intent_digest(intent: dict[str, Any]) -> dict[str, Any]:
    cloned = copy.deepcopy(intent)
    cloned["intent_digest"] = compute_intent_digest(cloned)
    return cloned


def operator_credentials(
    subject_id: str = "operator.alpha",
    roles: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": subject_id,
        "roles": roles or ["OPERATOR"],
    }


def build_gate_harness(
    *,
    ledger: IdempotencyLedger | None = None,
    quota_manager: QuotaManager | None = None,
    dispatch_port: MockWorkerDispatchPort | None = None,
) -> GateHarness:
    private_key = Ed25519PrivateKey.generate()
    public_key_hex = get_public_key_hex(private_key)
    actual_ledger = ledger or IdempotencyLedger()
    actual_dispatch = dispatch_port or MockWorkerDispatchPort()
    gate = AuthorizationGate(
        private_key=private_key,
        idempotency_ledger=actual_ledger,
        quota_manager=quota_manager or QuotaManager(),
        dispatch_port=actual_dispatch,
    )
    return GateHarness(
        gate=gate,
        public_key_hex=public_key_hex,
        dispatch_port=actual_dispatch,
        ledger=actual_ledger,
    )


def admit_train_ticket(
    harness: GateHarness,
    intent: dict[str, Any] | None = None,
    *,
    credentials: dict[str, Any] | None = None,
    current_time: datetime = CURRENT_TIME,
) -> dict[str, Any]:
    doc = intent or load_valid_fixture("execution-intent.train-ticket.json")
    return harness.gate.admit_and_dispatch(
        doc,
        credentials=credentials or operator_credentials(),
        current_time=current_time,
    )


def frozen_error_codes() -> set[str]:
    taxonomy = json.loads((CONTRACTS_DIR / "taxonomy" / "errors.json").read_text(encoding="utf-8"))
    return {entry["code"] for entry in taxonomy["errors"]}
