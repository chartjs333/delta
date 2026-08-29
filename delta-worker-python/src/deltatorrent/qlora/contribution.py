"""Canonical feature-004 encoding of normalized adapter-only contributions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import torch

from deltatorrent.reference.fixedpoint_encoder import (
    Rational,
    encode_envelope,
    encode_payload,
    leaf_id,
    merkle_root,
    quantize,
)


class ContributionError(ValueError):
    """Stable rejection before an eligible adapter commitment exists."""


_DEFAULT_QUANTUM: Final = Rational(1, 10_000)


@dataclass(frozen=True, slots=True)
class EncodedAdapterShard:
    parameter_name: str
    normalized_values: tuple[float, ...]
    q_values: tuple[int, ...]
    envelope: bytes
    encoded_shard_id: str


@dataclass(frozen=True, slots=True)
class AdapterContribution:
    actual_optimizer_steps: int
    ordered_shards: tuple[EncodedAdapterShard, ...]
    commitment_root: str

    def manifest(
        self,
        *,
        ticket_context_id: str,
        training_mode_id: str,
        base_model_manifest_id: str,
        quantized_base_profile_id: str,
        adapter_parameter_schema_id: str,
        parent_adapter_id: str,
        memory_qualification_evidence_id: str,
        formal_semantics_id: str,
    ) -> dict[str, object]:
        return {
            "actual_optimizer_steps": self.actual_optimizer_steps,
            "adapter_parameter_schema_id": adapter_parameter_schema_id,
            "base_model_manifest_id": base_model_manifest_id,
            "commitment_root": self.commitment_root,
            "formal_semantics_id": formal_semantics_id,
            "memory_qualification_evidence_id": memory_qualification_evidence_id,
            "ordered_shards": [
                {
                    "encoded_shard_id": item.encoded_shard_id,
                    "parameter_name": item.parameter_name,
                    "shard_id": f"adapter-{index:03d}",
                }
                for index, item in enumerate(self.ordered_shards)
            ],
            "parent_adapter_id": parent_adapter_id,
            "quantized_base_profile_id": quantized_base_profile_id,
            "schema_version": "1.0.0",
            "ticket_context_id": ticket_context_id,
            "training_mode_id": training_mode_id,
            "type_name": "ADAPTER_CONTRIBUTION_MANIFEST",
        }


def _rational(value: float) -> Rational:
    numerator, denominator = value.as_integer_ratio()
    return Rational(numerator, denominator)


def encode_adapter_contribution(
    parent: dict[str, torch.Tensor],
    final: dict[str, torch.Tensor] | None,
    *,
    actual_optimizer_steps: int,
    expected_optimizer_steps: int,
    quantum: Rational = _DEFAULT_QUANTUM,
) -> AdapterContribution:
    if final is None or actual_optimizer_steps != expected_optimizer_steps:
        raise ContributionError("INCOMPLETE_TICKET_NOT_ENCODABLE")
    if actual_optimizer_steps <= 0 or set(parent) != set(final):
        raise ContributionError("ADAPTER_PARAMETER_SET_MISMATCH")
    shards: list[EncodedAdapterShard] = []
    for index, name in enumerate(sorted(parent)):
        if parent[name].shape != final[name].shape:
            raise ContributionError("ADAPTER_SHAPE_MISMATCH")
        normalized_tensor = (final[name].to(torch.float64) - parent[name].to(torch.float64)) / (
            actual_optimizer_steps
        )
        if not torch.all(torch.isfinite(normalized_tensor)):
            raise ContributionError("NONFINITE_ADAPTER_DELTA")
        normalized = tuple(float(value) for value in normalized_tensor.reshape(-1))
        q_values = tuple(quantize(_rational(value), quantum) for value in normalized)
        payload = encode_payload(q_values)
        header = {
            "normalization_denominator": actual_optimizer_steps,
            "parameter_name": name,
            "quantum": quantum.to_json(),
            "schema_version": "1.0.0",
            "shard_index": index,
            "storage_dtype": "int16-fixed-v1",
        }
        envelope = encode_envelope(header, payload)
        shards.append(
            EncodedAdapterShard(
                parameter_name=name,
                normalized_values=normalized,
                q_values=q_values,
                envelope=envelope,
                encoded_shard_id=leaf_id(envelope),
            )
        )
    return AdapterContribution(
        actual_optimizer_steps=actual_optimizer_steps,
        ordered_shards=tuple(shards),
        commitment_root=merkle_root([item.encoded_shard_id for item in shards]),
    )
