"""Generate and verify canonical Feature 010 benchmark governance contracts."""

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
    "benchmark-definition": ("SCHEMA-BENCHMARK-DEFINITION-010-V1", "BENCHMARK_DEFINITION"),
    "benchmark-definition-attestation": (
        "SCHEMA-BENCHMARK-DEFINITION-ATTESTATION-010-V1",
        "BENCHMARK_DEFINITION_ATTESTATION",
    ),
    "benchmark-arm": ("SCHEMA-BENCHMARK-ARM-010-V1", "BENCHMARK_ARM"),
    "network-profile": ("SCHEMA-NETWORK-PROFILE-010-V1", "NETWORK_PROFILE"),
    "fault-profile": ("SCHEMA-FAULT-PROFILE-010-V1", "FAULT_PROFILE"),
    "run-manifest": ("SCHEMA-RUN-MANIFEST-010-V1", "RUN_MANIFEST"),
    "environment-manifest": ("SCHEMA-ENVIRONMENT-MANIFEST-010-V1", "ENVIRONMENT_MANIFEST"),
    "quality-evidence": ("SCHEMA-QUALITY-EVIDENCE-010-V1", "QUALITY_EVIDENCE"),
    "safety-evidence": ("SCHEMA-SAFETY-EVIDENCE-010-V1", "SAFETY_EVIDENCE"),
    "efficiency-evidence": ("SCHEMA-EFFICIENCY-EVIDENCE-010-V1", "EFFICIENCY_EVIDENCE"),
    "resilience-evidence": ("SCHEMA-RESILIENCE-EVIDENCE-010-V1", "RESILIENCE_EVIDENCE"),
    "formal-evidence": ("SCHEMA-FORMAL-EVIDENCE-010-V1", "FORMAL_EVIDENCE"),
    "evidence-manifest": ("SCHEMA-EVIDENCE-MANIFEST-010-V1", "EVIDENCE_MANIFEST"),
    "benchmark-result": ("SCHEMA-BENCHMARK-RESULT-010-V1", "BENCHMARK_RESULT"),
    "benchmark-result-qc": ("SCHEMA-BENCHMARK-RESULT-QC-010-V1", "BENCHMARK_RESULT_QC"),
}


class ContractError(RuntimeError):
    """Stable fail-closed Feature 010 contract error."""


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


def hash_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def content_id() -> dict[str, Any]:
    return {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}


def commit_id() -> dict[str, Any]:
    return {"pattern": "^[0-9a-f]{40}$", "type": "string"}


def text(maximum: int = 180) -> dict[str, Any]:
    return {
        "maxLength": maximum,
        "minLength": 1,
        "pattern": "^[A-Za-z0-9._:/+@=-]+$",
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
        "$id": f"urn:deltareduce:schema:010:{name}:1",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": all_properties,
        "required": sorted(all_properties),
        "title": f"DeltaReduce Feature 010 {name} v1",
        "type": "object",
    }


