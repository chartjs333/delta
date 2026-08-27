"""Worker-local final = parent - LocalDelta reconstruction."""

from __future__ import annotations

from collections.abc import Mapping

import torch
from torch import Tensor

from deltatorrent.delta.schema import included_tensor_names, validate_parameter_mapping
from deltatorrent.delta.validation import validate_fp32_tensor_bundle
from deltatorrent.domain.parameters import ParameterSchema


def reconstruct_final(
    parent: Mapping[str, Tensor],
    local_delta: Mapping[str, Tensor],
    schema: ParameterSchema,
) -> dict[str, Tensor]:
    validate_parameter_mapping(parent, schema)
    validate_fp32_tensor_bundle(local_delta, schema)
    reconstructed = {
        name: (parent[name].detach().to(device="cpu", dtype=torch.float32) - local_delta[name])
        .contiguous()
        .clone()
        for name in included_tensor_names(schema)
    }
    validate_fp32_tensor_bundle(reconstructed, schema)
    return reconstructed
