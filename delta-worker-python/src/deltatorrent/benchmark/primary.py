"""Fail-closed plans and measured-observation admission for primary benchmark arms."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from deltatorrent.benchmark.arms import ArmSpec, RunObservation
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id


class PrimaryRunError(ValueError):
    """Stable primary planning or measured-run admission rejection."""


SUPERSEDED_OR_FORBIDDEN_PRIMARY_DEFINITION_IDS: Final = frozenset(
    {
        "sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af",
        "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244",
        "sha256:5dd70a4addf14aa41f4530d117d515125575cbaf0842ad20e0b454988d87e868",
        "sha256:b3d8e5c01ecf95857de0732d7fe69a6ab2bf084b57cc113b258209ee6b90c7df",
    }
)
_PERMANENTLY_FORBIDDEN_CAMPAIGN02_DEFINITION_IDS: Final = frozenset(
    {"sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af"}
)
_LEGACY_COMPATIBILITY_OPERATIONS: Final = (
    "ADMIT",
    "COLLECT",
    "EXECUTE",
    "PLAN",
    "VERIFY",
)


@dataclass(frozen=True, slots=True)
class LegacyPrimaryCompatibilityAuthorization:
    benchmark_definition_id: str
    allowed_operations: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.benchmark_definition_id not in SUPERSEDED_OR_FORBIDDEN_PRIMARY_DEFINITION_IDS
            or self.benchmark_definition_id in _PERMANENTLY_FORBIDDEN_CAMPAIGN02_DEFINITION_IDS
            or not self.allowed_operations
            or self.allowed_operations != tuple(sorted(set(self.allowed_operations)))
            or not set(self.allowed_operations) <= set(_LEGACY_COMPATIBILITY_OPERATIONS)
        ):
            raise PrimaryRunError("LEGACY_PRIMARY_COMPATIBILITY_AUTHORIZATION_INVALID")

    @property
    def document(self) -> dict[str, object]:
        return {
            "allowed_operations": list(self.allowed_operations),
            "benchmark_definition_id": self.benchmark_definition_id,
            "campaign02_execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "primary_evidence_authorized": False,
            "purpose": "LEGACY_PRIMARY_TEST_AND_AUDIT_COMPATIBILITY",
            "schema_version": "1.0.0",
            "type_name": "LEGACY_PRIMARY_COMPATIBILITY_AUTHORIZATION",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.legacy-primary-compatibility-authorization.v1\0"
            + canonical_json_bytes(self.document)
        )


def reject_forbidden_primary_definition(
    definition: BenchmarkDefinition | ExecutionPlan,
    *,
    operation: str,
    compatibility_authorization: LegacyPrimaryCompatibilityAuthorization | None = None,
) -> None:
    """Keep superseded primary definitions parseable but never executable."""
    definition_id = (
        definition.content_id
        if isinstance(definition, BenchmarkDefinition)
        else definition.definition_id
    )
    if (
        definition.campaign_id == "campaign-02"
        or definition_id in _PERMANENTLY_FORBIDDEN_CAMPAIGN02_DEFINITION_IDS
    ):
        raise PrimaryRunError("LEGACY_PRIMARY_PATH_FORBIDDEN")
    if definition_id not in SUPERSEDED_OR_FORBIDDEN_PRIMARY_DEFINITION_IDS:
        return
    authorization = (
        definition.compatibility_authorization
        if isinstance(definition, ExecutionPlan)
        else compatibility_authorization
    )
    if (
        authorization is None
        or authorization.benchmark_definition_id != definition_id
        or operation not in authorization.allowed_operations
    ):
        raise PrimaryRunError("LEGACY_PRIMARY_PATH_FORBIDDEN")


def _object_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_primary_arms(path: Path, definition: BenchmarkDefinition) -> tuple[ArmSpec, ...]:
    try:
        raw = path.read_bytes()
        document = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrimaryRunError("PRIMARY_ARMS_INVALID") from exc
    if not isinstance(document, dict) or canonical_json_bytes(document) != raw:
        raise PrimaryRunError("PRIMARY_ARMS_INVALID")
    values = document.get("arms")
    if not isinstance(values, list) or any(not isinstance(item, dict) for item in values):
        raise PrimaryRunError("PRIMARY_ARMS_INVALID")
    arms = tuple(
        ArmSpec(
            content_id=_object_id(value),
            arm_id=str(value.get("arm_id")),
            kind=str(value.get("kind")),
            deployment_profile=str(value.get("deployment_profile")),
            mandatory=value.get("mandatory") is True,
            workload_identity=str(value.get("workload_identity")),
            runtime_profile_id=_object_id({"deployment_profile": value.get("deployment_profile")}),
            topology=str(value.get("topology")),
        )
        for value in values
    )
    if tuple(item.content_id for item in arms) != definition.arm_ids:
        raise PrimaryRunError("PRIMARY_ARM_SET_MISMATCH")
    if len({item.arm_id for item in arms}) != len(arms) or any(not item.mandatory for item in arms):
        raise PrimaryRunError("PRIMARY_ARMS_INVALID")
    return arms


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    definition_id: str
    arm: ArmSpec
    environment_manifest_id: str
    network_profile_id: str
    fault_profile_id: str
    seed: int
    repetition: int
    processed_tokens: int
    domains: tuple[str, ...]
    ticket_plan_id: str
    parent_checkpoint_id: str
    evaluation_ids: tuple[str, ...]
    campaign_id: str | None = None
    compatibility_authorization: LegacyPrimaryCompatibilityAuthorization | None = None

    @property
    def document(self) -> dict[str, object]:
        """Canonical runner input; the definition remains the methodology authority."""
        document: dict[str, object] = {
            "arm_kind": self.arm.kind,
            "arm_id": self.arm.content_id,
            "arm_name": self.arm.arm_id,
            "benchmark_definition_id": self.definition_id,
            "deployment_profile": self.arm.deployment_profile,
            "domains": list(self.domains),
            "environment_manifest_id": self.environment_manifest_id,
            "evaluation_ids": list(self.evaluation_ids),
            "fault_profile_id": self.fault_profile_id,
            "network_profile_id": self.network_profile_id,
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "processed_tokens": self.processed_tokens,
            "repetition": self.repetition,
            "seed": self.seed,
            "ticket_plan_id": self.ticket_plan_id,
            "topology": self.arm.topology,
            "workload_identity": self.arm.workload_identity,
        }
        if self.campaign_id is not None:
            document["campaign_id"] = self.campaign_id
        if self.compatibility_authorization is not None:
            document["compatibility_authorization_id"] = self.compatibility_authorization.content_id
        return document

    @property
    def content_id(self) -> str:
        return _object_id(self.document)


class PrimaryArmAdapter:
    allowed_kinds: frozenset[str]
    allowed_topologies: frozenset[str]

    def __init__(self, allowed_kinds: frozenset[str], allowed_topologies: frozenset[str]) -> None:
        self.allowed_kinds = allowed_kinds
        self.allowed_topologies = allowed_topologies

    def plan(
        self,
        definition: BenchmarkDefinition,
        arm: ArmSpec,
        *,
        environment_manifest_id: str,
        network_profile_id: str,
        fault_profile_id: str,
        seed: int,
        repetition: int,
        compatibility_authorization: LegacyPrimaryCompatibilityAuthorization | None = None,
    ) -> ExecutionPlan:
        reject_forbidden_primary_definition(
            definition,
            operation="PLAN",
            compatibility_authorization=compatibility_authorization,
        )
        if not definition.primary:
            raise PrimaryRunError("PRIMARY_ADAPTER_REQUIRES_PRIMARY_DEFINITION")
        if arm.content_id not in definition.arm_ids:
            raise PrimaryRunError("PRIMARY_ARM_NOT_IN_DEFINITION")
        if arm.kind not in self.allowed_kinds or arm.topology not in self.allowed_topologies:
            raise PrimaryRunError("PRIMARY_ADAPTER_ARM_CLASS_MISMATCH")
        if network_profile_id not in definition.network_profile_ids:
            raise PrimaryRunError("PRIMARY_NETWORK_PROFILE_MISMATCH")
        if fault_profile_id not in definition.fault_profile_ids:
            raise PrimaryRunError("PRIMARY_FAULT_PROFILE_MISMATCH")
        if repetition < 1 or repetition > definition.repetitions:
            raise PrimaryRunError("PRIMARY_REPETITION_INVALID")
        if definition.seeds[repetition - 1] != seed:
            raise PrimaryRunError("PRIMARY_SEED_REPETITION_MISMATCH")
        return ExecutionPlan(
            definition_id=definition.content_id,
            arm=arm,
            environment_manifest_id=environment_manifest_id,
            network_profile_id=network_profile_id,
            fault_profile_id=fault_profile_id,
            seed=seed,
            repetition=repetition,
            processed_tokens=definition.B,
            domains=tuple(item.domain_id for item in definition.domain_weights),
            ticket_plan_id=definition.ticket_plan_id,
            parent_checkpoint_id=definition.base_model_id,
            evaluation_ids=definition.evaluation_ids,
            campaign_id=definition.campaign_id,
            compatibility_authorization=compatibility_authorization,
        )

    def admit(self, plan: ExecutionPlan, observation: RunObservation) -> RunObservation:
        reject_forbidden_primary_definition(plan, operation="ADMIT")
        identity = (
            observation.definition_id == plan.definition_id
            and observation.arm == plan.arm
            and observation.environment_manifest_id == plan.environment_manifest_id
            and observation.network_profile_id == plan.network_profile_id
            and observation.fault_profile_id == plan.fault_profile_id
            and observation.seed == plan.seed
            and observation.repetition == plan.repetition
            and observation.processed_tokens == plan.processed_tokens
            and tuple(domain for domain, _ in observation.domain_ticket_counts) == plan.domains
            and observation.ticket_plan_id == plan.ticket_plan_id
            and observation.parent_checkpoint_id == plan.parent_checkpoint_id
            and len(observation.evaluation_artifact_ids) == len(plan.evaluation_ids)
        )
        if not identity:
            raise PrimaryRunError("PRIMARY_OBSERVATION_IDENTITY_DRIFT")
        if observation.terminal_outcome not in {"APPLIED", "ABORTED", "PIECE_UNAVAILABLE"}:
            raise PrimaryRunError("PRIMARY_TERMINAL_OUTCOME_INVALID")
        if observation.total_us <= 0 or observation.useful_compute_us > observation.total_us:
            raise PrimaryRunError("PRIMARY_OBSERVATION_ACCOUNTING_INVALID")
        if observation.arm.kind != "SCIENTIFIC_REFERENCE" and len(observation.certificate_ids) < 6:
            raise PrimaryRunError("PRIMARY_CERTIFICATE_EVIDENCE_INCOMPLETE")
        return observation


class ScientificReferenceAdapter(PrimaryArmAdapter):
    def __init__(self) -> None:
        super().__init__(frozenset({"SCIENTIFIC_REFERENCE"}), frozenset({"SINGLE_NODE_REFERENCE"}))


class FlatBftAdapter(PrimaryArmAdapter):
    def __init__(self) -> None:
        super().__init__(frozenset({"CERTIFIED_QLORA"}), frozenset({"FLAT_BFT"}))


class HierarchicalBftAdapter(PrimaryArmAdapter):
    def __init__(self) -> None:
        super().__init__(frozenset({"CERTIFIED_QLORA"}), frozenset({"HIERARCHICAL_BFT"}))


def adapter_for(arm: ArmSpec) -> PrimaryArmAdapter:
    if arm.kind == "SCIENTIFIC_REFERENCE":
        return ScientificReferenceAdapter()
    if arm.topology == "FLAT_BFT":
        return FlatBftAdapter()
    if arm.topology == "HIERARCHICAL_BFT":
        return HierarchicalBftAdapter()
    raise PrimaryRunError("PRIMARY_ADAPTER_NOT_FOUND")
