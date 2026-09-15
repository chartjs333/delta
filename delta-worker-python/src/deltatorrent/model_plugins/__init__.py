"""ModelPlugin API: Boundary separating ML architectures from Delta consensus and execution."""

from __future__ import annotations

from deltatorrent.model_plugins.base import EvaluationResult, LocalTrainingResult, ModelPlugin
from deltatorrent.model_plugins.mnist_centroid import MnistCentroidModel, MnistCentroidPlugin

__all__ = [
    "EvaluationResult",
    "LocalTrainingResult",
    "MnistCentroidModel",
    "MnistCentroidPlugin",
    "ModelPlugin",
]
