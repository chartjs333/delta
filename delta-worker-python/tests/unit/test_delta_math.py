from __future__ import annotations

from pathlib import Path

import pytest
import torch
from deltatorrent.delta.builder import build_local_delta, snapshot_fp32_parameters
from deltatorrent.delta.normalization import normalize_local_delta, require_complete_steps
from deltatorrent.delta.reconstruction import reconstruct_final
from deltatorrent.delta.schema import derive_parameter_schema
from deltatorrent.delta.validation import validate_fp32_tensor_bundle
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.parameters import ParameterSchema
from deltatorrent.training.baseline import TrainingState, train_to_optimizer_step
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, load_samples
from deltatorrent.training.model import TinyCausalLM

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"


def _trained_delta() -> tuple[
    dict[str, torch.Tensor],
    dict[str, torch.Tensor],
    dict[str, torch.Tensor],
    ParameterSchema,
]:
    config = BaselineConfig.from_json_file(CONFIG)
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)
    state = TrainingState.create(config, len(samples))
    schema = derive_parameter_schema(state.model)
    parent = snapshot_fp32_parameters(state.model, schema)
    train_to_optimizer_step(state, config, samples, 1)
    final = snapshot_fp32_parameters(state.model, schema)
    local_delta = build_local_delta(parent, final, schema)
    return parent, final, local_delta, schema


def test_parent_minus_final_reconstructs_and_normalizes_in_canonical_order() -> None:
    parent, final, local_delta, schema = _trained_delta()
    reconstructed = reconstruct_final(parent, local_delta, schema)
    normalized = normalize_local_delta(
        local_delta,
        schema,
        effective_steps=1,
        step_budget=1,
    )

    assert tuple(local_delta) == tuple(sorted(local_delta))
    assert tuple(normalized) == tuple(local_delta)
    for name in local_delta:
        torch.testing.assert_close(local_delta[name], parent[name] - final[name], rtol=0, atol=0)
        torch.testing.assert_close(reconstructed[name], final[name], rtol=1e-6, atol=1e-7)
        torch.testing.assert_close(normalized[name], local_delta[name], rtol=0, atol=0)


def test_normalization_uses_exact_effective_step_denominator() -> None:
    _, _, local_delta, schema = _trained_delta()
    doubled = {name: tensor.mul(2).contiguous() for name, tensor in local_delta.items()}
    normalized = normalize_local_delta(
        doubled,
        schema,
        effective_steps=2,
        step_budget=2,
    )
    for name in local_delta:
        torch.testing.assert_close(normalized[name], local_delta[name], rtol=0, atol=0)

    for effective_steps, step_budget in ((0, 0), (1, 2), (3, 2), (True, 1)):
        with pytest.raises(DeltaError) as raised:
            require_complete_steps(
                effective_steps=effective_steps,
                step_budget=step_budget,
            )
        assert raised.value.code is ErrorCode.INVALID_CONTRIBUTION_CANDIDATE


def test_validation_rejects_wrong_set_order_shape_dtype_nonfinite_and_norm() -> None:
    _, _, local_delta, schema = _trained_delta()
    names = tuple(local_delta)

    reversed_bundle = {name: local_delta[name] for name in reversed(names)}
    malformed = dict(local_delta)
    malformed.pop(names[0])
    wrong_shape = dict(local_delta)
    wrong_shape[names[0]] = wrong_shape[names[0]].reshape(-1)
    wrong_dtype = dict(local_delta)
    wrong_dtype[names[0]] = wrong_dtype[names[0]].double()
    non_finite = {name: tensor.clone() for name, tensor in local_delta.items()}
    non_finite[names[0]].view(-1)[0] = float("nan")

    for candidate in (reversed_bundle, malformed, wrong_shape, wrong_dtype, non_finite):
        with pytest.raises(DeltaError) as raised:
            validate_fp32_tensor_bundle(candidate, schema)
        assert raised.value.code is ErrorCode.INVALID_DELTA_TENSOR

    with pytest.raises(DeltaError, match="DELTA_TENSOR_NORM_EXCEEDED"):
        validate_fp32_tensor_bundle(
            local_delta,
            schema,
            per_tensor_norm_ceiling=0.0,
        )
    with pytest.raises(DeltaError, match="DELTA_GLOBAL_NORM_EXCEEDED"):
        validate_fp32_tensor_bundle(
            local_delta,
            schema,
            global_norm_ceiling=0.0,
        )


def test_norm_summary_uses_canonical_ieee_bit_strings() -> None:
    _, _, local_delta, schema = _trained_delta()
    summary = validate_fp32_tensor_bundle(local_delta, schema)
    assert len(summary.max_abs_fp32_bits) == 8
    assert len(summary.global_l2_norm_fp64_bits) == 16
    assert summary.max_abs_fp32_bits == summary.max_abs_fp32_bits.lower()
    assert summary.global_l2_norm_fp64_bits == summary.global_l2_norm_fp64_bits.lower()


@pytest.mark.parametrize("seed", [0, 7, 1729, 20260826])
def test_randomized_fp32_reconstruction_property(seed: int) -> None:
    model = TinyCausalLM(vocab_size=7, hidden_size=3, seed=seed)
    schema = derive_parameter_schema(model)
    parent = snapshot_fp32_parameters(model, schema)
    generator = torch.Generator(device="cpu").manual_seed(seed + 1)
    final = {
        name: (tensor + torch.randn(tensor.shape, generator=generator) * 0.001).contiguous()
        for name, tensor in parent.items()
    }
    local_delta = build_local_delta(parent, final, schema)
    reconstructed = reconstruct_final(parent, local_delta, schema)
    for name in final:
        torch.testing.assert_close(reconstructed[name], final[name], rtol=1e-5, atol=1e-7)
