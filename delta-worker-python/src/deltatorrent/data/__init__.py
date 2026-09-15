"""Data API: DatasetProvider contracts, descriptors, and static registry."""

from __future__ import annotations

from deltatorrent.data.base import (
    ContractCompatibilityError,
    DataPartition,
    DatasetDescriptor,
    DatasetProvider,
    DatasetProviderError,
    check_compatibility,
    check_contract_compatibility,
)
from deltatorrent.data.mnist import (
    MNIST_DESCRIPTOR,
    MnistDatasetProvider,
    MnistFile,
)
from deltatorrent.data.registry import (
    DatasetRegistry,
    DatasetRegistryError,
    build_default_dataset_registry,
    get_default_dataset_registry,
)

__all__ = [
    "MNIST_DESCRIPTOR",
    "ContractCompatibilityError",
    "DataPartition",
    "DatasetDescriptor",
    "DatasetProvider",
    "DatasetProviderError",
    "DatasetRegistry",
    "DatasetRegistryError",
    "MnistDatasetProvider",
    "MnistFile",
    "build_default_dataset_registry",
    "check_compatibility",
    "check_contract_compatibility",
    "get_default_dataset_registry",
]
