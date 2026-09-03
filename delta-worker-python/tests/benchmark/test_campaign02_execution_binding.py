from __future__ import annotations

import base64
import copy
import importlib.util
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.arms import ArmSpec
from deltatorrent.benchmark.campaign02 import (
    CAMPAIGN02_GATE_STAGES,
    CAMPAIGN02_STAGE_TASK_IDS,
    CampaignExecutionPlan,
    CertifiedRoundPolicy,
    ParameterShardKey,
    TicketAllocation,
    authorize_execution_class,
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.campaign02_binding import (
    Campaign02BindingError,
    Campaign02PlanCatalog,
    CertifiedPlanBinding,
    QualifiedRuntimeLineage,
    compile_campaign02_execution_set,
    compile_campaign02_plan_catalog,
    expected_round_id,
)
from deltatorrent.benchmark.campaign02_bootstrap import (
    BootstrapRuntimeProvenance,
    BootstrapValidatorSet,
    SignedBootstrapMappingVote,
    WorkflowBootstrapMapping,
    WorkflowRegistrationReceipt,
    verify_bootstrap_mapping,
)
from deltatorrent.benchmark.campaign02_exactness import run_stage_a
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.campaign02_network_fault import Campaign02NetworkFaultRunner
from deltatorrent.benchmark.campaign02_stage_a_evidence import (
    JAVA_MARKERS,
    NATIVE_TESTS,
    StageAEvidenceError,
    verify_stage_a_artifacts,
)
from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredStageCRuntimeBoundary,
    RuntimeArtifact,
)
from deltatorrent.benchmark.campaign02_stage_execution import (
    Campaign02StageGateFinalizer,
    StagePlanEvidence,
    validate_stage_admission_for_test,
    verify_bound_stage_gate_finalizer,
)
from deltatorrent.benchmark.definition import BenchmarkDefinition, load_definition
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    SignedDefinitionVote,
    VerifiedDefinitionAttestation,
    create_definition_vote,
    finalize_definition_attestation,
)
from deltatorrent.benchmark.measured_runner import (
    ComponentIdentity,
    PrimaryScientificRunner,
    RawArtifact,
    ReferenceRoundMeasurement,
    RunHandle,
    TicketContributionMeasurement,
)
from deltatorrent.benchmark.primary import ExecutionPlan, PrimaryRunError, adapter_for
from deltatorrent.benchmark.stage_authorization import (
    SignedStageAuthorizationVote,
    StageAuthorizationDocument,
    StageAuthorizationProof,
    StageAuthorizationValidatorSet,
    StageGateReceipt,
    create_stage_authorization_vote,
    finalize_stage_authorization_attestation,
)
from deltatorrent.cli.main import main
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/benchmark/campaign-02"
FIXTURES = ROOT / "delta-worker-python/tests/fixtures/benchmark"
NOW = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _id(label: str) -> str:
    return sha256_content_id(label.encode())


def _arms(workload_id: str) -> tuple[ArmSpec, ...]:
    values = (
        ("scientific-reference", "SCIENTIFIC_REFERENCE", "PYTHON", "SINGLE_NODE_REFERENCE"),
        ("flat-embedded", "CERTIFIED_QLORA", "EMBEDDED_FFM", "FLAT_BFT"),
        (
            "hierarchy-embedded",
            "CERTIFIED_QLORA",
            "EMBEDDED_FFM",
            "HIERARCHICAL_BFT",
        ),
        ("flat-sidecar", "CERTIFIED_QLORA", "ISOLATED_SIDECAR", "FLAT_BFT"),
        (
            "hierarchy-sidecar",
            "CERTIFIED_QLORA",
            "ISOLATED_SIDECAR",
            "HIERARCHICAL_BFT",
        ),
    )
    result: list[ArmSpec] = []
    for arm_name, kind, deployment, topology in values:
        document = {
            "allowed_differences": ["arithmetic", "deployment_profile", "topology"],
            "arm_id": arm_name,
            "deployment_profile": deployment,
            "kind": kind,
            "mandatory": True,
            "topology": topology,
            "workload_identity": workload_id,
        }
        result.append(
            ArmSpec(
                content_id=sha256_content_id(canonical_json_bytes(document)),
                arm_id=arm_name,
                kind=kind,
                deployment_profile=deployment,
                mandatory=True,
                workload_identity=workload_id,
                runtime_profile_id=_id(f"runtime:{deployment}:{topology}"),
                topology=topology,
            )
        )
    return tuple(result)


def _policy(gate_stage: str, arm: ArmSpec, seed: int, repetition: int) -> CertifiedRoundPolicy:
    return CertifiedRoundPolicy(
        round_id=expected_round_id(gate_stage, arm.arm_id, seed, repetition),
        height=1,
        view=0,
        round_config_id=_id(f"round-config:{gate_stage}:{arm.arm_id}:{seed}"),
        validator_epoch_id=_id("validator-epoch"),
        parameter_schema_id=_id("parameter-schema"),
        arithmetic_profile_id=_id("arithmetic-profile"),
        accumulator_proof_id=_id("accumulator-proof"),
        apply_arithmetic_profile_id=_id("apply-profile"),
        validator_ids=("validator-0", "validator-1", "validator-2", "validator-3"),
        quorum_threshold=3,
        required_shards=(ParameterShardKey("wikitext-en", "adapter-shard-0"),),
    )


def _component_identity(component: str) -> ComponentIdentity:
    return ComponentIdentity(
        component=component,
        source_commit="a" * 40,
        source_tree="b" * 40,
        executable_hashes=((f"{component}.py", _id(f"source:{component}")),),
        environment_id=_id("environment"),
        image_id=_id("image"),
        hardware_compatibility_class_id=_id("hardware-class"),
        model_data_staging_policy_id=_id("staging"),
        timeout_policy_id=_id("timeout"),
        output_schema_ids=(_id(f"schema:{component}"),),
        create_only_store_policy_id=_id("create-only"),
    )


def _stage_identity_manifest() -> StageExecutionIdentityManifest:
    scientific = _component_identity("PRIMARY_SCIENTIFIC_RUNNER")
    evaluation = _component_identity("PRIMARY_EVALUATION_RUNNER")
    writer = _component_identity("PRIMARY_OBSERVATION_WRITER")

    def hashes(*paths: str) -> list[dict[str, str]]:
        return [
            {"content_id": sha256_content_id((ROOT / path).read_bytes()), "path": path}
            for path in paths
        ]

    def implementation_id(value: dict[str, object]) -> str:
        implementation = {
            "entrypoints": value.get("entrypoints"),
            "executable_hashes": value.get("executable_hashes"),
            "workflow_hashes": value.get("workflow_hashes"),
        }
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-implementation.v1\0"
            + canonical_json_bytes(implementation)
        )

    exactness: dict[str, object] = {
        "allowed_role": "EXACTNESS_RUNNER",
        "entrypoints": ["deltatorrent.benchmark.campaign02_exactness.run_stage_a"],
        "environment_id": _id("environment"),
        "executable_hashes": hashes(
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_exactness.py"
        ),
        "execution_authorized": False,
        "implementation_class": (
            "deltatorrent.benchmark.campaign02_exactness.Campaign02ExactnessEvidenceRunner"
        ),
        "role": "EXACTNESS_RUNNER",
        "source_class": "MEASURED_CI_WORKFLOW",
        "source_commit": "a" * 40,
        "source_tree": "b" * 40,
        "workflow_default_ref": "refs/heads/main",
        "workflow_hashes": hashes(".github/workflows/benchmark-campaign02-stage-a.yml"),
        "workflow_path": ".github/workflows/benchmark-campaign02-stage-a.yml",
        "workflow_repository": "chartjs333/delta",
    }
    exactness["implementation_id"] = implementation_id(exactness)
    network: dict[str, object] = {
        "allowed_role": "NETWORK_FAULT_RUNNER",
        "entrypoints": ["deltatorrent.benchmark.campaign02_network_fault.run_stage_c"],
        "environment_id": _id("environment"),
        "executable_hashes": hashes(
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py"
        ),
        "execution_authorized": False,
        "implementation_class": (
            "deltatorrent.benchmark.campaign02_network_fault.Campaign02NetworkFaultRunner"
        ),
        "role": "NETWORK_FAULT_RUNNER",
        "source_class": "MEASURED_HARDWARE",
        "source_commit": "a" * 40,
        "source_tree": "b" * 40,
        "workflow_hashes": [],
    }
    network["implementation_id"] = implementation_id(network)
    domains = {
        "evaluation_runner": "deltareduce.010.primary-component.v1",
        "exactness_runner": "deltareduce.010.campaign02-stage-role-identity.v3",
        "multi_role_runner": "deltareduce.010.campaign02-multi-role-runner.v3",
        "native_feature008_verifier": ("deltareduce.010.campaign02-native-feature008-verifier.v2"),
        "network_fault_runner": "deltareduce.010.campaign02-stage-role-identity.v3",
        "observation_writer": "deltareduce.010.primary-component.v1",
        "scientific_runner": "deltareduce.010.primary-component.v1",
        "signed_stage_authorization_verifier": (
            "deltareduce.010.campaign02-signed-stage-authorization-verifier.v2"
        ),
        "stage_gate_analyzer": "deltareduce.010.campaign02-stage-gate-analyzer.v3",
        "typed_gate_receipt_verifier": (
            "deltareduce.010.campaign02-typed-stage-gate-receipt-verifier.v2"
        ),
    }

    def item(name: str, value: dict[str, object]) -> dict[str, object]:
        domain = domains[name]
        return {
            "content_id": sha256_content_id(domain.encode() + b"\0" + canonical_json_bytes(value)),
            "identity_domain": domain,
            "value": value,
        }

    exactness_item = item("exactness_runner", exactness)
    network_item = item("network_fault_runner", network)
    scientific_item = item("scientific_runner", scientific.document)
    values: dict[str, dict[str, object]] = {
        "evaluation_runner": item("evaluation_runner", evaluation.document),
        "exactness_runner": exactness_item,
        "network_fault_runner": network_item,
        "observation_writer": item("observation_writer", writer.document),
        "scientific_runner": scientific_item,
    }
    multi_role = {
        "execution_authorized": False,
        "role_identity_ids": {
            "EXACTNESS_RUNNER": exactness_item["content_id"],
            "NETWORK_FAULT_RUNNER": network_item["content_id"],
            "SCIENTIFIC_RUNNER": scientific_item["content_id"],
        },
        "source_commit": "a" * 40,
        "source_tree": "b" * 40,
        "type_name": "CAMPAIGN02_MULTI_ROLE_RUNNER_IDENTITY",
    }
    values["multi_role_runner"] = item("multi_role_runner", multi_role)
    for name in (
        "native_feature008_verifier",
        "signed_stage_authorization_verifier",
        "stage_gate_analyzer",
        "typed_gate_receipt_verifier",
    ):
        identity_value: dict[str, object] = {
            "purpose": name.upper(),
            "source_commit": "a" * 40,
            "source_tree": "b" * 40,
        }
        if name == "stage_gate_analyzer":
            identity_value.update(
                {
                    "component": "CAMPAIGN02_STAGE_GATE_ANALYZER",
                    "environment_id": _id("environment"),
                    "entrypoint": (
                        "deltatorrent.benchmark.campaign02_stage_execution.execute_stage"
                    ),
                    "entrypoints": [
                        "deltatorrent.benchmark.campaign02_stage_execution.execute_stage"
                    ],
                    "executable_hashes": hashes(
                        "delta-worker-python/src/deltatorrent/benchmark/"
                        "campaign02_stage_execution.py"
                    ),
                    "execution_authorized": False,
                    "implementation_class": (
                        "deltatorrent.benchmark.campaign02_stage_execution."
                        "Campaign02StageGateFinalizer"
                    ),
                    "source_class": "MEASURED_CONTROL_PLANE",
                    "workflow_default_ref": "refs/heads/main",
                    "workflow_hashes": hashes(".github/workflows/benchmark-campaign02-stage-a.yml"),
                    "workflow_path": ".github/workflows/benchmark-campaign02-stage-a.yml",
                    "workflow_repository": "chartjs333/delta",
                }
            )
            identity_value["implementation_id"] = implementation_id(identity_value)
        values[name] = item(
            name,
            identity_value,
        )
    return StageExecutionIdentityManifest.from_dict(
        {
            "campaign_id": "campaign-02",
            "execution_authorized": False,
            "formal_semantics_id": (
                "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
            ),
            "identities": values,
            "schema_version": "3.0.0",
            "source_commit": "a" * 40,
            "source_tree": "b" * 40,
            "type_name": "CAMPAIGN02_STAGE_EXECUTION_IDENTITIES",
        }
    )


