"""Construct the immutable Campaign 02 Definition without execution authority."""

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

from deltatorrent.benchmark.arms import ArmSpec  # noqa: E402
from deltatorrent.benchmark.campaign02 import (  # noqa: E402
    CAMPAIGN02_GATE_STAGES,
    CertifiedRoundPolicy,
    ParameterShardKey,
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.campaign02_binding import (  # noqa: E402
    CertifiedPlanBinding,
    QualifiedRuntimeLineage,
    expected_round_id,
)
from deltatorrent.benchmark.definition import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    BenchmarkDefinition,
)
from deltatorrent.benchmark.stage_authorization import (  # noqa: E402
    CAMPAIGN02_STAGE_GATE_ANALYZER_ID,
)
from deltatorrent.protocol.canonical import (  # noqa: E402
    canonical_json_bytes,
    sha256_content_id,
)

CONFIG: Final = ROOT / "configs/benchmark/campaign-02"
REPORTS: Final = ROOT / "reports/benchmark/campaigns/campaign-02"
EVIDENCE: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence"

QUALIFIED_SOURCE: Final = "f323ae1bff31841f75431b47853d1860d3c3b3e6"
QUALIFIED_TREE: Final = "6cb86a3c9d31dcf242445280ebf16ec4389cd0e1"
REMEDIATION_MERGE: Final = "881301d8443c667a478617cc663d1450aee9777a"
REMEDIATION_BASE: Final = "8e945ac9713de5898d3abdb10ad2474079a87260"
REMEDIATION_HEAD: Final = "48d3315a707b07eec4e5143ec3931d6b6f474b8e"
EVIDENCE_OVERLAY: Final = "89360158860cf07f595e4a731e4b7f971524d994"
EXACT_QUALIFICATION_ID: Final = (
    "sha256:12c77ab5f2bafaeb3a0214113c364ae15567060033b28715d0af43335552ba26"
)
HARDWARE_QUALIFICATION_ID: Final = (
    "sha256:0f7c85be413674ccd971ae5c464db91b24feaae2c6c7b621fd51e64953d7619e"
)
TERMINAL_RECEIPT: Final = REMEDIATION_HEAD
DEDICATED_RUN_ID: Final = 33_620_734_265
TERMINAL_RUN_ID: Final = 33_621_631_925

FORBIDDEN_DEFINITION_IDS: Final = (
    "sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af",
    "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244",
    "sha256:5dd70a4addf14aa41f4530d117d515125575cbaf0842ad20e0b454988d87e868",
    "sha256:b3d8e5c01ecf95857de0732d7fe69a6ab2bf084b57cc113b258209ee6b90c7df",
)

ARMS_PATH: Final = CONFIG / "definition-arms-v2.json"
DATASETS_PATH: Final = CONFIG / "definition-dataset-manifest-v1.json"
METRICS_PATH: Final = CONFIG / "definition-metrics-v2.json"
IDENTITIES_PATH: Final = CONFIG / "stage-execution-identities-v1.json"
LINEAGE_PATH: Final = CONFIG / "qualified-runtime-lineage-v2.json"
DEFINITION_PATH: Final = CONFIG / "definition-v2.json"
AUTHORIZATION_PATH: Final = REPORTS / "definition-construction-authorization-v2.json"
METHODOLOGY_PATH: Final = REPORTS / "methodology-diff-v2.json"
READINESS_PATH: Final = REPORTS / "definition-readiness-v2.json"


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
        ("git", "show", f"{commit}:{path}"),
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def tracked_json(commit: str, path: str) -> dict[str, object]:
    value = json.loads(tracked_bytes(commit, path))
    require(isinstance(value, dict), f"TRACKED_JSON_INVALID:{path}")
    return value


