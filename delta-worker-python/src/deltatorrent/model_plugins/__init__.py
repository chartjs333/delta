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
from deltatorrent.model_plugins.qlora import (
    QloraAdapterModel,
    QloraModelPlugin,
    QloraPluginError,
)
from deltatorrent.model_plugins.registry import (
    EEG_BANDPOWER_DESCRIPTOR,
    MNIST_CENTROID_DESCRIPTOR,
    QLORA_DESCRIPTOR,
    ModelPluginRegistry,
    PluginRegistryError,
    build_default_registry,
    get_default_registry,
)
from deltatorrent.model_plugins.runner import (
    VALID_DOMAIN_ROLES,
    VALID_EXECUTION_SCOPES,
    DomainBindingSpec,
    ModelDatasetBinding,
    ModelPluginRunner,
    ModelPluginRunnerError,
    MultiDomainBinding,
    bind_model_and_dataset,
    bind_model_dataset_domains,
)

__all__ = [
    "EEG_BANDPOWER_DESCRIPTOR",
    "MNIST_CENTROID_DESCRIPTOR",
    "QLORA_DESCRIPTOR",
    "VALID_DOMAIN_ROLES",
    "VALID_EXECUTION_SCOPES",
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
    "ModelPluginRunner",
    "ModelPluginRunnerError",
    "MultiDomainBinding",
    "PluginDescriptor",
    "PluginRegistryError",
    "QloraAdapterModel",
    "QloraModelPlugin",
    "QloraPluginError",
    "bind_model_and_dataset",
    "bind_model_dataset_domains",
    "build_default_registry",
    "get_default_registry",
]
