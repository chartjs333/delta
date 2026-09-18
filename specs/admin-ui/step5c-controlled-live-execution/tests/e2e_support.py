"""Shared final-integration harness for Step 5C T036-T039."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.auth import AuthenticatedSubject, StaticAuthenticationPort
from deltacontroller.dispatch import IntegratedWorkerDispatchPort
from deltacontroller.gate import AdmissionSigningIdentity, AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

CURRENT_TIME = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
RUNTIME_KEY_ID = "step5c-e2e-runtime-key-v1"
RUNTIME_ISSUER_ID = "step5c-e2e-runtime-controller"

TRUSTED_LOCAL_PEERS = {
    "operator.alpha": AuthenticatedSubject(
        subject_id="operator.alpha",
        authenticated_via="LOCAL_PEER_CREDENTIAL",
        effective_roles=["OPERATOR"],
    ),
    "operator.beta": AuthenticatedSubject(
        subject_id="operator.beta",
        authenticated_via="LOCAL_PEER_CREDENTIAL",
        effective_roles=["OPERATOR"],
    ),
}


@dataclass(frozen=True, slots=True)
class IntegratedGateHarness:
    gate: AuthorizationGate
    preflight: AuthorizedExecutionPreflight
    dispatch_port: IntegratedWorkerDispatchPort
    private_key: Ed25519PrivateKey
    public_key_hex: str


def operator_credentials(subject_id: str = "operator.alpha") -> dict[str, Any]:
    """Return transport credentials whose caller-supplied roles carry no authority."""
    return {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": subject_id,
        "roles": ["AUDITOR"],
    }


def build_integrated_gate(
    ledger_path: Path,
    *,
    private_key: Ed25519PrivateKey | None = None,
    worker_public_key_hex: str | None = None,
    cancellation_token: Any | None = None,
    dispatcher: Any | None = None,
) -> IntegratedGateHarness:
    """Build the real Controller-to-Worker integration with explicit trust inputs."""
    actual_private_key = private_key or Ed25519PrivateKey.generate()
    public_key_hex = actual_private_key.public_key().public_bytes_raw().hex()
    preflight = AuthorizedExecutionPreflight(
        trusted_keys={RUNTIME_KEY_ID: worker_public_key_hex or public_key_hex}
    )
    dispatch_port = IntegratedWorkerDispatchPort(
        preflight=preflight,
        dispatcher=dispatcher,
        cancellation_token=cancellation_token,
        clock=lambda: CURRENT_TIME,
    )
    gate = AuthorizationGate(
        auth_port=StaticAuthenticationPort(
            allow_local_peer=True,
            peer_subjects=TRUSTED_LOCAL_PEERS,
        ),
        signing_identity=AdmissionSigningIdentity(
            private_key=actual_private_key,
            key_id=RUNTIME_KEY_ID,
            issuer_id=RUNTIME_ISSUER_ID,
        ),
        dispatch_port=dispatch_port,
        idempotency_ledger=IdempotencyLedger(persistence_path=ledger_path),
    )
    return IntegratedGateHarness(
        gate=gate,
        preflight=preflight,
        dispatch_port=dispatch_port,
        private_key=actual_private_key,
        public_key_hex=public_key_hex,
    )


def rebuild_gate(harness: IntegratedGateHarness, ledger_path: Path) -> AuthorizationGate:
    """Rebuild only Controller process state while reusing explicit runtime trust."""
    return AuthorizationGate(
        auth_port=StaticAuthenticationPort(
            allow_local_peer=True,
            peer_subjects=TRUSTED_LOCAL_PEERS,
        ),
        signing_identity=harness.gate.signing_identity,
        dispatch_port=harness.dispatch_port,
        idempotency_ledger=IdempotencyLedger(persistence_path=ledger_path),
    )
