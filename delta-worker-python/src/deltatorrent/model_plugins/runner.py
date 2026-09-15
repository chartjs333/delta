"""Generic runner binding ModelPlugin and DatasetProvider with contract validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
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
    PluginDescriptor,
)
from deltatorrent.model_plugins.registry import (
    ModelPluginRegistry,
    get_default_registry,
)


class ModelPluginRunnerError(ValueError):
    """Stable error raised by generic model/dataset runner binding operations."""


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
        result = self.model_plugin.train_ticket(
            ticket_id=ticket_id,
            data=(partition.samples, partition.targets),
            parent_model=parent_model,
            **kwargs,
        )
        metadata = dict(result.metadata)
        metadata["data_partition_id"] = partition.partition_id
        metadata["data_partition_metadata"] = dict(partition.metadata)
        return LocalTrainingResult(
            ticket_id=result.ticket_id,
            tensors=result.tensors,
            metadata=metadata,
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


@dataclass(frozen=True, slots=True)
class DomainBindingSpec:
    """One named domain in a multi-domain model/dataset run."""

    domain_id: str
    model_plugin_id: str
    dataset_id: str
    role: str = "WORKLOAD_DOMAIN"
    execution_scope: str = "PLUGIN_BOUNDARY"

    def __post_init__(self) -> None:
        if not self.domain_id:
            raise ModelPluginRunnerError("DOMAIN_ID_EMPTY")
        if not self.model_plugin_id:
            raise ModelPluginRunnerError("DOMAIN_MODEL_PLUGIN_ID_EMPTY")
        if not self.dataset_id:
            raise ModelPluginRunnerError("DOMAIN_DATASET_ID_EMPTY")
        if not self.role:
            raise ModelPluginRunnerError("DOMAIN_ROLE_EMPTY")
        if not self.execution_scope:
            raise ModelPluginRunnerError("DOMAIN_EXECUTION_SCOPE_EMPTY")


@dataclass(frozen=True, slots=True)
class MultiDomainBinding:
    """Validated fail-closed structure for multiple independent workload domains."""

    bindings: Mapping[str, ModelDatasetBinding]
    specs: Mapping[str, DomainBindingSpec]

    @property
    def domain_ids(self) -> tuple[str, ...]:
        """Return domain IDs in the deterministic order supplied by the caller."""
        return tuple(self.bindings)

    def get(self, domain_id: str) -> ModelDatasetBinding:
        """Return the validated binding for a domain or fail closed."""
        try:
            return self.bindings[domain_id]
        except KeyError as exc:
            raise ModelPluginRunnerError(f"UNKNOWN_DOMAIN_ID: {domain_id}") from exc

    def describe(self) -> tuple[dict[str, object], ...]:
        """Return UI/report-safe descriptors without exposing mutable registry state."""
        documents: list[dict[str, object]] = []
        for domain_id in self.domain_ids:
            binding = self.bindings[domain_id]
            spec = self.specs[domain_id]
            documents.append(
                {
                    "contract_compatibility": "PASS",
                    "dataset_id": binding.dataset_descriptor.dataset_id,
                    "dataset_name": binding.dataset_descriptor.display_name,
                    "domain_id": domain_id,
                    "execution_scope": spec.execution_scope,
                    "model_name": binding.model_descriptor.display_name,
                    "model_plugin_id": binding.model_descriptor.plugin_id,
                    "role": spec.role,
                    "sample_kind": binding.model_descriptor.sample_kind,
                    "target_kind": binding.model_descriptor.target_kind,
                    "total_elements": binding.model_plugin.total_elements,
                }
            )
        return tuple(documents)


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


def bind_model_dataset_domains(
    specs: Sequence[DomainBindingSpec],
    *,
    model_registry: ModelPluginRegistry | None = None,
    dataset_registry: DatasetRegistry | None = None,
) -> MultiDomainBinding:
    """Resolve multiple model/dataset domain bindings with fail-closed uniqueness checks."""
    if not specs:
        raise ModelPluginRunnerError("DOMAIN_BINDING_SET_EMPTY")

    bindings: dict[str, ModelDatasetBinding] = {}
    spec_map: dict[str, DomainBindingSpec] = {}
    for spec in specs:
        if spec.domain_id in bindings:
            raise ModelPluginRunnerError(f"DUPLICATE_DOMAIN_ID: {spec.domain_id}")
        bindings[spec.domain_id] = bind_model_and_dataset(
            model_plugin_id=spec.model_plugin_id,
            dataset_id=spec.dataset_id,
            model_registry=model_registry,
            dataset_registry=dataset_registry,
        )
        spec_map[spec.domain_id] = spec

    return MultiDomainBinding(
        bindings=MappingProxyType(bindings),
        specs=MappingProxyType(spec_map),
    )
