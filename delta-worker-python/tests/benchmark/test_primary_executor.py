from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
import time
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
    identify_runner,
    observation_record,
    parse_observation,
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
    command = (sys.executable, str(runner), str(template))
    runner_id = identify_runner(command)
    admitted = store.execute_plan(
        plan,
        command,
        runner_id=runner_id,
        timeout_seconds=30,
    )
    assert admitted.content_id == observation(plan).content_id
    assert (
        store.execute_plan(
            plan,
            ("runner-is-not-reexecuted-for-an-admitted-plan",),
            runner_id=runner_id,
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
    command = (sys.executable, str(runner))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_EXIT_7"):
        store.execute_plan(
            plan,
            command,
            runner_id=identify_runner(command),
            timeout_seconds=30,
        )
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


def _copy_runner(tmp_path: Path, record: Path, *, noisy: bool = False) -> tuple[str, ...]:
    runner = tmp_path / ("noisy-runner.py" if noisy else "copy-runner.py")
    runner.write_text(
        "from pathlib import Path\n"
        "import os, sys\n"
        "assert 'DELTA_TEST_SECRET' not in os.environ\n"
        + ("print('x' * 200000)\n" if noisy else "")
        + "Path(sys.argv[3]).write_bytes(Path(sys.argv[1]).read_bytes())\n",
        encoding="utf-8",
    )
    return (sys.executable, str(runner), str(record))


def test_primary_observation_negative_identity_and_artifact_matrix(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    distributed = next(plan for plan in execution.plans if plan.arm.kind != "SCIENTIFIC_REFERENCE")
    base = observation_record(distributed, observation(distributed))
    other_arm = next(plan for plan in execution.plans if plan.arm != distributed.arm)

    def manifest(document: dict[str, object]) -> dict[str, object]:
        value = document["run_manifest"]
        assert isinstance(value, dict)
        return value

    def mutations() -> tuple[tuple[str, object], ...]:
        return (
            (
                "wrong_plan",
                lambda value: value.__setitem__("execution_plan_id", "sha256:" + "0" * 64),
            ),
            (
                "wrong_definition",
                lambda value: manifest(value).__setitem__(
                    "benchmark_definition_id", "sha256:" + "0" * 64
                ),
            ),
            (
                "wrong_arm",
                lambda value: manifest(value).__setitem__("arm_id", other_arm.arm.content_id),
            ),
            ("wrong_seed", lambda value: manifest(value).__setitem__("seed", distributed.seed + 1)),
            (
                "wrong_repetition",
                lambda value: manifest(value).__setitem__(
                    "repetition", distributed.repetition % 3 + 1
                ),
            ),
            (
                "wrong_environment",
                lambda value: manifest(value).__setitem__(
                    "environment_manifest_id", "sha256:" + "1" * 64
                ),
            ),
            (
                "wrong_network",
                lambda value: manifest(value).__setitem__(
                    "network_profile_id", "sha256:" + "2" * 64
                ),
            ),
            (
                "wrong_fault",
                lambda value: manifest(value).__setitem__("fault_profile_id", "sha256:" + "3" * 64),
            ),
            (
                "wrong_tokens",
                lambda value: manifest(value).__setitem__(
                    "processed_tokens", distributed.processed_tokens - 1
                ),
            ),
            (
                "wrong_ticket_plan",
                lambda value: manifest(value).__setitem__("ticket_plan_id", "sha256:" + "4" * 64),
            ),
            (
                "missing_certificates",
                lambda value: manifest(value).__setitem__("certificate_ids", []),
            ),
            (
                "missing_evaluations",
                lambda value: manifest(value).__setitem__("evaluation_artifact_ids", []),
            ),
            (
                "duplicate_artifacts",
                lambda value: manifest(value).__setitem__(
                    "certificate_ids",
                    [
                        *manifest(value)["certificate_ids"],  # type: ignore[index]
                        manifest(value)["certificate_ids"][0],  # type: ignore[index]
                    ],
                ),
            ),
        )

    store = PrimaryExecutionStore(tmp_path / "negative-store")
    for case, mutate in mutations():
        document = json.loads(canonical_json_bytes(base))
        assert callable(mutate)
        mutate(document)
        path = tmp_path / f"{case}.json"
        path.write_bytes(canonical_json_bytes(document))
        with pytest.raises(PrimaryExecutorError):
            store.admit_file(distributed, path)
        assert not store.observation_path(distributed).exists()


def test_noncanonical_partial_and_synthetic_artifacts_are_rejected(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    store = PrimaryExecutionStore(tmp_path / "store")
    partial = tmp_path / "partial.json"
    partial.write_bytes(b'{"type_name":"PRIMARY_RUN_OBSERVATION"')
    synthetic = tmp_path / "synthetic.json"
    synthetic.write_bytes(
        canonical_json_bytes(
            {
                "fixture_class": "SYNTHETIC_NOT_PRIMARY_EVIDENCE",
                "type_name": "SYNTHETIC_BENCHMARK_RESULT",
            }
        )
    )
    for path in (partial, synthetic):
        with pytest.raises(PrimaryExecutorError, match="PRIMARY_OBSERVATION_INVALID"):
            store.admit_file(plan, path)
    assert not store.observation_path(plan).exists()


def test_create_only_concurrent_publishers_are_idempotent_or_conflict(
    tmp_path: Path,
) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    first = tmp_path / "first.json"
    first.write_bytes(canonical_json_bytes(observation_record(plan, observation(plan))))
    conflicting_observation = replace(
        observation(plan),
        samples=(MetricSample("validation_loss_micro", 2_000_001, "micro-loss"),),
    )
    second_value = observation_record(plan, conflicting_observation)
    second = tmp_path / "second.json"
    second.write_bytes(canonical_json_bytes(second_value))
    store = PrimaryExecutionStore(tmp_path / "store")

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        same_results = list(pool.map(lambda _: store.admit_file(plan, first), range(64)))
    assert len({item.content_id for item in same_results}) == 1

    outcomes: list[str] = []

    def publish(path: Path) -> None:
        try:
            store.admit_file(plan, path)
            outcomes.append("PASS")
        except PrimaryExecutorError as exc:
            outcomes.append(str(exc))

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(publish, (first, second)))
    assert outcomes.count("PASS") == 1
    assert outcomes.count("PRIMARY_EXECUTION_IMMUTABLE_CONFLICT") == 1
    admitted, _ = parse_observation(store.observation_path(plan), plan)
    assert admitted.content_id == observation(plan).content_id


def test_partial_publisher_failure_exposes_no_final_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import deltatorrent.benchmark.primary_executor as executor_module

    _, _, _, execution = execution_inputs(tmp_path)
    store = PrimaryExecutionStore(tmp_path / "store")

    def fail_link(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected crash before atomic publication")

    monkeypatch.setattr(executor_module.os, "link", fail_link)
    with pytest.raises(OSError, match="injected crash"):
        store.stage(execution)
    assert not (store.root / "environment-manifest.json").exists()
    assert not tuple(store.root.rglob(".publish.*.tmp"))


def test_symlink_escape_and_result_substitution_are_rejected_or_snapshot_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import deltatorrent.benchmark.primary_executor as executor_module

    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    incoming = tmp_path / "incoming.json"
    original = canonical_json_bytes(observation_record(plan, observation(plan)))
    incoming.write_bytes(original)
    symlink = tmp_path / "incoming-link.json"
    try:
        symlink.symlink_to(incoming)
    except OSError:
        pass
    else:
        with pytest.raises(PrimaryExecutorError, match="PRIMARY_OBSERVATION_INVALID"):
            PrimaryExecutionStore(tmp_path / "symlink-store").admit_file(plan, symlink)

    escape_store = PrimaryExecutionStore(tmp_path / "escape-store")
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (escape_store.root / "runs").symlink_to(outside, target_is_directory=True)
    except OSError:
        pass
    else:
        with pytest.raises(PrimaryExecutorError, match="PRIMARY_EXECUTION_STORE_SYMLINK_FORBIDDEN"):
            escape_store.admit_file(plan, incoming)
        assert not tuple(outside.rglob("observation.json"))

    real_publish = executor_module._publish_create_only

    def substitute(root: Path, target: Path, value: bytes) -> None:
        incoming.write_bytes(b"substituted-after-parse")
        real_publish(root, target, value)

    monkeypatch.setattr(executor_module, "_publish_create_only", substitute)
    store = PrimaryExecutionStore(tmp_path / "snapshot-store")
    store.admit_file(plan, incoming)
    assert store.observation_path(plan).read_bytes() == original


def test_external_runner_is_pinned_secret_free_bounded_and_receipted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    record = tmp_path / "record.json"
    record.write_bytes(canonical_json_bytes(observation_record(plan, observation(plan))))
    command = _copy_runner(tmp_path, record, noisy=True)
    runner_id = identify_runner(command)
    monkeypatch.setenv("DELTA_TEST_SECRET", "must-not-be-inherited")
    store = PrimaryExecutionStore(tmp_path / "store")
    store.stage(execution)
    result = store.execute_plan(
        plan,
        command,
        runner_id=runner_id,
        timeout_seconds=30,
    )
    assert result.content_id == observation(plan).content_id
    receipt = json.loads(store.receipt_path(plan, runner_id, "PASS").read_bytes())
    assert receipt["exit_code"] == 0
    assert receipt["signal"] is None
    assert receipt["stdout_bytes"] > 65_536
    assert receipt["stdout_truncated"] is True
    assert "stdout" not in receipt


def test_runner_missing_nonzero_timeout_and_identity_mismatch_fail_closed(
    tmp_path: Path,
) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    store = PrimaryExecutionStore(tmp_path / "store")
    store.stage(execution)
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_EXECUTABLE_INVALID"):
        identify_runner((str(tmp_path / "missing-runner"),))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_EXECUTABLE_INVALID"):
        store.execute_plan(
            plan,
            (str(tmp_path / "missing-runner"),),
            runner_id="sha256:" + "0" * 64,
            timeout_seconds=30,
        )

    no_output = tmp_path / "no-output.py"
    no_output.write_text("raise SystemExit(0)\n", encoding="utf-8")
    no_output_command = (sys.executable, str(no_output))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_OBSERVATION_MISSING"):
        store.execute_plan(
            plan,
            no_output_command,
            runner_id=identify_runner(no_output_command),
            timeout_seconds=30,
        )

    failed = tmp_path / "failed.py"
    failed.write_text("raise SystemExit(13)\n", encoding="utf-8")
    failed_command = (sys.executable, str(failed))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_ID_MISMATCH"):
        store.execute_plan(
            plan,
            failed_command,
            runner_id="sha256:" + "0" * 64,
            timeout_seconds=30,
        )
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_EXIT_13"):
        store.execute_plan(
            plan,
            failed_command,
            runner_id=identify_runner(failed_command),
            timeout_seconds=30,
        )
    assert not store.observation_path(plan).exists()

    timeout = tmp_path / "timeout.py"
    timeout.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    timeout_command = (sys.executable, str(timeout))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_TIMEOUT"):
        store.execute_plan(
            plan,
            timeout_command,
            runner_id=identify_runner(timeout_command),
            timeout_seconds=1,
        )
    assert not store.observation_path(plan).exists()


def test_sealed_plan_mutation_is_rejected_before_runner_launch(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    record = tmp_path / "record.json"
    record.write_bytes(canonical_json_bytes(observation_record(plan, observation(plan))))
    command = _copy_runner(tmp_path, record)
    store = PrimaryExecutionStore(tmp_path / "store")
    store.stage(execution)
    plan_path = store.plan_path(plan)
    mutated = json.loads(plan_path.read_bytes())
    value = mutated["value"]
    assert isinstance(value, dict)
    value["seed"] = plan.seed + 1
    plan_path.write_bytes(canonical_json_bytes(mutated))
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_EXECUTION_PLAN_INVALID"):
        store.execute_plan(
            plan,
            command,
            runner_id=identify_runner(command),
            timeout_seconds=30,
        )


def test_runner_dependency_mutation_is_rejected(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    record = tmp_path / "record.json"
    record.write_bytes(canonical_json_bytes(observation_record(plan, observation(plan))))
    runner = tmp_path / "mutating-runner.py"
    runner.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "source=Path(sys.argv[1])\n"
        "Path(sys.argv[3]).write_bytes(source.read_bytes())\n"
        "source.write_bytes(b'mutated')\n",
        encoding="utf-8",
    )
    command = (sys.executable, str(runner), str(record))
    store = PrimaryExecutionStore(tmp_path / "store")
    store.stage(execution)
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_DEPENDENCY_MUTATED"):
        store.execute_plan(
            plan,
            command,
            runner_id=identify_runner(command),
            timeout_seconds=30,
        )
    assert not store.observation_path(plan).exists()


def test_runner_timeout_terminates_process_tree(tmp_path: Path) -> None:
    _, _, _, execution = execution_inputs(tmp_path)
    plan = execution.plans[0]
    pid_file = tmp_path / "child.pid"
    runner = tmp_path / "tree.py"
    runner.write_text(
        "from pathlib import Path\n"
        "import subprocess, sys, time\n"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\n"
        "Path(sys.argv[1]).write_text(str(child.pid))\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    command = (sys.executable, str(runner), str(pid_file))
    store = PrimaryExecutionStore(tmp_path / "store")
    store.stage(execution)
    with pytest.raises(PrimaryExecutorError, match="PRIMARY_RUNNER_TIMEOUT"):
        store.execute_plan(
            plan,
            command,
            runner_id=identify_runner(command),
            timeout_seconds=1,
        )
    child_pid = int(pid_file.read_text())
    for _ in range(50):
        try:
            os.kill(child_pid, 0)
        except OSError:
            break
        time.sleep(0.02)
    else:
        if os.name == "nt":
            subprocess.run(
                ("taskkill", "/PID", str(child_pid), "/F"),
                check=False,
                capture_output=True,
            )
        pytest.fail("runner child process survived the hard timeout")


def test_cli_primary_runner_round_trip_and_cross_definition_rejection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    definition, _, environment_path, execution = execution_inputs(tmp_path)
    output = tmp_path / "cli-store"
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    records: list[Path] = []
    for index, plan in enumerate(execution.plans):
        path = incoming / f"{index}.json"
        path.write_bytes(canonical_json_bytes(observation_record(plan, observation(plan))))
        records.append(path)
    bundle = tmp_path / "runner-bundle.json"
    bundle.write_bytes(
        canonical_json_bytes(
            {
                plan.content_id: observation_record(plan, observation(plan))
                for plan in execution.plans
            }
        )
    )
    runner = tmp_path / "bundle-runner.py"
    runner.write_text(
        "from pathlib import Path\n"
        "import json, sys\n"
        "bundle=json.loads(Path(sys.argv[1]).read_bytes())\n"
        "plan=json.loads(Path(sys.argv[2]).read_bytes())\n"
        "raw=json.dumps(bundle[plan['content_id']],sort_keys=True,separators=(',',':')).encode()\n"
        "Path(sys.argv[3]).write_bytes(raw)\n",
        encoding="utf-8",
    )
    command = (sys.executable, str(runner), str(bundle))
    runner_id = identify_runner(command)

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
    capsys.readouterr()
    assert (
        main(
            (
                "benchmark",
                "execute-primary",
                "--timeout-seconds",
                "30",
                "--runner-id",
                runner_id,
                str(DEFINITION),
                str(ATTESTATION),
                str(ARMS),
                str(environment_path),
                str(output),
                "--",
                *command,
            )
        )
        == 0
    )
    executed = json.loads(capsys.readouterr().out)
    assert executed["status"] == "RUNS_ADMITTED_NOT_EVALUATED"
    assert executed["run_count"] == 15
    assert (
        main(
            (
                "benchmark",
                "collect-primary",
                str(DEFINITION),
                str(ATTESTATION),
                str(ARMS),
                str(environment_path),
                str(output),
                *(str(path) for path in records),
            )
        )
        == 0
    )
    collected = json.loads(capsys.readouterr().out)
    assert collected["status"] == "COMPLETE_RUN_SET_ADMITTED_NOT_EVALUATED"
    assert (
        main(
            (
                "benchmark",
                "verify-primary-runs",
                str(DEFINITION),
                str(ATTESTATION),
                str(ARMS),
                str(environment_path),
                str(output),
            )
        )
        == 0
    )
    verified = json.loads(capsys.readouterr().out)
    assert verified == {
        "definition_id": definition.content_id,
        "run_count": 15,
        "status": "RUN_SET_COMPLETE_NOT_GATE_EVALUATED",
    }

    wrong = json.loads(records[0].read_bytes())
    wrong_manifest = wrong["run_manifest"]
    assert isinstance(wrong_manifest, dict)
    wrong_manifest["benchmark_definition_id"] = "sha256:" + "0" * 64
    wrong_path = tmp_path / "wrong-definition.json"
    wrong_path.write_bytes(canonical_json_bytes(wrong))
    rejected_store = PrimaryExecutionStore(tmp_path / "rejected-store")
    with pytest.raises(PrimaryExecutorError):
        rejected_store.collect(execution, (wrong_path,))
