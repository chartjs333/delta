from __future__ import annotations

from pathlib import Path

import pytest
import torch
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.tickets import DataRange, DomainPureWorkTicket
from deltatorrent.qlora.backend import TinyOfflineBackend
from deltatorrent.qlora.contribution import ContributionError, encode_adapter_contribution
from deltatorrent.qlora.model_loader import load_tiny_backend
from deltatorrent.qlora.trainer import Batch, Ticket, ticket_from_domain_pure, train_fixed_ticket

FIXTURE = Path(__file__).parents[1] / "fixtures" / "models" / "tiny_qlora"


def _ticket() -> Ticket:
    return Ticket("tiny-ticket-009", "tiny-text", 8, 2, "sha256:" + "a" * 64)


def _batches() -> tuple[Batch, ...]:
    return (
        Batch(torch.tensor([[1.0, 0.0], [0.0, 1.0]]), torch.zeros((2, 2)), 4),
        Batch(torch.tensor([[1.0, 1.0], [0.5, -0.5]]), torch.ones((2, 2)), 4),
    )


def _artifact(name: str, digest: str) -> ArtifactRef:
    return ArtifactRef(
        content_id="sha256:" + digest * 64,
        media_type="application/octet-stream",
        schema_id="SCHEMA-TEST-V1",
        schema_version="1.0.0",
        byte_length=1,
        locator=f"objects/{name}",
    )


def test_feature007_ticket_projection_preserves_fixed_b_and_h() -> None:
    source = DomainPureWorkTicket(
        ticket_id="ticket-009",
        domain_id="tiny-text",
        data=_artifact("data", "b"),
        data_range=DataRange(0, 8),
        batch_budget=8,
        step_budget=2,
        parent_model=_artifact("adapter", "a"),
        parameter_schema_id="sha256:" + "c" * 64,
        optimizer_profile_id="sha256:" + "d" * 64,
        arithmetic_profile_id="sha256:" + "e" * 64,
        deterministic_seed=9,
        logical_deadline_ms=1_000,
    )
    projected = ticket_from_domain_pure(source)
    assert projected.batch_budget == source.batch_budget
    assert projected.optimizer_steps == source.step_budget
    assert projected.parent_adapter_id == source.parent_model.content_id


def test_complete_ticket_emits_normalized_canonical_adapter_shards() -> None:
    _, backend = load_tiny_backend(FIXTURE)
    result = train_fixed_ticket(backend, _ticket(), _batches(), learning_rate=0.01)

    assert result.status == "COMPLETE"
    assert result.eligible_for_commitment
    assert result.actual_optimizer_steps == _ticket().optimizer_steps
    assert result.processed_tokens == _ticket().batch_budget
    assert result.base_hash_before == result.base_hash_after
    contribution = encode_adapter_contribution(
        result.parent_adapters,
        result.final_adapters,
        actual_optimizer_steps=result.actual_optimizer_steps,
        expected_optimizer_steps=_ticket().optimizer_steps,
    )
    assert tuple(item.parameter_name for item in contribution.ordered_shards) == (
        "model.layer0.lora_A",
        "model.layer0.lora_B",
    )
    assert contribution.commitment_root.startswith("sha256:")
    assert all(item.envelope.startswith(b"DRQ1") for item in contribution.ordered_shards)


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("oom", "OOM"),
        ("cancel", "CANCELLED"),
        ("exhausted", "DATA_EXHAUSTED"),
        ("partial", "PARTIAL_TICKET"),
    ],
)
def test_terminal_failures_never_publish(kind: str, expected: str) -> None:
    _, backend = load_tiny_backend(FIXTURE)
    ticket = _ticket()
    batches = _batches()
    cancelled_value = kind == "cancel"

    def cancelled() -> bool:
        return cancelled_value

    if kind == "oom":
        backend.fail_on_step = 0
    elif kind == "exhausted":
        batches = batches[:1]
    elif kind == "partial":
        batches = (Batch(batches[0].inputs, batches[0].targets, 3), batches[1])
    result = train_fixed_ticket(backend, ticket, batches, learning_rate=0.01, cancelled=cancelled)

    assert result.status == expected
    assert not result.eligible_for_commitment
    assert result.final_adapters is None
    with pytest.raises(ContributionError, match="INCOMPLETE_TICKET_NOT_ENCODABLE"):
        encode_adapter_contribution(
            result.parent_adapters,
            result.final_adapters,
            actual_optimizer_steps=result.actual_optimizer_steps,
            expected_optimizer_steps=ticket.optimizer_steps,
        )


def test_base_mutation_and_nonfinite_adapter_are_terminal() -> None:
    _, original = load_tiny_backend(FIXTURE)

    class MutatingBackend(TinyOfflineBackend):
        def train_step(
            self, inputs: torch.Tensor, targets: torch.Tensor, learning_rate: float
        ) -> float:
            loss = super().train_step(inputs, targets, learning_rate)
            self._base["model.layer0.weight"][0, 0] += 1
            return loss

    backend = MutatingBackend(original._base, original._buffers, original._adapters)
    result = train_fixed_ticket(backend, _ticket(), _batches(), learning_rate=0.01)
    assert result.status == "BASE_MUTATION"
    assert not result.eligible_for_commitment

    _, backend = load_tiny_backend(FIXTURE)
    backend._adapters["model.layer0.lora_A"].data[0, 0] = float("nan")
    result = train_fixed_ticket(backend, _ticket(), _batches(), learning_rate=0.01)
    assert result.status in {"BACKEND_FAILURE", "NONFINITE_ADAPTER"}
    assert not result.eligible_for_commitment
