from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
TAXONOMY = ROOT / "taxonomy"
VALID = ROOT / "fixtures" / "valid"
INVALID = ROOT / "fixtures" / "invalid"
VECTORS = ROOT / "vectors"
EVIDENCE = ROOT / "evidence"

CONTRACT_FREEZE_SHA = "66e3e7e5bb07a48aadbee8d9c4683144b812d229"
SCHEMA_VERSION = "1.0.0"
HASH_RE = "^sha256:[0-9a-f]{64}$"
UUID_RE = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
GIT_SHA_RE = "^[0-9a-f]{40}$"
CONTROLLER_COMMIT = "66e3e7e5bb07a48aadbee8d9c4683144b812d229"[:40]
CATALOG_REF = "670b58f6458fe84620f4f9f46401f855d04ae05d"
PRODUCER_COMMIT = "4992d9eca319da21b5a2c7b94593f3668b92329c"
WORKLOAD_CONFIG_DIGEST = "sha256:93caaf42c2a8f1bacb9fbc9bf835a48a8641fd16c416794a7a0ca7f52a0138c8"

# Deterministic public verification vector. No private key material is stored.
FIXTURE_PUBLIC_KEY_HEX = "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8"
FIXTURE_SIGNATURE_HEX = (
    "d9eb4c690692b428d951ce111cf17d3e6f93ea552a23a927506225def9103788"
    "fddd350bc7be9cc691949dc8fccc5edd855b89067bf30a9f4a2952b288ada90f"
)


def _ordered(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            key: _ordered(obj[key])
            for key in sorted(obj, key=lambda item: item.encode("utf-16-be"))
        }
    if isinstance(obj, list):
        return [_ordered(item) for item in obj]
    return obj


def _number_to_jcs(value: int | float) -> str:
    if isinstance(value, bool):
        raise TypeError("bool is not a number")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not valid JCS")
        if value == 0.0:
            return "0"
        if value.is_integer() and abs(value) < 1e21:
            return str(int(value))
        formatted = f"{value:.16g}"
        return formatted.replace("e+0", "e+").replace("e-0", "e-")
    raise TypeError(f"unsupported number type: {type(value)!r}")


def jcs_dumps(obj: Any) -> str:
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return _number_to_jcs(obj)
    if isinstance(obj, list):
        return "[" + ",".join(jcs_dumps(item) for item in obj) + "]"
    if isinstance(obj, dict):
        pieces = []
        for key in sorted(obj, key=lambda item: item.encode("utf-16-be")):
            pieces.append(jcs_dumps(str(key)) + ":" + jcs_dumps(obj[key]))
        return "{" + ",".join(pieces) + "}"
    raise TypeError(f"unsupported JCS value: {type(obj)!r}")


def jcs_bytes(obj: Any) -> bytes:
    return jcs_dumps(obj).encode("utf-8")


def sha256_prefixed(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def without_paths(obj: dict[str, Any], paths: list[tuple[str, ...]]) -> dict[str, Any]:
    result = copy.deepcopy(obj)
    for path in paths:
        cursor: Any = result
        for key in path[:-1]:
            cursor = cursor[key]
        cursor.pop(path[-1], None)
    return result


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_ordered(obj), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base_string_schema(pattern: str | None = None, max_length: int | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string"}
    if pattern is not None:
        schema["pattern"] = pattern
    if max_length is not None:
        schema["maxLength"] = max_length
    return schema


def execution_intent_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://delta.local/schemas/step5c/execution-intent.schema.json",
        "title": "ExecutionIntent",
        "type": "object",
        "required": [
            "schema_version",
            "intent_id",
            "created_at",
            "expires_at",
            "declared_operator",
            "workload",
            "operation",
            "operation_payload",
            "execution_constraints",
            "intent_digest",
        ],
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "intent_id": {"type": "string", "format": "uuid"},
            "created_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": "string", "format": "date-time"},
            "declared_operator": {
                "type": "object",
                "required": ["subject_id", "role"],
                "additionalProperties": False,
                "properties": {
                    "subject_id": {"type": "string", "minLength": 1, "maxLength": 128},
                    "role": {"type": "string", "enum": ["OPERATOR", "RESEARCHER", "AUDITOR"]},
                },
            },
            "workload": {
                "type": "object",
                "required": [
                    "model_plugin_id",
                    "dataset_id",
                    "requested_scope",
                    "catalog_backend_ref",
                ],
                "additionalProperties": False,
                "properties": {
                    "model_plugin_id": base_string_schema("^[a-z0-9-]+$", 64),
                    "dataset_id": base_string_schema("^[a-z0-9-]+$", 64),
                    "requested_scope": {
                        "type": "string",
                        "enum": ["PLUGIN_BOUNDARY", "MODEL_DATASET_BINDING_ONLY"],
                    },
                    "catalog_backend_ref": base_string_schema(GIT_SHA_RE),
                },
            },
            "operation": {
                "type": "string",
                "enum": ["TRAIN_TICKET", "EVALUATE_CHECKPOINT", "MATERIALIZE_DATASET"],
            },
            "operation_payload": {"type": "object"},
            "execution_constraints": {
                "type": "object",
                "required": ["timeout_seconds", "requested_allow_downloads"],
                "additionalProperties": False,
                "properties": {
                    "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
                    "requested_allow_downloads": {"type": "boolean"},
                    "retry_of_intent_id": {"type": "string", "format": "uuid"},
                },
            },
            "intent_digest": base_string_schema(HASH_RE),
        },
        "allOf": [
            {
                "if": {"properties": {"operation": {"const": "TRAIN_TICKET"}}},
                "then": {
                    "properties": {
                        "workload": {
                            "properties": {"requested_scope": {"const": "PLUGIN_BOUNDARY"}}
                        },
                        "operation_payload": {
                            "type": "object",
                            "required": ["ticket_id", "partition_id"],
                            "additionalProperties": False,
                            "properties": {
                                "ticket_id": base_string_schema("^[A-Za-z0-9_-]+$", 64),
                                "partition_id": base_string_schema("^[A-Za-z0-9_-]+$", 64),
                            },
                        },
                    }
                },
            },
            {
                "if": {"properties": {"operation": {"const": "EVALUATE_CHECKPOINT"}}},
                "then": {
                    "properties": {
                        "operation_payload": {
                            "type": "object",
                            "required": ["checkpoint_coordinates"],
                            "additionalProperties": False,
                            "properties": {
                                "checkpoint_coordinates": {
                                    "type": "array",
                                    "items": {
                                        "type": "integer",
                                        "minimum": -2147483648,
                                        "maximum": 2147483647,
                                    },
                                    "minItems": 1,
                                    "maxItems": 4096,
                                }
                            },
                        }
                    }
                },
            },
            {
                "if": {"properties": {"operation": {"const": "MATERIALIZE_DATASET"}}},
                "then": {
                    "properties": {
                        "operation_payload": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {"cache_key": base_string_schema("^[A-Za-z0-9_-]+$", 64)},
                        }
                    }
                },
            },
        ],
    }


