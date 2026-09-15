from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import fields
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from deltatorrent.benchmark import mnist_demo
from deltatorrent.benchmark.mnist_delta_nodes import (
    MODEL_MAGIC,
    VECTOR_WIDTH,
    AppliedModel,
    DeltaExecutionResult,
    NodeContribution,
    expected_central_model,
)
from deltatorrent.benchmark.mnist_demo import (
    MNIST_FILES,
    MnistDataset,
    MnistDemoError,
    NodeSummary,
    compute_summary,
    materialize_node_shards,
    prepare_mnist_cache,
    run_mnist_demo,
    run_node_summaries,
)
from deltatorrent.benchmark.mnist_demo_workspace import (
    WORKSPACE_HTML,
    _validate_workspace_report,
    serve_workspace,
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _synthetic_dataset() -> MnistDataset:
    train_labels = np.repeat(np.arange(10, dtype=np.uint8), 6)
    test_labels = np.repeat(np.arange(10, dtype=np.uint8), 2)

    def image(digit: int, variation: int) -> np.ndarray:
        value = np.zeros((28, 28), dtype=np.uint8)
        row = digit * 2 + 2
        column = 25 - digit * 2
        value[row : row + 2, 3:25] = 180 + variation
        value[3:25, column : column + 2] = 220 + variation
        return value

    train_images = np.stack(
        [image(int(digit), index % 2) for index, digit in enumerate(train_labels)]
    )
    test_images = np.stack(
        [image(int(digit), index % 2) for index, digit in enumerate(test_labels)]
    )
    return MnistDataset(
        source_id="sha256:" + "1" * 64,
        train_images=np.asarray(train_images, dtype=np.uint8),
        train_labels=train_labels,
        test_images=np.asarray(test_images, dtype=np.uint8),
        test_labels=test_labels,
    )


def _patch_dataset(monkeypatch: pytest.MonkeyPatch, dataset: MnistDataset) -> None:
    monkeypatch.setattr(
        mnist_demo,
        "prepare_mnist_cache",
        lambda _cache, *, allow_download: {
            "source_id": dataset.source_id,
            "download_was_allowed": allow_download,
        },
    )
    monkeypatch.setattr(mnist_demo, "load_mnist", lambda _cache, _source_id: dataset)


def _patch_delta_nodes(monkeypatch: pytest.MonkeyPatch, dataset: MnistDataset) -> None:
    central_sums, central_counts = compute_summary(dataset.train_images, dataset.train_labels)
    central_values = expected_central_model(central_sums, central_counts)

    def fake_delta_nodes(
        _root: Path,
        destination: Path,
        _controllers: Path,
        node_contributions: tuple[NodeContribution, ...],
        _source_id: str,
        *,
        toolchain: object = None,
    ) -> DeltaExecutionResult:
        del toolchain
        destination.mkdir(parents=True)
        trace_path = destination / "execution-trace.json"
        diagram_path = destination / "execution-path.mmd"
        trace_path.write_text('{"status":"PASS"}\n', encoding="utf-8")
        diagram_path.write_text("flowchart LR\n", encoding="utf-8")
        raw = MODEL_MAGIC + struct.pack(">I", VECTOR_WIDTH) + central_values.astype(">i2").tobytes()
        model = AppliedModel(
            raw_bytes=raw,
            content_id=f"sha256:{hashlib.sha256(raw).hexdigest()}",
            centroids=central_values[: 10 * 28 * 28].reshape(10, 28 * 28).astype(np.int64),
            presence=central_values[10 * 28 * 28 :].astype(np.int64),
            values=central_values,
        )
        delta_execution: dict[str, object] = {
            "aggregation_authority": "delta::robust::reduce_parameter_shard",
            "applied_model_file_sha256": model.content_id,
            "components": [
                {"component": name, "evidence": {}, "sequence": index, "status": "PASS"}
                for index, name in enumerate(
                    (
                        "deltatorrent.benchmark.mnist_demo",
                        "io.deltareduce.demo.MnistDeltaNettyRelay",
                        "delta::runtime::CertificateVoteRuntime",
                        "delta::certificates::ChainVerifier",
                        "delta::robust::build_plan",
                        "delta::robust::reduce_parameter_shard",
                        "delta::apply::compute_candidate",
                        "delta::runtime::CurrentPointerStore",
                    ),
                    start=1,
                )
            ],
            "contributions_bound_netty_to_native": True,
            "execution_path_id": "sha256:" + "2" * 64,
            "distributed_orchestrator_received_node_local_numeric_arrays": False,
            "python_cross_node_aggregation_performed": False,
            "status": "PASS",
            "terminal_outcome": "APPLIED",
            "toolchain": {
                "source_snapshot": {
                    "no_hidden_aggregation_static_gate": "PASS",
                    "semantic_completeness_claimed": False,
                }
            },
        }
        return DeltaExecutionResult(
            applied_model=model,
            delta_execution=delta_execution,
            execution_trace_path=trace_path,
            execution_diagram_path=diagram_path,
            failure_simulation={
                "failed_node_id": "validator-04",
                "protocol_accepted_after_recovery": True,
                "replay_observed": True,
                "status": "RECOVERED_AND_APPLIED",
                "terminal_outcome": "APPLIED",
            },
            node_contributions=node_contributions,
        )

    monkeypatch.setattr(mnist_demo, "run_delta_nodes", fake_delta_nodes)


def test_mnist_sources_are_content_pinned() -> None:
    assert len(MNIST_FILES) == 4
    assert len({item.filename for item in MNIST_FILES}) == 4
    assert all(len(item.sha256) == 64 for item in MNIST_FILES)
    assert all(item.size_bytes > 0 for item in MNIST_FILES)
    assert all(item.url.startswith("https://storage.googleapis.com/") for item in MNIST_FILES)


def test_offline_cache_fails_closed_when_a_pinned_source_is_missing(tmp_path: Path) -> None:
    with pytest.raises(MnistDemoError, match="MNIST_SOURCE_MISSING_OFFLINE"):
        prepare_mnist_cache(tmp_path / "empty-cache", allow_download=False)


def test_four_label_skew_shards_are_disjoint_and_exact(tmp_path: Path) -> None:
    dataset = _synthetic_dataset()
    manifests = materialize_node_shards(
        dataset.train_images,
        dataset.train_labels,
        tmp_path / "nodes",
    )

    assert len(manifests) == 4
    observed_counts = np.sum(
        np.asarray([manifest["label_counts"] for manifest in manifests], dtype=np.int64),
        axis=0,
    )
    assert np.array_equal(observed_counts, np.bincount(dataset.train_labels, minlength=10))
    for manifest in manifests:
        allowed = set(cast(list[int], manifest["allowed_digits"]))
        counts = cast(list[int], manifest["label_counts"])
        assert all(count == 0 for digit, count in enumerate(counts) if digit not in allowed)


def test_workers_return_opaque_contributions_not_numeric_model_sums(tmp_path: Path) -> None:
    dataset = _synthetic_dataset()
    node_root = tmp_path / "nodes"
    manifests = materialize_node_shards(dataset.train_images, dataset.train_labels, node_root)
    node_dirs = tuple(node_root / f"demo-mnist-worker-{index:02d}" for index in range(1, 5))
    shard_ids = {
        cast(str, manifest["node_id"]): cast(str, manifest["shard_id"]) for manifest in manifests
    }
    summaries = run_node_summaries(node_dirs, shard_ids)
    assert len(summaries) == 4
    assert len({summary.process_id for summary in summaries}) == 4
    assert sum(summary.contribution.sample_count for summary in summaries) == int(
        dataset.train_labels.size
    )
    for summary in summaries:
        assert summary.contribution.record_path.is_file()
        assert summary.contribution.size_bytes == summary.contribution.record_path.stat().st_size
        assert not hasattr(summary, "counts")
        assert not hasattr(summary, "sums")


def test_production_demo_has_no_cross_node_python_aggregation() -> None:
    root = _repository_root()
    demo_source = (root / "delta-worker-python/src/deltatorrent/benchmark/mnist_demo.py").read_text(
        encoding="utf-8"
    )
    integration_source = (
        root / "delta-worker-python/src/deltatorrent/benchmark/mnist_delta_nodes.py"
    ).read_text(encoding="utf-8")
    native_source = (root / "integration/mnist-delta/native/mnist_delta_node.cpp").read_text(
        encoding="utf-8"
    )
    java_source = (
        root / "integration/mnist-delta/java/io/deltareduce/demo/MnistDeltaNettyRelay.java"
    ).read_text(encoding="utf-8")

    assert "def aggregate_summaries" not in demo_source
    assert "def aggregate_summaries" not in integration_source
    assert "node_contributions: Sequence[NodeContribution]" in integration_source
    assert "tuple(summary.contribution for summary in node_summaries)" in demo_source
    assert "sums" not in {field.name for field in fields(NodeSummary)}
    assert "run_delta_nodes(" in demo_source
    assert "delta::robust::reduce_parameter_shard" in native_source
    assert "certificates::ChainVerifier" in native_source
    assert "delta::apply::compute_candidate" in native_source
    assert "runtime::CurrentPointerStore" in native_source
    assert "BenchmarkTransport" in java_source
    assert "NioServerSocketChannel" in java_source


def test_checked_in_trace_excerpt_documents_observed_delta_execution_path() -> None:
    trace = json.loads(
        (_repository_root() / "integration/mnist-delta/example-execution-trace.json").read_text(
            encoding="utf-8"
        )
    )
    expected_components = [
        "deltatorrent.benchmark.mnist_demo",
        "io.deltareduce.demo.MnistDeltaNettyRelay",
        "delta::runtime::CertificateVoteRuntime",
        "delta::certificates::ChainVerifier",
        "delta::robust::build_plan",
        "delta::robust::reduce_parameter_shard",
        "delta::apply::compute_candidate",
        "delta::runtime::CurrentPointerStore",
    ]

    assert trace["type_name"] == "MNIST_DELTA_VERIFIED_RUN_TRACE_EXCERPT"
    assert trace["actual_run"] is True
    assert trace["classification"] == "LOCAL_DEMO_ONLY"
    assert trace["authoritative"] is False
    assert trace["governance_eligible"] is False
    assert trace["terminal_outcome"] == "APPLIED"
    assert trace["python_cross_node_aggregation_performed"] is False
    assert trace["exact_model_match_with_centralized"] is True
    assert trace["centralized_accuracy_ppm"] == trace["distributed_accuracy_ppm"]
    assert trace["dataset"]["train_samples"] == 60_000
    assert trace["dataset"]["test_samples"] == 10_000
    assert trace["toolchain"]["java_feature"] == 25
    assert trace["network"]["ed25519_verified"] is True
    assert trace["network"]["native_receipts_bound_contribution_ids"] is True
    assert trace["network"]["netty_loopback_receipts"] == 8
    assert len(trace["contribution_ids"]) == 4
    assert trace["native_results"] == {"applied": 4, "votes_exposed": 4}
    assert [item["component"] for item in trace["components"]] == expected_components
    assert [item["sequence"] for item in trace["components"]] == list(range(1, 9))
    assert all(item["status"] == "PASS" for item in trace["components"])
    assert len(trace["quorum_certificates"]) == 6
    assert all(item["threshold"] == 3 for item in trace["quorum_certificates"])
    assert all(item["signer_count"] == 4 for item in trace["quorum_certificates"])
    assert trace["recovery"]["crash_point"] == ("AFTER_DURABLE_APPLY_VOTE_BEFORE_EXPOSE")
    assert trace["recovery"]["replay_observed"] is True
    assert trace["recovery"]["status"] == "RECOVERED_AND_APPLIED"
    assert trace["source_execution_trace_bytes"] > 100_000
    assert trace["source_execution_trace_sha256"].startswith("sha256:")


def test_run_uses_applied_delta_model_and_real_recovery_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _synthetic_dataset()
    _patch_dataset(monkeypatch, dataset)
    _patch_delta_nodes(monkeypatch, dataset)

    result = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run",
        allow_download=False,
    )
    report = json.loads(result.report_json.read_text(encoding="utf-8"))

    assert report["demo_status"] == "DEMO_PASS"
    assert report["authoritative"] is False
    assert report["governance_eligible"] is False
    assert report["execution_authorized"] is False
    assert report["feature_010_go_claimed"] is False
    assert report["dataset"]["name"] == "MNIST"
    assert report["distributed"]["exact_model_match_with_centralized"] is True
    assert report["distributed"]["aggregation_owner"] == ("delta::robust::reduce_parameter_shard")
    assert report["distributed"]["native_runtime_terminal"] == "APPLIED"
    assert report["distributed"]["parallel_processes_observed"] == 4
    assert report["distributed"]["worker_processes_required"] == 4
    assert report["centralized"]["evaluation"] == report["distributed"]["evaluation"]
    assert report["delta_execution"]["python_cross_node_aggregation_performed"] is False
    assert report["delta_execution"]["terminal_outcome"] == "APPLIED"
    assert report["execution_path"]["acceptance_status"] == "PASS"
    assert report["execution_path"]["demo_owned_aggregation"] is False
    assert report["execution_path"]["existing_delta_node_interfaces"] is True
    assert report["execution_path"]["mnist_is_workload_only"] is True
    assert report["execution_path"]["centralized_baseline_isolated_from_delta_inputs"] is True
    assert (
        report["execution_path"]["distributed_orchestrator_received_node_local_numeric_arrays"]
        is False
    )
    assert report["execution_path"]["four_distinct_worker_processes_observed"] is True
    assert (result.output_dir / report["execution_path"]["diagram"]).is_file()
    assert (result.output_dir / report["execution_path"]["trace"]).is_file()
    assert report["failure_simulation"]["failed_node_id"] == "validator-04"
    assert report["failure_simulation"]["replay_observed"] is True
    assert report["failure_simulation"]["protocol_accepted_after_recovery"] is True
    assert report["failure_simulation"]["terminal_outcome"] == "APPLIED"
    assert report["failure_simulation"]["evaluation"] == report["distributed"]["evaluation"]
    assert all(node["raw_images_shared"] is False for node in report["distributed"]["nodes"])
    assert {node["shared_payload"] for node in report["distributed"]["nodes"]} == {
        "SIGNED_CANONICAL_INT16_MODEL_DELTA_ONLY"
    }
    assert report["controller_quorum"]["keys_cryptographically_valid"] is True
    assert report["controller_quorum"]["valid_for_campaign02_governance"] is False
    assert _validate_workspace_report(report) is report


