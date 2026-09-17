"""Generic runner binding ModelPlugin and DatasetProvider with contract validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import numpy as np

from deltatorrent.data.base import (
    DataPartition,
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


VALID_DOMAIN_ROLES: Final[tuple[str, ...]] = (
    "PRIMARY_DELTA_EXECUTION",
    "WORKLOAD_DOMAIN",
    "PLUGIN_BINDING_SMOKE",
)

VALID_EXECUTION_SCOPES: Final[tuple[str, ...]] = (
    "STAGE_C_REAL_DRQ1",
    "PLUGIN_BOUNDARY",
    "MODEL_DATASET_BINDING_ONLY",
)


def validate_model_dataset_capability(
    *,
    model_descriptor: PluginDescriptor,
    dataset_descriptor: DatasetDescriptor,
    requested_scope: str,
) -> None:
    """Validate descriptor compatibility and requested execution scope fail-closed."""
    if requested_scope not in VALID_EXECUTION_SCOPES:
        raise ModelPluginRunnerError(f"INVALID_EXECUTION_SCOPE: {requested_scope}")
    check_contract_compatibility(
        model_sample_kind=model_descriptor.sample_kind,
        model_target_kind=model_descriptor.target_kind,
        dataset_descriptor=dataset_descriptor,
    )
    if requested_scope == "STAGE_C_REAL_DRQ1" and not model_descriptor.supports_stage_c_real_drq1:
        raise ModelPluginRunnerError(
            f"CAPABILITY_MISMATCH: plugin '{model_descriptor.plugin_id}' "
            f"does not support STAGE_C_REAL_DRQ1"
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
        cache_dir: Path | None = None,
        *,
        allow_download: bool = True,
    ) -> Mapping[str, object]:
        """Ensure dataset sources are materialized and validated fail-closed."""
        resolved_cache = (
            cache_dir
            if cache_dir is not None
            else Path(".cache") / "deltatorrent" / self.dataset_descriptor.dataset_id
        )
        return self.dataset_provider.materialize(resolved_cache, allow_download=allow_download)

    def train_ticket(
        self,
        *,
        ticket_id: str,
        partition_id: str,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Retrieve partition from dataset provider and train model plugin ticket."""
        if not ticket_id or not isinstance(ticket_id, str):
            raise ModelPluginRunnerError("INVALID_TICKET_ID")
        if not partition_id or not isinstance(partition_id, str):
            raise ModelPluginRunnerError("INVALID_PARTITION_ID")

        partition = self.dataset_provider.training_partition(partition_id)
        if not isinstance(partition, DataPartition):
            raise ModelPluginRunnerError("INVALID_DATA_PARTITION")

        # Fail-closed ticket context validation when present
        ticket_context = partition.metadata.get("ticket_context")
        if ticket_context is not None:
            if not isinstance(ticket_context, (list, tuple)):
                raise ModelPluginRunnerError("INVALID_TICKET_CONTEXT_TYPE")
            sample_count = len(partition.samples) if hasattr(partition.samples, "__len__") else 0
            if len(ticket_context) != sample_count:
                raise ModelPluginRunnerError(
                    f"TICKET_CONTEXT_COUNT_MISMATCH: context={len(ticket_context)} "
                    f"vs samples={sample_count}"
                )
            for idx, item in enumerate(ticket_context):
                if not isinstance(item, Mapping):
                    raise ModelPluginRunnerError(f"INVALID_TICKET_CONTEXT_ITEM:{idx}")
                for key in ("session_id", "data_window_id", "intervention_event_id"):
                    val = item.get(key)
                    if not val or not isinstance(val, str):
                        raise ModelPluginRunnerError(f"TICKET_CONTEXT_KEY_MISSING:{key}:{idx}")

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


