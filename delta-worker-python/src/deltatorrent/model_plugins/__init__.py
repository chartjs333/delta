"""ModelPlugin API: Boundary separating ML architectures from Delta consensus and execution."""

from __future__ import annotations

from deltatorrent.model_plugins.base import (
    EvaluationResult,
    LocalTrainingResult,
    ModelPlugin,
    PluginDescriptor,
)
from deltatorrent.model_plugins.eeg_bandpower import (
    EegBandpowerCentroidPlugin,
    EegBandpowerModel,
    EegPluginError,
)
from deltatorrent.model_plugins.mnist_centroid import MnistCentroidModel, MnistCentroidPlugin
from deltatorrent.model_plugins.registry import (
    EEG_BANDPOWER_DESCRIPTOR,
    MNIST_CENTROID_DESCRIPTOR,
    ModelPluginRegistry,
    PluginRegistryError,
    build_default_registry,
    get_default_registry,
)
from deltatorrent.model_plugins.runner import (
    DomainBindingSpec,
    ModelDatasetBinding,
    ModelPluginRunnerError,
    MultiDomainBinding,
    bind_model_and_dataset,
    bind_model_dataset_domains,
)

__all__ = [
    "EEG_BANDPOWER_DESCRIPTOR",
    "MNIST_CENTROID_DESCRIPTOR",
    "DomainBindingSpec",
    "EegBandpowerCentroidPlugin",
    "EegBandpowerModel",
    "EegPluginError",
    "EvaluationResult",
    "LocalTrainingResult",
    "MnistCentroidModel",
    "MnistCentroidPlugin",
    "ModelDatasetBinding",
    "ModelPlugin",
    "ModelPluginRegistry",
    "ModelPluginRunnerError",
    "MultiDomainBinding",
    "PluginDescriptor",
    "PluginRegistryError",
    "bind_model_and_dataset",
    "bind_model_dataset_domains",
    "build_default_registry",
    "get_default_registry",
]
