from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.artifacts.verifier import BundleVerifier
from deltatorrent.cli.main import main
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef, CheckpointManifest, RunManifest
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.runner import BaselineRunResult, run_baseline

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"
REGISTRY = ROOT / "delta-protocol" / "registry.json"


def test_shared_partial_media_type_cannot_select_artifact_schema(tmp_path: Path) -> None:
    verifier = BundleVerifier(tmp_path, REGISTRY)
    reference = ArtifactRef(
        content_id="sha256:" + "0" * 64,
        media_type="application/vnd.deltareduce.regional-partial;version=1",
        schema_id="SCHEMA-REGIONAL-SHARD-RESULT-V1",
        schema_version="1.0.0",
        byte_length=0,
        locator="partials/forbidden.json",
    )

    with pytest.raises(DeltaError) as captured:
        verifier._verify_reference(reference)

    assert captured.value.code is ErrorCode.INVALID_SCHEMA_ID
    assert "shared denylisted media type" in captured.value.message


@pytest.fixture(scope="module")
def verified_bundle(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, BaselineRunResult]:
    output = tmp_path_factory.mktemp("verified-bundle")
    config = replace(
        BaselineConfig.from_json_file(CONFIG),
        run_id="verify-bundle",
        output_dir=str(output),
    )
    return output, run_baseline(config, repository_root=ROOT)


def all_references(output: Path, result: BaselineRunResult) -> tuple[ArtifactRef, ...]:
    run = result.run_manifest
    checkpoint_ref = run.checkpoint_refs[0]
    checkpoint = CheckpointManifest.from_dict(
        json.loads((output / checkpoint_ref.locator).read_text(encoding="utf-8"))
    )
    return (*run.artifacts, checkpoint_ref, *checkpoint.artifacts)


def test_recursive_bundle_verifier_and_cli_report_pass(
    verified_bundle: tuple[Path, BaselineRunResult],
    capsys: pytest.CaptureFixture[str],
) -> None:
    output, result = verified_bundle
    manifest_path = output / result.run_manifest_ref.locator
    report = BundleVerifier(output, REGISTRY).verify(manifest_path)
    assert report.run_id == "verify-bundle"
    assert report.verified_objects == 8

    assert main(["artifacts", "verify", str(manifest_path), "--root", str(output)]) == 0
    cli_report = json.loads(capsys.readouterr().out)
    assert cli_report == report.to_dict()


@pytest.mark.parametrize("reference_index", range(8))
def test_every_reachable_artifact_corruption_reports_exact_content_id(
    verified_bundle: tuple[Path, BaselineRunResult], reference_index: int
) -> None:
    output, result = verified_bundle
    reference = all_references(output, result)[reference_index]
    path = output / reference.locator
    original = path.read_bytes()
    path.write_bytes(original + b"\x00")
    try:
        with pytest.raises(DeltaError) as captured:
            BundleVerifier(output, REGISTRY).verify(output / result.run_manifest_ref.locator)
        assert captured.value.code is ErrorCode.ARTIFACT_HASH_MISMATCH
        assert captured.value.details["content_id"] == reference.content_id
        assert captured.value.details["locator"] == reference.locator
    finally:
        path.write_bytes(original)


def test_cli_corruption_is_nonzero_and_machine_readable(
    verified_bundle: tuple[Path, BaselineRunResult], capsys: pytest.CaptureFixture[str]
) -> None:
    output, result = verified_bundle
    reference = result.run_manifest.artifacts[0]
    path = output / reference.locator
    original = path.read_bytes()
    path.write_bytes(original + b"corrupt")
    try:
        assert (
            main(
                [
                    "artifacts",
                    "verify",
                    str(output / result.run_manifest_ref.locator),
                    "--root",
                    str(output),
                ]
            )
            == 2
        )
        error = json.loads(capsys.readouterr().err)
        assert error["code"] == "ARTIFACT_HASH_MISMATCH"
        assert error["details"]["content_id"] == reference.content_id
    finally:
        path.write_bytes(original)


def test_manifest_identity_substitution_is_rejected(
    verified_bundle: tuple[Path, BaselineRunResult],
) -> None:
    output, result = verified_bundle
    value = result.run_manifest.to_dict()
    value["config_id"] = "sha256:" + "0" * 64
    substituted = RunManifest.from_dict(value)
    manifest_path = output / result.run_manifest_ref.locator
    original = manifest_path.read_bytes()
    from deltatorrent.artifacts.canonical_json import canonical_json_bytes

    manifest_path.write_bytes(canonical_json_bytes(substituted.to_dict()))
    try:
        with pytest.raises(DeltaError, match="RUN_ARTIFACT_IDENTITY_MISMATCH"):
            BundleVerifier(output, REGISTRY).verify(manifest_path)
    finally:
        manifest_path.write_bytes(original)
