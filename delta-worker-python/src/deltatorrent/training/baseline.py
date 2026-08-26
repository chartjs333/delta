"""Deterministic gradient-accumulated AdamW training loop."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch
from torch import Tensor, nn
from torch.nn import functional as functional

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import DeterministicSampler, TokenSample
from deltatorrent.training.model import TinyCausalLM


@dataclass(frozen=True, slots=True)
class TrainingMetric:
    step: int
    optimizer_step: int
    processed_tokens: int
    loss: float
    learning_rate: float


@dataclass(slots=True)
class CanonicalAdamW:
    parameters: dict[str, nn.Parameter]
    learning_rate: float
    beta1: float
    beta2: float
    epsilon: float
    weight_decay: float
    step_count: int = 0
    first_moment: dict[str, Tensor] = field(default_factory=dict)
    second_moment: dict[str, Tensor] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.parameters = dict(sorted(self.parameters.items()))
        if not self.first_moment:
            self.first_moment = {
                name: torch.zeros_like(parameter) for name, parameter in self.parameters.items()
            }
        if not self.second_moment:
            self.second_moment = {
                name: torch.zeros_like(parameter) for name, parameter in self.parameters.items()
            }

    def step(self) -> None:
        self.step_count += 1
        bias1 = 1.0 - self.beta1**self.step_count
        bias2 = 1.0 - self.beta2**self.step_count
        with torch.no_grad():
            for name, parameter in self.parameters.items():
                gradient = parameter.grad
                if gradient is None:
                    raise DeltaError(ErrorCode.INVALID_MANIFEST, "MISSING_GRADIENT", {"name": name})
                if not bool(torch.isfinite(gradient).all()):
                    raise DeltaError(
                        ErrorCode.INVALID_MANIFEST, "NON_FINITE_GRADIENT", {"name": name}
                    )
                first = self.first_moment[name]
                second = self.second_moment[name]
                first.mul_(self.beta1).add_(gradient, alpha=1.0 - self.beta1)
                second.mul_(self.beta2).addcmul_(gradient, gradient, value=1.0 - self.beta2)
                if self.weight_decay:
                    parameter.mul_(1.0 - self.learning_rate * self.weight_decay)
                denominator = second.sqrt().div_(math.sqrt(bias2)).add_(self.epsilon)
                parameter.addcdiv_(first, denominator, value=-(self.learning_rate / bias1))
                parameter.grad = None


@dataclass(slots=True)
class TrainingState:
    model: TinyCausalLM
    optimizer: CanonicalAdamW
    sampler: DeterministicSampler
    micro_step: int = 0
    optimizer_step: int = 0
    processed_tokens: int = 0

    @classmethod
    def create(cls, config: BaselineConfig, sample_count: int) -> TrainingState:
        torch.use_deterministic_algorithms(True)
        torch.set_num_threads(1)
        torch.manual_seed(config.seed)
        model = TinyCausalLM(config.vocab_size, config.hidden_size, config.seed)
        optimizer = CanonicalAdamW(
            parameters=dict(model.named_parameters()),
            learning_rate=config.learning_rate,
            beta1=config.beta1,
            beta2=config.beta2,
            epsilon=config.epsilon,
            weight_decay=config.weight_decay,
        )
        return cls(
            model=model,
            optimizer=optimizer,
            sampler=DeterministicSampler(sample_count, config.seed),
        )


def train_to_optimizer_step(
    state: TrainingState,
    config: BaselineConfig,
    samples: tuple[TokenSample, ...],
    target_optimizer_step: int,
) -> tuple[TrainingMetric, ...]:
    if (
        target_optimizer_step < state.optimizer_step
        or target_optimizer_step > config.optimizer_steps
    ):
        raise ValueError("TRAINING_TARGET_INVALID")
    accumulated_loss = 0.0
    metrics: list[TrainingMetric] = []
    while state.optimizer_step < target_optimizer_step:
        indices = state.sampler.take(config.batch_size)
        inputs = torch.tensor([samples[index].inputs for index in indices], dtype=torch.long)
        targets = torch.tensor([samples[index].targets for index in indices], dtype=torch.long)
        logits = state.model(inputs)
        loss = functional.cross_entropy(
            logits.reshape(-1, config.vocab_size),
            targets.reshape(-1),
            ignore_index=0,
        )
        if not bool(torch.isfinite(loss)):
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "NON_FINITE_LOSS")
        (loss / config.gradient_accumulation_steps).backward()  # type: ignore[no-untyped-call]
        accumulated_loss += float(loss.detach())
        state.micro_step += 1
        state.processed_tokens += int(targets.ne(0).sum())
        if state.micro_step % config.gradient_accumulation_steps != 0:
            continue
        state.optimizer.step()
        state.optimizer_step += 1
        metrics.append(
            TrainingMetric(
                step=state.micro_step,
                optimizer_step=state.optimizer_step,
                processed_tokens=state.processed_tokens,
                loss=accumulated_loss / config.gradient_accumulation_steps,
                learning_rate=config.learning_rate,
            )
        )
        accumulated_loss = 0.0
    return tuple(metrics)
