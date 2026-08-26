"""Fail-closed recursive verification for immutable baseline run bundles."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID
from deltatorrent.domain.manifests import ArtifactRef, CheckpointManifest, RunManifest, RunStatus


@dataclass(frozen=True, slots=True)
class BundleVerificationResult:
    run_id: str
    run_manifest_id: str
    verified_objects: int

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_manifest_id": self.run_manifest_id,
            "schema_version": "1.0.0",
            "status": "PASS",
            "verified_objects": self.verified_objects,
        }


class BundleVerifier:
    """Verify the trust root and every object reachable from one run manifest."""

    def __init__(self, store_root: Path, registry_path: Path) -> None:
        self.store = FilesystemArtifactStore(store_root)
        self.registry_path = registry_path.resolve()
        self._media_schemas = self._load_registry()
        self._verified: set[tuple[str, str]] = set()

    def verify(self, run_manifest_path: Path) -> BundleVerificationResult:
        manifest_bytes = self._read_trust_root(run_manifest_path)
        manifest_value = self._decode_object(manifest_bytes, "RUN_MANIFEST_JSON_INVALID")
        manifest = RunManifest.from_dict(manifest_value)
        if canonical_json_bytes(manifest.to_dict()) != manifest_bytes:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "RUN_MANIFEST_NOT_CANONICAL")

        direct = self._index_by_schema(manifest.artifacts, "RUN_ARTIFACT_SET_INVALID")
        self._require_identity(direct, "SCHEMA-BASELINE-CONFIG-V1", manifest.config_id)
        self._require_identity(direct, "SCHEMA-CORPUS-TEXT-V1", manifest.dataset_id)
        self._require_identity(direct, "SCHEMA-TOKENIZER-V1", manifest.tokenizer_id)
        self._require_identity(direct, "SCHEMA-UV-LOCK-V1", manifest.dependency_lock_id)
        self._require_single(direct, "SCHEMA-METRICS-JSONL-V1")
        for reference in manifest.artifacts:
            self._verify_reference(reference)

        if manifest.status is RunStatus.COMPLETED and not manifest.checkpoint_refs:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "COMPLETED_RUN_HAS_NO_CHECKPOINT")
        checkpoints = tuple(
            self._verify_checkpoint(reference, expected_run_id=manifest.run_id)
            for reference in manifest.checkpoint_refs
        )
        if checkpoints:
            final = max(checkpoints, key=lambda item: (item.optimizer_step, item.step))
            if final.processed_tokens != manifest.processed_tokens:
                raise DeltaError(
                    ErrorCode.INVALID_MANIFEST,
                    "RUN_CHECKPOINT_TOKEN_COUNT_MISMATCH",
                    {"checkpoint_id": final.checkpoint_id},
                )
            self._verify_model_identity(final, manifest.model_id)

        config = self._decode_object(
            self.store.read(direct["SCHEMA-BASELINE-CONFIG-V1"]),
            "BASELINE_CONFIG_JSON_INVALID",
        )
        if config.get("run_id") != manifest.run_id:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "RUN_CONFIG_IDENTITY_MISMATCH")

        return BundleVerificationResult(
            run_id=manifest.run_id,
            run_manifest_id=sha256_content_id(manifest_bytes),
            verified_objects=len(self._verified),
        )

    def _verify_checkpoint(
        self, reference: ArtifactRef, *, expected_run_id: str
    ) -> CheckpointManifest:
        if reference.schema_id != "SCHEMA-CHECKPOINT-MANIFEST-V1":
            raise DeltaError(
                ErrorCode.INVALID_SCHEMA_ID,
                "checkpoint reference has the wrong schema",
                {"content_id": reference.content_id, "schema_id": reference.schema_id},
            )
        value = self._decode_object(
            self._verify_reference(reference), "CHECKPOINT_MANIFEST_JSON_INVALID"
        )
        checkpoint = CheckpointManifest.from_dict(value)
        if checkpoint.run_id != expected_run_id:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_RUN_ID_MISMATCH")
        artifacts = self._index_by_schema(checkpoint.artifacts, "CHECKPOINT_ARTIFACT_SET_INVALID")
        if set(artifacts) != {"SCHEMA-SAFETENSORS-V1", "SCHEMA-TRAINING-STATE-V1"}:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_ARTIFACT_SET_INVALID")
        for artifact in checkpoint.artifacts:
            self._verify_reference(artifact)
        state = self._decode_object(
            self.store.read(artifacts["SCHEMA-TRAINING-STATE-V1"]),
            "CHECKPOINT_STATE_JSON_INVALID",
        )
        self._verify_checkpoint_state(checkpoint, state)
        return checkpoint

    def _verify_model_identity(self, checkpoint: CheckpointManifest, model_id: str) -> None:
        artifacts = self._index_by_schema(checkpoint.artifacts, "CHECKPOINT_ARTIFACT_SET_INVALID")
        state = self._decode_object(
            self.store.read(artifacts["SCHEMA-TRAINING-STATE-V1"]),
            "CHECKPOINT_STATE_JSON_INVALID",
        )
        if state.get("model_schema_id") != model_id:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "RUN_MODEL_ID_MISMATCH")

    def _verify_checkpoint_state(
        self, checkpoint: CheckpointManifest, state: dict[str, Any]
    ) -> None:
        expected = {
            "checkpoint_id",
            "formal_semantics_id",
            "model_schema_id",
            "optimizer",
            "rng",
            "run_id",
            "sampler",
            "scaler",
            "scheduler",
            "schema_version",
        }
        if set(state) != expected:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_STATE_FIELDS_INVALID")
        optimizer = state.get("optimizer")
        sampler = state.get("sampler")
        if (
            state.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            or state.get("schema_version") != "1.0.0"
            or state.get("run_id") != checkpoint.run_id
            or state.get("checkpoint_id") != checkpoint.checkpoint_id
            or not isinstance(optimizer, dict)
            or set(optimizer) != {"kind", "step"}
            or optimizer.get("kind") != "CANONICAL_ADAMW_V1"
            or optimizer.get("step") != checkpoint.optimizer_step
            or not isinstance(sampler, dict)
            or set(sampler) != {"cursor", "sample_count", "seed"}
            or sampler.get("cursor") != checkpoint.sampler_cursor
        ):
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "CHECKPOINT_STATE_MISMATCH")

    def _verify_reference(self, reference: ArtifactRef) -> bytes:
        expected_schema = self._media_schemas.get(reference.media_type)
        if expected_schema is None:
            raise DeltaError(
                ErrorCode.UNKNOWN_MEDIA_TYPE,
                "artifact media type is not registered",
                {"content_id": reference.content_id, "media_type": reference.media_type},
            )
        if expected_schema != reference.schema_id:
            raise DeltaError(
                ErrorCode.INVALID_SCHEMA_ID,
                "artifact media type and schema do not match",
                {"content_id": reference.content_id, "schema_id": reference.schema_id},
            )
        value = self.store.read(reference)
        self._verified.add((reference.content_id, reference.locator))
        return value

    def _load_registry(self) -> dict[str, str]:
        try:
            registry_bytes = self.registry_path.read_bytes()
        except OSError as exc:
            raise DeltaError(
                ErrorCode.ARTIFACT_NOT_FOUND,
                "protocol registry does not exist",
                {"path": str(self.registry_path)},
            ) from exc
        value = self._decode_object(registry_bytes, "REGISTRY_JSON_INVALID")
        if value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID:
            raise DeltaError(ErrorCode.FORMAL_SEMANTICS_MISMATCH, "registry semantics mismatch")
        schemas = value.get("schemas")
        media_types = value.get("media_types")
        if not isinstance(schemas, list) or not isinstance(media_types, list):
            raise DeltaError(ErrorCode.INVALID_MANIFEST, "REGISTRY_FIELDS_INVALID")
        schema_ids: set[str] = set()
        for record in schemas:
            if not isinstance(record, dict) or set(record) != {"id", "path", "sha256"}:
                raise DeltaError(ErrorCode.INVALID_MANIFEST, "REGISTRY_SCHEMA_INVALID")
            path = (self.registry_path.parent / str(record["path"])).resolve()
            if not path.is_relative_to(self.registry_path.parent):
                raise DeltaError(ErrorCode.INVALID_MANIFEST, "REGISTRY_SCHEMA_PATH_INVALID")
            try:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                raise DeltaError(ErrorCode.INVALID_MANIFEST, "REGISTRY_SCHEMA_MISSING") from exc
            if actual != record["sha256"]:
                raise DeltaError(ErrorCode.ARTIFACT_HASH_MISMATCH, "registry schema hash mismatch")
            schema_ids.add(str(record["id"]))
        result: dict[str, str] = {}
        for record in media_types:
            if not isinstance(record, dict) or set(record) != {"id", "schema_id", "value"}:
                raise DeltaError(ErrorCode.INVALID_MANIFEST, "REGISTRY_MEDIA_TYPE_INVALID")
            schema_id = str(record["schema_id"])
            media_type = str(record["value"])
            if schema_id not in schema_ids or media_type in result:
                raise DeltaError(ErrorCode.INVALID_MANIFEST, "REGISTRY_MEDIA_TYPE_INVALID")
            result[media_type] = schema_id
        return result

    def _read_trust_root(self, path: Path) -> bytes:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.store.root):
            raise DeltaError(ErrorCode.INVALID_ARTIFACT_LOCATOR, "run manifest escaped store root")
        try:
            return resolved.read_bytes()
        except OSError as exc:
            raise DeltaError(ErrorCode.ARTIFACT_NOT_FOUND, "run manifest does not exist") from exc

    @staticmethod
    def _decode_object(value: bytes, error: str) -> dict[str, Any]:
        try:
            decoded = json.loads(value.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DeltaError(ErrorCode.INVALID_MANIFEST, error) from exc
        if not isinstance(decoded, dict):
            raise DeltaError(ErrorCode.INVALID_MANIFEST, error)
        return decoded

    @staticmethod
    def _index_by_schema(references: tuple[ArtifactRef, ...], error: str) -> dict[str, ArtifactRef]:
        result = {item.schema_id: item for item in references}
        if len(result) != len(references):
            raise DeltaError(ErrorCode.INVALID_MANIFEST, error)
        return result

    @staticmethod
    def _require_identity(
        references: dict[str, ArtifactRef], schema_id: str, content_id: str
    ) -> None:
        reference = BundleVerifier._require_single(references, schema_id)
        if reference.content_id != content_id:
            raise DeltaError(
                ErrorCode.INVALID_MANIFEST,
                "RUN_ARTIFACT_IDENTITY_MISMATCH",
                {"content_id": content_id, "schema_id": schema_id},
            )

    @staticmethod
    def _require_single(references: dict[str, ArtifactRef], schema_id: str) -> ArtifactRef:
        try:
            return references[schema_id]
        except KeyError as exc:
            raise DeltaError(
                ErrorCode.INVALID_MANIFEST,
                "RUN_ARTIFACT_MISSING",
                {"schema_id": schema_id},
            ) from exc


def infer_store_root(run_manifest_path: Path) -> Path:
    resolved = run_manifest_path.resolve()
    if (
        resolved.name != "run-manifest.json"
        or len(resolved.parents) < 3
        or resolved.parent.parent.name != "runs"
    ):
        raise DeltaError(
            ErrorCode.INVALID_ARTIFACT_LOCATOR,
            "cannot infer artifact store root from run manifest path",
        )
    return resolved.parents[2]
