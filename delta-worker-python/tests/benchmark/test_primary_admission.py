from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.benchmark.arms import ArmSpec, MetricSample, RunObservation
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.primary import (
    ExecutionPlan,
    PrimaryRunError,
    adapter_for,
    load_primary_arms,
)

ROOT = Path(__file__).resolve().parents[3]
DEFINITION = ROOT / "configs/benchmark/primary.yaml"
ARMS = ROOT / "configs/benchmark/arms-v1.json"


def inputs() -> tuple[BenchmarkDefinition, tuple[ArmSpec, ...]]:
    definition = BenchmarkDefinition.from_dict(json.loads(DEFINITION.read_text(encoding="utf-8")))
    return definition, load_primary_arms(ARMS, definition)


def observation(plan: ExecutionPlan) -> RunObservation:
    return RunObservation(
        definition_id=plan.definition_id,
        arm=plan.arm,
        environment_manifest_id=plan.environment_manifest_id,
        network_profile_id=plan.network_profile_id,
        fault_profile_id=plan.fault_profile_id,
        seed=plan.seed,
        repetition=plan.repetition,
        processed_tokens=plan.processed_tokens,
        domain_ticket_counts=tuple((item, 32) for item in plan.domains),
        terminal_outcome="APPLIED",
        protocol_hash="sha256:" + "1" * 64,
        checkpoint_id="sha256:" + "2" * 64,
        samples=(MetricSample("validation_loss_micro", 2_000_000, "micro-loss"),),
        phase_latencies_us=(("native_transition", 100),),
        bytes_sent=1024,
        useful_compute_us=9_000,
        total_us=10_000,
    )


def test_all_primary_arm_classes_plan_and_admit_exact_observations() -> None:
    definition, untyped_arms = inputs()
    arms = tuple(untyped_arms)
    assert {arm.topology for arm in arms} == {
        "FLAT_BFT",
        "HIERARCHICAL_BFT",
        "SINGLE_NODE_REFERENCE",
    }
    for arm in arms:
        adapter = adapter_for(arm)
        plan = adapter.plan(
            definition,
            arm,
            environment_manifest_id="sha256:" + "3" * 64,
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )
        measured = observation(plan)
        assert adapter.admit(plan, measured) is measured


def test_primary_observation_identity_drift_is_rejected() -> None:
    definition, arms = inputs()
    arm = arms[1]
    adapter = adapter_for(arm)
    plan = adapter.plan(
        definition,
        arm,
        environment_manifest_id="sha256:" + "3" * 64,
        network_profile_id=definition.network_profile_ids[0],
        fault_profile_id=definition.fault_profile_ids[0],
        seed=definition.seeds[0],
        repetition=1,
    )
    with pytest.raises(PrimaryRunError, match="PRIMARY_OBSERVATION_IDENTITY_DRIFT"):
        adapter.admit(plan, replace(observation(plan), processed_tokens=definition.B - 1))


def test_wrong_adapter_and_seed_are_rejected() -> None:
    definition, arms = inputs()
    reference = arms[0]
    flat_adapter = adapter_for(arms[1])
    with pytest.raises(PrimaryRunError, match="PRIMARY_ADAPTER_ARM_CLASS_MISMATCH"):
        flat_adapter.plan(
            definition,
            reference,
            environment_manifest_id="sha256:" + "3" * 64,
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )
    with pytest.raises(PrimaryRunError, match="PRIMARY_SEED_REPETITION_MISMATCH"):
        adapter_for(reference).plan(
            definition,
            reference,
            environment_manifest_id="sha256:" + "3" * 64,
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[1],
            repetition=1,
        )