def schema_documents() -> dict[str, dict[str, Any]]:
    metric_definition = strict_object(
        {
            "aggregation": {"enum": ["ALL", "MEAN", "MEDIAN", "P95", "P99"]},
            "direction": {"enum": ["EXACT", "HIGHER", "LOWER"]},
            "implementation_id": content_id(),
            "mandatory": {"type": "boolean"},
            "metric_id": text(),
            "missing_run_rule": {"enum": ["FAIL", "REQUIRE_ALL"]},
            "outlier_rule": {"enum": ["NONE", "PREDECLARED_IQR"]},
            "pass_threshold": uint(),
            "repetitions": uint(1000, 1),
            "statistical_method": {"enum": ["EXACT", "FIXED_SEED_MEAN", "NON_INFERIORITY"]},
            "unit": text(),
        }
    )
    domain_weight = strict_object(
        {
            "denominator": uint(2**31 - 1, 1),
            "domain_id": text(),
            "numerator": uint(2**31 - 1),
        }
    )
    fault_event = strict_object(
        {
            "action": {
                "enum": [
                    "CRASH",
                    "DELAY",
                    "DISCONNECT",
                    "DROP_STORAGE",
                    "DUPLICATE",
                    "PARTITION",
                    "REORDER",
                    "RESTART",
                ]
            },
            "actor_class": {"enum": ["COLLECTOR", "REGION", "STORAGE", "VALIDATOR", "WORKER"]},
            "assumptions_hold": {"type": "boolean"},
            "at_step": uint(),
            "event_id": text(),
            "expected_outcome": {"enum": ["ABORTED", "APPLIED", "BLOCKED", "RECOVERED"]},
        }
    )
    metric_value = strict_object({"metric_id": text(), "unit": text(), "value": uint()})
    gate = strict_object(
        {
            "gate_id": text(),
            "mandatory": {"type": "boolean"},
            "reason": text(320),
            "status": {"enum": ["FAIL", "PASS"]},
        }
    )
    evidence_ref = strict_object(
        {
            "content_id": content_id(),
            "kind": {"enum": ["EFFICIENCY", "FORMAL", "QUALITY", "RESILIENCE", "SAFETY"]},
        }
    )
    return {
        "benchmark-arm": schema_document(
            "benchmark-arm",
            {
                "allowed_differences": array(text(), minimum=0, unique=True),
                "arm_id": text(),
                "deployment_profile": {"enum": ["EMBEDDED_FFM", "ISOLATED_SIDECAR", "PYTHON"]},
                "kind": {
                    "enum": [
                        "CERTIFIED_QLORA",
                        "FLAT_NATIVE",
                        "HIERARCHICAL_NATIVE",
                        "SCIENTIFIC_REFERENCE",
                    ]
                },
                "mandatory": {"type": "boolean"},
                "runtime_profile_id": content_id(),
                "workload_identity": content_id(),
            },
        ),
        "network-profile": schema_document(
            "network-profile",
            {
                "bandwidth_kbps": uint(minimum=1),
                "disconnect_ms": uint(),
                "duplication_ppm": uint(1_000_000),
                "jitter_ms": uint(),
                "loss_ppm": uint(1_000_000),
                "profile_id": text(),
                "reordering_ppm": uint(1_000_000),
                "rtt_ms": uint(),
                "seed": uint(2**31 - 1),
            },
        ),
        "fault-profile": schema_document(
            "fault-profile",
            {"events": array(fault_event, minimum=0), "profile_id": text()},
        ),
        "benchmark-definition": schema_document(
            "benchmark-definition",
            {
                "B": uint(2**31 - 1, 1),
                "H": uint(2**31 - 1, 1),
                "abi_descriptor_id": content_id(),
                "apply_profile_id": content_id(),
                "arm_ids": array(content_id(), minimum=2, unique=True),
                "base_model_id": content_id(),
                "compiler_profile_id": content_id(),
                "compatibility_policy_id": content_id(),
                "dataset_manifest_id": content_id(),
                "decision_function": {"const": "ALL_MANDATORY"},
                "dependency_lock_ids": array(content_id(), unique=True),
                "deployment_policy_id": content_id(),
                "domain_manifest_id": content_id(),
                "evaluation_ids": array(content_id(), unique=True),
                "exclusions": array(text(), minimum=0, unique=True),
                "fault_profile_ids": array(content_id(), unique=True),
                "fixedpoint_profile_id": content_id(),
                "formal_report_id": content_id(),
                "formal_trace_schema_id": content_id(),
                "image_id": content_id(),
                "isolation_policy": {"const": "COMPARE_BOTH"},
                "jdk_profile_id": content_id(),
                "license_policy_id": content_id(),
                "metric_definitions": array(metric_definition),
                "missing_run_policy": {"const": "FAIL_CLOSED"},
                "model_mode": {"enum": ["FULL_MODEL", "QLORA_ADAPTER"]},
                "native_build_id": content_id(),
                "netty_profile_id": content_id(),
                "network_profile_ids": array(content_id(), unique=True),
                "optimizer_profile_id": content_id(),
                "pi_d": array(domain_weight),
                "physical_profile_id": content_id(),
                "primary": {"type": "boolean"},
                "protocol_registry_id": content_id(),
                "python_profile_id": content_id(),
                "qlora_profile_id": content_id(),
                "refinement_evidence_ids": array(content_id(), unique=True),
                "repetitions": uint(1000, 1),
                "robust_profile_id": content_id(),
                "sbom_id": content_id(),
                "seeds": array(uint(2**31 - 1), unique=True),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "ticket_plan_id": content_id(),
                "theorem_build_id": content_id(),
                "tokenizer_id": content_id(),
            },
        ),
        "benchmark-definition-attestation": schema_document(
            "benchmark-definition-attestation",
            {
                "benchmark_definition_id": content_id(),
                "f_b": uint(1000),
                "governance_only": {"const": True},
                "ordered_signers": array(text(), unique=True),
                "quorum_threshold": uint(1000, 1),
                "validator_set_id": content_id(),
            },
        ),
        "environment-manifest": schema_document(
            "environment-manifest",
            {
                "abi_descriptor_id": content_id(),
                "accelerator": text(),
                "compiler_id": content_id(),
                "dependency_lock_ids": array(content_id(), unique=True),
                "hardware_id": content_id(),
                "image_id": content_id(),
                "jdk_id": content_id(),
                "netty_id": content_id(),
                "os_id": content_id(),
                "python_id": content_id(),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "time_sync_status": {"enum": ["BOUNDED", "NOT_APPLICABLE"]},
            },
        ),
        "run-manifest": schema_document(
            "run-manifest",
            {
                "arm_id": content_id(),
                "benchmark_definition_id": content_id(),
                "bytes_sent": uint(),
                "certificate_ids": array(content_id(), minimum=0, unique=True),
                "checkpoint_id": content_id(),
                "copy_fallback_bytes": uint(),
                "domain_ticket_counts": array(
                    strict_object({"count": uint(), "domain_id": text()})
                ),
                "environment_manifest_id": content_id(),
                "evaluation_artifact_ids": array(content_id(), unique=True),
                "fault_profile_id": content_id(),
                "gpu_peak_reserved_bytes": uint(),
                "gpu_utilization_ppm": uint(1_000_000),
                "host_offload_bytes": uint(),
                "model_artifact_id": content_id(),
                "namespace": text(),
                "network_profile_id": content_id(),
                "output_ids": array(content_id(), minimum=0, unique=True),
                "parent_checkpoint_id": content_id(),
                "phase_latencies": array(
                    strict_object({"microseconds": uint(), "phase_id": text()}), minimum=0
                ),
                "processed_tokens": uint(),
                "protocol_hash": content_id(),
                "repetition": uint(1000, 1),
                "seed": uint(2**31 - 1),
                "terminal_outcome": {
                    "enum": ["ABORTED", "APPLIED", "BLOCKED", "PIECE_UNAVAILABLE"]
                },
                "ticket_plan_id": content_id(),
                "total_us": uint(),
                "useful_compute_us": uint(),
                "zero_copy_eligible": uint(),
                "zero_copy_hits": uint(),
            },
        ),
        "quality-evidence": schema_document(
            "quality-evidence",
            {
                "benchmark_definition_id": content_id(),
                "domain_match": {"type": "boolean"},
                "metrics": array(metric_value),
                "run_ids": array(content_id(), minimum=2, unique=True),
                "status": {"enum": ["FAIL", "PASS"]},
                "token_match": {"type": "boolean"},
            },
        ),
        "safety-evidence": schema_document(
            "safety-evidence",
            {
                "attacks": array(
                    strict_object(
                        {
                            "actual_outcome": text(),
                            "attack_id": text(),
                            "current_unchanged": {"type": "boolean"},
                            "expected_outcome": text(),
                            "rejected": {"type": "boolean"},
                        }
                    )
                ),
                "benchmark_definition_id": content_id(),
                "exact_hashes_match": {"type": "boolean"},
                "formal_regression_status": {"const": "PASS"},
                "status": {"enum": ["FAIL", "PASS"]},
            },
        ),
        "efficiency-evidence": schema_document(
            "efficiency-evidence",
            {
                "benchmark_definition_id": content_id(),
                "metrics": array(metric_value),
                "phase_latencies": array(metric_value),
                "status": {"enum": ["FAIL", "PASS"]},
                "zero_copy_fallback_bytes": uint(),
                "zero_copy_hit_rate_ppm": uint(1_000_000),
            },
        ),
        "resilience-evidence": schema_document(
            "resilience-evidence",
            {
                "benchmark_definition_id": content_id(),
                "scenarios": array(
                    strict_object(
                        {
                            "actual_outcome": {
                                "enum": ["ABORTED", "APPLIED", "BLOCKED", "RECOVERED"]
                            },
                            "current_unchanged_on_non_apply": {"type": "boolean"},
                            "expected_outcome": {
                                "enum": ["ABORTED", "APPLIED", "BLOCKED", "RECOVERED"]
                            },
                            "scenario_id": text(),
                        }
                    )
                ),
                "status": {"enum": ["FAIL", "PASS"]},
            },
        ),
        "formal-evidence": schema_document(
            "formal-evidence",
            {
                "benchmark_definition_id": content_id(),
                "classification": {"const": "REGRESSION_ONLY"},
                "formal_go_overlay_commit": commit_id(),
                "formal_report_id": content_id(),
                "formal_source_commit": commit_id(),
                "regression_report_id": content_id(),
                "semantic_completeness_claimed": {"const": False},
                "status": {"const": "PASS"},
            },
        ),
        "evidence-manifest": schema_document(
            "evidence-manifest",
            {
                "benchmark_definition_id": content_id(),
                "complete": {"type": "boolean"},
                "evidence": array(evidence_ref, unique=True),
                "run_ids": array(content_id(), minimum=2, unique=True),
            },
        ),
        "benchmark-result": schema_document(
            "benchmark-result",
            {
                "benchmark_definition_id": content_id(),
                "decision": {"enum": ["GO", "NO_GO"]},
                "evidence_manifest_id": content_id(),
                "failed_or_missing": array(text(), minimum=0, unique=True),
                "gate_table": array(gate),
                "limitations": array(text(320), minimum=0, unique=True),
                "measured_values": array(metric_value, minimum=0),
                "run_ids": array(content_id(), minimum=2, unique=True),
            },
        ),
        "benchmark-result-qc": schema_document(
            "benchmark-result-qc",
            {
                "benchmark_result_id": content_id(),
                "decision": {"enum": ["GO", "NO_GO"]},
                "evaluator_set_id": content_id(),
                "f_b": uint(1000),
                "governance_only": {"const": True},
                "ordered_signers": array(text(), unique=True),
                "protocol_current_transition": {"const": False},
                "quorum_threshold": uint(1000, 1),
            },
        ),
    }