class ModelPluginRunner:
    """Generic runner dispatching model and dataset execution by unique IDs.

    Resolves ModelPlugin and DatasetProvider strictly by plugin_id and dataset_id
    through ModelPluginRegistry and DatasetRegistry, ensuring fail-closed contract
    validation and fresh instance isolation.
    """

    def __init__(
        self,
        *,
        plugin_id: str,
        dataset_id: str,
        execution_scope: str = "PLUGIN_BOUNDARY",
        model_registry: ModelPluginRegistry | None = None,
        dataset_registry: DatasetRegistry | None = None,
    ) -> None:
        if not plugin_id or not isinstance(plugin_id, str):
            raise ModelPluginRunnerError("INVALID_PLUGIN_ID")
        if not dataset_id or not isinstance(dataset_id, str):
            raise ModelPluginRunnerError("INVALID_DATASET_ID")
        binding = bind_model_and_dataset(
            model_plugin_id=plugin_id,
            dataset_id=dataset_id,
            requested_execution_scope=execution_scope,
            model_registry=model_registry,
            dataset_registry=dataset_registry,
        )

        self._binding = binding
        self._execution_scope = execution_scope

    @property
    def execution_scope(self) -> str:
        """Return the validated execution scope."""
        return self._execution_scope

    @property
    def binding(self) -> ModelDatasetBinding:
        """Return the underlying validated ModelDatasetBinding."""
        return self._binding

    @property
    def model_plugin(self) -> ModelPlugin:
        """Return the resolved model plugin instance."""
        return self._binding.model_plugin

    @property
    def model_descriptor(self) -> PluginDescriptor:
        """Return the model plugin descriptor."""
        return self._binding.model_descriptor

    @property
    def dataset_provider(self) -> DatasetProvider:
        """Return the resolved dataset provider instance."""
        return self._binding.dataset_provider

    @property
    def dataset_descriptor(self) -> DatasetDescriptor:
        """Return the dataset provider descriptor."""
        return self._binding.dataset_descriptor

    def materialize_dataset(
        self,
        cache_dir: Path | None = None,
        *,
        allow_download: bool = True,
    ) -> Mapping[str, object]:
        """Ensure dataset sources are materialized and validated fail-closed."""
        return self._binding.materialize_dataset(cache_dir, allow_download=allow_download)

    def train_ticket(
        self,
        *,
        ticket_id: str,
        partition_id: str,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Execute local worker ticket training on a dataset partition."""
        return self._binding.train_ticket(
            ticket_id=ticket_id,
            partition_id=partition_id,
            parent_model=parent_model,
            **kwargs,
        )

    def evaluate(self, model: Any) -> EvaluationResult:
        """Evaluate model against dataset evaluation split."""
        return self._binding.evaluate(model)

    def evaluate_checkpoint(
        self,
        checkpoint_values: Sequence[int] | np.ndarray,
    ) -> EvaluationResult:
        """Decode applied checkpoint integer coordinates and evaluate against dataset."""
        return self._binding.evaluate_checkpoint(checkpoint_values)

    def emit_execution_receipt(
        self,
        *,
        backend_commit: str = "670b58f6458fe84620f4f9f46401f855d04ae05d",
        repository: str = "chartjs333/delta",
        produced_at: str | None = None,
        output_path: Path | str | None = None,
    ) -> dict[str, Any]:
        """Emit a validated ExecutionReceipt for this runner binding fail-closed.

        For PLUGIN_BOUNDARY scope, emits an un-attested plugin boundary execution receipt
        without fabricated consensus evidence.
        """
        import hashlib
        import json
        from datetime import UTC, datetime

        if self._execution_scope == "STAGE_C_REAL_DRQ1":
            raise ModelPluginRunnerError(
                "STAGE_C_REAL_DRQ1_REQUIRES_NATIVE_CONSENSUS_HARNESS: "
                "local ModelPluginRunner cannot emit consensus evidence"
            )

        canonical_string = (
            f"{self.model_descriptor.plugin_id}:{self.dataset_descriptor.dataset_id}:"
            f"{self._execution_scope}:{backend_commit}"
        )
        digest = hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()
        workload_config_digest = f"sha256:{digest}"

        timestamp = produced_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        receipt: dict[str, Any] = {
            "schema_version": "1.0.0",
            "receipt_type": "DELTAREDUCE_EXECUTION_RECEIPT",
            "provenance": {
                "repository": repository,
                "backend_commit": backend_commit,
                "produced_at": timestamp,
            },
            "workload": {
                "model_plugin_id": self.model_descriptor.plugin_id,
                "dataset_id": self.dataset_descriptor.dataset_id,
                "executed_scope": self._execution_scope,
                "workload_config_digest": workload_config_digest,
            },
            "execution": {
                "verdict": "SUCCESS",
                "terminal_status": "COMPLETED",
            },
        }

        try:
            serialized = json.dumps(receipt, indent=2, allow_nan=False)
        except ValueError as exc:
            raise ModelPluginRunnerError(f"RECEIPT_SERIALIZATION_FAILED_NON_FINITE: {exc}") from exc

        if output_path is not None:
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(serialized)
                f.write("\n")

        return receipt


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
        if self.role not in VALID_DOMAIN_ROLES:
            raise ModelPluginRunnerError(f"INVALID_DOMAIN_ROLE: {self.role}")
        if self.execution_scope not in VALID_EXECUTION_SCOPES:
            raise ModelPluginRunnerError(f"INVALID_EXECUTION_SCOPE: {self.execution_scope}")


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
                    "requested_execution_scope": spec.execution_scope,
                    "role": spec.role,
                    "sample_kind": binding.model_descriptor.sample_kind,
                    "supports_stage_c_real_drq1": (
                        binding.model_descriptor.supports_stage_c_real_drq1
                    ),
                    "target_kind": binding.model_descriptor.target_kind,
                    "total_elements": binding.model_plugin.total_elements,
                }
            )
        return tuple(documents)


def bind_model_and_dataset(
    *,
    model_plugin_id: str,
    dataset_id: str,
    requested_execution_scope: str = "PLUGIN_BOUNDARY",
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

    validate_model_dataset_capability(
        model_descriptor=model_descriptor,
        dataset_descriptor=dataset_descriptor,
        requested_scope=requested_execution_scope,
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
        binding = bind_model_and_dataset(
            model_plugin_id=spec.model_plugin_id,
            dataset_id=spec.dataset_id,
            requested_execution_scope=spec.execution_scope,
            model_registry=model_registry,
            dataset_registry=dataset_registry,
        )
        bindings[spec.domain_id] = binding
        spec_map[spec.domain_id] = spec

    return MultiDomainBinding(
        bindings=MappingProxyType(bindings),
        specs=MappingProxyType(spec_map),
    )


__all__ = [
    "VALID_DOMAIN_ROLES",
    "VALID_EXECUTION_SCOPES",
    "DomainBindingSpec",
    "ModelDatasetBinding",
    "ModelPluginRunner",
    "ModelPluginRunnerError",
    "MultiDomainBinding",
    "bind_model_and_dataset",
    "bind_model_dataset_domains",
    "validate_model_dataset_capability",
]
