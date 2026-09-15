"""Generic runner binding ModelPlugin and DatasetProvider with contract validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from deltatorrent.data.base import (
    DatasetDescriptor,
    DatasetProvider,
    check_contract_compatibility,
)
from deltatorrent.data.registry import (
    DatasetRegistry,
    get_default_dataset_registry,
)
from deltatorrent.model_plugins.base import (
    EvaluationResult,
    LocalTrainingResult,
    ModelPlugin,
)
from deltatorrent.model_plugins.registry import (
    ModelPluginRegistry,
    PluginDescriptor,
    get_default_registry,
)


@dataclass(frozen=True, slots=True)
class ModelDatasetBinding:
    """Validated, fail-closed binding between a model plugin and dataset provider."""

    model_plugin: ModelPlugin
    model_descriptor: PluginDescriptor
    dataset_provider: DatasetProvider
    dataset_descriptor: DatasetDescriptor

    def materialize_dataset(
        self,
        cache_dir: Path,
        *,
        allow_download: bool = True,
    ) -> Mapping[str, object]:
        """Ensure dataset sources are materialized and validated fail-closed."""
        return self.dataset_provider.materialize(cache_dir, allow_download=allow_download)

    def train_ticket(
        self,
        *,
        ticket_id: str,
        partition_id: str,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Retrieve partition from dataset provider and train model plugin ticket."""
        partition = self.dataset_provider.training_partition(partition_id)
        return self.model_plugin.train_ticket(
            ticket_id=ticket_id,
            data=(partition.samples, partition.targets),
            parent_model=parent_model,
            **kwargs,
        )

    def evaluate(self, model: Any) -> EvaluationResult:
        """Evaluate model against dataset provider's test set."""
        eval_samples, eval_targets = self.dataset_provider.evaluation_data()
        return self.model_plugin.evaluate(model, (eval_samples, eval_targets))

    def evaluate_checkpoint(
        self,
        checkpoint_values: Sequence[int] | np.ndarray,
    ) -> EvaluationResult:
        """Decode applied checkpoint coordinates via plugin and evaluate against dataset."""
        model = self.model_plugin.load_applied_checkpoint(checkpoint_values)
        return self.evaluate(model)


def bind_model_and_dataset(
    *,
    model_plugin_id: str,
    dataset_id: str,
    model_registry: ModelPluginRegistry | None = None,
    dataset_registry: DatasetRegistry | None = None,
) -> ModelDatasetBinding:
    """Resolve and validate a model plugin and dataset provider fail-closed.

    1. Resolves model plugin and descriptor from model registry.
    2. Resolves dataset provider and descriptor from dataset registry.
    3. Strictly validates sample_kind and target_kind contract compatibility.
    4. Returns an immutable ModelDatasetBinding.
    """
    models = model_registry if model_registry is not None else get_default_registry()
    datasets = dataset_registry if dataset_registry is not None else get_default_dataset_registry()

    model_descriptor = models.get_descriptor(model_plugin_id)
    dataset_descriptor = datasets.get_descriptor(dataset_id)

    check_contract_compatibility(
        model_sample_kind=model_descriptor.sample_kind,
        model_target_kind=model_descriptor.target_kind,
        dataset_descriptor=dataset_descriptor,
    )

    model_plugin = models.get(model_plugin_id)
    dataset_provider = datasets.get(dataset_id)

    return ModelDatasetBinding(
        model_plugin=model_plugin,
        model_descriptor=model_descriptor,
        dataset_provider=dataset_provider,
        dataset_descriptor=dataset_descriptor,
    )
