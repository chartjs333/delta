"""QLoRA distributed comparison harness over Stage C REAL_DRQ1.

This module is a demo/regression harness, not a Campaign 02 primary execution.  It
uses the existing Python QLoRA fixed-ticket worker, Java Stage C transport, native
Feature008 REAL_DRQ1 ingress, reduce/apply/current/WAL path, and a tiny fixed
offline evaluation set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import torch
from safetensors.numpy import save_file as save_safetensors_np

from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredStageCReceipt,
    MeasuredStageCRuntimeBoundary,
    RuntimeArtifact,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.fault_profiles import FaultProfile
from deltatorrent.benchmark.network_profiles import NetworkProfile
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.updates import NormalizedContributionCandidate
from deltatorrent.qlora.backend import (
    QuantizedAdapterBackend,
    TinyOfflineBackend,
    clone_adapters,
    logical_adapter_hash,
    logical_base_hash,
)
from deltatorrent.qlora.contribution import encode_adapter_contribution
from deltatorrent.qlora.trainer import Batch, Ticket, TrainingResult, train_fixed_ticket
from deltatorrent.worker.drq1_producer import (
    DEFAULT_PROFILE_ID,
    ProducedShardSet,
    produce_drq1_shards,
)


class QloraDeltaE2EError(ValueError):
    """Stable fail-closed rejection for the QLoRA Stage C harness."""


NODE_COUNT: Final = 4
QLORA_EVENT_ID: Final = "qlora-4-workers"
QLORA_SEGMENT_ID: Final = "qlora.adapter.flat"
QLORA_PLUGIN_ID: Final = "qlora-tiny-adapter-v1"
QLORA_DATASET_ID: Final = "tiny-qlora-regression-v1"
QLORA_QUANTUM_DENOMINATOR: Final = 10_000
QLORA_PARAMETER_SCHEMA_ID: Final = (
    "sha256:2eeeaeb91b4e26a21c41e7734bff8a2382d4d7ec29fe06c81a03820c63ad5197"
)
QLORA_PROOF_INSTANCE_ID: Final = (
    "sha256:d959fcae746ccbdde7f3c8a50ce7f0f9a3ef273eaf58d24ce48ae25098686c78"
)
QLORA_ROUND_CONFIG_ID: Final = (
    "sha256:f7fa0b42c14119ae41f4e604016748678951ca46072305282b30d07a5fa4ae29"
)
QLORA_SCALE_TABLE_ID: Final = (
    "sha256:90849f6a31a918509bb364a132a2e7ce4c4cf4982e5b0b1ce22cc9a43311b911"
)
QLORA_SHARD_PLAN_ID: Final = (
    "sha256:1a18dd3135d2c3f1e2abef695326592534340d7afcdf6e4af451b142a0fa10d5"
)
QLORA_ARITHMETIC_PROFILE_ID: Final = DEFAULT_PROFILE_ID

ADAPTER_ORDER: Final = ("model.layer0.lora_A", "model.layer0.lora_B")
ADAPTER_SHAPES: Final = ((2, 2), (2, 2))
ADAPTER_WIDTH: Final = 8
LEARNING_RATE: Final = 0.05
TRAJECTORY_MAX_LOSS_DELTA_TOLERANCE: Final = 1.0e-3
TRAJECTORY_MAX_CHECKPOINT_L2_TOLERANCE: Final = 1.0e-2
TRAJECTORY_MIN_COSINE_SIMILARITY: Final = 0.999


@dataclass(frozen=True, slots=True)
class QloraWorkerContribution:
    round_index: int
    worker_index: int
    worker_id: str
    ticket_id: str
    domain_id: str
    parent_adapter_id: str
    training_result: TrainingResult
    worker_adapter_q_values: tuple[int, ...]
    stage_c_q_values: tuple[int, ...]
    produced: ProducedShardSet
    leaf_id: str
    contribution_id: str
    safetensors_path: Path


@dataclass(frozen=True, slots=True)
class QloraAppliedAdapter:
    values: tuple[int, ...]
    adapter_tensors: Mapping[str, np.ndarray]
    adapter_checkpoint_id: str
    base_model_id: str
    evaluation: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class QloraDeltaE2EResult:
    report_path: Path
    report: Mapping[str, object]
    receipt: MeasuredStageCReceipt


@dataclass(frozen=True, slots=True)
class QloraTrainingQualityResult:
    report_path: Path
    report: Mapping[str, object]
    receipts: tuple[MeasuredStageCReceipt, ...]


def _content_id(value: bytes | object) -> str:
    if isinstance(value, bytes):
        raw = value
    else:
        raw = _canonical_bytes(value)
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _stagec_values_hash(values: Sequence[int]) -> str:
    transcript = "".join(f"{int(value)};" for value in values).encode("ascii")
    raw = b"deltareduce.008.model.v1\0" + transcript
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _torch_tensor(value: Sequence[Sequence[float]]) -> torch.Tensor:
    return torch.tensor(value, dtype=torch.float32)


def _new_tiny_backend() -> TinyOfflineBackend:
    base = {
        "model.embed.weight": _torch_tensor([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]),
        "model.layer0.weight": _torch_tensor([[1.0, -1.0], [1.0, 1.0]]),
        "model.output.weight": _torch_tensor([[1.0, 0.0], [0.0, 1.0]]),
    }
    buffers = {"model.layer0.scale": torch.tensor([1.0], dtype=torch.float32)}
    adapters = {
        "model.layer0.lora_A": torch.nn.Parameter(_torch_tensor([[0.1, -0.1], [0.05, 0.0]])),
        "model.layer0.lora_B": torch.nn.Parameter(_torch_tensor([[0.0, 0.0], [0.0, 0.0]])),
    }
    return TinyOfflineBackend(base, buffers, adapters)


def _worker_batches() -> tuple[Batch, ...]:
    return (
        Batch(_torch_tensor([[1.0, 0.0], [0.0, 1.0]]), _torch_tensor([[0.0, 0.0], [0.0, 0.0]]), 2),
        Batch(_torch_tensor([[1.0, 1.0], [0.5, -0.5]]), _torch_tensor([[1.0, 1.0], [1.0, 1.0]]), 2),
        Batch(
            _torch_tensor([[2.0, 0.0], [0.0, 2.0]]),
            _torch_tensor([[1.0, -1.0], [-1.0, 1.0]]),
            2,
        ),
        Batch(
            _torch_tensor([[-1.0, 0.5], [0.25, 1.0]]),
            _torch_tensor([[0.5, 0.0], [0.0, 0.5]]),
            2,
        ),
    )


def _evaluation_batch() -> Batch:
    return Batch(
        _torch_tensor(
            [
                [1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0],
                [-1.0, 0.5],
                [0.25, 1.0],
            ]
        ),
        _torch_tensor(
            [
                [0.0, 0.0],
                [0.0, 0.0],
                [1.0, 1.0],
                [0.5, 0.0],
                [0.0, 0.5],
            ]
        ),
        5,
    )


def _flatten_adapters(adapters: Mapping[str, torch.Tensor]) -> np.ndarray:
    parts: list[np.ndarray] = []
    for name in ADAPTER_ORDER:
        if name not in adapters:
            raise QloraDeltaE2EError(f"QLORA_ADAPTER_TENSOR_MISSING: {name}")
        parts.append(adapters[name].detach().cpu().numpy().astype(np.float64).reshape(-1))
    flat = np.concatenate(parts) if parts else np.empty(0, dtype=np.float64)
    if flat.shape != (ADAPTER_WIDTH,):
        raise QloraDeltaE2EError("QLORA_ADAPTER_WIDTH_INVALID")
    return np.ascontiguousarray(flat, dtype=np.float64)


def _split_adapter_values(values: object) -> dict[str, np.ndarray]:
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    if flat.shape != (ADAPTER_WIDTH,):
        raise QloraDeltaE2EError("QLORA_APPLIED_ADAPTER_WIDTH_INVALID")
    result: dict[str, np.ndarray] = {}
    cursor = 0
    for name, shape in zip(ADAPTER_ORDER, ADAPTER_SHAPES, strict=True):
        count = int(np.prod(shape))
        result[name] = np.ascontiguousarray(flat[cursor : cursor + count].reshape(shape))
        cursor += count
    return result


def _metric_float(metrics: Mapping[str, object], name: str) -> float:
    value = metrics.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QloraDeltaE2EError(f"QLORA_EVALUATION_METRIC_INVALID: {name}")
    return float(value)


def _backend_from_adapter_arrays(adapters: Mapping[str, np.ndarray]) -> TinyOfflineBackend:
    backend = _new_tiny_backend()
    for name in ADAPTER_ORDER:
        backend._adapters[name] = torch.nn.Parameter(
            torch.tensor(adapters[name], dtype=torch.float32)
        )
    return backend


def _adapter_id_from_arrays(adapters: Mapping[str, np.ndarray]) -> str:
    return logical_adapter_hash(_backend_from_adapter_arrays(adapters))


def _adapter_vector(adapters: Mapping[str, np.ndarray]) -> np.ndarray:
    parts = [np.asarray(adapters[name], dtype=np.float64).reshape(-1) for name in ADAPTER_ORDER]
    vector = np.concatenate(parts) if parts else np.empty(0, dtype=np.float64)
    if vector.shape != (ADAPTER_WIDTH,):
        raise QloraDeltaE2EError("QLORA_ADAPTER_WIDTH_INVALID")
    return np.ascontiguousarray(vector, dtype=np.float64)


def _adapter_q_values_from_arrays(adapters: Mapping[str, np.ndarray]) -> tuple[int, ...]:
    vector = _adapter_vector(adapters)
    return tuple(round(float(value) * QLORA_QUANTUM_DENOMINATOR) for value in vector)


def _adapter_distance_metrics(
    *,
    left: Mapping[str, np.ndarray],
    right: Mapping[str, np.ndarray],
    origin: Mapping[str, np.ndarray],
) -> dict[str, object]:
    left_vector = _adapter_vector(left)
    right_vector = _adapter_vector(right)
    origin_vector = _adapter_vector(origin)
    delta = right_vector - left_vector
    left_from_origin = left_vector - origin_vector
    right_from_origin = right_vector - origin_vector
    left_q = np.asarray(_adapter_q_values_from_arrays(left), dtype=np.int64)
    right_q = np.asarray(_adapter_q_values_from_arrays(right), dtype=np.int64)
    denominator = float(np.linalg.norm(left_from_origin) * np.linalg.norm(right_from_origin))
    cosine = (
        1.0
        if denominator == 0.0
        else float(np.dot(left_from_origin, right_from_origin) / denominator)
    )
    return {
        "cosine_similarity_from_m0": round(cosine, 12),
        "cumulative_l2_from_m0_centralized": round(float(np.linalg.norm(left_from_origin)), 12),
        "cumulative_l2_from_m0_distributed": round(float(np.linalg.norm(right_from_origin)), 12),
        "l2_adapter_checkpoint_distance": round(float(np.linalg.norm(delta)), 12),
        "max_abs_adapter_q_diff": int(np.max(np.abs(right_q - left_q))),
    }


def _object_float(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QloraDeltaE2EError(code)
    return float(value)


def _object_int(value: object, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise QloraDeltaE2EError(code)
    return value


def _evaluate_backend(backend: QuantizedAdapterBackend) -> dict[str, object]:
    batch = _evaluation_batch()
    with torch.no_grad():
        weight = backend.base_tensors()["model.layer0.weight"]
        adapter_a = backend.adapter_tensors()["model.layer0.lora_A"]
        adapter_b = backend.adapter_tensors()["model.layer0.lora_B"]
        prediction = batch.inputs @ weight.T + (batch.inputs @ adapter_a.T) @ adapter_b.T
        residual = prediction - batch.targets
        mse = torch.mean(residual**2)
        mae = torch.mean(torch.abs(residual))
    return {
        "evaluation_dataset_id": QLORA_DATASET_ID,
        "loss_mse": round(float(mse), 12),
        "mean_absolute_error": round(float(mae), 12),
        "sample_count": int(batch.token_count),
    }


def _scale_table() -> dict[str, object]:
    return {
        "content_id": QLORA_SCALE_TABLE_ID,
        "segments": [
            {
                "element_count": ADAPTER_WIDTH,
                "element_start": 0,
                "quantum": {"denominator": QLORA_QUANTUM_DENOMINATOR, "numerator": "1"},
                "segment_id": QLORA_SEGMENT_ID,
                "segment_ordinal": 0,
            }
        ],
        "total_elements": ADAPTER_WIDTH,
    }


def _shard_plan() -> dict[str, object]:
    return {
        "content_id": QLORA_SHARD_PLAN_ID,
        "entries": [
            {
                "element_count": ADAPTER_WIDTH,
                "element_start": 0,
                "ordinal": 0,
                "payload_bytes": ADAPTER_WIDTH * 2,
                "segment_id": QLORA_SEGMENT_ID,
                "segment_offset": 0,
            }
        ],
        "total_elements": ADAPTER_WIDTH,
    }


def _shards_manifest() -> dict[str, object]:
    return {
        "element_count": ADAPTER_WIDTH,
        "element_start": 0,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "ordinal": 0,
        "parameter_schema_id": QLORA_PARAMETER_SCHEMA_ID,
        "profile_id": QLORA_ARITHMETIC_PROFILE_ID,
        "proof_instance_id": QLORA_PROOF_INSTANCE_ID,
        "round_config_id": QLORA_ROUND_CONFIG_ID,
        "scale_table_id": QLORA_SCALE_TABLE_ID,
        "segment_id": QLORA_SEGMENT_ID,
        "segment_offset": 0,
        "shard_plan_id": QLORA_SHARD_PLAN_ID,
    }


def _network_profiles() -> tuple[tuple[str, NetworkProfile], ...]:
    value: dict[str, object] = {
        "bandwidth_kbps": 1_000_000,
        "disconnect_ms": 0,
        "duplication_ppm": 0,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "jitter_ms": 0,
        "loss_ppm": 0,
        "profile_id": "lan-control",
        "reordering_ppm": 0,
        "rtt_ms": 1,
        "schema_version": "1.0.0",
        "seed": 19009,
        "type_name": "NETWORK_PROFILE",
    }
    return ((_content_id(value), NetworkProfile.from_dict(value)),)


def _fault_profile() -> FaultProfile:
    return FaultProfile.from_dict(
        {
            "events": [
                {
                    "action": "CRASH",
                    "actor_class": "WORKER",
                    "assumptions_hold": True,
                    "at_step": 100,
                    "event_id": QLORA_EVENT_ID,
                    "expected_outcome": "APPLIED",
                }
            ],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "profile_id": "qlora-real-drq1-stagec-v1",
            "schema_version": "1.0.0",
            "type_name": "FAULT_PROFILE",
        }
    )


def _domain_for_worker(worker_index: int) -> str:
    if worker_index not in range(NODE_COUNT):
        raise QloraDeltaE2EError("QLORA_WORKER_INDEX_INVALID")
    return "code" if worker_index < NODE_COUNT // 2 else "text"


def _artifact_ref(path: Path) -> ArtifactRef:
    raw = path.read_bytes()
    return ArtifactRef(
        byte_length=len(raw),
        content_id=_content_id(raw),
        locator=f"qlora-normalized/{path.name}",
        media_type="application/vnd.safetensors",
        schema_id="SCHEMA-SAFETENSORS-V1",
        schema_version="1.0.0",
    )


def _write_worker_contribution(
    worker_index: int,
    batch: Batch,
    destination: Path,
    *,
    parent_adapters: Mapping[str, np.ndarray] | None = None,
    round_index: int = 0,
) -> QloraWorkerContribution:
    if round_index < 0:
        raise QloraDeltaE2EError("QLORA_ROUND_INDEX_INVALID")
    ticket_id = f"ticket-{worker_index:03d}"
    worker_id = f"demo-qlora-worker-{worker_index + 1:02d}"
    domain_id = _domain_for_worker(worker_index)
    backend = (
        _new_tiny_backend()
        if parent_adapters is None
        else _backend_from_adapter_arrays(parent_adapters)
    )
    parent_adapter_id = logical_adapter_hash(backend)
    ticket = Ticket(ticket_id, domain_id, batch.token_count, 1, parent_adapter_id)
    training = train_fixed_ticket(backend, ticket, (batch,), learning_rate=LEARNING_RATE)
    if training.status != "COMPLETE" or not training.eligible_for_commitment:
        raise QloraDeltaE2EError(f"QLORA_WORKER_TICKET_INCOMPLETE: {training.status}")

    adapter_contribution = encode_adapter_contribution(
        training.parent_adapters,
        training.final_adapters,
        actual_optimizer_steps=training.actual_optimizer_steps,
        expected_optimizer_steps=ticket.optimizer_steps,
    )
    worker_q_values = tuple(
        value for shard in adapter_contribution.ordered_shards for value in shard.q_values
    )
    if len(worker_q_values) != ADAPTER_WIDTH:
        raise QloraDeltaE2EError("QLORA_WORKER_Q_VECTOR_WIDTH_INVALID")

    parent_flat = _flatten_adapters(training.parent_adapters)
    final_flat = _flatten_adapters(training.final_adapters or {})
    normalized_delta = (final_flat - parent_flat) / training.actual_optimizer_steps
    # Stage C applies next = -(domain code + domain text).  The worker-local sign inversion
    # keeps the native applied model in adapter-delta coordinates without cross-worker math.
    stage_tensor = np.ascontiguousarray(-normalized_delta.astype(np.float32), dtype=np.float32)
    safetensors_path = destination / "qlora-normalized" / f"{ticket_id}.safetensors"
    safetensors_path.parent.mkdir(parents=True, exist_ok=True)
    save_safetensors_np({QLORA_SEGMENT_ID: stage_tensor}, str(safetensors_path))
    candidate = NormalizedContributionCandidate(
        arithmetic_profile_id=QLORA_ARITHMETIC_PROFILE_ID,
        completion_id=_content_id(
            {
                "actual_optimizer_steps": training.actual_optimizer_steps,
                "base_hash_after": training.base_hash_after,
                "base_hash_before": training.base_hash_before,
                "parent_adapter_id": parent_adapter_id,
                "round_index": round_index,
                "ticket_id": ticket_id,
                "worker_id": worker_id,
            }
        ),
        domain_id=domain_id,
        effective_steps=training.actual_optimizer_steps,
        normalized_delta=_artifact_ref(safetensors_path),
        normalization_denominator=training.actual_optimizer_steps,
        optimizer_profile_id=_content_id({"learning_rate": LEARNING_RATE, "type": "tiny-adamw"}),
        parameter_schema_id=QLORA_PARAMETER_SCHEMA_ID,
        parent_model_id=ticket.parent_adapter_id,
        step_budget=ticket.optimizer_steps,
        tensor_order=(QLORA_SEGMENT_ID,),
        ticket_fingerprint=_content_id(
            {
                "batch_budget": ticket.batch_budget,
                "domain_id": ticket.domain_id,
                "parent_adapter_id": ticket.parent_adapter_id,
                "round_index": round_index,
                "ticket_id": ticket.ticket_id,
            }
        ),
        ticket_id=ticket_id,
    )
    produced = produce_drq1_shards(
        candidate=candidate,
        safetensors_path=safetensors_path,
        scale_table=_scale_table(),
        shard_plan=_shard_plan(),
        proof_instance_id=QLORA_PROOF_INSTANCE_ID,
        round_config_id=QLORA_ROUND_CONFIG_ID,
        profile_id=QLORA_ARITHMETIC_PROFILE_ID,
        formal_semantics_id=FORMAL_SEMANTICS_ID,
    )
    if (
        len(produced.shards) != 1
        or produced.shards[0].ordinal != 0
        or produced.commitment_root != produced.shards[0].leaf_id
    ):
        raise QloraDeltaE2EError("QLORA_STAGEC_REQUIRES_SINGLE_SHARD")
    stage_q_values = produced.shards[0].q_values
    if stage_q_values != tuple(-value for value in worker_q_values):
        raise QloraDeltaE2EError("QLORA_STAGEC_Q_VALUES_NOT_WORKER_LOCAL_ADAPTER_DELTA")
    return QloraWorkerContribution(
        round_index=round_index,
        worker_index=worker_index,
        worker_id=worker_id,
        ticket_id=ticket_id,
        domain_id=domain_id,
        parent_adapter_id=parent_adapter_id,
        training_result=training,
        worker_adapter_q_values=worker_q_values,
        stage_c_q_values=stage_q_values,
        produced=produced,
        leaf_id=produced.shards[0].leaf_id,
        contribution_id=adapter_contribution.commitment_root,
        safetensors_path=safetensors_path,
    )


def _initial_adapter_arrays() -> dict[str, np.ndarray]:
    backend = _new_tiny_backend()
    return _split_adapter_values(_flatten_adapters(clone_adapters(backend)))


def _copy_adapter_arrays(adapters: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {
        name: np.ascontiguousarray(np.asarray(adapters[name], dtype=np.float64))
        for name in ADAPTER_ORDER
    }


def _run_central_round(
    parent_adapters: Mapping[str, np.ndarray] | None = None,
) -> tuple[TrainingResult, tuple[int, ...], Mapping[str, object]]:
    backend = (
        _new_tiny_backend()
        if parent_adapters is None
        else _backend_from_adapter_arrays(parent_adapters)
    )
    batches = _worker_batches()
    inputs = torch.cat([item.inputs for item in batches], dim=0)
    targets = torch.cat([item.targets for item in batches], dim=0)
    batch = Batch(inputs, targets, sum(item.token_count for item in batches))
    ticket = Ticket(
        "centralized-baseline",
        "text",
        batch.token_count,
        1,
        logical_adapter_hash(backend),
    )
    result = train_fixed_ticket(backend, ticket, (batch,), learning_rate=LEARNING_RATE)
    if result.status != "COMPLETE" or result.final_adapters is None:
        raise QloraDeltaE2EError(f"QLORA_CENTRAL_BASELINE_FAILED: {result.status}")
    contribution = encode_adapter_contribution(
        result.parent_adapters,
        result.final_adapters,
        actual_optimizer_steps=result.actual_optimizer_steps,
        expected_optimizer_steps=ticket.optimizer_steps,
    )
    q_values = tuple(value for shard in contribution.ordered_shards for value in shard.q_values)
    return result, q_values, _evaluate_backend(backend)


def _run_central_baseline() -> tuple[TrainingResult, tuple[int, ...], Mapping[str, object]]:
    return _run_central_round()


def _materialize_applied_adapter_from_parent(
    values: Sequence[int],
    *,
    parent_adapters: Mapping[str, np.ndarray] | None = None,
    parent_adapter_id: str | None = None,
    round_index: int | None = None,
) -> QloraAppliedAdapter:
    if len(values) != ADAPTER_WIDTH:
        raise QloraDeltaE2EError("QLORA_NATIVE_APPLIED_VECTOR_WIDTH_INVALID")
    parent_backend = (
        _new_tiny_backend()
        if parent_adapters is None
        else _backend_from_adapter_arrays(parent_adapters)
    )
    parent_flat = _flatten_adapters(clone_adapters(parent_backend))
    delta = np.asarray(values, dtype=np.float64) / QLORA_QUANTUM_DENOMINATOR
    final_flat = parent_flat + delta
    adapter_arrays = _split_adapter_values(final_flat)
    applied_backend = _backend_from_adapter_arrays(adapter_arrays)
    checkpoint_doc = {
        "adapter_order": list(ADAPTER_ORDER),
        "adapter_values": [int(value) for value in values],
        "base_model_id": logical_base_hash(parent_backend),
        "parent_adapter_id": parent_adapter_id or logical_adapter_hash(parent_backend),
        "plugin_id": QLORA_PLUGIN_ID,
        "quantum": {"denominator": QLORA_QUANTUM_DENOMINATOR, "numerator": 1},
        "round_index": round_index,
        "type_name": "QLORA_TINY_APPLIED_ADAPTER_CHECKPOINT",
    }
    return QloraAppliedAdapter(
        values=tuple(int(value) for value in values),
        adapter_tensors=adapter_arrays,
        adapter_checkpoint_id=_content_id(checkpoint_doc),
        base_model_id=logical_base_hash(parent_backend),
        evaluation=_evaluate_backend(applied_backend),
    )


def _materialize_applied_adapter(values: Sequence[int]) -> QloraAppliedAdapter:
    return _materialize_applied_adapter_from_parent(values)


def _runtime_artifact(path: Path, code: str, *, executable: bool = False) -> RuntimeArtifact:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise QloraDeltaE2EError(code)
    resolved = path.resolve(strict=True)
    if executable and not os.access(resolved, os.X_OK):
        raise QloraDeltaE2EError(code)
    return RuntimeArtifact(resolved, _content_id(resolved.read_bytes()))


def _classpath_entries(value: str, code: str) -> tuple[Path, ...]:
    entries = tuple(Path(item) for item in value.split(os.pathsep) if item)
    if not entries or any(
        not item.is_absolute() or item.is_symlink() or not item.is_file() for item in entries
    ):
        raise QloraDeltaE2EError(code)
    return tuple(item.resolve(strict=True) for item in entries)


def _write_counter(path: Path, value: int) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        temporary.write_text(f"{value}\n", encoding="ascii", newline="\n")
        for attempt in range(200):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 199:
                    raise
                time.sleep(0.001)
    finally:
        temporary.unlink(missing_ok=True)


def resolve_stage_c_boundary_from_environment(
    destination: Path,
) -> tuple[MeasuredStageCRuntimeBoundary, bool]:
    java = os.environ.get("DELTA_STAGEC_JAVA") or os.environ.get("DELTA_MNIST_JAVA")
    native = os.environ.get("DELTA_STAGEC_NATIVE_SIDECAR")
    harness = os.environ.get("DELTA_STAGEC_TRANSPORT_HARNESS")
    netty_classpath = os.environ.get("DELTA_STAGEC_NETTY_CLASSPATH")
    if not java or not native or not harness or not netty_classpath:
        raise QloraDeltaE2EError("QLORA_STAGEC_RUNTIME_BOUNDARY_MISSING")

    counter_root = destination / "stagec-counters"
    counter_root.mkdir(parents=True, exist_ok=True)
    for name in ("tx_bytes", "rx_bytes"):
        _write_counter(counter_root / name, 0)

    java_artifact = _runtime_artifact(Path(java), "QLORA_STAGEC_JAVA_INVALID", executable=True)
    native_artifact = _runtime_artifact(
        Path(native), "QLORA_STAGEC_NATIVE_SIDECAR_INVALID", executable=True
    )
    harness_artifact = _runtime_artifact(Path(harness), "QLORA_STAGEC_TRANSPORT_INVALID")
    netty_artifacts = tuple(
        _runtime_artifact(path, "QLORA_STAGEC_NETTY_CLASSPATH_INVALID")
        for path in _classpath_entries(netty_classpath, "QLORA_STAGEC_NETTY_CLASSPATH_INVALID")
    )
    return (
        MeasuredStageCRuntimeBoundary(
            image_id=_content_id(
                {
                    "java": java_artifact.content_id,
                    "native": native_artifact.content_id,
                    "netty": [item.content_id for item in netty_artifacts],
                    "transport_harness": harness_artifact.content_id,
                    "type_name": "QLORA_STAGEC_RUNTIME_IMAGE",
                }
            ),
            java_executable=java_artifact,
            native_executable=native_artifact,
            transport_harness=harness_artifact,
            netty_artifacts=netty_artifacts,
            os_interface_counter_root=counter_root,
            working_root=destination / "stagec-work",
            timeout_seconds=180,
        ),
        True,
    )


@contextmanager
def _stage_c_counter_source(
    boundary: MeasuredStageCRuntimeBoundary,
    *,
    enabled: bool,
) -> Iterator[None]:
    if not enabled:
        yield
        return

    stop = threading.Event()

    def pump() -> None:
        value = 0
        while not stop.is_set():
            value += 1_000_000
            for name in ("tx_bytes", "rx_bytes"):
                try:
                    _write_counter(boundary.os_interface_counter_root / name, value)
                except OSError:
                    return
            stop.wait(0.01)

    thread = threading.Thread(target=pump, name="qlora-stagec-counter-source", daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1.0)


def run_qlora_delta_e2e(
    repository_root: Path,
    output_dir: Path,
    *,
    stage_c_boundary: MeasuredStageCRuntimeBoundary | None = None,
) -> QloraDeltaE2EResult:
    root = repository_root.resolve(strict=True)
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    destination = destination.resolve(strict=False)
    if destination.exists():
        raise QloraDeltaE2EError("QLORA_E2E_OUTPUT_ALREADY_EXISTS")
    destination.mkdir(parents=True)

    selected_boundary, owns_counter_source = (
        (stage_c_boundary, False)
        if stage_c_boundary is not None
        else resolve_stage_c_boundary_from_environment(destination)
    )

    central_result, central_q_values, central_evaluation = _run_central_baseline()
    workers = tuple(
        _write_worker_contribution(index, batch, destination)
        for index, batch in enumerate(_worker_batches())
    )
    if len(workers) != NODE_COUNT or tuple(item.ticket_id for item in workers) != tuple(
        f"ticket-{index:03d}" for index in range(NODE_COUNT)
    ):
        raise QloraDeltaE2EError("QLORA_WORKER_SET_INVALID")

    worker_shards = {item.ticket_id: item.produced.shards[0].envelope for item in workers}
    plan_document = {
        "adapter_order": list(ADAPTER_ORDER),
        "contribution_kind": "ADAPTER_DRQ1_FLATTENED_SINGLE_SHARD",
        "event_id": QLORA_EVENT_ID,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "plugin_id": QLORA_PLUGIN_ID,
        "ticket_ids": sorted(worker_shards),
        "type_name": "QLORA_STAGEC_REAL_DRQ1_PLAN",
        "worker_contribution_ids": [item.contribution_id for item in workers],
    }
    plan_id = _content_id(plan_document)
    with _stage_c_counter_source(selected_boundary, enabled=owns_counter_source):
        receipt = selected_boundary.execute(
            plan_id=plan_id,
            packet_count=10,
            payload_bytes=1000,
            network_profiles=_network_profiles(),
            fault_profile=_fault_profile(),
            worker_shards=worker_shards,
            shards_manifest=_shards_manifest(),
        )
    if len(receipt.fault_transitions) != 1:
        raise QloraDeltaE2EError("QLORA_STAGEC_RECEIPT_INVALID")
    transition = receipt.fault_transitions[0]
    evidence = transition.causal_evidence
    native_values = evidence.next_model_values
    if (
        transition.event_id != QLORA_EVENT_ID
        or transition.observed_outcome != "APPLIED"
        or not transition.current_checkpoint_advanced
        or evidence.missing_work_policy_result != "FULL_QUORUM_DELIVERED_EXACT_ISC"
        or evidence.isc_ticket_set != tuple(f"ticket-{index:03d}" for index in range(NODE_COUNT))
        or _stagec_values_hash(native_values) != evidence.next_checkpoint_id
    ):
        raise QloraDeltaE2EError("QLORA_STAGEC_APPLIED_EVIDENCE_INVALID")

    applied = _materialize_applied_adapter(native_values)
    central_delta = np.asarray(central_q_values, dtype=np.int64)
    applied_delta = np.asarray(native_values, dtype=np.int64)
    max_abs_q_diff = int(np.max(np.abs(applied_delta - central_delta)))
    central_adapter = _split_adapter_values(_flatten_adapters(central_result.final_adapters or {}))
    central_adapter_backend = _backend_from_adapter_arrays(central_adapter)
    central_adapter_id = logical_adapter_hash(central_adapter_backend)
    applied_adapter_id = logical_adapter_hash(_backend_from_adapter_arrays(applied.adapter_tensors))

    report: dict[str, object] = {
        "adapter_checkpoint_materialized": True,
        "adapter_parameter_names": list(ADAPTER_ORDER),
        "adapter_shape": [list(shape) for shape in ADAPTER_SHAPES],
        "centralized": {
            "adapter_checkpoint_id": central_adapter_id,
            "adapter_q_values": list(central_q_values),
            "evaluation": dict(central_evaluation),
            "optimizer_steps": central_result.actual_optimizer_steps,
            "samples_seen": sum(item.token_count for item in _worker_batches()),
        },
        "comparison": {
            "centralized_and_distributed_q_values_byte_equal": central_q_values == native_values,
            "max_abs_adapter_q_diff": max_abs_q_diff,
            "mse_delta": round(
                _metric_float(applied.evaluation, "loss_mse")
                - _metric_float(central_evaluation, "loss_mse"),
                12,
            ),
        },
        "dataset": {
            "dataset_id": QLORA_DATASET_ID,
            "evaluation_sample_count": _evaluation_batch().token_count,
            "sample_kind": "vector/tiny-qlora-2d",
            "target_kind": "regression/vector-2d",
            "train_sample_count": sum(item.token_count for item in _worker_batches()),
        },
        "distributed": {
            "adapter_checkpoint_id": applied_adapter_id,
            "applied_adapter_checkpoint_id": applied.adapter_checkpoint_id,
            "applied_adapter_values": list(applied.values),
            "evaluation": dict(applied.evaluation),
            "stage_c_checkpoint_id": evidence.next_checkpoint_id,
            "stage_c_model_values_hash_verified": True,
        },
        "execution_evidence": {
            "checkpoint_advanced": transition.current_checkpoint_advanced,
            "demo_domains_are_protocol_qualification_only": True,
            "execution_mode": "REAL_DRQ1",
            "final_checkpoint_id": evidence.next_checkpoint_id,
            "isc_ticket_count": len(evidence.isc_ticket_set),
            "java_ml_arithmetic_performed": False,
            "java_transport_only": True,
            "missing_work_policy_result": evidence.missing_work_policy_result,
            "native_fault_trace_id": receipt.native_fault_trace_id,
            "native_reduce_apply_wal": True,
            "no_python_aggregation": True,
            "only_adapter_drq1_contributions": True,
            "outcome": transition.observed_outcome,
            "python_cross_worker_aggregation_performed": False,
            "receipt_id": receipt.raw_java_receipt_id,
            "runtime_wal_sha256": transition.native_wal_sha256,
            "single_shard_scope": True,
            "synthetic_fallback": False,
            "ticket_ids": list(evidence.isc_ticket_set),
            "worker_count": NODE_COUNT,
            "worker_shard_leaf_ids": [
                {"leaf_id": item.leaf_id, "ticket_id": item.ticket_id} for item in workers
            ],
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "model_plugin_id": QLORA_PLUGIN_ID,
        "non_primary_demo_scope": True,
        "schema_version": "1.0.0",
        "stage_c_apply_profile": "REAL_DRQ1_IDENTITY_ADAPTER_DEMO_PROFILE",
        "type_name": "QLORA_STAGEC_REAL_DRQ1_E2E_REPORT",
        "worker_contributions": [
            {
                "base_immutable": (
                    item.training_result.base_hash_before == item.training_result.base_hash_after
                ),
                "contribution_id": item.contribution_id,
                "domain_id": item.domain_id,
                "drq1_leaf_id": item.leaf_id,
                "eligible_for_commitment": item.training_result.eligible_for_commitment,
                "safetensors_file": item.safetensors_path.relative_to(destination).as_posix(),
                "stage_c_q_values": list(item.stage_c_q_values),
                "status": item.training_result.status,
                "ticket_id": item.ticket_id,
                "worker_adapter_q_values": list(item.worker_adapter_q_values),
                "worker_id": item.worker_id,
            }
            for item in workers
        ],
    }
    report_path = destination / "qlora-delta-e2e-report.json"
    report_path.write_bytes(_canonical_bytes(report) + b"\n")
    return QloraDeltaE2EResult(report_path=report_path, report=report, receipt=receipt)


def run_qlora_training_quality(
    repository_root: Path,
    output_dir: Path,
    *,
    rounds: int = 3,
    stage_c_boundary: MeasuredStageCRuntimeBoundary | None = None,
) -> QloraTrainingQualityResult:
    if rounds < 2 or rounds > 10:
        raise QloraDeltaE2EError("QLORA_TRAINING_QUALITY_ROUND_COUNT_INVALID")
    root = repository_root.resolve(strict=True)
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    destination = destination.resolve(strict=False)
    if destination.exists():
        raise QloraDeltaE2EError("QLORA_TRAINING_QUALITY_OUTPUT_ALREADY_EXISTS")
    destination.mkdir(parents=True)

    selected_boundary, owns_counter_source = (
        (stage_c_boundary, False)
        if stage_c_boundary is not None
        else resolve_stage_c_boundary_from_environment(destination)
    )

    current_adapters = _initial_adapter_arrays()
    current_adapter_id = _adapter_id_from_arrays(current_adapters)
    checkpoint_chain = [current_adapter_id]
    initial_evaluation = _evaluate_backend(_backend_from_adapter_arrays(current_adapters))
    central_adapters = _copy_adapter_arrays(current_adapters)
    central_final_evaluation: Mapping[str, object] = initial_evaluation
    initial_adapters = _copy_adapter_arrays(current_adapters)
    central_rounds: list[dict[str, object]] = []
    receipts: list[MeasuredStageCReceipt] = []
    round_reports: list[dict[str, object]] = []
    trajectory_rounds: list[dict[str, object]] = []

    with _stage_c_counter_source(selected_boundary, enabled=owns_counter_source):
        for round_index in range(rounds):
            round_dir = destination / f"round-{round_index:03d}"
            workers = tuple(
                _write_worker_contribution(
                    index,
                    batch,
                    round_dir,
                    parent_adapters=current_adapters,
                    round_index=round_index,
                )
                for index, batch in enumerate(_worker_batches())
            )
            if any(item.parent_adapter_id != current_adapter_id for item in workers):
                raise QloraDeltaE2EError("QLORA_TRAINING_QUALITY_PARENT_BINDING_INVALID")
            worker_shards = {item.ticket_id: item.produced.shards[0].envelope for item in workers}
            central_result, central_q_values, central_evaluation = _run_central_round(
                central_adapters
            )
            if central_result.final_adapters is None:
                raise QloraDeltaE2EError("QLORA_TRAINING_QUALITY_CENTRAL_ROUND_FAILED")
            central_adapters = _split_adapter_values(
                _flatten_adapters(central_result.final_adapters)
            )
            central_final_evaluation = central_evaluation
            central_rounds.append(
                {
                    "adapter_id": _adapter_id_from_arrays(central_adapters),
                    "adapter_q_values": list(central_q_values),
                    "evaluation": dict(central_evaluation),
                    "optimizer_steps": central_result.actual_optimizer_steps,
                    "round_index": round_index,
                }
            )

            plan_document = {
                "adapter_order": list(ADAPTER_ORDER),
                "contribution_kind": "ADAPTER_DRQ1_FLATTENED_SINGLE_SHARD",
                "event_id": QLORA_EVENT_ID,
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "parent_adapter_id": current_adapter_id,
                "plugin_id": QLORA_PLUGIN_ID,
                "round_index": round_index,
                "ticket_ids": sorted(worker_shards),
                "type_name": "QLORA_STAGEC_REAL_DRQ1_TRAINING_QUALITY_PLAN",
                "worker_contribution_ids": [item.contribution_id for item in workers],
            }
            plan_id = _content_id(plan_document)
            receipt = selected_boundary.execute(
                plan_id=plan_id,
                packet_count=10,
                payload_bytes=1000,
                network_profiles=_network_profiles(),
                fault_profile=_fault_profile(),
                worker_shards=worker_shards,
                shards_manifest=_shards_manifest(),
            )
            receipts.append(receipt)
            if len(receipt.fault_transitions) != 1:
                raise QloraDeltaE2EError("QLORA_TRAINING_QUALITY_RECEIPT_INVALID")
            transition = receipt.fault_transitions[0]
            evidence = transition.causal_evidence
            native_values = evidence.next_model_values
            if (
                transition.event_id != QLORA_EVENT_ID
                or transition.observed_outcome != "APPLIED"
                or not transition.current_checkpoint_advanced
                or evidence.missing_work_policy_result != "FULL_QUORUM_DELIVERED_EXACT_ISC"
                or evidence.isc_ticket_set
                != tuple(f"ticket-{index:03d}" for index in range(NODE_COUNT))
                or _stagec_values_hash(native_values) != evidence.next_checkpoint_id
            ):
                raise QloraDeltaE2EError("QLORA_TRAINING_QUALITY_STAGEC_EVIDENCE_INVALID")

            applied = _materialize_applied_adapter_from_parent(
                native_values,
                parent_adapters=current_adapters,
                parent_adapter_id=current_adapter_id,
                round_index=round_index,
            )
            applied_adapter_id = _adapter_id_from_arrays(applied.adapter_tensors)
            central_adapter_id = _adapter_id_from_arrays(central_adapters)
            central_loss = _metric_float(central_evaluation, "loss_mse")
            distributed_loss = _metric_float(applied.evaluation, "loss_mse")
            distance_metrics = _adapter_distance_metrics(
                left=central_adapters,
                right=applied.adapter_tensors,
                origin=initial_adapters,
            )
            trajectory_rounds.append(
                {
                    "centralized_adapter_q_values": list(
                        _adapter_q_values_from_arrays(central_adapters)
                    ),
                    "centralized_checkpoint_id": central_adapter_id,
                    "centralized_loss": central_loss,
                    "cosine_similarity_from_m0": distance_metrics["cosine_similarity_from_m0"],
                    "cumulative_l2_from_m0_centralized": distance_metrics[
                        "cumulative_l2_from_m0_centralized"
                    ],
                    "cumulative_l2_from_m0_distributed": distance_metrics[
                        "cumulative_l2_from_m0_distributed"
                    ],
                    "distributed_adapter_q_values": list(
                        _adapter_q_values_from_arrays(applied.adapter_tensors)
                    ),
                    "distributed_checkpoint_id": applied_adapter_id,
                    "distributed_loss": distributed_loss,
                    "l2_adapter_checkpoint_distance": distance_metrics[
                        "l2_adapter_checkpoint_distance"
                    ],
                    "loss_delta": round(distributed_loss - central_loss, 12),
                    "max_abs_adapter_q_diff": distance_metrics["max_abs_adapter_q_diff"],
                    "round": round_index + 1,
                    "stage_c_checkpoint_id": evidence.next_checkpoint_id,
                }
            )
            round_reports.append(
                {
                    "adapter_checkpoint_materialized": True,
                    "applied_adapter_checkpoint_id": applied.adapter_checkpoint_id,
                    "applied_adapter_id": applied_adapter_id,
                    "evaluation": dict(applied.evaluation),
                    "native_model_values": list(native_values),
                    "parent_adapter_id": current_adapter_id,
                    "receipt_id": receipt.raw_java_receipt_id,
                    "round_index": round_index,
                    "runtime_wal_sha256": transition.native_wal_sha256,
                    "stage_c_checkpoint_id": evidence.next_checkpoint_id,
                    "stage_c_model_values_hash_verified": True,
                    "worker_parent_adapter_ids": [item.parent_adapter_id for item in workers],
                    "worker_shard_leaf_ids": [
                        {"leaf_id": item.leaf_id, "ticket_id": item.ticket_id} for item in workers
                    ],
                }
            )
            current_adapters = _copy_adapter_arrays(applied.adapter_tensors)
            current_adapter_id = applied_adapter_id
            checkpoint_chain.append(current_adapter_id)

    final_evaluation = _evaluate_backend(_backend_from_adapter_arrays(current_adapters))
    initial_loss = _metric_float(initial_evaluation, "loss_mse")
    final_loss = _metric_float(final_evaluation, "loss_mse")
    if final_loss >= initial_loss:
        raise QloraDeltaE2EError("QLORA_TRAINING_QUALITY_LOSS_DID_NOT_IMPROVE")
    max_loss_delta = max(
        abs(_object_float(item["loss_delta"], "QLORA_TRAJECTORY_METRIC_INVALID"))
        for item in trajectory_rounds
    )
    max_checkpoint_distance = max(
        _object_float(
            item["l2_adapter_checkpoint_distance"],
            "QLORA_TRAJECTORY_METRIC_INVALID",
        )
        for item in trajectory_rounds
    )
    max_adapter_q_diff = max(
        _object_int(item["max_abs_adapter_q_diff"], "QLORA_TRAJECTORY_METRIC_INVALID")
        for item in trajectory_rounds
    )
    min_cosine_similarity = min(
        _object_float(
            item["cosine_similarity_from_m0"],
            "QLORA_TRAJECTORY_METRIC_INVALID",
        )
        for item in trajectory_rounds
    )
    trajectory_within_tolerance = (
        max_loss_delta <= TRAJECTORY_MAX_LOSS_DELTA_TOLERANCE
        and max_checkpoint_distance <= TRAJECTORY_MAX_CHECKPOINT_L2_TOLERANCE
        and min_cosine_similarity >= TRAJECTORY_MIN_COSINE_SIMILARITY
    )

    report: dict[str, object] = {
        "adapter_parameter_names": list(ADAPTER_ORDER),
        "adapter_shape": [list(shape) for shape in ADAPTER_SHAPES],
        "centralized": {
            "baseline_used_for_execution": False,
            "final_adapter_id": _adapter_id_from_arrays(central_adapters),
            "final_evaluation": dict(central_final_evaluation),
            "rounds": central_rounds,
            "same_training_budget": True,
        },
        "checkpoint_chain": checkpoint_chain,
        "dataset": {
            "dataset_id": QLORA_DATASET_ID,
            "evaluation_sample_count": _evaluation_batch().token_count,
            "sample_kind": "vector/tiny-qlora-2d",
            "target_kind": "regression/vector-2d",
            "train_sample_count_per_round": sum(item.token_count for item in _worker_batches()),
        },
        "execution_evidence": {
            "all_rounds_applied": True,
            "checkpoint_chain_continuous": len(checkpoint_chain) == rounds + 1,
            "demo_domains_are_protocol_qualification_only": True,
            "execution_mode": "REAL_DRQ1",
            "java_ml_arithmetic_performed": False,
            "java_transport_only": True,
            "native_reduce_apply_wal": True,
            "only_adapter_drq1_contributions": True,
            "python_cross_worker_aggregation_performed": False,
            "round_count": rounds,
            "synthetic_fallback": False,
            "worker_count_per_round": NODE_COUNT,
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "model_plugin_id": QLORA_PLUGIN_ID,
        "non_primary_demo_scope": True,
        "rounds": round_reports,
        "schema_version": "1.0.0",
        "stage_c_apply_profile": "REAL_DRQ1_IDENTITY_ADAPTER_DEMO_PROFILE",
        "training_quality": {
            "distributed_final_evaluation": dict(final_evaluation),
            "distributed_final_loss_mse": final_loss,
            "distributed_initial_evaluation": dict(initial_evaluation),
            "distributed_initial_loss_mse": initial_loss,
            "distributed_loss_improved": final_loss < initial_loss,
            "loss_mse_delta": round(final_loss - initial_loss, 12),
        },
        "trajectory": {
            "rounds": trajectory_rounds,
            "summary": {
                "max_adapter_q_diff": max_adapter_q_diff,
                "max_checkpoint_distance": max_checkpoint_distance,
                "max_loss_delta": round(max_loss_delta, 12),
                "min_cosine_similarity": round(min_cosine_similarity, 12),
                "tolerances": {
                    "max_checkpoint_l2": TRAJECTORY_MAX_CHECKPOINT_L2_TOLERANCE,
                    "max_loss_delta": TRAJECTORY_MAX_LOSS_DELTA_TOLERANCE,
                    "min_cosine_similarity": TRAJECTORY_MIN_COSINE_SIMILARITY,
                },
                "trajectory_within_tolerance": trajectory_within_tolerance,
            },
        },
        "type_name": "QLORA_STAGEC_REAL_DRQ1_MULTI_ROUND_TRAINING_QUALITY_REPORT",
    }
    report_path = destination / "qlora-training-quality-report.json"
    report_path.write_bytes(_canonical_bytes(report) + b"\n")
    return QloraTrainingQualityResult(
        report_path=report_path,
        report=report,
        receipts=tuple(receipts),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="delta-qlora-e2e")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_qlora_delta_e2e(args.repository_root, args.output)
    print(json.dumps({"report": str(result.report_path), "status": "PASS"}, sort_keys=True))
    return 0


__all__ = [
    "QloraDeltaE2EError",
    "QloraDeltaE2EResult",
    "QloraTrainingQualityResult",
    "run_qlora_delta_e2e",
    "run_qlora_training_quality",
]
