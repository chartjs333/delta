"""Tiny deterministic bigram causal language model."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor, nn

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id


class TinyCausalLM(nn.Module):
    def __init__(self, vocab_size: int, hidden_size: int, seed: int) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.output = nn.Linear(hidden_size, vocab_size)
        generator = torch.Generator(device="cpu")
        generator.manual_seed(seed)
        with torch.no_grad():
            self.embedding.weight.normal_(mean=0.0, std=0.02, generator=generator)
            self.output.weight.normal_(mean=0.0, std=0.02, generator=generator)
            self.output.bias.zero_()

    def forward(self, token_ids: Tensor) -> Tensor:
        return cast(Tensor, self.output(self.embedding(token_ids)))


def parameter_schema_id(model: nn.Module) -> str:
    records = [
        {
            "dtype": str(parameter.dtype).removeprefix("torch."),
            "name": name,
            "shape": list(parameter.shape),
        }
        for name, parameter in sorted(model.named_parameters())
    ]
    return sha256_content_id(canonical_json_bytes({"parameters": records, "version": "1.0.0"}))
