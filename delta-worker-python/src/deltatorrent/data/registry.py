"""DatasetRegistry: Safe, static management of dataset provider implementations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from deltatorrent.data.base import DatasetDescriptor, DatasetProvider
from deltatorrent.data.eeg import EEG_DATASET_DESCRIPTOR, EegWindowDatasetProvider
from deltatorrent.data.mnist import MNIST_DESCRIPTOR, MnistDatasetProvider
from deltatorrent.data.qlora import QLORA_DATASET_DESCRIPTOR, TinyQloraDatasetProvider


class DatasetRegistryError(ValueError):
    """Stable error raised when a dataset registry operation fails."""


class DatasetRegistry:
    """Registry maintaining registered DatasetProvider factories and descriptors.

    Adheres to strict safety boundaries:
    - No dynamic imports or code evaluation from UI/REST calls.
    - Explicit registration with immutable descriptors.
    - No dataset downloading or loading during descriptor listing.
    - Deterministic ordering on listing.
    - get() returns fresh DatasetProvider instances.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], DatasetProvider]] = {}
        self._descriptors: dict[str, DatasetDescriptor] = {}

    def register(
        self,
        descriptor: DatasetDescriptor,
        factory: Callable[[], DatasetProvider],
    ) -> None:
        """Register a dataset provider factory with its immutable descriptor."""
        dataset_id = descriptor.dataset_id
        if not dataset_id or not isinstance(dataset_id, str):
            raise DatasetRegistryError("INVALID_DATASET_ID")
        if dataset_id in self._descriptors:
            raise DatasetRegistryError(f"DUPLICATE_DATASET_ID: {dataset_id}")
        sample = factory()
        if not isinstance(sample, DatasetProvider):
            raise DatasetRegistryError("FACTORY_NOT_DATASET_PROVIDER")
        if sample.dataset_id != dataset_id:
            raise DatasetRegistryError(
                f"DESCRIPTOR_DATASET_ID_MISMATCH: descriptor={dataset_id} "
                f"vs factory={sample.dataset_id}"
            )
        if sample.descriptor() != descriptor:
            raise DatasetRegistryError("DESCRIPTOR_FACTORY_MISMATCH")
        self._descriptors[dataset_id] = descriptor
        self._factories[dataset_id] = factory

    def get(self, dataset_id: str) -> DatasetProvider:
        """Instantiate and return a fresh DatasetProvider instance by its unique dataset_id."""
        if dataset_id not in self._factories:
            raise DatasetRegistryError(f"UNKNOWN_DATASET_ID: {dataset_id}")
        provider = self._factories[dataset_id]()
        if provider.dataset_id != dataset_id:
            raise DatasetRegistryError(
                f"DATASET_INSTANCE_ID_MISMATCH: expected {dataset_id}, got {provider.dataset_id}"
            )
        if provider.descriptor() != self._descriptors[dataset_id]:
            raise DatasetRegistryError(f"DATASET_INSTANCE_DESCRIPTOR_MISMATCH: {dataset_id}")
        return provider

    def get_descriptor(self, dataset_id: str) -> DatasetDescriptor:
        """Retrieve the immutable DatasetDescriptor for a registered dataset."""
        if dataset_id not in self._descriptors:
            raise DatasetRegistryError(f"UNKNOWN_DATASET_ID: {dataset_id}")
        return self._descriptors[dataset_id]

    def list_descriptors(self) -> tuple[DatasetDescriptor, ...]:
        """Return all registered dataset descriptors in deterministic sorted order."""
        return tuple(
            self._descriptors[dataset_id] for dataset_id in sorted(self._descriptors.keys())
        )

    def has_dataset(self, dataset_id: str) -> bool:
        """Return True if dataset_id is registered."""
        return dataset_id in self._descriptors


def build_default_dataset_registry() -> DatasetRegistry:
    """Construct a new DatasetRegistry pre-populated with baseline datasets."""
    registry = DatasetRegistry()
    registry.register(
        descriptor=MNIST_DESCRIPTOR,
        factory=MnistDatasetProvider,
    )
    registry.register(
        descriptor=EEG_DATASET_DESCRIPTOR,
        factory=EegWindowDatasetProvider,
    )
    registry.register(
        descriptor=QLORA_DATASET_DESCRIPTOR,
        factory=TinyQloraDatasetProvider,
    )
    return registry


_DEFAULT_DATASET_REGISTRY: Final[DatasetRegistry] = build_default_dataset_registry()


def get_default_dataset_registry() -> DatasetRegistry:
    """Return the shared global default DatasetRegistry instance."""
    return _DEFAULT_DATASET_REGISTRY
