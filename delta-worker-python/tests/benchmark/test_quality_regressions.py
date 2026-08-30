from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.benchmark.arms import ArmSpec, RunObservation, SyntheticArmRunner
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.quality import analyze_quality
from deltatorrent.benchmark.reconciliation import ReconciliationError, reconcile

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json"


def fixture_inputs() -> tuple[BenchmarkDefinition, tuple[ArmSpec, ...]]:
    artifacts = json.loads(FIXTURE.read_text(encoding="utf-8"))["artifacts"]
    value = copy.deepcopy(artifacts["definition"]["value"])
    downstream = copy.deepcopy(value["metric_definitions"][1])
    downstream.update(
        {
            "direction": "HIGHER",
            "metric_id": "downstream_accuracy_ppm",
            "pass_threshold": 100,
            "unit": "ppm",
        }
    )
    value["metric_definitions"] = [value["metric_definitions"][0], downstream]
    definition = BenchmarkDefinition.from_dict(value)
    arms = tuple(
        ArmSpec.from_wrapper(artifacts[key])
        for key in ("arm_reference", "arm_embedded", "arm_sidecar")
    )
    return definition, arms


def runs() -> tuple[BenchmarkDefinition, tuple[RunObservation, ...]]:
    definition, arms = fixture_inputs()
    runner = SyntheticArmRunner()
    observations = tuple(
        runner.run(
            definition,
            arm,
            definition_id=definition.content_id,
            environment_manifest_id="sha256:" + "3" * 64,
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=seed,
            repetition=repetition,
        )
        for arm in arms
        for repetition, seed in enumerate(definition.seeds, start=1)
    )
    return definition, observations


def test_normal_loss_cannot_hide_downstream_noninferiority_failure() -> None:
    definition, untyped_runs = runs()
    observations = tuple(untyped_runs)
    reconciliation = reconcile(definition, observations)
    result = analyze_quality(definition, definition.content_id, observations, reconciliation)
    assert result.status == "FAIL"
    assert any(
        item["metric_id"] == "downstream_accuracy_ppm" and item["degradation"] > 100
        for item in result.document["metrics"]
    )


def test_missing_seed_and_environment_drift_fail_before_quality() -> None:
    definition, untyped_runs = runs()
    observations = tuple(untyped_runs)
    with pytest.raises(ReconciliationError, match="RUN_REPETITION_SET_MISMATCH"):
        reconcile(definition, observations[:-1])
    with pytest.raises(ReconciliationError, match="RUN_ENVIRONMENT_DRIFT"):
        reconcile(
            definition,
            (
                *observations[:-1],
                replace(observations[-1], environment_manifest_id="sha256:" + "4" * 64),
            ),
        )


def test_domain_and_token_drift_fail_before_quality() -> None:
    definition, untyped_runs = runs()
    observations = tuple(untyped_runs)
    with pytest.raises(ReconciliationError, match="RUN_TOKEN_EXPOSURE_MISMATCH"):
        reconcile(definition, (replace(observations[0], processed_tokens=7), *observations[1:]))
    with pytest.raises(ReconciliationError, match="RUN_DOMAIN_EXPOSURE_MISMATCH"):
        reconcile(
            definition,
            (
                replace(observations[0], domain_ticket_counts=(("wrong-domain", 1),)),
                *observations[1:],
            ),
        )
