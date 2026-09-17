"""Typed controller errors mapped 1:1 to Step 5C error taxonomy."""

from __future__ import annotations

from typing import Any


class ControllerError(Exception):
    """Base error for all Step 5C controller exceptions."""

    def __init__(
        self,
        code: str,
        message: str,
        category: str,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.category = category
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category,
            "retryable": self.retryable,
            "details": self.details,
        }


class SchemaVersionUnsupportedError(ControllerError):
    def __init__(
        self, message: str = "Unsupported schema version", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__("ERR_SCHEMA_VERSION_UNSUPPORTED", message, "SCHEMA", False, details)


class SchemaValidationError(ControllerError):
    def __init__(
        self, message: str = "Schema validation failed", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__("ERR_SCHEMA_VALIDATION_FAILED", message, "SCHEMA", False, details)


class JcsCanonicalizationError(ControllerError):
    def __init__(
        self,
        message: str = "RFC 8785 canonicalization failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            "ERR_JCS_CANONICALIZATION_FAILED", message, "CANONICALIZATION", False, details
        )


class IntentDigestMismatchError(ControllerError):
    def __init__(
        self,
        message: str = "Recomputed RFC 8785 digest does not match declared intent_digest",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_INTENT_DIGEST_MISMATCH", message, "DIGEST", False, details)


class AdmissionDigestMismatchError(ControllerError):
    def __init__(
        self, message: str = "Admission digest mismatch", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__("ERR_ADMISSION_DIGEST_MISMATCH", message, "DIGEST", False, details)


class IntentExpiredError(ControllerError):
    def __init__(
        self,
        message: str = "Intent expires_at is in the past",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_INTENT_EXPIRED", message, "AUTHZ", False, details)


class AdmissionExpiredError(ControllerError):
    def __init__(
        self,
        message: str = "Admission has expired before dispatch",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_ADMISSION_EXPIRED", message, "AUTHZ", False, details)


class AuthenticationRequiredError(ControllerError):
    def __init__(
        self,
        message: str = "Missing or empty caller credentials",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_AUTHENTICATION_REQUIRED", message, "AUTHN", True, details)


class AuthenticationFailedError(ControllerError):
    def __init__(
        self, message: str = "Authentication failed", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__("ERR_AUTHENTICATION_FAILED", message, "AUTHN", False, details)


class UnauthorizedCallerError(ControllerError):
    def __init__(
        self,
        message: str = "Caller identity does not match existing intent owner",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_UNAUTHORIZED_CALLER", message, "AUTHZ", False, details)


class PolicyDeniedError(ControllerError):
    def __init__(
        self,
        message: str = "Governance policy evaluation denied admission",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_POLICY_DENIED", message, "POLICY", False, details)


class RoleForbiddenError(ControllerError):
    def __init__(
        self,
        message: str = "Effective caller roles cannot authorize requested operation",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_ROLE_FORBIDDEN", message, "POLICY", False, details)


class CatalogRefMismatchError(ControllerError):
    def __init__(
        self,
        message: str = "Intent catalog_backend_ref does not match frozen catalog",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_CATALOG_REF_MISMATCH", message, "CATALOG", False, details)


class UnknownPluginIdError(ControllerError):
    def __init__(
        self,
        message: str = "Unknown model_plugin_id not present in catalog",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_UNKNOWN_PLUGIN_ID", message, "CATALOG", False, details)


class UnknownDatasetIdError(ControllerError):
    def __init__(
        self,
        message: str = "Unknown dataset_id not present in catalog",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_UNKNOWN_DATASET_ID", message, "CATALOG", False, details)


class OperationScopeUnsupportedError(ControllerError):
    def __init__(
        self,
        message: str = "Requested operation is not supported under requested scope",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_OPERATION_SCOPE_UNSUPPORTED", message, "CATALOG", False, details)


class IntentIdDigestConflictError(ControllerError):
    def __init__(
        self,
        message: str = "Existing intent_id found with different intent_digest",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_INTENT_ID_DIGEST_CONFLICT", message, "IDEMPOTENCY", False, details)


class IntentCollisionDetectedError(ControllerError):
    def __init__(
        self,
        message: str = "Duplicate intent_digest under a different intent_id detected",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_INTENT_COLLISION_DETECTED", message, "IDEMPOTENCY", False, details)


class QuotaExceededError(ControllerError):
    def __init__(
        self,
        message: str = "Resource quota or concurrency limit exceeded",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_QUOTA_EXCEEDED", message, "RESOURCE", True, details)


class WorkerDispatchFailedError(ControllerError):
    def __init__(
        self,
        message: str = "Failed to dispatch authorized execution bundle to worker",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_WORKER_DISPATCH_FAILED", message, "DISPATCH", True, details)


class AdmissionSignatureInvalidError(ControllerError):
    def __init__(
        self,
        message: str = "Admission signature verification failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_ADMISSION_SIGNATURE_INVALID", message, "WORKER", False, details)


class AuthorizedExecutionParityMismatchError(ControllerError):
    def __init__(
        self,
        message: str = "AuthorizedExecution parity validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH", message, "LINEAGE", False, details
        )


class ReceiptLineageMismatchError(ControllerError):
    def __init__(
        self,
        message: str = "Terminal receipt lineage does not match admitted execution",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_RECEIPT_LINEAGE_MISMATCH", message, "LINEAGE", False, details)


class TimeoutError(ControllerError):
    def __init__(
        self,
        message: str = "Execution exceeded admitted timeout",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_TIMEOUT", message, "WORKER", True, details)


class CancelledError(ControllerError):
    def __init__(
        self, message: str = "Execution was cancelled", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__("ERR_CANCELLED", message, "WORKER", True, details)


class StageCForbiddenError(ControllerError):
    def __init__(
        self,
        message: str = "STAGE_C_REAL_DRQ1 capability cannot be claimed by local live execution",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("ERR_STAGE_C_FORBIDDEN", message, "CONSENSUS_BOUNDARY", False, details)