def admission_record_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://delta.local/schemas/step5c/admission-record.schema.json",
        "title": "AdmissionRecord",
        "type": "object",
        "required": [
            "schema_version",
            "admission_id",
            "intent_id",
            "intent_digest",
            "execution_id",
            "authenticated_subject",
            "policy_context",
            "resource_grants",
            "admitted_at",
            "admission_expires_at",
            "admission_digest",
            "authenticator",
        ],
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "admission_id": {"type": "string", "format": "uuid"},
            "intent_id": {"type": "string", "format": "uuid"},
            "intent_digest": base_string_schema(HASH_RE),
            "execution_id": {"type": "string", "format": "uuid"},
            "authenticated_subject": {
                "type": "object",
                "required": ["subject_id", "authenticated_via", "effective_roles"],
                "additionalProperties": False,
                "properties": {
                    "subject_id": {"type": "string", "maxLength": 128},
                    "authenticated_via": {
                        "type": "string",
                        "enum": ["LOCAL_PEER_CREDENTIAL", "MTLS", "TOKEN"],
                    },
                    "effective_roles": {"type": "array", "items": {"type": "string"}},
                },
            },
            "policy_context": {
                "type": "object",
                "required": ["policy_version", "controller_commit", "verdict"],
                "additionalProperties": False,
                "properties": {
                    "policy_version": {"type": "string", "maxLength": 64},
                    "controller_commit": base_string_schema(GIT_SHA_RE),
                    "verdict": {"type": "string", "const": "ADMITTED"},
                },
            },
            "resource_grants": {
                "type": "object",
                "required": ["max_memory_bytes", "timeout_seconds", "allow_downloads"],
                "additionalProperties": False,
                "properties": {
                    "max_memory_bytes": {"type": "integer", "minimum": 1},
                    "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
                    "allow_downloads": {"type": "boolean"},
                },
            },
            "admitted_at": {"type": "string", "format": "date-time"},
            "admission_expires_at": {"type": "string", "format": "date-time"},
            "admission_digest": base_string_schema(HASH_RE),
            "authenticator": {
                "type": "object",
                "required": ["issuer_id", "key_id", "algorithm", "signature"],
                "additionalProperties": False,
                "properties": {
                    "issuer_id": {"type": "string", "maxLength": 128},
                    "key_id": base_string_schema("^[a-z0-9-]+$", 64),
                    "algorithm": {"type": "string", "const": "ED25519"},
                    "signature": base_string_schema("^[0-9a-f]{128}$"),
                },
            },
        },
    }


def authorized_execution_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://delta.local/schemas/step5c/authorized-execution.schema.json",
        "title": "AuthorizedExecution",
        "type": "object",
        "required": ["schema_version", "intent", "admission"],
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "intent": {"$ref": "#/$defs/ExecutionIntent"},
            "admission": {"$ref": "#/$defs/AdmissionRecord"},
        },
        "$defs": {
            "ExecutionIntent": strip_schema_header(execution_intent_schema()),
            "AdmissionRecord": strip_schema_header(admission_record_schema()),
        },
    }


def error_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://delta.local/schemas/step5c/preflight-error.schema.json",
        "title": "Step5CError",
        "type": "object",
        "required": ["schema_version", "error_code", "category", "retryable", "message"],
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "error_code": {"type": "string", "enum": [item["code"] for item in error_taxonomy()]},
            "category": {
                "type": "string",
                "enum": [
                    "SCHEMA",
                    "CANONICALIZATION",
                    "DIGEST",
                    "AUTHN",
                    "AUTHZ",
                    "POLICY",
                    "CATALOG",
                    "IDEMPOTENCY",
                    "RESOURCE",
                    "DISPATCH",
                    "WORKER",
                    "LINEAGE",
                    "CONSENSUS_BOUNDARY",
                ],
            },
            "retryable": {"type": "boolean"},
            "message": {"type": "string", "minLength": 1, "maxLength": 512},
        },
    }


