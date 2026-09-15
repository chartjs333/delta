"""Unit tests for ModelDatasetBinding and contract-validated runner execution."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from deltatorrent.data.base import (
    ContractCompatibilityError,
    DataPartition,
    DatasetDescriptor,
)
from deltatorrent.data.mnist import (
    DEMO_SEED,
    MnistDatasetProvider,
)
from deltatorrent.data.registry import (
    DatasetRegistry,
    DatasetRegistryError,
)
from deltatorrent.model_plugins import (
    EvaluationResult,
    LocalTrainingResult,
    MnistCentroidPlugin,
    ModelDatasetBinding,
    PluginRegistryError,
    bind_model_and_dataset,
)


def _synthetic_mnist_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate minimal synthetic MNIST arrays for test execution."""
    rng = np.random.Generator(np.random.PCG64(DEMO_SEED))
    train_images = rng.integers(0, 256, size=(40, 28, 28), dtype=np.uint8)
    train_labels = np.tile(np.arange(10, dtype=np.uint8), 4)

    test_images = rng.integers(0, 256, size=(20, 28, 28), dtype=np.uint8)
    test_labels = np.tile(np.arange(10, dtype=np.uint8), 2)
    return train_images, train_labels, test_images, test_labels


class DummyIncompatibleDatasetProvider:
    def __init__(
        self,
        sample_kind: str,
        target_kind: str,
        dataset_id: str = "incompatible-v1",
    ) -> None:
        self._sample_kind = sample_kind
        self._target_kind = target_kind
        self._dataset_id = dataset_id

    @property
    def dataset_id(self) -> str:
        return self._dataset_id

    def descriptor(self) -> DatasetDescriptor:
        return DatasetDescriptor(
            dataset_id=self._dataset_id,
            display_name="Incompatible Dataset",
            sample_kind=self._sample_kind,
            target_kind=self._target_kind,
            deterministic=True,
            supports_offline_cache=False,
        )

    def materialize(self, cache_dir: Any, *, allow_download: bool = True) -> dict[str, object]:
        return {
            "allow_download": allow_download,
            "cache_dir": str(cache_dir),
            "source_id": "sha256:" + "2" * 64,
        }

    def training_partition(self, partition_id: str) -> DataPartition:
        return DataPartition(
            partition_id=partition_id,
            samples=np.zeros(10),
            targets=np.zeros(10),
            metadata={},
        )

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        return np.zeros(10), np.zeros(10)


def test_bind_model_and_dataset_mnist_success() -> None:
    binding = bind_model_and_dataset(
        model_plugin_id="mnist-centroid-v1",
        dataset_id="mnist-v1",
    )
    assert isinstance(binding, ModelDatasetBinding)
    assert isinstance(binding.model_plugin, MnistCentroidPlugin)
    assert binding.model_descriptor.plugin_id == "mnist-centroid-v1"
    assert binding.model_descriptor.sample_kind == "image/grayscale-28x28"
    assert binding.model_descriptor.target_kind == "class-id/0-9"

    assert isinstance(binding.dataset_provider, MnistDatasetProvider)
    assert binding.dataset_descriptor.dataset_id == "mnist-v1"
    assert binding.dataset_descriptor.sample_kind == "image/grayscale-28x28"
    assert binding.dataset_descriptor.target_kind == "class-id/0-9"


def test_bind_model_and_dataset_incompatible_sample_kind_fail_closed() -> None:
    dataset_registry = DatasetRegistry()
    incompatible_provider = DummyIncompatibleDatasetProvider(
        sample_kind="text/token-sequence",
        target_kind="class-id/0-9",
        dataset_id="text-classification-v1",
    )
    dataset_registry.register(
        descriptor=incompatible_provider.descriptor(),
        factory=lambda: DummyIncompatibleDatasetProvider(
            sample_kind="text/token-sequence",
            target_kind="class-id/0-9",
            dataset_id="text-classification-v1",
        ),
    )

    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="text-classification-v1",
            dataset_registry=dataset_registry,
        )


