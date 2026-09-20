"""Runtime application boundary used by the HTTP transport host."""

from __future__ import annotations

import threading
from typing import Any, Protocol

from deltacontroller.errors import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    ControllerError,
)
from deltacontroller.gate import AuthorizationGate
from deltacontroller.idempotency import TERMINAL_STATUSES, LedgerRecord
from deltacontroller.runtime_config import RuntimeIdentity, WorkingVersionConfig


class CancellableDispatchPort(Protocol):
    """Operational controls implemented by the bounded Worker subprocess queue."""

    def cancel(self, execution_id: str) -> LedgerRecord | None: ...

    def shutdown(self, timeout_seconds: float) -> None: ...


class WorkingVersionApplication:
    """Join trusted Controller operations without exposing Worker/internal state to HTTP."""

    def __init__(
        self,
        *,
        config: WorkingVersionConfig,
        build_id: str,
        gate: AuthorizationGate,
        dispatch_port: CancellableDispatchPort,
        runtime_identity: RuntimeIdentity,
        instance_id: str,
    ) -> None:
        self.config = config
        self.build_id = build_id
        self.gate = gate
        self.dispatch_port = dispatch_port
        self.runtime_identity = runtime_identity
        self.instance_id = instance_id
        self._ready = threading.Event()
        self._ready.set()

    def credentials_for_request(
        self, peer_ip: str, authorization_header: str | None
    ) -> dict[str, Any]:
        """Derive credentials only from trusted socket/TLS profile inputs."""
        if self.config.is_local:
            if peer_ip != "127.0.0.1":
                raise AuthenticationFailedError("Local profile accepts loopback peers only")
            if authorization_header is not None:
                raise AuthenticationFailedError(
                    "Local profile derives identity from loopback and rejects Authorization"
                )
            return {
                "type": "LOCAL_PEER_CREDENTIAL",
                "subject_id": "working-version-loopback",
            }

        if authorization_header is None:
            raise AuthenticationRequiredError("Bearer authentication is required")
        scheme, separator, value = authorization_header.partition(" ")
        if scheme.casefold() != "bearer" or not separator or not value or " " in value:
            raise AuthenticationFailedError("Malformed bearer authorization")
        return {"type": "TOKEN", "token": value}

    def submit(self, body: bytes, credentials: dict[str, Any]) -> dict[str, Any]:
        if not self._ready.is_set():
            raise ControllerError(
                "ERR_SHUTTING_DOWN",
                "Controller is shutting down",
                "RESOURCE",
                retryable=True,
            )
        return self.gate.admit_and_dispatch(body, credentials=credentials)

    def get_status(self, execution_id: str, credentials: dict[str, Any]) -> dict[str, Any] | None:
        return self.gate.get_status(execution_id, credentials=credentials)

    def get_receipt(self, execution_id: str, credentials: dict[str, Any]) -> dict[str, Any] | None:
        return self.gate.get_receipt(execution_id, credentials=credentials)

    def cancel(self, execution_id: str, credentials: dict[str, Any]) -> dict[str, Any] | None:
        # The status lookup is the owner-authentication gate. The queue never
        # accepts caller-supplied identity or roles.
        current_status = self.gate.get_status(execution_id, credentials=credentials)
        if current_status is None:
            return None
        if current_status["state"] in TERMINAL_STATUSES:
            raise ControllerError(
                "ERR_EXECUTION_TERMINAL",
                "Execution is already terminal and cannot be cancelled",
                "IDEMPOTENCY",
                retryable=False,
            )
        transitioned = self.dispatch_port.cancel(execution_id)
        if transitioned is None:
            # Completion may have won the durable compare-and-set after the
            # owner check. Return a conflict rather than claiming cancellation.
            raise ControllerError(
                "ERR_EXECUTION_TERMINAL",
                "Execution became terminal before cancellation committed",
                "IDEMPOTENCY",
                retryable=False,
            )
        return self.gate.get_status(execution_id, credentials=credentials)

    def health_document(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "status": "UP",
            "profile": self.config.profile,
            "build_id": self.build_id,
            "protocol_id": self.config.protocol_id,
            "contract_schema_version": self.config.contract_schema_version,
            "formal_semantics_id": self.config.formal_semantics_id,
            "instance_id": self.instance_id,
            "components": {
                "controller": "UP",
                "worker": "SUBPROCESS_BOUNDARY",
                "admin_ui": "STATIC_LIVE_BUILD",
                "native_runtime": "REFERENCE_ONLY_NOT_STARTED",
                "jvm_node": "REFERENCE_ONLY_NOT_STARTED",
            },
        }

    def readiness_document(self) -> tuple[bool, dict[str, Any]]:
        ready = self._ready.is_set()
        return ready, {
            "schema_version": "1.0.0",
            "status": "READY" if ready else "DRAINING",
            "build_id": self.build_id,
            "protocol_id": self.config.protocol_id,
            "contract_schema_version": self.config.contract_schema_version,
            "formal_semantics_id": self.config.formal_semantics_id,
            "instance_id": self.instance_id,
            "signing_key_id": self.runtime_identity.signing_identity.key_id,
            "worker_trust_root": "EXPLICIT_MATCH",
        }

    def begin_shutdown(self) -> None:
        self._ready.clear()

    def shutdown(self) -> None:
        self.begin_shutdown()
        self.dispatch_port.shutdown(self.config.shutdown_grace_seconds)