def execution_status_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://delta.local/schemas/step5c/execution-status.schema.json",
        "title": "ExecutionStatus",
        "type": "object",
        "required": [
            "schema_version",
            "execution_id",
            "intent_id",
            "intent_digest",
            "admission_id",
            "admission_digest",
            "state",
            "updated_at",
        ],
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "execution_id": {"type": "string", "format": "uuid"},
            "intent_id": {"type": "string", "format": "uuid"},
            "intent_digest": base_string_schema(HASH_RE),
            "admission_id": {"type": "string", "format": "uuid"},
            "admission_digest": base_string_schema(HASH_RE),
            "operation": {
                "type": "string",
                "enum": [
                    "TRAIN_TICKET",
                    "EVALUATE_CHECKPOINT",
                    "MATERIALIZE_DATASET",
                ],
            },
            "state": {
                "type": "string",
                "enum": [
                    "ADMITTED",
                    "QUEUED",
                    "RUNNING",
                    "COMPLETED",
                    "FAILED",
                    "TIMED_OUT",
                    "CANCELLED",
                    "STALE_UNAVAILABLE",
                ],
            },
            "updated_at": {"type": "string", "format": "date-time"},
            "terminal": {"type": "boolean"},
            "receipt_digest": base_string_schema(HASH_RE),
            "error": {"$ref": "preflight-error.schema.json"},
        },
        "allOf": [
            {
                "if": {"properties": {"state": {"enum": ["FAILED", "TIMED_OUT", "CANCELLED"]}}},
                "then": {"required": ["error"]},
            },
            {
                "if": {
                    "properties": {
                        "state": {"const": "COMPLETED"},
                        "operation": {"const": "MATERIALIZE_DATASET"},
                    },
                    "required": ["state", "operation"],
                },
                "then": {},
                "else": {
                    "if": {"properties": {"state": {"const": "COMPLETED"}}, "required": ["state"]},
                    "then": {"required": ["receipt_digest"]},
                },
            },
        ],
    }


