from __future__ import annotations

import torch
from deltatorrent.delta.schema import (
    canonical_parameter_tensors,
    derive_parameter_schema,
    included_tensor_names,
)
from deltatorrent.domain.parameters import FrozenOmissionPolicy, ParameterSchema
from torch import nn


class TiedModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embedding = nn.Embedding(4, 3)
        self.frozen_scale = nn.Parameter(torch.ones(()), requires_grad=False)
        self.lm_head = nn.Linear(3, 4, bias=False)
        self.lm_head.weight = self.embedding.weight


def test_schema_has_one_canonical_owner_and_explicit_tied_alias() -> None:
    model = TiedModel()
    schema = derive_parameter_schema(model)

    assert tuple(item.name for item in schema.parameters) == (
        "embedding.weight",
        "frozen_scale",
    )
    assert dict(schema.tied_aliases) == {"lm_head.weight": "embedding.weight"}
    assert included_tensor_names(schema) == ("embedding.weight",)
    assert tuple(canonical_parameter_tensors(model, schema)) == ("embedding.weight",)
    assert ParameterSchema.from_dict(schema.to_dict()).fingerprint == schema.fingerprint
    assert derive_parameter_schema(model).fingerprint == schema.fingerprint
    assert derive_parameter_schema(TiedModel()).fingerprint == schema.fingerprint


def test_include_all_policy_keeps_frozen_parameter_in_tensor_order() -> None:
    model = TiedModel()
    schema = derive_parameter_schema(
        model,
        omission_policy=FrozenOmissionPolicy.INCLUDE_ALL,
    )
    assert included_tensor_names(schema) == ("embedding.weight", "frozen_scale")
    assert tuple(canonical_parameter_tensors(model, schema)) == (
        "embedding.weight",
        "frozen_scale",
    )
