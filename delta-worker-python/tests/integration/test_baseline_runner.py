from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.artifacts.verifier import BundleVerifier
from deltatorrent.cli.main import main
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.training.baseline import TrainingState, train_to_optimizer_step
from deltatorrent.training.checkpoint import save_checkpoint
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, load_samples
from deltatorrent.training.runner import BaselineRunResult, MetricsJournal, run_baseline

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"


def tensor_content_id(result: BaselineRunResult) -> str:
    final = result.final_checkpoint
    return next(
        item.content_id
        for item in final.manifest.artifacts
        if item.schema_id == "SCHEMA-SAFETENSORS-V1"
    )


def test_two_runs_publish_complete_bundles_with_same_checkpoint_bytes(tmp_path: Path) -> None:
    base = BaselineConfig.from_json_file(CONFIG)
    first_config = replace(base, run_id="repeat-a", output_dir=str(tmp_path))
    second_config = replace(base, run_id="repeat-b", output_dir=str(tmp_path))
    first = run_baseline(first_config, repository_root=ROOT)
    second = run_baseline(second_config, repository_root=ROOT)

    assert first.run_manifest.status.value == "COMPLETED"
    assert first.run_manifest.processed_tokens == second.run_manifest.processed_tokens == 64
    assert tensor_content_id(first) == tensor_content_id(second)
    for run_id in ("repeat-a", "repeat-b"):
        manifest_path = tmp_path / "runs" / run_id / "run-manifest.json"
        metrics_path = tmp_path / "runs" / run_id / "metrics.jsonl"
        assert manifest_path.is_file()
        assert len(metrics_path.read_text(encoding="utf-8").splitlines()) == 4
        assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "COMPLETED"

    with pytest.raises(DeltaError) as captured:
        run_baseline(first_config, repository_root=ROOT)
    assert captured.value.code is ErrorCode.ARTIFACT_IMMUTABLE_CONFLICT


def test_cli_baseline_run_returns_machine_readable_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = replace(
        BaselineConfig.from_json_file(CONFIG),
        run_id="cli-run",
        output_dir=str(tmp_path / "bundle"),
    )
    config_path = tmp_path / "config.json"
    config_path.write_bytes(canonical_json_bytes(config.to_dict()))
    assert main(["baseline", "run", str(config_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["run_id"] == "cli-run"
    assert result["status"] == "COMPLETED"


def test_metrics_journal_rejects_non_finite_values(tmp_path: Path) -> None:
    journal = MetricsJournal(tmp_path / "metrics.jsonl", resume=False)
    with pytest.raises(DeltaError) as captured:
        journal.append({"loss": float("nan")})
    assert captured.value.code is ErrorCode.UNSAFE_SERIALIZATION
    assert not (tmp_path / "metrics.jsonl").exists()


def test_non_finite_training_publishes_failed_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = replace(
        BaselineConfig.from_json_file(CONFIG),
        run_id="failed-run",
        output_dir=str(tmp_path),
    )

    def fail_training(*args: object, **kwargs: object) -> tuple[()]:
        raise DeltaError(ErrorCode.INVALID_MANIFEST, "NON_FINITE_LOSS")

    monkeypatch.setattr("deltatorrent.training.runner.train_to_optimizer_step", fail_training)
    with pytest.raises(DeltaError, match="NON_FINITE_LOSS"):
        run_baseline(config, repository_root=ROOT)

    manifest_path = tmp_path / "runs/failed-run/run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"
    assert manifest["failure_code"] == "NON_FINITE_LOSS"
    assert manifest["checkpoint_refs"] == []
    verified = BundleVerifier(tmp_path, ROOT / "delta-protocol/registry.json").verify(manifest_path)
    assert verified.verified_objects == 4


def test_cli_resume_completes_from_safe_optimizer_boundary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "resume-bundle"
    config = replace(
        BaselineConfig.from_json_file(CONFIG),
        run_id="cli-resume",
        output_dir=str(output),
    )
    tokenizer = Tokenizer.from_json_file(ROOT / config.tokenizer_path)
    samples = load_samples(ROOT / config.corpus_path, tokenizer, config.sequence_length)
    state = TrainingState.create(config, len(samples))
    train_to_optimizer_step(state, config, samples, 2)
    saved = save_checkpoint(FilesystemArtifactStore(output), state, config, "optimizer-step-2")
    config_path = tmp_path / "resume-config.json"
    config_path.write_bytes(canonical_json_bytes(config.to_dict()))

    assert (
        main(
            [
                "baseline",
                "resume",
                str(config_path),
                str(output / saved.named_manifest_ref.locator),
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "COMPLETED"
    manifest = json.loads((output / result["run_manifest"]["locator"]).read_text(encoding="utf-8"))
    assert manifest["processed_tokens"] == 64
