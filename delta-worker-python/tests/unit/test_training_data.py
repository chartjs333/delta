from __future__ import annotations

import json
from pathlib import Path

import pytest
from deltatorrent.domain.errors import DeltaError
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import DeterministicSampler, Tokenizer, load_samples

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"


def test_config_is_strict_versioned_and_integer_canonical() -> None:
    config = BaselineConfig.from_json_file(CONFIG)
    assert config.schema_version == "1.0.0"
    assert config.learning_rate == 0.01
    assert all(not isinstance(value, float) for value in config.to_dict().values())
    mutated = json.loads(CONFIG.read_text(encoding="utf-8"))
    mutated["unknown"] = True
    with pytest.raises(DeltaError, match="CONFIG_FIELDS_INVALID"):
        BaselineConfig.from_mapping(mutated)


def test_sampler_order_and_cursor_are_deterministic() -> None:
    first = DeterministicSampler(sample_count=7, seed=1729)
    second = DeterministicSampler(sample_count=7, seed=1729)
    assert first.take(20) == second.take(20)
    assert first.cursor == 20
    resumed = DeterministicSampler(sample_count=7, seed=1729, cursor=8)
    full = DeterministicSampler(sample_count=7, seed=1729)
    assert full.take(8) + resumed.take(6) == DeterministicSampler(7, 1729).take(14)


def test_corpus_fixture_produces_fixed_next_token_windows() -> None:
    config = BaselineConfig.from_json_file(CONFIG)
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)
    assert len(tokenizer.vocabulary) == config.vocab_size
    assert len(samples) == 11
    assert all(len(sample.inputs) == config.sequence_length for sample in samples)
    assert all(sample.inputs[1:] == sample.targets[:-1] for sample in samples)