def raw_id(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def tracked_id(commit: str, path: str) -> str:
    return raw_id(tracked_bytes(commit, path))


def object_id(value: object, domain: bytes = b"") -> str:
    return sha256_content_id(domain + canonical_json_bytes(value))


def canonical_output(value: object, *, newline: bool = True) -> bytes:
    return canonical_json_bytes(value) + (b"\n" if newline else b"")


def source_artifact_id(exact: dict[str, object], path: str) -> str:
    source = exact.get("source")
    require(isinstance(source, dict), "EXACT_SOURCE_MISSING")
    artifacts = source.get("artifacts")
    require(isinstance(artifacts, list), "EXACT_SOURCE_ARTIFACTS_MISSING")
    matches = [item for item in artifacts if isinstance(item, dict) and item.get("path") == path]
    if len(matches) == 1:
        content_id = matches[0].get("sha256")
        require(isinstance(content_id, str), f"SOURCE_ARTIFACT_ID_INVALID:{path}")
        return content_id
    return tracked_id(QUALIFIED_SOURCE, path)


def qualification() -> tuple[dict[str, object], dict[str, object]]:
    exact_path = (
        "specs/010-wan-benchmark-and-quality/evidence/"
        "campaign-02-signed-stage-tsan-lifetime-exact-source-qualification.json"
    )
    hardware_path = (
        "specs/010-wan-benchmark-and-quality/evidence/"
        "campaign-02-signed-stage-tsan-lifetime-hardware-qualification.json"
    )
    receipt_path = (
        "specs/010-wan-benchmark-and-quality/evidence/"
        "campaign-02-signed-stage-tsan-lifetime-exact-source-ci-receipt.json"
    )
    parents = git("show", "-s", "--format=%P", REMEDIATION_MERGE)
    require(
        parents == f"{REMEDIATION_BASE} {REMEDIATION_HEAD}",
        "REMEDIATION_MERGE_LINEAGE_INVALID",
    )
    exact = tracked_json(REMEDIATION_MERGE, exact_path)
    hardware = tracked_json(REMEDIATION_MERGE, hardware_path)
    receipt = tracked_json(REMEDIATION_MERGE, receipt_path)
    require(tracked_id(REMEDIATION_MERGE, exact_path) == EXACT_QUALIFICATION_ID, "EXACT_ID")
    require(
        tracked_id(REMEDIATION_MERGE, hardware_path) == HARDWARE_QUALIFICATION_ID,
        "HARDWARE_ID",
    )
    source = exact.get("source")
    require(
        exact.get("status") == "PASS"
        and hardware.get("status") == "PASS"
        and receipt.get("status") == "PASS"
        and isinstance(source, dict)
        and source.get("commit") == QUALIFIED_SOURCE
        and source.get("tree") == QUALIFIED_TREE,
        "QUALIFICATION_NOT_PASS",
    )
    require(
        receipt.get("source") == {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE}
        and receipt.get("primary_execution_authorized") is False
        and receipt.get("primary_scientific_execution_count") == 0
        and receipt.get("scientific_observations_created") is False,
        "QUALIFICATION_EXECUTION_BOUNDARY_INVALID",
    )
    return exact, hardware


def _identity(
    *,
    role: str,
    executable_paths: tuple[str, ...],
    entrypoints: tuple[str, ...],
    exact: dict[str, object],
) -> dict[str, object]:
    gpu = exact.get("gpu_environment")
    require(isinstance(gpu, dict), "GPU_ENVIRONMENT_MISSING")
    return {
        "allowed_role": role,
        "campaign_id": "campaign-02",
        "entrypoints": list(entrypoints),
        "environment_id": gpu["environment_id"],
        "executable_hashes": [
            {"content_id": source_artifact_id(exact, path), "path": path}
            for path in executable_paths
        ],
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "hardware_id": gpu["hardware_id"],
        "image_id": gpu["image_id"],
        "schema_version": "1.0.0",
        "source_commit": QUALIFIED_SOURCE,
        "source_tree": QUALIFIED_TREE,
        "type_name": "CAMPAIGN02_STAGE_ROLE_IDENTITY",
        "workflow_hashes": [
            {
                "content_id": tracked_id(
                    QUALIFIED_SOURCE,
                    ".github/workflows/benchmark-campaign02-remediation.yml",
                ),
                "path": ".github/workflows/benchmark-campaign02-remediation.yml",
            }
        ],
    }


def component_identities(exact: dict[str, object]) -> dict[str, object]:
    exactness = _identity(
        role="EXACTNESS_RUNNER",
        executable_paths=(
            "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_binding.py",
            "delta-worker-python/src/deltatorrent/benchmark/governance.py",
            "delta-worker-python/src/deltatorrent/benchmark/primary.py",
            "delta-worker-python/src/deltatorrent/benchmark/primary_executor.py",
            "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
            "delta-worker-python/src/deltatorrent/cli/benchmark.py",
            "delta-ffi/src/certificate_chain_abi.cpp",
            "delta-runtime-cpp/src/runtime.cpp",
        ),
        entrypoints=(
            "deltatorrent.benchmark.campaign02.authorize_execution_class",
            "deltatorrent.benchmark.campaign02_binding.compile_campaign02_plan_catalog",
        ),
        exact=exact,
    )
    network = _identity(
        role="NETWORK_FAULT_RUNNER",
        executable_paths=(
            "delta-worker-python/src/deltatorrent/benchmark/fault_profiles.py",
            "delta-worker-python/src/deltatorrent/benchmark/network_profiles.py",
            "delta-runtime-cpp/src/benchmark/fault_control.cpp",
            "delta-node-java/src/main/java/io/deltareduce/node/benchmark/"
            "NetworkFaultController.java",
            "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
        ),
        entrypoints=(
            "deltatorrent.benchmark.fault_profiles",
            "deltatorrent.benchmark.network_profiles",
            "io.deltareduce.node.benchmark.NetworkFaultController",
        ),
        exact=exact,
    )
    components = exact.get("components")
    require(isinstance(components, dict), "QUALIFIED_COMPONENTS_MISSING")

    def qualified_component(name: str) -> dict[str, object]:
        value = components.get(name)
        require(isinstance(value, dict), f"QUALIFIED_COMPONENT_MISSING:{name}")
        content_id = value.get("content_id")
        document = value.get("value")
        require(
            isinstance(content_id, str)
            and isinstance(document, dict)
            and object_id(document, b"deltareduce.010.primary-component.v1\0") == content_id,
            f"QUALIFIED_COMPONENT_INVALID:{name}",
        )
        return {"content_id": content_id, "value": document}

    exactness_id = object_id(exactness, b"deltareduce.010.campaign02-stage-role-identity.v1\0")
    network_id = object_id(network, b"deltareduce.010.campaign02-stage-role-identity.v1\0")
    scientific = qualified_component("scientific_runner")
    evaluation = qualified_component("evaluation_runner")
    writer = qualified_component("observation_writer")
    multi_role = {
        "allowed_roles": [
            "EXACTNESS_RUNNER",
            "NETWORK_FAULT_RUNNER",
            "SCIENTIFIC_RUNNER",
        ],
        "campaign_id": "campaign-02",
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "role_identity_ids": {
            "EXACTNESS_RUNNER": exactness_id,
            "NETWORK_FAULT_RUNNER": network_id,
            "SCIENTIFIC_RUNNER": scientific["content_id"],
        },
        "schema_version": "1.0.0",
        "source_commit": QUALIFIED_SOURCE,
        "source_tree": QUALIFIED_TREE,
        "type_name": "CAMPAIGN02_MULTI_ROLE_RUNNER_IDENTITY",
    }
    multi_role_id = object_id(multi_role, b"deltareduce.010.campaign02-multi-role-runner.v1\0")
    analyzer = {
        "content_id": CAMPAIGN02_STAGE_GATE_ANALYZER_ID,
        "source_id": source_artifact_id(
            exact, "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py"
        ),
    }
    native = {
        "content_id": object_id(
            {
                "abi_source_id": source_artifact_id(
                    exact, "delta-ffi/src/certificate_chain_abi.cpp"
                ),
                "core_verifier_id": source_artifact_id(
                    exact, "delta-core-cpp/src/certificates/verifier.cpp"
                ),
                "source_commit": QUALIFIED_SOURCE,
                "source_tree": QUALIFIED_TREE,
                "type_name": "CAMPAIGN02_NATIVE_FEATURE008_VERIFIER_IDENTITY",
            }
        ),
        "source_ids": [
            source_artifact_id(exact, "delta-core-cpp/src/certificates/verifier.cpp"),
            source_artifact_id(exact, "delta-ffi/src/certificate_chain_abi.cpp"),
        ],
    }
    return {
        "campaign_id": "campaign-02",
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "identities": {
            "evaluation_runner": evaluation,
            "exactness_runner": {"content_id": exactness_id, "value": exactness},
            "multi_role_runner": {"content_id": multi_role_id, "value": multi_role},
            "native_feature008_verifier": native,
            "network_fault_runner": {"content_id": network_id, "value": network},
            "observation_writer": writer,
            "scientific_runner": scientific,
            "signed_stage_authorization_verifier": {
                "content_id": object_id(
                    {
                        "purpose": "SIGNED_STAGE_AUTHORIZATION_VERIFIER",
                        "source_id": analyzer["source_id"],
                    }
                ),
                "source_id": analyzer["source_id"],
            },
            "stage_gate_analyzer": analyzer,
            "typed_gate_receipt_verifier": {
                "content_id": object_id(
                    {
                        "purpose": "TYPED_STAGE_GATE_RECEIPT_VERIFIER",
                        "source_id": analyzer["source_id"],
                    }
                ),
                "source_id": analyzer["source_id"],
            },
        },
        "schema_version": "1.0.0",
        "source_commit": QUALIFIED_SOURCE,
        "source_tree": QUALIFIED_TREE,
        "type_name": "CAMPAIGN02_STAGE_EXECUTION_IDENTITIES",
    }


def arms_document(workload_id: str) -> dict[str, object]:
    predecessor = tracked_json(REMEDIATION_MERGE, "configs/benchmark/arms-v1.json")
    arms = copy.deepcopy(predecessor.get("arms"))
    require(isinstance(arms, list) and len(arms) == 5, "PREDECESSOR_ARMS_INVALID")
    for arm in arms:
        require(isinstance(arm, dict), "PREDECESSOR_ARM_INVALID")
        arm["workload_identity"] = workload_id
    return {
        "arms": arms,
        "campaign_id": "campaign-02",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": "2.0.0",
        "type_name": "CAMPAIGN02_PRIMARY_ARMS",
    }


def arm_specs(document: dict[str, object]) -> tuple[ArmSpec, ...]:
    values = document.get("arms")
    require(isinstance(values, list), "ARMS_MISSING")
    result: list[ArmSpec] = []
    for value in values:
        require(isinstance(value, dict), "ARM_INVALID")
        result.append(
            ArmSpec(
                content_id=object_id(value),
                arm_id=str(value.get("arm_id")),
                kind=str(value.get("kind")),
                deployment_profile=str(value.get("deployment_profile")),
                mandatory=value.get("mandatory") is True,
                workload_identity=str(value.get("workload_identity")),
                runtime_profile_id=object_id(
                    {"deployment_profile": value.get("deployment_profile")}
                ),
                topology=str(value.get("topology")),
            )
        )
    return tuple(result)


def evaluator_metadata(exact: dict[str, object]) -> tuple[tuple[str, ...], ...]:
    implementations = exact.get("evaluator_implementations")
    require(isinstance(implementations, dict), "EVALUATOR_IMPLEMENTATIONS_MISSING")
    dataset_ids: list[str] = []
    profile_ids: list[str] = []
    implementation_ids: list[str] = []
    for name in ("wikitext", "lambada", "hellaswag"):
        qualified = implementations.get(name)
        require(isinstance(qualified, dict), f"EVALUATOR_MISSING:{name}")
        manifest = qualified.get("manifest")
        require(isinstance(manifest, dict), f"EVALUATOR_MANIFEST_MISSING:{name}")
        profile = tracked_json(
            QUALIFIED_SOURCE, f"configs/benchmark/campaign-02/evaluators/{name}-v1.json"
        )
        require(
            profile.get("dataset_id") == manifest.get("dataset_id", profile.get("dataset_id"))
            and profile.get("tokenizer_id")
            == tracked_json(
                QUALIFIED_SOURCE,
                "configs/benchmark/campaign-02/evaluators/wikitext-v1.json",
            ).get("tokenizer_id"),
            f"EVALUATOR_PROFILE_DRIFT:{name}",
        )
        dataset_ids.append(str(profile["dataset_id"]))
        profile_ids.append(str(manifest["profile_id"]))
        implementation_ids.append(str(qualified["implementation_id"]))
    return tuple(dataset_ids), tuple(profile_ids), tuple(implementation_ids)


def dataset_manifest(exact: dict[str, object]) -> dict[str, object]:
    dataset_ids, profile_ids, implementation_ids = evaluator_metadata(exact)
    return {
        "campaign_id": "campaign-02",
        "datasets": [
            {
                "dataset_id": dataset_id,
                "evaluation_implementation_id": implementation_id,
                "evaluation_profile_id": profile_id,
            }
            for dataset_id, profile_id, implementation_id in zip(
                dataset_ids, profile_ids, implementation_ids, strict=True
            )
        ],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": "1.0.0",
        "source_commit": QUALIFIED_SOURCE,
        "source_tree": QUALIFIED_TREE,
        "type_name": "CAMPAIGN02_DATASET_EVALUATION_MANIFEST",
    }


def metrics_document(exact: dict[str, object], identities: dict[str, object]) -> dict[str, object]:
    predecessor = tracked_json(REMEDIATION_MERGE, "configs/benchmark/metrics-v1.json")
    metrics = copy.deepcopy(predecessor.get("metrics"))
    require(isinstance(metrics, list) and len(metrics) == 9, "PREDECESSOR_METRICS_INVALID")
    _, _, evaluator_ids = evaluator_metadata(exact)
    identity_values = identities.get("identities")
    require(isinstance(identity_values, dict), "STAGE_IDENTITIES_MISSING")

    def identity_id(name: str) -> str:
        value = identity_values.get(name)
        require(isinstance(value, dict), f"STAGE_IDENTITY_MISSING:{name}")
        content_id = value.get("content_id")
        require(isinstance(content_id, str), f"STAGE_IDENTITY_ID_INVALID:{name}")
        return content_id

    mapping = {
        "protocol_exactness": identity_id("native_feature008_verifier"),
        "validation_loss_micro": evaluator_ids[0],
        "downstream_lambada_accuracy_ppm": evaluator_ids[1],
        "post_training_hellaswag_accuracy_ppm": evaluator_ids[2],
        "per_domain_wikitext_loss_micro": evaluator_ids[0],
        "network_share_ppm": identity_id("network_fault_runner"),
        "bytes_per_token": identity_id("network_fault_runner"),
        "gpu_utilization_ppm": identity_id("scientific_runner"),
        "resilience_exact": identity_id("stage_gate_analyzer"),
    }
    for metric in metrics:
        require(isinstance(metric, dict), "PREDECESSOR_METRIC_INVALID")
        metric_id = metric.get("metric_id")
        require(isinstance(metric_id, str) and metric_id in mapping, "METRIC_ID_UNKNOWN")
        metric["implementation_id"] = mapping[metric_id]
    return {
        "campaign_id": "campaign-02",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "metrics": metrics,
        "schema_version": "2.0.0",
        "type_name": "CAMPAIGN02_PRIMARY_METRICS",
    }


def runtime_lineage(
    exact: dict[str, object],
    identities: dict[str, object],
    arms: tuple[ArmSpec, ...],
) -> QualifiedRuntimeLineage:
    primary = tracked_json(REMEDIATION_MERGE, "configs/benchmark/primary.yaml")
    gpu = exact.get("gpu_environment")
    identity_values = identities.get("identities")
    require(isinstance(gpu, dict), "GPU_ENVIRONMENT_MISSING")
    require(isinstance(identity_values, dict), "STAGE_IDENTITIES_MISSING")

    def identity_id(name: str) -> str:
        value = identity_values.get(name)
        require(isinstance(value, dict), f"STAGE_IDENTITY_MISSING:{name}")
        content_id = value.get("content_id")
        require(isinstance(content_id, str), f"STAGE_IDENTITY_ID_INVALID:{name}")
        return content_id

    validator_ids = (
        "runtime-validator-0",
        "runtime-validator-1",
        "runtime-validator-2",
        "runtime-validator-3",
    )
    validator_epoch_id = object_id(
        {
            "campaign_id": "campaign-02",
            "source_commit": QUALIFIED_SOURCE,
            "type_name": "CAMPAIGN02_RUNTIME_VALIDATOR_EPOCH_IDENTITY",
            "validator_ids": list(validator_ids),
        }
    )
    parameter_schema_id = tracked_id(QUALIFIED_SOURCE, "configs/worker/smoke-parameter-schema.json")
    seeds = tuple(int(item) for item in primary["seeds"])
    bindings = tuple(
        sorted(
            (
                CertifiedPlanBinding(
                    gate_stage=gate_stage,
                    arm_id=arm.content_id,
                    arm_name=arm.arm_id,
                    seed=seed,
                    repetition=repetition,
                    policy=CertifiedRoundPolicy(
                        round_id=expected_round_id(gate_stage, arm.arm_id, seed, repetition),
                        height=1,
                        view=0,
                        round_config_id=object_id(
                            {
                                "arm_id": arm.content_id,
                                "gate_stage": gate_stage,
                                "repetition": repetition,
                                "seed": seed,
                                "source_commit": QUALIFIED_SOURCE,
                                "type_name": "CAMPAIGN02_CERTIFIED_ROUND_CONFIG_IDENTITY",
                            }
                        ),
                        validator_epoch_id=validator_epoch_id,
                        parameter_schema_id=parameter_schema_id,
                        arithmetic_profile_id=str(primary["fixedpoint_profile_id"]),
                        accumulator_proof_id=str(primary["theorem_build_id"]),
                        apply_arithmetic_profile_id=str(primary["apply_profile_id"]),
                        validator_ids=validator_ids,
                        quorum_threshold=3,
                        required_shards=(ParameterShardKey("wikitext-en", "adapter-shard-0"),),
                    ),
                )
                for gate_stage in CAMPAIGN02_GATE_STAGES
                for arm in arms
                if arm.kind == "CERTIFIED_QLORA"
                for repetition, seed in enumerate(seeds, start=1)
            ),
            key=lambda item: (
                item.gate_stage,
                item.arm_name,
                item.repetition,
                item.seed,
            ),
        )
    )
    dataset_ids, profile_ids, implementation_ids = evaluator_metadata(exact)
    tokenizer_id = str(
        tracked_json(
            QUALIFIED_SOURCE,
            "configs/benchmark/campaign-02/evaluators/wikitext-v1.json",
        )["tokenizer_id"]
    )
    return QualifiedRuntimeLineage(
        source_commit=QUALIFIED_SOURCE,
        source_tree=QUALIFIED_TREE,
        environment_id=str(gpu["environment_id"]),
        image_id=str(gpu["image_id"]),
        hardware_id=str(gpu["hardware_id"]),
        runner_id=identity_id("multi_role_runner"),
        evaluation_runner_id=identity_id("evaluation_runner"),
        writer_id=identity_id("observation_writer"),
        model_id=str(primary["base_model_id"]),
        parent_checkpoint_id=str(primary["base_model_id"]),
        tokenizer_id=tokenizer_id,
        dataset_ids=dataset_ids,
        evaluation_profile_ids=profile_ids,
        evaluation_implementation_ids=implementation_ids,
        certified_plan_bindings=bindings,
    )


def definition_document(
    exact: dict[str, object],
    arms: dict[str, object],
    datasets: dict[str, object],
    metrics: dict[str, object],
    lineage: QualifiedRuntimeLineage,
) -> dict[str, object]:
    value = copy.deepcopy(tracked_json(REMEDIATION_MERGE, "configs/benchmark/primary.yaml"))
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    domain_manifest = load_domain_manifest(CONFIG / "domain-manifest-v1.json")
    ticket_plan = load_ticket_plan(CONFIG / "ticket-plan-v1.json", workload, domain_manifest)
    gpu = exact.get("gpu_environment")
    require(isinstance(gpu, dict), "GPU_ENVIRONMENT_MISSING")
    dependency_paths = (
        "delta-core-cpp/toolchain/build-tools.lock.json",
        "delta-core-cpp/toolchain/compilers.lock.json",
        "delta-node-java/distribution-dependencies.lock.json",
        "configs/benchmark/campaign-02/gpu-environment-lock-v1.json",
        "uv.lock",
    )
    value.update(
        {
            "B": workload.tokens_per_ticket,
            "H": workload.optimizer_steps_per_ticket,
            "abi_descriptor_id": tracked_id(
                QUALIFIED_SOURCE, "delta-protocol/schemas/003/delta-abi-v1.json"
            ),
            "arm_ids": [object_id(item) for item in arms["arms"]],
            "campaign_id": "campaign-02",
            "compatibility_policy_id": str(gpu["environment_id"]),
            "compiler_profile_id": tracked_id(
                QUALIFIED_SOURCE, "delta-core-cpp/toolchain/compilers.lock.json"
            ),
            "dataset_manifest_id": object_id(datasets),
            "dependency_lock_ids": [
                tracked_id(QUALIFIED_SOURCE, path) for path in dependency_paths
            ],
            "deployment_policy_id": tracked_id(
                QUALIFIED_SOURCE,
                "configs/benchmark/campaign-02/runner-policy-v1.json",
            ),
            "domain_manifest_id": domain_manifest.content_id,
            "evaluation_ids": list(lineage.evaluation_implementation_ids),
            "fixedpoint_profile_id": tracked_id(
                QUALIFIED_SOURCE,
                "delta-core-cpp/toolchain/fixedpoint-targets.lock.json",
            ),
            "formal_trace_schema_id": tracked_id(
                QUALIFIED_SOURCE, "formal/schemas/formal-trace.schema.json"
            ),
            "image_id": lineage.image_id,
            "jdk_profile_id": tracked_id(QUALIFIED_SOURCE, "delta-node-java/toolchains.toml"),
            "metric_definitions": metrics["metrics"],
            "native_build_id": lineage.content_id,
            "netty_profile_id": tracked_id(
                QUALIFIED_SOURCE,
                "delta-node-java/distribution-dependencies.lock.json",
            ),
            "physical_profile_id": str(gpu["environment_id"]),
            "protocol_registry_id": tracked_id(QUALIFIED_SOURCE, "delta-protocol/registry.json"),
            "python_profile_id": str(gpu["lock_id"]),
            "qualified_runtime_lineage_id": lineage.content_id,
            "schema_version": "2.0.0",
            "sbom_id": str(gpu["sbom_id"]),
            "source_commit": QUALIFIED_SOURCE,
            "source_tree": QUALIFIED_TREE,
            "ticket_plan_id": ticket_plan.content_id,
            "tokenizer_id": lineage.tokenizer_id,
            "workload_contract_id": workload.content_id,
        }
    )
    return value


def construction_authorization() -> dict[str, object]:
    return {
        "approved_task_ids": ["C2-022"],
        "definition_construction_authorized": True,
        "execution_authorization": {
            "c2_024_authorized": False,
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
            "pull_request": 17,
            "terminal_head": REMEDIATION_HEAD,
        },
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "schema_version": "1.0.0",
        "status": "APPROVED_FOR_MERGE_AND_C2_022_ONLY",
        "type_name": "CAMPAIGN02_DEFINITION_CONSTRUCTION_AUTHORIZATION",
    }


def methodology_diff(
    definition: BenchmarkDefinition,
    metrics: dict[str, object],
    identities: dict[str, object],
) -> dict[str, object]:
    predecessor_value = tracked_json(REMEDIATION_MERGE, "configs/benchmark/primary.yaml")
    predecessor = BenchmarkDefinition.from_dict(predecessor_value)
    current_metrics = metrics.get("metrics")
    require(isinstance(current_metrics, list), "METRICS_MISSING")
    require(definition.raw["metric_definitions"] == current_metrics, "METRIC_BINDING_DRIFT")
    scientific_metric_fields = (
        "aggregation",
        "direction",
        "mandatory",
        "metric_id",
        "missing_run_rule",
        "outlier_rule",
        "pass_threshold",
        "repetitions",
        "statistical_method",
        "unit",
    )
    old_metrics = predecessor_value.get("metric_definitions")
    require(isinstance(old_metrics, list), "PREDECESSOR_METRICS_MISSING")
    require(
        [{field: metric[field] for field in scientific_metric_fields} for metric in old_metrics]
        == [
            {field: metric[field] for field in scientific_metric_fields}
            for metric in current_metrics
        ],
        "METRIC_SCIENTIFIC_DRIFT",
    )
    unchanged_fields = (
        "B",
        "H",
        "apply_profile_id",
        "base_model_id",
        "decision_function",
        "exclusions",
        "fault_profile_ids",
        "isolation_policy",
        "license_policy_id",
        "missing_run_policy",
        "model_mode",
        "network_profile_ids",
        "optimizer_profile_id",
        "pi_d",
        "primary",
        "qlora_profile_id",
        "refinement_evidence_ids",
        "repetitions",
        "robust_profile_id",
        "seeds",
        "theorem_build_id",
    )
    for field in unchanged_fields:
        require(
            predecessor_value[field] == definition.raw[field],
            f"SCIENTIFIC_METHOD_DRIFT:{field}",
        )
    identity_values = identities.get("identities")
    require(isinstance(identity_values, dict), "STAGE_IDENTITIES_MISSING")
    required_identity_ids = {
        name: value["content_id"]
        for name, value in identity_values.items()
        if isinstance(value, dict) and isinstance(value.get("content_id"), str)
    }
    return {
        "campaign_transition": "CAMPAIGN_01_TO_CAMPAIGN_02",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "predecessor_definition_id": predecessor.content_id,
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
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "replacement_definition_id": definition.content_id,
        "required_stage_execution_identity_ids": required_identity_ids,
        "schema_version": "2.0.0",
        "scientific_observations_used_to_change_methodology": 0,
        "status": "PASS",
        "type_name": "CAMPAIGN02_METHODOLOGY_DIFF",
        "unchanged_scientific_fields": list(unchanged_fields),
    }


def readiness(
    definition: BenchmarkDefinition,
    lineage: QualifiedRuntimeLineage,
    identities: dict[str, object],
    authorization: dict[str, object],
    diff: dict[str, object],
) -> dict[str, object]:
    return {
        "authorization": authorization["execution_authorization"],
        "benchmark_definition_id": definition.content_id,
        "c2_023": {
            "definition_attestation": "ABSENT",
            "independent_votes_present": 0,
            "private_keys_committed": False,
            "status": "AWAITING_EXTERNAL_VALIDATOR_SET_AND_SIGNATURES",
        },
        "c2_024_status": "NOT_AUTHORIZED",
        "definition_construction_authorization_id": object_id(authorization),
        "definition_created": True,
        "execution_authorization": "ABSENT",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "methodology_diff_id": object_id(diff),
        "next_required_gate": "C2_023_INDEPENDENT_DEFINITION_SIGNATURES",
        "plan_catalog": {
            "authoritative_catalog_created": False,
            "reason": "VERIFIED_DEFINITION_ATTESTATION_REQUIRED",
            "status": "NOT_CONSTRUCTED",
        },
        "primary_observations_created": 0,
        "qualified_runtime_lineage_id": lineage.content_id,
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "schema_version": "2.0.0",
        "stage_execution_identities_id": object_id(identities),
        "status": "IMMUTABLE_DEFINITION_CREATED_AWAITING_C2_023",
        "type_name": "CAMPAIGN02_DEFINITION_READINESS",
    }


def validate_package(
    definition: BenchmarkDefinition,
    lineage: QualifiedRuntimeLineage,
    identities: dict[str, object],
    arms: tuple[ArmSpec, ...],
) -> None:
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    domain_manifest = load_domain_manifest(CONFIG / "domain-manifest-v1.json")
    ticket_plan = load_ticket_plan(CONFIG / "ticket-plan-v1.json", workload, domain_manifest)
    require(
        definition.campaign_id == "campaign-02"
        and definition.raw["schema_version"] == "2.0.0"
        and definition.primary,
        "DEFINITION_V2_REQUIRED",
    )
    require(
        definition.B == workload.tokens_per_ticket
        and definition.H == workload.optimizer_steps_per_ticket
        and definition.workload_contract_id == workload.content_id
        and definition.raw["domain_manifest_id"] == domain_manifest.content_id
        and definition.ticket_plan_id == ticket_plan.content_id,
        "DEFINITION_WORKLOAD_BINDING_INVALID",
    )
    require(
        definition.source_commit == lineage.source_commit == QUALIFIED_SOURCE
        and definition.source_tree == lineage.source_tree == QUALIFIED_TREE
        and definition.qualified_runtime_lineage_id == lineage.content_id
        and definition.raw["image_id"] == lineage.image_id
        and definition.base_model_id == lineage.parent_checkpoint_id
        and definition.raw["tokenizer_id"] == lineage.tokenizer_id
        and definition.evaluation_ids == lineage.evaluation_implementation_ids,
        "DEFINITION_RUNTIME_LINEAGE_INVALID",
    )
    require(
        tuple(item.content_id for item in arms) == definition.arm_ids
        and len(arms) == 5
        and all(item.mandatory and item.workload_identity == workload.content_id for item in arms),
        "DEFINITION_ARM_BINDING_INVALID",
    )
    identity_values = identities.get("identities")
    require(isinstance(identity_values, dict), "STAGE_IDENTITIES_MISSING")
    multi_role = identity_values.get("multi_role_runner")
    require(isinstance(multi_role, dict), "MULTI_ROLE_IDENTITY_MISSING")
    require(
        lineage.runner_id == multi_role.get("content_id")
        and len(lineage.certified_plan_bindings) == 36
        and len(
            {
                (
                    item.policy.round_id,
                    item.policy.height,
                    item.policy.view,
                    item.policy.validator_epoch_id,
                )
                for item in lineage.certified_plan_bindings
            }
        )
        == 36,
        "STAGE_RUNTIME_IDENTITY_BINDING_INVALID",
    )


def documents() -> dict[Path, tuple[dict[str, object], bool]]:
    exact, _hardware = qualification()
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    arms = arms_document(workload.content_id)
    arms_values = arm_specs(arms)
    identities = component_identities(exact)
    datasets = dataset_manifest(exact)
    metrics = metrics_document(exact, identities)
    lineage = runtime_lineage(exact, identities, arms_values)
    definition_value = definition_document(exact, arms, datasets, metrics, lineage)
    definition = BenchmarkDefinition.from_dict(definition_value)
    require(definition.content_id not in FORBIDDEN_DEFINITION_IDS, "DEFINITION_FORBIDDEN")
    validate_package(definition, lineage, identities, arms_values)
    authorization = construction_authorization()
    diff = methodology_diff(definition, metrics, identities)
    ready = readiness(definition, lineage, identities, authorization, diff)
    return {
        ARMS_PATH: (arms, False),
        DATASETS_PATH: (datasets, True),
        METRICS_PATH: (metrics, True),
        IDENTITIES_PATH: (identities, True),
        LINEAGE_PATH: (lineage.document, True),
        DEFINITION_PATH: (definition.raw, True),
        AUTHORIZATION_PATH: (authorization, True),
        METHODOLOGY_PATH: (diff, True),
        READINESS_PATH: (ready, True),
    }


def expected_outputs() -> dict[Path, bytes]:
    return {
        path: canonical_output(value, newline=newline)
        for path, (value, newline) in documents().items()
    }


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)


def check_outputs() -> None:
    for path, expected in expected_outputs().items():
        require(path.is_file() and path.read_bytes() == expected, f"OUTPUT_DRIFT:{path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if arguments.write:
        write_outputs()
    else:
        check_outputs()
    definition = BenchmarkDefinition.from_dict(json.loads(DEFINITION_PATH.read_bytes()))
    print(
        canonical_json_bytes(
            {
                "definition_id": definition.content_id,
                "independent_votes_present": 0,
                "output_count": len(expected_outputs()),
                "primary_execution_authorized": False,
                "status": "PASS",
            }
        ).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
