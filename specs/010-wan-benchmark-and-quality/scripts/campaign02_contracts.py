"""Generate Campaign 02 remediation schemas and registry entries."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SCHEMA_ROOT: Final = ROOT / "delta-protocol/schemas/010/campaign-02"
REGISTRY_PATH: Final = SCHEMA_ROOT / "registry-v1.json"

SCHEMAS: Final = {
    "benchmark-definition-v2": (
        "SCHEMA-CAMPAIGN02-BENCHMARK-DEFINITION-010-V2",
        "BENCHMARK_DEFINITION",
        "2.0.0",
    ),
    "benchmark-definition-v3": (
        "SCHEMA-CAMPAIGN02-BENCHMARK-DEFINITION-010-V3",
        "BENCHMARK_DEFINITION",
        "3.0.0",
    ),
    "benchmark-definition-v4": (
        "SCHEMA-CAMPAIGN02-BENCHMARK-DEFINITION-010-V4",
        "BENCHMARK_DEFINITION",
        "4.0.0",
    ),
    "benchmark-definition-v5": (
        "SCHEMA-CAMPAIGN02-BENCHMARK-DEFINITION-010-V5",
        "BENCHMARK_DEFINITION",
        "5.0.0",
    ),
    "benchmark-review-validator-set-v1": (
        "SCHEMA-CAMPAIGN02-BENCHMARK-REVIEW-VALIDATOR-SET-010-V1",
        "BENCHMARK_REVIEW_VALIDATOR_SET",
        "1.0.0",
    ),
    "benchmark-definition-vote-v1": (
        "SCHEMA-CAMPAIGN02-BENCHMARK-DEFINITION-VOTE-010-V1",
        "BENCHMARK_DEFINITION_VOTE",
        "1.0.0",
    ),
    "benchmark-definition-attestation-v2": (
        "SCHEMA-CAMPAIGN02-BENCHMARK-DEFINITION-ATTESTATION-010-V2",
        "BENCHMARK_DEFINITION_ATTESTATION",
        "2.0.0",
    ),
    "domain-manifest-v1": (
        "SCHEMA-CAMPAIGN02-DOMAIN-MANIFEST-010-V1",
        "CAMPAIGN_DOMAIN_MANIFEST",
        "1.0.0",
    ),
    "ticket-plan-v1": (
        "SCHEMA-CAMPAIGN02-TICKET-PLAN-010-V1",
        "CAMPAIGN_TICKET_PLAN",
        "1.0.0",
    ),
    "qualified-runtime-lineage-v1": (
        "SCHEMA-CAMPAIGN02-QUALIFIED-RUNTIME-LINEAGE-010-V1",
        "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
        "1.0.0",
    ),
    "qualified-runtime-lineage-v2": (
        "SCHEMA-CAMPAIGN02-QUALIFIED-RUNTIME-LINEAGE-010-V2",
        "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
        "2.0.0",
    ),
    "qualified-runtime-lineage-v3": (
        "SCHEMA-CAMPAIGN02-QUALIFIED-RUNTIME-LINEAGE-010-V3",
        "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
        "3.0.0",
    ),
    "qualified-runtime-lineage-v4": (
        "SCHEMA-CAMPAIGN02-QUALIFIED-RUNTIME-LINEAGE-010-V4",
        "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
        "4.0.0",
    ),
    "qualified-runtime-lineage-v5": (
        "SCHEMA-CAMPAIGN02-QUALIFIED-RUNTIME-LINEAGE-010-V5",
        "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
        "5.0.0",
    ),
    "stage-execution-identities-v2": (
        "SCHEMA-CAMPAIGN02-STAGE-EXECUTION-IDENTITIES-010-V2",
        "CAMPAIGN02_STAGE_EXECUTION_IDENTITIES",
        "2.0.0",
    ),
    "stage-execution-identities-v3": (
        "SCHEMA-CAMPAIGN02-STAGE-EXECUTION-IDENTITIES-010-V3",
        "CAMPAIGN02_STAGE_EXECUTION_IDENTITIES",
        "3.0.0",
    ),
    "stage-execution-identities-v4": (
        "SCHEMA-CAMPAIGN02-STAGE-EXECUTION-IDENTITIES-010-V4",
        "CAMPAIGN02_STAGE_EXECUTION_IDENTITIES",
        "4.0.0",
    ),
    "workload-v2": ("SCHEMA-CAMPAIGN02-WORKLOAD-010-V2", "CAMPAIGN_WORKLOAD", "2.0.0"),
    "execution-plan-v2": (
        "SCHEMA-CAMPAIGN02-EXECUTION-PLAN-010-V2",
        "PRIMARY_EXECUTION_PLAN",
        "2.0.0",
    ),
    "execution-plan-v3": (
        "SCHEMA-CAMPAIGN02-EXECUTION-PLAN-010-V3",
        "PRIMARY_EXECUTION_PLAN",
        "3.0.0",
    ),
    "execution-plan-v4": (
        "SCHEMA-CAMPAIGN02-EXECUTION-PLAN-010-V4",
        "PRIMARY_EXECUTION_PLAN",
        "4.0.0",
    ),
    "execution-plan-v5": (
        "SCHEMA-CAMPAIGN02-EXECUTION-PLAN-010-V5",
        "PRIMARY_EXECUTION_PLAN",
        "5.0.0",
    ),
    "execution-plan-v6": (
        "SCHEMA-CAMPAIGN02-EXECUTION-PLAN-010-V6",
        "PRIMARY_EXECUTION_PLAN",
        "6.0.0",
    ),
    "plan-catalog-v1": (
        "SCHEMA-CAMPAIGN02-PLAN-CATALOG-010-V1",
        "CAMPAIGN02_PLAN_CATALOG",
        "1.0.0",
    ),
    "plan-catalog-v2": (
        "SCHEMA-CAMPAIGN02-PLAN-CATALOG-010-V2",
        "CAMPAIGN02_PLAN_CATALOG",
        "2.0.0",
    ),
    "plan-catalog-v3": (
        "SCHEMA-CAMPAIGN02-PLAN-CATALOG-010-V3",
        "CAMPAIGN02_PLAN_CATALOG",
        "3.0.0",
    ),
    "stage-execution-authorization-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-EXECUTION-AUTHORIZATION-010-V1",
        "BENCHMARK_STAGE_EXECUTION_AUTHORIZATION",
        "1.0.0",
    ),
    "stage-execution-authorization-v2": (
        "SCHEMA-CAMPAIGN02-STAGE-EXECUTION-AUTHORIZATION-010-V2",
        "BENCHMARK_STAGE_EXECUTION_AUTHORIZATION",
        "2.0.0",
    ),
    "stage-authorization-validator-set-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-AUTHORIZATION-VALIDATOR-SET-010-V1",
        "BENCHMARK_STAGE_AUTHORIZATION_VALIDATOR_SET",
        "1.0.0",
    ),
    "stage-authorization-vote-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-AUTHORIZATION-VOTE-010-V1",
        "BENCHMARK_STAGE_AUTHORIZATION_VOTE",
        "1.0.0",
    ),
    "stage-authorization-attestation-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-AUTHORIZATION-ATTESTATION-010-V1",
        "BENCHMARK_STAGE_AUTHORIZATION_ATTESTATION",
        "1.0.0",
    ),
    "stage-gate-receipt-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-GATE-RECEIPT-010-V1",
        "BENCHMARK_STAGE_GATE_RECEIPT",
        "1.0.0",
    ),
    "stage-gate-receipt-v2": (
        "SCHEMA-CAMPAIGN02-STAGE-GATE-RECEIPT-010-V2",
        "BENCHMARK_STAGE_GATE_RECEIPT",
        "2.0.0",
    ),
    "stage-gate-receipt-v3": (
        "SCHEMA-CAMPAIGN02-STAGE-GATE-RECEIPT-010-V3",
        "BENCHMARK_STAGE_GATE_RECEIPT",
        "3.0.0",
    ),
    "stage-plan-evidence-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-PLAN-EVIDENCE-010-V1",
        "CAMPAIGN02_STAGE_PLAN_EVIDENCE",
        "1.0.0",
    ),
    "stage-plan-evidence-v2": (
        "SCHEMA-CAMPAIGN02-STAGE-PLAN-EVIDENCE-010-V2",
        "CAMPAIGN02_STAGE_PLAN_EVIDENCE",
        "2.0.0",
    ),
    "stage-gate-result-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-GATE-RESULT-010-V1",
        "CAMPAIGN02_STAGE_GATE_RESULT",
        "1.0.0",
    ),
    "stage-gate-result-v2": (
        "SCHEMA-CAMPAIGN02-STAGE-GATE-RESULT-010-V2",
        "CAMPAIGN02_STAGE_GATE_RESULT",
        "2.0.0",
    ),
    "network-fault-plan-evidence-v1": (
        "SCHEMA-CAMPAIGN02-NETWORK-FAULT-PLAN-EVIDENCE-010-V1",
        "CAMPAIGN02_NETWORK_FAULT_PLAN_EVIDENCE",
        "1.0.0",
    ),
    "network-fault-plan-evidence-v2": (
        "SCHEMA-CAMPAIGN02-NETWORK-FAULT-PLAN-EVIDENCE-010-V2",
        "CAMPAIGN02_NETWORK_FAULT_PLAN_EVIDENCE",
        "2.0.0",
    ),
    "network-fault-plan-evidence-v3": (
        "SCHEMA-CAMPAIGN02-NETWORK-FAULT-PLAN-EVIDENCE-010-V3",
        "CAMPAIGN02_NETWORK_FAULT_PLAN_EVIDENCE",
        "3.0.0",
    ),
    "network-fault-plan-evidence-v4": (
        "SCHEMA-CAMPAIGN02-NETWORK-FAULT-PLAN-EVIDENCE-010-V4",
        "CAMPAIGN02_NETWORK_FAULT_PLAN_EVIDENCE",
        "4.0.0",
    ),
    "stage-c-candidate-run-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-C-CANDIDATE-RUN-010-V1",
        "CAMPAIGN02_STAGE_C_NON_PRIMARY_CANDIDATE_RUN",
        "1.0.0",
    ),
    "stage-c-candidate-summary-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-C-CANDIDATE-SUMMARY-010-V1",
        "CAMPAIGN02_STAGE_C_NON_PRIMARY_CANDIDATE_SUMMARY",
        "1.0.0",
    ),
    "stage-a-semantic-evidence-v1": (
        "SCHEMA-CAMPAIGN02-STAGE-A-SEMANTIC-EVIDENCE-010-V1",
        "CAMPAIGN02_STAGE_A_SEMANTIC_EVIDENCE_SUMMARY",
        "1.0.0",
    ),
    "stage-workflow-gate-qc-v2": (
        "SCHEMA-CAMPAIGN02-STAGE-WORKFLOW-GATE-QC-010-V2",
        "CAMPAIGN02_STAGE_WORKFLOW_GATE_QC",
        "2.0.0",
    ),
    "stage-workflow-gate-qc-v3": (
        "SCHEMA-CAMPAIGN02-STAGE-WORKFLOW-GATE-QC-010-V3",
        "CAMPAIGN02_STAGE_WORKFLOW_GATE_QC",
        "3.0.0",
    ),
    "stage-workflow-gate-qc-v4": (
        "SCHEMA-CAMPAIGN02-STAGE-WORKFLOW-GATE-QC-010-V4",
        "CAMPAIGN02_STAGE_WORKFLOW_GATE_QC",
        "4.0.0",
    ),
    "workflow-bootstrap-mapping-v1": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-BOOTSTRAP-MAPPING-010-V1",
        "CAMPAIGN02_WORKFLOW_BOOTSTRAP_MAPPING",
        "1.0.0",
    ),
    "workflow-bootstrap-validator-set-v1": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-BOOTSTRAP-VALIDATOR-SET-010-V1",
        "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET",
        "1.0.0",
    ),
    "workflow-bootstrap-signature-v1": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-BOOTSTRAP-SIGNATURE-010-V1",
        "CAMPAIGN02_WORKFLOW_BOOTSTRAP_SIGNATURE",
        "1.0.0",
    ),
    "workflow-registration-receipt-v1": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-REGISTRATION-RECEIPT-010-V1",
        "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT",
        "1.0.0",
    ),
    "workflow-registration-api-evidence-v1": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-REGISTRATION-API-EVIDENCE-010-V1",
        "CAMPAIGN02_WORKFLOW_REGISTRATION_API_EVIDENCE",
        "1.0.0",
    ),
    "workflow-registration-signature-v1": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-REGISTRATION-SIGNATURE-010-V1",
        "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE",
        "1.0.0",
    ),
    "workflow-registration-receipt-v2": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-REGISTRATION-RECEIPT-010-V2",
        "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT",
        "2.0.0",
    ),
    "workflow-registration-receipt-v3": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-REGISTRATION-RECEIPT-010-V3",
        "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT",
        "3.0.0",
    ),
    "workflow-registration-signature-v2": (
        "SCHEMA-CAMPAIGN02-WORKFLOW-REGISTRATION-SIGNATURE-010-V2",
        "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE",
        "2.0.0",
    ),
    "evaluator-profile-v1": (
        "SCHEMA-CAMPAIGN02-EVALUATOR-PROFILE-010-V1",
        "EVALUATOR_PROFILE",
        "1.0.0",
    ),
    "measured-evaluation-v1": (
        "SCHEMA-CAMPAIGN02-MEASURED-EVALUATION-010-V1",
        "MEASURED_EVALUATION",
        "1.0.0",
    ),
    "component-identity-v1": (
        "SCHEMA-CAMPAIGN02-COMPONENT-IDENTITY-010-V1",
        "PRIMARY_COMPONENT_IDENTITY",
        "1.0.0",
    ),
    "observation-v2": (
        "SCHEMA-CAMPAIGN02-OBSERVATION-010-V2",
        "PRIMARY_RUN_OBSERVATION",
        "2.0.0",
    ),
    "observation-v3": (
        "SCHEMA-CAMPAIGN02-OBSERVATION-010-V3",
        "PRIMARY_RUN_OBSERVATION",
        "3.0.0",
    ),
    "observation-receipt-v1": (
        "SCHEMA-CAMPAIGN02-OBSERVATION-RECEIPT-010-V1",
        "PRIMARY_OBSERVATION_RECEIPT",
        "1.0.0",
    ),
    "gpu-environment-lock-v1": (
        "SCHEMA-CAMPAIGN02-GPU-ENVIRONMENT-LOCK-010-V1",
        "GPU_ENVIRONMENT_LOCK",
        "1.0.0",
    ),
    "native-chain-admission-bundle-v1": (
        "SCHEMA-CAMPAIGN02-NATIVE-CHAIN-ADMISSION-BUNDLE-010-V1",
        "CAMPAIGN02_NATIVE_CHAIN_ADMISSION_BUNDLE",
        "1.0.0",
    ),
    "native-chain-admission-receipt-v1": (
        "SCHEMA-CAMPAIGN02-NATIVE-CHAIN-ADMISSION-RECEIPT-010-V1",
        "CAMPAIGN02_NATIVE_CHAIN_ADMISSION_RECEIPT",
        "1.0.0",
    ),
}


class Campaign02SchemaError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def pretty(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def content_id() -> dict[str, object]:
    return {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}


def commit_id() -> dict[str, object]:
    return {"pattern": "^[0-9a-f]{40}$", "type": "string"}


def uint(minimum: int = 0) -> dict[str, object]:
    return {"maximum": 9_007_199_254_740_991, "minimum": minimum, "type": "integer"}


def text() -> dict[str, object]:
    return {"minLength": 1, "type": "string"}


def array(item: dict[str, object], minimum: int = 1, unique: bool = False) -> dict[str, object]:
    value: dict[str, object] = {"items": item, "minItems": minimum, "type": "array"}
    if unique:
        value["uniqueItems"] = True
    return value


def strict(properties: dict[str, object]) -> dict[str, object]:
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": sorted(properties),
        "type": "object",
    }


def schema(
    name: str,
    properties: dict[str, object],
    *,
    result_class_union: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    _, type_name, version = SCHEMAS[name]
    all_properties = {
        "formal_semantics_id": {"const": FORMAL_ID},
        "schema_version": {"const": version},
        "type_name": {"const": type_name},
        **properties,
    }
    document: dict[str, object] = {
        "$id": f"urn:deltareduce:schema:010:campaign-02:{name}",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **strict(all_properties),
        "title": f"DeltaReduce Feature 010 Campaign 02 {name}",
    }
    if result_class_union is not None:
        document["oneOf"] = result_class_union
    return document


def schema_documents() -> dict[str, dict[str, object]]:
    domain_count = strict({"domain_id": text(), "ticket_count": uint(1)})
    ticket = strict(
        {
            "domain_id": text(),
            "optimizer_steps": uint(1),
            "ordinal": uint(),
            "ticket_id": content_id(),
            "tokens_per_optimizer_step": uint(1),
            "tokens_per_ticket": uint(1),
        }
    )
    metric = strict({"metric_id": text(), "unit": text(), "value": uint()})
    executable = strict({"content_id": content_id(), "path": text()})
    ticket_result = strict(
        {
            "availability_certificate_id": content_id(),
            "commitment_id": content_id(),
            "contribution_id": content_id(),
            "domain_id": text(),
            "local_artifact_ids": array(content_id(), unique=True),
            "optimizer_steps": uint(1),
            "processed_tokens": uint(1),
            "ticket_id": content_id(),
        }
    )
    shard_key = strict({"domain_id": text(), "shard_id": text()})
    certified_policy = strict(
        {
            "accumulator_proof_id": content_id(),
            "apply_arithmetic_profile_id": content_id(),
            "arithmetic_profile_id": content_id(),
            "height": uint(1),
            "parameter_schema_id": content_id(),
            "quorum_threshold": uint(1),
            "required_shards": array(shard_key, unique=True),
            "round_config_id": content_id(),
            "round_id": text(),
            "validator_epoch_id": content_id(),
            "validator_ids": array(text(), unique=True),
            "view": uint(),
        }
    )
    reference_result = strict(
        {
            "final_checkpoint_id": content_id(),
            "ordered_data_exposure_ids": array(content_id(), unique=True),
            "ordered_ticket_ids": array(content_id(), unique=True),
            "parent_checkpoint_id": content_id(),
            "processed_tokens": uint(1),
            "result_class": {"const": "REFERENCE"},
            "round_id": text(),
            "terminal_outcome": {"const": "COMPLETED"},
            "training_artifact_ids": array(content_id(), unique=True),
        }
    )
    certified_result = strict(
        {
            "aggregate_root_qc_id": content_id(),
            "aggregation_plan_certificate_id": content_id(),
            "apply_qc_id": content_id(),
            "checkpoint_wal_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
            "effect_set_id": content_id(),
            "eligibility_certificate_id": content_id(),
            "final_checkpoint_id": content_id(),
            "input_set_certificate_id": content_id(),
            "native_chain_admission_receipt_id": content_id(),
            "native_chain_verifier_id": content_id(),
            "ordered_contribution_ids": array(content_id(), unique=True),
            "ordered_ticket_ids": array(content_id(), unique=True),
            "parameter_shard_qc_ids": array(content_id(), unique=True),
            "parent_checkpoint_id": content_id(),
            "result_class": {"const": "CERTIFIED_DELTAREDUCE"},
            "round_id": text(),
            "runtime_receipt_id": content_id(),
            "runtime_state_id": content_id(),
            "runtime_wal_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
            "seed_transcript_id": content_id(),
            "terminal_outcome": {"const": "APPLIED"},
        }
    )
    lock_ref = strict({"path": text(), "sha256": content_id(), "target": text()})
    base_definition = json.loads(
        (ROOT / "delta-protocol/schemas/010/benchmark-definition-v1.json").read_bytes()
    )
    base_properties = dict(base_definition["properties"])
    for field in ("formal_semantics_id", "schema_version", "type_name"):
        del base_properties[field]
    definition_v2_properties = {
        **base_properties,
        "campaign_id": {"const": "campaign-02"},
        "qualified_runtime_lineage_id": content_id(),
        "workload_contract_id": content_id(),
    }
    definition_v3_properties = {
        **definition_v2_properties,
        "stage_execution_identities_id": content_id(),
    }
    definition_v4_properties = dict(definition_v3_properties)
    definition_v5_properties = {
        **definition_v4_properties,
        "bootstrap_mapping_id": content_id(),
    }
    domain = strict(
        {
            "dataset_id": content_id(),
            "denominator": uint(1),
            "domain_id": text(),
            "numerator": uint(1),
            "ticket_count": uint(1),
        }
    )
    timestamp = {"pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+Z$", "type": "string"}
    validator = strict(
        {
            "controller_id": text(),
            "key_custody_statement_id": content_id(),
            "public_key": {"pattern": "^[A-Za-z0-9+/]{43}=$", "type": "string"},
            "public_key_id": content_id(),
            "signature_algorithm": {"const": "ED25519"},
            "valid_from": timestamp,
            "valid_until": {"oneOf": [{"type": "null"}, timestamp]},
            "validator_id": text(),
        }
    )
    policy_binding = strict(
        {
            "arm_id": content_id(),
            "arm_name": text(),
            "policy": certified_policy,
            "repetition": uint(1),
            "seed": uint(),
        }
    )
    stages = [
        "STAGE_A_EXACTNESS",
        "STAGE_B_SCIENTIFIC",
        "STAGE_C_EMULATED_WAN",
    ]
    policy_binding_v2 = strict(
        {
            "arm_id": content_id(),
            "arm_name": text(),
            "gate_stage": {"enum": stages},
            "policy": certified_policy,
            "repetition": uint(1),
            "seed": uint(),
        }
    )
    identity_wrapper = strict(
        {
            "content_id": content_id(),
            "identity_domain": text(),
            "value": {"type": "object"},
        }
    )
    observation_properties = {
        "arm_id": content_id(),
        "benchmark_definition_id": content_id(),
        "campaign_id": {"const": "campaign-02"},
        "dataset_ids": array(content_id(), unique=True),
        "definition_attestation_id": content_id(),
        "environment_id": content_id(),
        "evaluation_ids": array(content_id(), unique=True),
        "evaluation_implementation_ids": array(content_id(), unique=True),
        "evaluation_runner_id": content_id(),
        "execution_authorization_id": content_id(),
        "execution_class": {"enum": ["NON_PRIMARY_SMOKE", "PRIMARY_MEASURED"]},
        "execution_plan_id": content_id(),
        "hardware_id": content_id(),
        "image_id": content_id(),
        "model_artifact_id": content_id(),
        "processed_tokens": uint(1),
        "raw_artifact_ids": array(content_id(), unique=True),
        "repetition": uint(1),
        "result_class": {"enum": ["REFERENCE", "CERTIFIED_DELTAREDUCE"]},
        "run_result": {"oneOf": [reference_result, certified_result]},
        "runner_id": content_id(),
        "seed": uint(),
        "source_class": {"enum": ["MEASURED_HARDWARE", "NON_PRIMARY_SMOKE"]},
        "source_commit": commit_id(),
        "source_tree": commit_id(),
        "ticket_results": array(ticket_result),
        "tokenizer_id": content_id(),
        "workload_id": content_id(),
        "writer_id": content_id(),
    }
    observation_result_union = [
        {
            "properties": {
                "result_class": {"const": "REFERENCE"},
                "run_result": reference_result,
            }
        },
        {
            "properties": {
                "result_class": {"const": "CERTIFIED_DELTAREDUCE"},
                "run_result": certified_result,
            }
        },
    ]
    observation_v3_properties = {
        **observation_properties,
        "execution_class": {"const": "PRIMARY_MEASURED"},
        "source_class": {"const": "MEASURED_HARDWARE"},
        "stage_authorization_attestation_id": content_id(),
        "stage_authorization_id": content_id(),
        "stage_authorization_proof_artifact_ids": array(content_id(), unique=True),
        "stage_authorization_quorum_threshold": uint(1),
        "stage_authorization_signature_set_root": content_id(),
        "stage_authorization_validator_set_id": content_id(),
        "stage_authorization_vote_ids": array(content_id(), unique=True),
    }
    documents = {
        "benchmark-definition-v2": schema("benchmark-definition-v2", definition_v2_properties),
        "benchmark-definition-v3": schema("benchmark-definition-v3", definition_v3_properties),
        "benchmark-definition-v4": schema("benchmark-definition-v4", definition_v4_properties),
        "benchmark-definition-v5": schema("benchmark-definition-v5", definition_v5_properties),
        "benchmark-review-validator-set-v1": schema(
            "benchmark-review-validator-set-v1",
            {
                "campaign_id": {"const": "campaign-02"},
                "f_b": uint(),
                "purpose": {"const": "BENCHMARK_DEFINITION_REVIEW"},
                "validators": array(validator, unique=True),
            },
        ),
        "benchmark-definition-vote-v1": schema(
            "benchmark-definition-vote-v1",
            {
                "benchmark_definition_id": content_id(),
                "public_key_id": content_id(),
                "purpose": {"const": "BENCHMARK_DEFINITION_REVIEW"},
                "signature": {"pattern": "^[A-Za-z0-9+/]{86}==$", "type": "string"},
                "signature_algorithm": {"const": "ED25519"},
                "signed_message_sha256": content_id(),
                "signer_id": text(),
                "submitted_at": timestamp,
                "validator_set_id": content_id(),
            },
        ),
        "benchmark-definition-attestation-v2": schema(
            "benchmark-definition-attestation-v2",
            {
                "benchmark_definition_id": content_id(),
                "f_b": uint(),
                "governance_only": {"const": True},
                "independent_approval": {"const": True},
                "ordered_signers": array(text(), unique=True),
                "ordered_vote_ids": array(content_id(), unique=True),
                "quorum_threshold": uint(1),
                "signature_set_root": content_id(),
                "validator_set_id": content_id(),
                "verified_at": timestamp,
            },
        ),
        "domain-manifest-v1": schema(
            "domain-manifest-v1",
            {"campaign_id": {"const": "campaign-02"}, "domains": array(domain, unique=True)},
        ),
        "ticket-plan-v1": schema(
            "ticket-plan-v1",
            {
                "campaign_id": {"const": "campaign-02"},
                "domain_manifest_id": content_id(),
                "tickets": array(ticket, unique=True),
                "workload_contract_id": content_id(),
            },
        ),
        "qualified-runtime-lineage-v1": schema(
            "qualified-runtime-lineage-v1",
            {
                "campaign_id": {"const": "campaign-02"},
                "certified_plan_bindings": array(policy_binding, unique=True),
                "dataset_ids": array(content_id(), unique=True),
                "environment_id": content_id(),
                "evaluation_implementation_ids": array(content_id(), unique=True),
                "evaluation_profile_ids": array(content_id(), unique=True),
                "evaluation_runner_id": content_id(),
                "hardware_id": content_id(),
                "image_id": content_id(),
                "model_id": content_id(),
                "parent_checkpoint_id": content_id(),
                "runner_id": content_id(),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "tokenizer_id": content_id(),
                "writer_id": content_id(),
            },
        ),
        "qualified-runtime-lineage-v2": schema(
            "qualified-runtime-lineage-v2",
            {
                "campaign_id": {"const": "campaign-02"},
                "certified_plan_bindings": {
                    "items": policy_binding_v2,
                    "maxItems": 36,
                    "minItems": 36,
                    "type": "array",
                    "uniqueItems": True,
                },
                "dataset_ids": array(content_id(), unique=True),
                "environment_id": content_id(),
                "evaluation_implementation_ids": array(content_id(), unique=True),
                "evaluation_profile_ids": array(content_id(), unique=True),
                "evaluation_runner_id": content_id(),
                "hardware_id": content_id(),
                "image_id": content_id(),
                "model_id": content_id(),
                "parent_checkpoint_id": content_id(),
                "runner_id": content_id(),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "stage_execution_model": {"const": "INDEPENDENT_BFT_RUNS"},
                "tokenizer_id": content_id(),
                "writer_id": content_id(),
            },
        ),
        "qualified-runtime-lineage-v3": schema(
            "qualified-runtime-lineage-v3",
            {
                "campaign_id": {"const": "campaign-02"},
                "certified_plan_bindings": {
                    "items": policy_binding_v2,
                    "maxItems": 36,
                    "minItems": 36,
                    "type": "array",
                    "uniqueItems": True,
                },
                "dataset_ids": array(content_id(), unique=True),
                "environment_id": content_id(),
                "evaluation_implementation_ids": array(content_id(), unique=True),
                "evaluation_profile_ids": array(content_id(), unique=True),
                "evaluation_runner_id": content_id(),
                "exactness_runner_id": content_id(),
                "hardware_id": content_id(),
                "image_id": content_id(),
                "model_id": content_id(),
                "network_fault_runner_id": content_id(),
                "parent_checkpoint_id": content_id(),
                "scientific_runner_id": content_id(),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "stage_execution_identities_id": content_id(),
                "stage_execution_model": {"const": "INDEPENDENT_BFT_RUNS"},
                "tokenizer_id": content_id(),
                "writer_id": content_id(),
            },
        ),
        "qualified-runtime-lineage-v4": schema(
            "qualified-runtime-lineage-v4",
            {
                "campaign_id": {"const": "campaign-02"},
                "certified_plan_bindings": {
                    "items": policy_binding_v2,
                    "maxItems": 36,
                    "minItems": 36,
                    "type": "array",
                    "uniqueItems": True,
                },
                "dataset_ids": array(content_id(), unique=True),
                "environment_id": content_id(),
                "evaluation_implementation_ids": array(content_id(), unique=True),
                "evaluation_profile_ids": array(content_id(), unique=True),
                "evaluation_runner_id": content_id(),
                "exactness_runner_id": content_id(),
                "hardware_id": content_id(),
                "image_id": content_id(),
                "model_id": content_id(),
                "network_fault_runner_id": content_id(),
                "parent_checkpoint_id": content_id(),
                "scientific_runner_id": content_id(),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "stage_execution_identities_id": content_id(),
                "stage_execution_model": {"const": "INDEPENDENT_BFT_RUNS"},
                "tokenizer_id": content_id(),
                "writer_id": content_id(),
            },
        ),
        "qualified-runtime-lineage-v5": schema(
            "qualified-runtime-lineage-v5",
            {
                "campaign_id": {"const": "campaign-02"},
                "certified_plan_bindings": {
                    "items": policy_binding_v2,
                    "maxItems": 36,
                    "minItems": 36,
                    "type": "array",
                    "uniqueItems": True,
                },
                "dataset_ids": array(content_id(), unique=True),
                "environment_id": content_id(),
                "evaluation_implementation_ids": array(content_id(), unique=True),
                "evaluation_profile_ids": array(content_id(), unique=True),
                "evaluation_runner_id": content_id(),
                "exactness_runner_id": content_id(),
                "hardware_id": content_id(),
                "image_id": content_id(),
                "java_executable_id": content_id(),
                "model_id": content_id(),
                "native_executable_id": content_id(),
                "network_fault_runner_id": content_id(),
                "netty_artifact_ids": array(content_id(), unique=True),
                "parent_checkpoint_id": content_id(),
                "scientific_runner_id": content_id(),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "stage_execution_identities_id": content_id(),
                "stage_execution_model": {"const": "INDEPENDENT_BFT_RUNS"},
                "tokenizer_id": content_id(),
                "transport_harness_id": content_id(),
                "writer_id": content_id(),
            },
        ),
        "stage-execution-identities-v2": schema(
            "stage-execution-identities-v2",
            {
                "campaign_id": {"const": "campaign-02"},
                "execution_authorized": {"const": False},
                "identities": strict(
                    {
                        name: identity_wrapper
                        for name in (
                            "evaluation_runner",
                            "exactness_runner",
                            "multi_role_runner",
                            "native_feature008_verifier",
                            "network_fault_runner",
                            "observation_writer",
                            "scientific_runner",
                            "signed_stage_authorization_verifier",
                            "stage_gate_analyzer",
                            "typed_gate_receipt_verifier",
                        )
                    }
                ),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
            },
        ),
        "stage-execution-identities-v3": schema(
            "stage-execution-identities-v3",
            {
                "campaign_id": {"const": "campaign-02"},
                "execution_authorized": {"const": False},
                "identities": strict(
                    {
                        name: identity_wrapper
                        for name in (
                            "evaluation_runner",
                            "exactness_runner",
                            "multi_role_runner",
                            "native_feature008_verifier",
                            "network_fault_runner",
                            "observation_writer",
                            "scientific_runner",
                            "signed_stage_authorization_verifier",
                            "stage_gate_analyzer",
                            "typed_gate_receipt_verifier",
                        )
                    }
                ),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
            },
        ),
        "stage-execution-identities-v4": schema(
            "stage-execution-identities-v4",
            {
                "campaign_id": {"const": "campaign-02"},
                "execution_authorized": {"const": False},
                "identities": strict(
                    {
                        name: identity_wrapper
                        for name in (
                            "evaluation_runner",
                            "exactness_runner",
                            "multi_role_runner",
                            "native_feature008_verifier",
                            "network_fault_runner",
                            "observation_writer",
                            "scientific_runner",
                            "signed_stage_authorization_verifier",
                            "stage_gate_analyzer",
                            "typed_gate_receipt_verifier",
                        )
                    }
                ),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
            },
        ),
        "workload-v2": schema(
            "workload-v2",
            {
                "campaign_id": {"const": "campaign-02"},
                "domain_ticket_counts": array(domain_count),
                "execution_class": {"const": "DESIGN_ONLY_NO_PRIMARY_EXECUTION"},
                "optimizer_steps_per_ticket": uint(1),
                "ticket_count": uint(1),
                "tokens_per_optimizer_step": uint(1),
                "tokens_per_ticket": uint(1),
                "total_tokens_per_arm_run": uint(1),
            },
        ),
        "execution-plan-v2": schema(
            "execution-plan-v2",
            {
                "arm_id": content_id(),
                "benchmark_definition_id": content_id(),
                "campaign_id": {"const": "campaign-02"},
                "certified_round_policy": {"oneOf": [{"type": "null"}, certified_policy]},
                "dataset_ids": array(content_id(), unique=True),
                "definition_attestation_id": content_id(),
                "environment_id": content_id(),
                "evaluation_implementation_ids": array(content_id(), unique=True),
                "evaluation_profile_ids": array(content_id(), unique=True),
                "evaluation_runner_id": content_id(),
                "execution_authorization_id": content_id(),
                "execution_class": {"enum": ["NON_PRIMARY_SMOKE", "PRIMARY_MEASURED"]},
                "hardware_id": content_id(),
                "image_id": content_id(),
                "model_id": content_id(),
                "optimizer_steps_per_ticket": uint(1),
                "parent_checkpoint_id": content_id(),
                "processed_tokens": uint(1),
                "repetition": uint(1),
                "result_class": {"enum": ["REFERENCE", "CERTIFIED_DELTAREDUCE"]},
                "round_id": text(),
                "runner_id": content_id(),
                "seed": uint(),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "ticket_count": uint(1),
                "tickets": array(ticket),
                "tokenizer_id": content_id(),
                "tokens_per_optimizer_step": uint(1),
                "tokens_per_ticket": uint(1),
                "total_tokens_per_arm_run": uint(1),
                "workload_id": content_id(),
                "writer_id": content_id(),
            },
            result_class_union=[
                {
                    "properties": {
                        "certified_round_policy": {"type": "null"},
                        "result_class": {"const": "REFERENCE"},
                    }
                },
                {
                    "properties": {
                        "certified_round_policy": certified_policy,
                        "result_class": {"const": "CERTIFIED_DELTAREDUCE"},
                    }
                },
            ],
        ),
        "evaluator-profile-v1": schema(
            "evaluator-profile-v1",
            {
                "dataset_id": content_id(),
                "evaluator_id": {"enum": ["hellaswag", "lambada", "wikitext"]},
                "method": {"minProperties": 1, "type": "object"},
                "tokenizer_id": content_id(),
            },
        ),
        "measured-evaluation-v1": schema(
            "measured-evaluation-v1",
            {
                "checkpoint_id": content_id(),
                "dataset_id": content_id(),
                "environment_id": content_id(),
                "evaluator_id": {"enum": ["hellaswag", "lambada", "wikitext"]},
                "evaluator_implementation_id": content_id(),
                "evaluator_profile_id": content_id(),
                "execution_plan_id": content_id(),
                "item_count": uint(1),
                "item_evidence_root": content_id(),
                "method_observation": {"minProperties": 1, "type": "object"},
                "metrics": array(metric),
                "model_id": content_id(),
                "scored_token_count": uint(),
                "source_class": {"const": "MEASURED_MODEL_INFERENCE"},
                "tokenizer_id": content_id(),
            },
        ),
        "component-identity-v1": schema(
            "component-identity-v1",
            {
                "component": {
                    "enum": [
                        "PRIMARY_EVALUATION_RUNNER",
                        "PRIMARY_OBSERVATION_WRITER",
                        "PRIMARY_SCIENTIFIC_RUNNER",
                    ]
                },
                "create_only_store_policy_id": content_id(),
                "environment_id": content_id(),
                "executable_hashes": array(executable),
                "hardware_compatibility_class_id": content_id(),
                "image_id": content_id(),
                "model_data_staging_policy_id": content_id(),
                "output_schema_ids": array(content_id(), unique=True),
                "source_commit": commit_id(),
                "source_tree": commit_id(),
                "timeout_policy_id": content_id(),
            },
        ),
        "observation-v2": schema(
            "observation-v2",
            observation_properties,
            result_class_union=observation_result_union,
        ),
        "observation-v3": schema(
            "observation-v3",
            observation_v3_properties,
            result_class_union=observation_result_union,
        ),
        "observation-receipt-v1": schema(
            "observation-receipt-v1",
            {
                "artifact_ids": array(content_id(), unique=True),
                "create_only": {"const": True},
                "execution_plan_id": content_id(),
                "observation_id": content_id(),
                "status": {"const": "PUBLISHED"},
                "writer_id": content_id(),
            },
        ),
        "gpu-environment-lock-v1": schema(
            "gpu-environment-lock-v1",
            {
                "cpu_portable_lock_id": content_id(),
                "cuda_runtime_id": text(),
                "image_scope": {"const": "PINNED_CUDA_BASE_PLUS_HASH_LOCKED_PYTHON_ENVIRONMENT"},
                "immutable_resolution": {"const": True},
                "oci_image_digest": content_id(),
                "platform_locks": array(lock_ref),
                "policy_id": content_id(),
                "python": {"const": "3.12.1"},
                "required_packages": {"minProperties": 6, "type": "object"},
                "requirements_input_id": content_id(),
                "sbom_id": content_id(),
                "scientific_use": {"const": True},
            },
        ),
        "native-chain-admission-bundle-v1": schema(
            "native-chain-admission-bundle-v1",
            {
                "aggregate_root_qc": {"minProperties": 1, "type": "object"},
                "aggregation_plan_certificate": {"minProperties": 1, "type": "object"},
                "apply_arithmetic_profile": {"minProperties": 1, "type": "object"},
                "apply_candidate": {"minProperties": 1, "type": "object"},
                "apply_qc": {"minProperties": 1, "type": "object"},
                "checkpoint_wal_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
                "current_pointer_command": {"minProperties": 1, "type": "object"},
                "effect_set_id": content_id(),
                "eligibility_certificate": {"minProperties": 1, "type": "object"},
                "execution_plan_id": content_id(),
                "expected_input_tuples": array(
                    strict(
                        {
                            "availability_certificate_id": content_id(),
                            "commitment_id": content_id(),
                            "domain_id": text(),
                            "ticket_id": content_id(),
                        }
                    )
                ),
                "final_checkpoint_id": content_id(),
                "input_set_certificate": {"minProperties": 1, "type": "object"},
                "norm_evidence": {"minProperties": 1, "type": "object"},
                "ordered_contributions": array(
                    strict({"contribution_id": content_id(), "ticket_id": content_id()})
                ),
                "parameter_shard_qcs": array({"minProperties": 1, "type": "object"}),
                "parent_checkpoint_id": content_id(),
                "policy": certified_policy,
                "runtime_state_id": content_id(),
                "runtime_wal_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
                "seed_transcript": {"minProperties": 1, "type": "object"},
                "terminal_outcome": {"const": "APPLIED"},
            },
        ),
        "native-chain-admission-receipt-v1": schema(
            "native-chain-admission-receipt-v1",
            {
                "aggregate_root_qc_id": content_id(),
                "apply_qc_id": content_id(),
                "certificate_bundle_id": content_id(),
                "certified_round_policy_id": content_id(),
                "checkpoint_wal_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
                "effect_set_id": content_id(),
                "execution_plan_id": content_id(),
                "final_checkpoint_id": content_id(),
                "input_set_certificate_id": content_id(),
                "native_build_id": content_id(),
                "native_chain_verifier_id": content_id(),
                "runtime_state_id": content_id(),
                "runtime_wal_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
                "status": {"const": "ACCEPT"},
            },
        ),
    }
    execution_v2 = documents["execution-plan-v2"]
    execution_v2_properties = execution_v2["properties"]
    assert isinstance(execution_v2_properties, dict)
    documents["execution-plan-v3"] = schema(
        "execution-plan-v3",
        {
            **{
                key: value
                for key, value in execution_v2_properties.items()
                if key not in {"formal_semantics_id", "schema_version", "type_name"}
            },
            "domain_manifest_id": content_id(),
            "qualified_runtime_lineage_id": content_id(),
            "ticket_plan_id": content_id(),
        },
        result_class_union=[
            {
                "properties": {
                    "certified_round_policy": {"type": "null"},
                    "result_class": {"const": "REFERENCE"},
                }
            },
            {
                "properties": {
                    "certified_round_policy": certified_policy,
                    "result_class": {"const": "CERTIFIED_DELTAREDUCE"},
                }
            },
        ],
    )
    execution_v3 = documents["execution-plan-v3"]
    execution_v3_properties = execution_v3["properties"]
    assert isinstance(execution_v3_properties, dict)
    documents["execution-plan-v4"] = schema(
        "execution-plan-v4",
        {
            **{
                key: value
                for key, value in execution_v3_properties.items()
                if key
                not in {
                    "execution_authorization_id",
                    "formal_semantics_id",
                    "schema_version",
                    "type_name",
                }
            },
            "execution_authorized": {"const": False},
            "gate_stage": {
                "enum": [
                    "STAGE_A_EXACTNESS",
                    "STAGE_B_SCIENTIFIC",
                    "STAGE_C_EMULATED_WAN",
                ]
            },
        },
        result_class_union=[
            {
                "properties": {
                    "certified_round_policy": {"type": "null"},
                    "result_class": {"const": "REFERENCE"},
                }
            },
            {
                "properties": {
                    "certified_round_policy": certified_policy,
                    "result_class": {"const": "CERTIFIED_DELTAREDUCE"},
                }
            },
        ],
    )
    execution_v4 = documents["execution-plan-v4"]
    execution_v4_properties = execution_v4["properties"]
    assert isinstance(execution_v4_properties, dict)
    documents["execution-plan-v5"] = schema(
        "execution-plan-v5",
        {
            **{
                key: value
                for key, value in execution_v4_properties.items()
                if key not in {"formal_semantics_id", "schema_version", "type_name"}
            },
            "ticket_identity_scope": {"const": "ROUND_ID_PLUS_TICKET_TEMPLATE_ID"},
        },
        result_class_union=[
            {
                "properties": {
                    "certified_round_policy": {"type": "null"},
                    "result_class": {"const": "REFERENCE"},
                }
            },
            {
                "properties": {
                    "certified_round_policy": certified_policy,
                    "result_class": {"const": "CERTIFIED_DELTAREDUCE"},
                }
            },
        ],
    )
    execution_v5 = documents["execution-plan-v5"]
    execution_v5_properties = execution_v5["properties"]
    assert isinstance(execution_v5_properties, dict)
    documents["execution-plan-v6"] = schema(
        "execution-plan-v6",
        {
            **{
                key: value
                for key, value in execution_v5_properties.items()
                if key not in {"formal_semantics_id", "schema_version", "type_name"}
            },
            "java_executable_id": content_id(),
            "native_executable_id": content_id(),
            "netty_artifact_ids": array(content_id(), unique=True),
            "transport_harness_id": content_id(),
        },
        result_class_union=[
            {
                "properties": {
                    "certified_round_policy": {"type": "null"},
                    "result_class": {"const": "REFERENCE"},
                }
            },
            {
                "properties": {
                    "certified_round_policy": certified_policy,
                    "result_class": {"const": "CERTIFIED_DELTAREDUCE"},
                }
            },
        ],
    )
    exact_stage_ids = {
        "items": content_id(),
        "maxItems": 15,
        "minItems": 15,
        "type": "array",
        "uniqueItems": True,
    }
    documents["plan-catalog-v1"] = schema(
        "plan-catalog-v1",
        {
            "base_plan_count": {"const": 15},
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "definition_attestation_id": content_id(),
            "domain_manifest_id": content_id(),
            "execution_authorized": {"const": False},
            "plan_ids": {
                "items": content_id(),
                "maxItems": 45,
                "minItems": 45,
                "type": "array",
                "uniqueItems": True,
            },
            "plan_ids_by_stage": strict(
                {
                    "STAGE_A_EXACTNESS": exact_stage_ids,
                    "STAGE_B_SCIENTIFIC": exact_stage_ids,
                    "STAGE_C_EMULATED_WAN": exact_stage_ids,
                }
            ),
            "qualified_runtime_lineage_id": content_id(),
            "status": {"const": "COMPILED_NOT_EXECUTABLE_REQUIRES_STAGE_AUTHORIZATION"},
            "ticket_plan_id": content_id(),
            "workload_contract_id": content_id(),
        },
    )
    documents["plan-catalog-v2"] = schema(
        "plan-catalog-v2",
        {
            "base_plan_count": {"const": 15},
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "definition_attestation_id": content_id(),
            "definition_attestation_verified_at": timestamp,
            "domain_manifest_id": content_id(),
            "execution_authorized": {"const": False},
            "plan_ids": {
                "items": content_id(),
                "maxItems": 45,
                "minItems": 45,
                "type": "array",
                "uniqueItems": True,
            },
            "plan_ids_by_stage": strict(
                {
                    "STAGE_A_EXACTNESS": exact_stage_ids,
                    "STAGE_B_SCIENTIFIC": exact_stage_ids,
                    "STAGE_C_EMULATED_WAN": exact_stage_ids,
                }
            ),
            "qualified_runtime_lineage_id": content_id(),
            "stage_execution_model": {"const": "INDEPENDENT_BFT_RUNS"},
            "status": {"const": "COMPILED_NOT_EXECUTABLE_REQUIRES_STAGE_AUTHORIZATION"},
            "ticket_identity_scope": {"const": "ROUND_ID_PLUS_TICKET_TEMPLATE_ID"},
            "ticket_plan_id": content_id(),
            "workload_contract_id": content_id(),
        },
    )
    documents["plan-catalog-v3"] = schema(
        "plan-catalog-v3",
        {
            "base_plan_count": {"const": 15},
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "definition_attestation_id": content_id(),
            "definition_attestation_verified_at": timestamp,
            "domain_manifest_id": content_id(),
            "execution_authorized": {"const": False},
            "gate_analyzer_id": content_id(),
            "plan_ids": {
                "items": content_id(),
                "maxItems": 45,
                "minItems": 45,
                "type": "array",
                "uniqueItems": True,
            },
            "plan_ids_by_stage": strict(
                {
                    "STAGE_A_EXACTNESS": exact_stage_ids,
                    "STAGE_B_SCIENTIFIC": exact_stage_ids,
                    "STAGE_C_EMULATED_WAN": exact_stage_ids,
                }
            ),
            "qualified_runtime_lineage_id": content_id(),
            "stage_execution_identities_id": content_id(),
            "stage_execution_model": {"const": "INDEPENDENT_BFT_RUNS"},
            "status": {"const": "COMPILED_NOT_EXECUTABLE_REQUIRES_STAGE_AUTHORIZATION"},
            "ticket_identity_scope": {"const": "ROUND_ID_PLUS_TICKET_TEMPLATE_ID"},
            "ticket_plan_id": content_id(),
            "workload_contract_id": content_id(),
        },
    )
    documents["stage-execution-authorization-v1"] = schema(
        "stage-execution-authorization-v1",
        {
            "allowed_plan_ids": array(content_id(), unique=True),
            "authorized_stage": {
                "enum": [
                    "STAGE_A_EXACTNESS",
                    "STAGE_B_SCIENTIFIC",
                    "STAGE_C_EMULATED_WAN",
                ]
            },
            "authorized_task_ids": array(text(), unique=True),
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "definition_attestation_id": content_id(),
            "plan_catalog_id": content_id(),
            "real_wan_authorized": {"const": False},
            "required_predecessor_receipt_ids": {
                "items": content_id(),
                "type": "array",
                "uniqueItems": True,
            },
            "result_qc_authorized": {"const": False},
            "stage_a_authorized": {"type": "boolean"},
            "stage_b_authorized": {"type": "boolean"},
            "stage_c_authorized": {"type": "boolean"},
        },
    )
    documents["stage-execution-authorization-v2"] = schema(
        "stage-execution-authorization-v2",
        {
            "allowed_plan_ids": {
                "items": content_id(),
                "maxItems": 15,
                "minItems": 15,
                "type": "array",
                "uniqueItems": True,
            },
            "authorized_stage": {"enum": stages},
            "authorized_task_ids": array(text(), unique=True),
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "definition_attestation_id": content_id(),
            "issued_at": timestamp,
            "plan_catalog_id": content_id(),
            "real_wan_authorized": {"const": False},
            "required_predecessor_receipt_ids": {
                "items": content_id(),
                "maxItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "result_qc_authorized": {"const": False},
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_a_authorized": {"type": "boolean"},
            "stage_b_authorized": {"type": "boolean"},
            "stage_c_authorized": {"type": "boolean"},
            "validator_set_id": content_id(),
        },
    )
    documents["stage-authorization-validator-set-v1"] = schema(
        "stage-authorization-validator-set-v1",
        {
            "campaign_id": {"const": "campaign-02"},
            "f_b": uint(),
            "purpose": {"const": "BENCHMARK_STAGE_AUTHORIZATION_REVIEW"},
            "validators": array(validator, unique=True),
        },
    )
    documents["stage-authorization-vote-v1"] = schema(
        "stage-authorization-vote-v1",
        {
            "public_key_id": content_id(),
            "purpose": {"const": "BENCHMARK_STAGE_AUTHORIZATION_REVIEW"},
            "signature": {"pattern": "^[A-Za-z0-9+/]{86}==$", "type": "string"},
            "signature_algorithm": {"const": "ED25519"},
            "signed_message_sha256": content_id(),
            "signer_id": text(),
            "stage_authorization_id": content_id(),
            "submitted_at": timestamp,
            "validator_set_id": content_id(),
        },
    )
    documents["stage-authorization-attestation-v1"] = schema(
        "stage-authorization-attestation-v1",
        {
            "f_b": uint(),
            "governance_only": {"const": True},
            "independent_approval": {"const": True},
            "ordered_public_key_ids": array(content_id(), unique=True),
            "ordered_signers": array(text(), unique=True),
            "ordered_vote_ids": array(content_id(), unique=True),
            "quorum_threshold": uint(1),
            "signature_set_root": content_id(),
            "stage_authorization_id": content_id(),
            "validator_set_id": content_id(),
            "verified_at": timestamp,
        },
    )
    documents["stage-gate-receipt-v1"] = schema(
        "stage-gate-receipt-v1",
        {
            "accepted_plan_ids": {
                "items": content_id(),
                "maxItems": 15,
                "minItems": 15,
                "type": "array",
                "uniqueItems": True,
            },
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "completed_stage": {"enum": stages},
            "decision": {"enum": ["FAIL", "PASS"]},
            "definition_attestation_id": content_id(),
            "evidence_root": content_id(),
            "finalized_at": timestamp,
            "gate_analyzer_id": content_id(),
            "gate_qc_id": content_id(),
            "gate_result_id": content_id(),
            "plan_catalog_id": content_id(),
            "qualified_runtime_lineage_id": content_id(),
            "required_plan_ids": {
                "items": content_id(),
                "maxItems": 15,
                "minItems": 15,
                "type": "array",
                "uniqueItems": True,
            },
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_authorization_attestation_id": content_id(),
        },
    )
    documents["stage-gate-receipt-v2"] = schema(
        "stage-gate-receipt-v2",
        {
            "accepted_plan_ids": exact_stage_ids,
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "completed_stage": {"enum": stages},
            "decision": {"enum": ["FAIL", "PASS"]},
            "definition_attestation_id": content_id(),
            "evidence_root": content_id(),
            "finalized_at": timestamp,
            "gate_analyzer_id": content_id(),
            "gate_qc_id": content_id(),
            "gate_result_id": content_id(),
            "plan_catalog_id": content_id(),
            "qualified_runtime_lineage_id": content_id(),
            "required_plan_ids": exact_stage_ids,
            "runner_id": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_authorization_attestation_id": content_id(),
        },
    )
    documents["stage-gate-receipt-v3"] = schema(
        "stage-gate-receipt-v3",
        {
            "accepted_plan_ids": exact_stage_ids,
            "benchmark_definition_id": content_id(),
            "campaign_id": {"const": "campaign-02"},
            "completed_stage": {"enum": stages},
            "decision": {"enum": ["FAIL", "PASS"]},
            "definition_attestation_id": content_id(),
            "evidence_root": content_id(),
            "finalized_at": timestamp,
            "gate_analyzer_id": content_id(),
            "gate_qc_id": content_id(),
            "gate_result_id": content_id(),
            "plan_catalog_id": content_id(),
            "qualified_runtime_lineage_id": content_id(),
            "required_plan_ids": exact_stage_ids,
            "runner_environment_id": content_id(),
            "runner_id": content_id(),
            "runner_implementation_id": content_id(),
            "runner_role": text(),
            "runner_source_class": {"enum": ["MEASURED_CI_WORKFLOW", "MEASURED_HARDWARE"]},
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_authorization_attestation_id": content_id(),
        },
    )
    documents["stage-plan-evidence-v1"] = schema(
        "stage-plan-evidence-v1",
        {
            "decision": {"const": "PASS"},
            "evidence_ids": array(content_id(), unique=True),
            "plan_id": content_id(),
            "runner_id": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
        },
    )
    documents["stage-plan-evidence-v2"] = schema(
        "stage-plan-evidence-v2",
        {
            "decision": {"const": "PASS"},
            "environment_id": content_id(),
            "evidence_ids": array(content_id(), unique=True),
            "evidence_kind": {"enum": ["NETWORK_FAULT_EXECUTION", "SEMANTIC_EXACTNESS_MATRIX"]},
            "implementation_id": content_id(),
            "plan_id": content_id(),
            "runner_id": content_id(),
            "runner_identity_id": content_id(),
            "runner_role": {"enum": ["EXACTNESS_RUNNER", "NETWORK_FAULT_RUNNER"]},
            "source_class": {"enum": ["MEASURED_CI_WORKFLOW", "MEASURED_HARDWARE"]},
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "verified_summary_ids": array(content_id(), unique=True),
        },
    )
    documents["stage-gate-result-v1"] = schema(
        "stage-gate-result-v1",
        {
            "accepted_plan_ids": exact_stage_ids,
            "benchmark_definition_id": content_id(),
            "completed_stage": {"enum": stages},
            "definition_attestation_id": content_id(),
            "evidence_root": content_id(),
            "gate_analyzer_id": content_id(),
            "plan_catalog_id": content_id(),
            "plan_evidence_ids": exact_stage_ids,
            "qualified_runtime_lineage_id": content_id(),
            "required_plan_ids": exact_stage_ids,
            "runner_id": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_authorization_attestation_id": content_id(),
            "stage_execution_identities_id": content_id(),
        },
    )
    documents["stage-gate-result-v2"] = schema(
        "stage-gate-result-v2",
        {
            "accepted_plan_ids": exact_stage_ids,
            "benchmark_definition_id": content_id(),
            "completed_stage": {"enum": stages},
            "definition_attestation_id": content_id(),
            "evidence_root": content_id(),
            "gate_analyzer_id": content_id(),
            "plan_catalog_id": content_id(),
            "plan_evidence_ids": exact_stage_ids,
            "qualified_runtime_lineage_id": content_id(),
            "required_plan_ids": exact_stage_ids,
            "runner_environment_id": content_id(),
            "runner_id": content_id(),
            "runner_implementation_id": content_id(),
            "runner_role": text(),
            "runner_source_class": {"enum": ["MEASURED_CI_WORKFLOW", "MEASURED_HARDWARE"]},
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_authorization_attestation_id": content_id(),
            "stage_execution_identities_id": content_id(),
        },
    )
    network_counters = strict(
        {
            "bytes_per_token": uint(),
            "cumulative_delay_ms": uint(),
            "delivered_packets": uint(),
            "dropped_packets": uint(),
            "duplicated_packets": uint(),
            "network_share_ppm": uint(),
            "packet_count": uint(1),
            "payload_bytes": uint(1),
            "profile_id": content_id(),
            "reordered_packets": uint(),
            "wire_bytes": uint(),
        }
    )
    fault_result = strict(
        {
            "at_step": uint(),
            "event_id": text(),
            "expected_outcome": text(),
            "observed_outcome": text(),
            "passed": {"const": True},
        }
    )
    documents["network-fault-plan-evidence-v1"] = schema(
        "network-fault-plan-evidence-v1",
        {
            "applied_network_profile_ids": array(content_id(), unique=True),
            "decision": {"const": "PASS"},
            "definition_network_profile_ids": array(content_id(), unique=True),
            "environment_id": content_id(),
            "excluded_real_wan_profile": strict(
                {
                    "profile_id": content_id(),
                    "reason": {"const": "STAGE_C_EMULATED_ONLY_REAL_WAN_NOT_AUTHORIZED"},
                }
            ),
            "fault_profile_ids": array(content_id(), unique=True),
            "fault_results": array(fault_result, unique=True),
            "implementation_id": content_id(),
            "network_counters": array(network_counters, unique=True),
            "plan_id": content_id(),
            "resilience_result": {"const": "PASS"},
            "runner_id": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
        },
    )
    measured_network_counters = strict(
        {
            "attempted_packets": uint(1),
            "attempted_payload_bytes": uint(1),
            "disconnect_count": uint(),
            "disconnect_duration_ms": uint(),
            "dropped_packets": uint(),
            "dropped_payload_bytes": uint(),
            "duplicate_packets": uint(),
            "duplicate_payload_bytes": uint(),
            "java_rx_payload_bytes": uint(1),
            "java_transport_receipt_id": content_id(),
            "java_tx_payload_bytes": uint(1),
            "network_profile_id": content_id(),
            "os_rx_bytes": uint(1),
            "os_tx_bytes": uint(1),
            "reordered_packets": uint(),
            "unique_delivered_packets": uint(1),
            "unique_delivered_payload_bytes": uint(1),
        }
    )
    native_fault_result = strict(
        {
            "at_step": uint(),
            "event_id": text(),
            "expected_outcome": text(),
            "native_effect_root": content_id(),
            "native_state_root": content_id(),
            "native_trace_id": content_id(),
            "native_wal_sha256": content_id(),
            "observed_outcome": text(),
            "passed": {"const": True},
        }
    )
    documents["network-fault-plan-evidence-v2"] = schema(
        "network-fault-plan-evidence-v2",
        {
            "applied_network_profile_ids": {
                "items": content_id(),
                "maxItems": 3,
                "minItems": 3,
                "type": "array",
                "uniqueItems": True,
            },
            "decision": {"const": "PASS"},
            "definition_network_profile_ids": {
                "items": content_id(),
                "maxItems": 4,
                "minItems": 4,
                "type": "array",
                "uniqueItems": True,
            },
            "environment_id": content_id(),
            "excluded_real_wan_profile": strict(
                {
                    "profile_id": content_id(),
                    "reason": {"const": "STAGE_C_EMULATED_ONLY_REAL_WAN_NOT_AUTHORIZED"},
                }
            ),
            "fault_profile_ids": {
                "items": content_id(),
                "maxItems": 1,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "fault_results": {
                "items": native_fault_result,
                "maxItems": 7,
                "minItems": 7,
                "type": "array",
                "uniqueItems": True,
            },
            "image_id": content_id(),
            "implementation_id": content_id(),
            "java_executable_id": content_id(),
            "measurement_source": {"const": "PYTHON_JAVA_NETTY_CPP_OS"},
            "native_effect_root": content_id(),
            "native_executable_id": content_id(),
            "native_fault_trace_id": content_id(),
            "native_state_root": content_id(),
            "native_wal_sha256": content_id(),
            "netty_artifact_ids": array(content_id(), unique=True),
            "network_counters": {
                "items": measured_network_counters,
                "maxItems": 3,
                "minItems": 3,
                "type": "array",
                "uniqueItems": True,
            },
            "plan_id": content_id(),
            "resilience_result": {"const": "PASS"},
            "runner_id": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "transport_harness_id": content_id(),
        },
    )
    measured_network_counters_v3 = strict(
        {
            "attempted_packets": uint(1),
            "attempted_payload_bytes": uint(1),
            "disconnect_count": uint(),
            "disconnect_duration_ms": uint(),
            "dropped_packets": uint(),
            "dropped_payload_bytes": uint(),
            "duplicate_packets": uint(),
            "duplicate_payload_bytes": uint(),
            "java_rx_payload_bytes": uint(1),
            "java_transport_receipt_id": content_id(),
            "java_tx_payload_bytes": uint(1),
            "network_profile_id": content_id(),
            "os_rx_bytes": uint(1),
            "os_rx_bytes_after": uint(1),
            "os_rx_bytes_before": uint(),
            "os_tx_bytes": uint(1),
            "os_tx_bytes_after": uint(1),
            "os_tx_bytes_before": uint(),
            "reordered_packets": uint(),
            "unique_delivered_packets": uint(1),
            "unique_delivered_payload_bytes": uint(1),
        }
    )
    native_fault_result_v3 = strict(
        {
            "action": text(),
            "actor_class": text(),
            "at_step": uint(),
            "availability_success": {"type": "boolean"},
            "current_checkpoint_advanced": {"type": "boolean"},
            "event_id": text(),
            "expected_outcome": text(),
            "native_effect_root": content_id(),
            "native_state_root": content_id(),
            "native_trace_base64": {"minLength": 1, "type": "string"},
            "native_trace_id": content_id(),
            "native_wal_sha256": content_id(),
            "observation_source": {"const": "ACTUAL_RUNTIME_TRANSITION"},
            "observed_outcome": text(),
            "passed": {"const": True},
            "runtime_operation_count": uint(1),
            "view_change_observed": {"type": "boolean"},
            "wal_replayed": {"type": "boolean"},
        }
    )
    network_fault_v3 = {
        key: value
        for key, value in documents["network-fault-plan-evidence-v2"]["properties"].items()
        if key not in {"formal_semantics_id", "schema_version", "type_name"}
    }
    network_fault_v3.update(
        {
            "fault_results": {
                "items": native_fault_result_v3,
                "maxItems": 7,
                "minItems": 7,
                "type": "array",
                "uniqueItems": True,
            },
            "network_counters": {
                "items": measured_network_counters_v3,
                "maxItems": 3,
                "minItems": 3,
                "type": "array",
                "uniqueItems": True,
            },
            "raw_java_receipt_base64": {"minLength": 1, "type": "string"},
            "raw_java_receipt_id": content_id(),
        }
    )
    documents["network-fault-plan-evidence-v3"] = schema(
        "network-fault-plan-evidence-v3", network_fault_v3
    )
    nullable_content_id = {"anyOf": [content_id(), {"type": "null"}]}
    causal_message_tick = strict({"logical_tick": uint(), "message_id": text()})
    causal_fault_result = {
        key: value for key, value in native_fault_result_v3["properties"].items()
    }
    causal_fault_result.update(
        {
            "abort_qc_id": nullable_content_id,
            "aggregate_root_qc_id": nullable_content_id,
            "aggregate_root_qc_tick": uint(),
            "apply_qc_id": nullable_content_id,
            "apply_qc_tick": uint(),
            "apply_quorum_threshold": uint(),
            "apply_validator_set_id": nullable_content_id,
            "apply_work_item_id": nullable_content_id,
            "causal_transport_receipt_id": content_id(),
            "certified_abort_tick": uint(),
            "current_pointer_after": nullable_content_id,
            "current_pointer_before": nullable_content_id,
            "dropped_message_ids": array(text(), minimum=0, unique=True),
            "failed_quorum_reason": {"type": ["string", "null"]},
            "gst_tick": uint(),
            "hard_deadline_tick": uint(),
            "isc_ticket_set": array(text(), minimum=0, unique=True),
            "loss_fraction": strict({"denominator": uint(1), "numerator": uint()}),
            "lost_ticket_ids": array(text(), minimum=0, unique=True),
            "lost_worker_ids": array(text(), minimum=0, unique=True),
            "message_delivery_ticks": array(causal_message_tick, minimum=0, unique=True),
            "missing_work_policy_result": text(),
            "network_profile_id": text(),
            "next_checkpoint_id": nullable_content_id,
            "next_optimizer_state_id": nullable_content_id,
            "parent_checkpoint_id": nullable_content_id,
            "parent_optimizer_state_id": nullable_content_id,
            "partition_start_tick": uint(),
            "per_domain_remaining_tickets": {
                "additionalProperties": uint(),
                "type": "object",
            },
            "per_domain_required_tickets": {
                "additionalProperties": uint(),
                "type": "object",
            },
            "pi_d_renormalized": {"const": False},
            "quorum_capacity_after": uint(),
            "quorum_capacity_before": uint(),
            "quorum_formation_tick": uint(),
            "unavailable_ids": array(text(), minimum=0, unique=True),
            "worker_count_before": uint(),
            "worker_count_lost": uint(),
        }
    )
    network_fault_v4 = {key: value for key, value in network_fault_v3.items()}
    network_fault_v4["fault_results"] = {
        "items": strict(causal_fault_result),
        "maxItems": 7,
        "minItems": 7,
        "type": "array",
        "uniqueItems": True,
    }
    documents["network-fault-plan-evidence-v4"] = schema(
        "network-fault-plan-evidence-v4", network_fault_v4
    )
    candidate_plan_record = strict(
        {
            "applied_network_profile_ids": {
                "items": content_id(),
                "maxItems": 3,
                "minItems": 3,
                "type": "array",
                "uniqueItems": True,
            },
            "fault_profile_ids": {
                "items": content_id(),
                "maxItems": 1,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "plan_id": content_id(),
            "raw_evidence_file_id": content_id(),
            "raw_evidence_path": {
                "pattern": "^raw-evidence/network-fault-[0-9a-f]{64}\\.json$",
                "type": "string",
            },
            "raw_java_receipt_id": content_id(),
            "semantic_projection_id": content_id(),
            "typed_evidence_id": content_id(),
        }
    )
    documents["stage-c-candidate-run-v1"] = schema(
        "stage-c-candidate-run-v1",
        {
            "authoritative_definition_vote_count": {"const": 0},
            "authoritative_definition_attestation_present": {"const": False},
            "benchmark_result_qc_emitted": {"const": False},
            "candidate_compiler_attestation_class": {"const": "TEST_ONLY_DETERMINISTIC_EPHEMERAL"},
            "candidate_compiler_signature_ids": {
                "items": content_id(),
                "maxItems": 3,
                "minItems": 3,
                "type": "array",
                "uniqueItems": True,
            },
            "candidate_definition_id": content_id(),
            "candidate_run_ordinal": {"maximum": 2, "minimum": 1, "type": "integer"},
            "decision": {"const": "PASS"},
            "execution_authorized": {"const": False},
            "observation_count": {"const": 0},
            "plan_catalog_id": content_id(),
            "plan_count": {"const": 15},
            "plan_records": {
                "items": candidate_plan_record,
                "maxItems": 15,
                "minItems": 15,
                "type": "array",
                "uniqueItems": True,
            },
            "qualified_runtime_lineage_id": content_id(),
            "raw_evidence_root": content_id(),
            "semantic_root": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_execution_identities_id": content_id(),
            "stage_gate_receipt_emitted": {"const": False},
        },
    )
    exact_candidate_ids = {
        "items": content_id(),
        "maxItems": 15,
        "minItems": 15,
        "type": "array",
        "uniqueItems": True,
    }
    documents["stage-c-candidate-summary-v1"] = schema(
        "stage-c-candidate-summary-v1",
        {
            "authoritative_catalog_constructed": {"const": False},
            "authoritative_definition_attestation_present": {"const": False},
            "authoritative_definition_vote_count": {"const": 0},
            "benchmark_result_qc_emitted": {"const": False},
            "candidate_definition_id": content_id(),
            "candidate_plan_catalog_id": content_id(),
            "candidate_run_package_ids": {
                "items": content_id(),
                "maxItems": 2,
                "minItems": 2,
                "type": "array",
            },
            "decision": {"const": "PASS"},
            "execution_authorized": {"const": False},
            "observation_count": {"const": 0},
            "plan_count": {"const": 15},
            "plan_ids": exact_candidate_ids,
            "raw_evidence_roots": {
                "items": content_id(),
                "maxItems": 2,
                "minItems": 2,
                "type": "array",
            },
            "repeat_semantic_match": {"const": True},
            "semantic_root": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "stage_gate_receipt_emitted": {"const": False},
        },
    )
    artifact_summary = strict(
        {
            "evidence_type": {
                "enum": ["JAVA_CONFORMANCE_LOG", "NATIVE_CTEST_JUNIT", "PYTHON_JUNIT"]
            },
            "filename": text(),
            "formal_semantics_id": {"const": FORMAL_ID},
            "raw_digest": content_id(),
            "schema_version": {"const": "1.0.0"},
            "test_count": uint(1),
            "type_name": {"const": "CAMPAIGN02_STAGE_A_VERIFIED_ARTIFACT_SUMMARY"},
            "verified_items": array(text(), unique=True),
        }
    )
    documents["stage-a-semantic-evidence-v1"] = schema(
        "stage-a-semantic-evidence-v1",
        {
            "artifact_summaries": {
                "items": artifact_summary,
                "maxItems": 7,
                "minItems": 7,
                "type": "array",
                "uniqueItems": True,
            },
            "artifact_summary_ids": {
                "items": content_id(),
                "maxItems": 7,
                "minItems": 7,
                "type": "array",
                "uniqueItems": True,
            },
            "decision": {"const": "PASS"},
        },
    )
    digest_map = {
        "additionalProperties": content_id(),
        "minProperties": 1,
        "propertyNames": {"minLength": 1, "type": "string"},
        "type": "object",
    }
    documents["stage-workflow-gate-qc-v2"] = schema(
        "stage-workflow-gate-qc-v2",
        {
            "authority_artifact_digest": content_id(),
            "decision": {"const": "PASS"},
            "dispatch_ref": {"const": "refs/heads/main"},
            "dispatch_sha": commit_id(),
            "gate_analyzer_id": content_id(),
            "gate_result_id": content_id(),
            "input_artifact_digests": digest_map,
            "output_artifact_digests": digest_map,
            "plan_evidence_ids": exact_stage_ids,
            "runner_id": content_id(),
            "source_commit": commit_id(),
            "source_tree": commit_id(),
            "workflow_file_content_id": content_id(),
            "workflow_ref": {
                "const": (
                    "chartjs333/delta/.github/workflows/"
                    "benchmark-campaign02-stage-a.yml@refs/heads/main"
                )
            },
            "workflow_repository": {"const": "chartjs333/delta"},
            "workflow_run_attempt": {"const": 1},
            "workflow_run_id": uint(1),
            "workflow_sha": commit_id(),
        },
    )
    artifact_id_map = {
        "additionalProperties": uint(1),
        "minProperties": 1,
        "propertyNames": {"minLength": 1, "type": "string"},
        "type": "object",
    }
    artifact_origin_map = {
        "additionalProperties": {
            "enum": ["AUTHORITY_RUN", "BOOTSTRAP_REGISTRATION_RUN", "CURRENT_STAGE_RUN"]
        },
        "minProperties": 1,
        "propertyNames": {"minLength": 1, "type": "string"},
        "type": "object",
    }
    documents["stage-workflow-gate-qc-v3"] = schema(
        "stage-workflow-gate-qc-v3",
        {
            "authority_artifact_digest": content_id(),
            "authority_artifact_content_digest": content_id(),
            "authority_artifact_id": uint(1),
            "bootstrap_mapping_attestation_id": content_id(),
            "bootstrap_mapping_id": content_id(),
            "decision": {"const": "PASS"},
            "dispatch_ref": {"const": "refs/heads/main"},
            "event_name": {"const": "workflow_dispatch"},
            "gate_analyzer_id": content_id(),
            "gate_result_id": content_id(),
            "github_sha": commit_id(),
            "input_artifact_digests": digest_map,
            "input_artifact_content_digests": digest_map,
            "input_artifact_ids": artifact_id_map,
            "input_artifact_origins": artifact_origin_map,
            "input_artifact_run_attempts": artifact_id_map,
            "input_artifact_run_ids": artifact_id_map,
            "output_artifact_digests": digest_map,
            "output_artifact_content_digests": digest_map,
            "output_artifact_ids": artifact_id_map,
            "output_artifact_origins": artifact_origin_map,
            "output_artifact_run_attempts": artifact_id_map,
            "output_artifact_run_ids": artifact_id_map,
            "plan_evidence_ids": exact_stage_ids,
            "qualified_source_commit": commit_id(),
            "qualified_source_tree": commit_id(),
            "registration_receipt_id": content_id(),
            "repository": {"const": "chartjs333/delta"},
            "run_attempt": uint(1),
            "run_id": uint(1),
            "runner_id": content_id(),
            "source_commit": commit_id(),
            "source_stage_a_workflow_content_id": content_id(),
            "source_tree": commit_id(),
            "workflow_blob_id": commit_id(),
            "workflow_content_id": content_id(),
            "workflow_id": uint(1),
            "workflow_path": {"const": ".github/workflows/campaign02-stage-a-bootstrap.yml"},
            "workflow_ref": {
                "const": (
                    "chartjs333/delta/.github/workflows/"
                    "campaign02-stage-a-bootstrap.yml@refs/heads/main"
                )
            },
            "workflow_sha": commit_id(),
        },
    )
    stage_workflow_v4 = {
        key: value
        for key, value in documents["stage-workflow-gate-qc-v3"]["properties"].items()
        if key not in {"formal_semantics_id", "schema_version", "type_name"}
    }
    stage_workflow_v4.update(
        {
            "registration_api_evidence_root": content_id(),
            "registration_artifact_archive_digest": content_id(),
            "registration_artifact_id": uint(1),
            "registration_attestation_id": content_id(),
            "registration_run_attempt": uint(1),
            "registration_run_id": uint(1),
        }
    )
    documents["stage-workflow-gate-qc-v4"] = schema("stage-workflow-gate-qc-v4", stage_workflow_v4)
    documents["workflow-bootstrap-mapping-v1"] = schema(
        "workflow-bootstrap-mapping-v1",
        {
            "bootstrap_commit": commit_id(),
            "bootstrap_workflow_blob_id": commit_id(),
            "bootstrap_workflow_content_id": content_id(),
            "bootstrap_workflow_path": {
                "const": ".github/workflows/campaign02-stage-a-bootstrap.yml"
            },
            "execution_authorized": {"const": False},
            "qualified_source_commit": commit_id(),
            "qualified_source_tree": commit_id(),
            "repository": {"const": "chartjs333/delta"},
            "source_stage_a_workflow_content_id": content_id(),
            "source_stage_a_workflow_path": {
                "const": ".github/workflows/benchmark-campaign02-stage-a.yml"
            },
        },
    )
    bootstrap_validator = strict(
        {
            "controller_id": text(),
            "public_key_base64": {
                "pattern": "^[A-Za-z0-9+/]{43}=$",
                "type": "string",
            },
            "signer_id": text(),
        }
    )
    documents["workflow-bootstrap-validator-set-v1"] = schema(
        "workflow-bootstrap-validator-set-v1",
        {
            "execution_authorized": {"const": False},
            "f_b": uint(1),
            "quorum_threshold": uint(1),
            "validators": array(bootstrap_validator, unique=True),
        },
    )
    documents["workflow-bootstrap-signature-v1"] = schema(
        "workflow-bootstrap-signature-v1",
        {
            "mapping_id": content_id(),
            "signature_base64": {
                "pattern": "^[A-Za-z0-9+/]{86}==$",
                "type": "string",
            },
            "signer_id": text(),
            "submitted_at": {"format": "date-time", "type": "string"},
            "validator_set_id": content_id(),
        },
    )
    documents["workflow-registration-receipt-v1"] = schema(
        "workflow-registration-receipt-v1",
        {
            "authority_bundle_supplied": {"const": False},
            "bootstrap_commit": commit_id(),
            "bootstrap_commit_on_default_branch": {"const": True},
            "bootstrap_mapping_id": content_id(),
            "bootstrap_workflow_blob_id": commit_id(),
            "bootstrap_workflow_content_id": content_id(),
            "checked_at": {"format": "date-time", "type": "string"},
            "default_branch_ref": {"const": "refs/heads/main"},
            "github_api_evidence_digest": content_id(),
            "observations": {"const": 0},
            "qualified_source_commit": commit_id(),
            "qualified_source_exists": {"const": True},
            "qualified_source_tree": commit_id(),
            "repository": {"const": "chartjs333/delta"},
            "stage_a_plans_executed": {"const": 0},
            "stage_gate_receipt_emitted": {"const": False},
            "workflow_id": uint(1),
            "workflow_path": {"const": ".github/workflows/campaign02-stage-a-bootstrap.yml"},
            "workflow_state": {"const": "active"},
            "workflow_visible_on_default_branch": {"const": True},
        },
    )
    raw_api_snapshot = strict(
        {
            "endpoint": {
                "format": "uri",
                "pattern": "^https://api\\.github\\.com/",
                "type": "string",
            },
            "response_base64": {"minLength": 1, "type": "string"},
            "response_sha256": content_id(),
            "status_code": {"const": 200},
        }
    )
    documents["workflow-registration-api-evidence-v1"] = schema(
        "workflow-registration-api-evidence-v1",
        {
            "collected_at": {"format": "date-time", "type": "string"},
            "execution_authorized": {"const": False},
            "repository": {"const": "chartjs333/delta"},
            "snapshots": strict(
                {
                    "bootstrap_workflow_file": raw_api_snapshot,
                    "default_branch_ref": raw_api_snapshot,
                    "registration_artifact_metadata": raw_api_snapshot,
                    "registration_workflow_run": raw_api_snapshot,
                    "workflow_metadata": raw_api_snapshot,
                }
            ),
        },
    )
    documents["workflow-registration-signature-v1"] = schema(
        "workflow-registration-signature-v1",
        {
            "api_evidence_root": content_id(),
            "mapping_id": content_id(),
            "registration_receipt_id": content_id(),
            "signature_base64": {
                "pattern": "^[A-Za-z0-9+/]{86}==$",
                "type": "string",
            },
            "signer_id": text(),
            "submitted_at": {"format": "date-time", "type": "string"},
            "validator_set_id": content_id(),
        },
    )
    documents["workflow-registration-receipt-v2"] = schema(
        "workflow-registration-receipt-v2",
        {
            "api_evidence_root": content_id(),
            "authority_bundle_supplied": {"const": False},
            "bootstrap_commit": commit_id(),
            "bootstrap_commit_on_default_branch": {"const": True},
            "bootstrap_mapping_id": content_id(),
            "bootstrap_workflow_blob_id": commit_id(),
            "bootstrap_workflow_content_id": content_id(),
            "checked_at": {"format": "date-time", "type": "string"},
            "default_branch_ref": {"const": "refs/heads/main"},
            "execution_artifact_count": {"const": 0},
            "execution_count": {"const": 0},
            "observation_count": {"const": 0},
            "qualified_source_commit": commit_id(),
            "qualified_source_exists": {"const": True},
            "qualified_source_tree": commit_id(),
            "registration_artifact_archive_digest": content_id(),
            "registration_artifact_id": uint(1),
            "registration_run_attempt": uint(1),
            "registration_run_event": {"const": "workflow_dispatch"},
            "registration_run_head_sha": commit_id(),
            "registration_run_id": uint(1),
            "registration_run_ref": {"const": "refs/heads/main"},
            "registration_workflow_id": uint(1),
            "repository": {"const": "chartjs333/delta"},
            "stage_a_plans_executed": {"const": 0},
            "stage_gate_receipt_emitted": {"const": False},
            "workflow_id": uint(1),
            "workflow_path": {"const": ".github/workflows/campaign02-stage-a-bootstrap.yml"},
            "workflow_state": {"const": "active"},
            "workflow_visible_on_default_branch": {"const": True},
        },
    )
    terminal_registration_fields = {
        "registration_artifact_created_at": {"format": "date-time", "type": "string"},
        "registration_artifact_expires_at": {"format": "date-time", "type": "string"},
        "registration_artifact_name": {
            "minLength": 1,
            "pattern": "^.+-attempt-[1-9][0-9]*$",
            "type": "string",
        },
        "registration_run_completed_at": {"format": "date-time", "type": "string"},
        "registration_run_conclusion": {"const": "success"},
        "registration_run_created_at": {"format": "date-time", "type": "string"},
        "registration_run_status": {"const": "completed"},
        "registration_run_updated_at": {"format": "date-time", "type": "string"},
    }
    registration_receipt_v3 = {
        key: value
        for key, value in documents["workflow-registration-receipt-v2"]["properties"].items()
        if key not in {"formal_semantics_id", "schema_version", "type_name"}
    }
    registration_receipt_v3.update(terminal_registration_fields)
    documents["workflow-registration-receipt-v3"] = schema(
        "workflow-registration-receipt-v3", registration_receipt_v3
    )
    registration_signature_v2 = {
        key: value
        for key, value in documents["workflow-registration-signature-v1"]["properties"].items()
        if key not in {"formal_semantics_id", "schema_version", "type_name"}
    }
    registration_signature_v2.update(terminal_registration_fields)
    documents["workflow-registration-signature-v2"] = schema(
        "workflow-registration-signature-v2", registration_signature_v2
    )
    return documents


def fixture_entries() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for path in sorted((ROOT / "delta-protocol/fixtures/010/campaign-02").rglob("*.json")):
        relative = path.relative_to(ROOT / "delta-protocol").as_posix()
        result.append(
            {
                "id": "BENCHMARK010-CAMPAIGN02-" + path.stem.upper().replace("-", "_"),
                "path": relative,
                "sha256": digest(path.read_bytes()),
            }
        )
    return result


def registry(schemas: dict[str, dict[str, object]]) -> dict[str, object]:
    artifacts = []
    media_types = []
    for name, (schema_id, _, version) in SCHEMAS.items():
        path = f"schemas/010/campaign-02/{name}.json"
        artifacts.append({"id": schema_id, "path": path, "sha256": digest(pretty(schemas[name]))})
        media_types.append(
            {
                "id": "MEDIA-CAMPAIGN02-" + name.upper(),
                "schema_id": schema_id,
                "value": (
                    f"application/vnd.deltareduce.campaign-02.{name}+json;"
                    f"version={version.split('.')[0]}"
                ),
            }
        )
    return {
        "artifacts": artifacts,
        "fixtures": fixture_entries(),
        "formal_semantics_id": FORMAL_ID,
        "media_types": media_types,
        "registry_version": "010.10.0-causal-stagec-terminal-registration",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
    }


def root_registry(registry_value: dict[str, object]) -> bytes:
    root_path = ROOT / "delta-protocol/registry.json"
    root = json.loads(root_path.read_bytes())
    if not isinstance(root, dict):
        raise Campaign02SchemaError("ROOT_REGISTRY_INVALID")
    schema_ids = {item[0] for item in SCHEMAS.values()}
    root["extensions"] = [
        item
        for item in root["extensions"]
        if item.get("id") != "REGISTRY-BENCHMARK-010-CAMPAIGN-02"
    ]
    root["fixtures"] = [
        item
        for item in root["fixtures"]
        if not str(item.get("id", "")).startswith("BENCHMARK010-CAMPAIGN02-")
    ]
    root["media_types"] = [
        item for item in root["media_types"] if item.get("schema_id") not in schema_ids
    ]
    root["schemas"] = [item for item in root["schemas"] if item.get("id") not in schema_ids]
    registry_bytes = pretty(registry_value)
    root["extensions"].append(
        {
            "id": "REGISTRY-BENCHMARK-010-CAMPAIGN-02",
            "path": "schemas/010/campaign-02/registry-v1.json",
            "sha256": digest(registry_bytes),
        }
    )
    root["fixtures"].extend(registry_value["fixtures"])
    root["media_types"].extend(registry_value["media_types"])
    root["schemas"].extend(registry_value["artifacts"])
    for field, key in (
        ("extensions", "path"),
        ("fixtures", "path"),
        ("media_types", "id"),
        ("schemas", "path"),
    ):
        root[field] = sorted(root[field], key=lambda item: item[key])
    return pretty(root)


def expected_outputs() -> dict[Path, bytes]:
    schemas = schema_documents()
    registry_value = registry(schemas)
    outputs = {SCHEMA_ROOT / f"{name}.json": pretty(value) for name, value in schemas.items()}
    outputs[REGISTRY_PATH] = pretty(registry_value)
    outputs[ROOT / "delta-protocol/registry.json"] = root_registry(registry_value)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    outputs = expected_outputs()
    if arguments.write:
        for path, value in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
    else:
        for path, expected in outputs.items():
            if not path.is_file() or path.read_bytes() != expected:
                raise Campaign02SchemaError(f"CAMPAIGN02_SCHEMA_OUTPUT_DRIFT:{path.name}")
    print(
        canonical(
            {
                "fixture_count": len(fixture_entries()),
                "schema_count": len(SCHEMAS),
                "semantic_completeness_claimed": False,
                "status": "PASS",
            }
        ).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
