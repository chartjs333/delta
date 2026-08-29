"""Deterministic target resolution and adapter parameter schema checks."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from deltatorrent.qlora.backend import QuantizedAdapterBackend


class AdapterSchemaError(ValueError):
    """Stable rejection for ambiguous adapter state."""


@dataclass(frozen=True, slots=True)
class AdapterParameter:
    name: str
    target_module: str
    shape: tuple[int, ...]
    logical_dtype: str
    alias_owner: str


def resolve_adapter_schema(
    backend: QuantizedAdapterBackend, expected_targets: tuple[str, ...]
) -> tuple[AdapterParameter, ...]:
    if not expected_targets:
        raise AdapterSchemaError("ZERO_TARGET_MODULES")
    if len(set(expected_targets)) != len(expected_targets):
        raise AdapterSchemaError("DUPLICATE_TARGET_MODULE")
    if backend.target_modules() != expected_targets:
        raise AdapterSchemaError("TARGET_MODULE_SET_MISMATCH")
    adapters = backend.adapter_tensors()
    expected_names = tuple(
        name for target in expected_targets for name in (f"{target}.lora_A", f"{target}.lora_B")
    )
    if tuple(sorted(adapters)) != tuple(sorted(expected_names)):
        raise AdapterSchemaError("ADAPTER_PARAMETER_SET_MISMATCH")
    pointers: dict[int, str] = {}
    result: list[AdapterParameter] = []
    for name in expected_names:
        value = adapters[name]
        if not isinstance(value, torch.nn.Parameter) or not value.requires_grad:
            raise AdapterSchemaError("ADAPTER_NOT_TRAINABLE")
        pointer = value.data_ptr()
        if pointer in pointers:
            raise AdapterSchemaError(f"TIED_ADAPTER_PARAMETER:{pointers[pointer]}:{name}")
        pointers[pointer] = name
        result.append(
            AdapterParameter(
                name=name,
                target_module=name.rsplit(".", 1)[0],
                shape=tuple(value.shape),
                logical_dtype=str(value.dtype).removeprefix("torch.").upper(),
                alias_owner=name,
            )
        )
    base_ids = {id(value) for value in backend.base_tensors().values()}
    if base_ids & {id(value) for value in adapters.values()}:
        raise AdapterSchemaError("BASE_TENSOR_IN_ADAPTER_SET")
    return tuple(result)


def assert_adapter_only_optimizer(
    backend: QuantizedAdapterBackend, parameters: tuple[torch.nn.Parameter, ...]
) -> None:
    expected = {id(value) for value in backend.adapter_tensors().values()}
    actual = {id(value) for value in parameters}
    if actual != expected or len(parameters) != len(expected):
        raise AdapterSchemaError("OPTIMIZER_PARAMETER_SET_MISMATCH")
    if any(value.requires_grad for value in backend.base_tensors().values()):
        raise AdapterSchemaError("BASE_TENSOR_REQUIRES_GRAD")
