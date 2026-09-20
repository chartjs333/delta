"""Separate Worker process protocol and explicit trust-root tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.auth import AuthenticatedSubject, StaticAuthenticationPort
from deltacontroller.dispatch import MockWorkerDispatchPort
from deltacontroller.gate import AdmissionSigningIdentity, AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger
from deltatorrent.live_execution.process import (
    MAX_AUTHORIZED_EXECUTION_BYTES,
    WorkerProcessProtocolError,
    execute_authorized_bytes,
    load_trust_roots,
)

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)
BUILD_SHA = "ab1e522e07f3a2207ec37e3c2e2d4943b48a3a6e"
ISSUER_ID = "working-version-test-controller"
KEY_ID = "working-version-test-key"
CURRENT_TIME = datetime(2026, 9, 17, 14, 30, tzinfo=UTC)


def _authorized_bundle(tmp_path: Path) -> tuple[dict, str]:
    intent = json.loads(
        (CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json").read_text(
            "utf-8"
        )
    )
    key = Ed25519PrivateKey.generate()
    public_key_hex = key.public_key().public_bytes_raw().hex()
    dispatch = MockWorkerDispatchPort()
    gate = AuthorizationGate(
        controller_commit=BUILD_SHA,
        auth_port=StaticAuthenticationPort(
            allow_local_peer=True,
            peer_subjects={
                "peer": AuthenticatedSubject(
                    "operator.alpha", "LOCAL_PEER_CREDENTIAL", ["OPERATOR"]
                )
            },
        ),
        signing_identity=AdmissionSigningIdentity(key, KEY_ID, ISSUER_ID),
        idempotency_ledger=IdempotencyLedger(tmp_path / "ledger.jsonl"),
        dispatch_port=dispatch,
    )
    gate.admit_and_dispatch(
        intent,
        credentials={"type": "LOCAL_PEER_CREDENTIAL", "subject_id": "peer"},
        current_time=CURRENT_TIME,
    )
    return dispatch.dispatched_bundles[-1], public_key_hex


def _write_trust_roots(path: Path, public_key_hex: str, issuer_id: str = ISSUER_ID) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "issuer_id": issuer_id,
                "keys": [
                    {
                        "key_id": KEY_ID,
                        "algorithm": "ED25519",
                        "public_key_hex": public_key_hex,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_process_executes_one_explicitly_trusted_bundle(tmp_path: Path) -> None:
    bundle, public_key_hex = _authorized_bundle(tmp_path)
    trust_path = tmp_path / "trust-roots.json"
    _write_trust_roots(trust_path, public_key_hex)
    issuer_id, trusted_keys = load_trust_roots(trust_path)

    result = execute_authorized_bytes(
        json.dumps(bundle).encode("utf-8"),
        trusted_keys=trusted_keys,
        trusted_issuer_id=issuer_id,
        producer_commit=BUILD_SHA,
        cache_root=tmp_path / "cache",
        current_time=CURRENT_TIME,
    )
    assert result["status"] == "COMPLETED"
    assert result["dispatched"] is True
    assert result["receipt"]["provenance"]["producer_commit"] == BUILD_SHA
    assert result["receipt"]["provenance"]["execution_id"] == bundle["admission"]["execution_id"]


def test_process_rejects_issuer_mismatch_before_dispatch(tmp_path: Path) -> None:
    bundle, public_key_hex = _authorized_bundle(tmp_path)
    with pytest.raises(WorkerProcessProtocolError, match="issuer_id"):
        execute_authorized_bytes(
            json.dumps(bundle).encode("utf-8"),
            trusted_keys={KEY_ID: public_key_hex},
            trusted_issuer_id="different-runtime-issuer",
            producer_commit=BUILD_SHA,
            cache_root=tmp_path / "cache",
            current_time=CURRENT_TIME,
        )


def test_process_rejects_fixture_trust_and_oversized_input(tmp_path: Path) -> None:
    fixture = json.loads((CONTRACTS_ROOT / "vectors" / "ed25519-fixture.json").read_text("utf-8"))
    fixture_path = tmp_path / "fixture-trust.json"
    fixture_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "issuer_id": "runtime-controller",
                "keys": [
                    {
                        "key_id": fixture["key_id"],
                        "algorithm": "ED25519",
                        "public_key_hex": fixture["public_key_hex"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(WorkerProcessProtocolError, match="fixture trust"):
        load_trust_roots(fixture_path)

    with pytest.raises(WorkerProcessProtocolError, match="exceeds"):
        execute_authorized_bytes(
            b"{" + b" " * MAX_AUTHORIZED_EXECUTION_BYTES,
            trusted_keys={KEY_ID: "00" * 32},
            trusted_issuer_id=ISSUER_ID,
            producer_commit=BUILD_SHA,
            cache_root=tmp_path / "cache",
        )
