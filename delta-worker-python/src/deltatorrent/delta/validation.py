"""Exact tensor-set, FP32, finite and norm validation."""

from __future__ import annotations

import math
import struct
from collections.abc import Mapping
from dataclasses import dataclass

import torch
from torch import Tensor

from deltatorrent.delta.schema import included_tensor_names
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.parameters import ParameterSchema


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_DELTA_TENSOR, message, details)


@dataclass(frozen=True, slots=True)
class TensorNormSummary:
    max_abs_fp32_bits: str
    global_l2_norm_fp64_bits: str


def _ceiling(value: float | None, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _invalid("NORM_CEILING_INVALID", field=field)
    converted = float(value)
    if not math.isfinite(converted) or converted < 0.0:
        raise _invalid("NORM_CEILING_INVALID", field=field)
    return converted


def validate_fp32_tensor_bundle(
    tensors: Mapping[str, Tensor],
    schema: ParameterSchema,
    *,
    per_tensor_norm_ceiling: float | None = None,
    global_norm_ceiling: float | None = None,
) -> TensorNormSummary:
    expected = included_tensor_names(schema)
    if not isinstance(tensors, Mapping) or tuple(tensors) != expected:
        raise _invalid(
            "DELTA_TENSOR_SET_OR_ORDER_INVALID",
            actual=list(tensors) if isinstance(tensors, Mapping) else None,
            expected=list(expected),
        )
    per_tensor_limit = _ceiling(per_tensor_norm_ceiling, "per_tensor_norm_ceiling")
    global_limit = _ceiling(global_norm_ceiling, "global_norm_ceiling")
    specs = {item.name: item for item in schema.parameters}
    maximum = 0.0
    squared_norm = 0.0
    for name in expected:
        tensor = tensors[name]
        if (
            not isinstance(tensor, Tensor)
            or tuple(tensor.shape) != specs[name].shape
            or tensor.dtype is not torch.float32
            or tensor.device.type != "cpu"
            or not tensor.is_contiguous()
        ):
            raise _invalid("DELTA_TENSOR_LAYOUT_INVALID", name=name)
        if not bool(torch.isfinite(tensor).all()):
            raise _invalid("DELTA_TENSOR_NON_FINITE", name=name)
        tensor_maximum = float(tensor.abs().max())
        tensor_norm = float(torch.linalg.vector_norm(tensor.double()))
        if per_tensor_limit is not None and tensor_norm > per_tensor_limit:
            raise _invalid("DELTA_TENSOR_NORM_EXCEEDED", name=name)
        maximum = max(maximum, tensor_maximum)
        squared_norm += tensor_norm * tensor_norm
    global_norm = math.sqrt(squared_norm)
    if not math.isfinite(global_norm):
        raise _invalid("DELTA_GLOBAL_NORM_NON_FINITE")
    if global_limit is not None and global_norm > global_limit:
        raise _invalid("DELTA_GLOBAL_NORM_EXCEEDED")
    return TensorNormSummary(
        max_abs_fp32_bits=struct.pack(">f", maximum).hex(),
        global_l2_norm_fp64_bits=struct.pack(">d", global_norm).hex(),
    )