def identified(schema_name: str, value: dict[str, Any]) -> dict[str, Any]:
    encoded = canonical_json_bytes(value)
    domain = f"deltareduce.010.{schema_name}.v1"
    digest = hashlib.sha256(domain.encode() + b"\0" + encoded).hexdigest()
    return {
        "bytes_hex": encoded.hex(),
        "content_id": f"sha256:{digest}",
        "schema_name": schema_name,
        "value": value,
    }


def common(type_name: str) -> dict[str, Any]:
    return {
        "formal_semantics_id": FORMAL_ID,
        "schema_version": SCHEMA_VERSION,
        "type_name": type_name,
    }


def fixture_artifacts() -> dict[str, dict[str, Any]]:
    artifacts: dict[str, dict[str, Any]] = {}
    workload_id = hash_id("tiny-token-domain-workload")
    for key, kind, deployment in (
        ("arm_reference", "SCIENTIFIC_REFERENCE", "PYTHON"),
        ("arm_embedded", "CERTIFIED_QLORA", "EMBEDDED_FFM"),
        ("arm_sidecar", "CERTIFIED_QLORA", "ISOLATED_SIDECAR"),
    ):
        artifacts[key] = identified(
            "benchmark-arm",
            {
                **common("BENCHMARK_ARM"),
                "allowed_differences": ["deployment_profile"],
                "arm_id": key.replace("arm_", ""),
                "deployment_profile": deployment,
                "kind": kind,
                "mandatory": True,
                "runtime_profile_id": hash_id(f"runtime:{deployment}"),
                "workload_identity": workload_id,
            },
        )
    artifacts["network_profile"] = identified(
        "network-profile",
        {
            **common("NETWORK_PROFILE"),
            "bandwidth_kbps": 10_000,
            "disconnect_ms": 0,
            "duplication_ppm": 1_000,
            "jitter_ms": 5,
            "loss_ppm": 10_000,
            "profile_id": "synthetic-wan",
            "reordering_ppm": 5_000,
            "rtt_ms": 80,
            "seed": 1010,
        },
    )
    artifacts["fault_profile"] = identified(
        "fault-profile",
        {
            **common("FAULT_PROFILE"),
            "events": [
                {
                    "action": "CRASH",
                    "actor_class": "WORKER",
                    "assumptions_hold": True,
                    "at_step": 2,
                    "event_id": "worker-loss-10pct",
                    "expected_outcome": "APPLIED",
                },
                {
                    "action": "RESTART",
                    "actor_class": "VALIDATOR",
                    "assumptions_hold": True,
                    "at_step": 3,
                    "event_id": "validator-restart",
                    "expected_outcome": "RECOVERED",
                },
            ],
            "profile_id": "synthetic-resilience",
        },
    )
    metric_definitions = [
        {
            "aggregation": "ALL",
            "direction": "EXACT",
            "implementation_id": hash_id("metric:protocol-exactness:v1"),
            "mandatory": True,
            "metric_id": "protocol_exactness",
            "missing_run_rule": "REQUIRE_ALL",
            "outlier_rule": "NONE",
            "pass_threshold": 1,
            "repetitions": 2,
            "statistical_method": "EXACT",
            "unit": "boolean",
        },
        {
            "aggregation": "MEAN",
            "direction": "LOWER",
            "implementation_id": hash_id("metric:validation-loss:v1"),
            "mandatory": True,
            "metric_id": "validation_loss_micro",
            "missing_run_rule": "FAIL",
            "outlier_rule": "NONE",
            "pass_threshold": 1_100_000,
            "repetitions": 2,
            "statistical_method": "NON_INFERIORITY",
            "unit": "micro-loss",
        },
        {
            "aggregation": "P95",
            "direction": "LOWER",
            "implementation_id": hash_id("metric:network-share:v1"),
            "mandatory": True,
            "metric_id": "network_share_ppm",
            "missing_run_rule": "REQUIRE_ALL",
            "outlier_rule": "NONE",
            "pass_threshold": 150_000,
            "repetitions": 2,
            "statistical_method": "FIXED_SEED_MEAN",
            "unit": "ppm",
        },
    ]
    artifacts["definition"] = identified(
        "benchmark-definition",
        {
            **common("BENCHMARK_DEFINITION"),
            "B": 8,
            "H": 2,
            "abi_descriptor_id": hash_id("abi-003-v1"),
            "apply_profile_id": hash_id("apply-profile-v1"),
            "arm_ids": [
                artifacts["arm_reference"]["content_id"],
                artifacts["arm_embedded"]["content_id"],
                artifacts["arm_sidecar"]["content_id"],
            ],
            "base_model_id": hash_id("tiny-base"),
            "compiler_profile_id": hash_id("compiler-profile-fixture"),
            "compatibility_policy_id": hash_id("compatibility-exact-v1"),
            "dataset_manifest_id": hash_id("tiny-dataset"),
            "decision_function": "ALL_MANDATORY",
            "dependency_lock_ids": [hash_id("uv-lock"), hash_id("java-lock")],
            "deployment_policy_id": hash_id("compare-embedded-sidecar"),
            "domain_manifest_id": hash_id("tiny-domains"),
            "evaluation_ids": [hash_id("tiny-validation"), hash_id("tiny-downstream")],
            "exclusions": [],
            "fault_profile_ids": [artifacts["fault_profile"]["content_id"]],
            "fixedpoint_profile_id": hash_id("fixedpoint-004-v1"),
            "formal_report_id": hash_id("formal-report-go"),
            "formal_trace_schema_id": hash_id("formal-trace-schema-v1"),
            "image_id": hash_id("fixture-image"),
            "isolation_policy": "COMPARE_BOTH",
            "jdk_profile_id": hash_id("jdk-25-profile"),
            "license_policy_id": hash_id("cc0-fixture-license"),
            "metric_definitions": metric_definitions,
            "missing_run_policy": "FAIL_CLOSED",
            "model_mode": "QLORA_ADAPTER",
            "native_build_id": hash_id("native-build-fixture"),
            "netty_profile_id": hash_id("netty-profile-fixture"),
            "network_profile_ids": [artifacts["network_profile"]["content_id"]],
            "optimizer_profile_id": hash_id("optimizer-intent-v1"),
            "pi_d": [{"denominator": 1, "domain_id": "tiny-text", "numerator": 1}],
            "physical_profile_id": hash_id("physical-profile-009"),
            "primary": False,
            "protocol_registry_id": hash_id("protocol-registry-009"),
            "python_profile_id": hash_id("python-3.12-pytorch-2.6"),
            "qlora_profile_id": hash_id("qlora-profile-009"),
            "refinement_evidence_ids": [
                hash_id(f"feature-{feature:03d}-refinement") for feature in range(3, 10)
            ],
            "repetitions": 2,
            "robust_profile_id": hash_id("robust-profile-v1"),
            "sbom_id": hash_id("fixture-sbom"),
            "seeds": [17, 29],
            "source_commit": "f43e39fa1c60d256bab5d7e37e0756f28438d5e4",
            "source_tree": "9" * 40,
            "ticket_plan_id": hash_id("tiny-ticket-plan"),
            "theorem_build_id": hash_id("lean-build"),
            "tokenizer_id": hash_id("tiny-tokenizer"),
        },
    )
    definition_id = artifacts["definition"]["content_id"]
    artifacts["definition_attestation"] = identified(
        "benchmark-definition-attestation",
        {
            **common("BENCHMARK_DEFINITION_ATTESTATION"),
            "benchmark_definition_id": definition_id,
            "f_b": 1,
            "governance_only": True,
            "ordered_signers": ["reviewer-0", "reviewer-1", "reviewer-2"],
            "quorum_threshold": 3,
            "validator_set_id": hash_id("benchmark-reviewers-v1"),
        },
    )
    artifacts["environment"] = identified(
        "environment-manifest",
        {
            **common("ENVIRONMENT_MANIFEST"),
            "abi_descriptor_id": hash_id("abi-003-v1"),
            "accelerator": "CPU-MOCK",
            "compiler_id": hash_id("compiler-fixture"),
            "dependency_lock_ids": [hash_id("uv-lock"), hash_id("java-lock")],
            "hardware_id": hash_id("fixture-hardware"),
            "image_id": hash_id("fixture-image"),
            "jdk_id": hash_id("jdk-25"),
            "netty_id": hash_id("netty-fixture"),
            "os_id": hash_id("fixture-os"),
            "python_id": hash_id("python-3.12"),
            "source_commit": "f43e39fa1c60d256bab5d7e37e0756f28438d5e4",
            "source_tree": "9" * 40,
            "time_sync_status": "NOT_APPLICABLE",
        },
    )
    run_ids: list[str] = []
    for key, arm_key, seed in (
        ("run_reference", "arm_reference", 17),
        ("run_embedded", "arm_embedded", 17),
        ("run_sidecar", "arm_sidecar", 29),
    ):
        certificates = (
            []
            if arm_key == "arm_reference"
            else [hash_id(f"certificate:{key}:{index}") for index in range(6)]
        )
        evaluations = [hash_id(f"evaluation:{key}:{index}") for index in range(2)]
        checkpoint_id = hash_id(f"checkpoint:{key}")
        model_artifact_id = hash_id(f"model:{key}")
        protocol_hash = hash_id(f"protocol:{key}")
        output_ids = [
            hash_id(f"output:{key}"),
            protocol_hash,
            checkpoint_id,
            model_artifact_id,
            *certificates,
            *evaluations,
        ]
        artifacts[key] = identified(
            "run-manifest",
            {
                **common("RUN_MANIFEST"),
                "arm_id": artifacts[arm_key]["content_id"],
                "benchmark_definition_id": definition_id,
                "bytes_sent": 1024,
                "certificate_ids": certificates,
                "checkpoint_id": checkpoint_id,
                "copy_fallback_bytes": 1024 if arm_key != "arm_embedded" else 0,
                "domain_ticket_counts": [{"count": 1, "domain_id": "tiny-text"}],
                "environment_manifest_id": artifacts["environment"]["content_id"],
                "evaluation_artifact_ids": evaluations,
                "fault_profile_id": artifacts["fault_profile"]["content_id"],
                "gpu_peak_reserved_bytes": 1_000_000,
                "gpu_utilization_ppm": 500_000,
                "host_offload_bytes": 0,
                "model_artifact_id": model_artifact_id,
                "namespace": f"benchmark-010-{key}",
                "network_profile_id": artifacts["network_profile"]["content_id"],
                "output_ids": output_ids,
                "parent_checkpoint_id": hash_id("tiny-parent-checkpoint"),
                "phase_latencies": [
                    {"microseconds": 100, "phase_id": "native_transition"},
                    {"microseconds": 75, "phase_id": "wal"},
                ],
                "processed_tokens": 8,
                "protocol_hash": protocol_hash,
                "repetition": 1,
                "seed": seed,
                "terminal_outcome": "APPLIED",
                "ticket_plan_id": hash_id("tiny-ticket-plan"),
                "total_us": 10_000,
                "useful_compute_us": 9_000,
                "zero_copy_eligible": 1 if arm_key != "arm_reference" else 0,
                "zero_copy_hits": 1 if arm_key == "arm_embedded" else 0,
            },
        )
        run_ids.append(artifacts[key]["content_id"])
    artifacts["quality"] = identified(
        "quality-evidence",
        {
            **common("QUALITY_EVIDENCE"),
            "benchmark_definition_id": definition_id,
            "domain_match": True,
            "metrics": [
                {"metric_id": "validation_loss_micro", "unit": "micro-loss", "value": 1_000_000},
                {"metric_id": "downstream_accuracy_ppm", "unit": "ppm", "value": 750_000},
            ],
            "run_ids": run_ids,
            "status": "PASS",
            "token_match": True,
        },
    )
    mandatory_attacks = (
        "ac-mutation",
        "certificate-downgrade",
        "conflicting-apply",
        "conflicting-config",
        "frankenstein-shard",
        "incomplete-root",
        "seed-before-isc",
        "unsafe-accumulator",
        "vote-equivocation",
    )
    artifacts["safety"] = identified(
        "safety-evidence",
        {
            **common("SAFETY_EVIDENCE"),
            "attacks": [
                {
                    "actual_outcome": "REJECTED",
                    "attack_id": attack_id,
                    "current_unchanged": True,
                    "expected_outcome": "REJECTED",
                    "rejected": True,
                }
                for attack_id in mandatory_attacks
            ],
            "benchmark_definition_id": definition_id,
            "exact_hashes_match": True,
            "formal_regression_status": "PASS",
            "status": "PASS",
        },
    )
    artifacts["efficiency"] = identified(
        "efficiency-evidence",
        {
            **common("EFFICIENCY_EVIDENCE"),
            "benchmark_definition_id": definition_id,
            "metrics": [
                {"metric_id": "network_share_ppm", "unit": "ppm", "value": 100_000},
                {"metric_id": "gpu_utilization_ppm", "unit": "ppm", "value": 800_000},
            ],
            "phase_latencies": [
                {"metric_id": "apply_p95_us", "unit": "microseconds", "value": 500}
            ],
            "status": "PASS",
            "zero_copy_fallback_bytes": 128,
            "zero_copy_hit_rate_ppm": 900_000,
        },
    )
    artifacts["resilience"] = identified(
        "resilience-evidence",
        {
            **common("RESILIENCE_EVIDENCE"),
            "benchmark_definition_id": definition_id,
            "scenarios": [
                {
                    "actual_outcome": outcome,
                    "current_unchanged_on_non_apply": True,
                    "expected_outcome": outcome,
                    "scenario_id": scenario,
                }
                for scenario, outcome in (
                    ("initial-seed-loss", "RECOVERED"),
                    ("worker-loss-10pct", "APPLIED"),
                    ("validator-restart", "RECOVERED"),
                    ("storage-loss", "RECOVERED"),
                    ("regional-partition", "ABORTED"),
                )
            ],
            "status": "PASS",
        },
    )
    artifacts["formal"] = identified(
        "formal-evidence",
        {
            **common("FORMAL_EVIDENCE"),
            "benchmark_definition_id": definition_id,
            "classification": "REGRESSION_ONLY",
            "formal_go_overlay_commit": "7abd0f43f8f1b15ec9aa6c3d2c80b32bfb4a6eca",
            "formal_report_id": artifacts["definition"]["value"]["formal_report_id"],
            "formal_source_commit": "1e6e0f6f70056161d95933e71494ec390c7c1151",
            "regression_report_id": hash_id("formal-regression-execution-report"),
            "semantic_completeness_claimed": False,
            "status": "PASS",
        },
    )
    evidence = [
        {"content_id": artifacts["formal"]["content_id"], "kind": "FORMAL"},
        {"content_id": artifacts["quality"]["content_id"], "kind": "QUALITY"},
        {"content_id": artifacts["safety"]["content_id"], "kind": "SAFETY"},
        {"content_id": artifacts["efficiency"]["content_id"], "kind": "EFFICIENCY"},
        {"content_id": artifacts["resilience"]["content_id"], "kind": "RESILIENCE"},
    ]
    artifacts["evidence_manifest"] = identified(
        "evidence-manifest",
        {
            **common("EVIDENCE_MANIFEST"),
            "benchmark_definition_id": definition_id,
            "complete": True,
            "evidence": evidence,
            "run_ids": run_ids,
        },
    )
    gate_ids = (
        "EVIDENCE",
        "FORMAL_REGRESSION",
        "PROCESS_ISOLATION",
        "PROTOCOL_EXACTNESS",
        "QUALITY",
        "RESILIENCE",
        "WAN_P2P",
    )
    artifacts["result"] = identified(
        "benchmark-result",
        {
            **common("BENCHMARK_RESULT"),
            "benchmark_definition_id": definition_id,
            "decision": "GO",
            "evidence_manifest_id": artifacts["evidence_manifest"]["content_id"],
            "failed_or_missing": [],
            "gate_table": [
                {"gate_id": gate_id, "mandatory": True, "reason": "VERIFIED", "status": "PASS"}
                for gate_id in gate_ids
            ],
            "limitations": ["SYNTHETIC_FIXTURE_NOT_PRIMARY_EVIDENCE"],
            "measured_values": [],
            "run_ids": run_ids,
        },
    )
    artifacts["result_qc"] = identified(
        "benchmark-result-qc",
        {
            **common("BENCHMARK_RESULT_QC"),
            "benchmark_result_id": artifacts["result"]["content_id"],
            "decision": "GO",
            "evaluator_set_id": hash_id("benchmark-evaluators-v1"),
            "f_b": 1,
            "governance_only": True,
            "ordered_signers": ["evaluator-0", "evaluator-1", "evaluator-2"],
            "protocol_current_transition": False,
            "quorum_threshold": 3,
        },
    )
    return artifacts


