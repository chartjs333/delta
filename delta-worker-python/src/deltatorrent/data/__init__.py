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
from deltatorrent.data.binding import (
    BINDING_ASSERTION_SCHEMA_VERSION,
    BINDING_ASSERTION_TYPE,
    BindingAssertion,
    BindingAssertionError,
)
from deltatorrent.data.eeg import (
    DEFAULT_EEG_ACQUISITION_PROFILE_ID,
    DEFAULT_EEG_PROFILE,
    EEG_DATASET_DESCRIPTOR,
    DataWindow,
    EegDataError,
    EegPreprocessingProfile,
    EegWindow,
    EegWindowDatasetProvider,
    InterventionEvent,
    ObservationSession,
    PhysiologicalWindow,
    ResponseAnalysisInput,
    eeg_raw_data_hash,
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
    "BINDING_ASSERTION_SCHEMA_VERSION",
    "BINDING_ASSERTION_TYPE",
    "DEFAULT_EEG_ACQUISITION_PROFILE_ID",
    "DEFAULT_EEG_PROFILE",
    "EEG_DATASET_DESCRIPTOR",
    "MNIST_DESCRIPTOR",
    "BindingAssertion",
    "BindingAssertionError",
    "ContractCompatibilityError",
    "DataPartition",
    "DataWindow",
    "DatasetDescriptor",
    "DatasetProvider",
    "DatasetProviderError",
    "DatasetRegistry",
    "DatasetRegistryError",
    "EegDataError",
    "EegPreprocessingProfile",
    "EegWindow",
    "EegWindowDatasetProvider",
    "InterventionEvent",
    "MnistDatasetProvider",
    "MnistFile",
    "ObservationSession",
    "PhysiologicalWindow",
    "ResponseAnalysisInput",
    "build_default_dataset_registry",
    "check_compatibility",
    "check_contract_compatibility",
    "eeg_raw_data_hash",
    "get_default_dataset_registry",
]
