"""T017: Preflight validation for AuthorizedExecution bundles."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from deltatorrent.live_execution.crypto import (
    FIXTURE_PUBLIC_KEY_HEX,
    verify_admission_digest,
    verify_admission_signature,
    verify_intent_digest,
)
from deltatorrent.live_execution.errors import WorkerPreflightError


@dataclass(frozen=True, slots=True)
class PreflightContext:
    """Immutable execution context verified by preflight checks."""

    execution_id: str
    intent_id: str
    intent_digest: str
    admission_id: str
    admission_digest: str
    controller_commit: str
    operation: str
    operation_payload: dict[str, Any]
    model_plugin_id: str
    dataset_id: str
    requested_scope: str
    catalog_backend_ref: str
    allow_downloads: bool
    timeout_seconds: int
    max_memory_bytes: int
    admission_expires_at: str
    intent: dict[str, Any]
    admission: dict[str, Any]


class AuthorizedExecutionPreflight:
    """Preflight validator ensuring tamper-evident authority before execution."""

    PINNED_KEY_IDS = frozenset({"step5c-fixture-ed25519"})

    def __init__(
        self,
        trusted_public_key_hex: str | None = None,
        pinned_key_ids: frozenset[str] | set[str] | None = None,
    ) -> None:
        self.trusted_public_key_hex = trusted_public_key_hex or FIXTURE_PUBLIC_KEY_HEX
        self.pinned_key_ids = (
            frozenset(pinned_key_ids) if pinned_key_ids is not None else self.PINNED_KEY_IDS
        )

    def validate(
        self,
        bundle: dict[str, Any],
        current_time: datetime | None = None,
    ) -> PreflightContext:
        """Validate an AuthorizedExecution bundle fail-closed."""
        if not isinstance(bundle, dict):
            raise WorkerPreflightError(
                "ERR_SCHEMA_VALIDATION_FAILED",
                "AuthorizedExecution bundle must be an object",
            )

        if bundle.get("schema_version") != "1.0.0":
            raise WorkerPreflightError(
                "ERR_SCHEMA_VALIDATION_FAILED",
                f"Unsupported schema_version '{bundle.get('schema_version')}'. Expected '1.0.0'",
            )

        intent = bundle.get("intent")
        admission = bundle.get("admission")
        if not isinstance(intent, dict) or not isinstance(admission, dict):
            raise WorkerPreflightError(
                "ERR_SCHEMA_VALIDATION_FAILED",
                "AuthorizedExecution bundle must contain 'intent' and 'admission' objects",
            )

        # 1. Parity checks between intent and admission
        intent_id = intent.get("intent_id")
        adm_intent_id = admission.get("intent_id")
        if not intent_id or intent_id != adm_intent_id:
            raise WorkerPreflightError(
                "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH",
                f"intent_id mismatch: intent has '{intent_id}', admission has '{adm_intent_id}'",
                details={"intent_id": intent_id, "admission_intent_id": adm_intent_id},
            )

        intent_digest = intent.get("intent_digest")
        adm_intent_digest = admission.get("intent_digest")
        if not intent_digest or intent_digest != adm_intent_digest:
            raise WorkerPreflightError(
                "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH",
                "intent_digest parity mismatch between intent and admission",
                details={
                    "intent_digest": intent_digest,
                    "admission_intent_digest": adm_intent_digest,
                },
            )

        # 2. Recompute intent digest and verify parity
        if not verify_intent_digest(intent):
            raise WorkerPreflightError(
                "ERR_INTENT_DIGEST_MISMATCH",
                f"Recomputed digest does not match declared intent_digest '{intent_digest}'",
                details={"declared_digest": intent_digest},
            )

        # 3. Recompute admission digest and verify parity
        if not verify_admission_digest(admission):
            raise WorkerPreflightError(
                "ERR_ADMISSION_DIGEST_MISMATCH",
                "Recomputed digest does not match declared admission_digest",
                details={"declared_digest": admission.get("admission_digest")},
            )

        # 4. Authenticator algorithm and key_id check
        authenticator = admission.get("authenticator", {})
        if not isinstance(authenticator, dict):
            raise WorkerPreflightError(
                "ERR_ADMISSION_SIGNATURE_INVALID",
                "AdmissionRecord missing authenticator block",
            )

        key_id = authenticator.get("key_id")
        algorithm = authenticator.get("algorithm")

        if algorithm != "ED25519":
            raise WorkerPreflightError(
                "ERR_ADMISSION_SIGNATURE_INVALID",
                f"Unsupported signature algorithm '{algorithm}'. Expected ED25519",
            )

        if key_id not in self.pinned_key_ids:
            raise WorkerPreflightError(
                "ERR_ADMISSION_SIGNATURE_INVALID",
                f"Unknown or un-pinned key_id '{key_id}'. Allowed: {sorted(self.pinned_key_ids)}",
            )

        # 5. Ed25519 signature verification
        if not verify_admission_signature(admission, self.trusted_public_key_hex):
            raise WorkerPreflightError(
                "ERR_ADMISSION_SIGNATURE_INVALID",
                "Admission signature verification failed over RFC8785(admission \\ signature)",
            )

        # 6. TTL freshness checks
        now = current_time or datetime.now(UTC)
        admitted_at_str = admission.get("admitted_at")
        admission_expires_at_str = admission.get("admission_expires_at")
        intent_expires_at_str = intent.get("expires_at")

        if not admitted_at_str or not admission_expires_at_str or not intent_expires_at_str:
            raise WorkerPreflightError(
                "ERR_SCHEMA_VALIDATION_FAILED",
                "Missing required TTL timestamp fields",
            )

        try:
            admitted_at = datetime.fromisoformat(admitted_at_str.replace("Z", "+00:00"))
            admission_expires_at = datetime.fromisoformat(
                admission_expires_at_str.replace("Z", "+00:00")
            )
            intent_expires_at = datetime.fromisoformat(intent_expires_at_str.replace("Z", "+00:00"))
        except Exception as exc:
            raise WorkerPreflightError(
                "ERR_SCHEMA_VALIDATION_FAILED",
                f"Malformed ISO-8601 date-time in TTL fields: {exc}",
            ) from exc

        if admitted_at > admission_expires_at:
            raise WorkerPreflightError(
                "ERR_ADMISSION_EXPIRED",
                f"admitted_at ({admitted_at_str}) is after expires_at ({admission_expires_at_str})",
            )

        if admission_expires_at > intent_expires_at:
            raise WorkerPreflightError(
                "ERR_ADMISSION_EXPIRED",
                "admission_expires_at exceeds intent.expires_at",
            )

        if now >= admission_expires_at:
            raise WorkerPreflightError(
                "ERR_ADMISSION_EXPIRED",
                f"Admission expired at {admission_expires_at_str} (now: {now.isoformat()})",
            )

        # 7. Scope and Stage C check
        workload = intent.get("workload", {})
        requested_scope = workload.get("requested_scope")
        if requested_scope == "STAGE_C_REAL_DRQ1":
            raise WorkerPreflightError(
                "ERR_STAGE_C_FORBIDDEN",
                "Local worker adapter cannot execute STAGE_C_REAL_DRQ1 operations",
            )

        operation = intent.get("operation")
        if operation == "TRAIN_TICKET" and requested_scope != "PLUGIN_BOUNDARY":
            raise WorkerPreflightError(
                "ERR_OPERATION_SCOPE_UNSUPPORTED",
                f"TRAIN_TICKET requires scope 'PLUGIN_BOUNDARY', got '{requested_scope}'",
            )

        # 8. Effective resource grants (allow_downloads strictly from admission grant)
        grants = admission.get("resource_grants", {})
        effective_allow_downloads = bool(grants.get("allow_downloads", False))
        timeout_seconds = int(grants.get("timeout_seconds", 900))
        max_memory_bytes = int(grants.get("max_memory_bytes", 2 * 1024 * 1024 * 1024))

        # Sole authoritative execution_id comes from admission.execution_id
        execution_id = admission.get("execution_id")
        if not execution_id:
            raise WorkerPreflightError(
                "ERR_SCHEMA_VALIDATION_FAILED",
                "AdmissionRecord missing authoritative execution_id",
            )

        return PreflightContext(
            execution_id=execution_id,
            intent_id=intent_id,
            intent_digest=intent_digest,
            admission_id=admission.get("admission_id", ""),
            admission_digest=admission.get("admission_digest", ""),
            controller_commit=admission.get("policy_context", {}).get("controller_commit", ""),
            operation=str(operation),
            operation_payload=copy.deepcopy(intent.get("operation_payload", {})),
            model_plugin_id=str(workload.get("model_plugin_id", "")),
            dataset_id=str(workload.get("dataset_id", "")),
            requested_scope=str(requested_scope),
            catalog_backend_ref=str(workload.get("catalog_backend_ref", "")),
            allow_downloads=effective_allow_downloads,
            timeout_seconds=timeout_seconds,
            max_memory_bytes=max_memory_bytes,
            admission_expires_at=admission_expires_at_str,
            intent=copy.deepcopy(intent),
            admission=copy.deepcopy(admission),
        )
