from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from deltatorrent.benchmark import mnist_demo
from deltatorrent.benchmark.mnist_demo import (
    MNIST_FILES,
    MnistDataset,
    MnistDemoError,
    aggregate_summaries,
    compute_summary,
    evaluate_centroid_model,
    materialize_node_shards,
    prepare_mnist_cache,
    run_mnist_demo,
    run_node_summaries,
)
from deltatorrent.benchmark.mnist_demo_workspace import WORKSPACE_HTML, serve_workspace


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
        allowed = set(manifest["allowed_digits"])
        counts = manifest["label_counts"]
        assert all(count == 0 for digit, count in enumerate(counts) if digit not in allowed)


def test_distributed_integer_model_exactly_matches_centralized(tmp_path: Path) -> None:
    dataset = _synthetic_dataset()
    node_root = tmp_path / "nodes"
    materialize_node_shards(dataset.train_images, dataset.train_labels, node_root)
    node_dirs = tuple(node_root / f"demo-mnist-worker-{index:02d}" for index in range(1, 5))

    central_sums, central_counts = compute_summary(dataset.train_images, dataset.train_labels)
    summaries = run_node_summaries(node_dirs, parallel=False)
    distributed_sums, distributed_counts = aggregate_summaries(summaries)

    assert np.array_equal(distributed_sums, central_sums)
    assert np.array_equal(distributed_counts, central_counts)
    central = evaluate_centroid_model(
        central_sums,
        central_counts,
        dataset.test_images,
        dataset.test_labels,
    )
    distributed = evaluate_centroid_model(
        distributed_sums,
        distributed_counts,
        dataset.test_images,
        dataset.test_labels,
    )
    assert central.accuracy_ppm == 1_000_000
    assert np.array_equal(central.predictions, distributed.predictions)


def test_run_records_failure_difference_without_protocol_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _synthetic_dataset()
    _patch_dataset(monkeypatch, dataset)

    result = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run",
        allow_download=False,
        parallel=False,
    )
    report = json.loads(result.report_json.read_text(encoding="utf-8"))

    assert report["demo_status"] == "DEMO_PASS"
    assert report["authoritative"] is False
    assert report["governance_eligible"] is False
    assert report["execution_authorized"] is False
    assert report["feature_010_go_claimed"] is False
    assert report["dataset"]["name"] == "MNIST"
    assert report["distributed"]["exact_model_match_with_centralized"] is True
    assert report["centralized"]["evaluation"] == report["distributed"]["evaluation"]
    assert report["failure_simulation"]["failed_node_id"] == "demo-mnist-worker-04"
    assert report["failure_simulation"]["missing_digits"] == [8, 9]
    assert report["failure_simulation"]["coverage_complete"] is False
    assert report["failure_simulation"]["protocol_accepted"] is False
    assert report["failure_simulation"]["evaluation"]["accuracy_ppm"] == 800_000
    assert all(node["raw_images_shared"] is False for node in report["distributed"]["nodes"])
    assert {node["shared_payload"] for node in report["distributed"]["nodes"]} == {
        "INTEGER_CLASS_SUMS_AND_COUNTS_ONLY"
    }
    assert report["controller_quorum"]["keys_cryptographically_valid"] is True
    assert report["controller_quorum"]["valid_for_campaign02_governance"] is False


def test_reproducibility_identity_excludes_observational_timings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _synthetic_dataset()
    _patch_dataset(monkeypatch, dataset)
    first = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run-a",
        allow_download=False,
        parallel=False,
    )
    second = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run-b",
        allow_download=False,
        parallel=False,
    )
    assert first.reproducibility_id == second.reproducibility_id


def test_workspace_is_one_button_and_does_not_expose_raw_json_by_default() -> None:
    assert "Запустить демо" in WORKSPACE_HTML
    assert "Покажи различия по цифрам" in WORKSPACE_HTML
    assert "Отключить worker-04" in WORKSPACE_HTML
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
            parallel=False,
        )
