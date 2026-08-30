from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.benchmark.arms import ArmSpec, MetricSample, RunObservation
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.preregistration import PreregisteredDefinition
from deltatorrent.benchmark.primary import ExecutionPlan, load_primary_arms
from deltatorrent.benchmark.primary_executor import (
    PrimaryEnvironment,
    PrimaryExecutionStore,
    PrimaryExecutorError,
    build_execution_set,
    observation_record,
)
from deltatorrent.benchmark.review import GovernanceAttestation
from deltatorrent.cli.main import main
from deltatorrent.protocol.canonical import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[3]
DEFINITION = ROOT / "configs/benchmark/primary.yaml"
ATTESTATION = ROOT / "configs/benchmark/primary-definition-attestation.json"
ARMS = ROOT / "configs/benchmark/arms-v1.json"


def definition_and_arms() -> tuple[BenchmarkDefinition, tuple[ArmSpec, ...]]:
    definition = BenchmarkDefinition.from_dict(json.loads(DEFINITION.read_bytes()))
    return definition, load_primary_arms(ARMS, definition)


def environment_document(definition: BenchmarkDefinition) -> dict[str, object]:
    return {
        "abi_descriptor_id": definition.raw["abi_descriptor_id"],
        "accelerator": "NVIDIA_GEFORCE_RTX_3070_LAPTOP_GPU",
        "compiler_id": definition.raw["compiler_profile_id"],
        "dependency_lock_ids": definition.raw["dependency_lock_ids"],
        "formal_semantics_id": definition.raw["formal_semantics_id"],
        "hardware_id": "sha256:" + "1" * 64,
        "image_id": definition.raw["image_id"],
        "jdk_id": definition.raw["jdk_profile_id"],
        "netty_id": definition.raw["netty_profile_id"],
        "os_id": "sha256:" + "2" * 64,
        "python_id": definition.raw["python_profile_id"],
        "schema_version": "1.0.0",
        "source_commit": definition.source_commit,
        "source_tree": definition.source_tree,
        "time_sync_status": "BOUNDED",
        "type_name": "ENVIRONMENT_MANIFEST",
    }


def execution_inputs(tmp_path: Path):  # type: ignore[no-untyped-def]
    definition, arms = definition_and_arms()
    environment_path = tmp_path / "environment.json"
    environment_path.write_bytes(canonical_json_bytes(environment_document(definition)))
    environment = PrimaryEnvironment.load(environment_path, definition)
    attestation = GovernanceAttestation(
        body_id=definition.content_id,
        validator_set_id="sha256:" + "3" * 64,
        purpose="DEFINITION",
        f_b=1,
        ordered_signers=("benchmark-validator-0", "benchmark-validator-1", "benchmark-validator-2"),
    )
    execution = build_execution_set(
        PreregisteredDefinition(definition, attestation), arms, environment
    )
    return definition, arms, environment_path, execution


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
        domain_ticket_counts=tuple((domain, 32) for domain in plan.domains),
        terminal_outcome="APPLIED",
        protocol_hash="sha256:" + "4" * 64,
        checkpoint_id="sha256:" + "5" * 64,
        ticket_plan_id=plan.ticket_plan_id,
        parent_checkpoint_id=plan.parent_checkpoint_id,
        certificate_ids=()
        if plan.arm.kind == "SCIENTIFIC_REFERENCE"
        else tuple(
            [
                *("sha256:" + str(index) * 64 for index in range(6, 10)),
                "sha256:" + "a" * 64,
                "sha256:" + "b" * 64,
            ]
        ),
        model_artifact_id="sha256:" + "c" * 64,
        evaluation_artifact_ids=(
            "sha256:" + "d" * 64,
            "sha256:" + "e" * 64,
            "sha256:" + "f" * 64,
        ),
        samples=(MetricSample("validation_loss_micro", 2_000_000, "micro-loss"),),
        phase_latencies_us=(("native_transition", 100),),
        bytes_sent=1024,
        useful_compute_us=9_000,
        total_us=10_000,
        zero_copy_eligible=1,
        zero_copy_hits=1,
        copy_fallback_bytes=0,
        gpu_utilization_ppm=500_000,
        gpu_peak_reserved_bytes=3_000_000,
        host_offload_bytes=0,
    )


def test_primary_execution_matrix_is_complete_deterministic_and_not_evidence(
    tmp_path: Path,
) -> None:
    definition, arms, _, execution = execution_inputs(tmp_path)
    assert len(execution.plans) == len(arms) * definition.repetitions == 15
    assert len({plan.content_id for plan in execution.plans}) == 15
    assert {plan.seed for plan in execution.plans} == set(definition.seeds)
    assert execution.index["status"] == "PLANNED_NOT_EXECUTED"
    assert execution.index["execution_class"] == "PRIMARY_MEASURED_REQUIRED"

    store = PrimaryExecutionStore(tmp_path / "execution")
    first = store.stage(execution)
    assert store.stage(execution) == first
    assert len(tuple((tmp_path / "execution/plans").glob("*.json"))) == 15