def receipt_lineage_extension_schema() -> dict[str, Any]:
    forbidden_consensus = [
        "round_id",
        "state_root",
        "wal_sequence",
        "qc",
        "apply_qc",
        "consensus_round",
        "validator_signatures",
        "bft_quorum",
        "stage_c_claim",
        "consensus_view",
    ]
    forbidden_rule: dict[str, Any] = {
        "not": {
            "anyOf": [{"required": [field]} for field in forbidden_consensus],
        },
        "propertyNames": {
            "not": {"enum": forbidden_consensus},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://delta.local/schemas/step5c/execution-receipt-lineage-extension.schema.json",
        "title": "ExecutionReceiptLineageExtension",
        "type": "object",
        "required": ["schema_version", "receipt_type", "provenance", "workload", "execution"],
        "additionalProperties": True,
        "not": forbidden_rule["not"],
        "propertyNames": forbidden_rule["propertyNames"],
        "properties": {
            "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "receipt_type": {"type": "string", "const": "DELTAREDUCE_EXECUTION_RECEIPT"},
            "provenance": {
                "type": "object",
                "required": [
                    "repository",
                    "backend_commit",
                    "catalog_backend_ref",
                    "producer_commit",
                    "controller_commit",
                    "produced_at",
                    "intent_id",
                    "intent_digest",
                    "admission_id",
                    "admission_digest",
                    "execution_id",
                ],
                "additionalProperties": True,
                "not": forbidden_rule["not"],
                "propertyNames": forbidden_rule["propertyNames"],
                "properties": {
                    "repository": {"type": "string", "const": "chartjs333/delta"},
                    "backend_commit": base_string_schema(GIT_SHA_RE),
                    "catalog_backend_ref": base_string_schema(GIT_SHA_RE),
                    "producer_commit": base_string_schema(GIT_SHA_RE),
                    "controller_commit": base_string_schema(GIT_SHA_RE),
                    "produced_at": {"type": "string", "format": "date-time"},
                    "intent_id": {"type": "string", "format": "uuid"},
                    "intent_digest": base_string_schema(HASH_RE),
                    "admission_id": {"type": "string", "format": "uuid"},
                    "admission_digest": base_string_schema(HASH_RE),
                    "execution_id": {"type": "string", "format": "uuid"},
                },
            },
            "workload": {
                "type": "object",
                "required": [
                    "model_plugin_id",
                    "dataset_id",
                    "executed_scope",
                    "workload_config_digest",
                ],
                "additionalProperties": True,
                "not": forbidden_rule["not"],
                "propertyNames": forbidden_rule["propertyNames"],
                "properties": {
                    "model_plugin_id": base_string_schema("^[a-z0-9-]+$", 64),
                    "dataset_id": base_string_schema("^[a-z0-9-]+$", 64),
                    "executed_scope": {
                        "type": "string",
                        "enum": ["PLUGIN_BOUNDARY", "MODEL_DATASET_BINDING_ONLY"],
                    },
                    "workload_config_digest": base_string_schema(HASH_RE),
                },
            },
            "execution": {
                "type": "object",
                "required": ["verdict", "terminal_status"],
                "additionalProperties": True,
                "not": forbidden_rule["not"],
                "propertyNames": forbidden_rule["propertyNames"],
                "properties": {
                    "verdict": {"type": "string", "enum": ["SUCCESS", "FAILED"]},
                    "terminal_status": {
                        "type": "string",
                        "enum": ["COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"],
                    },
                },
            },
        },
    }


def strip_schema_header(schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(schema)
    result.pop("$schema", None)
    result.pop("$id", None)
    result.pop("title", None)
    return result


def error_taxonomy() -> list[dict[str, Any]]:
    return [
        {"code": "ERR_SCHEMA_VERSION_UNSUPPORTED", "category": "SCHEMA", "retryable": False},
        {"code": "ERR_SCHEMA_VALIDATION_FAILED", "category": "SCHEMA", "retryable": False},
        {
            "code": "ERR_JCS_CANONICALIZATION_FAILED",
            "category": "CANONICALIZATION",
            "retryable": False,
        },
        {"code": "ERR_INTENT_DIGEST_MISMATCH", "category": "DIGEST", "retryable": False},
        {"code": "ERR_ADMISSION_DIGEST_MISMATCH", "category": "DIGEST", "retryable": False},
        {"code": "ERR_INTENT_EXPIRED", "category": "AUTHZ", "retryable": False},
        {"code": "ERR_ADMISSION_EXPIRED", "category": "AUTHZ", "retryable": False},
        {"code": "ERR_AUTHENTICATION_REQUIRED", "category": "AUTHN", "retryable": True},
        {"code": "ERR_AUTHENTICATION_FAILED", "category": "AUTHN", "retryable": False},
        {"code": "ERR_UNAUTHORIZED_CALLER", "category": "AUTHZ", "retryable": False},
        {"code": "ERR_POLICY_DENIED", "category": "POLICY", "retryable": False},
        {"code": "ERR_ROLE_FORBIDDEN", "category": "POLICY", "retryable": False},
        {"code": "ERR_CATALOG_REF_MISMATCH", "category": "CATALOG", "retryable": False},
        {"code": "ERR_UNKNOWN_PLUGIN_ID", "category": "CATALOG", "retryable": False},
        {"code": "ERR_UNKNOWN_DATASET_ID", "category": "CATALOG", "retryable": False},
        {"code": "ERR_OPERATION_SCOPE_UNSUPPORTED", "category": "CATALOG", "retryable": False},
        {"code": "ERR_INTENT_ID_DIGEST_CONFLICT", "category": "IDEMPOTENCY", "retryable": False},
        {"code": "ERR_INTENT_COLLISION_DETECTED", "category": "IDEMPOTENCY", "retryable": False},
        {"code": "ERR_QUOTA_EXCEEDED", "category": "RESOURCE", "retryable": True},
        {"code": "ERR_WORKER_DISPATCH_FAILED", "category": "DISPATCH", "retryable": True},
        {"code": "ERR_ADMISSION_SIGNATURE_INVALID", "category": "WORKER", "retryable": False},
        {
            "code": "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH",
            "category": "LINEAGE",
            "retryable": False,
        },
        {"code": "ERR_RECEIPT_LINEAGE_MISMATCH", "category": "LINEAGE", "retryable": False},
        {"code": "ERR_TIMEOUT", "category": "WORKER", "retryable": True},
        {"code": "ERR_CANCELLED", "category": "WORKER", "retryable": True},
        {"code": "ERR_STAGE_C_FORBIDDEN", "category": "CONSENSUS_BOUNDARY", "retryable": False},
    ]


def taxonomy_document() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_freeze_sha": CONTRACT_FREEZE_SHA,
        "errors": error_taxonomy(),
    }


def valid_intent_train() -> dict[str, Any]:
    intent = {
        "schema_version": SCHEMA_VERSION,
        "intent_id": "11111111-1111-4111-8111-111111111111",
        "created_at": "2026-09-17T14:30:00.000Z",
        "expires_at": "2026-09-17T14:40:00.000Z",
        "declared_operator": {"subject_id": "operator.alpha", "role": "OPERATOR"},
        "workload": {
            "model_plugin_id": "tabular-10gene-phenotype-v1",
            "dataset_id": "synthetic-10gene-cohort-v1",
            "requested_scope": "PLUGIN_BOUNDARY",
            "catalog_backend_ref": CATALOG_REF,
        },
        "operation": "TRAIN_TICKET",
        "operation_payload": {"ticket_id": "ticket_A-0001", "partition_id": "partition_00"},
        "execution_constraints": {
            "timeout_seconds": 900,
            "requested_allow_downloads": False,
            "retry_of_intent_id": "00000000-0000-4000-8000-000000000001",
        },
    }
    return with_intent_digest(intent)


def valid_intent_checkpoint() -> dict[str, Any]:
    intent = {
        "schema_version": SCHEMA_VERSION,
        "intent_id": "22222222-2222-4222-8222-222222222222",
        "created_at": "2026-09-17T14:31:00.000Z",
        "expires_at": "2026-09-17T14:41:00.000Z",
        "declared_operator": {"subject_id": "operator.unicode.é", "role": "RESEARCHER"},
        "workload": {
            "model_plugin_id": "tabular-10gene-phenotype-v1",
            "dataset_id": "synthetic-10gene-cohort-v1",
            "requested_scope": "MODEL_DATASET_BINDING_ONLY",
            "catalog_backend_ref": CATALOG_REF,
        },
        "operation": "EVALUATE_CHECKPOINT",
        "operation_payload": {"checkpoint_coordinates": [-2147483648, 0, 2147483647]},
        "execution_constraints": {"timeout_seconds": 3600, "requested_allow_downloads": False},
    }
    return with_intent_digest(intent)


def valid_intent_materialize() -> dict[str, Any]:
    intent = {
        "schema_version": SCHEMA_VERSION,
        "intent_id": "33333333-3333-4333-8333-333333333333",
        "created_at": "2026-09-17T14:32:00.000Z",
        "expires_at": "2026-09-17T14:42:00.000Z",
        "declared_operator": {"subject_id": "auditor.local", "role": "AUDITOR"},
        "workload": {
            "model_plugin_id": "mnist-centroid-v1",
            "dataset_id": "mnist-v1",
            "requested_scope": "MODEL_DATASET_BINDING_ONLY",
            "catalog_backend_ref": CATALOG_REF,
        },
        "operation": "MATERIALIZE_DATASET",
        "operation_payload": {"cache_key": "mnist_eval_cache"},
        "execution_constraints": {"timeout_seconds": 60, "requested_allow_downloads": False},
    }
    return with_intent_digest(intent)


def with_intent_digest(intent_without_digest: dict[str, Any]) -> dict[str, Any]:
    intent = copy.deepcopy(intent_without_digest)
    intent["intent_digest"] = sha256_prefixed(jcs_bytes(intent))
    return intent


def public_key_hex() -> str:
    return FIXTURE_PUBLIC_KEY_HEX


def sign_admission(admission_without_digest_auth: dict[str, Any]) -> dict[str, Any]:
    admission = copy.deepcopy(admission_without_digest_auth)
    admission["admission_digest"] = sha256_prefixed(jcs_bytes(admission))
    admission["authenticator"] = {
        "issuer_id": "step5c-fixture-controller",
        "key_id": "step5c-fixture-ed25519",
        "algorithm": "ED25519",
    }
    admission["authenticator"]["signature"] = FIXTURE_SIGNATURE_HEX
    return admission


def valid_admission(intent: dict[str, Any]) -> dict[str, Any]:
    return sign_admission(
        {
            "schema_version": SCHEMA_VERSION,
            "admission_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "intent_id": intent["intent_id"],
            "intent_digest": intent["intent_digest"],
            "execution_id": "55555555-5555-4555-8555-555555555555",
            "authenticated_subject": {
                "subject_id": "operator.alpha",
                "authenticated_via": "LOCAL_PEER_CREDENTIAL",
                "effective_roles": ["OPERATOR"],
            },
            "policy_context": {
                "policy_version": "step5c-policy-v1",
                "controller_commit": CONTROLLER_COMMIT,
                "verdict": "ADMITTED",
            },
            "resource_grants": {
                "max_memory_bytes": 2147483648,
                "timeout_seconds": 900,
                "allow_downloads": False,
            },
            "admitted_at": "2026-09-17T14:30:05.000Z",
            "admission_expires_at": "2026-09-17T14:35:00.000Z",
        }
    )


def valid_authorized_execution() -> dict[str, Any]:
    intent = valid_intent_train()
    return {
        "schema_version": SCHEMA_VERSION,
        "intent": intent,
        "admission": valid_admission(intent),
    }


def valid_status(authorized: dict[str, Any]) -> dict[str, Any]:
    admission = authorized["admission"]
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": admission["execution_id"],
        "intent_id": admission["intent_id"],
        "intent_digest": admission["intent_digest"],
        "admission_id": admission["admission_id"],
        "admission_digest": admission["admission_digest"],
        "operation": authorized["intent"].get("operation", "TRAIN_TICKET"),
        "state": "COMPLETED",
        "updated_at": "2026-09-17T14:35:30.000Z",
        "terminal": True,
        "receipt_digest": "sha256:93caaf42c2a8f1bacb9fbc9bf835a48a8641fd16c416794a7a0ca7f52a0138c8",
    }


