"""Canonical parameter traversal, tied aliases and schema verification."""

from __future__ import annotations

from collections.abc import Mapping

import torch
from torch import Tensor, nn

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.parameters import (
    FrozenOmissionPolicy,
    LogicalDType,
    ParameterSchema,
    ParameterSpec,
)

_DTYPES = {
    torch.bfloat16: LogicalDType.BFLOAT16,
    torch.float16: LogicalDType.FLOAT16,
    torch.float32: LogicalDType.FLOAT32,
    torch.float64: LogicalDType.FLOAT64,
}


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_PARAMETER_SCHEMA, message, details)


def _all_named_parameters(module: nn.Module) -> tuple[tuple[str, nn.Parameter], ...]:
    return tuple(sorted(module.named_parameters(remove_duplicate=False)))


def derive_parameter_schema(
    module: nn.Module,
    *,
    omission_policy: FrozenOmissionPolicy = FrozenOmissionPolicy.OMIT_FROZEN,
) -> ParameterSchema:
    """Derive one stable owner per parameter object and explicit aliases for ties."""

    if not isinstance(module, nn.Module):
        raise _invalid("PARAMETER_MODULE_INVALID")
    if not isinstance(omission_policy, FrozenOmissionPolicy):
        raise _invalid("FROZEN_OMISSION_POLICY_INVALID")
    grouped: dict[int, list[tuple[str, nn.Parameter]]] = {}
    for name, parameter in _all_named_parameters(module):
        grouped.setdefault(id(parameter), []).append((name, parameter))
    if not grouped:
        raise _invalid("PARAMETER_SET_EMPTY_OR_INVALID")

    specs: list[ParameterSpec] = []
    aliases: dict[str, str] = {}
    for group in grouped.values():
        owner_name, parameter = min(group, key=lambda item: item[0])
        try:
            logical_dtype = _DTYPES[parameter.dtype]
        except KeyError as exc:
            raise _invalid(
                "PARAMETER_DTYPE_UNSUPPORTED",
                dtype=str(parameter.dtype),
                name=owner_name,
            ) from exc
        specs.append(
            ParameterSpec(
                name=owner_name,
                shape=tuple(parameter.shape),
                logical_dtype=logical_dtype,
                trainable=parameter.requires_grad,
            )
        )
        aliases.update({name: owner_name for name, _ in group if name != owner_name})
    return ParameterSchema(
        parameters=tuple(sorted(specs, key=lambda item: item.name)),
        tied_aliases=aliases,
        frozen_omission_policy=omission_policy,
    )


def included_tensor_names(schema: ParameterSchema) -> tuple[str, ...]:
    if not isinstance(schema, ParameterSchema):
        raise _invalid("PARAMETER_SCHEMA_INVALID")
    if schema.frozen_omission_policy is FrozenOmissionPolicy.OMIT_FROZEN:
        return tuple(item.name for item in schema.parameters if item.trainable)
    return tuple(item.name for item in schema.parameters)


def canonical_parameter_tensors(
    module: nn.Module,
    schema: ParameterSchema,
) -> Mapping[str, Tensor]:
    """Return schema-verified owner tensors in canonical name order."""

    actual = derive_parameter_schema(module, omission_policy=schema.frozen_omission_policy)
    if actual.to_dict() != schema.to_dict():
        raise _invalid(
            "PARAMETER_SCHEMA_MISMATCH",
            actual=actual.fingerprint,
            expected=schema.fingerprint,
        )
    by_name = dict(_all_named_parameters(module))
    return {name: by_name[name] for name in included_tensor_names(schema)}


def validate_parameter_mapping(
    tensors: Mapping[str, Tensor],
    schema: ParameterSchema,
) -> None:
    """Validate exact names and shapes without imposing a storage dtype."""

    expected = included_tensor_names(schema)
    if tuple(sorted(tensors)) != expected:
        raise _invalid(
            "PARAMETER_TENSOR_SET_MISMATCH",
            actual=sorted(tensors),
            expected=list(expected),
        )
    specs = {item.name: item for item in schema.parameters}
    for name in expected:
        tensor = tensors[name]
        if not isinstance(tensor, Tensor) or tuple(tensor.shape) != specs[name].shape:
            raise _invalid("PARAMETER_TENSOR_SHAPE_MISMATCH", name=name)
