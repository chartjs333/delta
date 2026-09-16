"""Canonical deterministic offline reference profile and primitives for tiny QLoRA."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

import numpy as np
import torch

from deltatorrent.qlora.backend import (
    QuantizedAdapterBackend,
    TinyOfflineBackend,
    logical_adapter_hash,
)
from deltatorrent.qlora.trainer import Batch

ADAPTER_ORDER: Final[tuple[str, ...]] = ("model.layer0.lora_A", "model.layer0.lora_B")
ADAPTER_SHAPES: Final[tuple[tuple[int, ...], ...]] = ((2, 2), (2, 2))
ADAPTER_WIDTH: Final[int] = 8
QLORA_PLUGIN_ID: Final[str] = "qlora-tiny-adapter-v1"
QLORA_SEGMENT_ID: Final[str] = "qlora.adapter.flat"
QLORA_DATASET_ID: Final[str] = "tiny-qlora-regression-v1"
QLORA_QUANTUM_DENOMINATOR: Final[int] = 10_000
DEFAULT_LEARNING_RATE: Final[float] = 0.05


class TinyProfileError(ValueError):
    """Stable rejection for tiny QLoRA reference profile operations."""


def torch_tensor(value: Sequence[Sequence[float]]) -> torch.Tensor:
    return torch.tensor(value, dtype=torch.float32)


def new_tiny_backend() -> TinyOfflineBackend:
    base = {
        "model.embed.weight": torch_tensor([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]),
        "model.layer0.weight": torch_tensor([[1.0, -1.0], [1.0, 1.0]]),
        "model.output.weight": torch_tensor([[1.0, 0.0], [0.0, 1.0]]),
    }
    buffers = {"model.layer0.scale": torch.tensor([1.0], dtype=torch.float32)}
    adapters = {
        "model.layer0.lora_A": torch.nn.Parameter(torch_tensor([[0.1, -0.1], [0.05, 0.0]])),
        "model.layer0.lora_B": torch.nn.Parameter(torch_tensor([[0.0, 0.0], [0.0, 0.0]])),
    }
    return TinyOfflineBackend(base, buffers, adapters)


def worker_batches() -> tuple[Batch, ...]:
    return (
        Batch(torch_tensor([[1.0, 0.0], [0.0, 1.0]]), torch_tensor([[0.0, 0.0], [0.0, 0.0]]), 2),
        Batch(torch_tensor([[1.0, 1.0], [0.5, -0.5]]), torch_tensor([[1.0, 1.0], [1.0, 1.0]]), 2),
        Batch(
            torch_tensor([[2.0, 0.0], [0.0, 2.0]]),
            torch_tensor([[1.0, -1.0], [-1.0, 1.0]]),
            2,
        ),
        Batch(
            torch_tensor([[-1.0, 0.5], [0.25, 1.0]]),
            torch_tensor([[0.5, 0.0], [0.0, 0.5]]),
            2,
        ),
    )


def evaluation_batch() -> Batch:
    return Batch(
        torch_tensor(
            [
                [1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0],
                [-1.0, 0.5],
                [0.25, 1.0],
            ]
        ),
        torch_tensor(
            [
                [0.0, 0.0],
                [0.0, 0.0],
                [1.0, 1.0],
                [0.5, 0.0],
                [0.0, 0.5],
            ]
        ),
        5,
    )


def validate_adapter_shapes(adapters: Mapping[str, Any]) -> None:
    """Validate that adapter mapping has exact tensor names and matching shapes."""
    if set(adapters) != set(ADAPTER_ORDER):
        raise TinyProfileError("ADAPTER_PARAMETER_SET_MISMATCH")
    for name, expected_shape in zip(ADAPTER_ORDER, ADAPTER_SHAPES, strict=True):
        val = adapters[name]
        shape = tuple(val.shape) if hasattr(val, "shape") else ()
        if shape != expected_shape:
            raise TinyProfileError(
                f"ADAPTER_SHAPE_MISMATCH: {name} expected shape {expected_shape}, got {shape}"
            )


def flatten_adapters(adapters: Mapping[str, torch.Tensor | np.ndarray]) -> np.ndarray:
    validate_adapter_shapes(adapters)
    parts: list[np.ndarray] = []
    for name in ADAPTER_ORDER:
        val = adapters[name]
        if isinstance(val, torch.Tensor):
            arr = val.detach().cpu().numpy().astype(np.float64).reshape(-1)
        else:
            arr = np.asarray(val, dtype=np.float64).reshape(-1)
        parts.append(arr)
    flat = np.concatenate(parts) if parts else np.empty(0, dtype=np.float64)
    if flat.shape != (ADAPTER_WIDTH,):
        raise TinyProfileError("ADAPTER_WIDTH_INVALID")
    return np.ascontiguousarray(flat, dtype=np.float64)


def split_adapter_values(values: object) -> dict[str, np.ndarray]:
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    if flat.shape != (ADAPTER_WIDTH,):
        raise TinyProfileError("ADAPTER_WIDTH_INVALID")
    result: dict[str, np.ndarray] = {}
    cursor = 0
    for name, shape in zip(ADAPTER_ORDER, ADAPTER_SHAPES, strict=True):
        count = int(np.prod(shape))
        result[name] = np.ascontiguousarray(flat[cursor : cursor + count].reshape(shape))
        cursor += count
    return result


def backend_from_adapter_arrays(adapters: Mapping[str, np.ndarray]) -> TinyOfflineBackend:
    validate_adapter_shapes(adapters)
    backend = new_tiny_backend()
    for name in ADAPTER_ORDER:
        backend._adapters[name] = torch.nn.Parameter(
            torch.tensor(adapters[name], dtype=torch.float32)
        )
    return backend


def evaluate_backend(
    backend: QuantizedAdapterBackend, batch: Batch | None = None
) -> dict[str, object]:
    eval_batch = batch if batch is not None else evaluation_batch()
    with torch.no_grad():
        weight = backend.base_tensors()["model.layer0.weight"]
        adapter_a = backend.adapter_tensors()["model.layer0.lora_A"]
        adapter_b = backend.adapter_tensors()["model.layer0.lora_B"]
        prediction = eval_batch.inputs @ weight.T + (eval_batch.inputs @ adapter_a.T) @ adapter_b.T
        residual = prediction - eval_batch.targets
        mse = torch.mean(residual**2)
        mae = torch.mean(torch.abs(residual))
    return {
        "evaluation_dataset_id": QLORA_DATASET_ID,
        "loss_mse": round(float(mse), 12),
        "mean_absolute_error": round(float(mae), 12),
        "sample_count": int(eval_batch.token_count),
    }


def adapter_id_from_arrays(adapters: Mapping[str, np.ndarray]) -> str:
    return logical_adapter_hash(backend_from_adapter_arrays(adapters))


__all__ = [
    "ADAPTER_ORDER",
    "ADAPTER_SHAPES",
    "ADAPTER_WIDTH",
    "DEFAULT_LEARNING_RATE",
    "QLORA_DATASET_ID",
    "QLORA_PLUGIN_ID",
    "QLORA_QUANTUM_DENOMINATOR",
    "QLORA_SEGMENT_ID",
    "TinyProfileError",
    "adapter_id_from_arrays",
    "backend_from_adapter_arrays",
    "evaluate_backend",
    "evaluation_batch",
    "flatten_adapters",
    "new_tiny_backend",
    "split_adapter_values",
    "torch_tensor",
    "validate_adapter_shapes",
    "worker_batches",
]
