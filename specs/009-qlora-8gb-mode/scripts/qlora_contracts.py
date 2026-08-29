"""Generate and verify canonical feature-009 QLoRA specialization contracts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SCHEMA_VERSION: Final = "1.0.0"

SCHEMAS: Final = {
    "training-mode": ("SCHEMA-TRAINING-MODE-009-V1", "TRAINING_MODE"),
    "base-model-manifest": ("SCHEMA-BASE-MODEL-MANIFEST-009-V1", "BASE_MODEL_MANIFEST"),
    "quantized-base-profile": (
        "SCHEMA-QUANTIZED-BASE-PROFILE-009-V1",
        "QUANTIZED_BASE_PROFILE",
    ),
    "adapter-config": ("SCHEMA-ADAPTER-CONFIG-009-V1", "ADAPTER_CONFIG"),
    "adapter-parameter-schema": (
        "SCHEMA-ADAPTER-PARAMETER-SCHEMA-009-V1",
        "ADAPTER_PARAMETER_SCHEMA",
    ),
    "qlora-ticket-context": ("SCHEMA-QLORA-TICKET-CONTEXT-009-V1", "QLORA_TICKET_CONTEXT"),
    "adapter-contribution-manifest": (
        "SCHEMA-ADAPTER-CONTRIBUTION-MANIFEST-009-V1",
        "ADAPTER_CONTRIBUTION_MANIFEST",
    ),
    "global-adapter-checkpoint": (
        "SCHEMA-GLOBAL-ADAPTER-CHECKPOINT-009-V1",
        "GLOBAL_ADAPTER_CHECKPOINT",
    ),
    "model-composition-manifest": (
        "SCHEMA-MODEL-COMPOSITION-MANIFEST-009-V1",
        "MODEL_COMPOSITION_MANIFEST",
    ),
    "memory-qualification-profile": (
        "SCHEMA-MEMORY-QUALIFICATION-PROFILE-009-V1",
        "MEMORY_QUALIFICATION_PROFILE",
    ),
    "memory-qualification-evidence": (
        "SCHEMA-MEMORY-QUALIFICATION-EVIDENCE-009-V1",
        "MEMORY_QUALIFICATION_EVIDENCE",
    ),
}


class ContractError(RuntimeError):
    """Stable fail-closed feature-009 contract error."""


class SchemaValidationError(ValueError):
    """Deterministic validator error for the frozen JSON-schema subset."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ContractError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def file_json_bytes(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def pretty_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def content_id() -> dict[str, Any]:
    return {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}


def ascii_string(maximum: int = 160) -> dict[str, Any]:
    return {
        "maxLength": maximum,
        "minLength": 1,
        "pattern": "^[A-Za-z0-9._:/+-]+$",
        "type": "string",
    }


def uint(maximum: int = 2**53 - 1, minimum: int = 0) -> dict[str, Any]:
    return {"maximum": maximum, "minimum": minimum, "type": "integer"}


def array(items: dict[str, Any], minimum: int = 1, unique: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"items": items, "minItems": minimum, "type": "array"}
    if unique:
        result["uniqueItems"] = True
    return result


def strict_object(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": sorted(properties),
        "type": "object",
    }


def common_properties(type_name: str) -> dict[str, Any]:
    return {
        "formal_semantics_id": {"const": FORMAL_ID},
        "schema_version": {"const": SCHEMA_VERSION},
        "type_name": {"const": type_name},
    }


def schema_document(name: str, properties: dict[str, Any]) -> dict[str, Any]:
    all_properties = {**common_properties(SCHEMAS[name][1]), **properties}
    return {
        "$id": f"urn:deltareduce:schema:009:{name}:1",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": all_properties,
        "required": sorted(all_properties),
        "title": f"DeltaReduce feature-009 {name} v1",
        "type": "object",
    }


