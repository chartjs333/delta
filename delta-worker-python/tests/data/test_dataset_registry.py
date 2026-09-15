"""Unit tests for the static DatasetRegistry."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from deltatorrent.data import (
    DatasetDescriptor,
    DatasetProvider,
    DatasetRegistry,
    DatasetRegistryError,
    EegWindowDatasetProvider,
    MnistDatasetProvider,
    get_default_dataset_registry,
)


def _descriptor(dataset_id: str = "dummy-dataset-v1") -> DatasetDescriptor:
    return DatasetDescriptor(
        dataset_id=dataset_id,
        display_name="Dummy Dataset",
        sample_kind="vector/fp32-10",
        target_kind="scalar/fp32",
        deterministic=True,
        supports_offline_cache=True,
        description="Synthetic fixture dataset.",
    )


class DummyDatasetProvider:
    def __init__(self, descriptor: DatasetDescriptor | None = None) -> None:
        self._descriptor = descriptor or _descriptor()

    @property
    def dataset_id(self) -> str:
        return self._descriptor.dataset_id

    def descriptor(self) -> DatasetDescriptor:
        return self._descriptor

    def materialize(self, cache_dir: Path, *, allow_download: bool) -> dict[str, object]:
        return {
            "allow_download": allow_download,
            "cache_dir": str(cache_dir),
            "source_id": "sha256:" + "1" * 64,
        }

    def training_partition(self, partition_id: str) -> object:
        return {
            "partition_id": partition_id,
            "samples": np.zeros((2, 10), dtype=np.float32),
            "targets": np.zeros(2, dtype=np.float32),
        }

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        return np.zeros((1, 10), dtype=np.float32), np.zeros(1, dtype=np.float32)


def test_dataset_registry_register_and_get() -> None:
    registry = DatasetRegistry()
    descriptor = _descriptor()

    registry.register(descriptor=descriptor, factory=DummyDatasetProvider)

    assert registry.has_dataset("dummy-dataset-v1") is True
    assert registry.has_dataset("missing") is False
    assert registry.get_descriptor("dummy-dataset-v1") == descriptor

    provider = registry.get("dummy-dataset-v1")
    assert isinstance(provider, DatasetProvider)
    assert provider.dataset_id == "dummy-dataset-v1"
    assert provider.descriptor() == descriptor


def test_dataset_registry_get_returns_fresh_instances() -> None:
    registry = DatasetRegistry()
    registry.register(descriptor=_descriptor(), factory=DummyDatasetProvider)

    first = registry.get("dummy-dataset-v1")
    second = registry.get("dummy-dataset-v1")
    assert first is not second


def test_dataset_registry_rejects_duplicate_and_unknown_ids() -> None:
    registry = DatasetRegistry()
    descriptor = _descriptor()
    registry.register(descriptor=descriptor, factory=DummyDatasetProvider)

    with pytest.raises(DatasetRegistryError, match="DUPLICATE_DATASET_ID"):
        registry.register(descriptor=descriptor, factory=DummyDatasetProvider)

    with pytest.raises(DatasetRegistryError, match="UNKNOWN_DATASET_ID"):
        registry.get("missing")

    with pytest.raises(DatasetRegistryError, match="UNKNOWN_DATASET_ID"):
        registry.get_descriptor("missing")


def test_dataset_registry_rejects_descriptor_mismatches() -> None:
    registry = DatasetRegistry()

    with pytest.raises(DatasetRegistryError, match="DESCRIPTOR_DATASET_ID_MISMATCH"):
        registry.register(
            descriptor=_descriptor("wrong-id"),
            factory=DummyDatasetProvider,
        )

    descriptor = _descriptor()
    factory_descriptor = DatasetDescriptor(
        dataset_id="dummy-dataset-v1",
        display_name="Different Dataset",
        sample_kind="vector/fp32-10",
        target_kind="scalar/fp32",
        deterministic=True,
        supports_offline_cache=True,
    )
    with pytest.raises(DatasetRegistryError, match="DESCRIPTOR_FACTORY_MISMATCH"):
        registry.register(
            descriptor=descriptor,
            factory=lambda: DummyDatasetProvider(factory_descriptor),
        )


def test_dataset_registry_lists_descriptors_in_deterministic_order() -> None:
    registry = DatasetRegistry()
    for dataset_id in ("zeta-v1", "alpha-v1", "beta-v1"):
        descriptor = _descriptor(dataset_id)
        registry.register(
            descriptor=descriptor,
            factory=lambda desc=descriptor: DummyDatasetProvider(desc),
        )

    assert [item.dataset_id for item in registry.list_descriptors()] == [
        "alpha-v1",
        "beta-v1",
        "zeta-v1",
    ]


def test_dataset_descriptor_is_immutable() -> None:
    descriptor = _descriptor()

    with pytest.raises(AttributeError):
        descriptor.dataset_id = "mutated"  # type: ignore[misc]


def test_default_dataset_registry_contains_mnist_provider() -> None:
    registry = get_default_dataset_registry()
    assert registry.has_dataset("mnist-v1") is True

    descriptor = registry.get_descriptor("mnist-v1")
    assert descriptor.dataset_id == "mnist-v1"
    assert descriptor.sample_kind == "image/grayscale-28x28"
    assert descriptor.target_kind == "class-id/0-9"
    assert descriptor.deterministic is True
    assert descriptor.supports_offline_cache is True

    provider = registry.get("mnist-v1")
    assert isinstance(provider, MnistDatasetProvider)
    assert provider.dataset_id == "mnist-v1"


def test_default_dataset_registry_contains_eeg_provider() -> None:
    registry = get_default_dataset_registry()
    assert registry.has_dataset("eeg-synthetic-bci-v1") is True

    descriptor = registry.get_descriptor("eeg-synthetic-bci-v1")
    assert descriptor.dataset_id == "eeg-synthetic-bci-v1"
    assert descriptor.sample_kind == "eeg/bandpower-4ch-4band"
    assert descriptor.target_kind == "class-id/0-1"
    assert descriptor.deterministic is True
    assert descriptor.supports_offline_cache is True

    provider = registry.get("eeg-synthetic-bci-v1")
    assert isinstance(provider, EegWindowDatasetProvider)
    assert provider.dataset_id == "eeg-synthetic-bci-v1"