def _stage_identity_manifest_v4() -> StageExecutionIdentityManifest:
    raw = copy.deepcopy(_stage_identity_manifest().raw)

    def hashes(paths: set[str]) -> list[dict[str, str]]:
        return [
            {"content_id": sha256_content_id((ROOT / path).read_bytes()), "path": path}
            for path in sorted(paths)
        ]

    def implementation_id(value: dict[str, object]) -> str:
        implementation = {
            "entrypoints": value.get("entrypoints"),
            "executable_hashes": value.get("executable_hashes"),
            "workflow_hashes": value.get("workflow_hashes"),
        }
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-implementation.v1\0"
            + canonical_json_bytes(implementation)
        )

    def rewrap(name: str, domain: str, value: dict[str, object]) -> dict[str, object]:
        return {
            "content_id": sha256_content_id(domain.encode() + b"\0" + canonical_json_bytes(value)),
            "identity_domain": domain,
            "value": value,
        }

    identities = raw["identities"]
    assert isinstance(identities, dict)
    exactness = copy.deepcopy(identities["exactness_runner"]["value"])
    network = copy.deepcopy(identities["network_fault_runner"]["value"])
    analyzer = copy.deepcopy(identities["stage_gate_analyzer"]["value"])
    assert isinstance(exactness, dict) and isinstance(network, dict) and isinstance(analyzer, dict)
    exactness_item = rewrap(
        "exactness_runner", "deltareduce.010.campaign02-stage-role-identity.v4", exactness
    )
    stage_c_paths = {
        ".github/workflows/benchmark-campaign02-stage-c-measured.yml",
        "CMakeLists.txt",
        "configs/benchmark/faults-v1.json",
        "configs/benchmark/networks-v1.json",
        "delta-node-java/distribution-dependencies.lock.json",
        "delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkContracts.java",
        "delta-node-java/src/main/java/io/deltareduce/node/benchmark/MeasuredStageCTransport.java",
        "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NettyMetricsCollector.java",
        "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NetworkFaultController.java",
        "delta-protocol/schemas/010/campaign-02/benchmark-definition-v5.json",
        "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v2.json",
        "delta-protocol/schemas/010/campaign-02/execution-plan-v6.json",
        "delta-protocol/schemas/010/campaign-02/qualified-runtime-lineage-v5.json",
        "delta-protocol/schemas/010/campaign-02/stage-execution-identities-v4.json",
        "delta-protocol/schemas/010/fault-profile-v1.json",
        "delta-protocol/schemas/010/network-profile-v1.json",
        "delta-runtime-cpp/include/delta/runtime/benchmark.hpp",
        "delta-runtime-cpp/src/benchmark/fault_control.cpp",
        "delta-runtime-cpp/src/benchmark/sidecar_main.cpp",
        "delta-runtime-cpp/src/benchmark/trace_export.cpp",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_binding.py",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_c_runtime.py",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
        "delta-worker-python/src/deltatorrent/benchmark/definition.py",
        "delta-worker-python/src/deltatorrent/benchmark/fault_profiles.py",
        "delta-worker-python/src/deltatorrent/benchmark/network_profiles.py",
        "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py",
        "specs/010-wan-benchmark-and-quality/scripts/run_campaign02_stage_c_conformance.py",
    }
    network.update(
        {
            "executable_hashes": hashes(
                {path for path in stage_c_paths if not path.startswith(".github/")}
            ),
            "image_id": _id("stage-c-image"),
            "java_executable_id": _id("stage-c-java"),
            "native_executable_id": _id("stage-c-native"),
            "netty_artifact_ids": [_id("netty-buffer"), _id("netty-transport")],
            "source_class": "MEASURED_RUNTIME",
            "transport_harness_id": _id("stage-c-harness"),
            "workflow_hashes": hashes(
                {path for path in stage_c_paths if path.startswith(".github/")}
            ),
        }
    )
    network["implementation_id"] = implementation_id(network)
    network_item = rewrap(
        "network_fault_runner",
        "deltareduce.010.campaign02-stage-role-identity.v4",
        network,
    )
    bootstrap_paths = {
        ".github/workflows/benchmark-campaign02-stage-a.yml",
        "delta-protocol/schemas/010/campaign-02/benchmark-definition-v5.json",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_bootstrap.py",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
        "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
        "delta-worker-python/src/deltatorrent/benchmark/definition.py",
        "delta-protocol/schemas/010/campaign-02/stage-workflow-gate-qc-v3.json",
        "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-mapping-v1.json",
        "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-signature-v1.json",
        "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-validator-set-v1.json",
        "delta-protocol/schemas/010/campaign-02/workflow-registration-receipt-v1.json",
        "specs/010-wan-benchmark-and-quality/scripts/campaign02_bootstrap_control.py",
        "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py",
        "specs/010-wan-benchmark-and-quality/scripts/campaign02_stage_a_control.py",
    }
    analyzer.update(
        {
            "executable_hashes": hashes(
                {path for path in bootstrap_paths if not path.startswith(".github/")}
            ),
            "workflow_hashes": hashes(
                {path for path in bootstrap_paths if path.startswith(".github/")}
            ),
        }
    )
    analyzer["implementation_id"] = implementation_id(analyzer)
    analyzer_item = rewrap(
        "stage_gate_analyzer",
        "deltareduce.010.campaign02-stage-gate-analyzer.v4",
        analyzer,
    )
    scientific_item = identities["scientific_runner"]
    multi = copy.deepcopy(identities["multi_role_runner"]["value"])
    multi["role_identity_ids"] = {
        "EXACTNESS_RUNNER": exactness_item["content_id"],
        "NETWORK_FAULT_RUNNER": network_item["content_id"],
        "SCIENTIFIC_RUNNER": scientific_item["content_id"],
    }
    identities.update(
        {
            "exactness_runner": exactness_item,
            "multi_role_runner": rewrap(
                "multi_role_runner",
                "deltareduce.010.campaign02-multi-role-runner.v4",
                multi,
            ),
            "network_fault_runner": network_item,
            "stage_gate_analyzer": analyzer_item,
        }
    )
    raw["schema_version"] = "4.0.0"
    return StageExecutionIdentityManifest.from_dict(raw)


def _validator_set() -> tuple[BenchmarkReviewValidatorSet, tuple[Ed25519PrivateKey, ...]]:
    private_keys = tuple(Ed25519PrivateKey.generate() for _ in range(4))
    validators = []
    for index, private_key in enumerate(private_keys):
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        validators.append(
            {
                "controller_id": f"independent-controller-{index}",
                "key_custody_statement_id": _id(f"custody:{index}"),
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "public_key_id": sha256_content_id(
                    b"deltareduce.010.benchmark-review-key.v1\0" + public_key
                ),
                "signature_algorithm": "ED25519",
                "valid_from": "2026-08-01T00:00:00Z",
                "valid_until": None,
                "validator_id": f"benchmark-validator-{index}",
            }
        )
    return (
        BenchmarkReviewValidatorSet.from_dict(
            {
                "campaign_id": "campaign-02",
                "f_b": 1,
                "formal_semantics_id": (
                    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
                ),
                "purpose": "BENCHMARK_DEFINITION_REVIEW",
                "schema_version": "1.0.0",
                "type_name": "BENCHMARK_REVIEW_VALIDATOR_SET",
                "validators": validators,
            }
        ),
        private_keys,
    )