def schema_documents() -> dict[str, dict[str, Any]]:
    parameter = strict_object(
        {
            "alias_owner": ascii_string(),
            "logical_dtype": {"enum": ["FLOAT16", "BFLOAT16", "FLOAT32"]},
            "lora_rank": uint(1024, 1),
            "name": ascii_string(512),
            "shape": array(uint(2**31 - 1, 1)),
            "target_module": ascii_string(512),
        }
    )
    shard = strict_object(
        {
            "encoded_shard_id": content_id(),
            "parameter_name": ascii_string(512),
            "shard_id": ascii_string(),
        }
    )
    return {
        "training-mode": schema_document(
            "training-mode",
            {
                "mode": {"const": "QLORA_ADAPTER"},
                "parallel_certificate_graph": {"const": False},
            },
        ),
        "base-model-manifest": schema_document(
            "base-model-manifest",
            {
                "access_policy": {"const": "PUBLIC_NO_TOKEN"},
                "approved_ephemeral_caches": array(ascii_string(), minimum=0, unique=True),
                "config_hash": content_id(),
                "license": ascii_string(),
                "model_repository": ascii_string(),
                "model_revision": ascii_string(),
                "persistent_base_parameters": array(ascii_string(512), unique=True),
                "persistent_protocol_buffers": array(ascii_string(512), minimum=0, unique=True),
                "redistribution_allowed": {"type": "boolean"},
                "tokenizer_hash": content_id(),
                "weight_shard_ids": array(content_id(), unique=True),
            },
        ),
        "quantized-base-profile": schema_document(
            "quantized-base-profile",
            {
                "backend": {"enum": ["MOCK_INT4", "BITSANDBYTES"]},
                "backend_version": ascii_string(),
                "base_model_manifest_id": content_id(),
                "compute_dtype": {"enum": ["FLOAT16", "BFLOAT16", "FLOAT32"]},
                "double_quantization": {"type": "boolean"},
                "fallback_policy": {"const": "REJECT"},
                "quantization_type": {"enum": ["NF4", "MOCK_SYMMETRIC_INT4"]},
                "storage_bits": {"const": 4},
            },
        ),
        "adapter-config": schema_document(
            "adapter-config",
            {
                "alpha": uint(4096, 1),
                "bias_policy": {"enum": ["NONE"]},
                "dropout_ppm": uint(1_000_000),
                "initialization": ascii_string(),
                "ordered_target_modules": array(ascii_string(512), unique=True),
                "rank": uint(1024, 1),
                "trainable_dtype": {"enum": ["FLOAT16", "BFLOAT16", "FLOAT32"]},
            },
        ),
        "adapter-parameter-schema": schema_document(
            "adapter-parameter-schema",
            {
                "adapter_config_id": content_id(),
                "base_model_manifest_id": content_id(),
                "ordered_parameters": array(parameter),
                "ordered_target_modules": array(ascii_string(512), unique=True),
                "quantized_base_profile_id": content_id(),
                "tokenizer_hash": content_id(),
            },
        ),
        "qlora-ticket-context": schema_document(
            "qlora-ticket-context",
            {
                "B": uint(2**31 - 1, 1),
                "H": uint(2**31 - 1, 1),
                "adapter_parameter_schema_id": content_id(),
                "arithmetic_profile_id": content_id(),
                "base_model_manifest_id": content_id(),
                "data_range_id": content_id(),
                "domain_id": ascii_string(),
                "parent_adapter_id": content_id(),
                "quantized_base_profile_id": content_id(),
                "ticket_id": ascii_string(),
                "training_mode_id": content_id(),
            },
        ),
        "adapter-contribution-manifest": schema_document(
            "adapter-contribution-manifest",
            {
                "actual_optimizer_steps": uint(2**31 - 1, 1),
                "adapter_parameter_schema_id": content_id(),
                "base_model_manifest_id": content_id(),
                "commitment_root": content_id(),
                "memory_qualification_evidence_id": content_id(),
                "ordered_shards": array(shard),
                "parent_adapter_id": content_id(),
                "quantized_base_profile_id": content_id(),
                "ticket_context_id": content_id(),
                "training_mode_id": content_id(),
            },
        ),
        "global-adapter-checkpoint": schema_document(
            "global-adapter-checkpoint",
            {
                "adapter_parameter_schema_id": content_id(),
                "aggregate_root_qc_id": content_id(),
                "apply_qc_id": content_id(),
                "base_model_manifest_id": content_id(),
                "next_adapter_id": content_id(),
                "next_outer_optimizer_state_id": content_id(),
                "parent_adapter_id": content_id(),
                "quantized_base_profile_id": content_id(),
                "training_mode_id": content_id(),
            },
        ),
        "model-composition-manifest": schema_document(
            "model-composition-manifest",
            {
                "apply_qc_id": content_id(),
                "base_model_manifest_id": content_id(),
                "derived_merged_model_id": {
                    "oneOf": [{"type": "null"}, content_id()],
                },
                "global_adapter_checkpoint_id": content_id(),
                "quantized_base_profile_id": content_id(),
                "tokenizer_hash": content_id(),
            },
        ),
        "memory-qualification-profile": schema_document(
            "memory-qualification-profile",
            {
                "gpu_name": ascii_string(),
                "gpu_total_memory_bytes": uint(minimum=1),
                "hard_max_reserved_bytes": uint(minimum=1),
                "host_offload_limit_bytes": {"const": 0},
                "profile_kind": {"enum": ["TINY_OFFLINE", "PHYSICAL_8_GIB"]},
                "required_headroom_bytes": uint(minimum=1),
                "runner_id": ascii_string(),
                "software_profile_id": content_id(),
            },
        ),
        "memory-qualification-evidence": schema_document(
            "memory-qualification-evidence",
            {
                "available_memory_at_start_bytes": uint(minimum=1),
                "base_hash_after": content_id(),
                "base_hash_before": content_id(),
                "claim_eligible": {"type": "boolean"},
                "completed_optimizer_steps": uint(),
                "host_offload_peak_bytes": {"const": 0},
                "memory_qualification_profile_id": content_id(),
                "peak_allocated_bytes": uint(),
                "peak_reserved_bytes": uint(),
                "status": {"enum": ["PASS", "FAIL", "BLOCKED_HARDWARE"]},
            },
        ),
    }