def validate_schema(schema: dict[str, Any], value: object, path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            raise SchemaValidationError(f"{path}:TYPE_OBJECT")
        properties = schema.get("properties", {})
        missing = [key for key in schema.get("required", []) if key not in value]
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
    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}:CONST")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}:ENUM")


def validate_identified(wrapper: dict[str, Any], schemas: dict[str, Any]) -> None:
    schema_name = wrapper.get("schema_name")
    value = wrapper.get("value")
    require(isinstance(schema_name, str) and schema_name in schemas, "SCHEMA_NAME_INVALID")
    require(isinstance(value, dict), "ARTIFACT_VALUE_INVALID", str(schema_name))
    validate_schema(schemas[schema_name], value)
    encoded = canonical_json_bytes(value)
    require(wrapper.get("bytes_hex") == encoded.hex(), "CANONICAL_BYTES_DRIFT", schema_name)
    domain = f"deltareduce.010.{schema_name}.v1"
    expected = "sha256:" + hashlib.sha256(domain.encode() + b"\0" + encoded).hexdigest()
    require(wrapper.get("content_id") == expected, "CONTENT_ID_DRIFT", schema_name)


def _governance_quorum(value: dict[str, Any], code: str) -> None:
    f_b = value["f_b"]
    threshold = value["quorum_threshold"]
    signers = value["ordered_signers"]
    require(threshold == 2 * f_b + 1, code)
    require(len(signers) >= threshold and len(set(signers)) == len(signers), code)


