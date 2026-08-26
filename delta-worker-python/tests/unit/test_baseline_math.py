from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from deltatorrent.training.baseline import TrainingState, train_to_optimizer_step
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, load_samples
from deltatorrent.training.model import parameter_schema_id
from safetensors.torch import save as save_tensors

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"


def model_hash(state: TrainingState) -> str:
    tensors = {
        name: parameter.detach().cpu().contiguous()
        for name, parameter in sorted(state.model.named_parameters())
    }
    return hashlib.sha256(save_tensors(tensors)).hexdigest()


def test_one_optimizer_step_matches_frozen_numeric_reference() -> None:
    config = BaselineConfig.from_json_file(CONFIG)
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)
    state = TrainingState.create(config, len(samples))
    metrics = train_to_optimizer_step(state, config, samples, 1)
    assert len(metrics) == 1
    assert metrics[0].processed_tokens == 16
    # MKL/oneDNN reduction order differs slightly across supported CPU platforms.
    assert metrics[0].loss == pytest.approx(2.890206217765808, abs=5e-7)
    assert parameter_schema_id(state.model) == (
        "sha256:2e6342ebcadc1437c1b22a9d14ffe2fccf82e5dbdae210dc16783ae31bdd853b"
    )


def test_repeated_one_step_training_is_bit_identical() -> None:
    config = BaselineConfig.from_json_file(CONFIG)
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)
    first = TrainingState.create(config, len(samples))
    second = TrainingState.create(config, len(samples))
    train_to_optimizer_step(first, config, samples, 1)
    train_to_optimizer_step(second, config, samples, 1)
    assert model_hash(first) == model_hash(second)
