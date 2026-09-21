"""Deterministic arm-adapter plans; Foundation exposes no execution method."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.contracts import CanonicalContract, ContractError

STAGE_RECEIPT_PATH = ("WORKER_PYTHON", "TRANSPORT_JAVA_NETTY", "NATIVE_CPP_WAL")


@dataclass(frozen=True, slots=True)
class ArmAdapterPlan:
    arm_id: str
    adapter_id: str
    arm_kind: str
    deployment_profile: str
    model_mode: str
    ordered_receipt_stages: tuple[str, ...]
    execution_authorized: bool = False
    plan_class: str = "CONFORMANCE_ONLY"


def plan_arm_adapter(
    *,
    arm: CanonicalContract,
    runtime_identity: CanonicalContract,
    scientific_profile: CanonicalContract,
) -> ArmAdapterPlan:
    """Bind an arm to one runtime/scientific identity without running it."""

    if arm.type_name != "BENCHMARK_ARM":
        raise ContractError("ARM_ADAPTER_ARM_TYPE_INVALID")
    if runtime_identity.type_name != "BENCHMARK_RUNTIME_IDENTITY":
        raise ContractError("ARM_ADAPTER_RUNTIME_TYPE_INVALID")
    if scientific_profile.type_name != "BENCHMARK_SCIENTIFIC_PROFILE":
        raise ContractError("ARM_ADAPTER_SCIENCE_TYPE_INVALID")
    arm_document = arm.to_dict()
    runtime_document = runtime_identity.to_dict()
    science_document = scientific_profile.to_dict()
    if arm_document["deployment_profile"] != runtime_document["deployment_profile"]:
        raise ContractError("ARM_ADAPTER_DEPLOYMENT_MISMATCH")
    if arm_document["model_mode"] != science_document["model_mode"]:
        raise ContractError("ARM_ADAPTER_MODEL_MODE_MISMATCH")
    return ArmAdapterPlan(
        arm_id=arm.content_id,
        adapter_id=str(arm_document["adapter_id"]),
        arm_kind=str(arm_document["arm_kind"]),
        deployment_profile=str(arm_document["deployment_profile"]),
        model_mode=str(arm_document["model_mode"]),
        ordered_receipt_stages=STAGE_RECEIPT_PATH,
    )