def validate_chain(artifacts: dict[str, dict[str, Any]]) -> dict[str, object]:
    definition = artifacts["definition"]["value"]
    definition_id = artifacts["definition"]["content_id"]
    arms = [artifacts[key] for key in ("arm_reference", "arm_embedded", "arm_sidecar")]
    require(definition["arm_ids"] == [arm["content_id"] for arm in arms], "ARM_SET_MISMATCH")
    require(
        definition["network_profile_ids"] == [artifacts["network_profile"]["content_id"]],
        "NETWORK_PROFILE_MISMATCH",
    )
    require(
        definition["fault_profile_ids"] == [artifacts["fault_profile"]["content_id"]],
        "FAULT_PROFILE_MISMATCH",
    )
    require(definition["source_commit"] not in {"main", "master", "latest"}, "SOURCE_NOT_PINNED")
    profiles = {arm["value"]["deployment_profile"] for arm in arms}
    require({"EMBEDDED_FFM", "ISOLATED_SIDECAR"} <= profiles, "ISOLATION_PROFILE_MISSING")
    metrics = definition["metric_definitions"]
    require(metrics and all("pass_threshold" in metric for metric in metrics), "THRESHOLD_MISSING")

    attestation = artifacts["definition_attestation"]["value"]
    require(
        attestation["benchmark_definition_id"] == definition_id,
        "DEFINITION_ATTESTATION_MISMATCH",
    )
    _governance_quorum(attestation, "DEFINITION_ATTESTATION_QUORUM_INVALID")

    run_keys = ("run_reference", "run_embedded", "run_sidecar")
    run_ids = [artifacts[key]["content_id"] for key in run_keys]
    for key, arm in zip(run_keys, arms, strict=True):
        run = artifacts[key]["value"]
        require(run["benchmark_definition_id"] == definition_id, "RUN_DEFINITION_MISMATCH")
        require(run["arm_id"] == arm["content_id"], "RUN_ARM_MISMATCH")
        require(run["processed_tokens"] == definition["B"], "RUN_TOKEN_MISMATCH")
        require(run["ticket_plan_id"] == definition["ticket_plan_id"], "RUN_TICKET_MISMATCH")
        require(run["zero_copy_hits"] <= run["zero_copy_eligible"], "RUN_ZERO_COPY_INVALID")
        require(run["useful_compute_us"] <= run["total_us"], "RUN_TIME_ACCOUNTING_INVALID")
        require(
            sum(item["microseconds"] for item in run["phase_latencies"]) <= run["total_us"],
            "RUN_PHASE_ACCOUNTING_INVALID",
        )
        required_outputs = {
            run["protocol_hash"],
            run["checkpoint_id"],
            run["model_artifact_id"],
            *run["certificate_ids"],
            *run["evaluation_artifact_ids"],
        }
        require(required_outputs <= set(run["output_ids"]), "RUN_OUTPUT_GRAPH_INCOMPLETE")
        require(run["evaluation_artifact_ids"], "RUN_EVALUATION_EVIDENCE_MISSING")
        if arm["value"]["kind"] != "SCIENTIFIC_REFERENCE":
            require(len(run["certificate_ids"]) >= 6, "RUN_CERTIFICATE_EVIDENCE_MISSING")

    quality = artifacts["quality"]["value"]
    require(quality["benchmark_definition_id"] == definition_id, "QUALITY_DEFINITION_MISMATCH")
    require(quality["run_ids"] == run_ids, "QUALITY_RUN_SET_MISMATCH")
    require(
        quality["status"] != "PASS" or (quality["token_match"] and quality["domain_match"]),
        "QUALITY_MATCH_INVALID",
    )
    safety = artifacts["safety"]["value"]
    required_attacks = {
        "ac-mutation",
        "certificate-downgrade",
        "conflicting-apply",
        "conflicting-config",
        "frankenstein-shard",
        "incomplete-root",
        "seed-before-isc",
        "unsafe-accumulator",
        "vote-equivocation",
    }
    attacks = {item["attack_id"]: item for item in safety["attacks"]}
    require(set(attacks) == required_attacks, "ATTACK_CORPUS_INCOMPLETE")
    require(
        all(item["rejected"] and item["current_unchanged"] for item in attacks.values()),
        "ATTACK_NOT_SAFELY_REJECTED",
    )
    require(safety["exact_hashes_match"], "PROTOCOL_EXACTNESS_FAILED")

    evidence_manifest = artifacts["evidence_manifest"]["value"]
    require(
        evidence_manifest["benchmark_definition_id"] == definition_id,
        "EVIDENCE_DEFINITION_MISMATCH",
    )
    require(evidence_manifest["complete"], "EVIDENCE_MANIFEST_INCOMPLETE")
    require(evidence_manifest["run_ids"] == run_ids, "EVIDENCE_RUN_SET_MISMATCH")
    expected_evidence_ids = {
        artifacts["formal"]["content_id"],
        artifacts["quality"]["content_id"],
        artifacts["safety"]["content_id"],
        artifacts["efficiency"]["content_id"],
        artifacts["resilience"]["content_id"],
    }
    require(
        {item["content_id"] for item in evidence_manifest["evidence"]} == expected_evidence_ids,
        "EVIDENCE_GRAPH_INCOMPLETE",
    )

    result = artifacts["result"]["value"]
    require(result["benchmark_definition_id"] == definition_id, "RESULT_DEFINITION_MISMATCH")
    require(
        result["evidence_manifest_id"] == artifacts["evidence_manifest"]["content_id"],
        "RESULT_EVIDENCE_MISMATCH",
    )
    require(result["run_ids"] == run_ids, "RESULT_RUN_SET_MISMATCH")
    failed = [
        gate["gate_id"]
        for gate in result["gate_table"]
        if gate["mandatory"] and gate["status"] != "PASS"
    ]
    if result["decision"] == "GO":
        require(not failed and not result["failed_or_missing"], "GO_WITH_FAILED_MANDATORY_GATE")
    qc = artifacts["result_qc"]["value"]
    require(qc["benchmark_result_id"] == artifacts["result"]["content_id"], "RESULT_QC_MISMATCH")
    require(qc["decision"] == result["decision"], "RESULT_QC_DECISION_MISMATCH")
    _governance_quorum(qc, "RESULT_QC_QUORUM_INVALID")
    return {
        "artifact_count": len(artifacts),
        "decision": result["decision"],
        "gate_count": len(result["gate_table"]),
        "run_count": len(run_ids),
        "status": "PASS",
    }


