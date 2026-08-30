"""Fail-closed plans and measured-observation admission for primary benchmark arms."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from deltatorrent.benchmark.arms import ArmSpec, RunObservation
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.protocol.canonical import canonical_json_bytes


class PrimaryRunError(ValueError):
    """Stable primary planning or measured-run admission rejection."""


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

    @property
    def content_id(self) -> str:
        return _object_id(
            {
                "arm_id": self.arm.content_id,
                "benchmark_definition_id": self.definition_id,
                "domains": list(self.domains),
                "environment_manifest_id": self.environment_manifest_id,
                "fault_profile_id": self.fault_profile_id,
                "network_profile_id": self.network_profile_id,
                "processed_tokens": self.processed_tokens,
                "repetition": self.repetition,
                "seed": self.seed,
            }
        )


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
    ) -> ExecutionPlan:
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
        )

    def admit(self, plan: ExecutionPlan, observation: RunObservation) -> RunObservation:
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
        )
        if not identity:
            raise PrimaryRunError("PRIMARY_OBSERVATION_IDENTITY_DRIFT")
        if observation.terminal_outcome not in {"APPLIED", "ABORTED", "PIECE_UNAVAILABLE"}:
            raise PrimaryRunError("PRIMARY_TERMINAL_OUTCOME_INVALID")
        if observation.total_us <= 0 or observation.useful_compute_us > observation.total_us:
            raise PrimaryRunError("PRIMARY_OBSERVATION_ACCOUNTING_INVALID")
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
