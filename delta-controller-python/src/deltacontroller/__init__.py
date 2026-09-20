"""Delta Controller / Authorization Gate package."""

from __future__ import annotations

from deltacontroller.audit import AuditLogger, redact_sensitive_data
from deltacontroller.auth import (
    AuthenticatedSubject,
    AuthenticationPort,
    PolicyEngine,
    StaticAuthenticationPort,
)
from deltacontroller.canonical import (
    canonicalize_jcs,
    compute_admission_digest,
    compute_intent_digest,
    sha256_digest,
    sign_admission,
    verify_admission_signature,
    verify_intent_digest,
)
from deltacontroller.catalog import CatalogValidator
from deltacontroller.dispatch import (
    IntegratedWorkerDispatchPort,
    JsonSubprocessWorkerRunner,
    MockWorkerDispatchPort,
    SubprocessWorkerDispatchPort,
    WorkerDispatchPort,
    WorkerProcessRunner,
)
from deltacontroller.errors import ControllerError
from deltacontroller.gate import AdmissionSigningIdentity, AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger, LedgerRecord
from deltacontroller.ingress import IngressParser
from deltacontroller.quota import QuotaManager, ResourceGrants
from deltacontroller.schema import SchemaRegistry
from deltacontroller.status import build_execution_status

__version__ = "1.0.0"

__all__ = [
    "AdmissionSigningIdentity",
    "AuditLogger",
    "AuthenticatedSubject",
    "AuthenticationPort",
    "AuthorizationGate",
    "CatalogValidator",
    "ControllerError",
    "IdempotencyLedger",
    "IngressParser",
    "IntegratedWorkerDispatchPort",
    "JsonSubprocessWorkerRunner",
    "LedgerRecord",
    "MockWorkerDispatchPort",
    "PolicyEngine",
    "QuotaManager",
    "ResourceGrants",
    "SchemaRegistry",
    "StaticAuthenticationPort",
    "SubprocessWorkerDispatchPort",
    "WorkerDispatchPort",
    "WorkerProcessRunner",
    "build_execution_status",
    "canonicalize_jcs",
    "compute_admission_digest",
    "compute_intent_digest",
    "redact_sensitive_data",
    "sha256_digest",
    "sign_admission",
    "verify_admission_signature",
    "verify_intent_digest",
]
