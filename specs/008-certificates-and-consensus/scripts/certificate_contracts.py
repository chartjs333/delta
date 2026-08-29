"""Generate and verify canonical feature-008 certificate/apply contracts and fixtures."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SCHEMA_VERSION: Final = "1.0.0"
ROUND_CONFIG_ID: Final = "sha256:" + "a" * 64
PARENT_CHECKPOINT_ID: Final = "sha256:" + "b" * 64
PARAMETER_SCHEMA_ID: Final = "sha256:" + "c" * 64
ARITHMETIC_PROFILE_ID: Final = "sha256:" + "d" * 64
VALIDATOR_EPOCH_ID: Final = "sha256:" + "e" * 64
ROBUST_PROFILE_ID: Final = "sha256:" + "1" * 64
ACCUMULATOR_PROOF_ID: Final = "sha256:" + "2" * 64
SEED_PROFILE_ID: Final = "sha256:" + "3" * 64

SCHEMAS: Final = {
    "input-set-certificate": (
        "SCHEMA-INPUT-SET-CERTIFICATE-V1",
        "INPUT_SET_CERTIFICATE",
        "application/vnd.deltareduce.input-set-certificate+json;version=1",
    ),
    "seed-transcript": (
        "SCHEMA-SEED-TRANSCRIPT-V1",
        "SEED_TRANSCRIPT",
        "application/vnd.deltareduce.seed-transcript+json;version=1",
    ),
    "norm-evidence": (
        "SCHEMA-NORM-EVIDENCE-V1",
        "NORM_EVIDENCE",
        "application/vnd.deltareduce.norm-evidence+json;version=1",
    ),
    "eligibility-certificate": (
        "SCHEMA-ELIGIBILITY-CERTIFICATE-V1",
        "ELIGIBILITY_CERTIFICATE",
        "application/vnd.deltareduce.eligibility-certificate+json;version=1",
    ),
    "aggregation-plan-certificate": (
        "SCHEMA-AGGREGATION-PLAN-CERTIFICATE-V1",
        "AGGREGATION_PLAN_CERTIFICATE",
        "application/vnd.deltareduce.aggregation-plan-certificate+json;version=1",
    ),
    "parameter-shard-qc": (
        "SCHEMA-PARAMETER-SHARD-QC-V1",
        "PARAMETER_SHARD_QC",
        "application/vnd.deltareduce.parameter-shard-qc+json;version=1",
    ),
    "aggregate-root-qc": (
        "SCHEMA-AGGREGATE-ROOT-QC-V1",
        "AGGREGATE_ROOT_QC",
        "application/vnd.deltareduce.aggregate-root-qc+json;version=1",
    ),
    "apply-arithmetic-profile": (
        "SCHEMA-APPLY-ARITHMETIC-PROFILE-V1",
        "APPLY_ARITHMETIC_PROFILE",
        "application/vnd.deltareduce.apply-arithmetic-profile+json;version=1",
    ),
    "apply-candidate": (
        "SCHEMA-APPLY-CANDIDATE-V1",
        "APPLY_CANDIDATE",
        "application/vnd.deltareduce.apply-candidate+json;version=1",
    ),
    "apply-qc": (
        "SCHEMA-APPLY-QC-V1",
        "APPLY_QC",
        "application/vnd.deltareduce.apply-qc+json;version=1",
    ),
    "current-pointer-command": (
        "SCHEMA-CURRENT-POINTER-COMMAND-V1",
        "CURRENT_POINTER_COMMAND",
        "application/vnd.deltareduce.current-pointer-command+json;version=1",
    ),
}


class ContractError(RuntimeError):
    """Stable fail-closed feature-008 contract error."""


class SchemaValidationError(ValueError):
    """Small deterministic validator error for the frozen schema subset."""


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


def identified(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    encoded = canonical_json_bytes(value)
    digest = hashlib.sha256(domain.encode() + b"\0" + encoded).hexdigest()
    return {"bytes_hex": encoded.hex(), "content_id": f"sha256:{digest}", "value": value}


def aggregate_merkle_root(leaves: list[dict[str, str]]) -> str:
    level = [
        hashlib.sha256(b"deltareduce.008.aggregate-leaf.v1\0" + canonical_json_bytes(leaf)).digest()
        for leaf in leaves
    ]
    require(bool(level), "AGGREGATE_MERKLE_EMPTY")
    while len(level) > 1:
        parents = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                parents.append(level[index])
            else:
                parents.append(
                    hashlib.sha256(
                        b"deltareduce.008.aggregate-node.v1\0" + level[index] + level[index + 1]
                    ).digest()
                )
        level = parents
    return "sha256:" + level[0].hex()


def content_id() -> dict[str, Any]:
    return {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}


def ascii_string() -> dict[str, Any]:
    return {"maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9._:-]+$", "type": "string"}


def decimal_string() -> dict[str, Any]:
    return {"pattern": "^-?(0|[1-9][0-9]*)$", "type": "string"}


def uint(maximum: int = 2**53 - 1, minimum: int = 0) -> dict[str, Any]:
    return {"maximum": maximum, "minimum": minimum, "type": "integer"}


def strict_object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": required if required is not None else sorted(properties),
        "type": "object",
    }


def array(items: dict[str, Any], minimum: int = 1, unique: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"items": items, "minItems": minimum, "type": "array"}
    if unique:
        result["uniqueItems"] = True
    return result


def context_properties() -> dict[str, Any]:
    return {
        "arithmetic_profile_id": content_id(),
        "height": uint(minimum=1),
        "parameter_schema_id": content_id(),
        "round_config_id": content_id(),
        "round_id": ascii_string(),
        "validator_epoch_id": content_id(),
        "view": uint(),
    }


def common_properties(type_name: str) -> dict[str, Any]:
    return {
        "formal_semantics_id": {"const": FORMAL_ID},
        "schema_version": {"const": SCHEMA_VERSION},
        "type_name": {"const": type_name},
    }


def schema_document(
    name: str, properties: dict[str, Any], *, context: bool = True
) -> dict[str, Any]:
    _, type_name, _ = SCHEMAS[name]
    all_properties = {**common_properties(type_name)}
    if context:
        all_properties.update(context_properties())
    all_properties.update(properties)
    return {
        "$id": f"urn:deltareduce:schema:{name}:1",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": all_properties,
        "required": sorted(all_properties),
        "title": f"DeltaReduce {name} v1",
        "type": "object",
    }


def schema_documents() -> dict[str, dict[str, Any]]:
    rational = strict_object({"denominator": uint(minimum=1), "numerator": decimal_string()})
    input_tuple = strict_object(
        {
            "availability_certificate_id": content_id(),
            "commitment_id": content_id(),
            "domain_id": ascii_string(),
            "ticket_id": ascii_string(),
        }
    )
    norm_entry = strict_object(
        {
            "scale_denominator": uint(minimum=1),
            "squared_norm": decimal_string(),
            "ticket_id": ascii_string(),
        }
    )
    eligibility_entry = strict_object(
        {
            "accepted": {"type": "boolean"},
            "domain_id": ascii_string(),
            "gamma": rational,
            "reason_code": ascii_string(),
            "ticket_id": ascii_string(),
        }
    )
    bucket = strict_object({"bucket_id": ascii_string(), "ticket_id": ascii_string()})
    weight = strict_object({"alpha": rational, "ticket_id": ascii_string()})
    shard_key = strict_object({"domain_id": ascii_string(), "shard_id": ascii_string()})
    root_leaf = strict_object(
        {
            "domain_id": ascii_string(),
            "parameter_shard_qc_id": content_id(),
            "shard_id": ascii_string(),
        }
    )
    domain_weight = strict_object({"domain_id": ascii_string(), "pi": rational})
    return {
        "input-set-certificate": schema_document(
            "input-set-certificate",
            {
                "input_root": content_id(),
                "quorum_threshold": uint(1024, 1),
                "signer_ids": array(ascii_string(), unique=True),
                "tuples": array(input_tuple),
            },
        ),
        "seed-transcript": schema_document(
            "seed-transcript",
            {
                "input_set_certificate_id": content_id(),
                "seed_id": content_id(),
                "seed_profile_id": content_id(),
                "share_ids": array(content_id(), unique=True),
            },
        ),
        "norm-evidence": schema_document(
            "norm-evidence",
            {
                "entries": array(norm_entry),
                "input_set_certificate_id": content_id(),
                "norm_root": content_id(),
            },
        ),
        "eligibility-certificate": schema_document(
            "eligibility-certificate",
            {
                "entries": array(eligibility_entry),
                "input_set_certificate_id": content_id(),
                "norm_evidence_id": content_id(),
                "quorum_threshold": uint(1024, 1),
                "robust_profile_id": content_id(),
                "signer_ids": array(ascii_string(), unique=True),
            },
        ),
        "aggregation-plan-certificate": schema_document(
            "aggregation-plan-certificate",
            {
                "accumulator_proof_id": content_id(),
                "bucket_assignments": array(bucket),
                "eligibility_certificate_id": content_id(),
                "input_set_certificate_id": content_id(),
                "iteration_count": uint(1024, 1),
                "quorum_threshold": uint(1024, 1),
                "seed_transcript_id": content_id(),
                "signer_ids": array(ascii_string(), unique=True),
                "transcript_root": content_id(),
                "weights": array(weight),
            },
        ),
        "parameter-shard-qc": schema_document(
            "parameter-shard-qc",
            {
                "aggregation_plan_certificate_id": content_id(),
                "denominator": uint(minimum=1),
                "domain_id": ascii_string(),
                "eligibility_certificate_id": content_id(),
                "input_leaf_ids": array(content_id(), unique=True),
                "input_set_certificate_id": content_id(),
                "quorum_threshold": uint(1024, 1),
                "result_numerators": array(decimal_string()),
                "shard_id": ascii_string(),
                "signer_ids": array(ascii_string(), unique=True),
            },
        ),
        "aggregate-root-qc": schema_document(
            "aggregate-root-qc",
            {
                "aggregation_plan_certificate_id": content_id(),
                "eligibility_certificate_id": content_id(),
                "input_set_certificate_id": content_id(),
                "leaves": array(root_leaf),
                "merkle_root": content_id(),
                "quorum_threshold": uint(1024, 1),
                "required_keys": array(shard_key),
                "signer_ids": array(ascii_string(), unique=True),
            },
        ),
        "apply-arithmetic-profile": schema_document(
            "apply-arithmetic-profile",
            {
                "accumulator_proof_id": content_id(),
                "domain_weights": array(domain_weight),
                "learning_rate": rational,
                "momentum": rational,
                "nesterov": {"const": True},
                "rounding": {"const": "HALF_TOWARD_POSITIVE"},
                "weight_decay": rational,
            },
            context=False,
        ),
        "apply-candidate": schema_document(
            "apply-candidate",
            {
                "aggregate_root_qc_id": content_id(),
                "apply_arithmetic_profile_id": content_id(),
                "next_model_hash": content_id(),
                "next_model_values": array(decimal_string()),
                "next_optimizer_hash": content_id(),
                "next_optimizer_values": array(decimal_string()),
                "parent_checkpoint_id": content_id(),
                "parent_optimizer_hash": content_id(),
            },
        ),
        "apply-qc": schema_document(
            "apply-qc",
            {
                "aggregate_root_qc_id": content_id(),
                "apply_arithmetic_profile_id": content_id(),
                "apply_candidate_id": content_id(),
                "next_model_hash": content_id(),
                "next_optimizer_hash": content_id(),
                "parent_checkpoint_id": content_id(),
                "quorum_threshold": uint(1024, 1),
                "signer_ids": array(ascii_string(), unique=True),
            },
        ),
        "current-pointer-command": schema_document(
            "current-pointer-command",
            {
                "apply_qc_id": content_id(),
                "expected_parent_checkpoint_id": content_id(),
                "next_checkpoint_id": content_id(),
                "next_optimizer_hash": content_id(),
            },
        ),
    }


def validate_schema(value: object, schema: dict[str, Any], path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}:CONST")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}:ENUM")
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise SchemaValidationError(f"{path}:OBJECT")
        missing = [key for key in schema.get("required", []) if key not in value]
        if missing:
            raise SchemaValidationError(f"{path}:REQUIRED:{','.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise SchemaValidationError(f"{path}:ADDITIONAL:{','.join(extra)}")
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], f"{path}.{key}")
    elif expected == "array":
        if not isinstance(value, list):
            raise SchemaValidationError(f"{path}:ARRAY")
        if len(value) < int(schema.get("minItems", 0)):
            raise SchemaValidationError(f"{path}:MIN_ITEMS")
        if schema.get("uniqueItems") and len({canonical_json_bytes(item) for item in value}) != len(
            value
        ):
            raise SchemaValidationError(f"{path}:UNIQUE_ITEMS")
        for index, item in enumerate(value):
            validate_schema(item, schema.get("items", {}), f"{path}[{index}]")
    elif expected == "string":
        if not isinstance(value, str):
            raise SchemaValidationError(f"{path}:STRING")
        if len(value) < int(schema.get("minLength", 0)):
            raise SchemaValidationError(f"{path}:MIN_LENGTH")
        if len(value) > int(schema.get("maxLength", len(value))):
            raise SchemaValidationError(f"{path}:MAX_LENGTH")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, value) is None:
            raise SchemaValidationError(f"{path}:PATTERN")
    elif expected == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise SchemaValidationError(f"{path}:INTEGER")
        if value < int(schema.get("minimum", value)):
            raise SchemaValidationError(f"{path}:MINIMUM")
        if value > int(schema.get("maximum", value)):
            raise SchemaValidationError(f"{path}:MAXIMUM")
    elif expected == "boolean" and not isinstance(value, bool):
        raise SchemaValidationError(f"{path}:BOOLEAN")


def base(type_name: str) -> dict[str, Any]:
    return {
        "formal_semantics_id": FORMAL_ID,
        "schema_version": SCHEMA_VERSION,
        "type_name": type_name,
    }


def context() -> dict[str, Any]:
    return {
        "arithmetic_profile_id": ARITHMETIC_PROFILE_ID,
        "height": 8,
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "round_config_id": ROUND_CONFIG_ID,
        "round_id": "round-008",
        "validator_epoch_id": VALIDATOR_EPOCH_ID,
        "view": 0,
    }


def cid(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def contract_fixture() -> dict[str, Any]:
    tuples = [
        {
            "availability_certificate_id": cid(f"ac-{index}"),
            "commitment_id": cid(f"commit-{index}"),
            "domain_id": "code" if index < 2 else "text",
            "ticket_id": f"ticket-{index:03d}",
        }
        for index in range(3)
    ]
    isc = identified(
        "deltareduce.008.input-set-certificate.v1",
        {
            **base("INPUT_SET_CERTIFICATE"),
            **context(),
            "input_root": cid("input-root"),
            "quorum_threshold": 3,
            "signer_ids": ["validator-0", "validator-1", "validator-2"],
            "tuples": tuples,
        },
    )
    seed = identified(
        "deltareduce.008.seed-transcript.v1",
        {
            **base("SEED_TRANSCRIPT"),
            **context(),
            "input_set_certificate_id": isc["content_id"],
            "seed_id": cid("seed"),
            "seed_profile_id": SEED_PROFILE_ID,
            "share_ids": [cid(f"share-{index}") for index in range(3)],
        },
    )
    norms = identified(
        "deltareduce.008.norm-evidence.v1",
        {
            **base("NORM_EVIDENCE"),
            **context(),
            "entries": [
                {
                    "scale_denominator": 16,
                    "squared_norm": str(value),
                    "ticket_id": f"ticket-{index:03d}",
                }
                for index, value in enumerate((25, 41, 9))
            ],
            "input_set_certificate_id": isc["content_id"],
            "norm_root": cid("norm-root"),
        },
    )
    eligibility_entries = [
        {
            "accepted": True,
            "domain_id": item["domain_id"],
            "gamma": {"denominator": 2, "numerator": str(3 + index)},
            "reason_code": "ACCEPTED",
            "ticket_id": item["ticket_id"],
        }
        for index, item in enumerate(tuples)
    ]
    ec = identified(
        "deltareduce.008.eligibility-certificate.v1",
        {
            **base("ELIGIBILITY_CERTIFICATE"),
            **context(),
            "entries": eligibility_entries,
            "input_set_certificate_id": isc["content_id"],
            "norm_evidence_id": norms["content_id"],
            "quorum_threshold": 3,
            "robust_profile_id": ROBUST_PROFILE_ID,
            "signer_ids": ["validator-0", "validator-1", "validator-2"],
        },
    )
    apc = identified(
        "deltareduce.008.aggregation-plan-certificate.v1",
        {
            **base("AGGREGATION_PLAN_CERTIFICATE"),
            **context(),
            "accumulator_proof_id": ACCUMULATOR_PROOF_ID,
            "bucket_assignments": [
                {"bucket_id": f"bucket-{index % 2}", "ticket_id": item["ticket_id"]}
                for index, item in enumerate(tuples)
            ],
            "eligibility_certificate_id": ec["content_id"],
            "input_set_certificate_id": isc["content_id"],
            "iteration_count": 4,
            "quorum_threshold": 3,
            "seed_transcript_id": seed["content_id"],
            "signer_ids": ["validator-0", "validator-1", "validator-2"],
            "transcript_root": cid("clipping-transcript"),
            "weights": [
                {"alpha": {"denominator": 3, "numerator": "1"}, "ticket_id": item["ticket_id"]}
                for item in tuples
            ],
        },
    )
    shard_qcs = []
    required_keys = []
    leaves = []
    for domain in ("code", "text"):
        for shard in ("shard-000", "shard-001"):
            value = {
                **base("PARAMETER_SHARD_QC"),
                **context(),
                "aggregation_plan_certificate_id": apc["content_id"],
                "denominator": 3,
                "domain_id": domain,
                "eligibility_certificate_id": ec["content_id"],
                "input_leaf_ids": [cid(f"{domain}-{shard}-leaf-{index}") for index in range(3)],
                "input_set_certificate_id": isc["content_id"],
                "quorum_threshold": 3,
                "result_numerators": [str(12 + len(shard_qcs)), str(-3 - len(shard_qcs))],
                "shard_id": shard,
                "signer_ids": ["validator-0", "validator-1", "validator-2"],
            }
            item = identified("deltareduce.008.parameter-shard-qc.v1", value)
            shard_qcs.append(item)
            required_keys.append({"domain_id": domain, "shard_id": shard})
            leaves.append(
                {
                    "domain_id": domain,
                    "parameter_shard_qc_id": item["content_id"],
                    "shard_id": shard,
                }
            )
    root = identified(
        "deltareduce.008.aggregate-root-qc.v1",
        {
            **base("AGGREGATE_ROOT_QC"),
            **context(),
            "aggregation_plan_certificate_id": apc["content_id"],
            "eligibility_certificate_id": ec["content_id"],
            "input_set_certificate_id": isc["content_id"],
            "leaves": leaves,
            "merkle_root": aggregate_merkle_root(leaves),
            "quorum_threshold": 3,
            "required_keys": required_keys,
            "signer_ids": ["validator-0", "validator-1", "validator-2"],
        },
    )
    profile = identified(
        "deltareduce.008.apply-arithmetic-profile.v1",
        {
            **base("APPLY_ARITHMETIC_PROFILE"),
            "accumulator_proof_id": ACCUMULATOR_PROOF_ID,
            "domain_weights": [
                {"domain_id": "code", "pi": {"denominator": 2, "numerator": "1"}},
                {"domain_id": "text", "pi": {"denominator": 2, "numerator": "1"}},
            ],
            "learning_rate": {"denominator": 100, "numerator": "1"},
            "momentum": {"denominator": 10, "numerator": "9"},
            "nesterov": True,
            "rounding": "HALF_TOWARD_POSITIVE",
            "weight_decay": {"denominator": 1000, "numerator": "1"},
        },
    )
    candidate = identified(
        "deltareduce.008.apply-candidate.v1",
        {
            **base("APPLY_CANDIDATE"),
            **context(),
            "aggregate_root_qc_id": root["content_id"],
            "apply_arithmetic_profile_id": profile["content_id"],
            "next_model_hash": cid("next-model"),
            "next_model_values": ["101", "-49"],
            "next_optimizer_hash": cid("next-optimizer"),
            "next_optimizer_values": ["11", "-4"],
            "parent_checkpoint_id": PARENT_CHECKPOINT_ID,
            "parent_optimizer_hash": cid("parent-optimizer"),
        },
    )
    apply_qc = identified(
        "deltareduce.008.apply-qc.v1",
        {
            **base("APPLY_QC"),
            **context(),
            "aggregate_root_qc_id": root["content_id"],
            "apply_arithmetic_profile_id": profile["content_id"],
            "apply_candidate_id": candidate["content_id"],
            "next_model_hash": candidate["value"]["next_model_hash"],
            "next_optimizer_hash": candidate["value"]["next_optimizer_hash"],
            "parent_checkpoint_id": PARENT_CHECKPOINT_ID,
            "quorum_threshold": 3,
            "signer_ids": ["validator-0", "validator-1", "validator-2"],
        },
    )
    pointer = identified(
        "deltareduce.008.current-pointer-command.v1",
        {
            **base("CURRENT_POINTER_COMMAND"),
            **context(),
            "apply_qc_id": apply_qc["content_id"],
            "expected_parent_checkpoint_id": PARENT_CHECKPOINT_ID,
            "next_checkpoint_id": candidate["value"]["next_model_hash"],
            "next_optimizer_hash": candidate["value"]["next_optimizer_hash"],
        },
    )
    return {
        "aggregate_root_qc": root,
        "aggregation_plan_certificate": apc,
        "apply_arithmetic_profile": profile,
        "apply_candidate": candidate,
        "apply_qc": apply_qc,
        "current_pointer_command": pointer,
        "eligibility_certificate": ec,
        "expected": {
            "formal_semantics_id": FORMAL_ID,
            "required_key_count": 4,
            "shard_qc_count": 4,
            "status": "ACCEPT",
            "terminal_action": "ACT-CURRENT-ADVANCE",
        },
        "formal_semantics_id": FORMAL_ID,
        "input_set_certificate": isc,
        "norm_evidence": norms,
        "parameter_shard_qcs": shard_qcs,
        "schema_version": SCHEMA_VERSION,
        "seed_transcript": seed,
    }


def invalid_fixture(golden: dict[str, Any]) -> dict[str, Any]:
    early_seed = copy.deepcopy(golden["seed_transcript"]["value"])
    early_seed["input_set_certificate_id"] = "NONE"
    mixed = copy.deepcopy(golden["parameter_shard_qcs"][0]["value"])
    mixed["aggregation_plan_certificate_id"] = cid("wrong-apc")
    incomplete = copy.deepcopy(golden["aggregate_root_qc"]["value"])
    incomplete["leaves"] = incomplete["leaves"][:-1]
    unsafe = copy.deepcopy(golden["aggregation_plan_certificate"]["value"])
    unsafe["accumulator_proof_id"] = cid("unsafe-proof")
    conflict = copy.deepcopy(golden["apply_qc"]["value"])
    conflict["next_model_hash"] = cid("conflicting-next-model")
    current = copy.deepcopy(golden["current_pointer_command"]["value"])
    current["apply_qc_id"] = cid("missing-apply-qc")
    return {
        "cases": [
            {
                "expected_reason": "INPUT_SET_NOT_CERTIFIED",
                "name": "early-seed",
                "value": early_seed,
            },
            {"expected_reason": "MIXED_VIEW_SHARD", "name": "wrong-apc-parent", "value": mixed},
            {
                "expected_reason": "AGGREGATE_INCOMPLETE",
                "name": "missing-required-shard",
                "value": incomplete,
            },
            {"expected_reason": "ACCUMULATOR_PROOF_UNSAFE", "name": "unsafe-apc", "value": unsafe},
            {
                "expected_reason": "CONFLICTING_APPLY",
                "name": "conflicting-apply",
                "value": conflict,
            },
            {
                "expected_reason": "APPLY_QC_REQUIRED",
                "name": "uncertified-current",
                "value": current,
            },
        ],
        "formal_semantics_id": FORMAL_ID,
        "schema_version": SCHEMA_VERSION,
    }


FIXTURE_GROUPS: Final = {
    "aggregate_root_qc": ("aggregate-root-qc", "deltareduce.008.aggregate-root-qc.v1"),
    "aggregation_plan_certificate": (
        "aggregation-plan-certificate",
        "deltareduce.008.aggregation-plan-certificate.v1",
    ),
    "apply_arithmetic_profile": (
        "apply-arithmetic-profile",
        "deltareduce.008.apply-arithmetic-profile.v1",
    ),
    "apply_candidate": ("apply-candidate", "deltareduce.008.apply-candidate.v1"),
    "apply_qc": ("apply-qc", "deltareduce.008.apply-qc.v1"),
    "current_pointer_command": (
        "current-pointer-command",
        "deltareduce.008.current-pointer-command.v1",
    ),
    "eligibility_certificate": (
        "eligibility-certificate",
        "deltareduce.008.eligibility-certificate.v1",
    ),
    "input_set_certificate": (
        "input-set-certificate",
        "deltareduce.008.input-set-certificate.v1",
    ),
    "norm_evidence": ("norm-evidence", "deltareduce.008.norm-evidence.v1"),
    "seed_transcript": ("seed-transcript", "deltareduce.008.seed-transcript.v1"),
}


def unwrap(item: dict[str, Any], domain: str) -> dict[str, Any]:
    value = item.get("value")
    require(isinstance(value, dict), "IDENTIFIED_VALUE_INVALID")
    require(
        item == identified(domain, value),
        "IDENTIFIED_BYTES_OR_ID_DRIFT",
        value.get("type_name", "UNKNOWN"),
    )
    return value


def validate_contract(document: dict[str, Any]) -> dict[str, Any]:
    schemas = schema_documents()
    values: dict[str, dict[str, Any]] = {}
    for group, (schema_name, domain) in FIXTURE_GROUPS.items():
        value = unwrap(document[group], domain)
        validate_schema(value, schemas[schema_name])
        values[group] = value
    shards = document.get("parameter_shard_qcs")
    require(isinstance(shards, list) and shards, "SHARD_QC_SET_INVALID")
    shard_values = []
    for item in shards:
        value = unwrap(item, "deltareduce.008.parameter-shard-qc.v1")
        validate_schema(value, schemas["parameter-shard-qc"])
        shard_values.append(value)

    isc_id = document["input_set_certificate"]["content_id"]
    ec_id = document["eligibility_certificate"]["content_id"]
    apc_id = document["aggregation_plan_certificate"]["content_id"]
    root_id = document["aggregate_root_qc"]["content_id"]
    profile_id = document["apply_arithmetic_profile"]["content_id"]
    candidate_id = document["apply_candidate"]["content_id"]
    apply_qc_id = document["apply_qc"]["content_id"]
    require(
        values["seed_transcript"]["input_set_certificate_id"] == isc_id, "SEED_ISC_PARENT_DRIFT"
    )
    require(values["norm_evidence"]["input_set_certificate_id"] == isc_id, "NORM_ISC_PARENT_DRIFT")
    require(
        values["eligibility_certificate"]["input_set_certificate_id"] == isc_id,
        "EC_ISC_PARENT_DRIFT",
    )
    require(
        values["aggregation_plan_certificate"]["input_set_certificate_id"] == isc_id,
        "APC_ISC_PARENT_DRIFT",
    )
    require(
        values["aggregation_plan_certificate"]["eligibility_certificate_id"] == ec_id,
        "APC_EC_PARENT_DRIFT",
    )
    for shard in shard_values:
        require(
            (
                shard["input_set_certificate_id"],
                shard["eligibility_certificate_id"],
                shard["aggregation_plan_certificate_id"],
            )
            == (isc_id, ec_id, apc_id),
            "SHARD_PARENT_DRIFT",
        )
    root = values["aggregate_root_qc"]
    required = [(item["domain_id"], item["shard_id"]) for item in root["required_keys"]]
    leaves = [(item["domain_id"], item["shard_id"]) for item in root["leaves"]]
    require(
        required == sorted(required) and len(required) == len(set(required)),
        "REQUIRED_MATRIX_INVALID",
    )
    require(leaves == required, "AGGREGATE_COVERAGE_DRIFT")
    require(
        root["merkle_root"] == aggregate_merkle_root(root["leaves"]),
        "AGGREGATE_MERKLE_DRIFT",
    )
    shard_ids = {item["content_id"] for item in shards}
    require(
        {item["parameter_shard_qc_id"] for item in root["leaves"]} == shard_ids,
        "AGGREGATE_LEAF_ID_DRIFT",
    )
    candidate = values["apply_candidate"]
    require(
        (candidate["aggregate_root_qc_id"], candidate["apply_arithmetic_profile_id"])
        == (root_id, profile_id),
        "APPLY_CANDIDATE_PARENT_DRIFT",
    )
    apply_qc = values["apply_qc"]
    require(
        (
            apply_qc["aggregate_root_qc_id"],
            apply_qc["apply_arithmetic_profile_id"],
            apply_qc["apply_candidate_id"],
            apply_qc["next_model_hash"],
            apply_qc["next_optimizer_hash"],
        )
        == (
            root_id,
            profile_id,
            candidate_id,
            candidate["next_model_hash"],
            candidate["next_optimizer_hash"],
        ),
        "APPLY_QC_BODY_DRIFT",
    )
    pointer = values["current_pointer_command"]
    require(pointer["apply_qc_id"] == apply_qc_id, "CURRENT_APPLY_QC_DRIFT")
    require(pointer["next_checkpoint_id"] == candidate["next_model_hash"], "CURRENT_NEXT_DRIFT")
    return {
        "apply_qc_id": apply_qc_id,
        "input_set_certificate_id": isc_id,
        "required_key_count": len(required),
        "shard_qc_count": len(shards),
        "status": "PASS",
    }


def validate_invalid(document: dict[str, Any]) -> list[dict[str, str]]:
    expected = {
        "early-seed": "INPUT_SET_NOT_CERTIFIED",
        "wrong-apc-parent": "MIXED_VIEW_SHARD",
        "missing-required-shard": "AGGREGATE_INCOMPLETE",
        "unsafe-apc": "ACCUMULATOR_PROOF_UNSAFE",
        "conflicting-apply": "CONFLICTING_APPLY",
        "uncertified-current": "APPLY_QC_REQUIRED",
    }
    results = []
    cases = document.get("cases")
    require(isinstance(cases, list), "INVALID_CASES_MISSING")
    for case in cases:
        name = case.get("name")
        reason = case.get("expected_reason")
        require(
            name in expected and reason == expected[name], "INVALID_CASE_REASON_DRIFT", str(name)
        )
        results.append({"expected_reason": reason, "name": name, "status": "PASS"})
    require(len(results) == len(expected), "INVALID_CASE_COUNT_DRIFT")
    return results


def registry_document(outputs: dict[str, bytes]) -> dict[str, Any]:
    artifacts = []
    media_types = []
    for name, (schema_id, _, media_type) in sorted(SCHEMAS.items()):
        path = f"schemas/008/{name}-v1.json"
        artifacts.append({"id": schema_id, "path": path, "sha256": sha256_bytes(outputs[path])})
        media_types.append(
            {
                "id": schema_id.replace("SCHEMA-", "MEDIA-"),
                "schema_id": schema_id,
                "value": media_type,
            }
        )
    fixtures = []
    for fixture_id, path in (
        ("CERTIFICATE008-CROSS-LANGUAGE-GOLDEN-V1", "fixtures/008/cross-language/golden-v1.json"),
        ("CERTIFICATE008-NEGATIVE-V1", "fixtures/008/invalid/certificate-negative-v1.json"),
        ("CERTIFICATE008-VALID-CONTRACT-V1", "fixtures/008/valid/certificate-contract-v1.json"),
    ):
        fixtures.append({"id": fixture_id, "path": path, "sha256": sha256_bytes(outputs[path])})
    return {
        "artifacts": artifacts,
        "fixtures": fixtures,
        "formal_semantics_id": FORMAL_ID,
        "media_types": media_types,
        "registry_version": "008.1.0",
        "schema_version": SCHEMA_VERSION,
        "semantic_completeness_claimed": False,
    }


def replace_prefixed(
    items: list[dict[str, Any]], prefixes: tuple[str, ...], new: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    kept = [
        item for item in items if not any(str(item.get("id", "")).startswith(p) for p in prefixes)
    ]
    return [*kept, *new]


def global_registry(outputs: dict[str, bytes], local: dict[str, Any]) -> dict[str, Any]:
    process = subprocess.run(
        ["git", "show", "HEAD:delta-protocol/registry.json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, "BASE_REGISTRY_READ_FAILED")
    document = json.loads(process.stdout)
    registry_path = "schemas/008/registry-v1.json"
    document["extensions"] = sorted(
        replace_prefixed(
            document["extensions"],
            ("REGISTRY-CERTIFICATE-008-",),
            [
                {
                    "id": "REGISTRY-CERTIFICATE-008-V1",
                    "path": registry_path,
                    "sha256": sha256_bytes(outputs[registry_path]),
                }
            ],
        ),
        key=lambda item: item["path"],
    )
    document["fixtures"] = sorted(
        replace_prefixed(document["fixtures"], ("CERTIFICATE008-",), local["fixtures"]),
        key=lambda item: item["path"],
    )
    document["schemas"] = sorted(
        replace_prefixed(
            document["schemas"],
            tuple(item[0].replace("-V1", "-") for item in SCHEMAS.values()),
            local["artifacts"],
        ),
        key=lambda item: item["path"],
    )
    document["media_types"] = replace_prefixed(
        document["media_types"],
        tuple(
            item[0].replace("SCHEMA-", "MEDIA-").replace("-V1", "-") for item in SCHEMAS.values()
        ),
        local["media_types"],
    )
    return document


def build_outputs() -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    for name, document in schema_documents().items():
        outputs[f"schemas/008/{name}-v1.json"] = pretty_json_bytes(document)
    golden = contract_fixture()
    outputs["fixtures/008/cross-language/golden-v1.json"] = file_json_bytes(golden)
    outputs["fixtures/008/valid/certificate-contract-v1.json"] = file_json_bytes(
        copy.deepcopy(golden)
    )
    outputs["fixtures/008/invalid/certificate-negative-v1.json"] = file_json_bytes(
        invalid_fixture(golden)
    )
    local = registry_document(outputs)
    outputs["schemas/008/registry-v1.json"] = pretty_json_bytes(local)
    outputs["registry.json"] = pretty_json_bytes(global_registry(outputs, local))
    return outputs


def validate_outputs(outputs: dict[str, bytes]) -> dict[str, Any]:
    golden = json.loads(outputs["fixtures/008/cross-language/golden-v1.json"])
    valid = json.loads(outputs["fixtures/008/valid/certificate-contract-v1.json"])
    invalid = json.loads(outputs["fixtures/008/invalid/certificate-negative-v1.json"])
    require(golden == valid, "VALID_FIXTURE_DRIFT")
    valid_result = validate_contract(golden)
    invalid_result = validate_invalid(invalid)
    registry = json.loads(outputs["registry.json"])
    for key in ("extensions", "fixtures", "media_types", "schemas"):
        ids = [item["id"] for item in registry[key]]
        require(len(ids) == len(set(ids)), "REGISTRY_DUPLICATE_ID", key)
    return {
        "formal_semantics_id": FORMAL_ID,
        "invalid_cases": invalid_result,
        "output_count": len(outputs),
        "schema_count": len(SCHEMAS),
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "valid": valid_result,
    }


def write_outputs(outputs: dict[str, bytes]) -> None:
    for relative, content in outputs.items():
        path = ROOT / "delta-protocol" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def check_outputs(outputs: dict[str, bytes]) -> None:
    for relative, expected in outputs.items():
        path = ROOT / "delta-protocol" / relative
        require(path.is_file(), "CONTRACT_OUTPUT_MISSING", relative)
        require(path.read_bytes() == expected, "CONTRACT_OUTPUT_DRIFT", relative)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    require(arguments.check ^ arguments.write, "EXACTLY_ONE_MODE_REQUIRED")
    outputs = build_outputs()
    result = validate_outputs(outputs)
    if arguments.write:
        write_outputs(outputs)
    else:
        check_outputs(outputs)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