def valid_status_materialize(authorized: dict[str, Any]) -> dict[str, Any]:
    admission = authorized["admission"]
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": admission["execution_id"],
        "intent_id": admission["intent_id"],
        "intent_digest": admission["intent_digest"],
        "admission_id": admission["admission_id"],
        "admission_digest": admission["admission_digest"],
        "operation": "MATERIALIZE_DATASET",
        "state": "COMPLETED",
        "updated_at": "2026-09-17T14:35:30.000Z",
        "terminal": True,
    }


def valid_receipt_lineage(authorized: dict[str, Any]) -> dict[str, Any]:
    intent = authorized["intent"]
    admission = authorized["admission"]
    return {
        "schema_version": SCHEMA_VERSION,
        "receipt_type": "DELTAREDUCE_EXECUTION_RECEIPT",
        "provenance": {
            "repository": "chartjs333/delta",
            "backend_commit": CATALOG_REF,
            "catalog_backend_ref": CATALOG_REF,
            "producer_commit": PRODUCER_COMMIT,
            "controller_commit": CONTROLLER_COMMIT,
            "produced_at": "2026-09-17T14:35:30.000Z",
            "intent_id": intent["intent_id"],
            "intent_digest": intent["intent_digest"],
            "admission_id": admission["admission_id"],
            "admission_digest": admission["admission_digest"],
            "execution_id": admission["execution_id"],
        },
        "workload": {
            "model_plugin_id": intent["workload"]["model_plugin_id"],
            "dataset_id": intent["workload"]["dataset_id"],
            "executed_scope": intent["workload"]["requested_scope"],
            "workload_config_digest": WORKLOAD_CONFIG_DIGEST,
        },
        "execution": {"verdict": "SUCCESS", "terminal_status": "COMPLETED"},
    }


@dataclass(frozen=True)
class SchemaCase:
    name: str
    schema_name: str
    document: dict[str, Any]
    expected_error: str