def identified(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    encoded = canonical_json_bytes(value)
    digest = hashlib.sha256(domain.encode() + b"\0" + encoded).hexdigest()
    return {"bytes_hex": encoded.hex(), "content_id": f"sha256:{digest}", "value": value}


def hash_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def base_value() -> dict[str, Any]:
    return {
        "access_policy": "PUBLIC_NO_TOKEN",
        "approved_ephemeral_caches": [],
        "config_hash": hash_id("tiny-config"),
        "formal_semantics_id": FORMAL_ID,
        "license": "CC0-1.0",
        "model_repository": "local/tiny-qlora-fixture",
        "model_revision": "fixture-v1",
        "persistent_base_parameters": [
            "model.embed.weight",
            "model.layer0.weight",
            "model.output.weight",
        ],
        "persistent_protocol_buffers": ["model.layer0.scale"],
        "redistribution_allowed": True,
        "schema_version": SCHEMA_VERSION,
        "tokenizer_hash": hash_id("tiny-tokenizer"),
        "type_name": "BASE_MODEL_MANIFEST",
        "weight_shard_ids": [hash_id("tiny-base-weights")],
    }


def fixture_documents() -> dict[str, Any]:
    artifacts: dict[str, dict[str, Any]] = {}
    artifacts["training_mode"] = identified(
        "deltareduce.009.training-mode.v1",
        {
            "formal_semantics_id": FORMAL_ID,
            "mode": "QLORA_ADAPTER",
            "parallel_certificate_graph": False,
            "schema_version": SCHEMA_VERSION,
            "type_name": "TRAINING_MODE",
        },
    )
    artifacts["base_model_manifest"] = identified(
        "deltareduce.009.base-model-manifest.v1", base_value()
    )
    base_id = artifacts["base_model_manifest"]["content_id"]
    tokenizer_hash = artifacts["base_model_manifest"]["value"]["tokenizer_hash"]
    artifacts["quantized_base_profile"] = identified(
        "deltareduce.009.quantized-base-profile.v1",
        {
            "backend": "MOCK_INT4",
            "backend_version": "fixture-1",
            "base_model_manifest_id": base_id,
            "compute_dtype": "FLOAT32",
            "double_quantization": False,
            "fallback_policy": "REJECT",
            "formal_semantics_id": FORMAL_ID,
            "quantization_type": "MOCK_SYMMETRIC_INT4",
            "schema_version": SCHEMA_VERSION,
            "storage_bits": 4,
            "type_name": "QUANTIZED_BASE_PROFILE",
        },
    )
    target_modules = ["model.layer0"]
    artifacts["adapter_config"] = identified(
        "deltareduce.009.adapter-config.v1",
        {
            "alpha": 4,
            "bias_policy": "NONE",
            "dropout_ppm": 0,
            "formal_semantics_id": FORMAL_ID,
            "initialization": "ZEROS",
            "ordered_target_modules": target_modules,
            "rank": 2,
            "schema_version": SCHEMA_VERSION,
            "trainable_dtype": "FLOAT32",
            "type_name": "ADAPTER_CONFIG",
        },
    )
    parameters = [
        {
            "alias_owner": "model.layer0.lora_A",
            "logical_dtype": "FLOAT32",
            "lora_rank": 2,
            "name": "model.layer0.lora_A",
            "shape": [2, 2],
            "target_module": "model.layer0",
        },
        {
            "alias_owner": "model.layer0.lora_B",
            "logical_dtype": "FLOAT32",
            "lora_rank": 2,
            "name": "model.layer0.lora_B",
            "shape": [2, 2],
            "target_module": "model.layer0",
        },
    ]
    artifacts["adapter_parameter_schema"] = identified(
        "deltareduce.009.adapter-parameter-schema.v1",
        {
            "adapter_config_id": artifacts["adapter_config"]["content_id"],
            "base_model_manifest_id": base_id,
            "formal_semantics_id": FORMAL_ID,
            "ordered_parameters": parameters,
            "ordered_target_modules": target_modules,
            "quantized_base_profile_id": artifacts["quantized_base_profile"]["content_id"],
            "schema_version": SCHEMA_VERSION,
            "tokenizer_hash": tokenizer_hash,
            "type_name": "ADAPTER_PARAMETER_SCHEMA",
        },
    )
    artifacts["memory_qualification_profile"] = identified(
        "deltareduce.009.memory-qualification-profile.v1",
        {
            "formal_semantics_id": FORMAL_ID,
            "gpu_name": "CPU-MOCK",
            "gpu_total_memory_bytes": 1024**3,
            "hard_max_reserved_bytes": 512 * 1024**2,
            "host_offload_limit_bytes": 0,
            "profile_kind": "TINY_OFFLINE",
            "required_headroom_bytes": 128 * 1024**2,
            "runner_id": "tiny-offline-runner",
            "schema_version": SCHEMA_VERSION,
            "software_profile_id": hash_id("tiny-software"),
            "type_name": "MEMORY_QUALIFICATION_PROFILE",
        },
    )
    artifacts["memory_qualification_evidence"] = identified(
        "deltareduce.009.memory-qualification-evidence.v1",
        {
            "available_memory_at_start_bytes": 768 * 1024**2,
            "base_hash_after": hash_id("tiny-persistent-base"),
            "base_hash_before": hash_id("tiny-persistent-base"),
            "claim_eligible": False,
            "completed_optimizer_steps": 2,
            "formal_semantics_id": FORMAL_ID,
            "host_offload_peak_bytes": 0,
            "memory_qualification_profile_id": artifacts["memory_qualification_profile"][
                "content_id"
            ],
            "peak_allocated_bytes": 64 * 1024**2,
            "peak_reserved_bytes": 96 * 1024**2,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "type_name": "MEMORY_QUALIFICATION_EVIDENCE",
        },
    )
    artifacts["qlora_ticket_context"] = identified(
        "deltareduce.009.qlora-ticket-context.v1",
        {
            "B": 8,
            "H": 2,
            "adapter_parameter_schema_id": artifacts["adapter_parameter_schema"]["content_id"],
            "arithmetic_profile_id": hash_id("int16-fixed-v1"),
            "base_model_manifest_id": base_id,
            "data_range_id": hash_id("tiny-data-range"),
            "domain_id": "tiny-text",
            "formal_semantics_id": FORMAL_ID,
            "parent_adapter_id": hash_id("tiny-parent-adapter"),
            "quantized_base_profile_id": artifacts["quantized_base_profile"]["content_id"],
            "schema_version": SCHEMA_VERSION,
            "ticket_id": "tiny-ticket-009",
            "training_mode_id": artifacts["training_mode"]["content_id"],
            "type_name": "QLORA_TICKET_CONTEXT",
        },
    )
    shards = [
        {
            "encoded_shard_id": hash_id(f"q:{parameter['name']}"),
            "parameter_name": parameter["name"],
            "shard_id": f"adapter-{index:03d}",
        }
        for index, parameter in enumerate(parameters)
    ]
    artifacts["adapter_contribution_manifest"] = identified(
        "deltareduce.009.adapter-contribution-manifest.v1",
        {
            "actual_optimizer_steps": 2,
            "adapter_parameter_schema_id": artifacts["adapter_parameter_schema"]["content_id"],
            "base_model_manifest_id": base_id,
            "commitment_root": hash_id("tiny-adapter-commitment"),
            "formal_semantics_id": FORMAL_ID,
            "memory_qualification_evidence_id": artifacts["memory_qualification_evidence"][
                "content_id"
            ],
            "ordered_shards": shards,
            "parent_adapter_id": hash_id("tiny-parent-adapter"),
            "quantized_base_profile_id": artifacts["quantized_base_profile"]["content_id"],
            "schema_version": SCHEMA_VERSION,
            "ticket_context_id": artifacts["qlora_ticket_context"]["content_id"],
            "training_mode_id": artifacts["training_mode"]["content_id"],
            "type_name": "ADAPTER_CONTRIBUTION_MANIFEST",
        },
    )
    artifacts["global_adapter_checkpoint"] = identified(
        "deltareduce.009.global-adapter-checkpoint.v1",
        {
            "adapter_parameter_schema_id": artifacts["adapter_parameter_schema"]["content_id"],
            "aggregate_root_qc_id": hash_id("feature008-aggregate-root-qc"),
            "apply_qc_id": hash_id("feature008-apply-qc"),
            "base_model_manifest_id": base_id,
            "formal_semantics_id": FORMAL_ID,
            "next_adapter_id": hash_id("tiny-next-adapter"),
            "next_outer_optimizer_state_id": hash_id("tiny-next-outer-state"),
            "parent_adapter_id": hash_id("tiny-parent-adapter"),
            "quantized_base_profile_id": artifacts["quantized_base_profile"]["content_id"],
            "schema_version": SCHEMA_VERSION,
            "training_mode_id": artifacts["training_mode"]["content_id"],
            "type_name": "GLOBAL_ADAPTER_CHECKPOINT",
        },
    )
    artifacts["model_composition_manifest"] = identified(
        "deltareduce.009.model-composition-manifest.v1",
        {
            "apply_qc_id": hash_id("feature008-apply-qc"),
            "base_model_manifest_id": base_id,
            "derived_merged_model_id": None,
            "formal_semantics_id": FORMAL_ID,
            "global_adapter_checkpoint_id": artifacts["global_adapter_checkpoint"]["content_id"],
            "quantized_base_profile_id": artifacts["quantized_base_profile"]["content_id"],
            "schema_version": SCHEMA_VERSION,
            "tokenizer_hash": tokenizer_hash,
            "type_name": "MODEL_COMPOSITION_MANIFEST",
        },
    )
    valid = {
        "artifacts": artifacts,
        "formal_semantics_id": FORMAL_ID,
        "ordered_artifact_names": list(artifacts),
        "schema_version": SCHEMA_VERSION,
        "semantic_completeness_claimed": False,
    }
    negative_cases = []
    for name, artifact_name, expected_reason, mutate in negative_specs():
        candidate = copy.deepcopy(artifacts[artifact_name]["value"])
        mutate(candidate)
        negative_cases.append(
            {
                "artifact_name": artifact_name,
                "expected_reason": expected_reason,
                "name": name,
                "value": candidate,
            }
        )
    invalid = {
        "cases": negative_cases,
        "formal_semantics_id": FORMAL_ID,
        "schema_version": SCHEMA_VERSION,
        "semantic_completeness_claimed": False,
    }
    tiny = {
        "initial_adapter_values": {
            "model.layer0.lora_A": [0, 0, 0, 0],
            "model.layer0.lora_B": [0, 0, 0, 0],
        },
        "model_inputs": [[1, 2], [2, 1], [1, 1], [2, 2]],
        "targets": [[0, 1], [1, 0], [1, 1], [0, 0]],
        "tokenizer": {"1": "alpha", "2": "beta"},
        "valid_contract_id": hash_id("feature009-valid-contract"),
    }
    return {"invalid": invalid, "tiny": tiny, "valid": valid}


def negative_specs() -> list[tuple[str, str, str, Any]]:
    return [
        (
            "wrong-base",
            "qlora_ticket_context",
            "BASE_CONTEXT_MISMATCH",
            lambda value: value.__setitem__("base_model_manifest_id", hash_id("wrong-base")),
        ),
        (
            "partial-ticket",
            "adapter_contribution_manifest",
            "PARTIAL_TICKET",
            lambda value: value.__setitem__("actual_optimizer_steps", 1),
        ),
        (
            "wrong-schema",
            "adapter_contribution_manifest",
            "ADAPTER_SCHEMA_MISMATCH",
            lambda value: value.__setitem__("adapter_parameter_schema_id", hash_id("wrong-schema")),
        ),
        (
            "base-injection",
            "adapter_contribution_manifest",
            "BASE_PARAMETER_INJECTION",
            lambda value: value["ordered_shards"].append(
                {
                    "encoded_shard_id": hash_id("base-injection"),
                    "parameter_name": "model.embed.weight",
                    "shard_id": "forbidden-base",
                }
            ),
        ),
        (
            "parallel-certificate-graph",
            "training_mode",
            "PARALLEL_CERTIFICATE_GRAPH",
            lambda value: value.__setitem__("parallel_certificate_graph", True),
        ),
        (
            "mock-physical-claim",
            "memory_qualification_evidence",
            "MOCK_HARDWARE_CLAIM",
            lambda value: value.__setitem__("claim_eligible", True),
        ),
        (
            "base-mutated",
            "memory_qualification_evidence",
            "BASE_MUTATION",
            lambda value: value.__setitem__("base_hash_after", hash_id("mutated-base")),
        ),
    ]


def schema_for_artifact(name: str) -> str:
    return name.replace("_", "-")


def validate_schema(schema: dict[str, Any], value: object, path: str = "$") -> None:
    if "oneOf" in schema:
        successes = 0
        for candidate in schema["oneOf"]:
            try:
                validate_schema(candidate, value, path)
                successes += 1
            except SchemaValidationError:
                pass
        if successes != 1:
            raise SchemaValidationError(f"{path}:ONE_OF")
        return
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            raise SchemaValidationError(f"{path}:TYPE_OBJECT")
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise SchemaValidationError(f"{path}:MISSING:{','.join(missing)}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise SchemaValidationError(f"{path}:EXTRA:{','.join(extra)}")
        for key, item in value.items():
            if key in properties:
                validate_schema(properties[key], item, f"{path}.{key}")
    elif expected_type == "array":
        if not isinstance(value, list):
            raise SchemaValidationError(f"{path}:TYPE_ARRAY")
        if len(value) < schema.get("minItems", 0):
            raise SchemaValidationError(f"{path}:MIN_ITEMS")
        if schema.get("uniqueItems") and len({canonical_json_bytes(item) for item in value}) != len(
            value
        ):
            raise SchemaValidationError(f"{path}:UNIQUE_ITEMS")
        for index, item in enumerate(value):
            validate_schema(schema["items"], item, f"{path}[{index}]")
    elif expected_type == "string":
        if not isinstance(value, str):
            raise SchemaValidationError(f"{path}:TYPE_STRING")
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 2**31):
            raise SchemaValidationError(f"{path}:STRING_LENGTH")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise SchemaValidationError(f"{path}:PATTERN")
    elif expected_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise SchemaValidationError(f"{path}:TYPE_INTEGER")
        if value < schema.get("minimum", -(2**63)) or value > schema.get("maximum", 2**63):
            raise SchemaValidationError(f"{path}:INTEGER_BOUND")
    elif expected_type == "boolean" and not isinstance(value, bool):
        raise SchemaValidationError(f"{path}:TYPE_BOOLEAN")
    elif expected_type == "null" and value is not None:
        raise SchemaValidationError(f"{path}:TYPE_NULL")
    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}:CONST")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}:ENUM")


