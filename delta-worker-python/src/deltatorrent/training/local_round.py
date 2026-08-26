"""Reusable single-optimizer-step loop with boundary-atomic accounting."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

import torch
from torch import Tensor, nn
from torch.nn import functional

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import DeterministicSampler, TokenSample
from deltatorrent.training.token_accounting import OptimizerBoundaryLedger


class _Optimizer(Protocol):
    def step(self) -> None: ...


class MutableTrainingState(Protocol):
    micro_step: int
    optimizer_step: int
    processed_tokens: int

    @property
    def model(self) -> nn.Module: ...

    @property
    def optimizer(self) -> _Optimizer: ...

    @property
    def sampler(self) -> DeterministicSampler: ...


@dataclass(frozen=True, slots=True)
class TrainingMetric:
    step: int
    optimizer_step: int
    processed_tokens: int
    loss: float
    learning_rate: float


def train_one_optimizer_step(
    state: MutableTrainingState,
    config: BaselineConfig,
    samples: tuple[TokenSample, ...],
    *,
    ledger: OptimizerBoundaryLedger | None = None,
    before_microbatch: Callable[[], None] | None = None,
) -> TrainingMetric:
    """Execute one AdamW update and commit counters only after it succeeds."""

    if state.optimizer_step >= config.optimizer_steps:
        raise ValueError("TRAINING_TARGET_INVALID")
    if state.micro_step % config.gradient_accumulation_steps != 0:
        raise ValueError("TRAINING_NOT_AT_OPTIMIZER_BOUNDARY")
    starting_cursor = state.sampler.cursor
    accumulated_loss = 0.0
    pending_tokens = 0
    pending_micro_steps = 0
    try:
        for _ in range(config.gradient_accumulation_steps):
            if before_microbatch is not None:
                before_microbatch()
            cursor_start = state.sampler.cursor
            indices = state.sampler.take(config.batch_size)
            cursor_end = state.sampler.cursor
            inputs = torch.tensor([samples[index].inputs for index in indices], dtype=torch.long)
            targets = torch.tensor([samples[index].targets for index in indices], dtype=torch.long)
            logits = cast(Tensor, state.model(inputs))
            loss = functional.cross_entropy(
                logits.reshape(-1, config.vocab_size),
                targets.reshape(-1),
                ignore_index=0,
            )
            if not bool(torch.isfinite(loss)):
                raise DeltaError(ErrorCode.INVALID_MANIFEST, "NON_FINITE_LOSS")
            (loss / config.gradient_accumulation_steps).backward()  # type: ignore[no-untyped-call]
            accumulated_loss += float(loss.detach())
            non_padding_tokens = int(targets.ne(0).sum())
            pending_tokens += non_padding_tokens
            pending_micro_steps += 1
            if ledger is not None:
                ledger.stage_microbatch(
                    cursor_start=cursor_start,
                    cursor_end=cursor_end,
                    non_padding_tokens=non_padding_tokens,
                )
        state.optimizer.step()
    except Exception:
        state.sampler.cursor = starting_cursor
        for parameter in state.model.parameters():
            parameter.grad = None
        if ledger is not None:
            ledger.discard_partial_accumulation()
        raise

    state.micro_step += pending_micro_steps
    state.optimizer_step += 1
    state.processed_tokens += pending_tokens
    if ledger is not None:
        record = ledger.commit_optimizer_step(
            expected_micro_steps=config.gradient_accumulation_steps
        )
        if (
            record.effective_steps != state.optimizer_step
            or record.committed_micro_steps != state.micro_step
            or record.processed_tokens != state.processed_tokens
        ):
            raise DeltaError(ErrorCode.INVALID_TOKEN_ACCOUNTING, "ACCOUNTING_STATE_DIVERGENCE")
    return TrainingMetric(
        step=state.micro_step,
        optimizer_step=state.optimizer_step,
        processed_tokens=state.processed_tokens,
        loss=accumulated_loss / config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
    )