def invalid_cases() -> list[SchemaCase]:
    train = valid_intent_train()
    unknown_operation = copy.deepcopy(train)
    unknown_operation["operation"] = "EVALUATE_SPLIT"
    unknown_operation["intent_digest"] = sha256_prefixed(
        jcs_bytes(without_paths(unknown_operation, [("intent_digest",)]))
    )

    extra_property = copy.deepcopy(train)
    extra_property["shell"] = "python run.py"
    extra_property["intent_digest"] = sha256_prefixed(
        jcs_bytes(without_paths(extra_property, [("intent_digest",)]))
    )

    wrong_scope = copy.deepcopy(train)
    wrong_scope["workload"]["requested_scope"] = "MODEL_DATASET_BINDING_ONLY"
    wrong_scope["intent_digest"] = sha256_prefixed(
        jcs_bytes(without_paths(wrong_scope, [("intent_digest",)]))
    )

    checkpoint_overflow = valid_intent_checkpoint()
    checkpoint_overflow["operation_payload"]["checkpoint_coordinates"] = [2147483648]
    checkpoint_overflow["intent_digest"] = sha256_prefixed(
        jcs_bytes(without_paths(checkpoint_overflow, [("intent_digest",)]))
    )

    invalid_admission = valid_admission(train)
    invalid_admission["resource_grants"]["allow_downloads"] = "false"

    invalid_authorized = valid_authorized_execution()
    invalid_authorized["admission"]["intent_id"] = "99999999-9999-4999-8999-999999999999"

    receipt_with_consensus = valid_receipt_lineage(valid_authorized_execution())
    receipt_with_consensus["provenance"]["wal_sequence"] = 7

    receipt_top_consensus = valid_receipt_lineage(valid_authorized_execution())
    receipt_top_consensus["round_id"] = 1

    receipt_workload_consensus = valid_receipt_lineage(valid_authorized_execution())
    receipt_workload_consensus["workload"]["qc"] = "consensus_quorum_certificate"

    receipt_execution_consensus = valid_receipt_lineage(valid_authorized_execution())
    zero_hash = "sha256:" + ("0" * 64)
    receipt_execution_consensus["execution"]["state_root"] = zero_hash

    status_missing_receipt = copy.deepcopy(valid_status(valid_authorized_execution()))
    status_missing_receipt["operation"] = "TRAIN_TICKET"
    status_missing_receipt.pop("receipt_digest", None)

    return [
        SchemaCase(
            "execution-intent.unknown-operation",
            "execution-intent",
            unknown_operation,
            "ERR_SCHEMA_VALIDATION_FAILED",
        ),
        SchemaCase(
            "execution-intent.extra-property",
            "execution-intent",
            extra_property,
            "ERR_SCHEMA_VALIDATION_FAILED",
        ),
        SchemaCase(
            "execution-intent.train-ticket-wrong-scope",
            "execution-intent",
            wrong_scope,
            "ERR_OPERATION_SCOPE_UNSUPPORTED",
        ),
        SchemaCase(
            "execution-intent.checkpoint-overflow",
            "execution-intent",
            checkpoint_overflow,
            "ERR_SCHEMA_VALIDATION_FAILED",
        ),
        SchemaCase(
            "admission-record.invalid-grant-type",
            "admission-record",
            invalid_admission,
            "ERR_SCHEMA_VALIDATION_FAILED",
        ),
        SchemaCase(
            "authorized-execution.intent-id-mismatch",
            "authorized-execution",
            invalid_authorized,
            "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH",
        ),
        SchemaCase(
            "receipt-lineage.consensus-field",
            "execution-receipt-lineage-extension",
            receipt_with_consensus,
            "ERR_STAGE_C_FORBIDDEN",
        ),
        SchemaCase(
            "receipt-lineage.top-level-consensus-claim",
            "execution-receipt-lineage-extension",
            receipt_top_consensus,
            "ERR_STAGE_C_FORBIDDEN",
        ),
        SchemaCase(
            "receipt-lineage.workload-consensus-claim",
            "execution-receipt-lineage-extension",
            receipt_workload_consensus,
            "ERR_STAGE_C_FORBIDDEN",
        ),
        SchemaCase(
            "receipt-lineage.execution-consensus-claim",
            "execution-receipt-lineage-extension",
            receipt_execution_consensus,
            "ERR_STAGE_C_FORBIDDEN",
        ),
        SchemaCase(
            "execution-status.completed-without-receipt-for-train-ticket",
            "execution-status",
            status_missing_receipt,
            "ERR_SCHEMA_VALIDATION_FAILED",
        ),
    ]


def schema_map() -> dict[str, dict[str, Any]]:
    return {
        "execution-intent": execution_intent_schema(),
        "admission-record": admission_record_schema(),
        "authorized-execution": authorized_execution_schema(),
        "preflight-error": error_schema(),
        "execution-status": execution_status_schema(),
        "execution-receipt-lineage-extension": receipt_lineage_extension_schema(),
    }


def materialize() -> None:
    for directory in [SCHEMAS, TAXONOMY, VALID, INVALID, VECTORS, EVIDENCE]:
        directory.mkdir(parents=True, exist_ok=True)

    schemas = schema_map()
    for name, schema in schemas.items():
        write_json(SCHEMAS / f"{name}.schema.json", schema)

    write_json(TAXONOMY / "errors.json", taxonomy_document())

    train = valid_intent_train()
    checkpoint = valid_intent_checkpoint()
    materialize_dataset = valid_intent_materialize()
    admission = valid_admission(train)
    authorized = {"schema_version": SCHEMA_VERSION, "intent": train, "admission": admission}
    status = valid_status(authorized)
    receipt = valid_receipt_lineage(authorized)

    admission_materialize = valid_admission(materialize_dataset)
    authorized_materialize = {
        "schema_version": SCHEMA_VERSION,
        "intent": materialize_dataset,
        "admission": admission_materialize,
    }
    status_materialize = valid_status_materialize(authorized_materialize)

    valid_docs = {
        "execution-intent.train-ticket": train,
        "execution-intent.evaluate-checkpoint": checkpoint,
        "execution-intent.materialize-dataset": materialize_dataset,
        "admission-record.train-ticket": admission,
        "authorized-execution.train-ticket": authorized,
        "execution-status.completed": status,
        "execution-status.materialize-dataset.completed": status_materialize,
        "execution-receipt-lineage-extension.train-ticket": receipt,
    }
    for name, doc in valid_docs.items():
        write_json(VALID / f"{name}.json", doc)

    invalid_manifest = []
    for case in invalid_cases():
        write_json(INVALID / f"{case.name}.json", case.document)
        invalid_manifest.append(
            {
                "name": case.name,
                "schema": case.schema_name,
                "expected_error": case.expected_error,
            }
        )
    write_json(
        INVALID / "manifest.json", {"schema_version": SCHEMA_VERSION, "cases": invalid_manifest}
    )

    canonical_vectors = build_vectors(authorized, status, receipt, status_materialize)
    for name, vector in canonical_vectors.items():
        write_json(VECTORS / f"{name}.json", vector)

    write_json(EVIDENCE / "artifact-manifest.json", artifact_manifest())


