"""End-to-end baseline run composition and immutable bundle publication."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import torch

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef, RunManifest, RunStatus
from deltatorrent.training.baseline import TrainingState, train_to_optimizer_step
from deltatorrent.training.checkpoint import (
    SavedCheckpoint,
    load_checkpoint_manifest,
    restore_checkpoint,
    save_checkpoint,
)
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, load_samples
from deltatorrent.training.model import parameter_schema_id


@dataclass(frozen=True, slots=True)
class BaselineRunResult:
    run_manifest: RunManifest
    run_manifest_ref: ArtifactRef
    final_checkpoint: SavedCheckpoint

    def to_dict(self) -> dict[str, object]:
        return {
            "checkpoint_manifest": self.final_checkpoint.named_manifest_ref.to_dict(),
            "run_id": self.run_manifest.run_id,
            "run_manifest": self.run_manifest_ref.to_dict(),
            "status": self.run_manifest.status.value,
        }


class MetricsJournal:
    def __init__(self, path: Path, resume: bool) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not resume:
            raise DeltaError(ErrorCode.ARTIFACT_IMMUTABLE_CONFLICT, "metrics journal exists")

    def append(self, value: dict[str, object]) -> None:
        try:
            encoded = json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise DeltaError(ErrorCode.UNSAFE_SERIALIZATION, "metrics are not finite") from exc
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded + "\n")
            stream.flush()
            os.fsync(stream.fileno())


_NUMERIC_FAILURES = {
    "NON_FINITE_GRADIENT",
    "NON_FINITE_LOSS",
    "NON_FINITE_OPTIMIZER_STATE",
}


def run_baseline(
    config: BaselineConfig,
    *,
    repository_root: Path,
    resume_checkpoint: Path | None = None,
) -> BaselineRunResult:
    output = (repository_root / config.output_dir).resolve()
    store = FilesystemArtifactStore(output)
    final_manifest_path = output / f"runs/{config.run_id}/run-manifest.json"
    if final_manifest_path.exists():
        raise DeltaError(
            ErrorCode.ARTIFACT_IMMUTABLE_CONFLICT,
            "completed run is immutable",
            {"run_id": config.run_id},
        )

    tokenizer_path = (repository_root / config.tokenizer_path).resolve()
    corpus_path = (repository_root / config.corpus_path).resolve()
    tokenizer = Tokenizer.from_json_file(tokenizer_path)
    if len(tokenizer.vocabulary) != config.vocab_size or tokenizer.pad_id != 0:
        raise DeltaError(ErrorCode.SCHEMA_INVALID, "TOKENIZER_CONFIG_MISMATCH")
    samples = load_samples(corpus_path, tokenizer, config.sequence_length)
    state = TrainingState.create(config, len(samples))
    if resume_checkpoint is not None:
        manifest = load_checkpoint_manifest(resume_checkpoint)
        restore_checkpoint(store, state, config, manifest)

    config_ref = store.publish_json(
        config.to_dict(),
        media_type="application/vnd.deltareduce.baseline-config+json;version=1",
        schema_id="SCHEMA-BASELINE-CONFIG-V1",
    )
    corpus_ref = store.publish_bytes(
        corpus_path.read_bytes(),
        media_type="text/plain;charset=utf-8",
        schema_id="SCHEMA-CORPUS-TEXT-V1",
    )
    tokenizer_ref = store.publish_bytes(
        tokenizer_path.read_bytes(),
        media_type="application/vnd.deltareduce.tokenizer+json;version=1",
        schema_id="SCHEMA-TOKENIZER-V1",
    )
    lock_path = repository_root / "uv.lock"
    lock_ref = store.publish_bytes(
        lock_path.read_bytes(),
        media_type="application/vnd.deltareduce.uv-lock+toml;version=1",
        schema_id="SCHEMA-UV-LOCK-V1",
    )

    metrics_locator = f"runs/{config.run_id}/metrics.jsonl"
    journal = MetricsJournal(output / metrics_locator, resume=resume_checkpoint is not None)
    final_checkpoint: SavedCheckpoint | None = None
    try:
        while state.optimizer_step < config.optimizer_steps:
            prior_tokens = state.processed_tokens
            started = time.perf_counter()
            (metric,) = train_to_optimizer_step(state, config, samples, state.optimizer_step + 1)
            elapsed = max(time.perf_counter() - started, sys.float_info.min)
            interval_tokens = state.processed_tokens - prior_tokens
            journal.append(
                {
                    "learning_rate": metric.learning_rate,
                    "loss": metric.loss,
                    "optimizer_step": metric.optimizer_step,
                    "peak_memory_bytes": None,
                    "processed_tokens": metric.processed_tokens,
                    "schema_version": "1.0.0",
                    "step": metric.step,
                    "throughput_tokens_per_second": interval_tokens / elapsed,
                    "wall_time_seconds": elapsed,
                }
            )
            if state.optimizer_step % config.checkpoint_every_optimizer_steps == 0:
                final_checkpoint = save_checkpoint(
                    store, state, config, f"optimizer-step-{state.optimizer_step}"
                )
    except DeltaError as exc:
        if exc.message not in _NUMERIC_FAILURES and exc.code is not ErrorCode.UNSAFE_SERIALIZATION:
            raise
        _publish_failed_run(
            store=store,
            output=output,
            repository_root=repository_root,
            config=config,
            state=state,
            base_artifacts=(config_ref, corpus_ref, tokenizer_ref, lock_ref),
            metrics_locator=metrics_locator,
            final_checkpoint=final_checkpoint,
            failure_code=(exc.message if exc.message in _NUMERIC_FAILURES else "NON_FINITE_METRIC"),
        )
        raise
    if final_checkpoint is None or final_checkpoint.manifest.optimizer_step != state.optimizer_step:
        final_checkpoint = save_checkpoint(
            store, state, config, f"optimizer-step-{state.optimizer_step}"
        )

    metrics_ref = store.publish_named(
        metrics_locator,
        (output / metrics_locator).read_bytes(),
        media_type="application/vnd.deltareduce.metrics+jsonl;version=1",
        schema_id="SCHEMA-METRICS-JSONL-V1",
    )
    run_manifest = RunManifest(
        run_id=config.run_id,
        status=RunStatus.COMPLETED,
        config_id=config_ref.content_id,
        code_revision=_code_revision(repository_root),
        dependency_lock_id=lock_ref.content_id,
        dataset_id=corpus_ref.content_id,
        model_id=parameter_schema_id(state.model),
        tokenizer_id=tokenizer_ref.content_id,
        processed_tokens=state.processed_tokens,
        platform=_platform_fingerprint(config),
        seeds={"data": config.seed, "model": config.seed, "torch": config.seed},
        artifacts=(config_ref, corpus_ref, tokenizer_ref, lock_ref, metrics_ref),
        checkpoint_refs=(final_checkpoint.named_manifest_ref,),
    )
    run_manifest_ref = _publish_run_manifest(store, run_manifest)
    return BaselineRunResult(run_manifest, run_manifest_ref, final_checkpoint)


def _publish_failed_run(
    *,
    store: FilesystemArtifactStore,
    output: Path,
    repository_root: Path,
    config: BaselineConfig,
    state: TrainingState,
    base_artifacts: tuple[ArtifactRef, ...],
    metrics_locator: str,
    final_checkpoint: SavedCheckpoint | None,
    failure_code: str,
) -> None:
    artifacts = base_artifacts
    metrics_path = output / metrics_locator
    if metrics_path.is_file():
        metrics_ref = store.publish_named(
            metrics_locator,
            metrics_path.read_bytes(),
            media_type="application/vnd.deltareduce.metrics+jsonl;version=1",
            schema_id="SCHEMA-METRICS-JSONL-V1",
        )
        artifacts = (*artifacts, metrics_ref)
    manifest = RunManifest(
        run_id=config.run_id,
        status=RunStatus.FAILED,
        config_id=base_artifacts[0].content_id,
        code_revision=_code_revision(repository_root),
        dependency_lock_id=base_artifacts[3].content_id,
        dataset_id=base_artifacts[1].content_id,
        model_id=parameter_schema_id(state.model),
        tokenizer_id=base_artifacts[2].content_id,
        processed_tokens=state.processed_tokens,
        platform=_platform_fingerprint(config),
        seeds={"data": config.seed, "model": config.seed, "torch": config.seed},
        artifacts=artifacts,
        checkpoint_refs=(final_checkpoint.named_manifest_ref,) if final_checkpoint else (),
        failure_code=failure_code,
    )
    _publish_run_manifest(store, manifest)


def _publish_run_manifest(store: FilesystemArtifactStore, manifest: RunManifest) -> ArtifactRef:
    return store.publish_named(
        f"runs/{manifest.run_id}/run-manifest.json",
        canonical_json_bytes(manifest.to_dict()),
        media_type="application/vnd.deltareduce.run-manifest+json;version=1",
        schema_id="SCHEMA-RUN-MANIFEST-V1",
    )


def _code_revision(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        return sha256_content_id(b"UNVERSIONED")
    return completed.stdout.strip()


def _platform_fingerprint(config: BaselineConfig) -> dict[str, str]:
    return {
        "device": config.device,
        "dtype": config.dtype,
        "machine": platform.machine() or "unknown",
        "operating_system": platform.system() or "unknown",
        "python": platform.python_version(),
        "reproducibility_class": "cpu-float32-torch-2.6-v1",
        "torch": torch.__version__,
    }