def test_bind_model_and_dataset_incompatible_target_kind_fail_closed() -> None:
    dataset_registry = DatasetRegistry()
    incompatible_provider = DummyIncompatibleDatasetProvider(
        sample_kind="image/grayscale-28x28",
        target_kind="bounding-box/xywh",
        dataset_id="image-detection-v1",
    )
    dataset_registry.register(
        descriptor=incompatible_provider.descriptor(),
        factory=lambda: DummyIncompatibleDatasetProvider(
            sample_kind="image/grayscale-28x28",
            target_kind="bounding-box/xywh",
            dataset_id="image-detection-v1",
        ),
    )

    with pytest.raises(ContractCompatibilityError, match="TARGET_KIND_MISMATCH"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="image-detection-v1",
            dataset_registry=dataset_registry,
        )


def test_bind_model_and_dataset_checks_descriptors_before_provider_get() -> None:
    calls = 0
    dataset_registry = DatasetRegistry()
    descriptor = DummyIncompatibleDatasetProvider(
        dataset_id="text-classification-v1",
        sample_kind="text/token-sequence",
        target_kind="class-id/0-9",
    ).descriptor()

    def factory() -> DummyIncompatibleDatasetProvider:
        nonlocal calls
        calls += 1
        return DummyIncompatibleDatasetProvider(
            sample_kind="text/token-sequence",
            target_kind="class-id/0-9",
            dataset_id="text-classification-v1",
        )

    dataset_registry.register(descriptor=descriptor, factory=factory)
    assert calls == 1  # registration validation only

    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="text-classification-v1",
            dataset_registry=dataset_registry,
        )

    assert calls == 1


def test_bind_model_and_dataset_unknown_model_rejected() -> None:
    with pytest.raises(PluginRegistryError, match="UNKNOWN_PLUGIN_ID: unknown-model-v1"):
        bind_model_and_dataset(
            model_plugin_id="unknown-model-v1",
            dataset_id="mnist-v1",
        )


def test_bind_model_and_dataset_unknown_dataset_rejected() -> None:
    with pytest.raises(DatasetRegistryError, match="UNKNOWN_DATASET_ID: unknown-dataset-v1"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="unknown-dataset-v1",
        )


def test_model_dataset_binding_workflow_execution() -> None:
    train_images, train_labels, test_images, test_labels = _synthetic_mnist_data()
    provider = MnistDatasetProvider(
        train_images=train_images,
        train_labels=train_labels,
        test_images=test_images,
        test_labels=test_labels,
    )

    custom_dataset_registry = DatasetRegistry()
    custom_dataset_registry.register(
        descriptor=provider.descriptor(),
        factory=lambda: MnistDatasetProvider(
            train_images=train_images,
            train_labels=train_labels,
            test_images=test_images,
            test_labels=test_labels,
        ),
    )

    binding = bind_model_and_dataset(
        model_plugin_id="mnist-centroid-v1",
        dataset_id="mnist-v1",
        dataset_registry=custom_dataset_registry,
    )

    # 1. Train partition for worker-01 (digits 0, 1, 2)
    local_result = binding.train_ticket(
        ticket_id="ticket-001",
        partition_id="demo-mnist-worker-01",
    )
    assert isinstance(local_result, LocalTrainingResult)
    assert local_result.ticket_id == "ticket-001"
    assert "mnist.linear" in local_result.tensors
    tensor = local_result.tensors["mnist.linear"]
    assert tensor.shape == (7850,)
    assert tensor.dtype == np.float32

    # Presence flags for digits 0, 1, 2 should be active (1.0)
    presence = tensor[7840:]
    assert presence[0] == 1.0
    assert presence[1] == 1.0
    assert presence[2] == 1.0

    # 2. Evaluate applied model
    # Construct an applied checkpoint vector
    checkpoint_vector = tensor.astype(np.int64)
    evaluation = binding.evaluate_checkpoint(checkpoint_vector)
    assert isinstance(evaluation, EvaluationResult)
    assert evaluation.accuracy_ppm >= 0
    assert evaluation.metrics["total"] == 20
