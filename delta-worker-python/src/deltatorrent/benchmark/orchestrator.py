"""Deterministic Feature 010 planning only; no execution entrypoint exists here."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.canonical import canonical_bytes, content_id
from deltatorrent.benchmark.compatibility import CompatibilityAdmission, admit_plan
from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
    validate_scientific_dependencies,
)


@dataclass(frozen=True, slots=True)
class PlannedRun:
    manifest: CanonicalContract
    plan_key_id: str


@dataclass(frozen=True, slots=True)
class BenchmarkPlan:
    definition_id: str
    runs: tuple[PlannedRun, ...]
    plan_id: str
    execution_authorized: bool = False
    plan_class: str = "CONFORMANCE_ONLY"


def _run_id(plan_key_id: str) -> str:
    return "foundation-" + plan_key_id.removeprefix("sha256:")[:32]


def plan_benchmark(
    *,
    definition: CanonicalContract,
    runtime_identity: CanonicalContract,
    scientific_profile: CanonicalContract,
    environment: CanonicalContract,
    arms: tuple[CanonicalContract, ...],
    network_profiles: tuple[CanonicalContract, ...],
    fault_profiles: tuple[CanonicalContract, ...],
    ticket_ids: tuple[str, ...],
    compatibility: CompatibilityAdmission,
) -> BenchmarkPlan:
    """Expand one immutable definition into a byte-stable conformance plan."""

    if not compatibility.admitted or compatibility.admission_class != "CONFORMANCE_ONLY":
        raise ContractError("ORCHESTRATION_COMPATIBILITY_REQUIRED")
    if definition.type_name != "BENCHMARK_DEFINITION":
        raise ContractError("ORCHESTRATION_DEFINITION_TYPE_INVALID")
    if runtime_identity.type_name != "BENCHMARK_RUNTIME_IDENTITY":
        raise ContractError("ORCHESTRATION_RUNTIME_IDENTITY_TYPE_INVALID")
    if scientific_profile.type_name != "BENCHMARK_SCIENTIFIC_PROFILE":
        raise ContractError("ORCHESTRATION_SCIENTIFIC_PROFILE_TYPE_INVALID")
    if environment.type_name != "BENCHMARK_ENVIRONMENT_MANIFEST":
        raise ContractError("ORCHESTRATION_ENVIRONMENT_TYPE_INVALID")
    if not ticket_ids or tuple(sorted(set(ticket_ids))) != ticket_ids:
        raise ContractError("ORCHESTRATION_TICKET_IDS_INVALID")
    definition_doc = definition.to_dict()
    runtime_doc = runtime_identity.to_dict()
    scientific_doc = scientific_profile.to_dict()
    environment_doc = environment.to_dict()
    if compatibility.expected_identity_id != definition_doc["runtime_identity_id"]:
        raise ContractError("ORCHESTRATION_EXPECTED_RUNTIME_MISMATCH")
    if compatibility.actual_identity_id != environment_doc["runtime_identity_id"]:
        raise ContractError("ORCHESTRATION_ACTUAL_RUNTIME_MISMATCH")
    if (
        compatibility.expected_identity_id != compatibility.actual_identity_id
        or compatibility.expected_identity_id != runtime_identity.content_id
        or compatibility.mismatch_codes
        or compatibility.deployment_profile != runtime_doc["deployment_profile"]
    ):
        raise ContractError("ORCHESTRATION_COMPATIBILITY_BINDING_INVALID")
    authoritative_admission = admit_plan(
        definition=definition,
        expected_runtime=runtime_identity,
        actual_runtime=runtime_identity,
        environment=environment,
        admission_class="CONFORMANCE_ONLY",
    )
    if authoritative_admission != compatibility:
        raise ContractError("ORCHESTRATION_COMPATIBILITY_BINDING_INVALID")
    if definition_doc["scientific_profile_id"] != scientific_profile.content_id:
        raise ContractError("ORCHESTRATION_SCIENTIFIC_PROFILE_MISMATCH")
    validate_scientific_dependencies(definition, scientific_profile)
    if tuple(scientific_doc["ticket_ids"]) != ticket_ids:
        raise ContractError("ORCHESTRATION_TICKET_PLAN_MISMATCH")
    if len({item.content_id for item in arms}) != len(arms):
        raise ContractError("ORCHESTRATION_ARM_DUPLICATE")
    if len({item.content_id for item in network_profiles}) != len(network_profiles):
        raise ContractError("ORCHESTRATION_NETWORK_DUPLICATE")
    if len({item.content_id for item in fault_profiles}) != len(fault_profiles):
        raise ContractError("ORCHESTRATION_FAULT_DUPLICATE")
    arm_by_id = {arm.content_id: arm for arm in arms}
    network_by_id = {profile.content_id: profile for profile in network_profiles}
    fault_by_id = {profile.content_id: profile for profile in fault_profiles}
    if tuple(sorted(arm_by_id)) != tuple(definition_doc["arm_ids"]):
        raise ContractError("ORCHESTRATION_ARM_SET_MISMATCH")
    if tuple(sorted(network_by_id)) != tuple(definition_doc["network_profile_ids"]):
        raise ContractError("ORCHESTRATION_NETWORK_SET_MISMATCH")
    if tuple(sorted(fault_by_id)) != tuple(definition_doc["fault_profile_ids"]):
        raise ContractError("ORCHESTRATION_FAULT_SET_MISMATCH")
    if any(arm.type_name != "BENCHMARK_ARM" for arm in arms):
        raise ContractError("ORCHESTRATION_ARM_TYPE_INVALID")
    if any(profile.type_name != "BENCHMARK_NETWORK_PROFILE" for profile in network_profiles):
        raise ContractError("ORCHESTRATION_NETWORK_TYPE_INVALID")
    if any(profile.type_name != "BENCHMARK_FAULT_PROFILE" for profile in fault_profiles):
        raise ContractError("ORCHESTRATION_FAULT_TYPE_INVALID")
    if {str(arm.to_dict()["arm_kind"]) for arm in arms} != {"REFERENCE", "DELTAREDUCE"}:
        raise ContractError("ORCHESTRATION_ARM_KIND_SET_INVALID")
    for benchmark_arm in arms:
        arm_doc = benchmark_arm.to_dict()
        if arm_doc["model_mode"] != scientific_doc["model_mode"]:
            raise ContractError("ORCHESTRATION_ARM_MODEL_MODE_MISMATCH")
        if arm_doc["deployment_profile"] != compatibility.deployment_profile:
            raise ContractError("ORCHESTRATION_ARM_DEPLOYMENT_MISMATCH")
    runs: list[PlannedRun] = []
    for arm_id in definition_doc["arm_ids"]:
        for network_id in definition_doc["network_profile_ids"]:
            for fault_id in definition_doc["fault_profile_ids"]:
                for repetition, seed in enumerate(scientific_doc["seeds"], start=1):
                    key = {
                        "arm_id": arm_id,
                        "benchmark_definition_id": definition.content_id,
                        "environment_manifest_id": environment.content_id,
                        "fault_profile_id": fault_id,
                        "network_profile_id": network_id,
                        "repetition": repetition,
                        "seed": seed,
                        "ticket_ids": list(ticket_ids),
                    }
                    plan_key_id = content_id(canonical_bytes(key))
                    manifest = CanonicalContract.from_dict(
                        {
                            "arm_id": arm_id,
                            "authority_scope": AUTHORITY_SCOPE,
                            "benchmark_definition_id": definition.content_id,
                            "environment_manifest_id": environment.content_id,
                            "evidence_class": "FOUNDATION_ONLY",
                            "execution_authorization_id": None,
                            "execution_mode": "PLAN_ONLY",
                            "fault_profile_id": fault_id,
                            "formal_semantics_id": FORMAL_SEMANTICS_ID,
                            "gate_eligible": False,
                            "network_profile_id": network_id,
                            "primary_eligible": False,
                            "repetition": repetition,
                            "run_id": _run_id(plan_key_id),
                            "schema_version": SCHEMA_VERSION,
                            "scientific_profile_id": scientific_profile.content_id,
                            "seed": seed,
                            "stage_receipt_ids": [],
                            "status": "PLANNED",
                            "ticket_ids": list(ticket_ids),
                            "type_name": "BENCHMARK_RUN_MANIFEST",
                        }
                    )
                    runs.append(PlannedRun(manifest, plan_key_id))
    plan_document = {
        "definition_id": definition.content_id,
        "execution_authorized": False,
        "plan_class": "CONFORMANCE_ONLY",
        "run_manifest_ids": [run.manifest.content_id for run in runs],
    }
    return BenchmarkPlan(
        definition_id=definition.content_id,
        runs=tuple(runs),
        plan_id=content_id(canonical_bytes(plan_document)),
    )


def reconcile_exposure(
    reference: CanonicalContract,
    candidate: CanonicalContract,
) -> None:
    """Require exact token/domain/scientific exposure before any comparison."""

    if reference.type_name != "BENCHMARK_SCIENTIFIC_PROFILE" or candidate.type_name != (
        "BENCHMARK_SCIENTIFIC_PROFILE"
    ):
        raise ContractError("EXPOSURE_PROFILE_TYPE_INVALID")
    left = reference.to_dict()
    right = candidate.to_dict()
    fields = (
        "dataset_id",
        "domain_tokens",
        "evaluator_ids",
        "model_id",
        "model_mode",
        "optimizer_id",
        "repetitions",
        "seeds",
        "ticket_ids",
        "ticket_plan_id",
        "tokenizer_id",
        "total_eligible_tokens",
    )
    mismatches = tuple(field for field in fields if left[field] != right[field])
    if mismatches:
        raise ContractError("EXPOSURE_MISMATCH:" + ",".join(mismatches))
