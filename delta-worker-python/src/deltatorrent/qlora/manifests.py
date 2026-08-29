"""Fail-closed model provenance and repository-safe import contracts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
_FIELDS: Final = {
    "access_policy",
    "approved_ephemeral_caches",
    "config_hash",
    "formal_semantics_id",
    "license",
    "model_repository",
    "model_revision",
    "persistent_base_parameters",
    "persistent_protocol_buffers",
    "redistribution_allowed",
    "schema_version",
    "tokenizer_hash",
    "type_name",
    "weight_shard_ids",
}
_UNSAFE_SUFFIXES: Final = {".bin", ".joblib", ".pickle", ".pkl", ".pt", ".pth"}


class ManifestError(ValueError):
    """Stable rejection for an unsafe or ambiguous model import."""


def _fail(code: str) -> ManifestError:
    return ManifestError(code)


def _strings(value: object, code: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise _fail(code)
    result = tuple(value)
    if len(set(result)) != len(result):
        raise _fail(f"{code}_DUPLICATE")
    return result


@dataclass(frozen=True, slots=True)
class BaseModelManifest:
    repository: str
    revision: str
    license_id: str
    redistribution_allowed: bool
    tokenizer_hash: str
    config_hash: str
    weight_shard_ids: tuple[str, ...]
    persistent_base_parameters: tuple[str, ...]
    persistent_protocol_buffers: tuple[str, ...]
    approved_ephemeral_caches: tuple[str, ...]
    raw: dict[str, Any]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> BaseModelManifest:
        if set(value) != _FIELDS:
            raise _fail("BASE_MANIFEST_FIELDS_INVALID")
        if value["type_name"] != "BASE_MODEL_MANIFEST" or value["schema_version"] != "1.0.0":
            raise _fail("BASE_MANIFEST_VERSION_INVALID")
        if value["formal_semantics_id"] != _FORMAL_ID:
            raise _fail("FORMAL_SEMANTICS_MISMATCH")
        if value["access_policy"] != "PUBLIC_NO_TOKEN":
            raise _fail("BASE_ACCESS_POLICY_REQUIRES_TOKEN")
        repository = value["model_repository"]
        revision = value["model_revision"]
        license_id = value["license"]
        if not all(isinstance(item, str) and item for item in (repository, revision, license_id)):
            raise _fail("BASE_PROVENANCE_INVALID")
        if revision.lower() in {"main", "master", "latest", "head"}:
            raise _fail("BASE_REVISION_NOT_PINNED")
        if not isinstance(value["redistribution_allowed"], bool):
            raise _fail("BASE_REDISTRIBUTION_POLICY_INVALID")
        content_ids = (
            value["tokenizer_hash"],
            value["config_hash"],
            *_strings(value["weight_shard_ids"], "BASE_WEIGHT_SHARDS_INVALID"),
        )
        if any(
            not isinstance(item, str) or _CONTENT_ID.fullmatch(item) is None
            for item in content_ids
        ):
            raise _fail("BASE_CONTENT_ID_INVALID")
        base = _strings(value["persistent_base_parameters"], "BASE_PARAMETERS_INVALID")
        buffers = _strings(value["persistent_protocol_buffers"], "BASE_BUFFERS_INVALID")
        caches = _strings(value["approved_ephemeral_caches"], "BASE_CACHES_INVALID")
        if not base or set(base) & set(buffers) or (set(base) | set(buffers)) & set(caches):
            raise _fail("BASE_STATE_PARTITION_INVALID")
        return cls(
            repository=repository,
            revision=revision,
            license_id=license_id,
            redistribution_allowed=value["redistribution_allowed"],
            tokenizer_hash=value["tokenizer_hash"],
            config_hash=value["config_hash"],
            weight_shard_ids=tuple(content_ids[2:]),
            persistent_base_parameters=base,
            persistent_protocol_buffers=buffers,
            approved_ephemeral_caches=caches,
            raw=dict(value),
        )

    @property
    def content_id(self) -> str:
        return sha256_content_id(canonical_json_bytes(self.raw))


@dataclass(frozen=True, slots=True)
class ImportRequest:
    manifest: BaseModelManifest
    repository_root: Path
    config_path: Path
    tokenizer_path: Path
    weight_paths: tuple[Path, ...]
    local_files_only: bool = True
    trust_remote_code: bool = False
    use_safetensors: bool = True


def _safe_child(root: Path, relative: object, code: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise _fail(code)
    path = (root / relative).resolve(strict=True)
    if root not in path.parents or path.is_symlink() or not path.is_file():
        raise _fail(code)
    if path.suffix.lower() in _UNSAFE_SUFFIXES:
        raise _fail("UNSAFE_MODEL_SERIALIZATION")
    return path


def load_import_request(path: Path, *, allowed_root: Path) -> ImportRequest:
    root = allowed_root.resolve(strict=True)
    manifest_path = path.resolve(strict=True)
    if root not in manifest_path.parents or manifest_path.is_symlink():
        raise _fail("IMPORT_PATH_OUTSIDE_ALLOWED_ROOT")
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail("IMPORT_MANIFEST_JSON_INVALID") from exc
    if not isinstance(value, dict) or set(value) != {"base_manifest", "files", "import_policy"}:
        raise _fail("IMPORT_MANIFEST_FIELDS_INVALID")
    policy = value["import_policy"]
    expected_policy = {
        "local_files_only": True,
        "trust_remote_code": False,
        "use_safetensors": True,
    }
    if policy != expected_policy:
        raise _fail("UNSAFE_IMPORT_POLICY")
    files = value["files"]
    if not isinstance(files, dict) or set(files) != {"config", "tokenizer", "weights"}:
        raise _fail("IMPORT_FILES_INVALID")
    weights = _strings(files["weights"], "IMPORT_WEIGHTS_INVALID")
    repository_root = manifest_path.parent.resolve()
    request = ImportRequest(
        manifest=BaseModelManifest.from_mapping(value["base_manifest"]),
        repository_root=repository_root,
        config_path=_safe_child(repository_root, files["config"], "IMPORT_CONFIG_INVALID"),
        tokenizer_path=_safe_child(repository_root, files["tokenizer"], "IMPORT_TOKENIZER_INVALID"),
        weight_paths=tuple(
            _safe_child(repository_root, item, "IMPORT_WEIGHT_INVALID") for item in weights
        ),
    )
    actual_ids = tuple(sha256_content_id(item.read_bytes()) for item in request.weight_paths)
    if actual_ids != request.manifest.weight_shard_ids:
        raise _fail("IMPORT_WEIGHT_HASH_MISMATCH")
    if sha256_content_id(request.config_path.read_bytes()) != request.manifest.config_hash:
        raise _fail("IMPORT_CONFIG_HASH_MISMATCH")
    if sha256_content_id(request.tokenizer_path.read_bytes()) != request.manifest.tokenizer_hash:
        raise _fail("IMPORT_TOKENIZER_HASH_MISMATCH")
    return request