def validate_identified(name: str, wrapper: dict[str, Any], schemas: dict[str, Any]) -> None:
    value = wrapper.get("value")
    require(isinstance(value, dict), "ARTIFACT_VALUE_INVALID", name)
    validate_schema(schemas[schema_for_artifact(name)], value)
    encoded = canonical_json_bytes(value)
    require(wrapper.get("bytes_hex") == encoded.hex(), "CANONICAL_BYTES_DRIFT", name)
    domain = f"deltareduce.009.{schema_for_artifact(name)}.v1"
    expected = "sha256:" + hashlib.sha256(domain.encode() + b"\0" + encoded).hexdigest()
    require(wrapper.get("content_id") == expected, "CONTENT_ID_DRIFT", name)


def validate_chain(artifacts: dict[str, Any]) -> dict[str, Any]:
    mode = artifacts["training_mode"]
    base = artifacts["base_model_manifest"]
    quantized = artifacts["quantized_base_profile"]
    config = artifacts["adapter_config"]
    schema = artifacts["adapter_parameter_schema"]
    ticket = artifacts["qlora_ticket_context"]
    contribution = artifacts["adapter_contribution_manifest"]
    memory_profile = artifacts["memory_qualification_profile"]
    memory = artifacts["memory_qualification_evidence"]
    checkpoint = artifacts["global_adapter_checkpoint"]
    composition = artifacts["model_composition_manifest"]

    require(mode["value"]["parallel_certificate_graph"] is False, "PARALLEL_CERTIFICATE_GRAPH")
    base_id = base["content_id"]
    require(quantized["value"]["base_model_manifest_id"] == base_id, "BASE_CONTEXT_MISMATCH")
    require(schema["value"]["base_model_manifest_id"] == base_id, "BASE_CONTEXT_MISMATCH")
    require(ticket["value"]["base_model_manifest_id"] == base_id, "BASE_CONTEXT_MISMATCH")
    require(contribution["value"]["base_model_manifest_id"] == base_id, "BASE_CONTEXT_MISMATCH")
    require(checkpoint["value"]["base_model_manifest_id"] == base_id, "BASE_CONTEXT_MISMATCH")
    require(composition["value"]["base_model_manifest_id"] == base_id, "BASE_CONTEXT_MISMATCH")
    require(
        schema["value"]["adapter_config_id"] == config["content_id"],
        "ADAPTER_CONFIG_MISMATCH",
    )
    schema_id = schema["content_id"]
    require(
        contribution["value"]["adapter_parameter_schema_id"] == schema_id,
        "ADAPTER_SCHEMA_MISMATCH",
    )
    require(ticket["value"]["adapter_parameter_schema_id"] == schema_id, "ADAPTER_SCHEMA_MISMATCH")
    require(
        contribution["value"]["actual_optimizer_steps"] == ticket["value"]["H"],
        "PARTIAL_TICKET",
    )
    expected_parameters = [entry["name"] for entry in schema["value"]["ordered_parameters"]]
    actual_parameters = [
        entry["parameter_name"] for entry in contribution["value"]["ordered_shards"]
    ]
    base_parameters = set(base["value"]["persistent_base_parameters"])
    require(not base_parameters.intersection(actual_parameters), "BASE_PARAMETER_INJECTION")
    require(actual_parameters == expected_parameters, "ADAPTER_COVERAGE_MISMATCH")
    require(
        memory["value"]["base_hash_before"] == memory["value"]["base_hash_after"],
        "BASE_MUTATION",
    )
    if memory["value"]["claim_eligible"]:
        require(
            memory_profile["value"]["profile_kind"] == "PHYSICAL_8_GIB",
            "MOCK_HARDWARE_CLAIM",
        )
        require(memory["value"]["status"] == "PASS", "HARDWARE_CLAIM_NOT_PASS")
    require(
        composition["value"]["derived_merged_model_id"] is None, "AUTHORITATIVE_MERGE_FORBIDDEN"
    )
    return {
        "adapter_parameter_count": len(expected_parameters),
        "artifact_count": len(artifacts),
        "status": "PASS",
    }