def test_environment_drift_is_rejected_before_planning(tmp_path: Path) -> None:
    definition, _ = definition_and_arms()
    value = environment_document(definition)
    value["source_tree"] = "0" * 40
    path = tmp_path / "environment.json"
    path.write_bytes(canonical_json_bytes(value))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_ENVIRONMENT_DEFINITION_MISMATCH"):
        PrimaryEnvironment.load(path, definition)


def test_external_runner_observation_is_admitted_create_only(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    template = tmp_path / "measured-observation.json"
    template.write_bytes(canonical_json_bytes(observation_record(plan, observation(plan))))
    runner = tmp_path / "runner.py"
    runner.write_text(
        "from pathlib import Path\n"
        "import shutil, sys\n"
        "assert Path(sys.argv[2]).is_file()\n"
        "shutil.copyfile(sys.argv[1], sys.argv[3])\n",
        encoding="utf-8",
    )
    store = PrimaryExecutionStore(tmp_path / "execution")
    store.stage(execution)
    admitted = store.execute_plan(
        plan,
        (sys.executable, str(runner), str(template)),
        timeout_seconds=30,
    )
    assert admitted.content_id == observation(plan).content_id
    assert (
        store.execute_plan(
            plan,
            ("runner-is-not-reexecuted-for-an-admitted-plan",),
            timeout_seconds=30,
        ).content_id
        == admitted.content_id
    )


def test_identity_drift_and_failed_runner_leave_no_admitted_observation(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    store = PrimaryExecutionStore(tmp_path / "execution")
    store.stage(execution)
    drifted = observation_record(plan, observation(plan))
    manifest = drifted["run_manifest"]
    assert isinstance(manifest, dict)
    manifest["processed_tokens"] = plan.processed_tokens - 1
    path = tmp_path / "drifted.json"
    path.write_bytes(canonical_json_bytes(drifted))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_OBSERVATION_IDENTITY_DRIFT"):
        store.admit_file(plan, path)
    assert not store.observation_path(plan).exists()

    runner = tmp_path / "failed-runner.py"
    runner.write_text("raise SystemExit(7)\n", encoding="utf-8")
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_EXIT_7"):
        store.execute_plan(plan, (sys.executable, str(runner)), timeout_seconds=30)
    assert not store.observation_path(plan).exists()


def test_remote_collection_is_partial_until_complete_run_set_reconciles(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    paths: list[Path] = []
    for index, plan in enumerate(execution.plans):
        path = incoming / f"observation-{index}.json"
        path.write_bytes(canonical_json_bytes(observation_record(plan, observation(plan))))
        paths.append(path)

    store = PrimaryExecutionStore(tmp_path / "execution")
    store.collect(execution, (paths[0],))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUN_SET_INCOMPLETE"):
        store.load_complete(execution)
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_OBSERVATION_PLAN_DUPLICATE"):
        store.collect(execution, (paths[1], paths[1]))

    store.collect(execution, tuple(paths[1:]))
    complete = store.load_complete(execution)
    assert len(complete) == len(execution.plans) == 15


def test_plan_primary_cli_stages_only_non_evidence_plans(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    definition, _, environment_path, _ = execution_inputs(tmp_path)
    output = tmp_path / "cli-execution"
    assert (
        main(
            (
                "benchmark",
                "plan-primary",
                str(DEFINITION),
                str(ATTESTATION),
                str(ARMS),
                str(environment_path),
                str(output),
            )
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["definition_id"] == definition.content_id
    assert result["plan_count"] == 15
    assert result["status"] == "PLANNED_NOT_EXECUTED"
    assert not (output / "runs").exists()


def test_observation_helper_rejects_mismatched_plan() -> None:
    definition, arms = definition_and_arms()
    first = ExecutionPlan(
        definition.content_id,
        arms[0],
        "sha256:" + "0" * 64,
        definition.network_profile_ids[0],
        definition.fault_profile_ids[0],
        definition.seeds[0],
        1,
        definition.B,
        tuple(item.domain_id for item in definition.domain_weights),
        definition.ticket_plan_id,
        definition.base_model_id,
        definition.evaluation_ids,
    )
    second = replace(first, seed=definition.seeds[1], repetition=2)
    with pytest.raises(ValueError, match="PRIMARY_OBSERVATION_IDENTITY_DRIFT"):
        observation_record(second, observation(first))
