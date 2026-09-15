"""ModelPlugin API: Generic boundary contract separating ML models from Delta consensus.

The Delta worker and consensus runtime remain completely model-agnostic:
- Model plugins own architecture, ParameterSchema, tensor ordering, local training
  (sufficient statistics / state), applied-checkpoint decoding, and task-specific metrics.
- The generic Delta spine owns normalization validation, quantization, ShardPlan partition,
  Feature 004 DRQ1 envelope creation, Feature 008 BFT consensus, WAL durability, and receipts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np

from deltatorrent.domain.parameters import ParameterSchema


@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    """Immutable metadata descriptor for a model plugin, safe for UI/CLI exposure."""

    plugin_id: str
    display_name: str
    model_family: str
    task_type: str
    sample_kind: str
    target_kind: str
    deterministic: bool
    supports_stage_c_real_drq1: bool
    parameter_schema_id: str | None = None


@dataclass(frozen=True, slots=True)
class LocalTrainingResult:
    """Output of local worker training or sufficient statistics computation for one ticket.

    Contains model-specific canonical local state/statistics; the generic Delta worker boundary
    owns normalizing these into a consensus-visible contribution.
    """

    ticket_id: str
    tensors: Mapping[str, np.ndarray]
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Measured model performance metrics on validation or test dataset."""

    accuracy_ppm: int
    loss: float | None
    metrics: Mapping[str, object]


@runtime_checkable
class ModelPlugin(Protocol):
    """Abstract model plugin contract separating ML models from Delta consensus/Stage C."""

    @property
    def plugin_id(self) -> str:
        """Unique identifier for this model plugin (e.g. 'mnist-centroid-v1')."""
        ...

    def parameter_schema(self) -> ParameterSchema:
        """Canonical parameter schema describing trainable tensor shapes and types."""
        ...

    @property
    def tensor_order(self) -> tuple[str, ...]:
        """Deterministic ordering of tensor names in the flattened parameter vector."""
        ...

    @property
    def total_elements(self) -> int:
        """Total number of scalar elements across all tensors in tensor_order."""
        ...

    def create_model(self, state: Any | None = None) -> Any:
        """Instantiate a model instance, optionally initialized with state or checkpoint."""
        ...

    def train_ticket(
        self,
        *,
        ticket_id: str,
        data: Any,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Execute local worker computation for one ticket.

        Returns model-specific canonical local state and statistics.
        """
        ...

    def load_applied_checkpoint(
        self,
        checkpoint_values: Sequence[int] | np.ndarray,
        parent_model: Any | None = None,
    ) -> Any:
        """Reconstruct model instance from applied checkpoint integer coordinates."""
        ...

    def evaluate(self, model: Any, test_data: Any) -> EvaluationResult:
        """Measure classifier accuracy, loss, and task-specific metrics on test data."""
        ...