def validate_negative(
    case: dict[str, Any],
    artifacts: dict[str, Any],
    schemas: dict[str, Any],
) -> None:
    candidate = copy.deepcopy(artifacts)
    name = case["artifact_name"]
    candidate[name] = identified(f"deltareduce.009.{schema_for_artifact(name)}.v1", case["value"])
    expected = case["expected_reason"]
    try:
        validate_chain(candidate)
        validate_identified(name, candidate[name], schemas)
    except (ContractError, SchemaValidationError) as error:
        require(expected in str(error), "NEGATIVE_REASON_DRIFT", case["name"])
        return
    raise ContractError(f"NEGATIVE_ACCEPTED:{case['name']}")


def schema_registry(schemas: dict[str, dict[str, Any]], fixtures: dict[str, Any]) -> dict[str, Any]:
    artifacts = []
    media_types = []
    for name, (schema_id, _) in SCHEMAS.items():
        path = f"schemas/009/{name}-v1.json"
        artifacts.append(
            {
                "id": schema_id,
                "path": path,
                "sha256": sha256_bytes(pretty_json_bytes(schemas[name])),
            }
        )
        media_types.append(
            {
                "id": f"MEDIA-{name.upper().replace('-', '-')}-009-V1",
                "schema_id": schema_id,
                "value": f"application/vnd.deltareduce.{name}+json;version=1",
            }
        )
    fixture_entries = [
        {
            "id": "QLORA009-VALID-CONTRACT-V1",
            "path": "fixtures/009/valid/qlora-contract-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["valid"])),
        },
        {
            "id": "QLORA009-CROSS-LANGUAGE-GOLDEN-V1",
            "path": "fixtures/009/cross-language/golden-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["valid"])),
        },
        {
            "id": "QLORA009-NEGATIVE-V1",
            "path": "fixtures/009/invalid/qlora-negative-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["invalid"])),
        },
        {
            "id": "QLORA009-TINY-OFFLINE-V1",
            "path": "fixtures/009/tiny-offline/tiny-qlora-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["tiny"])),
        },
    ]
    return {
        "artifacts": artifacts,
        "fixtures": fixture_entries,
        "formal_semantics_id": FORMAL_ID,
        "media_types": media_types,
        "registry_version": "009.1.0",
        "schema_version": SCHEMA_VERSION,
        "semantic_completeness_claimed": False,
    }


