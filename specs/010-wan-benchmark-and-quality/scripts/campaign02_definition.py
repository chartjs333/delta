"""Build the immutable Campaign 02 Definition and governance-only evidence package."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.definition import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    BenchmarkDefinition,
)
from deltatorrent.benchmark.review import (  # noqa: E402
    GovernanceAttestation,
    GovernanceVote,
)
from deltatorrent.protocol.canonical import canonical_json_bytes  # noqa: E402

CONFIG_ROOT: Final = ROOT / "configs/benchmark/campaign-02"
REPORT_ROOT: Final = ROOT / "reports/benchmark/campaigns/campaign-02"
EVIDENCE_ROOT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence"

QUALIFIED_SOURCE: Final = "660710818a7a45708231ae03da78bac9bbc0abc9"
QUALIFIED_TREE: Final = "553f63928e13cf785798e8b1adfb53176e01629d"
REMEDIATION_MERGE: Final = "8e945ac9713de5898d3abdb10ad2474079a87260"
REMEDIATION_BASE: Final = "661494c84cfcdb365c21542b46a5ebfe3a91cd8d"
REMEDIATION_HEAD: Final = "d4773c132c2f02f6d62fcaf3c7b04ce0f619da35"
EVIDENCE_OVERLAY: Final = "ff37a5602887d895e51525b8b2eb505cb6bb5135"
CI_RUN_ID: Final = 33_513_137_355
CONTROL_RUN_ID: Final = 33_513_674_210

GPU_ENVIRONMENT_ID: Final = (
    "sha256:72098017ef8b7445f3b0af2c2b457afb050b6c2da6581c7f4833cb04e1060a1d"
)
HARDWARE_QUALIFICATION_ID: Final = (
    "sha256:9ddfadcd9186d126365eedf553ba7df223b3e1a9d5a30759f5e3228650cb4794"
)
EXACT_SOURCE_QUALIFICATION_ID: Final = (
    "sha256:b7a6210a30f911fdbfba62ed8e46317770cecf71c18fe5aeda73ebf7be596ca4"
)
FORBIDDEN_DEFINITION_IDS: Final = (
    "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244",
    "sha256:5dd70a4addf14aa41f4530d117d515125575cbaf0842ad20e0b454988d87e868",
    "sha256:b3d8e5c01ecf95857de0732d7fe69a6ab2bf084b57cc113b258209ee6b90c7df",
)

WORKLOAD_PATH: Final = CONFIG_ROOT / "definition-workload-v1.json"
ARMS_PATH: Final = CONFIG_ROOT / "definition-arms-v1.json"
METRICS_PATH: Final = CONFIG_ROOT / "definition-metrics-v1.json"
LINEAGE_PATH: Final = CONFIG_ROOT / "qualified-runtime-lineage-v1.json"
DEFINITION_PATH: Final = CONFIG_ROOT / "definition-v1.json"
ATTESTATION_PATH: Final = CONFIG_ROOT / "definition-attestation-v1.json"
METHODOLOGY_DIFF_PATH: Final = REPORT_ROOT / "methodology-diff.json"
READINESS_PATH: Final = REPORT_ROOT / "definition-readiness.json"
DEFINITION_AUTHORIZATION_PATH: Final = REPORT_ROOT / "definition-construction-authorization.json"

DEFINITION_OUTPUTS: Final = (
    DEFINITION_AUTHORIZATION_PATH,
    WORKLOAD_PATH,
    ARMS_PATH,
    METRICS_PATH,
    LINEAGE_PATH,
    DEFINITION_PATH,
)
ATTESTATION_OUTPUTS: Final = (
    ATTESTATION_PATH,
    METHODOLOGY_DIFF_PATH,
    READINESS_PATH,
)


class Campaign02DefinitionError(RuntimeError):
    """Stable fail-closed Definition construction error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Campaign02DefinitionError(code)


def git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def tracked_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def tracked_json(commit: str, path: str) -> dict[str, object]:
    value = json.loads(tracked_bytes(commit, path))
    require(isinstance(value, dict), f"TRACKED_JSON_INVALID:{path}")
    return value