def negative_documents(artifacts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        (
            "missing-threshold",
            "definition",
            "MISSING",
            lambda value: value["metric_definitions"][0].pop("pass_threshold"),
        ),
        (
            "mutable-source",
            "definition",
            "PATTERN",
            lambda value: value.__setitem__("source_commit", "main"),
        ),
        (
            "definition-quorum",
            "definition_attestation",
            "DEFINITION_ATTESTATION_QUORUM_INVALID",
            lambda value: value.__setitem__("ordered_signers", ["reviewer-0", "reviewer-1"]),
        ),
        (
            "result-definition",
            "result",
            "RESULT_DEFINITION_MISMATCH",
            lambda value: value.__setitem__("benchmark_definition_id", hash_id("wrong-definition")),
        ),
        (
            "manual-go",
            "result",
            "GO_WITH_FAILED_MANDATORY_GATE",
            lambda value: value["gate_table"][0].__setitem__("status", "FAIL"),
        ),
        (
            "runtime-current",
            "result_qc",
            "CONST",
            lambda value: value.__setitem__("protocol_current_transition", True),
        ),
        (
            "token-mismatch",
            "quality",
            "QUALITY_MATCH_INVALID",
            lambda value: value.__setitem__("token_match", False),
        ),
        (
            "missing-evidence",
            "evidence_manifest",
            "EVIDENCE_MANIFEST_INCOMPLETE",
            lambda value: value.__setitem__("complete", False),
        ),
        ("adaptive-h", "definition", "EXTRA", lambda value: value.__setitem__("adaptive_H", True)),
        (
            "result-quorum",
            "result_qc",
            "RESULT_QC_QUORUM_INVALID",
            lambda value: value.__setitem__("ordered_signers", ["evaluator-0", "evaluator-1"]),
        ),
    ]
    cases: list[dict[str, Any]] = []
    for name, artifact_name, expected, mutate in specs:
        value = copy.deepcopy(artifacts[artifact_name]["value"])
        mutate(value)
        cases.append(
            {
                "artifact_name": artifact_name,
                "expected_reason": expected,
                "name": name,
                "schema_name": artifacts[artifact_name]["schema_name"],
                "value": value,
            }
        )
    return cases