def test_reproducibility_identity_excludes_observational_timings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _synthetic_dataset()
    _patch_dataset(monkeypatch, dataset)
    _patch_delta_nodes(monkeypatch, dataset)
    first = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run-a",
        allow_download=False,
    )
    second = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run-b",
        allow_download=False,
    )
    assert first.reproducibility_id == second.reproducibility_id


def test_workspace_is_one_button_and_does_not_expose_raw_json_by_default() -> None:
    assert "Запустить демо" in WORKSPACE_HTML
    assert "Покажи различия по цифрам" in WORKSPACE_HTML
    assert "Отказ и восстановление" in WORKSPACE_HTML
    assert "LOCAL DEMO ONLY" in WORKSPACE_HTML
    assert "Feature 010 GO" in WORKSPACE_HTML
    assert "<pre" not in WORKSPACE_HTML
    assert "mnist-demo-report.json" not in WORKSPACE_HTML


def test_workspace_refuses_non_loopback_binding(tmp_path: Path) -> None:
    with pytest.raises(MnistDemoError, match="MUST_BIND_LOOPBACK"):
        serve_workspace(
            _repository_root(),
            tmp_path / "cache",
            tmp_path / "runs",
            allow_download=False,
            host="0.0.0.0",
        )


def test_run_refuses_to_overwrite_prior_output(tmp_path: Path) -> None:
    destination = tmp_path / "run"
    destination.mkdir()
    with pytest.raises(MnistDemoError, match="OUTPUT_ALREADY_EXISTS"):
        run_mnist_demo(
            _repository_root(),
            tmp_path / "cache",
            destination,
            allow_download=False,
        )