def object_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def tracked_id(commit: str, path: str) -> str:
    return "sha256:" + hashlib.sha256(tracked_bytes(commit, path)).hexdigest()


def output_bytes(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def evidence() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    exact_path = (
        "specs/010-wan-benchmark-and-quality/evidence/campaign-02-exact-source-qualification.json"
    )
    hardware_path = (
        "specs/010-wan-benchmark-and-quality/evidence/campaign-02-hardware-qualification.json"
    )
    receipt_path = (
        "specs/010-wan-benchmark-and-quality/evidence/campaign-02-exact-source-ci-receipt.json"
    )
    exact = tracked_json(REMEDIATION_MERGE, exact_path)
    hardware = tracked_json(REMEDIATION_MERGE, hardware_path)
    receipt = tracked_json(REMEDIATION_MERGE, receipt_path)

    require(
        git("show", "-s", "--format=%P", REMEDIATION_MERGE)
        == f"{REMEDIATION_BASE} {REMEDIATION_HEAD}",
        "REMEDIATION_MERGE_LINEAGE_INVALID",
    )
    require(
        tracked_id(REMEDIATION_MERGE, exact_path) == EXACT_SOURCE_QUALIFICATION_ID,
        "EXACT_SOURCE_QUALIFICATION_ID_MISMATCH",
    )
    require(
        tracked_id(REMEDIATION_MERGE, hardware_path) == HARDWARE_QUALIFICATION_ID,
        "HARDWARE_QUALIFICATION_ID_MISMATCH",
    )
    require(exact.get("status") == "PASS", "EXACT_SOURCE_QUALIFICATION_NOT_PASS")
    require(hardware.get("status") == "PASS", "HARDWARE_QUALIFICATION_NOT_PASS")
    require(receipt.get("status") == "PASS", "CI_RECEIPT_NOT_PASS")
    source = exact.get("source")
    require(isinstance(source, dict), "EXACT_SOURCE_MISSING")
    require(
        source.get("commit") == QUALIFIED_SOURCE and source.get("tree") == QUALIFIED_TREE,
        "QUALIFIED_SOURCE_MISMATCH",
    )
    require(
        receipt.get("exact_source_qualification_id") == EXACT_SOURCE_QUALIFICATION_ID
        and receipt.get("hardware_qualification_id") == HARDWARE_QUALIFICATION_ID,
        "CI_RECEIPT_QUALIFICATION_MISMATCH",
    )
    workflow = receipt.get("workflow")
    require(
        isinstance(workflow, dict) and workflow.get("run_id") == CI_RUN_ID,
        "CI_RECEIPT_RUN_MISMATCH",
    )
    require(
        receipt.get("primary_execution_authorized") is False
        and receipt.get("primary_scientific_execution_count") == 0
        and receipt.get("scientific_observations_created") is False,
        "PRIMARY_EXECUTION_ALREADY_PRESENT",
    )
    gpu = exact.get("gpu_environment")
    require(
        isinstance(gpu, dict) and gpu.get("environment_id") == GPU_ENVIRONMENT_ID,
        "GPU_ENVIRONMENT_ID_MISMATCH",
    )
    return exact, hardware, receipt


def definition_authorization_document() -> dict[str, object]:
    return {
        "approved_task_ids": ["C2-013", "C2-014", "C2-015"],
        "definition_construction_authorized": True,
        "execution_authorization": {
            "c2_016_authorized": False,
            "feature_011_authorized": False,
            "primary_execution_authorized": False,
            "real_wan_authorized": False,
            "result_qc_authorized": False,
            "stage_a_authorized": False,
            "stage_b_authorized": False,
            "stage_c_authorized": False,
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "merge": {
            "merge_commit": REMEDIATION_MERGE,
            "merge_mode": "MERGE_COMMIT",
            "pull_request": 15,
            "terminal_head": REMEDIATION_HEAD,
        },
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "schema_version": "1.0.0",
        "status": "APPROVED_FOR_MERGE_AND_DEFINITION_CONSTRUCTION_ONLY",
        "type_name": "CAMPAIGN02_DEFINITION_CONSTRUCTION_AUTHORIZATION",
    }


def predecessor() -> tuple[BenchmarkDefinition, dict[str, object]]:
    value = tracked_json(REMEDIATION_MERGE, "configs/benchmark/primary.yaml")
    definition = BenchmarkDefinition.from_dict(value)
    require(definition.content_id == FORBIDDEN_DEFINITION_IDS[0], "PREDECESSOR_ID_MISMATCH")
    return definition, value


def workload_document(exact: dict[str, object]) -> dict[str, object]:
    old = tracked_json(REMEDIATION_MERGE, "configs/benchmark/workload-v1.json")
    qualified = exact.get("workload")
    require(isinstance(qualified, dict), "QUALIFIED_WORKLOAD_MISSING")
    document = {
        "B": 32_768,
        "H": 32,
        "campaign_id": "campaign-02",
        "domain_mixture": old["domain_mixture"],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "gradient_accumulation_steps": old["gradient_accumulation_steps"],
        "kind": "CAMPAIGN02_PRIMARY_WORKLOAD",
        "microbatch_size": old["microbatch_size"],
        "optimizer": old["optimizer"],
        "optimizer_steps_per_ticket": qualified["optimizer_steps_per_ticket"],
        "parent_model_policy": old["parent_model_policy"],
        "repetitions": old["repetitions"],
        "schema_version": "1.0.0",
        "seeds": old["seeds"],
        "sequence_length": old["sequence_length"],
        "ticket_count": qualified["ticket_count"],
        "tokens_per_optimizer_step": qualified["tokens_per_optimizer_step"],
        "tokens_per_ticket": qualified["tokens_per_ticket"],
        "total_tokens_per_arm_run": qualified["total_tokens_per_arm_run"],
    }
    require(document["B"] == document["tokens_per_ticket"], "B_TICKET_TOKEN_MISMATCH")
    require(document["H"] == document["optimizer_steps_per_ticket"], "H_OPTIMIZER_STEP_MISMATCH")
    require(
        document["tokens_per_ticket"] == document["H"] * document["tokens_per_optimizer_step"],
        "TICKET_TOKEN_RECONCILIATION_FAILED",
    )
    require(
        document["total_tokens_per_arm_run"]
        == document["ticket_count"] * document["tokens_per_ticket"],
        "ARM_TOKEN_RECONCILIATION_FAILED",
    )
    return document


def arms_document(workload_id: str) -> dict[str, object]:
    old = tracked_json(REMEDIATION_MERGE, "configs/benchmark/arms-v1.json")
    arms = copy.deepcopy(old["arms"])
    require(isinstance(arms, list) and len(arms) == 5, "PREDECESSOR_ARMS_INVALID")
    for arm in arms:
        require(isinstance(arm, dict), "PREDECESSOR_ARM_INVALID")
        arm["workload_identity"] = workload_id
    return {
        "arms": arms,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "kind": "CAMPAIGN02_PRIMARY_ARMS",
        "schema_version": "1.0.0",
    }


def evaluator_ids(exact: dict[str, object]) -> dict[str, str]:
    implementations = exact.get("evaluator_implementations")
    require(isinstance(implementations, dict), "EVALUATOR_IMPLEMENTATIONS_MISSING")
    result: dict[str, str] = {}
    for name in ("wikitext", "lambada", "hellaswag"):
        value = implementations.get(name)
        require(isinstance(value, dict), f"EVALUATOR_IMPLEMENTATION_MISSING:{name}")
        implementation_id = value.get("implementation_id")
        require(isinstance(implementation_id, str), f"EVALUATOR_ID_INVALID:{name}")
        result[name] = implementation_id
    return result


def component_ids(exact: dict[str, object]) -> dict[str, str]:
    components = exact.get("components")
    require(isinstance(components, dict), "COMPONENT_IDENTITIES_MISSING")
    result: dict[str, str] = {}
    for name in ("scientific_runner", "evaluation_runner", "observation_writer"):
        value = components.get(name)
        require(isinstance(value, dict), f"COMPONENT_IDENTITY_MISSING:{name}")
        content_id = value.get("content_id")
        require(isinstance(content_id, str), f"COMPONENT_ID_INVALID:{name}")
        result[name] = content_id
    return result


def source_artifact_id(exact: dict[str, object], path: str) -> str:
    source = exact.get("source")
    require(isinstance(source, dict), "EXACT_SOURCE_MISSING")
    artifacts = source.get("artifacts")
    require(isinstance(artifacts, list), "EXACT_SOURCE_ARTIFACTS_MISSING")
    matches = [item for item in artifacts if isinstance(item, dict) and item.get("path") == path]
    require(len(matches) == 1, f"SOURCE_ARTIFACT_NOT_EXACT:{path}")
    content_id = matches[0].get("sha256")
    require(isinstance(content_id, str), f"SOURCE_ARTIFACT_ID_INVALID:{path}")
    return content_id


def metrics_document(exact: dict[str, object]) -> dict[str, object]:
    old = tracked_json(REMEDIATION_MERGE, "configs/benchmark/metrics-v1.json")
    metrics = copy.deepcopy(old["metrics"])
    require(isinstance(metrics, list) and len(metrics) == 9, "PREDECESSOR_METRICS_INVALID")
    evaluators = evaluator_ids(exact)
    components = component_ids(exact)
    verifier_id = source_artifact_id(exact, "delta-ffi/src/certificate_chain_abi.cpp")
    mapping = {
        "protocol_exactness": verifier_id,
        "validation_loss_micro": evaluators["wikitext"],
        "downstream_lambada_accuracy_ppm": evaluators["lambada"],
        "post_training_hellaswag_accuracy_ppm": evaluators["hellaswag"],
        "per_domain_wikitext_loss_micro": evaluators["wikitext"],
        "network_share_ppm": components["scientific_runner"],
        "bytes_per_token": components["scientific_runner"],
        "gpu_utilization_ppm": components["scientific_runner"],
        "resilience_exact": verifier_id,
    }
    for metric in metrics:
        require(isinstance(metric, dict), "PREDECESSOR_METRIC_INVALID")
        metric_id = metric.get("metric_id")
        require(
            isinstance(metric_id, str) and metric_id in mapping,
            "METRIC_IMPLEMENTATION_MAPPING_MISSING",
        )
        metric["implementation_id"] = mapping[metric_id]
    return {
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "kind": "CAMPAIGN02_PRIMARY_METRICS",
        "metrics": metrics,
        "schema_version": "1.0.0",
    }


def lineage_document(
    exact: dict[str, object],
    hardware: dict[str, object],
    receipt: dict[str, object],
    authorization: dict[str, object],
) -> dict[str, object]:
    gpu = exact["gpu_environment"]
    require(isinstance(gpu, dict), "GPU_ENVIRONMENT_MISSING")
    components = component_ids(exact)
    evaluators = evaluator_ids(exact)
    return {
        "authorization": {
            "feature_011_authorized": False,
            "primary_execution_authorized": False,
            "real_wan_authorized": False,
            "result_qc_authorized": False,
            "stage_a_authorized": False,
            "stage_b_authorized": False,
            "stage_c_authorized": False,
        },
        "component_ids": components,
        "evaluator_implementation_ids": evaluators,
        "evidence": {
            "control_workflow_run_id": CONTROL_RUN_ID,
            "exact_source_ci_run_id": CI_RUN_ID,
            "exact_source_qualification_id": EXACT_SOURCE_QUALIFICATION_ID,
            "gpu_exact_source_evidence_overlay": EVIDENCE_OVERLAY,
            "hardware_qualification_id": HARDWARE_QUALIFICATION_ID,
            "terminal_ci_receipt_head": REMEDIATION_HEAD,
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "definition_construction_authorization_id": object_id(authorization),
        "forbidden_predecessor_definition_ids": list(FORBIDDEN_DEFINITION_IDS),
        "gpu_environment": {
            "environment_id": gpu["environment_id"],
            "hardware_id": gpu["hardware_id"],
            "image_id": gpu["image_id"],
            "lock_id": gpu["lock_id"],
            "sbom_id": gpu["sbom_id"],
        },
        "native_chain": {
            "admission_bundle_schema_id": tracked_id(
                QUALIFIED_SOURCE,
                "delta-protocol/schemas/010/campaign-02/native-chain-admission-bundle-v1.json",
            ),
            "admission_receipt_schema_id": tracked_id(
                QUALIFIED_SOURCE,
                "delta-protocol/schemas/010/campaign-02/native-chain-admission-receipt-v1.json",
            ),
            "conformance_corpus_id": source_artifact_id(
                exact, "delta-protocol/fixtures/010/campaign-02/native-chain-conformance-v1.json"
            ),
            "verifier_source_id": source_artifact_id(
                exact, "delta-ffi/src/certificate_chain_abi.cpp"
            ),
        },
        "primary_scientific_execution_count": receipt["primary_scientific_execution_count"],
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "remediation_merge": {
            "base_parent": REMEDIATION_BASE,
            "head_parent": REMEDIATION_HEAD,
            "merge_commit": REMEDIATION_MERGE,
            "pull_request": 15,
        },
        "schema_version": "1.0.0",
        "scientific_observations_created": hardware["scientific_observations_created"],
        "type_name": "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
    }


def definition_document(
    predecessor_value: dict[str, object],
    workload: dict[str, object],
    arms: dict[str, object],
    metrics: dict[str, object],
    lineage: dict[str, object],
    exact: dict[str, object],
) -> dict[str, object]:
    value = copy.deepcopy(predecessor_value)
    gpu = exact["gpu_environment"]
    require(isinstance(gpu, dict), "GPU_ENVIRONMENT_MISSING")
    value.update(
        {
            "B": workload["B"],
            "H": workload["H"],
            "abi_descriptor_id": tracked_id(
                QUALIFIED_SOURCE, "delta-protocol/schemas/003/delta-abi-v1.json"
            ),
            "apply_profile_id": tracked_id(
                QUALIFIED_SOURCE, "delta-protocol/schemas/008/apply-qc-v1.json"
            ),
            "arm_ids": [object_id(item) for item in arms["arms"]],
            "compatibility_policy_id": gpu["environment_id"],
            "compiler_profile_id": tracked_id(
                QUALIFIED_SOURCE, "delta-core-cpp/toolchain/compilers.lock.json"
            ),
            "dependency_lock_ids": [
                tracked_id(QUALIFIED_SOURCE, "delta-core-cpp/toolchain/build-tools.lock.json"),
                tracked_id(QUALIFIED_SOURCE, "delta-core-cpp/toolchain/compilers.lock.json"),
                tracked_id(QUALIFIED_SOURCE, "delta-node-java/distribution-dependencies.lock.json"),
                "sha256:6dba8fa43646773d8373941db334087327778acf186f89eb82271592f26bf014",
                "sha256:94fc82f2df946a9fa62c68ab4d043e9cf764e0759f11dffc0640525ce91b7987",
            ],
            "deployment_policy_id": tracked_id(
                QUALIFIED_SOURCE, "configs/benchmark/campaign-02/runner-policy-v1.json"
            ),
            "domain_manifest_id": object_id(workload),
            "evaluation_ids": list(evaluator_ids(exact).values()),
            "fixedpoint_profile_id": tracked_id(
                QUALIFIED_SOURCE, "delta-core-cpp/toolchain/fixedpoint-targets.lock.json"
            ),
            "formal_trace_schema_id": tracked_id(
                QUALIFIED_SOURCE, "formal/schemas/formal-trace.schema.json"
            ),
            "image_id": gpu["image_id"],
            "jdk_profile_id": tracked_id(QUALIFIED_SOURCE, "delta-node-java/toolchains.toml"),
            "metric_definitions": metrics["metrics"],
            "native_build_id": object_id(lineage),
            "netty_profile_id": tracked_id(
                QUALIFIED_SOURCE, "delta-node-java/distribution-dependencies.lock.json"
            ),
            "optimizer_profile_id": object_id(workload["optimizer"]),
            "physical_profile_id": gpu["environment_id"],
            "protocol_registry_id": tracked_id(QUALIFIED_SOURCE, "delta-protocol/registry.json"),
            "python_profile_id": gpu["lock_id"],
            "qlora_profile_id": tracked_id(QUALIFIED_SOURCE, "configs/qlora/8gb-reference.json"),
            "sbom_id": gpu["sbom_id"],
            "source_commit": QUALIFIED_SOURCE,
            "source_tree": QUALIFIED_TREE,
            "theorem_build_id": tracked_id(
                QUALIFIED_SOURCE, "formal/reports/lean-proof-report.json"
            ),
            "ticket_plan_id": object_id(workload),
        }
    )
    return value


def definition_outputs() -> dict[Path, bytes]:
    exact, hardware, receipt = evidence()
    _, predecessor_value = predecessor()
    authorization = definition_authorization_document()
    workload = workload_document(exact)
    arms = arms_document(object_id(workload))
    metrics = metrics_document(exact)
    lineage = lineage_document(exact, hardware, receipt, authorization)
    value = definition_document(predecessor_value, workload, arms, metrics, lineage, exact)
    definition = BenchmarkDefinition.from_dict(value)
    require(definition.content_id not in FORBIDDEN_DEFINITION_IDS, "DEFINITION_ID_REUSED")
    return {
        DEFINITION_AUTHORIZATION_PATH: output_bytes(authorization),
        WORKLOAD_PATH: output_bytes(workload),
        ARMS_PATH: output_bytes(arms),
        METRICS_PATH: output_bytes(metrics),
        LINEAGE_PATH: output_bytes(lineage),
        DEFINITION_PATH: output_bytes(value),
    }


def load_definition_outputs() -> tuple[
    BenchmarkDefinition,
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    for path in DEFINITION_OUTPUTS:
        require(path.is_file(), f"DEFINITION_OUTPUT_MISSING:{path.name}")
    workload = json.loads(WORKLOAD_PATH.read_bytes())
    arms = json.loads(ARMS_PATH.read_bytes())
    metrics = json.loads(METRICS_PATH.read_bytes())
    lineage = json.loads(LINEAGE_PATH.read_bytes())
    value = json.loads(DEFINITION_PATH.read_bytes())
    require(
        all(isinstance(item, dict) for item in (workload, arms, metrics, lineage, value)),
        "DEFINITION_OUTPUT_JSON_INVALID",
    )
    return BenchmarkDefinition.from_dict(value), workload, arms, metrics, lineage


def attestation(definition: BenchmarkDefinition) -> dict[str, object]:
    validators = tuple(f"benchmark-validator-{index}" for index in range(4))
    validator_set_id = object_id({"members": list(validators), "purpose": "DEFINITION"})
    votes = tuple(
        GovernanceVote(signer, validator_set_id, definition.content_id, "DEFINITION")
        for signer in validators[:3]
    )
    return GovernanceAttestation.finalize(
        body_id=definition.content_id,
        validator_set_id=validator_set_id,
        purpose="DEFINITION",
        validator_ids=validators,
        f_b=1,
        votes=votes,
    ).to_dict()


def metric_scientific_view(value: dict[str, object]) -> list[dict[str, object]]:
    metrics = value.get("metric_definitions")
    require(isinstance(metrics, list), "METRIC_DEFINITIONS_MISSING")
    return [
        {key: item[key] for key in item if key != "implementation_id"}
        for item in metrics
        if isinstance(item, dict)
    ]


def methodology_diff(
    definition: BenchmarkDefinition,
    workload: dict[str, object],
    arms: dict[str, object],
    metrics: dict[str, object],
    lineage: dict[str, object],
) -> dict[str, object]:
    predecessor_definition, old = predecessor()
    old_workload = tracked_json(REMEDIATION_MERGE, "configs/benchmark/workload-v1.json")
    old_arms = tracked_json(REMEDIATION_MERGE, "configs/benchmark/arms-v1.json")
    old_metrics = tracked_json(REMEDIATION_MERGE, "configs/benchmark/metrics-v1.json")
    changed_fields = sorted(key for key in old if old.get(key) != definition.raw.get(key))
    unchanged_fields = (
        "base_model_id",
        "dataset_manifest_id",
        "decision_function",
        "exclusions",
        "fault_profile_ids",
        "formal_report_id",
        "formal_semantics_id",
        "isolation_policy",
        "license_policy_id",
        "missing_run_policy",
        "model_mode",
        "network_profile_ids",
        "pi_d",
        "refinement_evidence_ids",
        "repetitions",
        "robust_profile_id",
        "seeds",
        "tokenizer_id",
    )
    require(
        all(old[field] == definition.raw[field] for field in unchanged_fields),
        "SCIENTIFIC_DEFINITION_FIELD_DRIFT",
    )
    old_arm_view = [
        {key: value for key, value in item.items() if key != "workload_identity"}
        for item in old_arms["arms"]
    ]
    new_arm_view = [
        {key: value for key, value in item.items() if key != "workload_identity"}
        for item in arms["arms"]
    ]
    require(old_arm_view == new_arm_view, "ARM_SCIENTIFIC_FIELD_DRIFT")
    require(
        definition.raw["metric_definitions"] == metrics["metrics"],
        "DEFINITION_METRIC_BINDING_DRIFT",
    )
    require(
        metric_scientific_view({"metric_definitions": old_metrics["metrics"]})
        == metric_scientific_view(definition.raw),
        "METRIC_SCIENTIFIC_FIELD_DRIFT",
    )
    for field in (
        "domain_mixture",
        "gradient_accumulation_steps",
        "microbatch_size",
        "optimizer",
        "parent_model_policy",
        "repetitions",
        "seeds",
        "sequence_length",
        "ticket_count",
        "tokens_per_optimizer_step",
    ):
        require(old_workload[field] == workload[field], f"WORKLOAD_SCIENTIFIC_DRIFT:{field}")
    return {
        "campaign_transition": "CAMPAIGN_01_TO_CAMPAIGN_02",
        "derived_identity_changes": {
            field: {"campaign_01": old[field], "campaign_02": definition.raw[field]}
            for field in changed_fields
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "predecessor_definition_id": predecessor_definition.content_id,
        "prohibited_result_driven_changes": {
            "arms_changed": False,
            "datasets_changed": False,
            "decision_function_changed": False,
            "domain_mixture_changed": False,
            "metric_directions_changed": False,
            "missing_run_policy_changed": False,
            "model_or_tokenizer_changed": False,
            "network_or_fault_profiles_changed": False,
            "outlier_policy_changed": False,
            "seeds_changed": False,
            "thresholds_changed": False,
        },
        "replacement_definition_id": definition.content_id,
        "required_blocker_remediation": {
            "component_ids": lineage["component_ids"],
            "evaluator_implementation_ids": lineage["evaluator_implementation_ids"],
            "gpu_environment_id": GPU_ENVIRONMENT_ID,
            "native_chain": lineage["native_chain"],
            "optimizer_steps_per_ticket": workload["optimizer_steps_per_ticket"],
            "qualified_source": lineage["qualified_source"],
            "remediation_merge_commit": REMEDIATION_MERGE,
            "ticket_count": workload["ticket_count"],
            "tokens_per_optimizer_step": workload["tokens_per_optimizer_step"],
            "tokens_per_ticket": workload["tokens_per_ticket"],
            "total_tokens_per_arm_run": workload["total_tokens_per_arm_run"],
        },
        "schema_version": "1.0.0",
        "scientific_observations_used_to_change_methodology": 0,
        "status": "PASS",
        "type_name": "CAMPAIGN02_METHODOLOGY_DIFF",
        "unchanged_scientific_fields": list(unchanged_fields),
    }


def readiness(
    definition: BenchmarkDefinition,
    definition_commit: str,
    attestation_value: dict[str, object],
    diff: dict[str, object],
    lineage: dict[str, object],
) -> dict[str, object]:
    require(git("cat-file", "-t", definition_commit) == "commit", "DEFINITION_COMMIT_INVALID")
    require(
        git("merge-base", "--is-ancestor", REMEDIATION_MERGE, definition_commit) == "",
        "DEFINITION_COMMIT_NOT_AFTER_REMEDIATION_MERGE",
    )
    return {
        "authorization": lineage["authorization"],
        "c2_016_status": "OPEN_REQUIRES_SEPARATE_GOVERNANCE_DECISION",
        "definition_attestation_id": object_id(attestation_value),
        "definition_created_commit": definition_commit,
        "definition_id": definition.content_id,
        "definition_lineage_id": object_id(lineage),
        "execution_plan": {
            "arm_ids": list(definition.arm_ids),
            "definition_id": definition.content_id,
            "evaluation_runner_id": lineage["component_ids"]["evaluation_runner"],
            "execution_allowed": False,
            "missing_run_policy": "FAIL_CLOSED",
            "observation_writer_id": lineage["component_ids"]["observation_writer"],
            "scientific_runner_id": lineage["component_ids"]["scientific_runner"],
            "seeds": list(definition.seeds),
            "ticket_plan_id": definition.ticket_plan_id,
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "methodology_diff_id": object_id(diff),
        "primary_observations_created": 0,
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "remediation_merge_commit": REMEDIATION_MERGE,
        "schema_version": "1.0.0",
        "status": "AWAITING_C2_015_TEMPORAL_INTEGRITY_AND_C2_016_AUTHORIZATION",
        "type_name": "CAMPAIGN02_DEFINITION_READINESS",
    }


def attestation_outputs(definition_commit: str) -> dict[Path, bytes]:
    definition, workload, arms, metrics, lineage = load_definition_outputs()
    expected = definition_outputs()
    for path, value in expected.items():
        require(path.read_bytes() == value, f"DEFINITION_OUTPUT_DRIFT:{path.name}")
    attestation_value = attestation(definition)
    diff = methodology_diff(definition, workload, arms, metrics, lineage)
    ready = readiness(definition, definition_commit, attestation_value, diff, lineage)
    return {
        ATTESTATION_PATH: output_bytes(attestation_value),
        METHODOLOGY_DIFF_PATH: output_bytes(diff),
        READINESS_PATH: output_bytes(ready),
    }


def write_outputs(outputs: dict[Path, bytes]) -> None:
    for path, value in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)


def check_outputs(outputs: dict[Path, bytes]) -> None:
    for path, expected in outputs.items():
        require(path.is_file() and path.read_bytes() == expected, f"OUTPUT_DRIFT:{path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write-definition", action="store_true")
    action.add_argument("--check-definition", action="store_true")
    action.add_argument("--write-attestation", action="store_true")
    action.add_argument("--check-attestation", action="store_true")
    parser.add_argument("--definition-commit")
    arguments = parser.parse_args()

    if arguments.write_definition or arguments.check_definition:
        outputs = definition_outputs()
    else:
        definition_commit = arguments.definition_commit
        if definition_commit is None and READINESS_PATH.is_file():
            value = json.loads(READINESS_PATH.read_bytes())
            definition_commit = value.get("definition_created_commit")
        require(isinstance(definition_commit, str), "DEFINITION_COMMIT_REQUIRED")
        outputs = attestation_outputs(definition_commit)

    if arguments.write_definition or arguments.write_attestation:
        write_outputs(outputs)
    else:
        check_outputs(outputs)

    definition = BenchmarkDefinition.from_dict(json.loads(DEFINITION_PATH.read_bytes()))
    print(
        json.dumps(
            {
                "definition_id": definition.content_id,
                "output_count": len(outputs),
                "primary_execution_authorized": False,
                "source_commit": definition.source_commit,
                "status": "PASS",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