def validate_negative(
    case: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    schemas: dict[str, Any],
) -> None:
    candidate = copy.deepcopy(artifacts)
    candidate[case["artifact_name"]] = identified(case["schema_name"], case["value"])
    try:
        for wrapper in candidate.values():
            validate_identified(wrapper, schemas)
        validate_chain(candidate)
    except (ContractError, SchemaValidationError) as error:
        require(case["expected_reason"] in str(error), "NEGATIVE_REASON_DRIFT", case["name"])
        return
    raise ContractError(f"NEGATIVE_ACCEPTED:{case['name']}")


def fixture_documents() -> dict[str, Any]:
    artifacts = fixture_artifacts()
    return {
        "invalid": {
            "cases": negative_documents(artifacts),
            "formal_semantics_id": FORMAL_ID,
            "schema_version": SCHEMA_VERSION,
            "semantic_completeness_claimed": False,
        },
        "synthetic": {
            "definition_id": artifacts["definition"]["content_id"],
            "expected_decision": "GO",
            "fixture_class": "SYNTHETIC_NOT_PRIMARY_EVIDENCE",
            "run_ids": [
                artifacts[key]["content_id"]
                for key in ("run_reference", "run_embedded", "run_sidecar")
            ],
        },
        "valid": {
            "artifacts": artifacts,
            "formal_semantics_id": FORMAL_ID,
            "schema_version": SCHEMA_VERSION,
            "semantic_completeness_claimed": False,
        },
    }


