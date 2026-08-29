from __future__ import annotations

from pathlib import Path

import pytest
import torch
from deltatorrent.qlora.adapter_schema import (
    AdapterSchemaError,
    assert_adapter_only_optimizer,
    resolve_adapter_schema,
)
from deltatorrent.qlora.backend import BackendError, logical_base_hash, validate_backend_contract
from deltatorrent.qlora.model_loader import load_tiny_backend

FIXTURE = Path(__file__).parents[1] / "fixtures" / "models" / "tiny_qlora"


def test_tiny_backend_has_exact_adapter_only_schema_and_immutable_base() -> None:
    request, backend = load_tiny_backend(FIXTURE)
    before = logical_base_hash(backend)
    schema = resolve_adapter_schema(backend, ("model.layer0",))

    assert tuple(item.name for item in schema) == (
        "model.layer0.lora_A",
        "model.layer0.lora_B",
    )
    assert set(backend.base_tensors()) == set(request.manifest.persistent_base_parameters)
    assert_adapter_only_optimizer(backend, tuple(backend.adapter_tensors().values()))
    validate_backend_contract(
        backend,
        expected_name="MOCK_INT4",
        expected_version="fixture-1",
        approved_ephemeral_caches=(),
    )
    backend.train_step(torch.ones((2, 2)), torch.zeros((2, 2)), 0.01)
    assert logical_base_hash(backend) == before
    assert all(value.grad is None for value in backend.base_tensors().values())


@pytest.mark.parametrize(
    ("targets", "code"),
    [
        ((), "ZERO_TARGET_MODULES"),
        (("model.layer0", "model.layer0"), "DUPLICATE_TARGET_MODULE"),
        (("model.unexpected",), "TARGET_MODULE_SET_MISMATCH"),
    ],
)
def test_target_resolution_is_exact(targets: tuple[str, ...], code: str) -> None:
    _, backend = load_tiny_backend(FIXTURE)
    with pytest.raises(AdapterSchemaError, match=code):
        resolve_adapter_schema(backend, targets)


def test_unexpected_and_tied_adapter_parameters_are_rejected() -> None:
    _, backend = load_tiny_backend(FIXTURE)
    backend._adapters["model.layer0.unexpected"] = torch.nn.Parameter(torch.zeros(1))
    with pytest.raises(AdapterSchemaError, match="ADAPTER_PARAMETER_SET_MISMATCH"):
        resolve_adapter_schema(backend, ("model.layer0",))
    backend._adapters.pop("model.layer0.unexpected")
    backend._adapters["model.layer0.lora_B"] = backend._adapters["model.layer0.lora_A"]
    with pytest.raises(AdapterSchemaError, match="TIED_ADAPTER_PARAMETER"):
        resolve_adapter_schema(backend, ("model.layer0",))


def test_optimizer_rejects_missing_or_base_parameters() -> None:
    _, backend = load_tiny_backend(FIXTURE)
    with pytest.raises(AdapterSchemaError, match="OPTIMIZER_PARAMETER_SET_MISMATCH"):
        assert_adapter_only_optimizer(backend, (backend._adapters["model.layer0.lora_A"],))
    base = next(iter(backend.base_tensors().values()))
    base.requires_grad_(True)
    with pytest.raises(AdapterSchemaError, match="OPTIMIZER_PARAMETER_SET_MISMATCH"):
        assert_adapter_only_optimizer(backend, (*backend._adapters.values(), base))


def test_backend_version_and_cache_policy_are_exact() -> None:
    _, backend = load_tiny_backend(FIXTURE)
    with pytest.raises(BackendError, match="BACKEND_VERSION_MISMATCH"):
        validate_backend_contract(
            backend,
            expected_name="MOCK_INT4",
            expected_version="fixture-2",
            approved_ephemeral_caches=(),
        )
    with pytest.raises(BackendError, match="EPHEMERAL_CACHE_POLICY_MISMATCH"):
        validate_backend_contract(
            backend,
            expected_name="MOCK_INT4",
            expected_version="fixture-1",
            approved_ephemeral_caches=("model.cache",),
        )
