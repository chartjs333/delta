"""Construct and execute a non-authoritative exact-catalog Campaign 02 Stage C candidate."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from deltatorrent.benchmark.arms import ArmSpec
from deltatorrent.benchmark.campaign02 import (
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.campaign02_binding import (
    Campaign02PlanCatalog,
    QualifiedRuntimeLineage,
    compile_campaign02_plan_catalog,
)
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.campaign02_stage_c_runtime import MeasuredStageCRuntimeBoundary
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    SignedDefinitionVote,
    create_definition_vote,
    finalize_definition_attestation,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_IDENTITY_DOMAINS: Final = {
    "evaluation_runner": "deltareduce.010.primary-component.v1",
    "exactness_runner": "deltareduce.010.campaign02-stage-role-identity.v4",
    "multi_role_runner": "deltareduce.010.campaign02-multi-role-runner.v4",
    "native_feature008_verifier": "deltareduce.010.campaign02-native-feature008-verifier.v2",
    "network_fault_runner": "deltareduce.010.campaign02-stage-role-identity.v4",
    "observation_writer": "deltareduce.010.primary-component.v1",
    "scientific_runner": "deltareduce.010.primary-component.v1",
    "signed_stage_authorization_verifier": (
        "deltareduce.010.campaign02-signed-stage-authorization-verifier.v2"
    ),
    "stage_gate_analyzer": "deltareduce.010.campaign02-stage-gate-analyzer.v4",
    "typed_gate_receipt_verifier": (
        "deltareduce.010.campaign02-typed-stage-gate-receipt-verifier.v2"
    ),
}
_STAGE_C_PATHS: Final = {
    ".github/workflows/benchmark-campaign02-stage-c-measured.yml",
    "CMakeLists.txt",
    "configs/benchmark/faults-v1.json",
    "configs/benchmark/networks-v1.json",
    "delta-node-java/distribution-dependencies.lock.json",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkContracts.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/MeasuredStageCTransport.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NettyMetricsCollector.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NetworkFaultController.java",
    "delta-core-cpp/include/delta/apply/engine.hpp",
    "delta-core-cpp/include/delta/certificates/contracts.hpp",
    "delta-core-cpp/include/delta/certificates/verifier.hpp",
    "delta-core-cpp/include/delta/core/canonical.hpp",
    "delta-core-cpp/include/delta/core/protocol.hpp",
    "delta-core-cpp/include/delta/core/transition.hpp",
    "delta-core-cpp/include/delta/robust/plan.hpp",
    "delta-core-cpp/src/apply/engine.cpp",
    "delta-core-cpp/src/canonical.cpp",
    "delta-core-cpp/src/certificates/contracts.cpp",
    "delta-core-cpp/src/certificates/verifier.cpp",
    "delta-core-cpp/src/protocol.cpp",
    "delta-core-cpp/src/robust/plan.cpp",
    "delta-core-cpp/src/transition.cpp",
    "delta-protocol/schemas/010/campaign-02/benchmark-definition-v5.json",
    "delta-protocol/schemas/010/campaign-02/execution-plan-v6.json",
    "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v4.json",
    "delta-protocol/schemas/010/campaign-02/qualified-runtime-lineage-v5.json",
    "delta-protocol/schemas/010/campaign-02/stage-c-candidate-run-v1.json",
    "delta-protocol/schemas/010/campaign-02/stage-c-candidate-summary-v1.json",
    "delta-protocol/schemas/010/campaign-02/stage-execution-identities-v4.json",
    "delta-protocol/schemas/010/fault-profile-v1.json",
    "delta-protocol/schemas/010/network-profile-v1.json",
    "delta-runtime-cpp/include/delta/runtime/benchmark.hpp",
    "delta-runtime-cpp/include/delta/runtime/bounded_mpsc.hpp",
    "delta-runtime-cpp/include/delta/runtime/certificate_runtime.hpp",
    "delta-runtime-cpp/include/delta/runtime/runtime.hpp",
    "delta-runtime-cpp/src/benchmark/fault_control.cpp",
    "delta-runtime-cpp/src/benchmark/fault_execution.cpp",
    "delta-runtime-cpp/src/benchmark/sidecar_main.cpp",
    "delta-runtime-cpp/src/benchmark/trace_export.cpp",
    "delta-runtime-cpp/src/certificate_runtime.cpp",
    "delta-runtime-cpp/src/runtime.cpp",
    "delta-runtime-cpp/src/wal.cpp",
    "delta-runtime-cpp/src/wal.hpp",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_binding.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_c_candidate.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_c_runtime.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
    "delta-worker-python/src/deltatorrent/benchmark/definition.py",
    "delta-worker-python/src/deltatorrent/benchmark/fault_profiles.py",
    "delta-worker-python/src/deltatorrent/benchmark/network_profiles.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py",
    "specs/010-wan-benchmark-and-quality/scripts/run_campaign02_stage_c_conformance.py",
}
_BOOTSTRAP_PATHS: Final = {
    ".github/workflows/benchmark-campaign02-stage-a.yml",
    "delta-protocol/schemas/010/campaign-02/benchmark-definition-v5.json",
    "delta-protocol/schemas/010/campaign-02/stage-workflow-gate-qc-v4.json",
    "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-mapping-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-signature-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-validator-set-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-registration-api-evidence-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-registration-receipt-v3.json",
    "delta-protocol/schemas/010/campaign-02/workflow-registration-signature-v2.json",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_bootstrap.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
    "delta-worker-python/src/deltatorrent/benchmark/definition.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_bootstrap_control.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_stage_a_control.py",
}
_CANDIDATE_TIME: Final = datetime(2026, 9, 3, 12, tzinfo=UTC)


class Campaign02StageCCandidateError(ValueError):
    """Stable fail-closed candidate construction rejection."""


@dataclass(frozen=True, slots=True)
class CandidateCatalog:
    definition: BenchmarkDefinition
    catalog: Campaign02PlanCatalog
    runtime_lineage: QualifiedRuntimeLineage
    stage_identities: StageExecutionIdentityManifest
    compiler_signature_ids: tuple[str, ...]


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise Campaign02StageCCandidateError("CAMPAIGN02_STAGE_C_CANDIDATE_INPUT_INVALID")
    return value


def _bind_source(value: object, source_commit: str, source_tree: str) -> None:
    if isinstance(value, dict):
        if "source_commit" in value:
            value["source_commit"] = source_commit
        if "source_tree" in value:
            value["source_tree"] = source_tree
        for item in value.values():
            _bind_source(item, source_commit, source_tree)
    elif isinstance(value, list):
        for item in value:
            _bind_source(item, source_commit, source_tree)


def _hashes(source_root: Path, paths: set[str]) -> list[dict[str, str]]:
    result = []
    for relative in sorted(paths):
        path = source_root / relative
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise Campaign02StageCCandidateError(
                f"CAMPAIGN02_STAGE_C_CANDIDATE_SOURCE_MISSING:{relative}"
            ) from exc
        result.append({"content_id": sha256_content_id(content), "path": relative})
    return result


def _refresh_hashes(source_root: Path, value: dict[str, object]) -> None:
    for field in ("executable_hashes", "workflow_hashes"):
        entries = value.get(field)
        if isinstance(entries, list):
            paths = {
                str(item["path"])
                for item in entries
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            }
            value[field] = _hashes(source_root, paths)


def _implementation_id(value: dict[str, object]) -> str:
    return sha256_content_id(
        b"deltareduce.010.campaign02-stage-implementation.v1\0"
        + canonical_json_bytes(
            {
                "entrypoints": value.get("entrypoints"),
                "executable_hashes": value.get("executable_hashes"),
                "workflow_hashes": value.get("workflow_hashes"),
            }
        )
    )


def _wrap(name: str, value: dict[str, object]) -> dict[str, object]:
    domain = _IDENTITY_DOMAINS[name]
    return {
        "content_id": sha256_content_id(
            domain.encode("ascii") + b"\0" + canonical_json_bytes(value)
        ),
        "identity_domain": domain,
        "value": value,
    }


def build_stage_identities(
    *,
    source_root: Path,
    source_commit: str,
    source_tree: str,
    environment_id: str,
    boundary: MeasuredStageCRuntimeBoundary,
) -> StageExecutionIdentityManifest:
    raw = copy.deepcopy(
        _load(source_root / "configs/benchmark/campaign-02/stage-execution-identities-v3.json")
    )
    raw["schema_version"] = "4.0.0"
    raw["source_commit"] = source_commit
    raw["source_tree"] = source_tree
    identities = raw.get("identities")
    if not isinstance(identities, dict) or set(identities) != set(_IDENTITY_DOMAINS):
        raise Campaign02StageCCandidateError("CAMPAIGN02_STAGE_C_CANDIDATE_IDENTITY_SET_INVALID")
    values: dict[str, dict[str, object]] = {}
    for name, wrapper in identities.items():
        if not isinstance(wrapper, dict) or not isinstance(wrapper.get("value"), dict):
            raise Campaign02StageCCandidateError("CAMPAIGN02_STAGE_C_CANDIDATE_IDENTITY_INVALID")
        value = copy.deepcopy(wrapper["value"])
        _bind_source(value, source_commit, source_tree)
        _refresh_hashes(source_root, value)
        values[str(name)] = value

    network = values["network_fault_runner"]
    network.update(
        {
            "environment_id": environment_id,
            "executable_hashes": _hashes(
                source_root, {path for path in _STAGE_C_PATHS if not path.startswith(".github/")}
            ),
            "image_id": boundary.image_id,
            "java_executable_id": boundary.java_executable_id,
            "native_executable_id": boundary.native_executable_id,
            "netty_artifact_ids": list(boundary.netty_artifact_ids),
            "source_class": "MEASURED_RUNTIME",
            "transport_harness_id": boundary.transport_harness_id,
            "workflow_hashes": _hashes(
                source_root, {path for path in _STAGE_C_PATHS if path.startswith(".github/")}
            ),
        }
    )
    analyzer = values["stage_gate_analyzer"]
    analyzer.update(
        {
            "executable_hashes": _hashes(
                source_root, {path for path in _BOOTSTRAP_PATHS if not path.startswith(".github/")}
            ),
            "workflow_hashes": _hashes(
                source_root, {path for path in _BOOTSTRAP_PATHS if path.startswith(".github/")}
            ),
        }
    )
    for name in ("exactness_runner", "network_fault_runner", "stage_gate_analyzer"):
        values[name]["implementation_id"] = _implementation_id(values[name])

    wrapped = {
        name: _wrap(name, value) for name, value in values.items() if name != "multi_role_runner"
    }
    multi = values["multi_role_runner"]
    multi["role_identity_ids"] = {
        "EXACTNESS_RUNNER": wrapped["exactness_runner"]["content_id"],
        "NETWORK_FAULT_RUNNER": wrapped["network_fault_runner"]["content_id"],
        "SCIENTIFIC_RUNNER": wrapped["scientific_runner"]["content_id"],
    }
    wrapped["multi_role_runner"] = _wrap("multi_role_runner", multi)
    raw["identities"] = wrapped
    return StageExecutionIdentityManifest.from_dict(raw)


def _arms(source_root: Path, workload_id: str) -> tuple[ArmSpec, ...]:
    document = _load(source_root / "configs/benchmark/campaign-02/definition-arms-v2.json")
    raw_arms = document.get("arms")
    if not isinstance(raw_arms, list):
        raise Campaign02StageCCandidateError("CAMPAIGN02_STAGE_C_CANDIDATE_ARMS_INVALID")
    result = []
    for raw in raw_arms:
        if not isinstance(raw, dict) or raw.get("workload_identity") != workload_id:
            raise Campaign02StageCCandidateError("CAMPAIGN02_STAGE_C_CANDIDATE_ARMS_INVALID")
        result.append(
            ArmSpec(
                content_id=sha256_content_id(canonical_json_bytes(raw)),
                arm_id=str(raw.get("arm_id")),
                kind=str(raw.get("kind")),
                deployment_profile=str(raw.get("deployment_profile")),
                mandatory=raw.get("mandatory") is True,
                workload_identity=workload_id,
                runtime_profile_id=sha256_content_id(
                    canonical_json_bytes({"deployment_profile": raw.get("deployment_profile")})
                ),
                topology=str(raw.get("topology")),
            )
        )
    return tuple(result)


def _candidate_validator_set() -> tuple[BenchmarkReviewValidatorSet, tuple[Ed25519PrivateKey, ...]]:
    keys = tuple(
        Ed25519PrivateKey.from_private_bytes(
            hashlib.sha256(f"campaign02-stage-c-candidate-{index}".encode("ascii")).digest()
        )
        for index in range(4)
    )
    validators = []
    for index, key in enumerate(keys):
        public_key = key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        validators.append(
            {
                "controller_id": f"candidate-controller-{index}",
                "key_custody_statement_id": sha256_content_id(
                    f"candidate-custody-{index}".encode("ascii")
                ),
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "public_key_id": sha256_content_id(
                    b"deltareduce.010.benchmark-review-key.v1\0" + public_key
                ),
                "signature_algorithm": "ED25519",
                "valid_from": "2026-09-01T00:00:00Z",
                "valid_until": None,
                "validator_id": f"candidate-validator-{index}",
            }
        )
    return (
        BenchmarkReviewValidatorSet.from_dict(
            {
                "campaign_id": "campaign-02",
                "f_b": 1,
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "purpose": "BENCHMARK_DEFINITION_REVIEW",
                "schema_version": "1.0.0",
                "type_name": "BENCHMARK_REVIEW_VALIDATOR_SET",
                "validators": validators,
            }
        ),
        keys,
    )


def build_candidate_catalog(
    *,
    source_root: Path,
    source_commit: str,
    source_tree: str,
    boundary: MeasuredStageCRuntimeBoundary,
) -> CandidateCatalog:
    config = source_root / "configs/benchmark/campaign-02"
    workload = load_workload_contract(config / "workload-v2.json")
    domain_manifest = load_domain_manifest(config / "domain-manifest-v1.json")
    ticket_plan = load_ticket_plan(config / "ticket-plan-v1.json", workload, domain_manifest)
    arms = _arms(source_root, workload.content_id)
    environment_id = sha256_content_id(
        b"deltareduce.010.campaign02-stage-c-candidate-environment.v1\0"
        + canonical_json_bytes(
            {
                "image_id": boundary.image_id,
                "java_executable_id": boundary.java_executable_id,
                "native_executable_id": boundary.native_executable_id,
                "netty_artifact_ids": list(boundary.netty_artifact_ids),
                "source_commit": source_commit,
                "source_tree": source_tree,
                "transport_harness_id": boundary.transport_harness_id,
            }
        )
    )
    stage_identities = build_stage_identities(
        source_root=source_root,
        source_commit=source_commit,
        source_tree=source_tree,
        environment_id=environment_id,
        boundary=boundary,
    )
    old_lineage = QualifiedRuntimeLineage.from_dict(
        _load(config / "qualified-runtime-lineage-v4.json")
    )
    runtime = replace(
        old_lineage,
        source_commit=source_commit,
        source_tree=source_tree,
        environment_id=environment_id,
        image_id=boundary.image_id,
        hardware_id=sha256_content_id(
            b"deltareduce.010.campaign02-stage-c-candidate-hardware.v1\0"
            + canonical_json_bytes(
                {
                    "counter_root": boundary.os_interface_counter_root.as_posix(),
                    "image_id": boundary.image_id,
                }
            )
        ),
        evaluation_runner_id=stage_identities.identity_id("evaluation_runner"),
        writer_id=stage_identities.identity_id("observation_writer"),
        stage_execution_identities_id=stage_identities.content_id,
        exactness_runner_id=stage_identities.identity_id("exactness_runner"),
        scientific_runner_id=stage_identities.identity_id("scientific_runner"),
        network_fault_runner_id=stage_identities.identity_id("network_fault_runner"),
        java_executable_id=boundary.java_executable_id,
        native_executable_id=boundary.native_executable_id,
        transport_harness_id=boundary.transport_harness_id,
        netty_artifact_ids=boundary.netty_artifact_ids,
        schema_version="5.0.0",
    )
    definition_value = copy.deepcopy(_load(config / "definition-v4.json"))
    definition_value.update(
        {
            "bootstrap_mapping_id": sha256_content_id(
                b"deltareduce.010.campaign02-stage-c-candidate-no-registration.v1\0"
                + canonical_json_bytes(
                    {
                        "execution_authorized": False,
                        "source_commit": source_commit,
                        "source_tree": source_tree,
                    }
                )
            ),
            "image_id": runtime.image_id,
            "native_build_id": boundary.native_executable_id,
            "qualified_runtime_lineage_id": runtime.content_id,
            "schema_version": "5.0.0",
            "source_commit": source_commit,
            "source_tree": source_tree,
            "stage_execution_identities_id": stage_identities.content_id,
        }
    )
    definition = BenchmarkDefinition.from_dict(definition_value)
    validator_set, keys = _candidate_validator_set()
    votes: tuple[SignedDefinitionVote, ...] = tuple(
        create_definition_vote(
            benchmark_definition_id=definition.content_id,
            validator_set=validator_set,
            signer_id=f"candidate-validator-{index}",
            submitted_at=_CANDIDATE_TIME,
            private_key=keys[index],
        )
        for index in range(3)
    )
    attestation = finalize_definition_attestation(
        benchmark_definition_id=definition.content_id,
        validator_set=validator_set,
        votes=votes,
        verified_at=_CANDIDATE_TIME,
    )
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
        stage_identities=stage_identities,
    )
    stage_c = tuple(plan for plan in catalog.plans if plan.gate_stage == "STAGE_C_EMULATED_WAN")
    if len(stage_c) != 15:
        raise Campaign02StageCCandidateError("CAMPAIGN02_STAGE_C_CANDIDATE_PLAN_COUNT_INVALID")
    return CandidateCatalog(
        definition,
        catalog,
        runtime,
        stage_identities,
        tuple(vote.content_id for vote in votes),
    )