def schema_registry(schemas: dict[str, Any], fixtures: dict[str, Any]) -> dict[str, Any]:
    artifacts = []
    media_types = []
    for name, (schema_id, _) in SCHEMAS.items():
        path = f"schemas/010/{name}-v1.json"
        artifacts.append(
            {
                "id": schema_id,
                "path": path,
                "sha256": sha256_bytes(pretty_json_bytes(schemas[name])),
            }
        )
        media_types.append(
            {
                "id": f"MEDIA-{name.upper()}-010-V1",
                "schema_id": schema_id,
                "value": f"application/vnd.deltareduce.{name}+json;version=1",
            }
        )
    fixture_entries = [
        {
            "id": "BENCHMARK010-VALID-CONTRACT-V1",
            "path": "fixtures/010/valid/benchmark-contract-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["valid"])),
        },
        {
            "id": "BENCHMARK010-CROSS-LANGUAGE-GOLDEN-V1",
            "path": "fixtures/010/cross-language/golden-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["valid"])),
        },
        {
            "id": "BENCHMARK010-NEGATIVE-V1",
            "path": "fixtures/010/invalid/benchmark-negative-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["invalid"])),
        },
        {
            "id": "BENCHMARK010-SYNTHETIC-V1",
            "path": "fixtures/010/synthetic/tiny-benchmark-v1.json",
            "sha256": sha256_bytes(file_json_bytes(fixtures["synthetic"])),
        },
    ]
    return {
        "artifacts": artifacts,
        "fixtures": fixture_entries,
        "formal_semantics_id": FORMAL_ID,
        "media_types": media_types,
        "registry_version": "010.1.0",
        "schema_version": SCHEMA_VERSION,
        "semantic_completeness_claimed": False,
    }


def root_registry_bytes(registry: dict[str, Any]) -> bytes:
    path = ROOT / "delta-protocol/registry.json"
    root = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(root, dict), "ROOT_REGISTRY_INVALID")
    schema_ids = {entry["id"] for entry in registry["artifacts"]}
    root["extensions"] = [
        entry for entry in root["extensions"] if entry.get("id") != "REGISTRY-BENCHMARK-010"
    ]
    root["fixtures"] = [
        entry
        for entry in root["fixtures"]
        if not str(entry.get("id", "")).startswith("BENCHMARK010-")
    ]
    root["media_types"] = [
        entry for entry in root["media_types"] if entry.get("schema_id") not in schema_ids
    ]
    root["schemas"] = [entry for entry in root["schemas"] if entry.get("id") not in schema_ids]
    feature_registry = pretty_json_bytes(registry)
    root["extensions"].append(
        {
            "id": "REGISTRY-BENCHMARK-010",
            "path": "schemas/010/registry-v1.json",
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
    for wrapper in fixtures["valid"]["artifacts"].values():
        validate_identified(wrapper, schemas)
    validate_chain(fixtures["valid"]["artifacts"])
    for case in fixtures["invalid"]["cases"]:
        validate_negative(case, fixtures["valid"]["artifacts"], schemas)
    registry = schema_registry(schemas, fixtures)
    outputs = {
        ROOT / "delta-protocol/schemas/010" / f"{name}-v1.json": pretty_json_bytes(schema)
        for name, schema in schemas.items()
    }
    outputs[ROOT / "delta-protocol/schemas/010/registry-v1.json"] = pretty_json_bytes(registry)
    outputs[ROOT / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json"] = (
        file_json_bytes(fixtures["valid"])
    )
    outputs[ROOT / "delta-protocol/fixtures/010/cross-language/golden-v1.json"] = file_json_bytes(
        fixtures["valid"]
    )
    outputs[ROOT / "delta-protocol/fixtures/010/invalid/benchmark-negative-v1.json"] = (
        file_json_bytes(fixtures["invalid"])
    )
    outputs[ROOT / "delta-protocol/fixtures/010/synthetic/tiny-benchmark-v1.json"] = (
        file_json_bytes(fixtures["synthetic"])
    )
    outputs[ROOT / "delta-protocol/registry.json"] = root_registry_bytes(registry)
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
                    "invalid_case_count": len(fixture_documents()["invalid"]["cases"]),
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
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(
            canonical_json_bytes(
                {"error_code": str(error), "formal_semantics_id": FORMAL_ID, "status": "FAIL"}
            ).decode()
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
