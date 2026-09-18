"""AuthorizationGate orchestrator enforcing Zone 2 trusted policy barrier."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from deltacontroller.audit import AuditLogger
from deltacontroller.auth import (
    AuthenticatedSubject,
    AuthenticationPort,
    PolicyEngine,
    StaticAuthenticationPort,
)
from deltacontroller.canonical import compute_admission_digest, sign_admission
from deltacontroller.catalog import CatalogValidator
from deltacontroller.dispatch import MockWorkerDispatchPort, WorkerDispatchPort
from deltacontroller.idempotency import IdempotencyLedger
from deltacontroller.ingress import IngressParser
from deltacontroller.quota import QuotaManager
from deltacontroller.schema import SchemaRegistry
from deltacontroller.status import build_execution_status

DEFAULT_CONTROLLER_COMMIT = "66e3e7e5bb07a48aadbee8d9c4683144b812d229"
DEFAULT_POLICY_VERSION = "step5c-policy-v1"
DEFAULT_ISSUER_ID = "step5c-fixture-controller"
DEFAULT_KEY_ID = "step5c-fixture-ed25519"
DEFAULT_ADMISSION_TTL_SECONDS = 300  # 5 minutes dispatch deadline


class AuthorizationGate:
    """Trusted Zone 2 Policy Enforcement Point and Admission Authority."""

    def __init__(
        self,
        schema_registry: SchemaRegistry | None = None,
        ingress_parser: IngressParser | None = None,
        auth_port: AuthenticationPort | None = None,
        policy_engine: PolicyEngine | None = None,
        catalog_validator: CatalogValidator | None = None,
        idempotency_ledger: IdempotencyLedger | None = None,
        quota_manager: QuotaManager | None = None,
        dispatch_port: WorkerDispatchPort | None = None,
        audit_logger: AuditLogger | None = None,
        private_key: Ed25519PrivateKey | None = None,
        key_id: str = DEFAULT_KEY_ID,
        issuer_id: str = DEFAULT_ISSUER_ID,
        controller_commit: str = DEFAULT_CONTROLLER_COMMIT,
        policy_version: str = DEFAULT_POLICY_VERSION,
        admission_ttl_seconds: int = DEFAULT_ADMISSION_TTL_SECONDS,
    ) -> None:
        self.schema_registry = schema_registry or SchemaRegistry()
        self.ingress_parser = ingress_parser or IngressParser(schema_registry=self.schema_registry)
        self.auth_port = auth_port or StaticAuthenticationPort()
        self.policy_engine = policy_engine or PolicyEngine()
        self.catalog_validator = catalog_validator or CatalogValidator()
        self.idempotency_ledger = idempotency_ledger or IdempotencyLedger()
        self.quota_manager = quota_manager or QuotaManager()
        self.dispatch_port = dispatch_port or MockWorkerDispatchPort(
            schema_registry=self.schema_registry
        )
        self.audit_logger = audit_logger or AuditLogger()
        self.private_key = private_key or Ed25519PrivateKey.generate()
        self.key_id = key_id
        self.issuer_id = issuer_id
        self.controller_commit = controller_commit
        self.policy_version = policy_version
        self.admission_ttl_seconds = admission_ttl_seconds

    def admit_and_dispatch(
        self,
        raw_or_dict_intent: bytes | str | dict[str, Any],
        credentials: dict[str, Any] | None = None,
        current_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Execute complete Zone 2 preflight pipeline and dispatch to worker if admitted.

        Steps:
            1. Bounded ingress parse, schema validation, JCS recomputation, TTL check.
            2. Transport caller authentication -> AuthenticatedSubject.
            3. Role-based governance policy evaluation.
            4. Catalog ref, known plugin/dataset, and capability matrix validation.
            5. Append-only idempotency ledger check (replay/conflict/collision).
            6. Resource quota and concurrency check.
            7. Assign UUIDs, determine admission_expires_at, construct AdmissionRecord.
            8. Compute admission_digest and Ed25519 signature over admission \\ signature.
            9. Record admission in ledger.
            10. Construct AuthorizedExecution bundle, validate schema, dispatch to Zone 3.
            11. Structured audit event logging with secret redaction.
        """
        now = current_time or datetime.now(UTC)

        # 1. Ingress parse & preflight checks
        intent = self.ingress_parser.parse_intent(raw_or_dict_intent, current_time=now)
        intent_id = intent["intent_id"]
        intent_digest = intent["intent_digest"]

        # 2. Authentication
        subject: AuthenticatedSubject = self.auth_port.authenticate(credentials)

        # 3. Policy evaluation
        self.policy_engine.evaluate_admission(subject, intent)

        # 4. Catalog integrity & capability matrix
        self.catalog_validator.validate(intent["workload"], intent["operation"])

        # 5. Idempotency & Replay check
        existing = self.idempotency_ledger.check_intent(
            intent_id, intent_digest, subject.subject_id
        )
        if existing is not None:
            # Re-submission handling
            self.audit_logger.log_event(
                "IDEMPOTENT_RESUBMISSION",
                subject.subject_id,
                {"intent_id": intent_id, "status": existing.status},
                intent_id=intent_id,
                execution_id=existing.execution_id,
            )
            status_doc = build_execution_status(
                execution_id=existing.execution_id,
                intent_id=existing.intent_id,
                intent_digest=existing.intent_digest,
                admission_id=existing.admission_record["admission_id"]
                if existing.admission_record
                else "",
                admission_digest=existing.admission_record["admission_digest"]
                if existing.admission_record
                else "",
                state=existing.status,
                receipt_digest=existing.receipt_digest,
                error=existing.error,
                updated_at=existing.updated_at,
                schema_registry=self.schema_registry,
            )
            return {
                "action": "ALREADY_ADMITTED",
                "admission": existing.admission_record,
                "status": status_doc,
                "receipt": existing.terminal_receipt,
            }

        # 6. Quotas and Resource Grants
        active_count = self.idempotency_ledger.active_count()
        grants = self.quota_manager.evaluate_grants(intent, active_count)

        # 7. Admission record creation
        admission_id = str(uuid.uuid4())
        execution_id = str(uuid.uuid4())
        admitted_at_iso = now.isoformat()

        # admission_expires_at: now <= admission_expires_at <= intent.expires_at
        intent_expires_at = datetime.fromisoformat(intent["expires_at"].replace("Z", "+00:00"))
        dispatch_deadline = now + timedelta(seconds=self.admission_ttl_seconds)
        admission_expires_at = min(intent_expires_at, dispatch_deadline)
        admission_expires_at_iso = admission_expires_at.isoformat()

        # Build admission document skeleton
        admission_doc: dict[str, Any] = {
            "schema_version": "1.0.0",
            "admission_id": admission_id,
            "intent_id": intent_id,
            "intent_digest": intent_digest,
            "execution_id": execution_id,
            "authenticated_subject": subject.to_dict(),
            "policy_context": {
                "policy_version": self.policy_version,
                "controller_commit": self.controller_commit,
                "verdict": "ADMITTED",
            },
            "resource_grants": grants.to_dict(),
            "admitted_at": admitted_at_iso,
            "admission_expires_at": admission_expires_at_iso,
        }

        # 8. Compute admission_digest (over doc excluding admission_digest and authenticator)
        admission_digest = compute_admission_digest(admission_doc)
        admission_doc["admission_digest"] = admission_digest

        # Add authenticator metadata
        admission_doc["authenticator"] = {
            "algorithm": "ED25519",
            "issuer_id": self.issuer_id,
            "key_id": self.key_id,
        }

        # Sign over RFC8785(admission_doc \ {"authenticator.signature"})
        signature = sign_admission(admission_doc, self.private_key)
        admission_doc["authenticator"]["signature"] = signature

        # Validate schema of AdmissionRecord
        self.schema_registry.validate("admission-record", admission_doc)

        # 9. Record admission in ledger
        constraints = intent.get("execution_constraints", {})
        retry_of = constraints.get("retry_of_intent_id")
        self.idempotency_ledger.record_admission(
            intent_id=intent_id,
            intent_digest=intent_digest,
            caller_subject_id=subject.subject_id,
            execution_id=execution_id,
            admission_record=admission_doc,
            retry_of_intent_id=retry_of,
        )

        # 10. Assemble and validate AuthorizedExecution bundle
        bundle: dict[str, Any] = {
            "schema_version": "1.0.0",
            "intent": intent,
            "admission": admission_doc,
        }
        self.schema_registry.validate("authorized-execution", bundle)

        # 11. Dispatch to Zone 3 worker
        try:
            dispatch_result = self.dispatch_port.dispatch(bundle, current_time=now)
        except TypeError:
            dispatch_result = self.dispatch_port.dispatch(bundle)
        worker_state = dispatch_result.get("status", "RUNNING")
        receipt = dispatch_result.get("receipt") or dispatch_result.get("terminal_receipt")
        receipt_digest = dispatch_result.get("receipt_digest")
        error = dispatch_result.get("error")

        ledger_rec = self.idempotency_ledger.update_execution(
            execution_id,
            status=worker_state,
            receipt_digest=receipt_digest,
            terminal_receipt=receipt,
            error=error,
        )

        # 12. Audit event
        self.audit_logger.log_event(
            "EXECUTION_ADMITTED",
            subject.subject_id,
            {
                "intent_id": intent_id,
                "execution_id": execution_id,
                "operation": intent["operation"],
                "worker_state": worker_state,
            },
            intent_id=intent_id,
            execution_id=execution_id,
        )

        # 13. Build initial status read model
        status_doc = build_execution_status(
            execution_id=execution_id,
            intent_id=intent_id,
            intent_digest=intent_digest,
            admission_id=admission_id,
            admission_digest=admission_digest,
            state=ledger_rec.status,
            receipt_digest=ledger_rec.receipt_digest,
            error=ledger_rec.error,
            updated_at=ledger_rec.updated_at,
            schema_registry=self.schema_registry,
        )

        return {
            "action": "ADMITTED",
            "admission": admission_doc,
            "bundle": bundle,
            "status": status_doc,
            "receipt": ledger_rec.terminal_receipt,
        }

    def get_status(self, execution_id: str) -> dict[str, Any] | None:
        """Retrieve the execution status document by execution_id."""
        rec = self.idempotency_ledger.get_by_execution_id(execution_id)
        if not rec:
            return None
        adm = rec.admission_record or {}
        return build_execution_status(
            execution_id=rec.execution_id,
            intent_id=rec.intent_id,
            intent_digest=rec.intent_digest,
            admission_id=adm.get("admission_id", rec.execution_id),
            admission_digest=adm.get("admission_digest", rec.intent_digest),
            state=rec.status,
            receipt_digest=rec.receipt_digest,
            error=rec.error,
            updated_at=rec.updated_at,
            schema_registry=self.schema_registry,
        )
