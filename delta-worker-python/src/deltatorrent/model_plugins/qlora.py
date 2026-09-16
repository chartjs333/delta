"""QLoRA Quantized Adapter ModelPlugin implementation.

Adapts existing QLoRA training, adapter contribution, and checkpoint primitives
to the ModelPlugin protocol. Encapsulates parameter schema, tensor ordering,
local fixed-ticket training, applied-checkpoint decoding, and evaluation.
Generic Delta consensus, sharding policy, quantization, and worker runtimes
interact with QLoRA exclusively through the ModelPlugin protocol.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

import numpy as np
import torch
from numpy.typing import NDArray

from deltatorrent.domain.parameters import (
    FrozenOmissionPolicy,
    LogicalDType,
    ParameterSchema,
    ParameterSpec,
)
from deltatorrent.model_plugins.base import EvaluationResult, LocalTrainingResult, ModelPlugin
from deltatorrent.qlora.adapter_schema import assert_adapter_only_optimizer
from deltatorrent.qlora.backend import (
    QuantizedAdapterBackend,
    clone_adapters,
    logical_adapter_hash,
    logical_base_hash,
)
from deltatorrent.qlora.tiny_profile import (
    ADAPTER_ORDER,
    ADAPTER_SHAPES,
    ADAPTER_WIDTH,
    DEFAULT_LEARNING_RATE,
    QLORA_DATASET_ID,
    QLORA_PLUGIN_ID,
    QLORA_QUANTUM_DENOMINATOR,
    QLORA_SEGMENT_ID,
    TinyProfileError,
    backend_from_adapter_arrays,
    evaluation_batch,
    flatten_adapters,
    new_tiny_backend,
    split_adapter_values,
    validate_adapter_shapes,
)
from deltatorrent.qlora.trainer import Batch, Ticket, train_fixed_ticket

PLUGIN_ID: Final[str] = QLORA_PLUGIN_ID
SEGMENT_ID: Final[str] = QLORA_SEGMENT_ID
TOTAL_ELEMENTS: Final[int] = ADAPTER_WIDTH
DEFAULT_QUANTUM_DENOMINATOR: Final[int] = QLORA_QUANTUM_DENOMINATOR

QLORA_PARAMETER_SCHEMA: Final[ParameterSchema] = ParameterSchema(
    parameters=(
        ParameterSpec(
            name=SEGMENT_ID,
            shape=(TOTAL_ELEMENTS,),
            logical_dtype=LogicalDType.FLOAT32,
            trainable=True,
        ),
    ),
    tied_aliases={},
    frozen_omission_policy=FrozenOmissionPolicy.INCLUDE_ALL,
)
QLORA_PARAMETER_SCHEMA_ID: Final[str] = QLORA_PARAMETER_SCHEMA.fingerprint


class QloraPluginError(ValueError):
    """Stable rejection for invalid QLoRA plugin operations."""


@dataclass(frozen=True, slots=True)
class QloraAdapterModel:
    """Decoded QLoRA adapter model with validated immutable base binding."""

    backend: QuantizedAdapterBackend
    adapter_tensors: Mapping[str, NDArray[np.float64]]
    values: tuple[int, ...]
    base_model_id: str
    adapter_id: str


def _validate_adapter_mapping_shapes(adapters: Mapping[str, Any]) -> None:
    try:
        validate_adapter_shapes(adapters)
    except TinyProfileError as exc:
        raise QloraPluginError(str(exc)) from exc


class QloraModelPlugin(ModelPlugin):
    """ModelPlugin implementation for QLoRA quantized adapter fine-tuning."""

    def __init__(
        self,
        base_factory: Callable[[], QuantizedAdapterBackend] | None = None,
    ) -> None:
        self._base_factory = base_factory or new_tiny_backend
        reference_backend = self._base_factory()
        self._base_model_id = logical_base_hash(reference_backend)
        self._reference_adapter_id = logical_adapter_hash(reference_backend)

    @property
    def plugin_id(self) -> str:
        return PLUGIN_ID

    def parameter_schema(self) -> ParameterSchema:
        return QLORA_PARAMETER_SCHEMA

    @property
    def tensor_order(self) -> tuple[str, ...]:
        return (SEGMENT_ID,)

    @property
    def total_elements(self) -> int:
        return TOTAL_ELEMENTS

    @property
    def base_model_id(self) -> str:
        return self._base_model_id

    @property
    def reference_adapter_id(self) -> str:
        return self._reference_adapter_id

    def _validate_base_binding(self, backend: QuantizedAdapterBackend) -> None:
        actual_hash = logical_base_hash(backend)
        if actual_hash != self._base_model_id:
            raise QloraPluginError(
                f"IMMUTABLE_BASE_BINDING_VIOLATION: expected {self._base_model_id}, "
                f"got {actual_hash}"
            )
        try:
            assert_adapter_only_optimizer(backend, tuple(backend.adapter_tensors().values()))
        except Exception as exc:
            raise QloraPluginError(f"ADAPTER_OPTIMIZER_VIOLATION: {exc}") from exc

    def _validate_model_state(self, model: QloraAdapterModel) -> None:
        if not isinstance(model, QloraAdapterModel):
            raise QloraPluginError("INVALID_QLORA_MODEL_TYPE")
        if model.base_model_id != self._base_model_id:
            raise QloraPluginError("IMMUTABLE_BASE_BINDING_VIOLATION")
        self._validate_base_binding(model.backend)
        _validate_adapter_mapping_shapes(model.adapter_tensors)
        backend_adapters = model.backend.adapter_tensors()
        _validate_adapter_mapping_shapes(backend_adapters)
        for name in ADAPTER_ORDER:
            m_raw = model.adapter_tensors[name]
            b_raw = backend_adapters[name]
            try:
                m_arr = np.asarray(m_raw, dtype=np.float64)
            except Exception as exc:
                raise QloraPluginError(f"INVALID_ADAPTER_DTYPE: {name}") from exc
            try:
                if isinstance(b_raw, torch.Tensor):
                    b_arr = b_raw.detach().cpu().numpy().astype(np.float64)
                else:
                    b_arr = np.asarray(b_raw, dtype=np.float64)
            except Exception as exc:
                raise QloraPluginError(f"INVALID_ADAPTER_DTYPE: {name}") from exc

            if not np.all(np.isfinite(m_arr)) or not np.all(np.isfinite(b_arr)):
                raise QloraPluginError(f"NON_FINITE_ADAPTER_VALUES: {name}")

            if not np.allclose(m_arr, b_arr, atol=1e-7, rtol=1e-7):
                raise QloraPluginError(
                    f"MODEL_ADAPTER_STATE_MISMATCH: backend {name} diverges from adapter_tensors"
                )

        expected_adapter_id = logical_adapter_hash(model.backend)
        if model.adapter_id != expected_adapter_id:
            raise QloraPluginError(
                f"MODEL_ADAPTER_STATE_MISMATCH: adapter_id mismatch "
                f"(expected {expected_adapter_id}, got {model.adapter_id})"
            )

    def create_model(self, state: Any | None = None) -> QloraAdapterModel:
        if state is None:
            backend = self._base_factory()
            self._validate_base_binding(backend)
            raw_adapters = clone_adapters(backend)
            _validate_adapter_mapping_shapes(raw_adapters)
            adapter_tensors = split_adapter_values(flatten_adapters(raw_adapters))
            values = tuple(
                round(float(v) * DEFAULT_QUANTUM_DENOMINATOR)
                for v in flatten_adapters(raw_adapters)
            )
            model = QloraAdapterModel(
                backend=backend,
                adapter_tensors=adapter_tensors,
                values=values,
                base_model_id=self._base_model_id,
                adapter_id=logical_adapter_hash(backend),
            )
            self._validate_model_state(model)
            return model
        if isinstance(state, QloraAdapterModel):
            self._validate_model_state(state)
            return state
        if isinstance(state, QuantizedAdapterBackend):
            self._validate_base_binding(state)
            raw_adapters = clone_adapters(state)
            _validate_adapter_mapping_shapes(raw_adapters)
            adapter_tensors = split_adapter_values(flatten_adapters(raw_adapters))
            values = tuple(
                round(float(v) * DEFAULT_QUANTUM_DENOMINATOR)
                for v in flatten_adapters(raw_adapters)
            )
            model = QloraAdapterModel(
                backend=state,
                adapter_tensors=adapter_tensors,
                values=values,
                base_model_id=self._base_model_id,
                adapter_id=logical_adapter_hash(state),
            )
            self._validate_model_state(model)
            return model
        if isinstance(state, (tuple, list, np.ndarray)):
            return self.load_applied_checkpoint(state)
        if isinstance(state, Mapping):
            if set(state.keys()) == {SEGMENT_ID}:
                state = split_adapter_values(state[SEGMENT_ID])
            _validate_adapter_mapping_shapes(state)
            adapter_arrays = {
                name: np.ascontiguousarray(np.asarray(state[name], dtype=np.float64))
                for name in ADAPTER_ORDER
            }
            backend = backend_from_adapter_arrays(adapter_arrays)
            self._validate_base_binding(backend)
            values = tuple(
                round(float(v) * DEFAULT_QUANTUM_DENOMINATOR)
                for v in flatten_adapters(clone_adapters(backend))
            )
            model = QloraAdapterModel(
                backend=backend,
                adapter_tensors=adapter_arrays,
                values=values,
                base_model_id=self._base_model_id,
                adapter_id=logical_adapter_hash(backend),
            )
            self._validate_model_state(model)
            return model
        raise QloraPluginError("INVALID_QLORA_MODEL_STATE")

    def train_ticket(
        self,
        *,
        ticket_id: str,
        data: Any,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Execute local worker computation for one ticket.

        Reuses existing QLoRA training arithmetic via train_fixed_ticket.
        Does NOT re-implement QLoRA training arithmetic.
        """
        if not ticket_id or not isinstance(ticket_id, str):
            raise QloraPluginError("INVALID_TICKET_ID")

        # Resolve parent backend with immutable base binding verification
        backend: QuantizedAdapterBackend
        if parent_model is None:
            backend = self._base_factory()
            self._validate_base_binding(backend)
        elif isinstance(parent_model, QloraAdapterModel):
            self._validate_model_state(parent_model)
            backend = backend_from_adapter_arrays(parent_model.adapter_tensors)
        elif isinstance(parent_model, QuantizedAdapterBackend):
            self._validate_base_binding(parent_model)
            raw_adapters = clone_adapters(parent_model)
            _validate_adapter_mapping_shapes(raw_adapters)
            backend = backend_from_adapter_arrays(
                split_adapter_values(flatten_adapters(raw_adapters))
            )
        elif isinstance(parent_model, Mapping):
            _validate_adapter_mapping_shapes(parent_model)
            backend = backend_from_adapter_arrays(parent_model)
            self._validate_base_binding(backend)
        elif isinstance(parent_model, (tuple, list, np.ndarray)):
            decoded = self.load_applied_checkpoint(parent_model)
            backend = backend_from_adapter_arrays(decoded.adapter_tensors)
        else:
            raise QloraPluginError("INVALID_PARENT_MODEL")

        # Resolve batches from data
        batches: tuple[Batch, ...]
        if isinstance(data, Batch):
            batches = (data,)
        elif isinstance(data, (tuple, list)) and len(data) > 0 and isinstance(data[0], Batch):
            batches = tuple(data)
        elif isinstance(data, (tuple, list)) and len(data) == 2:
            inputs, targets = data
            inp_t = torch.as_tensor(inputs, dtype=torch.float32)
            tgt_t = torch.as_tensor(targets, dtype=torch.float32)
            if inp_t.shape[0] != tgt_t.shape[0] or inp_t.shape[0] == 0:
                raise QloraPluginError("INVALID_TRAINING_DATA_SHAPE")
            batches = (Batch(inputs=inp_t, targets=tgt_t, token_count=int(inp_t.shape[0])),)
        elif hasattr(data, "inputs") and hasattr(data, "targets"):
            inp_t = torch.as_tensor(data.inputs, dtype=torch.float32)
            tgt_t = torch.as_tensor(data.targets, dtype=torch.float32)
            token_count = getattr(data, "token_count", int(inp_t.shape[0]))
            batches = (Batch(inputs=inp_t, targets=tgt_t, token_count=token_count),)
        else:
            raise QloraPluginError("INVALID_TRAINING_DATA")

        domain_id = str(kwargs.get("domain_id", "text"))
        learning_rate = float(kwargs.get("learning_rate", DEFAULT_LEARNING_RATE))
        total_tokens = sum(b.token_count for b in batches)
        batch_budget = int(kwargs.get("batch_budget", total_tokens))
        optimizer_steps = int(kwargs.get("optimizer_steps", len(batches)))

        parent_adapter_id = logical_adapter_hash(backend)
        ticket = Ticket(
            ticket_id=ticket_id,
            domain_id=domain_id,
            batch_budget=batch_budget,
            optimizer_steps=optimizer_steps,
            parent_adapter_id=parent_adapter_id,
        )

        # Reuse existing training primitives: do NOT re-implement arithmetic
        training = train_fixed_ticket(backend, ticket, batches, learning_rate=learning_rate)
        if training.status != "COMPLETE" or not training.eligible_for_commitment:
            raise QloraPluginError(f"QLORA_WORKER_TICKET_INCOMPLETE: {training.status}")

        parent_flat = flatten_adapters(training.parent_adapters)
        final_flat = flatten_adapters(training.final_adapters or {})
        normalized_delta = (final_flat - parent_flat) / training.actual_optimizer_steps
        stage_tensor = np.ascontiguousarray(-normalized_delta.astype(np.float32), dtype=np.float32)

        metadata: dict[str, object] = {
            "actual_optimizer_steps": training.actual_optimizer_steps,
            "base_hash_after": training.base_hash_after,
            "base_hash_before": training.base_hash_before,
            "domain_id": domain_id,
            "eligible_for_commitment": training.eligible_for_commitment,
            "losses": list(training.losses),
            "parent_adapter_id": parent_adapter_id,
            "processed_tokens": training.processed_tokens,
            "status": training.status,
            "ticket_id": ticket_id,
        }
        return LocalTrainingResult(
            ticket_id=ticket_id,
            tensors={SEGMENT_ID: stage_tensor},
            metadata=metadata,
        )

    def load_applied_checkpoint(
        self,
        checkpoint_values: Sequence[int] | NDArray[Any],
        parent_model: Any | None = None,
    ) -> QloraAdapterModel:
        """Reconstruct model instance from applied checkpoint integer coordinates.

        Enforces strict fail-closed validation:
        - Exact length == 8
        - Values must be integer
        - Coordinates fit within signed 16-bit range
        - Validates immutable base binding on both parent and materialized model
        - Validates adapter shapes strictly
        - Materializes ONLY adapter state
        """
        raw = np.asarray(checkpoint_values)
        if raw.size != TOTAL_ELEMENTS or (raw.ndim > 1 and raw.shape != (TOTAL_ELEMENTS,)):
            raise QloraPluginError(
                f"CHECKPOINT_SHAPE_MISMATCH: expected {TOTAL_ELEMENTS}, got {raw.size}"
            )
        flat = raw.reshape(-1)
        if not np.issubdtype(flat.dtype, np.integer):
            raise QloraPluginError("CHECKPOINT_VALUES_NOT_INTEGER")
        if bool(np.any(flat < -32768)) or bool(np.any(flat > 32767)):
            raise QloraPluginError("CHECKPOINT_INT16_OVERFLOW")

        # Resolve parent backend and verify immutable base binding
        if parent_model is None:
            parent_backend = self._base_factory()
            self._validate_base_binding(parent_backend)
        elif isinstance(parent_model, QloraAdapterModel):
            self._validate_model_state(parent_model)
            parent_backend = parent_model.backend
        elif isinstance(parent_model, QuantizedAdapterBackend):
            self._validate_base_binding(parent_model)
            raw_adapters = clone_adapters(parent_model)
            _validate_adapter_mapping_shapes(raw_adapters)
            parent_backend = parent_model
        elif isinstance(parent_model, Mapping):
            _validate_adapter_mapping_shapes(parent_model)
            parent_backend = backend_from_adapter_arrays(parent_model)
            self._validate_base_binding(parent_backend)
        else:
            raise QloraPluginError("INVALID_PARENT_MODEL")

        # Materialize ONLY adapter state
        parent_flat = flatten_adapters(clone_adapters(parent_backend))
        delta = flat.astype(np.float64) / DEFAULT_QUANTUM_DENOMINATOR
        final_flat = parent_flat + delta
        adapter_arrays = split_adapter_values(final_flat)
        applied_backend = backend_from_adapter_arrays(adapter_arrays)

        # Strictly verify immutable base binding on newly materialized backend
        self._validate_base_binding(applied_backend)

        int_values = tuple(int(v) for v in flat)
        model = QloraAdapterModel(
            backend=applied_backend,
            adapter_tensors=adapter_arrays,
            values=int_values,
            base_model_id=self._base_model_id,
            adapter_id=logical_adapter_hash(applied_backend),
        )
        self._validate_model_state(model)
        return model

    def evaluate(self, model: Any, test_data: Any = None) -> EvaluationResult:
        """Measure adapter model prediction loss and metrics on test batch."""
        if isinstance(model, QloraAdapterModel):
            self._validate_model_state(model)
        else:
            model = self.create_model(model)

        batch: Batch
        if test_data is None:
            batch = evaluation_batch()
        elif isinstance(test_data, Batch):
            batch = test_data
        elif isinstance(test_data, (tuple, list)) and len(test_data) == 2:
            inputs, targets = test_data
            inp_t = torch.as_tensor(inputs, dtype=torch.float32)
            tgt_t = torch.as_tensor(targets, dtype=torch.float32)
            batch = Batch(inputs=inp_t, targets=tgt_t, token_count=int(inp_t.shape[0]))
        else:
            raise QloraPluginError("INVALID_TEST_DATA")

        with torch.no_grad():
            weight = model.backend.base_tensors()["model.layer0.weight"]
            adapter_a = model.backend.adapter_tensors()["model.layer0.lora_A"]
            adapter_b = model.backend.adapter_tensors()["model.layer0.lora_B"]
            prediction = batch.inputs @ weight.T + (batch.inputs @ adapter_a.T) @ adapter_b.T
            residual = prediction - batch.targets
            mse = float(torch.mean(residual**2))
            mae = float(torch.mean(torch.abs(residual)))

        accuracy_ppm = int(max(0, 1_000_000 - round(mse * 1_000_000)))
        metrics: dict[str, object] = {
            "accuracy_ppm": accuracy_ppm,
            "evaluation_dataset_id": QLORA_DATASET_ID,
            "loss_mse": round(mse, 12),
            "mean_absolute_error": round(mae, 12),
            "sample_count": int(batch.token_count),
        }
        return EvaluationResult(
            accuracy_ppm=accuracy_ppm,
            loss=round(mse, 12),
            metrics=metrics,
        )


__all__ = [
    "ADAPTER_ORDER",
    "ADAPTER_SHAPES",
    "ADAPTER_WIDTH",
    "DEFAULT_LEARNING_RATE",
    "DEFAULT_QUANTUM_DENOMINATOR",
    "PLUGIN_ID",
    "QLORA_PARAMETER_SCHEMA",
    "QLORA_PARAMETER_SCHEMA_ID",
    "SEGMENT_ID",
    "TOTAL_ELEMENTS",
    "QloraAdapterModel",
    "QloraModelPlugin",
    "QloraPluginError",
]
