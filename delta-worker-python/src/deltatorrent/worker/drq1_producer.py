"""Canonical DRQ1 producer adapter for Delta worker contributions.

Converts normalized FP32 model updates (from NormalizedContributionCandidate / safetensors)
into canonical Feature 004 DRQ1 binary envelopes with exact 14-field ShardHeader,
signed INT16 payloads, leaf IDs, and commitment Merkle roots.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Final

import numpy as np
from safetensors.numpy import load_file as load_safetensors_np

from deltatorrent.domain.updates import NormalizedContributionCandidate
from deltatorrent.reference.fixedpoint_encoder import (
    FORMAL_SEMANTICS_ID,
    Rational,
    encode_envelope,
    encode_payload,
    leaf_id,
    merkle_root,
    quantize,
)

DEFAULT_PROFILE_ID: Final = (
    "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"
)


class DRQ1ProducerError(ValueError):
    """Stable failure during DRQ1 shard generation."""


def _float_to_rational(value: float) -> Rational:
    """Convert FP32/float value to reduced Rational with bounded denominator."""
    if not np.isfinite(value):
        raise DRQ1ProducerError("NON_FINITE_TENSOR_VALUE")
    # Limit denominator to avoid intermediate product overflow during quantization
    frac = Fraction(float(value)).limit_denominator(10_000_000)
    return Rational(numerator=frac.numerator, denominator=frac.denominator)


@dataclass(frozen=True, slots=True)
class ProducedShard:
    ordinal: int
    segment_id: str
    segment_offset: int
    element_start: int
    element_count: int
    header: dict[str, object]
    payload: bytes
    envelope: bytes
    leaf_id: str
    q_values: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ProducedShardSet:
    ticket_id: str
    shards: tuple[ProducedShard, ...]
    commitment_root: str
    total_elements: int
    total_payload_bytes: int

    def shard_by_ordinal(self, ordinal: int) -> ProducedShard:
        for shard in self.shards:
            if shard.ordinal == ordinal:
                return shard
        raise DRQ1ProducerError(f"SHARD_ORDINAL_NOT_FOUND: {ordinal}")


def produce_drq1_shards(
    *,
    candidate: NormalizedContributionCandidate,
    tensors: Mapping[str, np.ndarray] | None = None,
    safetensors_path: Path | str | None = None,
    scale_table: Mapping[str, object],
    shard_plan: Mapping[str, object],
    proof_instance_id: str,
    round_config_id: str,
    profile_id: str = DEFAULT_PROFILE_ID,
    formal_semantics_id: str = FORMAL_SEMANTICS_ID,
) -> ProducedShardSet:
    """Produces canonical Feature 004 DRQ1 shards from normalized candidate and tensors.

    Args:
        candidate: NormalizedContributionCandidate containing lineage metadata.
        tensors: Optional in-memory mapping of parameter names to float numpy arrays.
        safetensors_path: Optional path to a safetensors file.
        scale_table: Dict representing QUANTIZATION_SCALE_TABLE with segment rational quanta.
        shard_plan: Dict representing SHARD_PLAN with partition entries.
        proof_instance_id: Static AccumulatorProofInstance content ID.
        round_config_id: Content ID of the round configuration.
        profile_id: Content ID of the fixed-point profile.
        formal_semantics_id: Verified formal semantics content ID.

    Returns:
        ProducedShardSet containing ordered shards and commitment root.
    """
    if tensors is None:
        if safetensors_path is None:
            raise DRQ1ProducerError("TENSORS_OR_SAFETENSORS_PATH_REQUIRED")
        path = Path(safetensors_path)
        if not path.is_file():
            raise DRQ1ProducerError(f"SAFETENSORS_FILE_NOT_FOUND: {path}")
        tensors = load_safetensors_np(str(path))

    # 1. Verify and extract tensors according to candidate.tensor_order
    for name in candidate.tensor_order:
        if name not in tensors:
            raise DRQ1ProducerError(f"MISSING_REQUIRED_TENSOR: {name}")

    flattened_parts: list[np.ndarray] = []
    for name in candidate.tensor_order:
        tensor = tensors[name]
        flattened_parts.append(np.asarray(tensor, dtype=np.float32).reshape(-1))

    if flattened_parts:
        full_vector = np.concatenate(flattened_parts)
    else:
        full_vector = np.empty(0, dtype=np.float32)
    total_elements = len(full_vector)

    # 2. Parse scale table segments
    segments = scale_table.get("segments")
    if not isinstance(segments, Sequence) or not segments:
        raise DRQ1ProducerError("INVALID_SCALE_TABLE_SEGMENTS")

    segment_quantums: list[tuple[int, int, Rational]] = []  # (start, end, quantum)
    cursor = 0
    for seg in segments:
        count = int(seg["element_count"])
        q_dict = seg["quantum"]
        quantum = Rational(
            numerator=int(str(q_dict["numerator"])),
            denominator=int(q_dict["denominator"]),
        )
        segment_quantums.append((cursor, cursor + count, quantum))
        cursor += count

    if cursor != total_elements:
        raise DRQ1ProducerError(
            f"SCALE_TABLE_ELEMENTS_MISMATCH: scale table has {cursor}, vector has {total_elements}"
        )

    # 3. Quantize full vector into INT16
    quantized_values: list[int] = []
    for seg_start, seg_end, quantum in segment_quantums:
        for idx in range(seg_start, seg_end):
            val = float(full_vector[idx])
            q_val = quantize(_float_to_rational(val), quantum)
            quantized_values.append(q_val)

    # 4. Partition according to shard_plan entries
    entries = shard_plan.get("entries")
    if not isinstance(entries, Sequence) or not entries:
        raise DRQ1ProducerError("INVALID_SHARD_PLAN_ENTRIES")

    scale_table_id = str(scale_table.get("content_id", ""))
    if not scale_table_id:
        st_json = json.dumps(scale_table, sort_keys=True).encode("ascii")
        st_digest = hashlib.sha256(b"deltareduce.004.scale-table.v1\0" + st_json).hexdigest()
        scale_table_id = f"sha256:{st_digest}"

    shard_plan_id = str(shard_plan.get("content_id", ""))
    if not shard_plan_id:
        sp_json = json.dumps(shard_plan, sort_keys=True).encode("ascii")
        sp_digest = hashlib.sha256(b"deltareduce.004.shard-plan.v1\0" + sp_json).hexdigest()
        shard_plan_id = f"sha256:{sp_digest}"

    shards: list[ProducedShard] = []
    leaf_ids: list[str] = []
    total_payload_bytes = 0

    for entry in entries:
        ordinal = int(entry["ordinal"])
        seg_id = str(entry["segment_id"])
        seg_offset = int(entry["segment_offset"])
        el_start = int(entry["element_start"])
        el_count = int(entry["element_count"])

        if el_start + el_count > len(quantized_values):
            raise DRQ1ProducerError(
                f"SHARD_PLAN_BOUNDS_EXCEEDED: entry {ordinal} requests {el_start + el_count}, "
                f"total {len(quantized_values)}"
            )

        q_slice = tuple(quantized_values[el_start : el_start + el_count])
        payload = encode_payload(q_slice)
        payload_hash = f"sha256:{hashlib.sha256(payload).hexdigest()}"

        header: dict[str, object] = {
            "element_count": el_count,
            "element_start": el_start,
            "formal_semantics_id": formal_semantics_id,
            "ordinal": ordinal,
            "parameter_schema_id": candidate.parameter_schema_id,
            "payload_sha256": payload_hash,
            "profile_id": profile_id,
            "proof_instance_id": proof_instance_id,
            "round_config_id": round_config_id,
            "scale_table_id": scale_table_id,
            "schema_version": "1.0.0",
            "segment_id": seg_id,
            "segment_offset": seg_offset,
            "shard_plan_id": shard_plan_id,
            "ticket_id": candidate.ticket_id,
            "type_name": "ENCODED_INT16_SHARD",
        }

        envelope = encode_envelope(header, payload)
        current_leaf = leaf_id(envelope)
        leaf_ids.append(current_leaf)
        total_payload_bytes += len(payload)

        shards.append(
            ProducedShard(
                ordinal=ordinal,
                segment_id=seg_id,
                segment_offset=seg_offset,
                element_start=el_start,
                element_count=el_count,
                header=header,
                payload=payload,
                envelope=envelope,
                leaf_id=current_leaf,
                q_values=q_slice,
            )
        )

    commitment_root = merkle_root(leaf_ids)

    return ProducedShardSet(
        ticket_id=candidate.ticket_id,
        shards=tuple(shards),
        commitment_root=commitment_root,
        total_elements=total_elements,
        total_payload_bytes=total_payload_bytes,
    )
