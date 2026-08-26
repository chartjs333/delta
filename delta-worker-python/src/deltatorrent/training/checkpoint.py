"""Pickle-free checkpoint snapshot and exact optimizer-boundary restore."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef, CheckpointManifest
from deltatorrent.training.baseline import TrainingState
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.model import parameter_schema_id


@dataclass(frozen=True, slots=True)
class SavedCheckpoint:
    manifest: CheckpointManifest
    manifest_ref: ArtifactRef
    named_manifest_ref: ArtifactRef


def save_checkpoint(
    store: FilesystemArtifactStore,
    state: TrainingState,
    config: BaselineConfig,
    checkpoint_id: str,
) -> SavedCheckpoint:
    if state.micro_step % config.gradient_accumulation_steps != 0:
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_NOT_AT_OPTIMIZER_BOUNDARY")
    tensors: dict[str, torch.Tensor] = {}
    for name, parameter in sorted(state.model.named_parameters()):
        tensors[f"model::{name}"] = parameter.detach().cpu().contiguous()
        tensors[f"adam_first::{name}"] = state.optimizer.first_moment[name].cpu().contiguous()
        tensors[f"adam_second::{name}"] = state.optimizer.second_moment[name].cpu().contiguous()
    tensor_ref = store.publish_bytes(
        save_tensors(tensors),
        media_type="application/vnd.safetensors",
        schema_id="SCHEMA-SAFETENSORS-V1",
    )
    metadata = {
        "checkpoint_id": checkpoint_id,
        "formal_semantics_id": state_semantics_id(),
        "model_schema_id": parameter_schema_id(state.model),
        "optimizer": {
            "kind": "CANONICAL_ADAMW_V1",
            "step": state.optimizer.step_count,
        },
        "rng": {"torch_cpu_hex": bytes(torch.get_rng_state().tolist()).hex()},
        "run_id": config.run_id,
        "sampler": {
            "cursor": state.sampler.cursor,
            "sample_count": state.sampler.sample_count,
            "seed": state.sampler.seed,
        },
        "scaler": None,
        "scheduler": None,
        "schema_version": "1.0.0",
    }
    state_ref = store.publish_json(
        metadata,
        media_type="application/vnd.deltareduce.training-state+json;version=1",
        schema_id="SCHEMA-TRAINING-STATE-V1",
    )
    manifest = CheckpointManifest(
        run_id=config.run_id,
        checkpoint_id=checkpoint_id,
        step=state.micro_step,
        optimizer_step=state.optimizer_step,
        processed_tokens=state.processed_tokens,
        sampler_cursor=state.sampler.cursor,
        boundary="OPTIMIZER_STEP",
        artifacts=(tensor_ref, state_ref),
    )
    encoded = canonical_json_bytes(manifest.to_dict())
    manifest_ref = store.publish_bytes(
        encoded,
        media_type="application/vnd.deltareduce.checkpoint-manifest+json;version=1",
        schema_id="SCHEMA-CHECKPOINT-MANIFEST-V1",
    )
    named = store.publish_named(
        f"runs/{config.run_id}/checkpoints/{checkpoint_id}/checkpoint-manifest.json",
        encoded,
        media_type=manifest_ref.media_type,
        schema_id=manifest_ref.schema_id,
    )
    return SavedCheckpoint(manifest, manifest_ref, named)


def restore_checkpoint(
    store: FilesystemArtifactStore,
    state: TrainingState,
    config: BaselineConfig,
    manifest: CheckpointManifest,
) -> None:
    if manifest.run_id != config.run_id:
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_RUN_ID_MISMATCH")
    by_schema = {item.schema_id: item for item in manifest.artifacts}
    if set(by_schema) != {"SCHEMA-SAFETENSORS-V1", "SCHEMA-TRAINING-STATE-V1"}:
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_ARTIFACT_SET_INVALID")
    tensors = load_tensors(store.read(by_schema["SCHEMA-SAFETENSORS-V1"]))
    metadata = _load_metadata(store.read(by_schema["SCHEMA-TRAINING-STATE-V1"]))
    if metadata["model_schema_id"] != parameter_schema_id(state.model):
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_MODEL_SCHEMA_MISMATCH")
    expected_keys: set[str] = set()
    with torch.no_grad():
        for name, parameter in sorted(state.model.named_parameters()):
            model_key = f"model::{name}"
            first_key = f"adam_first::{name}"
            second_key = f"adam_second::{name}"
            expected_keys.update((model_key, first_key, second_key))
            parameter.copy_(tensors[model_key])
            state.optimizer.first_moment[name].copy_(tensors[first_key])
            state.optimizer.second_moment[name].copy_(tensors[second_key])
    if set(tensors) != expected_keys:
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_TENSOR_SET_INVALID")
    sampler = metadata["sampler"]
    if (
        sampler["seed"] != state.sampler.seed
        or sampler["sample_count"] != state.sampler.sample_count
    ):
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_SAMPLER_MISMATCH")
    state.sampler.cursor = manifest.sampler_cursor
    state.micro_step = manifest.step
    state.optimizer_step = manifest.optimizer_step
    state.processed_tokens = manifest.processed_tokens
    state.optimizer.step_count = manifest.optimizer_step
    torch.set_rng_state(
        torch.tensor(list(bytes.fromhex(metadata["rng"]["torch_cpu_hex"])), dtype=torch.uint8)
    )


def load_checkpoint_manifest(path: Path) -> CheckpointManifest:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_MANIFEST_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_MANIFEST_ROOT_INVALID")
    return CheckpointManifest.from_dict(value)


def _load_metadata(value: bytes) -> dict[str, Any]:
    try:
        result = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_STATE_INVALID") from exc
    if not isinstance(result, dict) or result.get("formal_semantics_id") != state_semantics_id():
        raise DeltaError(ErrorCode.FORMAL_SEMANTICS_MISMATCH, "checkpoint state mismatch")
    return result


def state_semantics_id() -> str:
    from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID

    return FORMAL_SEMANTICS_ID