def build_vectors(
    authorized: dict[str, Any],
    status: dict[str, Any],
    receipt: dict[str, Any],
    status_materialize: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intent = authorized["intent"]
    admission = authorized["admission"]
    unicode_probe = {
        "z": "last",
        "é": "latin-small-e-acute",
        "a": "first",
        "emoji": "😀",
        "nested": {"Ω": 1, "A": 2},
    }
    intent_input = without_paths(intent, [("intent_digest",)])
    admission_digest_input = without_paths(admission, [("admission_digest",), ("authenticator",)])
    admission_signature_input = without_paths(admission, [("authenticator", "signature")])

    reference_vectors = [
        {"name": "number-zero", "value": {"val": 0}},
        {"name": "number-negative-zero", "value": {"val": -0}},
        {"name": "number-positive-int", "value": {"val": 42}},
        {"name": "number-negative-int", "value": {"val": -42}},
        {"name": "number-max-safe-int", "value": {"val": 9007199254740991}},
        {"name": "number-min-safe-int", "value": {"val": -9007199254740991}},
        {"name": "number-large-int", "value": {"val": 1000000000000000}},
        {"name": "number-fraction", "value": {"val": 1.25}},
        {"name": "empty-structures", "value": {"arr": [], "obj": {}}},
        {"name": "string-escapes", "value": {"escapes": '"\\\b\f\n\r\t'}},
        {"name": "unicode-surrogate-pairs", "value": {"emoji": "😀", "music": "𝄞"}},
        {"name": "nested-arrays-and-objects", "value": {"a": [1, {"b": [2, 3]}], "c": 4}},
    ]
    built_reference_vectors = [
        {
            "name": ref["name"],
            "value": ref["value"],
            "canonical_json": jcs_dumps(ref["value"]),
            "sha256": sha256_prefixed(jcs_bytes(ref["value"])),
        }
        for ref in reference_vectors
    ]

    return {
        "jcs-golden-vectors": {
            "schema_version": SCHEMA_VERSION,
            "vectors": [
                {
                    "name": "unicode-key-order",
                    "value": unicode_probe,
                    "canonical_json": jcs_dumps(unicode_probe),
                    "sha256": sha256_prefixed(jcs_bytes(unicode_probe)),
                },
                {
                    "name": "execution-intent-train-ticket-without-digest",
                    "value": intent_input,
                    "canonical_json": jcs_dumps(intent_input),
                    "sha256": intent["intent_digest"],
                },
                {
                    "name": "admission-record-without-digest-authenticator",
                    "value": admission_digest_input,
                    "canonical_json": jcs_dumps(admission_digest_input),
                    "sha256": admission["admission_digest"],
                },
                {
                    "name": "admission-record-without-signature",
                    "value": admission_signature_input,
                    "canonical_json": jcs_dumps(admission_signature_input),
                    "sha256": sha256_prefixed(jcs_bytes(admission_signature_input)),
                },
                *built_reference_vectors,
            ],
        },
        "sha256-vectors": {
            "schema_version": SCHEMA_VERSION,
            "vectors": [
                {"name": "authorized-execution", "sha256": sha256_prefixed(jcs_bytes(authorized))},
                {"name": "execution-status", "sha256": sha256_prefixed(jcs_bytes(status))},
                *(
                    [
                        {
                            "name": "execution-status-materialize-dataset",
                            "sha256": sha256_prefixed(jcs_bytes(status_materialize)),
                        }
                    ]
                    if status_materialize is not None
                    else []
                ),
                {
                    "name": "receipt-lineage-extension",
                    "sha256": sha256_prefixed(jcs_bytes(receipt)),
                },
            ],
        },
        "ed25519-fixture": {
            "schema_version": SCHEMA_VERSION,
            "algorithm": "ED25519",
            "public_key_hex": public_key_hex(),
            "signed_input": {
                "description": 'RFC8785(AdmissionRecord \\ {"authenticator.signature"})',
                "canonical_json": jcs_dumps(admission_signature_input),
                "sha256": sha256_prefixed(jcs_bytes(admission_signature_input)),
            },
            "signature_hex": admission["authenticator"]["signature"],
            "admission_id": admission["admission_id"],
            "key_id": admission["authenticator"]["key_id"],
        },
    }


def artifact_manifest() -> dict[str, Any]:
    files = []
    excluded = {"evidence/artifact-manifest.json", "evidence/validation-report.json"}
    for path in sorted(ROOT.rglob("*")):
        relative_path = path.relative_to(ROOT).as_posix()
        if (
            path.is_file()
            and relative_path not in excluded
            and "__pycache__" not in path.parts
            and ".pytest_cache" not in path.parts
        ):
            file_bytes = path.stat().st_size
            file_sha = hash_file(path)
            entry: dict[str, Any] = {
                "path": relative_path,
                "file_bytes": file_bytes,
                "file_sha256": f"sha256:{file_sha}",
                "bytes": file_bytes,
                "sha256": file_sha,
            }
            if path.suffix == ".json":
                try:
                    data = read_json(path)
                    entry["canonical_digest"] = sha256_prefixed(jcs_bytes(data))
                except Exception:
                    pass
            files.append(entry)
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_freeze_sha": CONTRACT_FREEZE_SHA,
        "tasks": ["step5c:T005", "step5c:T006", "step5c:T007", "step5c:T008", "step5c:T009"],
        "artifact_count": len(files),
        "artifacts": files,
    }


