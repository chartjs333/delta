from __future__ import annotations

from pathlib import Path

import pytest
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.training.baseline import TrainingState
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, load_samples
from deltatorrent.training.local_round import train_one_optimizer_step
from deltatorrent.training.token_accounting import OptimizerBoundaryLedger

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"


def test_ledger_commits_only_complete_optimizer_boundaries() -> None:
    ledger = OptimizerBoundaryLedger(range_start=10, range_end=18)
    ledger.stage_microbatch(cursor_start=10, cursor_end=12, non_padding_tokens=7)
    ledger.stage_microbatch(cursor_start=12, cursor_end=14, non_padding_tokens=6)
    committed = ledger.commit_optimizer_step(expected_micro_steps=2)
    assert committed.effective_steps == 1
    assert committed.observed_micro_steps == 2
    assert committed.committed_micro_steps == 2
    assert committed.processed_tokens == 13
    assert committed.cursor_end == 14
    assert committed.pending_micro_steps == 0

    ledger.stage_microbatch(cursor_start=14, cursor_end=16, non_padding_tokens=5)
    discarded = ledger.discard_partial_accumulation()
    assert discarded.observed_micro_steps == 3
    assert discarded.committed_micro_steps == 2
    assert discarded.processed_tokens == 13
    assert discarded.cursor_end == 14
    assert discarded.pending_micro_steps == 0


def test_ledger_rejects_gaps_and_partial_boundary_commit() -> None:
    ledger = OptimizerBoundaryLedger(range_start=0, range_end=8)
    with pytest.raises(DeltaError) as gap:
        ledger.stage_microbatch(cursor_start=1, cursor_end=3, non_padding_tokens=2)
    assert gap.value.code is ErrorCode.INVALID_TOKEN_ACCOUNTING

    ledger.stage_microbatch(cursor_start=0, cursor_end=2, non_padding_tokens=2)
    with pytest.raises(DeltaError, match="ACCOUNTING_BOUNDARY_INCOMPLETE"):
        ledger.commit_optimizer_step(expected_micro_steps=2)


def test_training_step_commits_sampler_tokens_and_a_j_together() -> None:
    config = BaselineConfig.from_json_file(CONFIG)
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)
    state = TrainingState.create(config, len(samples))
    ledger = OptimizerBoundaryLedger(range_start=0, range_end=4)

    metric = train_one_optimizer_step(state, config, samples, ledger=ledger)
    record = ledger.snapshot()
    assert metric.optimizer_step == record.effective_steps == 1
    assert metric.step == record.committed_micro_steps == 2
    assert metric.processed_tokens == record.processed_tokens == 16
    assert state.sampler.cursor == record.cursor_end == 4


def test_partial_accumulation_rolls_back_committed_accounting() -> None:
    config = BaselineConfig.from_json_file(CONFIG)
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)
    state = TrainingState.create(config, len(samples))
    ledger = OptimizerBoundaryLedger(range_start=0, range_end=4)
    calls = 0

    def cancel_before_second_microbatch() -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("CANCELLED")

    with pytest.raises(RuntimeError, match="CANCELLED"):
        train_one_optimizer_step(
            state,
            config,
            samples,
            ledger=ledger,
            before_microbatch=cancel_before_second_microbatch,
        )

    record = ledger.snapshot()
    assert record.observed_micro_steps == 1
    assert record.committed_micro_steps == 0
    assert record.processed_tokens == 0
    assert record.cursor_end == 0
    assert state.sampler.cursor == 0
    assert state.micro_step == state.optimizer_step == state.processed_tokens == 0
