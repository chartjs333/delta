"""Fixed-ticket adapter-only local training with terminal no-publication failures."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import torch

from deltatorrent.domain.tickets import DomainPureWorkTicket
from deltatorrent.qlora.adapter_schema import assert_adapter_only_optimizer
from deltatorrent.qlora.backend import (
    QuantizedAdapterBackend,
    clone_adapters,
    logical_base_hash,
)


@dataclass(frozen=True, slots=True)
class Ticket:
    ticket_id: str
    domain_id: str
    batch_budget: int
    optimizer_steps: int
    parent_adapter_id: str


@dataclass(frozen=True, slots=True)
class Batch:
    inputs: torch.Tensor
    targets: torch.Tensor
    token_count: int


@dataclass(frozen=True, slots=True)
class TrainingResult:
    status: str
    actual_optimizer_steps: int
    processed_tokens: int
    base_hash_before: str
    base_hash_after: str
    parent_adapters: dict[str, torch.Tensor]
    final_adapters: dict[str, torch.Tensor] | None
    losses: tuple[float, ...]
    eligible_for_commitment: bool


def ticket_from_domain_pure(ticket: DomainPureWorkTicket) -> Ticket:
    """Project the feature-007 ticket without changing its fixed B/H budgets."""

    return Ticket(
        ticket_id=ticket.ticket_id,
        domain_id=ticket.domain_id,
        batch_budget=ticket.batch_budget,
        optimizer_steps=ticket.step_budget,
        parent_adapter_id=ticket.parent_model.content_id,
    )


def _failure(
    code: str,
    steps: int,
    tokens: int,
    before: str,
    backend: QuantizedAdapterBackend,
    parent: dict[str, torch.Tensor],
    losses: list[float],
) -> TrainingResult:
    return TrainingResult(
        status=code,
        actual_optimizer_steps=steps,
        processed_tokens=tokens,
        base_hash_before=before,
        base_hash_after=logical_base_hash(backend),
        parent_adapters=parent,
        final_adapters=None,
        losses=tuple(losses),
        eligible_for_commitment=False,
    )


def train_fixed_ticket(
    backend: QuantizedAdapterBackend,
    ticket: Ticket,
    batches: Sequence[Batch],
    *,
    learning_rate: float,
    cancelled: Callable[[], bool] = lambda: False,
) -> TrainingResult:
    if ticket.optimizer_steps <= 0 or ticket.batch_budget <= 0 or learning_rate <= 0:
        raise ValueError("TICKET_TRAINING_CONFIG_INVALID")
    assert_adapter_only_optimizer(backend, tuple(backend.adapter_tensors().values()))
    before = logical_base_hash(backend)
    parent = clone_adapters(backend)
    steps = 0
    tokens = 0
    losses: list[float] = []
    for step in range(ticket.optimizer_steps):
        if cancelled():
            return _failure("CANCELLED", steps, tokens, before, backend, parent, losses)
        if step >= len(batches):
            return _failure("DATA_EXHAUSTED", steps, tokens, before, backend, parent, losses)
        batch = batches[step]
        if batch.token_count <= 0 or tokens + batch.token_count > ticket.batch_budget:
            return _failure("BATCH_BUDGET_INVALID", steps, tokens, before, backend, parent, losses)
        try:
            losses.append(backend.train_step(batch.inputs, batch.targets, learning_rate))
        except RuntimeError as exc:
            code = "OOM" if "out of memory" in str(exc).lower() else "BACKEND_FAILURE"
            return _failure(code, steps, tokens, before, backend, parent, losses)
        steps += 1
        tokens += batch.token_count
        if logical_base_hash(backend) != before:
            return _failure("BASE_MUTATION", steps, tokens, before, backend, parent, losses)
    if steps != ticket.optimizer_steps or tokens != ticket.batch_budget:
        return _failure("PARTIAL_TICKET", steps, tokens, before, backend, parent, losses)
    final = clone_adapters(backend)
    if any(not torch.all(torch.isfinite(value)) for value in final.values()):
        return _failure("NONFINITE_ADAPTER", steps, tokens, before, backend, parent, losses)
    after = logical_base_hash(backend)
    if after != before:
        return _failure("BASE_MUTATION", steps, tokens, before, backend, parent, losses)
    return TrainingResult(
        status="COMPLETE",
        actual_optimizer_steps=steps,
        processed_tokens=tokens,
        base_hash_before=before,
        base_hash_after=after,
        parent_adapters=parent,
        final_adapters=final,
        losses=tuple(losses),
        eligible_for_commitment=True,
    )