def validate_schema_doc(schema_name: str, doc: dict[str, Any]) -> list[ValidationError]:
    schema = read_json(SCHEMAS / f"{schema_name}.schema.json")
    if schema_name == "execution-status":
        schema = copy.deepcopy(schema)
        schema["properties"]["error"] = strip_schema_header(
            read_json(SCHEMAS / "preflight-error.schema.json")
        )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return sorted(validator.iter_errors(doc), key=lambda error: list(error.path))


def verify_intent_digest(intent: dict[str, Any]) -> bool:
    return intent.get("intent_digest") == sha256_prefixed(
        jcs_bytes(without_paths(intent, [("intent_digest",)]))
    )


def verify_admission_digest(admission: dict[str, Any]) -> bool:
    digest_input = without_paths(admission, [("admission_digest",), ("authenticator",)])
    return admission.get("admission_digest") == sha256_prefixed(jcs_bytes(digest_input))


def verify_admission_signature(admission: dict[str, Any]) -> bool:
    signature = bytes.fromhex(admission["authenticator"]["signature"])
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex()))
    signed = without_paths(admission, [("authenticator", "signature")])
    try:
        public_key.verify(signature, jcs_bytes(signed))
    except Exception:
        return False
    return True


def verify_authorized_parity(bundle: dict[str, Any]) -> bool:
    intent = bundle["intent"]
    admission = bundle["admission"]
    return (
        intent["intent_id"] == admission["intent_id"]
        and intent["intent_digest"] == admission["intent_digest"]
        and verify_intent_digest(intent)
        and verify_admission_digest(admission)
        and verify_admission_signature(admission)
    )


def verify_all(write_report: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    valid_expectations = {
        "execution-intent.train-ticket.json": "execution-intent",
        "execution-intent.evaluate-checkpoint.json": "execution-intent",
        "execution-intent.materialize-dataset.json": "execution-intent",
        "admission-record.train-ticket.json": "admission-record",
        "authorized-execution.train-ticket.json": "authorized-execution",
        "execution-status.completed.json": "execution-status",
        "execution-status.materialize-dataset.completed.json": "execution-status",
        "execution-receipt-lineage-extension.train-ticket.json": (
            "execution-receipt-lineage-extension"
        ),
    }
    for file_name, schema_name in valid_expectations.items():
        doc = read_json(VALID / file_name)
        schema_errors = validate_schema_doc(schema_name, doc)
        if schema_errors:
            errors.append(f"{file_name} failed schema {schema_name}: {schema_errors[0].message}")

    train = read_json(VALID / "execution-intent.train-ticket.json")
    checkpoint = read_json(VALID / "execution-intent.evaluate-checkpoint.json")
    materialize_dataset = read_json(VALID / "execution-intent.materialize-dataset.json")
    for name, intent in [
        ("train", train),
        ("checkpoint", checkpoint),
        ("materialize", materialize_dataset),
    ]:
        if not verify_intent_digest(intent):
            errors.append(f"intent digest mismatch: {name}")

    admission = read_json(VALID / "admission-record.train-ticket.json")
    if not verify_admission_digest(admission):
        errors.append("admission digest mismatch")
    if not verify_admission_signature(admission):
        errors.append("admission signature mismatch")

    bundle = read_json(VALID / "authorized-execution.train-ticket.json")
    if not verify_authorized_parity(bundle):
        errors.append("authorized execution parity/signature mismatch")

    invalid_manifest = read_json(INVALID / "manifest.json")
    for case in invalid_manifest["cases"]:
        doc = read_json(INVALID / f"{case['name']}.json")
        schema_errors = validate_schema_doc(case["schema"], doc)
        parity_invalid = case["schema"] == "authorized-execution" and not verify_authorized_parity(
            doc
        )
        if not schema_errors and not parity_invalid:
            errors.append(f"invalid fixture unexpectedly accepted: {case['name']}")

    jcs_vectors = read_json(VECTORS / "jcs-golden-vectors.json")
    for vector in jcs_vectors["vectors"]:
        if jcs_dumps(vector["value"]) != vector["canonical_json"]:
            errors.append(f"JCS canonical JSON mismatch: {vector['name']}")
        if sha256_prefixed(vector["canonical_json"].encode("utf-8")) != vector["sha256"]:
            errors.append(f"JCS SHA mismatch: {vector['name']}")

    ed = read_json(VECTORS / "ed25519-fixture.json")
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(ed["public_key_hex"]))
    try:
        public_key.verify(
            bytes.fromhex(ed["signature_hex"]), ed["signed_input"]["canonical_json"].encode("utf-8")
        )
    except Exception as exc:
        errors.append(f"Ed25519 fixture verification failed: {exc}")

    manifest = artifact_manifest()
    if write_report:
        write_json(EVIDENCE / "artifact-manifest.json", manifest)
    manifest_bytes = json.dumps(
        _ordered(manifest), separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    manifest_raw_sha = hashlib.sha256(manifest_bytes).hexdigest()
    report = {
        "schema_version": SCHEMA_VERSION,
        "contract_freeze_sha": CONTRACT_FREEZE_SHA,
        "passed": not errors,
        "errors": errors,
        "validated_valid_fixture_count": len(valid_expectations),
        "validated_invalid_fixture_count": len(invalid_manifest["cases"]),
        "artifact_count": manifest["artifact_count"],
        "artifact_manifest_file_sha256": f"sha256:{manifest_raw_sha}",
        "artifact_manifest_canonical_digest": sha256_prefixed(jcs_bytes(manifest)),
        "artifact_manifest_sha256": manifest_raw_sha,
    }
    if write_report:
        write_json(EVIDENCE / "validation-report.json", report)
    if errors:
        raise SystemExit("\n".join(errors))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("materialize")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    if args.command == "materialize":
        materialize()
        verify_all(write_report=True)
    elif args.command == "verify":
        verify_all(write_report=args.write_report)


if __name__ == "__main__":
    main()
