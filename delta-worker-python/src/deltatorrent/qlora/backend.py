"""Backend-neutral QLoRA port and deterministic offline reference backend."""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import torch


class BackendError(RuntimeError):
    """Stable backend rejection."""


def _logical_tensor_hash(tensors: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256(b"deltareduce.009.logical-tensors.v1\x00")
    for name, tensor in sorted(tensors.items()):
        value = tensor.detach().cpu().contiguous()
        name_bytes = name.encode("utf-8")
        dtype_bytes = str(value.dtype).encode("ascii")
        digest.update(struct.pack("<I", len(name_bytes)))
        digest.update(name_bytes)
        digest.update(struct.pack("<I", len(dtype_bytes)))
        digest.update(dtype_bytes)
        digest.update(struct.pack("<I", value.ndim))
        for dimension in value.shape:
            digest.update(struct.pack("<Q", dimension))
        raw = value.view(torch.uint8).numpy().tobytes()
        digest.update(struct.pack("<Q", len(raw)))
        digest.update(raw)
    return f"sha256:{digest.hexdigest()}"


@runtime_checkable
class QuantizedAdapterBackend(Protocol):
    @property
    def backend_name(self) -> str: ...

    @property
    def backend_version(self) -> str: ...

    def base_tensors(self) -> Mapping[str, torch.Tensor]: ...

    def protocol_buffers(self) -> Mapping[str, torch.Tensor]: ...

    def adapter_tensors(self) -> Mapping[str, torch.nn.Parameter]: ...

    def target_modules(self) -> tuple[str, ...]: ...

    def approved_ephemeral_caches(self) -> tuple[str, ...]: ...

    def train_step(
        self, inputs: torch.Tensor, targets: torch.Tensor, learning_rate: float
    ) -> float: ...


def logical_base_hash(backend: QuantizedAdapterBackend) -> str:
    values = dict(backend.base_tensors())
    values.update(backend.protocol_buffers())
    return _logical_tensor_hash(values)


def logical_adapter_hash(backend: QuantizedAdapterBackend) -> str:
    return _logical_tensor_hash(backend.adapter_tensors())


def clone_adapters(backend: QuantizedAdapterBackend) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu().clone()
        for name, tensor in sorted(backend.adapter_tensors().items())
    }


def validate_backend_contract(
    backend: QuantizedAdapterBackend,
    *,
    expected_name: str,
    expected_version: str,
    approved_ephemeral_caches: tuple[str, ...],
) -> None:
    if backend.backend_name != expected_name:
        raise BackendError("BACKEND_NAME_MISMATCH")
    if backend.backend_version != expected_version:
        raise BackendError("BACKEND_VERSION_MISMATCH")
    if backend.approved_ephemeral_caches() != approved_ephemeral_caches:
        raise BackendError("EPHEMERAL_CACHE_POLICY_MISMATCH")


@dataclass(slots=True)
class TinyOfflineBackend:
    """Small CPU backend with real autograd and no production-memory claim."""

    _base: dict[str, torch.Tensor]
    _buffers: dict[str, torch.Tensor]
    _adapters: dict[str, torch.nn.Parameter]
    fail_on_step: int | None = None
    _step: int = 0

    @property
    def backend_name(self) -> str:
        return "MOCK_INT4"

    @property
    def backend_version(self) -> str:
        return "fixture-1"

    def base_tensors(self) -> Mapping[str, torch.Tensor]:
        return self._base

    def protocol_buffers(self) -> Mapping[str, torch.Tensor]:
        return self._buffers

    def adapter_tensors(self) -> Mapping[str, torch.nn.Parameter]:
        return self._adapters

    def target_modules(self) -> tuple[str, ...]:
        return ("model.layer0",)

    def approved_ephemeral_caches(self) -> tuple[str, ...]:
        return ()

    def train_step(
        self, inputs: torch.Tensor, targets: torch.Tensor, learning_rate: float
    ) -> float:
        if self.fail_on_step == self._step:
            raise RuntimeError("CUDA out of memory")
        weight = self._base["model.layer0.weight"]
        adapter_a = self._adapters["model.layer0.lora_A"]
        adapter_b = self._adapters["model.layer0.lora_B"]
        prediction = inputs @ weight.T + (inputs @ adapter_a.T) @ adapter_b.T
        loss = torch.mean((prediction - targets) ** 2)
        if not torch.isfinite(loss):
            raise BackendError("NONFINITE_LOSS")
        loss.backward()  # type: ignore[no-untyped-call]
        with torch.no_grad():
            for parameter in self._adapters.values():
                if parameter.grad is None or not torch.all(torch.isfinite(parameter.grad)):
                    raise BackendError("ADAPTER_GRADIENT_INVALID")
                parameter.add_(parameter.grad, alpha=-learning_rate)
                parameter.grad = None
        self._step += 1
        return float(loss.detach())


@dataclass(frozen=True, slots=True)
class BitsAndBytesAdapter:
    """Pinned production loader options; imports remain lazy for the CPU test environment."""

    backend_version: str
    compute_dtype: str
    quantization_type: str
    double_quantization: bool

    def loader_kwargs(self) -> dict[str, object]:
        if self.quantization_type != "NF4" or self.compute_dtype not in {"FLOAT16", "BFLOAT16"}:
            raise BackendError("PRODUCTION_QUANTIZATION_PROFILE_UNSUPPORTED")
        return {
            "bnb_4bit_compute_dtype": self.compute_dtype.lower(),
            "bnb_4bit_quant_type": "nf4",
            "bnb_4bit_use_double_quant": self.double_quantization,
            "load_in_4bit": True,
            "local_files_only": True,
            "trust_remote_code": False,
            "use_safetensors": True,
        }
