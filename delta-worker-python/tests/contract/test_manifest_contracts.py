from __future__ import annotations

import json
from pathlib import Path

import pytest
from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import (
    ArtifactRef,
    CheckpointManifest,
    RunManifest,
    RunStatus,
)

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "delta-protocol"
CONTENT_A = "sha256:" + "a" * 64
CONTENT_B = "sha256:" + "b" * 64
CONTENT_C = "sha256:" + "c" * 64
CONTENT_D = "sha256:" + "d" * 64
CONTENT_E = "sha256:" + "e" * 64


def artifact(content_id: str = CONTENT_A) -> ArtifactRef:
    return ArtifactRef(
        byte_length=3,
        content_id=content_id,
        locator=f"objects/sha256/{content_id[-2:]}/{content_id.removeprefix('sha256:')}",
        media_type="application/octet-stream",
        schema_id="SCHEMA-SAFETENSORS-V1",
        schema_version="1.0.0",
    )


def test_artifact_ref_matches_runtime_neutral_schema_shape() -> None:
    value = artifact().to_dict()
    schema = json.loads((PROTOCOL / "schemas/artifact-ref.schema.json").read_text(encoding="utf-8"))
    assert set(value) == set(schema["required"])
    assert schema["additionalProperties"] is False
    assert ArtifactRef.from_dict(value) == artifact()


def test_manifest_models_bind_formal_semantics_and_canonical_bytes() -> None:
    checkpoint = CheckpointManifest(
        run_id="run-001",
        checkpoint_id="checkpoint-001",
        step=2,
        optimizer_step=1,
        processed_tokens=16,
        sampler_cursor=4,
        boundary="OPTIMIZER_STEP",
        artifacts=(artifact(CONTENT_A),),
    )
    run = RunManifest(
        run_id="run-001",
        status=RunStatus.COMPLETED,
        config_id=CONTENT_A,
        code_revision="deadbeef",
        dependency_lock_id=CONTENT_B,
        dataset_id=CONTENT_C,
        model_id=CONTENT_D,
        tokenizer_id=CONTENT_E,
        processed_tokens=16,
        platform={"python": "3.12.1", "reproducibility_class": "cpu-reference-v1"},
        seeds={"data": 7, "model": 11},
        artifacts=(artifact(CONTENT_A),),
        checkpoint_refs=(artifact(CONTENT_B),),
    )
    checkpoint_schema = json.loads(
        (PROTOCOL / "schemas/checkpoint-manifest.schema.json").read_text(encoding="utf-8")
    )
    run_schema = json.loads(
        (PROTOCOL / "schemas/run-manifest.schema.json").read_text(encoding="utf-8")
    )
    assert set(checkpoint.to_dict()) == set(checkpoint_schema["required"])
    assert set(run.to_dict()) == set(run_schema["required"])
    assert CheckpointManifest.from_dict(checkpoint.to_dict()) == checkpoint
    assert RunManifest.from_dict(run.to_dict()) == run
    assert canonical_json_bytes(run.to_dict()).startswith(b'{"artifacts":')


def test_artifact_ref_rejects_unknown_fields_and_unsafe_locator() -> None:
    value = artifact().to_dict()
    value["unknown"] = "forbidden"
    with pytest.raises(DeltaError, match="fields do not match"):
        ArtifactRef.from_dict(value)
    with pytest.raises(DeltaError) as captured:
        ArtifactRef(
            byte_length=1,
            content_id=CONTENT_A,
            locator="../escape",
            media_type="application/octet-stream",
            schema_id="SCHEMA-SAFETENSORS-V1",
            schema_version="1.0.0",
        )
    assert captured.value.code is ErrorCode.INVALID_ARTIFACT_LOCATOR


def test_failed_and_completed_status_contracts_are_disjoint() -> None:
    common = {
        "artifacts": (),
        "checkpoint_refs": (),
        "code_revision": "deadbeef",
        "config_id": CONTENT_A,
        "dataset_id": CONTENT_C,
        "dependency_lock_id": CONTENT_B,
        "model_id": CONTENT_D,
        "platform": {"python": "3.12.1"},
        "processed_tokens": 0,
        "run_id": "run-001",
        "seeds": {"model": 1},
        "tokenizer_id": CONTENT_E,
    }
    with pytest.raises(DeltaError, match="completed run"):
        RunManifest(status=RunStatus.COMPLETED, failure_code="NON_FINITE_LOSS", **common)
    with pytest.raises(DeltaError, match="requires failure_code"):
        RunManifest(status=RunStatus.FAILED, **common)