def root_registry_bytes(registry: dict[str, Any]) -> bytes:
    path = ROOT / "delta-protocol" / "registry.json"
    root = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(root, dict), "ROOT_REGISTRY_INVALID")
    for key, prefix in (
        ("extensions", "REGISTRY-QLORA-009"),
        ("fixtures", "QLORA009-"),
        ("media_types", "MEDIA-"),
        ("schemas", "SCHEMA-"),
    ):
        values = root.get(key)
        require(isinstance(values, list), "ROOT_REGISTRY_SECTION_INVALID", key)
        if key == "extensions":
            root[key] = [entry for entry in values if entry.get("id") != prefix]
        elif key == "fixtures":
            root[key] = [
                entry for entry in values if not str(entry.get("id", "")).startswith(prefix)
            ]
        elif key == "media_types":
            schema_ids = {entry["id"] for entry in registry["artifacts"]}
            root[key] = [entry for entry in values if entry.get("schema_id") not in schema_ids]
        else:
            ids = {entry["id"] for entry in registry["artifacts"]}
            root[key] = [entry for entry in values if entry.get("id") not in ids]
    feature_registry = pretty_json_bytes(registry)
    root["extensions"].append(
        {
            "id": "REGISTRY-QLORA-009",
            "path": "schemas/009/registry-v1.json",
            "sha256": sha256_bytes(feature_registry),
        }
    )
    root["fixtures"].extend(registry["fixtures"])
    root["media_types"].extend(registry["media_types"])
    root["schemas"].extend(registry["artifacts"])
    root["extensions"] = sorted(root["extensions"], key=lambda entry: entry["path"])
    root["fixtures"] = sorted(root["fixtures"], key=lambda entry: entry["path"])
    root["media_types"] = sorted(root["media_types"], key=lambda entry: entry["id"])
    root["schemas"] = sorted(root["schemas"], key=lambda entry: entry["path"])
    return pretty_json_bytes(root)


