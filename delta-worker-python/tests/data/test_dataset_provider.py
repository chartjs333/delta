"""Tests for DatasetProvider contracts and the MNIST dataset provider."""

from __future__ import annotations

import gzip
import hashlib
import struct
from pathlib import Path

import numpy as np
import pytest
from deltatorrent.data import (
    MNIST_DESCRIPTOR,
    ContractCompatibilityError,
    DatasetProvider,
    DatasetProviderError,
    MnistDatasetProvider,
    MnistFile,
    check_compatibility,
)
from deltatorrent.data.mnist import NODE_LABELS, PARTITION_RULE_ID


def _synthetic_arrays() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_labels = np.repeat(np.arange(10, dtype=np.uint8), 2)
    test_labels = np.arange(10, dtype=np.uint8)

    def image(digit: int, variant: int) -> np.ndarray:
        value = np.zeros((28, 28), dtype=np.uint8)
        value[digit * 2 : digit * 2 + 2, 3:25] = 120 + variant
        value[3:25, 25 - digit * 2 : 27 - digit * 2] = 200 + variant
        return value

    train_images = np.stack(
        [image(int(digit), index % 2) for index, digit in enumerate(train_labels)]
    )
    test_images = np.stack([image(int(digit), 0) for digit in test_labels])
    return train_images, train_labels, test_images, test_labels


def _write_source(path: Path, payload: bytes) -> MnistFile:
    compressed = gzip.compress(payload)
    path.write_bytes(compressed)
    return MnistFile(
        filename=path.name,
        sha256=hashlib.sha256(compressed).hexdigest(),
        size_bytes=len(compressed),
        url=f"https://example.invalid/{path.name}",
    )


def _write_idx_sources(
    root: Path,
    train_images: np.ndarray,
    train_labels: np.ndarray,
    test_images: np.ndarray,
    test_labels: np.ndarray,
) -> tuple[MnistFile, ...]:
    train_image_payload = struct.pack(
        ">IIII", 2051, train_images.shape[0], 28, 28
    ) + np.ascontiguousarray(train_images, dtype=np.uint8).tobytes(order="C")
    train_label_payload = struct.pack(">II", 2049, train_labels.shape[0]) + np.ascontiguousarray(
        train_labels, dtype=np.uint8
    ).tobytes(order="C")
    test_image_payload = struct.pack(
        ">IIII", 2051, test_images.shape[0], 28, 28
    ) + np.ascontiguousarray(test_images, dtype=np.uint8).tobytes(order="C")
    test_label_payload = struct.pack(">II", 2049, test_labels.shape[0]) + np.ascontiguousarray(
        test_labels, dtype=np.uint8
    ).tobytes(order="C")
    return (
        _write_source(root / "train-images-idx3-ubyte.gz", train_image_payload),
        _write_source(root / "train-labels-idx1-ubyte.gz", train_label_payload),
        _write_source(root / "t10k-images-idx3-ubyte.gz", test_image_payload),
        _write_source(root / "t10k-labels-idx1-ubyte.gz", test_label_payload),
    )


def test_mnist_provider_materializes_content_pinned_cache_and_partitions(
    tmp_path: Path,
) -> None:
    train_images, train_labels, test_images, test_labels = _synthetic_arrays()
    sources = _write_idx_sources(tmp_path, train_images, train_labels, test_images, test_labels)
    provider = MnistDatasetProvider(
        source_files=sources,
        train_count=train_labels.size,
        test_count=test_labels.size,
    )

    assert isinstance(provider, DatasetProvider)
    manifest = provider.materialize(tmp_path, allow_download=False)

    assert manifest["source_id"] == provider.training_partition("ticket-000").metadata["source_id"]
    assert (tmp_path / "mnist-source-manifest.json").is_file()

    aggregate_counts = np.zeros(10, dtype=np.int64)
    partition_ids = [f"demo-mnist-worker-{index:02d}" for index in range(1, 5)]
    for partition_id, expected_digits in zip(partition_ids, NODE_LABELS, strict=True):
        partition = provider.training_partition(partition_id)
        labels = partition.targets
        assert partition.samples.shape[1:] == (28, 28)
        assert partition.samples.dtype == np.uint8
        assert labels.dtype == np.uint8
        assert {int(value) for value in np.unique(labels)} == set(expected_digits)
        assert partition.metadata["allowed_digits"] == list(expected_digits)
        assert partition.metadata["partition_rule_id"] == PARTITION_RULE_ID
        aggregate_counts += np.bincount(labels, minlength=10)

    assert np.array_equal(aggregate_counts, np.bincount(train_labels, minlength=10))

    eval_images, eval_labels = provider.evaluation_data()
    assert np.array_equal(eval_images, test_images)
    assert np.array_equal(eval_labels, test_labels)

    with pytest.raises(DatasetProviderError, match="UNKNOWN_PARTITION_ID"):
        provider.training_partition("worker-99")


