from __future__ import annotations

import pytest
import torch
from deltatorrent.qlora.qualification import QualificationError, _Fp32StateAdamW


def test_fp32_state_adamw_keeps_small_fp16_adapter_update_finite() -> None:
    adapter = torch.nn.Parameter(torch.zeros(4, dtype=torch.float16))
    optimizer = _Fp32StateAdamW([adapter], torch, learning_rate=1e-4)
    adapter.grad = torch.full_like(adapter, 1e-6)

    optimizer.step()

    assert torch.isfinite(adapter).all()
    assert torch.count_nonzero(adapter) == 4
    assert optimizer.state_bytes == 32
    assert optimizer.parameters[0] is adapter


def test_fp32_state_adamw_rejects_missing_adapter_gradient() -> None:
    adapter = torch.nn.Parameter(torch.zeros(1, dtype=torch.float16))
    optimizer = _Fp32StateAdamW([adapter], torch, learning_rate=1e-4)

    with pytest.raises(QualificationError, match="PHYSICAL_ADAPTER_GRADIENT_MISSING"):
        optimizer.step()