def expected_outputs() -> dict[Path, bytes]:
    schemas = schema_documents()
    fixtures = fixture_documents()
    for name, wrapper in fixtures["valid"]["artifacts"].items():
        validate_identified(name, wrapper, schemas)
    chain = validate_chain(fixtures["valid"]["artifacts"])
    require(chain["artifact_count"] == len(SCHEMAS), "VALID_ARTIFACT_COUNT_DRIFT")
    for case in fixtures["invalid"]["cases"]:
        validate_negative(case, fixtures["valid"]["artifacts"], schemas)
    registry = schema_registry(schemas, fixtures)
    outputs = {
        ROOT / "delta-protocol" / "schemas" / "009" / f"{name}-v1.json": pretty_json_bytes(schema)
        for name, schema in schemas.items()
    }
    outputs[ROOT / "delta-protocol" / "schemas" / "009" / "registry-v1.json"] = pretty_json_bytes(
        registry
    )
    outputs[ROOT / "delta-protocol" / "fixtures" / "009" / "valid" / "qlora-contract-v1.json"] = (
        file_json_bytes(fixtures["valid"])
    )
    outputs[ROOT / "delta-protocol" / "fixtures" / "009" / "cross-language" / "golden-v1.json"] = (
        file_json_bytes(fixtures["valid"])
    )
    outputs[ROOT / "delta-protocol" / "fixtures" / "009" / "invalid" / "qlora-negative-v1.json"] = (
        file_json_bytes(fixtures["invalid"])
    )
    outputs[
        ROOT / "delta-protocol" / "fixtures" / "009" / "tiny-offline" / "tiny-qlora-v1.json"
    ] = file_json_bytes(fixtures["tiny"])
    outputs[ROOT / "delta-protocol" / "registry.json"] = root_registry_bytes(registry)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        outputs = expected_outputs()
        if arguments.write:
            for path, value in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)
        else:
            for path, value in outputs.items():
                require(path.is_file(), "OUTPUT_MISSING", path.relative_to(ROOT).as_posix())
                require(
                    path.read_bytes() == value, "OUTPUT_STALE", path.relative_to(ROOT).as_posix()
                )
        print(
            canonical_json_bytes(
                {
                    "formal_semantics_id": FORMAL_ID,
                    "invalid_case_count": len(negative_specs()),
                    "output_count": len(outputs),
                    "schema_count": len(SCHEMAS),
                    "semantic_completeness_claimed": False,
                    "status": "PASS",
                }
            ).decode()
        )
    except (
        ContractError,
        SchemaValidationError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        print(
            canonical_json_bytes(
                {
                    "error_code": str(error),
                    "formal_semantics_id": FORMAL_ID,
                    "status": "FAIL",
                }
            ).decode()
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
