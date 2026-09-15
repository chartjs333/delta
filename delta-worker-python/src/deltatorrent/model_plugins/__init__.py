"""ModelPlugin API: Boundary separating ML architectures from Delta consensus and execution."""

from __future__ import annotations

from deltatorrent.model_plugins.base import EvaluationResult, LocalTrainingResult, ModelPlugin
from deltatorrent.model_plugins.mnist_centroid import MnistCentroidModel, MnistCentroidPlugin
from deltatorrent.model_plugins.registry import (
    MNIST_CENTROID_DESCRIPTOR,
    ModelPluginRegistry,
    PluginDescriptor,
    PluginRegistryError,
    build_default_registry,
    get_default_registry,
)

__all__ = [
    "MNIST_CENTROID_DESCRIPTOR",
    "EvaluationResult",
    "LocalTrainingResult",
    "MnistCentroidModel",
    "MnistCentroidPlugin",
    "ModelPlugin",
    "ModelPluginRegistry",
    "PluginDescriptor",
    "PluginRegistryError",
    "build_default_registry",
    "get_default_registry",
]
