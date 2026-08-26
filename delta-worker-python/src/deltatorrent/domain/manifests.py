"""Immutable, runtime-neutral artifact and run manifest domain models."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Self

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID

SCHEMA_VERSION = "1.0.0"
_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_SCHEMA_ID = re.compile(r"^SCHEMA-[A-Z0-9-]+-V[0-9]+$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_MANIFEST, message, details)


def _require_content_id(value: str, field: str) -> None:
    if _CONTENT_ID.fullmatch(value) is None:
        raise DeltaError(ErrorCode.INVALID_CONTENT_ID, f"invalid {field}", {"field": field})


def _require_identifier(value: str, field: str) -> None:
    if _IDENTIFIER.fullmatch(value) is None:
        raise _invalid(f"invalid {field}", field=field)


def _require_locator(value: str) -> None:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
        or str(path) != value
    ):
        raise DeltaError(
            ErrorCode.INVALID_ARTIFACT_LOCATOR,
            "artifact locator must be a normalized relative POSIX path",
            {"locator": value},
        )


def _strict_mapping(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise _invalid(
            f"{label} fields do not match the schema",
            missing=sorted(expected - set(value)),
            unknown=sorted(set(value) - expected),
        )


def _freeze_string_mapping(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    if not value or any(
        not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()
    ):
        raise _invalid(f"{field} must be a non-empty string mapping", field=field)
    return MappingProxyType(dict(sorted(value.items())))


def _freeze_seed_mapping(value: Mapping[str, int]) -> Mapping[str, int]:
    if not value or any(
        not isinstance(key, str) or isinstance(item, bool) or not isinstance(item, int) or item < 0
        for key, item in value.items()
    ):
        raise _invalid("seeds must be a non-empty mapping of non-negative integers")
    return MappingProxyType(dict(sorted(value.items())))


class RunStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    content_id: str
    media_type: str
    schema_id: str
    schema_version: str
    byte_length: int
    locator: str

    def __post_init__(self) -> None:
        _require_content_id(self.content_id, "content_id")
        if not self.media_type or len(self.media_type) > 255:
            raise _invalid("invalid media_type", field="media_type")
        if _SCHEMA_ID.fullmatch(self.schema_id) is None:
            raise DeltaError(ErrorCode.INVALID_SCHEMA_ID, "invalid schema_id")
        if self.schema_version != SCHEMA_VERSION:
            raise _invalid("unsupported schema_version", field="schema_version")
        if (
            isinstance(self.byte_length, bool)
            or not isinstance(self.byte_length, int)
            or self.byte_length < 0
        ):
            raise _invalid("byte_length must be non-negative", field="byte_length")
        _require_locator(self.locator)

    def to_dict(self) -> dict[str, object]:
        return {
            "byte_length": self.byte_length,
            "content_id": self.content_id,
            "locator": self.locator,
            "media_type": self.media_type,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        expected = {
            "byte_length",
            "content_id",
            "locator",
            "media_type",
            "schema_id",
            "schema_version",
        }
        _strict_mapping(value, expected, "ArtifactRef")
        try:
            return cls(
                byte_length=value["byte_length"],
                content_id=value["content_id"],
                locator=value["locator"],
                media_type=value["media_type"],
                schema_id=value["schema_id"],
                schema_version=value["schema_version"],
            )
        except TypeError as exc:
            raise _invalid("ArtifactRef field type is invalid") from exc


@dataclass(frozen=True, slots=True)
class CheckpointManifest:
    run_id: str
    checkpoint_id: str
    step: int
    optimizer_step: int
    processed_tokens: int
    sampler_cursor: int
    boundary: str
    artifacts: tuple[ArtifactRef, ...]
    formal_semantics_id: str = FORMAL_SEMANTICS_ID
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_identifier(self.run_id, "run_id")
        _require_identifier(self.checkpoint_id, "checkpoint_id")
        if self.formal_semantics_id != FORMAL_SEMANTICS_ID:
            raise DeltaError(ErrorCode.FORMAL_SEMANTICS_MISMATCH, "checkpoint semantics mismatch")
        if self.schema_version != SCHEMA_VERSION:
            raise _invalid("unsupported checkpoint schema_version")
        counters = (self.step, self.optimizer_step, self.processed_tokens, self.sampler_cursor)
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in counters
        ):
            raise _invalid("checkpoint counters must be non-negative integers")
        if self.boundary != "OPTIMIZER_STEP":
            raise _invalid("checkpoint boundary must be OPTIMIZER_STEP")
        if (
            not self.artifacts
            or any(not isinstance(item, ArtifactRef) for item in self.artifacts)
            or len({item.content_id for item in self.artifacts}) != len(self.artifacts)
        ):
            raise _invalid("checkpoint artifacts must be non-empty and unique")

    def to_dict(self) -> dict[str, object]:
        return {
            "artifacts": [item.to_dict() for item in self.artifacts],
            "boundary": self.boundary,
            "checkpoint_id": self.checkpoint_id,
            "formal_semantics_id": self.formal_semantics_id,
            "optimizer_step": self.optimizer_step,
            "processed_tokens": self.processed_tokens,
            "run_id": self.run_id,
            "sampler_cursor": self.sampler_cursor,
            "schema_version": self.schema_version,
            "step": self.step,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        expected = {
            "artifacts",
            "boundary",
            "checkpoint_id",
            "formal_semantics_id",
            "optimizer_step",
            "processed_tokens",
            "run_id",
            "sampler_cursor",
            "schema_version",
            "step",
        }
        _strict_mapping(value, expected, "CheckpointManifest")
        artifacts = value["artifacts"]
        if not isinstance(artifacts, list) or any(not isinstance(item, dict) for item in artifacts):
            raise _invalid("checkpoint artifacts must be an array of objects")
        try:
            return cls(
                artifacts=tuple(ArtifactRef.from_dict(item) for item in artifacts),
                boundary=value["boundary"],
                checkpoint_id=value["checkpoint_id"],
                formal_semantics_id=value["formal_semantics_id"],
                optimizer_step=value["optimizer_step"],
                processed_tokens=value["processed_tokens"],
                run_id=value["run_id"],
                sampler_cursor=value["sampler_cursor"],
                schema_version=value["schema_version"],
                step=value["step"],
            )
        except (TypeError, ValueError) as exc:
            raise _invalid("CheckpointManifest field type is invalid") from exc


@dataclass(frozen=True, slots=True)
class RunManifest:
    run_id: str
    status: RunStatus
    config_id: str
    code_revision: str
    dependency_lock_id: str
    dataset_id: str
    model_id: str
    tokenizer_id: str
    processed_tokens: int
    platform: Mapping[str, str]
    seeds: Mapping[str, int]
    artifacts: tuple[ArtifactRef, ...]
    checkpoint_refs: tuple[ArtifactRef, ...] = ()
    failure_code: str | None = None
    formal_semantics_id: str = FORMAL_SEMANTICS_ID
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_identifier(self.run_id, "run_id")
        for field, value in (
            ("config_id", self.config_id),
            ("dependency_lock_id", self.dependency_lock_id),
            ("dataset_id", self.dataset_id),
            ("model_id", self.model_id),
            ("tokenizer_id", self.tokenizer_id),
        ):
            _require_content_id(value, field)
        if self.formal_semantics_id != FORMAL_SEMANTICS_ID:
            raise DeltaError(ErrorCode.FORMAL_SEMANTICS_MISMATCH, "run semantics mismatch")
        if self.schema_version != SCHEMA_VERSION:
            raise _invalid("unsupported run schema_version")
        if not isinstance(self.status, RunStatus):
            raise _invalid("invalid run status")
        if not self.code_revision or len(self.code_revision) > 128:
            raise _invalid("invalid code_revision")
        if (
            isinstance(self.processed_tokens, bool)
            or not isinstance(self.processed_tokens, int)
            or self.processed_tokens < 0
        ):
            raise _invalid("processed_tokens must be non-negative")
        if self.status is RunStatus.COMPLETED and self.failure_code is not None:
            raise _invalid("completed run cannot have failure_code")
        if self.status is RunStatus.FAILED and not self.failure_code:
            raise _invalid("failed run requires failure_code")
        object.__setattr__(self, "platform", _freeze_string_mapping(self.platform, "platform"))
        object.__setattr__(self, "seeds", _freeze_seed_mapping(self.seeds))
        refs = (*self.artifacts, *self.checkpoint_refs)
        if any(not isinstance(item, ArtifactRef) for item in refs) or len(
            {item.content_id for item in refs}
        ) != len(refs):
            raise _invalid("run artifact references must be unique")

    def to_dict(self) -> dict[str, object]:
        return {
            "artifacts": [item.to_dict() for item in self.artifacts],
            "checkpoint_refs": [item.to_dict() for item in self.checkpoint_refs],
            "code_revision": self.code_revision,
            "config_id": self.config_id,
            "dataset_id": self.dataset_id,
            "dependency_lock_id": self.dependency_lock_id,
            "failure_code": self.failure_code,
            "formal_semantics_id": self.formal_semantics_id,
            "model_id": self.model_id,
            "platform": dict(self.platform),
            "processed_tokens": self.processed_tokens,
            "run_id": self.run_id,
            "schema_version": self.schema_version,
            "seeds": dict(self.seeds),
            "status": self.status.value,
            "tokenizer_id": self.tokenizer_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        expected = {
            "artifacts",
            "checkpoint_refs",
            "code_revision",
            "config_id",
            "dataset_id",
            "dependency_lock_id",
            "failure_code",
            "formal_semantics_id",
            "model_id",
            "platform",
            "processed_tokens",
            "run_id",
            "schema_version",
            "seeds",
            "status",
            "tokenizer_id",
        }
        _strict_mapping(value, expected, "RunManifest")
        artifacts = value["artifacts"]
        checkpoints = value["checkpoint_refs"]
        if not isinstance(artifacts, list) or any(not isinstance(item, dict) for item in artifacts):
            raise _invalid("run artifacts must be an array of objects")
        if not isinstance(checkpoints, list) or any(
            not isinstance(item, dict) for item in checkpoints
        ):
            raise _invalid("checkpoint_refs must be an array of objects")
        if not isinstance(value["platform"], dict) or not isinstance(value["seeds"], dict):
            raise _invalid("platform and seeds must be objects")
        try:
            return cls(
                artifacts=tuple(ArtifactRef.from_dict(item) for item in artifacts),
                checkpoint_refs=tuple(ArtifactRef.from_dict(item) for item in checkpoints),
                code_revision=value["code_revision"],
                config_id=value["config_id"],
                dataset_id=value["dataset_id"],
                dependency_lock_id=value["dependency_lock_id"],
                failure_code=value["failure_code"],
                formal_semantics_id=value["formal_semantics_id"],
                model_id=value["model_id"],
                platform=value["platform"],
                processed_tokens=value["processed_tokens"],
                run_id=value["run_id"],
                schema_version=value["schema_version"],
                seeds=value["seeds"],
                status=RunStatus(value["status"]),
                tokenizer_id=value["tokenizer_id"],
            )
        except (TypeError, ValueError) as exc:
            raise _invalid("RunManifest field type is invalid") from exc
