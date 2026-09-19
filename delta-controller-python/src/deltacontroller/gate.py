"""AuthorizationGate orchestrator enforcing Zone 2 trusted policy barrier."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from deltacontroller.audit import AuditLogger
from deltacontroller.auth import (
    AuthenticatedSubject,
    AuthenticationPort,
    PolicyEngine,
)
from deltacontroller.canonical import (
    canonicalize_jcs,
    compute_admission_digest,
    sha256_digest,
    sign_admission,
)
from deltacontroller.catalog import CatalogValidator
from deltacontroller.dispatch import MockWorkerDispatchPort, WorkerDispatchPort
from deltacontroller.errors import (
    ControllerError,
    UnauthorizedCallerError,
    WorkerDispatchFailedError,
)
from deltacontroller.idempotency import IdempotencyLedger
from deltacontroller.ingress import IngressParser
from deltacontroller.quota import QuotaManager
from deltacontroller.schema import SchemaRegistry
from deltacontroller.status import build_execution_status

DEFAULT_CONTROLLER_COMMIT = "66e3e7e5bb07a48aadbee8d9c4683144b812d229"
DEFAULT_POLICY_VERSION = "step5c-policy-v1"
DEFAULT_ADMISSION_TTL_SECONDS = 300  # 5 minutes dispatch deadline
_FROZEN_TEST_FIXTURE_ISSUER_ID = "step5c-fixture-controller"
_FROZEN_TEST_FIXTURE_KEY_ID = "step5c-fixture-ed25519"


@dataclass(frozen=True, slots=True)
class AdmissionSigningIdentity:
    """Explicit runtime signing identity shared with the Worker trust configuration."""

    private_key: Ed25519PrivateKey
    key_id: str
    issuer_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.private_key, Ed25519PrivateKey):
            raise TypeError("private_key must be an Ed25519PrivateKey")
        if not self.key_id.strip():
            raise ValueError("key_id must be non-empty")
        if not self.issuer_id.strip():
            raise ValueError("issuer_id must be non-empty")
        if (
            self.key_id == _FROZEN_TEST_FIXTURE_KEY_ID
            or self.issuer_id == _FROZEN_TEST_FIXTURE_ISSUER_ID
        ):
            raise ValueError(
                "Frozen fixture signing metadata is test-vector-only and cannot be used "
                "by the runtime AuthorizationGate"
            )


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
        signing_identity: AdmissionSigningIdentity | None = None,
        controller_commit: str = DEFAULT_CONTROLLER_COMMIT,
        policy_version: str = DEFAULT_POLICY_VERSION,
        admission_ttl_seconds: int = DEFAULT_ADMISSION_TTL_SECONDS,
    ) -> None:
        if auth_port is None:
            raise ValueError(
                "AuthorizationGate requires an explicitly configured trusted AuthenticationPort"
            )
        if signing_identity is None:
            raise ValueError(
                "AuthorizationGate requires an explicitly configured Ed25519 "
                "AdmissionSigningIdentity"
            )
        if idempotency_ledger is None or idempotency_ledger.persistence_path is None:
            raise ValueError(
                "AuthorizationGate requires an explicitly configured durable "
                "IdempotencyLedger persistence_path"
            )
        self.schema_registry = schema_registry or SchemaRegistry()
        self.ingress_parser = ingress_parser or IngressParser(schema_registry=self.schema_registry)
        self.auth_port = auth_port
        self.policy_engine = policy_engine or PolicyEngine()
        self.catalog_validator = catalog_validator or CatalogValidator()
        self.idempotency_ledger = idempotency_ledger
        self.quota_manager = quota_manager or QuotaManager()
        self.dispatch_port = dispatch_port or MockWorkerDispatchPort(
            schema_registry=self.schema_registry
        )
        self.audit_logger = audit_logger or AuditLogger()
        self.signing_identity = signing_identity
        self.controller_commit = controller_commit
        self.policy_version = policy_version
        self.admission_ttl_seconds = admission_ttl_seconds

    def _validate_dispatch_result(
        self,
        dispatch_result: Any,
        *,
        intent_id: str,
        execution_id: str,
        admission_id: str,
        intent_digest: str,
        admission_digest: str,
        operation: str,
        controller_commit: str,
        catalog_backend_ref: str,
        model_plugin_id: str,
        dataset_id: str,
        requested_scope: str,
    ) -> dict[str, Any]:
        """Validate worker output before it becomes a durable status read model."""
        if not isinstance(dispatch_result, dict):
            raise WorkerDispatchFailedError("Worker dispatch result must be an object")
        if dispatch_result.get("intent_id") != intent_id:
            raise WorkerDispatchFailedError("Worker dispatch intent_id mismatch")
        if dispatch_result.get("execution_id") != execution_id:
            raise WorkerDispatchFailedError("Worker dispatch execution_id mismatch")
        if not isinstance(dispatch_result.get("dispatched"), bool):
            raise WorkerDispatchFailedError("Worker dispatch result lacks dispatched boolean")

        state = dispatch_result.get("status")
        allowed_states = {"QUEUED", "RUNNING", "COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
        if state not in allowed_states:
            raise WorkerDispatchFailedError(f"Worker returned invalid status '{state}'")

        receipt = dispatch_result.get("receipt")
        receipt_digest = dispatch_result.get("receipt_digest")
        error = dispatch_result.get("error")

        if receipt is not None:
            if not isinstance(receipt, dict):
                raise WorkerDispatchFailedError("Worker receipt must be an object")
            self.schema_registry.validate("receipt-lineage", receipt)
            provenance = receipt.get("provenance", {})
            expected_lineage = {
                "intent_id": intent_id,
                "intent_digest": intent_digest,
                "admission_id": admission_id,
                "admission_digest": admission_digest,
                "execution_id": execution_id,
                "controller_commit": controller_commit,
                "catalog_backend_ref": catalog_backend_ref,
            }
            if any(provenance.get(key) != value for key, value in expected_lineage.items()):
                raise WorkerDispatchFailedError("Worker receipt lineage mismatch")
            if provenance.get("backend_commit") != catalog_backend_ref:
                raise WorkerDispatchFailedError("Worker receipt backend reference mismatch")
            receipt_workload = receipt.get("workload", {})
            expected_workload = {
                "model_plugin_id": model_plugin_id,
                "dataset_id": dataset_id,
                "executed_scope": requested_scope,
            }
            if any(receipt_workload.get(key) != value for key, value in expected_workload.items()):
                raise WorkerDispatchFailedError("Worker receipt workload binding mismatch")
            receipt_execution = receipt.get("execution", {})
            if (
                receipt_execution.get("verdict") != "SUCCESS"
                or receipt_execution.get("terminal_status") != "COMPLETED"
            ):
                raise WorkerDispatchFailedError("Worker receipt terminal verdict mismatch")
            computed_receipt_digest = sha256_digest(canonicalize_jcs(receipt))
            if receipt_digest != computed_receipt_digest:
                raise WorkerDispatchFailedError("Worker receipt digest mismatch")

        if state == "COMPLETED":
            if dispatch_result.get("dispatched") is not True:
                raise WorkerDispatchFailedError("Completed worker result was not dispatched")
            if error is not None:
                raise WorkerDispatchFailedError("Completed worker result contains an error")
            if operation == "MATERIALIZE_DATASET":
                if receipt is not None or receipt_digest is not None:
                    raise WorkerDispatchFailedError(
                        "MATERIALIZE_DATASET must not claim a terminal receipt"
                    )
            elif receipt is None or receipt_digest is None:
                raise WorkerDispatchFailedError(
                    "Completed worker result requires a bound terminal receipt"
                )
        elif state in {"FAILED", "TIMED_OUT", "CANCELLED"}:
            if receipt is not None or receipt_digest is not None:
                raise WorkerDispatchFailedError("Failed worker result must not contain a receipt")
            if not isinstance(error, dict):
                raise WorkerDispatchFailedError("Terminal worker failure requires an error")
            self.schema_registry.validate("preflight-error", error)
            if (
                state in {"TIMED_OUT", "CANCELLED"}
                and dispatch_result.get("dispatched") is not True
            ):
                raise WorkerDispatchFailedError(
                    f"Worker state {state} requires an attempted dispatch"
                )
        elif receipt is not None or receipt_digest is not None or error is not None:
            raise WorkerDispatchFailedError(
                "Non-terminal worker result must not contain terminal artifacts"
            )

        return dispatch_result

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
            5. Atomically acquire/check an idempotency reservation.
            6. Resource quota and concurrency check.
            7. Assign UUIDs, determine admission_expires_at, construct AdmissionRecord.
            8. Compute admission_digest and Ed25519 signature over admission \\ signature.
            9. Construct and validate the AuthorizedExecution bundle.
            10. Durably commit the reserved execution identity before dispatch.
            11. Dispatch once to Zone 3 and update the committed status.
            12. Structured audit event logging with secret redaction.
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
        reservation_state, existing = self.idempotency_ledger.acquire_or_check(
            intent_id, intent_digest, subject.subject_id
        )
        if reservation_state == "COMMITTED":
            assert existing is not None
            if existing.admission_record is None or existing.operation is None:
                raise RuntimeError("Durable execution record is missing admission metadata")
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
                admission_id=existing.admission_record["admission_id"],
                admission_digest=existing.admission_record["admission_digest"],
                operation=existing.operation,
                state=existing.status,
                receipt_digest=existing.receipt_digest,
                error=existing.error,
                updated_at=existing.updated_at,
                schema_registry=self.schema_registry,
            )
            return {
                "action": "ALREADY_ADMITTED",
                "admission": copy.deepcopy(existing.admission_record),
                "status": status_doc,
                "receipt": copy.deepcopy(existing.terminal_receipt),
            }

        if reservation_state != "RESERVED":
            raise RuntimeError(f"Unknown idempotency reservation state: {reservation_state}")

        reservation_active = True
        try:
            # 6. Quotas and Resource Grants
            active_count = self.idempotency_ledger.active_count(reservation_intent_id=intent_id)
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

            # 8. Compute admission_digest (excluding admission_digest and authenticator)
            admission_digest = compute_admission_digest(admission_doc)
            admission_doc["admission_digest"] = admission_digest

            # Add explicitly configured authenticator metadata.
            admission_doc["authenticator"] = {
                "algorithm": "ED25519",
                "issuer_id": self.signing_identity.issuer_id,
                "key_id": self.signing_identity.key_id,
            }

            # Sign over RFC8785(admission_doc \ {"authenticator.signature"})
            signature = sign_admission(admission_doc, self.signing_identity.private_key)
            admission_doc["authenticator"]["signature"] = signature

            # Validate schema of AdmissionRecord
            self.schema_registry.validate("admission-record", admission_doc)

            # 9. Assemble and validate AuthorizedExecution bundle
            bundle: dict[str, Any] = {
                "schema_version": "1.0.0",
                "intent": intent,
                "admission": admission_doc,
            }
            self.schema_registry.validate("authorized-execution", bundle)

            # 10. Publish one durable execution identity before external dispatch.
            constraints = intent.get("execution_constraints", {})
            retry_of = constraints.get("retry_of_intent_id")
            ledger_rec = self.idempotency_ledger.commit_admission(
                intent_id=intent_id,
                intent_digest=intent_digest,
                caller_subject_id=subject.subject_id,
                execution_id=execution_id,
                admission_record=copy.deepcopy(admission_doc),
                retry_of_intent_id=retry_of,
                operation=intent["operation"],
            )
            reservation_active = False
        except BaseException:
            if reservation_active:
                self.idempotency_ledger.release_reservation(intent_id)
            raise

        # 11. Dispatch exactly once after the durable identity is visible.
        try:
            dispatch_result = self._validate_dispatch_result(
                self.dispatch_port.dispatch(bundle),
                intent_id=intent_id,
                execution_id=execution_id,
                admission_id=admission_id,
                intent_digest=intent_digest,
                admission_digest=admission_digest,
                operation=intent["operation"],
                controller_commit=self.controller_commit,
                catalog_backend_ref=intent["workload"]["catalog_backend_ref"],
                model_plugin_id=intent["workload"]["model_plugin_id"],
                dataset_id=intent["workload"]["dataset_id"],
                requested_scope=intent["workload"]["requested_scope"],
            )
        except Exception as exc:
            if isinstance(exc, ControllerError):
                controller_error = exc
            else:
                controller_error = WorkerDispatchFailedError()
            stored_error = {
                "schema_version": "1.0.0",
                "error_code": controller_error.code,
                "category": controller_error.category,
                "retryable": controller_error.retryable,
                "message": controller_error.message[:512],
            }
            self.idempotency_ledger.update_execution(
                execution_id,
                status="FAILED",
                error=stored_error,
            )
            self.audit_logger.log_event(
                "EXECUTION_DISPATCH_FAILED",
                subject.subject_id,
                {
                    "intent_id": intent_id,
                    "execution_id": execution_id,
                    "error_code": stored_error["error_code"],
                },
                intent_id=intent_id,
                execution_id=execution_id,
            )
            raise

        worker_state = dispatch_result["status"]
        ledger_rec = self.idempotency_ledger.update_execution(
            execution_id,
            status=worker_state,
            receipt_digest=dispatch_result.get("receipt_digest"),
            terminal_receipt=copy.deepcopy(dispatch_result.get("receipt")),
            error=copy.deepcopy(dispatch_result.get("error")),
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
            operation=intent["operation"],
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
            "receipt": copy.deepcopy(ledger_rec.terminal_receipt),
        }

    def get_status(
        self,
        execution_id: str,
        *,
        credentials: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Rebuild an owner's durable execution status read model after restart."""
        subject = self.auth_port.authenticate(credentials)
        record = self.idempotency_ledger.get_by_execution_id(execution_id)
        if record is None:
            return None
        if record.authenticated_subject_id != subject.subject_id:
            raise UnauthorizedCallerError(
                f"Subject '{subject.subject_id}' cannot read execution '{execution_id}'",
                details={
                    "execution_id": execution_id,
                    "caller_subject_id": subject.subject_id,
                },
            )
        if record.admission_record is None or record.operation is None:
            raise RuntimeError("Durable execution record is missing admission metadata")
        admission = record.admission_record
        return build_execution_status(
            execution_id=record.execution_id,
            intent_id=record.intent_id,
            intent_digest=record.intent_digest,
            admission_id=admission["admission_id"],
            admission_digest=admission["admission_digest"],
            operation=record.operation,
            state=record.status,
            receipt_digest=record.receipt_digest,
            error=record.error,
            updated_at=record.updated_at,
            schema_registry=self.schema_registry,
        )