def test_mnist_provider_partitioning_is_deterministic(tmp_path: Path) -> None:
    train_images, train_labels, test_images, test_labels = _synthetic_arrays()
    sources = _write_idx_sources(tmp_path, train_images, train_labels, test_images, test_labels)
    first = MnistDatasetProvider(
        source_files=sources,
        train_count=train_labels.size,
        test_count=test_labels.size,
    )
    second = MnistDatasetProvider(
        source_files=sources,
        train_count=train_labels.size,
        test_count=test_labels.size,
    )
    first.materialize(tmp_path, allow_download=False)
    second.materialize(tmp_path, allow_download=False)

    assert np.array_equal(
        first.training_partition("demo-mnist-worker-01").targets,
        second.training_partition("demo-mnist-worker-01").targets,
    )


def test_mnist_provider_fails_closed_for_missing_or_corrupt_cache(tmp_path: Path) -> None:
    provider = MnistDatasetProvider()
    with pytest.raises(DatasetProviderError, match="MNIST_SOURCE_MISSING_OFFLINE"):
        provider.materialize(tmp_path / "missing", allow_download=False)

    train_images, train_labels, test_images, test_labels = _synthetic_arrays()
    sources = _write_idx_sources(tmp_path, train_images, train_labels, test_images, test_labels)
    (tmp_path / sources[0].filename).write_bytes(b"corrupt")
    corrupt = MnistDatasetProvider(
        source_files=sources,
        train_count=train_labels.size,
        test_count=test_labels.size,
    )
    with pytest.raises(DatasetProviderError, match="MNIST_SOURCE_SIZE_MISMATCH"):
        corrupt.materialize(tmp_path, allow_download=False)


def test_mnist_provider_supports_in_memory_fixture_data(tmp_path: Path) -> None:
    train_images, train_labels, test_images, test_labels = _synthetic_arrays()
    provider = MnistDatasetProvider(
        train_images=train_images,
        train_labels=train_labels,
        test_images=test_images,
        test_labels=test_labels,
    )

    manifest = provider.materialize(tmp_path, allow_download=False)
    assert manifest["type_name"] == "DELTAREDUCE_LOCAL_DEMO_MNIST_IN_MEMORY_SOURCE"
    assert isinstance(manifest["source_id"], str)
    assert provider.training_partition("worker-01").metadata["source_id"] == manifest["source_id"]


def test_dataset_model_contract_compatibility() -> None:
    check_compatibility(
        model_sample_kind="image/grayscale-28x28",
        model_target_kind="class-id/0-9",
        dataset_descriptor=MNIST_DESCRIPTOR,
    )

    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        check_compatibility(
            model_sample_kind="text/token-ids",
            model_target_kind="class-id/0-9",
            dataset_descriptor=MNIST_DESCRIPTOR,
        )

    with pytest.raises(ContractCompatibilityError, match="TARGET_KIND_MISMATCH"):
        check_compatibility(
            model_sample_kind="image/grayscale-28x28",
            model_target_kind="class-id/0-1",
            dataset_descriptor=MNIST_DESCRIPTOR,
        )
