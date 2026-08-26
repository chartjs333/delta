from __future__ import annotations

from pathlib import Path

import pytest
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef


def test_content_addressed_publish_is_atomic_and_idempotent(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path)
    first = store.publish_bytes(
        b"immutable bytes",
        media_type="application/octet-stream",
        schema_id="SCHEMA-SAFETENSORS-V1",
    )
    second = store.publish_bytes(
        b"immutable bytes",
        media_type="application/octet-stream",
        schema_id="SCHEMA-SAFETENSORS-V1",
    )
    assert first == second
    assert store.read(first) == b"immutable bytes"
    assert list(tmp_path.rglob("*.tmp")) == []


def test_named_publish_never_overwrites_finalized_bytes(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path)
    reference = store.publish_named(
        "runs/run-001/run-manifest.json",
        b"first",
        media_type="application/json",
        schema_id="SCHEMA-RUN-MANIFEST-V1",
    )
    with pytest.raises(DeltaError) as captured:
        store.publish_named(
            reference.locator,
            b"second",
            media_type=reference.media_type,
            schema_id=reference.schema_id,
        )
    assert captured.value.code is ErrorCode.ARTIFACT_IMMUTABLE_CONFLICT
    assert store.read(reference) == b"first"


def test_corruption_is_detected_before_bytes_are_returned(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path)
    reference = store.publish_bytes(
        b"correct",
        media_type="application/octet-stream",
        schema_id="SCHEMA-SAFETENSORS-V1",
    )
    (tmp_path / reference.locator).write_bytes(b"corrupt")
    with pytest.raises(DeltaError) as captured:
        store.read(reference)
    assert captured.value.code is ErrorCode.ARTIFACT_HASH_MISMATCH


def test_crash_temporary_file_is_invisible_and_cleanup_safe(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path)
    partial = tmp_path / "runs" / "run-001" / ".checkpoint.crash.tmp"
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b"partial")
    missing = ArtifactRef(
        byte_length=7,
        content_id="sha256:" + "0" * 64,
        locator="runs/run-001/checkpoint.json",
        media_type="application/json",
        schema_id="SCHEMA-CHECKPOINT-MANIFEST-V1",
        schema_version="1.0.0",
    )
    with pytest.raises(DeltaError) as captured:
        store.read(missing)
    assert captured.value.code is ErrorCode.ARTIFACT_NOT_FOUND
    assert store.cleanup_temporary_files() == ("runs/run-001/.checkpoint.crash.tmp",)
    assert not partial.exists()


def test_locator_cannot_escape_store(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path)
    with pytest.raises(DeltaError) as captured:
        store.publish_named(
            "../outside",
            b"unsafe",
            media_type="application/octet-stream",
            schema_id="SCHEMA-SAFETENSORS-V1",
        )
    assert captured.value.code is ErrorCode.INVALID_ARTIFACT_LOCATOR