def _attestation(
    definition_id: str,
) -> tuple[
    VerifiedDefinitionAttestation,
    BenchmarkReviewValidatorSet,
    tuple[SignedDefinitionVote, ...],
]:
    validator_set, private_keys = _validator_set()
    votes = tuple(
        create_definition_vote(
            benchmark_definition_id=definition_id,
            validator_set=validator_set,
            signer_id=f"benchmark-validator-{index}",
            submitted_at=NOW,
            private_key=private_keys[index],
        )
        for index in range(3)
    )
    attestation = finalize_definition_attestation(
        benchmark_definition_id=definition_id,
        validator_set=validator_set,
        votes=votes,
        verified_at=NOW,
    )
    return attestation, validator_set, votes


def _inputs() -> tuple[
    BenchmarkDefinition,
    dict[str, object],
    BenchmarkReviewValidatorSet,
    tuple[SignedDefinitionVote, ...],
    object,
    object,
    object,
    tuple[ArmSpec, ...],
    QualifiedRuntimeLineage,
    StageExecutionIdentityManifest,
]:
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    domain_manifest = load_domain_manifest(CONFIG / "domain-manifest-v1.json")
    ticket_plan = load_ticket_plan(CONFIG / "ticket-plan-v1.json", workload, domain_manifest)
    arms = _arms(workload.content_id)
    seeds = (2026090101, 2026090102, 2026090103)
    bindings = tuple(
        sorted(
            (
                CertifiedPlanBinding(
                    gate_stage,
                    arm.content_id,
                    arm.arm_id,
                    seed,
                    repetition,
                    _policy(gate_stage, arm, seed, repetition),
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
    evaluator_profiles = tuple(
        json.loads((CONFIG / "evaluators" / f"{name}-v1.json").read_bytes())
        for name in ("wikitext", "lambada", "hellaswag")
    )
    stage_identities = _stage_identity_manifest()
    runtime = QualifiedRuntimeLineage(
        source_commit="a" * 40,
        source_tree="b" * 40,
        environment_id=_id("environment"),
        image_id=_id("image"),
        hardware_id=_id("hardware"),
        runner_id=None,
        evaluation_runner_id=stage_identities.identity_id("evaluation_runner"),
        writer_id=stage_identities.identity_id("observation_writer"),
        model_id=_id("base-model"),
        parent_checkpoint_id=_id("base-model"),
        tokenizer_id=str(evaluator_profiles[0]["tokenizer_id"]),
        dataset_ids=tuple(str(item["dataset_id"]) for item in evaluator_profiles),
        evaluation_profile_ids=tuple(_id(f"profile:{index}") for index in range(3)),
        evaluation_implementation_ids=tuple(
            _id(f"implementation:{name}") for name in ("wikitext", "lambada", "hellaswag")
        ),
        certified_plan_bindings=bindings,
        stage_execution_identities_id=stage_identities.content_id,
        exactness_runner_id=stage_identities.identity_id("exactness_runner"),
        scientific_runner_id=stage_identities.identity_id("scientific_runner"),
        network_fault_runner_id=stage_identities.identity_id("network_fault_runner"),
    )
    value = json.loads((ROOT / "configs/benchmark/primary.yaml").read_bytes())
    value.update(
        {
            "B": workload.tokens_per_ticket,
            "H": workload.optimizer_steps_per_ticket,
            "arm_ids": [item.content_id for item in arms],
            "base_model_id": runtime.parent_checkpoint_id,
            "campaign_id": "campaign-02",
            "dataset_manifest_id": _id("campaign02-dataset-manifest"),
            "domain_manifest_id": domain_manifest.content_id,
            "evaluation_ids": list(runtime.evaluation_implementation_ids),
            "image_id": runtime.image_id,
            "native_build_id": _id("native-build"),
            "primary": True,
            "qualified_runtime_lineage_id": runtime.content_id,
            "repetitions": 3,
            "schema_version": "4.0.0",
            "seeds": list(seeds),
            "source_commit": runtime.source_commit,
            "source_tree": runtime.source_tree,
            "ticket_plan_id": ticket_plan.content_id,
            "tokenizer_id": runtime.tokenizer_id,
            "workload_contract_id": workload.content_id,
            "stage_execution_identities_id": stage_identities.content_id,
        }
    )
    for metric in value["metric_definitions"]:
        metric["repetitions"] = 3
    definition = BenchmarkDefinition.from_dict(value)
    attestation, validator_set, votes = _attestation(definition.content_id)
    return (
        definition,
        attestation.document,
        validator_set,
        votes,
        workload,
        domain_manifest,
        ticket_plan,
        arms,
        runtime,
        stage_identities,
    )


def _compile(**updates: object):  # type: ignore[no-untyped-def]
    names = (
        "definition",
        "attestation_document",
        "validator_set",
        "votes",
        "workload",
        "domain_manifest",
        "ticket_plan",
        "arms",
        "runtime_lineage",
        "stage_identities",
    )
    values = dict(zip(names, _inputs(), strict=True))
    values.update(updates)
    return compile_campaign02_plan_catalog(**values)  # type: ignore[arg-type]


def _stage_validator_set() -> tuple[StageAuthorizationValidatorSet, tuple[Ed25519PrivateKey, ...]]:
    definition_validator_set, private_keys = _validator_set()
    return (
        StageAuthorizationValidatorSet.from_dict(
            {
                "campaign_id": "campaign-02",
                "f_b": 1,
                "formal_semantics_id": (
                    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
                ),
                "purpose": "BENCHMARK_STAGE_AUTHORIZATION_REVIEW",
                "schema_version": "1.0.0",
                "type_name": "BENCHMARK_STAGE_AUTHORIZATION_VALIDATOR_SET",
                "validators": [item.document for item in definition_validator_set.validators],
            }
        ),
        private_keys,
    )


def _gate_receipt(
    catalog: Campaign02PlanCatalog,
    completed_stage: str,
    **updates: object,
) -> StageGateReceipt:
    plan = next(item for item in catalog.plans if item.gate_stage == completed_stage)
    value: dict[str, object] = {
        "accepted_plan_ids": list(catalog.plan_ids_for_stage(completed_stage)),
        "benchmark_definition_id": catalog.definition_id,
        "campaign_id": "campaign-02",
        "completed_stage": completed_stage,
        "decision": "PASS",
        "definition_attestation_id": catalog.attestation_id,
        "evidence_root": _id(f"{completed_stage}:evidence"),
        "finalized_at": NOW.isoformat().replace("+00:00", "Z"),
        "formal_semantics_id": (
            "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
        ),
        "gate_analyzer_id": catalog.gate_analyzer_id,
        "gate_qc_id": _id(f"{completed_stage}:gate-qc"),
        "gate_result_id": _id(f"{completed_stage}:gate-result"),
        "plan_catalog_id": catalog.content_id,
        "qualified_runtime_lineage_id": catalog.runtime_lineage_id,
        "required_plan_ids": list(catalog.plan_ids_for_stage(completed_stage)),
        "runner_id": plan.runner_id,
        "schema_version": "2.0.0",
        "source_commit": plan.source_commit,
        "source_tree": plan.source_tree,
        "stage_authorization_attestation_id": _id(
            f"{completed_stage}:stage-authorization-attestation"
        ),
        "type_name": "BENCHMARK_STAGE_GATE_RECEIPT",
    }
    value.update(updates)
    return StageGateReceipt.from_dict(value)


def _stage_authorization(
    catalog: Campaign02PlanCatalog,
    stage: str,
    predecessors: tuple[StageGateReceipt, ...] = (),
    **updates: object,
) -> StageAuthorizationProof:
    validator_set, private_keys = _stage_validator_set()
    plan = next(item for item in catalog.plans if item.gate_stage == stage)
    value: dict[str, object] = {
        "allowed_plan_ids": list(catalog.plan_ids_for_stage(stage)),
        "authorized_stage": stage,
        "authorized_task_ids": list(CAMPAIGN02_STAGE_TASK_IDS[stage]),
        "benchmark_definition_id": catalog.definition_id,
        "campaign_id": "campaign-02",
        "definition_attestation_id": catalog.attestation_id,
        "formal_semantics_id": (
            "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
        ),
        "issued_at": NOW.isoformat().replace("+00:00", "Z"),
        "plan_catalog_id": catalog.content_id,
        "real_wan_authorized": False,
        "required_predecessor_receipt_ids": sorted(item.content_id for item in predecessors),
        "result_qc_authorized": False,
        "schema_version": "2.0.0",
        "source_commit": plan.source_commit,
        "source_tree": plan.source_tree,
        "stage_a_authorized": stage == "STAGE_A_EXACTNESS",
        "stage_b_authorized": stage == "STAGE_B_SCIENTIFIC",
        "stage_c_authorized": stage == "STAGE_C_EMULATED_WAN",
        "type_name": "BENCHMARK_STAGE_EXECUTION_AUTHORIZATION",
        "validator_set_id": validator_set.content_id,
    }
    value.update(updates)
    authorization = StageAuthorizationDocument.from_dict(value)
    votes = tuple(
        create_stage_authorization_vote(
            authorization=authorization,
            validator_set=validator_set,
            signer_id=f"benchmark-validator-{index}",
            submitted_at=NOW,
            private_key=private_keys[index],
        )
        for index in range(3)
    )
    attestation = finalize_stage_authorization_attestation(
        authorization=authorization,
        validator_set=validator_set,
        votes=votes,
        verified_at=NOW,
    )
    return StageAuthorizationProof(
        authorization_document=authorization.document,
        attestation_document=attestation.document,
        validator_set=validator_set,
        votes=votes,
    )


class _DryStagePlanRunner:
    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence:
        return StagePlanEvidence(
            plan_id=plan.content_id,
            runner_id=plan.runner_id,
            source_commit=plan.source_commit,
            source_tree=plan.source_tree,
            evidence_ids=(_id(f"dry-evidence:{plan.content_id}"),),
        )


class _PrimaryReferenceBackend:
    source_class = "MEASURED_HARDWARE"
    result_class = "REFERENCE"

    def __init__(self, plan: CampaignExecutionPlan) -> None:
        self.environment_id = plan.environment_id
        self.model_id = plan.model_id
        self._plan = plan

    def begin_run(self, plan: CampaignExecutionPlan) -> RunHandle:
        return RunHandle(_id("stage-b-reference-run"), plan.content_id)

    def execute_ticket(
        self, _run: RunHandle, ticket: TicketAllocation
    ) -> TicketContributionMeasurement:
        ticket_id = ticket.ticket_id
        ordinal = ticket.ordinal
        return TicketContributionMeasurement(
            ticket_id=ticket_id,
            domain_id=ticket.domain_id,
            processed_tokens=ticket.tokens_per_ticket,
            optimizer_steps=ticket.optimizer_steps,
            contribution_id=_id(f"stage-b-contribution:{ordinal}"),
            commitment_id=_id(f"stage-b-commitment:{ordinal}"),
            availability_certificate_id=_id(f"stage-b-availability:{ordinal}"),
            artifacts=(
                RawArtifact(
                    f"stage-b-ticket-{ordinal}.bin",
                    "application/octet-stream",
                    f"measured:{ticket_id}".encode(),
                ),
            ),
        )

    def finalize_run(
        self,
        _run: RunHandle,
        contributions: tuple[TicketContributionMeasurement, ...],
    ) -> ReferenceRoundMeasurement:
        return ReferenceRoundMeasurement(
            round_id=self._plan.round_id,
            parent_checkpoint_id=self._plan.parent_checkpoint_id,
            ordered_ticket_ids=tuple(item.ticket_id for item in contributions),
            ordered_data_exposure_ids=tuple(item.contribution_id for item in contributions),
            processed_tokens=sum(item.processed_tokens for item in contributions),
            final_checkpoint_id=_id("stage-b-reference-final-checkpoint"),
            training_artifacts=(
                RawArtifact(
                    "stage-b-reference-final.safetensors",
                    "application/octet-stream",
                    b"measured-final",
                ),
            ),
        )


def test_campaign02_compiler_creates_exact_15_plan_matrix_per_stage() -> None:
    catalog = _compile()
    assert isinstance(catalog, Campaign02PlanCatalog)
    assert catalog.document["base_plan_count"] == 15
    assert catalog.document["execution_authorized"] is False
    assert len(catalog.plans) == 45
    assert len({item.content_id for item in catalog.plans}) == 45
    assert all(len(catalog.plan_ids_for_stage(stage)) == 15 for stage in CAMPAIGN02_GATE_STAGES)
    assert all(item.ticket_count == 32 for item in catalog.plans)
    assert all(item.tokens_per_ticket == 32_768 for item in catalog.plans)
    assert all(item.optimizer_steps_per_ticket == 32 for item in catalog.plans)
    assert all(item.processed_tokens == 1_048_576 for item in catalog.plans)
    assert sum(item.result_class == "REFERENCE" for item in catalog.plans) == 9
    assert sum(item.result_class == "CERTIFIED_DELTAREDUCE" for item in catalog.plans) == 36
    assert all(
        (item.result_class == "CERTIFIED_DELTAREDUCE") == (item.certified_round_policy is not None)
        for item in catalog.plans
    )


def test_campaign02_plan_catalog_requires_no_execution_authorization() -> None:
    catalog = _compile()
    assert catalog.document["status"] == "COMPILED_NOT_EXECUTABLE_REQUIRES_STAGE_AUTHORIZATION"
    assert all(item.execution_authorization_id is None for item in catalog.plans)


def test_generated_catalog_uses_one_exact_stage_specific_runner() -> None:
    catalog = _compile()
    *_, runtime, stage_identities = _inputs()
    expected = {
        "STAGE_A_EXACTNESS": runtime.exactness_runner_id,
        "STAGE_B_SCIENTIFIC": runtime.scientific_runner_id,
        "STAGE_C_EMULATED_WAN": runtime.network_fault_runner_id,
    }
    for stage, runner_id in expected.items():
        assert {item.runner_id for item in catalog.plans if item.gate_stage == stage} == {runner_id}
    assert catalog.stage_execution_identities_id == stage_identities.content_id
    assert catalog.gate_analyzer_id == stage_identities.identity_id("stage_gate_analyzer")
    assert set(expected.values()).isdisjoint({stage_identities.identity_id("multi_role_runner")})


@pytest.mark.parametrize(
    "runner_field",
    ("exactness_runner_id", "scientific_runner_id", "network_fault_runner_id"),
)
def test_multi_role_metadata_cannot_replace_a_stage_runner(runner_field: str) -> None:
    *_, runtime, stage_identities = _inputs()
    with pytest.raises(
        Campaign02BindingError,
        match="CAMPAIGN02_STAGE_EXECUTION_IDENTITY_MANIFEST_MISMATCH",
    ):
        _compile(
            runtime_lineage=replace(
                runtime,
                **{runner_field: stage_identities.identity_id("multi_role_runner")},
            )
        )


def test_authorization_verifier_cannot_be_presented_as_exactness_executor() -> None:
    *_, _runtime, stage_identities = _inputs()
    value = copy.deepcopy(stage_identities.raw)
    identities = value["identities"]
    assert isinstance(identities, dict)
    exactness = identities["exactness_runner"]
    assert isinstance(exactness, dict)
    identity_value = exactness["value"]
    assert isinstance(identity_value, dict)
    identity_value["entrypoints"] = ["deltatorrent.benchmark.campaign02.authorize_execution_class"]
    exactness["content_id"] = sha256_content_id(
        str(exactness["identity_domain"]).encode() + b"\0" + canonical_json_bytes(identity_value)
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_EXACTNESS_EXECUTOR_IDENTITY_INVALID"):
        StageExecutionIdentityManifest.from_dict(value)


def test_stage_a_admission_test_api_cannot_emit_a_gate_receipt() -> None:
    catalog = _compile()
    result = validate_stage_admission_for_test(
        completed_stage="STAGE_A_EXACTNESS",
        runner_role="EXACTNESS_RUNNER",
        plan_catalog=catalog,
        authorization_proof=_stage_authorization(catalog, "STAGE_A_EXACTNESS"),
        predecessor_gate_receipts={},
    )
    expected = catalog.plan_ids_for_stage("STAGE_A_EXACTNESS")
    assert result.accepted_plan_ids == expected
    assert not hasattr(result, "canonical_bytes")


def test_stage_a_rejects_caller_supplied_dry_runner_before_execution() -> None:
    definition, *_rest, runtime, stage_identities = _inputs()
    catalog = _compile()
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTOR_IDENTITY_MISMATCH"):
        run_stage_a(
            definition=definition,
            plan_catalog=catalog,
            authorization_proof=_stage_authorization(catalog, "STAGE_A_EXACTNESS"),
            runtime_lineage=runtime,
            stage_identities=stage_identities,
            plan_runner=_DryStagePlanRunner(),  # type: ignore[arg-type]
            gate_finalizer=object(),  # type: ignore[arg-type]
        )


def test_stage_a_requires_exact_15_plans_and_signed_authorization() -> None:
    catalog = _compile()
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_PLAN_CATALOG_INCOMPLETE"):
        replace(catalog, plans=catalog.plans[:-1])
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_AUTHORIZATION_PROOF_REQUIRED"):
        validate_stage_admission_for_test(
            completed_stage="STAGE_A_EXACTNESS",
            runner_role="EXACTNESS_RUNNER",
            plan_catalog=catalog,
            authorization_proof={},
            predecessor_gate_receipts={},
        )


def test_stage_a_rejects_unverified_runner_and_campaign01_bindings() -> None:
    definition, *_rest, runtime, stage_identities = _inputs()
    catalog = _compile()

    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTOR_IDENTITY_MISMATCH"):
        run_stage_a(
            definition=definition,
            plan_catalog=catalog,
            authorization_proof=_stage_authorization(catalog, "STAGE_A_EXACTNESS"),
            runtime_lineage=runtime,
            stage_identities=stage_identities,
            plan_runner=_DryStagePlanRunner(),  # type: ignore[arg-type]
            gate_finalizer=object(),  # type: ignore[arg-type]
        )
    campaign01_source = dict(definition.raw)
    campaign01_source["source_commit"] = "c460f3003277bb81db86f9afc1d7211e27870001"
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_PACKAGE_MISMATCH"):
        run_stage_a(
            definition=BenchmarkDefinition.from_dict(campaign01_source),
            plan_catalog=catalog,
            authorization_proof=_stage_authorization(catalog, "STAGE_A_EXACTNESS"),
            runtime_lineage=runtime,
            stage_identities=stage_identities,
            plan_runner=_DryStagePlanRunner(),  # type: ignore[arg-type]
            gate_finalizer=object(),  # type: ignore[arg-type]
        )
    campaign01_definition = load_definition(CONFIG.parent / "primary.yaml")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_PACKAGE_MISMATCH"):
        run_stage_a(
            definition=campaign01_definition,
            plan_catalog=catalog,
            authorization_proof=_stage_authorization(catalog, "STAGE_A_EXACTNESS"),
            runtime_lineage=runtime,
            stage_identities=stage_identities,
            plan_runner=_DryStagePlanRunner(),  # type: ignore[arg-type]
            gate_finalizer=object(),  # type: ignore[arg-type]
        )


def test_generated_stage_b_reference_plan_runs_through_primary_scientific_runner() -> None:
    catalog = _compile()
    plan = next(
        item
        for item in catalog.plans
        if item.gate_stage == "STAGE_B_SCIENTIFIC" and item.result_class == "REFERENCE"
    )
    stage_a_receipt = _gate_receipt(catalog, "STAGE_A_EXACTNESS")
    run = PrimaryScientificRunner(_component_identity("PRIMARY_SCIENTIFIC_RUNNER")).run(
        plan,
        _stage_authorization(catalog, "STAGE_B_SCIENTIFIC", (stage_a_receipt,)),
        _PrimaryReferenceBackend(plan),
        plan_catalog=catalog,
        predecessor_gate_receipts={stage_a_receipt.content_id: stage_a_receipt.canonical_bytes},
    )
    assert run.plan_id == plan.content_id
    assert run.runner_id == plan.runner_id


def test_stage_c_admission_requires_exact_stage_a_and_b_receipts_without_execution() -> None:
    catalog = _compile()
    stage_a = _gate_receipt(catalog, "STAGE_A_EXACTNESS")
    stage_b = _gate_receipt(catalog, "STAGE_B_SCIENTIFIC")
    proof = _stage_authorization(catalog, "STAGE_C_EMULATED_WAN", (stage_a, stage_b))
    receipts = {
        stage_a.content_id: stage_a.canonical_bytes,
        stage_b.content_id: stage_b.canonical_bytes,
    }
    result = validate_stage_admission_for_test(
        completed_stage="STAGE_C_EMULATED_WAN",
        runner_role="NETWORK_FAULT_RUNNER",
        plan_catalog=catalog,
        authorization_proof=proof,
        predecessor_gate_receipts=receipts,
    )
    assert result.accepted_plan_ids == catalog.plan_ids_for_stage("STAGE_C_EMULATED_WAN")
    assert not hasattr(result, "canonical_bytes")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_PREDECESSOR_INVALID"):
        validate_stage_admission_for_test(
            completed_stage="STAGE_C_EMULATED_WAN",
            runner_role="NETWORK_FAULT_RUNNER",
            plan_catalog=catalog,
            authorization_proof=proof,
            predecessor_gate_receipts={stage_a.content_id: stage_a.canonical_bytes},
        )


def test_superseded_v4_stage_c_identity_cannot_claim_measured_runtime(tmp_path: Path) -> None:
    definition, *_rest, stage_identities = _inputs()
    missing = RuntimeArtifact(tmp_path / "missing", _id("missing"))
    boundary = MeasuredStageCRuntimeBoundary(
        image_id=_id("image"),
        java_executable=missing,
        native_executable=missing,
        transport_harness=missing,
        netty_artifacts=(missing,),
        os_interface_counter_root=tmp_path,
        working_root=tmp_path / "work",
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_C_RUNTIME_IDENTITY_MISMATCH"):
        Campaign02NetworkFaultRunner(
            definition=definition,
            stage_identities=stage_identities,
            network_profiles_path=ROOT / "configs/benchmark/networks-v1.json",
            fault_profiles_path=ROOT / "configs/benchmark/faults-v1.json",
            evidence_root=tmp_path,
            runtime_boundary=boundary,
        )


def test_stage_c_v4_identity_rejects_missing_transitive_runtime_source() -> None:
    raw = copy.deepcopy(_stage_identity_manifest_v4().raw)
    identities = raw["identities"]
    assert isinstance(identities, dict)
    network_wrapper = identities["network_fault_runner"]
    assert isinstance(network_wrapper, dict)
    network = network_wrapper["value"]
    assert isinstance(network, dict)
    executable_hashes = network["executable_hashes"]
    assert isinstance(executable_hashes, list)
    network["executable_hashes"] = [
        item
        for item in executable_hashes
        if item["path"]
        != "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NettyMetricsCollector.java"
    ]
    implementation = {
        "entrypoints": network["entrypoints"],
        "executable_hashes": network["executable_hashes"],
        "workflow_hashes": network["workflow_hashes"],
    }
    network["implementation_id"] = sha256_content_id(
        b"deltareduce.010.campaign02-stage-implementation.v1\0"
        + canonical_json_bytes(implementation)
    )
    network_wrapper["content_id"] = sha256_content_id(
        b"deltareduce.010.campaign02-stage-role-identity.v4\0" + canonical_json_bytes(network)
    )
    multi_wrapper = identities["multi_role_runner"]
    assert isinstance(multi_wrapper, dict)
    multi = multi_wrapper["value"]
    assert isinstance(multi, dict)
    role_ids = multi["role_identity_ids"]
    assert isinstance(role_ids, dict)
    role_ids["NETWORK_FAULT_RUNNER"] = network_wrapper["content_id"]
    multi_wrapper["content_id"] = sha256_content_id(
        b"deltareduce.010.campaign02-multi-role-runner.v4\0" + canonical_json_bytes(multi)
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_C_RECURSIVE_IDENTITY_INCOMPLETE"):
        StageExecutionIdentityManifest.from_dict(raw)


def _write_stage_a_evidence_set(root: Path) -> tuple[tuple[str, str], ...]:
    native_cases = "".join(f'<testcase classname="ctest" name="{name}" />' for name in NATIVE_TESTS)
    native = (
        f'<testsuites><testsuite name="ctest" tests="{len(NATIVE_TESTS)}" '
        f'failures="0" errors="0" skipped="0">{native_cases}</testsuite></testsuites>'
    )
    for compiler in ("clang", "gcc"):
        for standard in (20, 23):
            (root / f"native-{compiler}-cpp{standard}.xml").write_text(native, encoding="utf-8")
    python_cases = (("tests.test_exact", "test_exact_case"),)
    (root / "python-cross-component.xml").write_text(
        '<testsuites><testsuite name="pytest" tests="1" failures="0" errors="0" '
        'skipped="0"><testcase classname="tests.test_exact" '
        'name="test_exact_case" /></testsuite></testsuites>',
        encoding="utf-8",
    )
    for feature, version in ((25, "25.0.4.1"), (26, "26.0.2")):
        markers = "\n".join(item.format(feature=feature) for item in JAVA_MARKERS)
        (root / f"java-jdk{feature}.log").write_text(
            f'openjdk version "{version}" 2026-07-21\n{markers}\n',
            encoding="utf-8",
        )
    return python_cases


def test_stage_a_semantic_verifier_rejects_same_named_fabricated_artifacts(
    tmp_path: Path,
) -> None:
    python_cases = _write_stage_a_evidence_set(tmp_path)
    paths = tuple(sorted(tmp_path.iterdir()))
    summary = verify_stage_a_artifacts(
        paths,
        source_root=ROOT,
        expected_python_cases=python_cases,
    )
    assert len(summary.artifacts) == 7
    assert summary.content_id.startswith("sha256:")
    native = tmp_path / "native-gcc-cpp20.xml"
    native.write_text(
        '<testsuites><testsuite name="ctest" tests="1" failures="0" errors="0" '
        'skipped="0"><testcase classname="ctest" name="invented" />'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    with pytest.raises(StageAEvidenceError, match="JUNIT_TEST_SET_MISMATCH"):
        verify_stage_a_artifacts(
            paths,
            source_root=ROOT,
            expected_python_cases=python_cases,
        )


def _bootstrap_finalizer_arguments() -> dict[str, object]:
    stage_identities = _stage_identity_manifest_v4()
    mapping = WorkflowBootstrapMapping.from_dict(
        {
            "bootstrap_commit": "c" * 40,
            "bootstrap_workflow_blob_id": "d" * 40,
            "bootstrap_workflow_content_id": _id("bootstrap-workflow"),
            "bootstrap_workflow_path": ".github/workflows/campaign02-stage-a-bootstrap.yml",
            "execution_authorized": False,
            "formal_semantics_id": (
                "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
            ),
            "qualified_source_commit": "a" * 40,
            "qualified_source_tree": "b" * 40,
            "repository": "chartjs333/delta",
            "schema_version": "1.0.0",
            "source_stage_a_workflow_content_id": sha256_content_id(
                (ROOT / ".github/workflows/benchmark-campaign02-stage-a.yml").read_bytes()
            ),
            "source_stage_a_workflow_path": (".github/workflows/benchmark-campaign02-stage-a.yml"),
            "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_MAPPING",
        }
    )
    private_keys = [Ed25519PrivateKey.generate() for _ in range(4)]
    validator_set = BootstrapValidatorSet.from_dict(
        {
            "execution_authorized": False,
            "f_b": 1,
            "formal_semantics_id": (
                "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
            ),
            "quorum_threshold": 3,
            "schema_version": "1.0.0",
            "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET",
            "validators": [
                {
                    "controller_id": f"controller-{index}",
                    "public_key_base64": base64.b64encode(
                        key.public_key().public_bytes(
                            serialization.Encoding.Raw,
                            serialization.PublicFormat.Raw,
                        )
                    ).decode("ascii"),
                    "signer_id": f"validator-{index}",
                }
                for index, key in enumerate(private_keys)
            ],
        }
    )
    votes = []
    for index, private_key in enumerate(private_keys[:3]):
        unsigned = SignedBootstrapMappingVote(
            mapping.content_id,
            validator_set.content_id,
            f"validator-{index}",
            NOW,
            b"\0" * 64,
        )
        votes.append(replace(unsigned, signature=private_key.sign(unsigned.message)))
    verified_mapping = verify_bootstrap_mapping(
        mapping, validator_set=validator_set, votes=tuple(votes)
    )
    registration = WorkflowRegistrationReceipt.from_dict(
        {
            "authority_bundle_supplied": False,
            "bootstrap_commit": mapping.bootstrap_commit,
            "bootstrap_commit_on_default_branch": True,
            "bootstrap_mapping_id": mapping.content_id,
            "bootstrap_workflow_blob_id": mapping.bootstrap_workflow_blob_id,
            "bootstrap_workflow_content_id": mapping.bootstrap_workflow_content_id,
            "checked_at": NOW.isoformat(),
            "default_branch_ref": "refs/heads/main",
            "formal_semantics_id": (
                "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
            ),
            "github_api_evidence_digest": _id("github-api"),
            "observations": 0,
            "qualified_source_commit": mapping.qualified_source_commit,
            "qualified_source_exists": True,
            "qualified_source_tree": mapping.qualified_source_tree,
            "repository": mapping.repository,
            "schema_version": "1.0.0",
            "stage_a_plans_executed": 0,
            "stage_gate_receipt_emitted": False,
            "type_name": "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT",
            "workflow_id": 17,
            "workflow_path": mapping.bootstrap_workflow_path,
            "workflow_state": "active",
            "workflow_visible_on_default_branch": True,
        }
    )
    provenance = BootstrapRuntimeProvenance(
        repository=mapping.repository,
        workflow_id=17,
        workflow_path=mapping.bootstrap_workflow_path,
        workflow_ref=(
            "chartjs333/delta/.github/workflows/campaign02-stage-a-bootstrap.yml@refs/heads/main"
        ),
        workflow_sha=mapping.bootstrap_commit,
        workflow_blob_id=mapping.bootstrap_workflow_blob_id,
        workflow_content_id=mapping.bootstrap_workflow_content_id,
        run_id=42,
        run_attempt=2,
        event_name="workflow_dispatch",
        dispatch_ref="refs/heads/main",
        github_sha="e" * 40,
        qualified_source_commit=mapping.qualified_source_commit,
        qualified_source_tree=mapping.qualified_source_tree,
        source_stage_a_workflow_content_id=mapping.source_stage_a_workflow_content_id,
    )
    authority = Campaign02StageGateFinalizer.Artifact(
        "authority", 1001, _id("authority"), _id("authority-content"), 41, 1, "AUTHORITY_RUN"
    )
    bootstrap = Campaign02StageGateFinalizer.Artifact(
        "bootstrap/mapping",
        1002,
        _id("mapping"),
        _id("mapping-content"),
        40,
        1,
        "BOOTSTRAP_REGISTRATION_RUN",
    )
    raw = Campaign02StageGateFinalizer.Artifact(
        "raw", 1003, _id("raw"), _id("raw-content"), 42, 2, "CURRENT_STAGE_RUN"
    )
    output = Campaign02StageGateFinalizer.Artifact(
        "plan", 1004, _id("plan"), _id("plan-content"), 42, 2, "CURRENT_STAGE_RUN"
    )
    return {
        "authority_artifact": authority,
        "bootstrap_mapping": verified_mapping,
        "finalized_at": NOW,
        "input_artifacts": (authority, bootstrap, raw),
        "output_artifacts": (output,),
        "provenance": provenance,
        "registration_receipt": registration,
        "stage_identities": stage_identities,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("repository", "attacker/fork"),
        ("workflow_sha", "f" * 40),
        ("workflow_blob_id", "f" * 40),
        ("dispatch_ref", "refs/heads/dev"),
        ("qualified_source_commit", "f" * 40),
        ("run_attempt", 0),
    ),
)
def test_stage_a_workflow_provenance_rejects_wrong_github_context(
    field: str, value: object
) -> None:
    arguments = _bootstrap_finalizer_arguments()
    provenance = arguments["provenance"]
    assert isinstance(provenance, BootstrapRuntimeProvenance)
    arguments["provenance"] = replace(provenance, **{field: value})
    with pytest.raises(ValueError, match="CAMPAIGN02_BOOTSTRAP_RUNTIME_PROVENANCE_INVALID"):
        Campaign02StageGateFinalizer(**arguments)  # type: ignore[arg-type]


def test_stage_a_workflow_finalizer_binds_to_exact_analyzer_bytes() -> None:
    arguments = _bootstrap_finalizer_arguments()
    stage_identities = arguments["stage_identities"]
    assert isinstance(stage_identities, StageExecutionIdentityManifest)
    finalizer = Campaign02StageGateFinalizer(**arguments)  # type: ignore[arg-type]
    bound = verify_bound_stage_gate_finalizer(
        finalizer,
        stage_identities=stage_identities,
        source_root=ROOT,
    )
    assert bound.identity_id == stage_identities.identity_id("stage_gate_analyzer")


def test_stage_a_workflow_finalizer_rejects_artifact_from_other_run_or_attempt() -> None:
    arguments = _bootstrap_finalizer_arguments()
    artifacts = arguments["input_artifacts"]
    assert isinstance(artifacts, tuple)
    arguments["input_artifacts"] = tuple(
        replace(item, workflow_run_attempt=3) if item.name == "raw" else item for item in artifacts
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_WORKFLOW_PROVENANCE_INVALID"):
        Campaign02StageGateFinalizer(**arguments)  # type: ignore[arg-type]


def test_stage_a_control_bundle_recompiles_exact_authoritative_catalog(
    tmp_path: Path,
) -> None:
    (
        definition,
        definition_attestation,
        definition_validator_set,
        definition_votes,
        workload,
        domain_manifest,
        ticket_plan,
        arms,
        runtime,
        stage_identities,
    ) = _inputs()
    catalog = compile_campaign02_plan_catalog(
        definition=definition,
        attestation_document=definition_attestation,
        validator_set=definition_validator_set,
        votes=definition_votes,
        workload=workload,
        domain_manifest=domain_manifest,
        ticket_plan=ticket_plan,
        arms=arms,
        runtime_lineage=runtime,
        stage_identities=stage_identities,
    )
    stage_proof = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    bundle = {
        "arms": [
            {
                "content_id": arm.content_id,
                "value": {
                    "arm_id": arm.arm_id,
                    "deployment_profile": arm.deployment_profile,
                    "kind": arm.kind,
                    "mandatory": arm.mandatory,
                    "runtime_profile_id": arm.runtime_profile_id,
                    "topology": arm.topology,
                    "type_name": "BENCHMARK_ARM",
                    "workload_identity": arm.workload_identity,
                },
            }
            for arm in arms
        ],
        "definition": definition.raw,
        "definition_attestation": definition_attestation,
        "definition_validator_set": definition_validator_set.document,
        "definition_votes": [item.document for item in definition_votes],
        "runtime_lineage": runtime.document,
        "schema_version": "1.0.0",
        "stage_authorization": stage_proof.authorization_document,
        "stage_authorization_attestation": stage_proof.attestation_document,
        "stage_authorization_validator_set": stage_proof.validator_set.document,
        "stage_authorization_votes": [item.document for item in stage_proof.votes],
        "stage_execution_identities": stage_identities.raw,
        "type_name": "CAMPAIGN02_STAGE_A_AUTHORITY_BUNDLE",
    }
    path = tmp_path / "campaign02-stage-a-authority-bundle.json"
    path.write_bytes(canonical_json_bytes(bundle) + b"\n")
    script = ROOT / "specs/010-wan-benchmark-and-quality/scripts/campaign02_stage_a_control.py"
    spec = importlib.util.spec_from_file_location("campaign02_stage_a_control", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    loaded = module.AuthorityBundle.load(path)
    assert loaded.definition.content_id == definition.content_id
    assert loaded.catalog.content_id == catalog.content_id
    assert loaded.catalog.plan_ids_for_stage("STAGE_A_EXACTNESS") == catalog.plan_ids_for_stage(
        "STAGE_A_EXACTNESS"
    )


def test_campaign02_compiler_rejects_wrong_definition_and_attestation() -> None:
    definition, attestation_document, validator_set, votes, *_ = _inputs()
    wrong_value = dict(definition.raw)
    wrong_value["workload_contract_id"] = _id("wrong-workload")
    wrong_definition = BenchmarkDefinition.from_dict(wrong_value)
    with pytest.raises(
        Campaign02BindingError, match="CAMPAIGN02_DEFINITION_EXECUTION_BINDING_MISMATCH"
    ):
        _compile(definition=wrong_definition)
    wrong_attestation = dict(attestation_document)
    wrong_attestation["benchmark_definition_id"] = _id("wrong-definition")
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_DEFINITION_ATTESTATION_INVALID"):
        _compile(
            attestation_document=wrong_attestation,
            validator_set=validator_set,
            votes=votes,
        )


def test_campaign02_compiler_rejects_wrong_source_tree() -> None:
    *_, runtime, _stage_identities = _inputs()
    with pytest.raises(
        Campaign02BindingError,
        match="CAMPAIGN02_STAGE_EXECUTION_IDENTITY_MANIFEST_MISMATCH",
    ):
        _compile(runtime_lineage=replace(runtime, source_tree="c" * 40))


def test_campaign02_legacy_primary_adapter_is_forbidden() -> None:
    definition, *_, arms, _runtime, _stage_identities = _inputs()
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter_for(arms[0]).plan(
            definition,
            arms[0],
            environment_manifest_id=_id("environment"),
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )


def test_exact_superseded_a4160_is_parseable_but_all_adapter_execution_is_forbidden() -> None:
    definition = load_definition(FIXTURES / "campaign-02-superseded-definition-a4160.json")
    assert definition.content_id == (
        "sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af"
    )
    assert definition.campaign_id is None
    arm = ArmSpec(
        definition.arm_ids[0],
        "historical-reference",
        "SCIENTIFIC_REFERENCE",
        "PYTHON",
        True,
        _id("historical-workload"),
        _id("historical-runtime"),
        "SINGLE_NODE_REFERENCE",
    )
    adapter = adapter_for(arm)
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter.plan(
            definition,
            arm,
            environment_manifest_id=_id("environment"),
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )
    legacy_plan = ExecutionPlan(
        definition_id=definition.content_id,
        arm=arm,
        environment_manifest_id=_id("environment"),
        network_profile_id=definition.network_profile_ids[0],
        fault_profile_id=definition.fault_profile_ids[0],
        seed=definition.seeds[0],
        repetition=1,
        processed_tokens=definition.B,
        domains=tuple(item.domain_id for item in definition.domain_weights),
        ticket_plan_id=definition.ticket_plan_id,
        parent_checkpoint_id=definition.base_model_id,
        evaluation_ids=definition.evaluation_ids,
    )
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter.admit(legacy_plan, object())  # type: ignore[arg-type]


def test_historical_campaign01_definition_remains_audit_parseable_not_executable() -> None:
    definition = load_definition(FIXTURES / "historical-campaign-01-definition-dd607.json")
    assert definition.content_id == (
        "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244"
    )
    assert definition.campaign_id is None
    arm = ArmSpec(
        definition.arm_ids[0],
        "historical-reference",
        "SCIENTIFIC_REFERENCE",
        "PYTHON",
        True,
        _id("historical-workload"),
        _id("historical-runtime"),
        "SINGLE_NODE_REFERENCE",
    )
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter_for(arm).plan(
            definition,
            arm,
            environment_manifest_id=_id("environment"),
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )


def test_campaign02_reference_and_certified_classes_cannot_cross() -> None:
    *_, arms, _runtime, _stage_identities = _inputs()
    wrong_reference = replace(arms[0], kind="CERTIFIED_QLORA")
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_ARM_MATRIX_MISMATCH"):
        _compile(arms=(wrong_reference, *arms[1:]))
    certified = next(
        item for item in _compile().plans if item.result_class == "CERTIFIED_DELTAREDUCE"
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_RESULT_CLASS_POLICY_MISMATCH"):
        replace(certified, certified_round_policy=None)


def test_campaign02_distinct_workload_domain_and_ticket_plan_ids() -> None:
    catalog = _compile()
    assert (
        len(
            {
                catalog.workload_contract_id,
                catalog.domain_manifest_id,
                catalog.ticket_plan_id,
            }
        )
        == 3
    )


def test_campaign02_plan_total_cannot_fall_back_to_per_ticket_b() -> None:
    plan = _compile().plans[0]
    assert plan.tokens_per_ticket == 32_768
    assert plan.processed_tokens != plan.tokens_per_ticket
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_TOKEN_RECONCILIATION"):
        replace(plan, total_tokens_per_arm_run=plan.tokens_per_ticket)


def test_campaign02_plan_requires_exact_ticket_table() -> None:
    plan = _compile().plans[0]
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_TOKEN_RECONCILIATION"):
        replace(plan, tickets=plan.tickets[:-1])
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_TICKET_ORDER_INVALID"):
        replace(
            plan,
            tickets=(replace(plan.tickets[0], ordinal=1), *plan.tickets[1:]),
        )


def test_campaign02_execution_plan_type_is_strict_runner_contract() -> None:
    assert all(isinstance(item, CampaignExecutionPlan) for item in _compile().plans)


def test_measured_stage_c_binary_boundary_is_versioned_in_lineage_and_plan() -> None:
    *_, runtime, _stage_identities = _inputs()
    boundary = {
        "java_executable_id": _id("stage-c-java"),
        "native_executable_id": _id("stage-c-native"),
        "transport_harness_id": _id("stage-c-harness"),
        "netty_artifact_ids": (_id("netty-buffer"), _id("netty-transport")),
    }
    with pytest.raises(
        Campaign02BindingError,
        match="CAMPAIGN02_RUNTIME_LINEAGE_STAGE_C_BOUNDARY_VERSION_INVALID",
    ):
        replace(runtime, **boundary)
    measured_lineage = replace(runtime, schema_version="5.0.0", **boundary)
    assert QualifiedRuntimeLineage.from_dict(measured_lineage.document) == measured_lineage

    plan = next(item for item in _compile().plans if item.gate_stage == "STAGE_C_EMULATED_WAN")
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_STAGE_C_BOUNDARY_INVALID"):
        replace(plan, java_executable_id=str(boundary["java_executable_id"]))
    measured_plan = replace(plan, **boundary)
    assert measured_plan.document["schema_version"] == "6.0.0"
    assert measured_plan.java_executable_id == measured_lineage.java_executable_id
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_STAGE_C_BOUNDARY_INVALID"):
        replace(measured_plan, gate_stage="STAGE_A_EXACTNESS")

    with pytest.raises(
        Campaign02BindingError,
        match="CAMPAIGN02_STAGE_C_RUNTIME_LINEAGE_MISMATCH",
    ):
        _compile(runtime_lineage=measured_lineage)


def test_definition_v5_compiles_only_with_bootstrap_and_measured_stage_c_bindings() -> None:
    (
        legacy_definition,
        _legacy_attestation,
        _legacy_validators,
        _legacy_votes,
        workload,
        domain_manifest,
        ticket_plan,
        arms,
        legacy_runtime,
        _legacy_identities,
    ) = _inputs()
    identities = _stage_identity_manifest_v4()
    network = identities.identity("network_fault_runner").value
    netty_ids = network["netty_artifact_ids"]
    assert isinstance(netty_ids, list)
    runtime = replace(
        legacy_runtime,
        schema_version="5.0.0",
        image_id=str(network["image_id"]),
        stage_execution_identities_id=identities.content_id,
        exactness_runner_id=identities.identity_id("exactness_runner"),
        scientific_runner_id=identities.identity_id("scientific_runner"),
        network_fault_runner_id=identities.identity_id("network_fault_runner"),
        java_executable_id=str(network["java_executable_id"]),
        native_executable_id=str(network["native_executable_id"]),
        transport_harness_id=str(network["transport_harness_id"]),
        netty_artifact_ids=tuple(str(item) for item in netty_ids),
    )
    definition_value = dict(legacy_definition.raw)
    definition_value.update(
        {
            "bootstrap_mapping_id": _id("bootstrap-mapping"),
            "image_id": runtime.image_id,
            "qualified_runtime_lineage_id": runtime.content_id,
            "schema_version": "5.0.0",
            "stage_execution_identities_id": identities.content_id,
        }
    )
    definition = BenchmarkDefinition.from_dict(definition_value)
    attestation, validator_set, votes = _attestation(definition.content_id)
    catalog = compile_campaign02_plan_catalog(
        definition=definition,
        attestation_document=attestation.document,
        validator_set=validator_set,
        votes=votes,
        workload=workload,
        domain_manifest=domain_manifest,
        ticket_plan=ticket_plan,
        arms=arms,
        runtime_lineage=runtime,
        stage_identities=identities,
    )
    stage_c = tuple(item for item in catalog.plans if item.gate_stage == "STAGE_C_EMULATED_WAN")
    assert len(stage_c) == 15
    assert {item.document["schema_version"] for item in stage_c} == {"6.0.0"}
    assert {item.java_executable_id for item in stage_c} == {runtime.java_executable_id}
    assert {item.native_executable_id for item in stage_c} == {runtime.native_executable_id}
    assert {item.transport_harness_id for item in stage_c} == {runtime.transport_harness_id}
    assert {item.netty_artifact_ids for item in stage_c} == {runtime.netty_artifact_ids}


def test_caller_constructed_verified_attestation_cannot_enter_binder() -> None:
    fake = VerifiedDefinitionAttestation(
        benchmark_definition_id=_id("definition"),
        validator_set_id=_id("validator-set"),
        f_b=1,
        ordered_signers=("a", "b", "c"),
        ordered_vote_ids=(_id("vote-a"), _id("vote-b"), _id("vote-c")),
        signature_set_root=_id("signature-root"),
        verified_at=NOW,
    )
    with pytest.raises(
        Campaign02BindingError,
        match="CAMPAIGN02_UNVERIFIED_ATTESTATION_INTERFACE_FORBIDDEN",
    ):
        compile_campaign02_execution_set(attestation=fake)


def test_campaign02_catalog_compiler_reverifies_every_detached_signature() -> None:
    _, attestation_document, validator_set, votes, *_ = _inputs()
    forged = replace(
        votes[0],
        signature=bytes([votes[0].signature[0] ^ 1]) + votes[0].signature[1:],
    )
    forged_attestation = dict(attestation_document)
    vote_ids = list(forged_attestation["ordered_vote_ids"])
    vote_ids[vote_ids.index(votes[0].content_id)] = forged.content_id
    forged_attestation["ordered_vote_ids"] = vote_ids
    with pytest.raises(Campaign02BindingError, match="BENCHMARK_DEFINITION_SIGNATURE_INVALID"):
        _compile(
            attestation_document=forged_attestation,
            validator_set=validator_set,
            votes=(forged, *votes[1:]),
        )


def test_stage_a_authorizes_only_exact_stage_a_catalog_plans() -> None:
    catalog = _compile()
    stage_a = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    proof = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    authorize_execution_class(
        proof,
        stage_a,
        plan_catalog=catalog,
        predecessor_gate_receipts={},
        runner_role="EXACTNESS_RUNNER",
    )

    stage_b = next(item for item in catalog.plans if item.gate_stage == "STAGE_B_SCIENTIFIC")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(
            proof,
            stage_b,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="SCIENTIFIC_RUNNER",
        )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_RUNNER_ROLE_NOT_AUTHORIZED"):
        authorize_execution_class(
            proof,
            stage_a,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EVALUATION_RUNNER",
        )
    stage_c = next(item for item in catalog.plans if item.gate_stage == "STAGE_C_EMULATED_WAN")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(
            proof,
            stage_c,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="NETWORK_FAULT_RUNNER",
        )


def test_stage_authorization_rejects_generic_extra_and_inexact_plan_sets() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_AUTHORIZATION_PROOF_REQUIRED"):
        authorize_execution_class(
            {"primary_execution_authorized": True},  # type: ignore[arg-type]
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )
    proof = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    proof = replace(
        proof,
        authorization_document={**proof.authorization_document, "extra": True},
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_AUTHORIZATION_FIELDS_INVALID"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )
    inexact = list(catalog.plan_ids_for_stage("STAGE_A_EXACTNESS"))[:-1]
    proof = _stage_authorization(catalog, "STAGE_A_EXACTNESS", allowed_plan_ids=inexact)
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )
    proof = _stage_authorization(
        catalog, "STAGE_A_EXACTNESS", benchmark_definition_id=_id("wrong-definition")
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )


def test_stage_b_and_c_require_exact_predecessor_gate_receipts() -> None:
    catalog = _compile()
    stage_a_receipt = _gate_receipt(catalog, "STAGE_A_EXACTNESS")
    stage_b_receipt = _gate_receipt(catalog, "STAGE_B_SCIENTIFIC")
    stage_b = next(item for item in catalog.plans if item.gate_stage == "STAGE_B_SCIENTIFIC")
    proof_b = _stage_authorization(
        catalog,
        "STAGE_B_SCIENTIFIC",
        (stage_a_receipt,),
    )
    authorize_execution_class(
        proof_b,
        stage_b,
        plan_catalog=catalog,
        predecessor_gate_receipts={stage_a_receipt.content_id: stage_a_receipt.canonical_bytes},
        runner_role="SCIENTIFIC_RUNNER",
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_PREDECESSOR_INVALID"):
        authorize_execution_class(
            proof_b,
            stage_b,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="SCIENTIFIC_RUNNER",
        )

    stage_c = next(item for item in catalog.plans if item.gate_stage == "STAGE_C_EMULATED_WAN")
    proof_c = _stage_authorization(
        catalog,
        "STAGE_C_EMULATED_WAN",
        (stage_a_receipt, stage_b_receipt),
    )
    authorize_execution_class(
        proof_c,
        stage_c,
        plan_catalog=catalog,
        predecessor_gate_receipts={
            stage_a_receipt.content_id: stage_a_receipt.canonical_bytes,
            stage_b_receipt.content_id: stage_b_receipt.canonical_bytes,
        },
        runner_role="NETWORK_FAULT_RUNNER",
    )


def test_unsigned_and_self_created_stage_authorization_are_rejected() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    document = _stage_authorization(catalog, "STAGE_A_EXACTNESS").authorization_document
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_AUTHORIZATION_PROOF_REQUIRED"):
        authorize_execution_class(
            document,  # type: ignore[arg-type]
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )


def test_stage_authorization_vote_artifacts_are_strictly_typed_and_round_trip() -> None:
    proof = _stage_authorization(_compile(), "STAGE_A_EXACTNESS")
    assert all(
        SignedStageAuthorizationVote.from_dict(vote.document) == vote for vote in proof.votes
    )


def test_changed_signed_stage_authorization_issued_at_is_rejected() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    proof = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    proof = replace(
        proof,
        authorization_document={
            **proof.authorization_document,
            "issued_at": "2026-09-01T11:59:59Z",
        },
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_ATTESTATION_HEADER_INVALID"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )


def test_forged_stage_authorization_signature_is_rejected() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    proof = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    forged = replace(
        proof.votes[0],
        signature=bytes([proof.votes[0].signature[0] ^ 1]) + proof.votes[0].signature[1:],
    )
    attestation = dict(proof.attestation_document)
    vote_ids = list(attestation["ordered_vote_ids"])
    vote_ids[vote_ids.index(proof.votes[0].content_id)] = forged.content_id
    attestation["ordered_vote_ids"] = vote_ids
    proof = replace(proof, attestation_document=attestation, votes=(forged, *proof.votes[1:]))
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_SIGNATURE_INVALID"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )


def test_wrong_stage_authorization_validator_set_is_rejected() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    proof = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    wrong_set, _ = _stage_validator_set()
    proof = replace(proof, validator_set=wrong_set)
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_AUTHORIZATION_VALIDATOR_SET_MISMATCH"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="EXACTNESS_RUNNER",
        )


def test_stage_b_rejects_random_fail_and_other_definition_predecessors() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_B_SCIENTIFIC")
    random_id = _id("random-predecessor")
    proof = _stage_authorization(
        catalog,
        "STAGE_B_SCIENTIFIC",
        required_predecessor_receipt_ids=[random_id],
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_PREDECESSOR_INVALID"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={random_id: b"{}\n"},
            runner_role="SCIENTIFIC_RUNNER",
        )
    for receipt in (
        _gate_receipt(catalog, "STAGE_A_EXACTNESS", decision="FAIL"),
        _gate_receipt(
            catalog,
            "STAGE_A_EXACTNESS",
            benchmark_definition_id=_id("another-definition"),
        ),
        _gate_receipt(
            catalog,
            "STAGE_A_EXACTNESS",
            gate_analyzer_id=_id("another-gate-analyzer"),
        ),
    ):
        proof = _stage_authorization(catalog, "STAGE_B_SCIENTIFIC", (receipt,))
        with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_PREDECESSOR_LINEAGE_INVALID"):
            authorize_execution_class(
                proof,
                plan,
                plan_catalog=catalog,
                predecessor_gate_receipts={receipt.content_id: receipt.canonical_bytes},
                runner_role="SCIENTIFIC_RUNNER",
            )


def test_stage_c_requires_exact_stage_a_and_stage_b_receipt_set() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_C_EMULATED_WAN")
    first = _gate_receipt(catalog, "STAGE_A_EXACTNESS")
    second = _gate_receipt(
        catalog, "STAGE_A_EXACTNESS", evidence_root=_id("second-stage-a-evidence")
    )
    proof = _stage_authorization(catalog, "STAGE_C_EMULATED_WAN", (first, second))
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_PREDECESSOR_STAGE_SET_INVALID"):
        authorize_execution_class(
            proof,
            plan,
            plan_catalog=catalog,
            predecessor_gate_receipts={
                first.content_id: first.canonical_bytes,
                second.content_id: second.canonical_bytes,
            },
            runner_role="NETWORK_FAULT_RUNNER",
        )


def test_missing_runner_role_and_cross_stage_roles_are_rejected() -> None:
    catalog = _compile()
    stage_a = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    proof_a = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_RUNNER_ROLE_REQUIRED"):
        authorize_execution_class(
            proof_a,
            stage_a,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role=None,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_RUNNER_ROLE_NOT_AUTHORIZED"):
        authorize_execution_class(
            proof_a,
            stage_a,
            plan_catalog=catalog,
            predecessor_gate_receipts={},
            runner_role="SCIENTIFIC_RUNNER",
        )
    stage_a_receipt = _gate_receipt(catalog, "STAGE_A_EXACTNESS")
    stage_b = next(item for item in catalog.plans if item.gate_stage == "STAGE_B_SCIENTIFIC")
    proof_b = _stage_authorization(catalog, "STAGE_B_SCIENTIFIC", (stage_a_receipt,))
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_RUNNER_ROLE_NOT_AUTHORIZED"):
        authorize_execution_class(
            proof_b,
            stage_b,
            plan_catalog=catalog,
            predecessor_gate_receipts={stage_a_receipt.content_id: stage_a_receipt.canonical_bytes},
            runner_role="NETWORK_FAULT_RUNNER",
        )


def test_independent_stages_have_unique_bft_round_contexts() -> None:
    catalog = _compile()
    contexts = {
        (
            item.round_id,
            item.certified_round_policy.height,
            item.certified_round_policy.view,
            item.certified_round_policy.validator_epoch_id,
        )
        for item in catalog.plans
        if item.certified_round_policy is not None
    }
    assert len(contexts) == 36
    assert all(
        item.gate_stage in item.round_id
        for item in catalog.plans
        if item.certified_round_policy is not None and item.gate_stage is not None
    )


def test_duplicate_bft_round_context_across_independent_stages_is_rejected() -> None:
    _, _, _, _, _, _, _, arms, _runtime, _stage_identities = _inputs()
    arm = next(item for item in arms if item.kind == "CERTIFIED_QLORA")
    stage_a_policy = _policy("STAGE_A_EXACTNESS", arm, 1, 1)
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_POLICY_ROUND_ID_MISMATCH"):
        CertifiedPlanBinding(
            "STAGE_B_SCIENTIFIC",
            arm.content_id,
            arm.arm_id,
            1,
            1,
            stage_a_policy,
        )


@pytest.mark.parametrize(
    ("command", "suffix"),
    (
        ("plan-primary", ()),
        ("execute-primary", ("--", "runner")),
        ("collect-primary", ("observation.json",)),
        ("verify-primary-runs", ()),
    ),
)
def test_all_legacy_primary_cli_routes_reject_campaign02(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    suffix: tuple[str, ...],
) -> None:
    definition, *_ = _inputs()
    definition_path = tmp_path / "definition-v2.json"
    definition_path.write_bytes(canonical_json_bytes(definition.raw))
    common = (
        str(definition_path),
        str(tmp_path / "attestation.json"),
        str(tmp_path / "arms.json"),
        str(tmp_path / "environment.json"),
        str(tmp_path / "output"),
    )
    options: tuple[str, ...] = ()
    if command == "execute-primary":
        options = ("--runner-id", _id("runner"))
    assert main(("benchmark", command, *options, *common, *suffix)) == 2
    assert "LEGACY_PRIMARY_PATH_FORBIDDEN" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("command", "suffix"),
    (
        ("plan-primary", ()),
        ("execute-primary", ("--", "runner")),
        ("collect-primary", ("observation.json",)),
        ("verify-primary-runs", ()),
    ),
)
def test_exact_a4160_and_unsigned_6c594_are_rejected_by_every_legacy_cli_route(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    suffix: tuple[str, ...],
) -> None:
    common = (
        str(FIXTURES / "campaign-02-superseded-definition-a4160.json"),
        str(FIXTURES / "campaign-02-superseded-attestation-6c594.json"),
        str(tmp_path / "arms.json"),
        str(tmp_path / "environment.json"),
        str(tmp_path / "output"),
    )
    options: tuple[str, ...] = ()
    if command == "execute-primary":
        options = ("--runner-id", _id("runner"))
    assert main(("benchmark", command, *options, *common, *suffix)) == 2
    assert "LEGACY_PRIMARY_PATH_FORBIDDEN" in capsys.readouterr().err


def test_exact_a4160_cannot_be_preregistered_for_executable_primary_use(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        main(
            (
                "benchmark",
                "preregister",
                str(FIXTURES / "campaign-02-superseded-definition-a4160.json"),
                str(FIXTURES / "campaign-02-superseded-attestation-6c594.json"),
                str(tmp_path / "store"),
            )
        )
        == 2
    )
    assert "LEGACY_PRIMARY_PATH_FORBIDDEN" in capsys.readouterr().err
