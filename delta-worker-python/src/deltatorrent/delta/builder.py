"""Canonical FP32 LocalDelta = parent - final construction."""

from __future__ import annotations

from collections.abc import Mapping

import torch
from torch import Tensor, nn

from deltatorrent.delta.schema import (
    canonical_parameter_tensors,
    included_tensor_names,
    validate_parameter_mapping,
)
from deltatorrent.delta.validation import validate_fp32_tensor_bundle
from deltatorrent.domain.parameters import ParameterSchema


def snapshot_fp32_parameters(module: nn.Module, schema: ParameterSchema) -> dict[str, Tensor]:
    parameters = canonical_parameter_tensors(module, schema)
    return {
        name: parameters[name].detach().to(device="cpu", dtype=torch.float32).contiguous().clone()
        for name in included_tensor_names(schema)
    }


def build_local_delta(
    parent: Mapping[str, Tensor],
    final: Mapping[str, Tensor],
    schema: ParameterSchema,
) -> dict[str, Tensor]:
    validate_parameter_mapping(parent, schema)
    validate_parameter_mapping(final, schema)
    result = {
        name: (
            parent[name].detach().to(device="cpu", dtype=torch.float32)
            - final[name].detach().to(device="cpu", dtype=torch.float32)
        )
        .contiguous()
        .clone()
        for name in included_tensor_names(schema)
    }
    validate_fp32_tensor_bundle(result, schema)
    return result
