from __future__ import annotations

import pytest
from deltatorrent.benchmark.adapters import STAGE_RECEIPT_PATH, plan_arm_adapter
from deltatorrent.benchmark.capture import capture_environment, capture_fixture_metrics
from deltatorrent.benchmark.contracts import ContractError
from deltatorrent.benchmark.profiles import FOUNDATION_FAULT_EVENTS, validate_fault_corpus

from .conftest import (
    arm,
    cid,
    completed_run,
    fault_profile,
    fixture_receipts,
    network_profile,
    runtime_identity,
    scientific_profile,
)


def test_explicit_environment_capture_binds_runtime_build_locks_and_sbom() -> None:
    runtime = runtime_identity()
    captured = capture_environment(
        runtime_identity=runtime,
        binary_artifacts={
            "binary-build": b"fixture-binary-build",
            "java-binary": b"java-binary",
            "native-runtime": b"native-runtime",
            "python-wheel": b"python-wheel",
        },
        dependency_locks={
            "compiler-lock": b"compiler-lock",
            "java-lock": b"java-dependencies",
            "python-lock": b"python-lock",
        },
        sbom=b"fixture-sbom",
        image_manifest=b"fixture-image",
        hardware_inventory=b"fixture-hardware",
        capture_epoch_ms=1_800_000_000_000,
        environment_variable_names=("CUDA_HOME", "PATH"),
    )
    manifest = captured.manifest.to_dict()
    assert manifest["runtime_identity_id"] == runtime.content_id
    assert manifest["source_commit"] == runtime.to_dict()["source_commit"]
    assert manifest["sbom_id"] == cid("fixture-sbom")
    assert tuple(item.name for item in captured.artifacts) == tuple(
        sorted(item.name for item in captured.artifacts)
    )


def test_environment_capture_rejects_unbound_sbom_and_missing_lock() -> None:
    runtime = runtime_identity()
    kwargs = {
        "runtime_identity": runtime,
        "binary_artifacts": {
            "binary-build": b"fixture-binary-build",
            "native-runtime": b"native-runtime",
        },
        "dependency_locks": {
            "compiler-lock": b"compiler-lock",
            "java-lock": b"java-dependencies",
        },
        "sbom": b"fixture-sbom",
        "image_manifest": b"fixture-image",
        "hardware_inventory": b"fixture-hardware",
        "capture_epoch_ms": 1,
        "environment_variable_names": ("PATH",),
    }
    with pytest.raises(ContractError, match="LOCKS_MISSING"):
        capture_environment(**kwargs)
    kwargs["dependency_locks"] = {
        **kwargs["dependency_locks"],
        "python-lock": b"python-lock",
    }
    kwargs["sbom"] = b"different-sbom"
    with pytest.raises(ContractError, match="SBOM_MISMATCH"):
        capture_environment(**kwargs)


def test_arm_adapter_and_metric_capture_remain_fixture_only() -> None:
    runtime = runtime_identity()
    science = scientific_profile(repetitions=1, seeds=[17])
    benchmark_arm = arm(
        "candidate",
        kind="DELTAREDUCE",
        topology="HIERARCHICAL",
        deployment_profile="EMBEDDED_FFM",
    )
    plan = plan_arm_adapter(
        arm=benchmark_arm,
        runtime_identity=runtime,
        scientific_profile=science,
    )
    assert plan.ordered_receipt_stages == STAGE_RECEIPT_PATH
    assert plan.execution_authorized is False
    definition_id = cid("definition")
    receipts = fixture_receipts(
        definition_id,
        benchmark_arm.content_id,
        runtime,
        cid("ticket-1"),
    )
    run = completed_run(
        definition_id,
        benchmark_arm.content_id,
        science,
        network_profile(),
        fault_profile(),
        capture_environment(
            runtime_identity=runtime,
            binary_artifacts={
                "binary-build": b"fixture-binary-build",
                "native-runtime": b"native-runtime",
            },
            dependency_locks={
                "compiler-lock": b"compiler-lock",
                "java-lock": b"java-dependencies",
                "python-lock": b"python-lock",
            },
            sbom=b"fixture-sbom",
            image_manifest=b"fixture-image",
            hardware_inventory=b"fixture-hardware",
            capture_epoch_ms=1,
            environment_variable_names=("PATH",),
        ).manifest,
        cid("ticket-1"),
        receipts,
    )
    captured = capture_fixture_metrics(
        run_manifest=run,
        phase_timings=(
            ("compute", 0, 10),
            ("upload", 10, 20),
            ("availability", 20, 30),
            ("certificate", 30, 40),
            ("reduce", 40, 50),
            ("apply", 50, 60),
            ("p2p", 60, 70),
            ("wait", 70, 80),
        ),
        byte_counters={
            "duplicate_bytes": 0,
            "global_bytes": 1,
            "p2p_bytes": 3,
            "regional_bytes": 1,
            "retry_bytes": 0,
            "storage_bytes": 1,
            "validator_bytes": 1,
            "worker_bytes": 5,
        },
        gpu_device_id=cid("fixture-gpu"),
        gpu_memory_peak_bytes=100,
        gpu_sample_count=2,
        gpu_utilization_basis_points=5000,
        cpu_time_ns=17,
        p2p_bytes=3,
        peak_rss_bytes=200,
    )
    assert captured.to_dict()["run_id"] == run.to_dict()["run_id"]
    assert captured.to_dict()["primary_eligible"] is False


def test_full_model_arm_adapter_is_bound_but_remains_plan_only() -> None:
    runtime = runtime_identity()
    full_model_science = scientific_profile(model_mode="FULL_MODEL")
    full_model_arm = arm(
        "full-model",
        kind="REFERENCE",
        topology="FLAT",
        deployment_profile="EMBEDDED_FFM",
        model_mode="FULL_MODEL",
    )
    plan = plan_arm_adapter(
        arm=full_model_arm,
        runtime_identity=runtime,
        scientific_profile=full_model_science,
    )
    assert plan.model_mode == "FULL_MODEL"
    assert plan.execution_authorized is False
    assert plan.plan_class == "CONFORMANCE_ONLY"


def test_frozen_fault_corpus_covers_all_process_and_churn_kinds() -> None:
    events = [event.to_dict() for event in FOUNDATION_FAULT_EVENTS]
    corpus = (fault_profile(duration_ms=20_000, events=events),)
    validate_fault_corpus(corpus)
    with pytest.raises(ContractError, match="FAULT_CORPUS_INCOMPLETE"):
        validate_fault_corpus((fault_profile(duration_ms=20_000, events=events[:-1]),))
