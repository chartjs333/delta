from __future__ import annotations

import pytest
import torch
from deltatorrent.delta.builder import build_local_delta, snapshot_fp32_parameters
from deltatorrent.delta.reconstruction import reconstruct_final
from deltatorrent.delta.schema import derive_parameter_schema
from deltatorrent.training.model import TinyCausalLM


@pytest.mark.skipif(not torch.cuda.is_available(), reason="optional CUDA smoke path")
def test_cuda_half_parameters_project_to_fp32_local_delta_reference() -> None:
    model = TinyCausalLM(vocab_size=7, hidden_size=3, seed=7).cuda().half()
    schema = derive_parameter_schema(model)
    parent = snapshot_fp32_parameters(model, schema)
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.add_(torch.full_like(parameter, 0.125))
    final = snapshot_fp32_parameters(model, schema)
    local_delta = build_local_delta(parent, final, schema)
    reconstructed = reconstruct_final(parent, local_delta, schema)
    assert all(
        tensor.device.type == "cpu" and tensor.dtype is torch.float32
        for tensor in local_delta.values()
    )
    for name in final:
        torch.testing.assert_close(reconstructed[name], final[name], rtol=0, atol=0)
