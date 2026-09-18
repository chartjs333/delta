"""Caller authentication and policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from deltacontroller.errors import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    PolicyDeniedError,
    RoleForbiddenError,
)


@dataclass(frozen=True)
class AuthenticatedSubject:
    """Represents a caller verified by a trusted authentication mechanism."""

    subject_id: str
    authenticated_via: str  # LOCAL_PEER_CREDENTIAL, MTLS, TOKEN
    effective_roles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "authenticated_via": self.authenticated_via,
            "effective_roles": list(self.effective_roles),
        }


VALID_ROLES = frozenset({"OPERATOR", "RESEARCHER", "AUDITOR"})


class AuthenticationPort(Protocol):
    """Protocol for authenticating caller credentials."""

    def authenticate(self, credentials: dict[str, Any] | None) -> AuthenticatedSubject: ...


class StaticAuthenticationPort:
    """Authentication port backed only by explicitly trusted identity mappings.

    LOCAL_PEER_CREDENTIAL ``subject_id`` and MTLS ``client_cn`` are lookup keys
    supplied by a trusted transport adapter, never values accepted from a request
    body as authority. Caller-supplied roles are ignored.
    """

    def __init__(
        self,
        token_map: dict[str, AuthenticatedSubject] | None = None,
        allow_local_peer: bool = False,
        peer_subjects: dict[str, AuthenticatedSubject] | None = None,
    ) -> None:
        self.token_map = token_map or {}
        self.allow_local_peer = allow_local_peer
        self.peer_subjects = peer_subjects or {}

    def authenticate(self, credentials: dict[str, Any] | None) -> AuthenticatedSubject:
        if not credentials:
            raise AuthenticationRequiredError("No authentication credentials provided")

        auth_type = credentials.get("type")
        if auth_type == "TOKEN":
            token = credentials.get("token")
            if not token or token not in self.token_map:
                raise AuthenticationFailedError("Invalid or unknown bearer token")
            return self.token_map[token]

        if auth_type == "LOCAL_PEER_CREDENTIAL":
            if not self.allow_local_peer:
                raise AuthenticationFailedError("Local peer authentication disabled")
            peer_id = credentials.get("subject_id")
            subject = self.peer_subjects.get(peer_id) if isinstance(peer_id, str) else None
            if subject is None:
                raise AuthenticationFailedError("Unknown local peer identity")
            if subject.authenticated_via != "LOCAL_PEER_CREDENTIAL":
                raise AuthenticationFailedError(
                    "Trusted identity mapping does not match LOCAL_PEER_CREDENTIAL"
                )
            return subject

        if auth_type == "MTLS":
            cert_cn = credentials.get("client_cn")
            if not cert_cn:
                raise AuthenticationFailedError("Missing mTLS client certificate common name")
            subject = self.peer_subjects.get(cert_cn)
            if subject is None:
                raise AuthenticationFailedError("Unknown mTLS client identity")
            if subject.authenticated_via != "MTLS":
                raise AuthenticationFailedError("Trusted identity mapping does not match MTLS")
            return subject

        raise AuthenticationFailedError(f"Unsupported authentication credential type: {auth_type}")


class PolicyEngine:
    """Evaluates governance policies and role permissions for admitted operations."""

    REQUIRED_ROLES_BY_OPERATION: ClassVar[dict[str, set[str]]] = {
        "TRAIN_TICKET": {"OPERATOR"},
        "EVALUATE_CHECKPOINT": {"OPERATOR", "RESEARCHER"},
        "MATERIALIZE_DATASET": {"OPERATOR", "RESEARCHER"},
    }

    def __init__(self, policy_version: str = "step5c-v1.0.0") -> None:
        self.policy_version = policy_version

    def evaluate_admission(self, subject: AuthenticatedSubject, intent_doc: dict[str, Any]) -> None:
        """Evaluate role requirements and invariants. Ignores declared_operator as untrusted."""
        operation = intent_doc.get("operation")
        required_roles = self.REQUIRED_ROLES_BY_OPERATION.get(str(operation))
        if required_roles is None:
            msg = f"Operation '{operation}' is not recognized in governance policy"
            raise PolicyDeniedError(msg)

        # Caller must have at least one of the required roles
        caller_roles = set(subject.effective_roles)
        if not (caller_roles & required_roles):
            msg = (
                f"Subject '{subject.subject_id}' with roles {list(caller_roles)} "
                f"cannot authorize '{operation}'. Required: {list(required_roles)}"
            )
            raise RoleForbiddenError(
                msg,
                details={
                    "subject_id": subject.subject_id,
                    "effective_roles": list(caller_roles),
                    "required_roles": list(required_roles),
                    "operation": operation,
                },
            )
