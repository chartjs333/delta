from __future__ import annotations

import hashlib
from pathlib import Path

from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.training.baseline import TrainingState, train_to_optimizer_step
from deltatorrent.training.checkpoint import restore_checkpoint, save_checkpoint
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, load_samples
from safetensors.torch import save as save_tensors

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"


def model_hash(state: TrainingState) -> str:
    tensors = {
        name: parameter.detach().cpu().contiguous()
        for name, parameter in sorted(state.model.named_parameters())
    }
    return hashlib.sha256(save_tensors(tensors)).hexdigest()


def test_continuous_and_optimizer_boundary_resume_are_bit_identical(tmp_path: Path) -> None:
    config = BaselineConfig.from_json_file(CONFIG)
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)

    continuous = TrainingState.create(config, len(samples))
    continuous_metrics = train_to_optimizer_step(
        continuous, config, samples, config.optimizer_steps
    )

    interrupted = TrainingState.create(config, len(samples))
    first_metrics = train_to_optimizer_step(interrupted, config, samples, 2)
    store = FilesystemArtifactStore(tmp_path)
    saved = save_checkpoint(store, interrupted, config, "optimizer-step-2")

    resumed = TrainingState.create(config, len(samples))
    restore_checkpoint(store, resumed, config, saved.manifest)
    resumed_metrics = train_to_optimizer_step(resumed, config, samples, config.optimizer_steps)

    assert model_hash(resumed) == model_hash(continuous)
    assert resumed.processed_tokens == continuous.processed_tokens == 64
    assert [item.loss for item in (*first_metrics, *resumed_metrics)] == [
        item.loss for item in continuous_metrics
    ]
    assert store.read(saved.manifest_ref) == store.read(saved.named_manifest_ref)
