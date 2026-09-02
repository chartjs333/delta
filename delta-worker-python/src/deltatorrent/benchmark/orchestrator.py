"""Isolated deterministic orchestration for preregistered benchmark arms."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.arms import ArmSpec, RunObservation, SyntheticArmRunner
from deltatorrent.benchmark.preregistration import PreregisteredDefinition


class OrchestrationError(ValueError):
    """Stable orchestration admission or completeness error."""


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    definition_id: str
    runs: tuple[RunObservation, ...]
    fixture_class: str = "SYNTHETIC_NOT_PRIMARY_EVIDENCE"


class ExperimentOrchestrator:
    def __init__(self, runner: SyntheticArmRunner | None = None) -> None:
        self.runner = runner or SyntheticArmRunner()

    def execute(
        self,
        preregistration: PreregisteredDefinition,
        arms: tuple[ArmSpec, ...],
        *,
        environment_manifest_id: str,
    ) -> OrchestrationResult:
        definition = preregistration.definition
        definition_id = definition.content_id
        actual_arm_ids = tuple(item.content_id for item in arms)
        if actual_arm_ids != definition.arm_ids:
            raise OrchestrationError("ORCHESTRATION_ARM_SET_MISMATCH")
        profiles = {item.deployment_profile for item in arms}
        if not {"EMBEDDED_FFM", "ISOLATED_SIDECAR"} <= profiles:
            raise OrchestrationError("ORCHESTRATION_ISOLATION_COVERAGE_MISSING")
        runs = tuple(
            self.runner.run(
                definition,
                arm,
                definition_id=definition_id,
                environment_manifest_id=environment_manifest_id,
                network_profile_id=definition.network_profile_ids[0],
                fault_profile_id=definition.fault_profile_ids[0],
                seed=seed,
                repetition=repetition,
            )
            for arm in arms
            for repetition, seed in enumerate(definition.seeds, start=1)
        )
        return OrchestrationResult(definition_id, runs)
