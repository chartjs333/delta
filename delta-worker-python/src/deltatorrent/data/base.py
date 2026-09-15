"""DatasetProvider API: Contracts for dataset management and partitioning.

Separates dataset sourcing, caching, and ticket-bound partitioning from model architectures.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np


class DatasetProviderError(ValueError):
    """Base error for dataset provider operations."""


class ContractCompatibilityError(DatasetProviderError):
    """Raised when model and dataset sample or target contracts are incompatible."""


@dataclass(frozen=True, slots=True)
class DatasetDescriptor:
    """Immutable metadata descriptor for a dataset provider, safe for UI/CLI exposure.

    Defines the contract tags (sample_kind, target_kind) and operational capabilities
    without executing data loading or download operations.
    """

    dataset_id: str
    display_name: str
    sample_kind: str
    target_kind: str
    deterministic: bool
    supports_offline_cache: bool
    description: str = ""
    version: str = "1.0.0"


@dataclass(frozen=True, slots=True)
class DataPartition:
    """A bounded data shard allocated to an individual ticket or worker."""

    partition_id: str
    samples: np.ndarray
    targets: np.ndarray
    metadata: Mapping[str, object]


@runtime_checkable
class DatasetProvider(Protocol):
    """Abstract dataset provider contract separating data management from model logic."""

    @property
    def dataset_id(self) -> str:
        """Unique identifier for this dataset provider (e.g. 'mnist-v1')."""
        ...

    def descriptor(self) -> DatasetDescriptor:
        """Return the immutable metadata descriptor for this dataset."""
        ...

    def materialize(self, cache_dir: Path, *, allow_download: bool) -> Mapping[str, object]:
        """Validate local cache or download raw sources fail-closed."""
        ...

    def training_partition(self, partition_id: str) -> DataPartition:
        """Return the training data partition assigned to the specified ticket or worker."""
        ...

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Return the evaluation dataset as a (samples, targets) tuple."""
        ...


def check_compatibility(
    *,
    model_sample_kind: str,
    model_target_kind: str,
    dataset_descriptor: DatasetDescriptor,
) -> None:
    """Validate that a model plugin and dataset provider share compatible contract tags.

    Fails closed if the sample kinds or target kinds do not match exactly.
    """
    if model_sample_kind != dataset_descriptor.sample_kind:
        raise ContractCompatibilityError(
            f"SAMPLE_KIND_MISMATCH: model requires '{model_sample_kind}', "
            f"dataset provides '{dataset_descriptor.sample_kind}'"
        )
    if model_target_kind != dataset_descriptor.target_kind:
        raise ContractCompatibilityError(
            f"TARGET_KIND_MISMATCH: model requires '{model_target_kind}', "
            f"dataset provides '{dataset_descriptor.target_kind}'"
        )


def check_contract_compatibility(
    *,
    model_sample_kind: str,
    model_target_kind: str,
    dataset_descriptor: DatasetDescriptor,
) -> None:
    """Backward-compatible alias for check_compatibility."""
    check_compatibility(
        model_sample_kind=model_sample_kind,
        model_target_kind=model_target_kind,
        dataset_descriptor=dataset_descriptor,
    )
