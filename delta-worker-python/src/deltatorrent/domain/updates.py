"""Raw local-delta, terminal completion and normalized-candidate contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Self

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID
from deltatorrent.domain.manifests import ArtifactRef

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_PARAMETER_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,255}$")
_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_PRODUCER_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
_FP32_BITS = re.compile(r"^[0-9a-f]{8}$")
_FP64_BITS = re.compile(r"^[0-9a-f]{16}$")
_SAFETENSORS_MEDIA_TYPE = "application/vnd.safetensors"


def _invalid_completion(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_LOCAL_COMPLETION, message, details)


def _invalid_candidate(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_CONTRIBUTION_CANDIDATE, message, details)


def _content_id(value: object, field: str, *, candidate: bool = False) -> str:
    if not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None:
        factory = _invalid_candidate if candidate else _invalid_completion
        raise factory("CONTENT_ID_INVALID", field=field)
    return value


def _identifier(value: object, field: str, *, candidate: bool = False) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        factory = _invalid_candidate if candidate else _invalid_completion
        raise factory("IDENTIFIER_INVALID", field=field)
    return value


def _non_negative(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _invalid_completion("COUNTER_INVALID", field=field)
    return value


def _positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _invalid_completion("POSITIVE_INTEGER_REQUIRED", field=field)
    return value


def _tensor_order(value: object, *, candidate: bool = False) -> tuple[str, ...]:
    factory = _invalid_candidate if candidate else _invalid_completion
    if (
        not isinstance(value, tuple)
        or not value
        or any(
            not isinstance(item, str) or _PARAMETER_NAME.fullmatch(item) is None for item in value
        )
        or tuple(sorted(value)) != value
        or len(set(value)) != len(value)
    ):
        raise factory("TENSOR_ORDER_INVALID")
    return value


class CompletionStatus(StrEnum):
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CompletionReason(StrEnum):
    CANCELLED = "CANCELLED"
    DATA_EXHAUSTED = "DATA_EXHAUSTED"
    DEADLINE = "DEADLINE"
    EXACT_H = "EXACT_H"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"
    NON_FINITE = "NON_FINITE"
    OOM = "OOM"


@dataclass(frozen=True, slots=True)
class NumericalSummary:
    all_finite: bool
    max_abs_fp32_bits: str | None
    global_l2_norm_fp64_bits: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.all_finite, bool):
            raise _invalid_completion("NUMERICAL_FINITE_FLAG_INVALID")
        if self.max_abs_fp32_bits is not None and (
            not isinstance(self.max_abs_fp32_bits, str)
            or _FP32_BITS.fullmatch(self.max_abs_fp32_bits) is None
        ):
            raise _invalid_completion("MAX_ABS_BITS_INVALID")
        if self.global_l2_norm_fp64_bits is not None and (
            not isinstance(self.global_l2_norm_fp64_bits, str)
            or _FP64_BITS.fullmatch(self.global_l2_norm_fp64_bits) is None
        ):
            raise _invalid_completion("GLOBAL_L2_BITS_INVALID")

    def to_dict(self) -> dict[str, object]:
        return {
            "all_finite": self.all_finite,
            "global_l2_norm_fp64_bits": self.global_l2_norm_fp64_bits,
            "max_abs_fp32_bits": self.max_abs_fp32_bits,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        if set(value) != {
            "all_finite",
            "global_l2_norm_fp64_bits",
            "max_abs_fp32_bits",
        }:
            raise _invalid_completion("NUMERICAL_SUMMARY_FIELDS_INVALID")
        try:
            return cls(
                all_finite=value["all_finite"],
                global_l2_norm_fp64_bits=value["global_l2_norm_fp64_bits"],
                max_abs_fp32_bits=value["max_abs_fp32_bits"],
            )
        except TypeError as exc:
            raise _invalid_completion("NUMERICAL_SUMMARY_TYPES_INVALID") from exc


@dataclass(frozen=True, slots=True)
class ResourceSummary:
    peak_memory_bytes: int
    wall_time_ms: int

    def __post_init__(self) -> None:
        _non_negative(self.peak_memory_bytes, "peak_memory_bytes")
        _non_negative(self.wall_time_ms, "wall_time_ms")

    def to_dict(self) -> dict[str, int]:
        return {
            "peak_memory_bytes": self.peak_memory_bytes,
            "wall_time_ms": self.wall_time_ms,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        if set(value) != {"peak_memory_bytes", "wall_time_ms"}:
            raise _invalid_completion("RESOURCE_SUMMARY_FIELDS_INVALID")
        try:
            return cls(
                peak_memory_bytes=value["peak_memory_bytes"],
                wall_time_ms=value["wall_time_ms"],
            )
        except TypeError as exc:
            raise _invalid_completion("RESOURCE_SUMMARY_TYPES_INVALID") from exc


@dataclass(frozen=True, slots=True)
class LocalDelta:
    ticket_id: str
    ticket_fingerprint: str
    parent_model_id: str
    parameter_schema_id: str
    artifact: ArtifactRef
    tensor_order: tuple[str, ...]
    sign_convention: str = "PARENT_MINUS_FINAL"
    storage_dtype: str = "float32"

    def __post_init__(self) -> None:
        _identifier(self.ticket_id, "ticket_id")
        _content_id(self.ticket_fingerprint, "ticket_fingerprint")
        _content_id(self.parent_model_id, "parent_model_id")
        _content_id(self.parameter_schema_id, "parameter_schema_id")
        if not isinstance(self.artifact, ArtifactRef):
            raise _invalid_completion("LOCAL_DELTA_ARTIFACT_INVALID")
        if (
            self.artifact.schema_id != "SCHEMA-SAFETENSORS-V1"
            or self.artifact.media_type != _SAFETENSORS_MEDIA_TYPE
        ):
            raise _invalid_completion("LOCAL_DELTA_FORMAT_UNSAFE")
        _tensor_order(self.tensor_order)
        if self.sign_convention != "PARENT_MINUS_FINAL":
            raise _invalid_completion("LOCAL_DELTA_SIGN_INVALID")
        if self.storage_dtype != "float32":
            raise _invalid_completion("LOCAL_DELTA_DTYPE_INVALID")

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact": self.artifact.to_dict(),
            "parameter_schema_id": self.parameter_schema_id,
            "parent_model_id": self.parent_model_id,
            "sign_convention": self.sign_convention,
            "storage_dtype": self.storage_dtype,
            "tensor_order": list(self.tensor_order),
            "ticket_fingerprint": self.ticket_fingerprint,
            "ticket_id": self.ticket_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise _invalid_completion("LOCAL_DELTA_FIELDS_INVALID")
        artifact = value["artifact"]
        tensor_order = value["tensor_order"]
        if not isinstance(artifact, dict) or not isinstance(tensor_order, list):
            raise _invalid_completion("LOCAL_DELTA_COLLECTION_FIELDS_INVALID")
        try:
            return cls(
                artifact=ArtifactRef.from_dict(artifact),
                parameter_schema_id=value["parameter_schema_id"],
                parent_model_id=value["parent_model_id"],
                sign_convention=value["sign_convention"],
                storage_dtype=value["storage_dtype"],
                tensor_order=tuple(tensor_order),
                ticket_fingerprint=value["ticket_fingerprint"],
                ticket_id=value["ticket_id"],
            )
        except TypeError as exc:
            raise _invalid_completion("LOCAL_DELTA_TYPES_INVALID") from exc


@dataclass(frozen=True, slots=True)
class LocalRoundCompletion:
    ticket_id: str
    domain_id: str
    worker_id: str
    ticket_fingerprint: str
    data_id: str
    data_range_start: int
    data_range_end: int
    parent_model_id: str
    parameter_schema_id: str
    optimizer_profile_id: str
    arithmetic_profile_id: str
    batch_budget: int
    step_budget: int
    deterministic_seed: int
    logical_deadline_ms: int
    effective_steps: int
    micro_steps: int
    processed_tokens: int
    cursor_start: int
    cursor_end: int
    status: CompletionStatus
    reason: CompletionReason
    candidate_eligible: bool
    local_delta: LocalDelta | None
    failure_code: str | None
    numerical_summary: NumericalSummary
    resource_summary: ResourceSummary
    producer_version: str
    formal_semantics_id: str = FORMAL_SEMANTICS_ID
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _identifier(self.ticket_id, "ticket_id")
        _identifier(self.domain_id, "domain_id")
        _identifier(self.worker_id, "worker_id")
        _content_id(self.ticket_fingerprint, "ticket_fingerprint")
        _content_id(self.data_id, "data_id")
        _content_id(self.parent_model_id, "parent_model_id")
        _content_id(self.parameter_schema_id, "parameter_schema_id")
        _content_id(self.optimizer_profile_id, "optimizer_profile_id")
        _content_id(self.arithmetic_profile_id, "arithmetic_profile_id")
        _positive(self.batch_budget, "batch_budget")
        _positive(self.step_budget, "step_budget")
        _non_negative(self.deterministic_seed, "deterministic_seed")
        _positive(self.logical_deadline_ms, "logical_deadline_ms")
        for field in (
            "data_range_start",
            "data_range_end",
            "effective_steps",
            "micro_steps",
            "processed_tokens",
            "cursor_start",
            "cursor_end",
        ):
            _non_negative(getattr(self, field), field)
        if (
            self.data_range_end <= self.data_range_start
            or self.cursor_start != self.data_range_start
            or self.cursor_end < self.cursor_start
            or self.cursor_end > self.data_range_end
            or self.effective_steps > self.step_budget
        ):
            raise _invalid_completion("COMPLETION_COUNTER_RELATION_INVALID")
        if not isinstance(self.status, CompletionStatus) or not isinstance(
            self.reason, CompletionReason
        ):
            raise _invalid_completion("COMPLETION_ENUM_INVALID")
        complete = (
            self.status is CompletionStatus.COMPLETED
            and self.reason is CompletionReason.EXACT_H
            and self.effective_steps == self.step_budget
        )
        if self.candidate_eligible is not complete:
            raise _invalid_completion("COMPLETION_ELIGIBILITY_INVALID")
        allowed_reasons = {
            CompletionStatus.CANCELLED: {CompletionReason.CANCELLED},
            CompletionStatus.COMPLETED: {CompletionReason.EXACT_H},
            CompletionStatus.FAILED: {
                CompletionReason.DATA_EXHAUSTED,
                CompletionReason.DEADLINE,
                CompletionReason.INTERNAL_FAILURE,
                CompletionReason.NON_FINITE,
                CompletionReason.OOM,
            },
        }
        if self.reason not in allowed_reasons[self.status]:
            raise _invalid_completion("COMPLETION_STATUS_REASON_INVALID")
        if complete:
            if not isinstance(self.local_delta, LocalDelta) or self.failure_code is not None:
                raise _invalid_completion("COMPLETION_SUCCESS_ARTIFACT_INVALID")
            if (
                self.local_delta.ticket_id != self.ticket_id
                or self.local_delta.ticket_fingerprint != self.ticket_fingerprint
                or self.local_delta.parent_model_id != self.parent_model_id
                or self.local_delta.parameter_schema_id != self.parameter_schema_id
            ):
                raise _invalid_completion("COMPLETION_LOCAL_DELTA_LINEAGE_INVALID")
            if (
                not isinstance(self.numerical_summary, NumericalSummary)
                or not self.numerical_summary.all_finite
                or self.numerical_summary.max_abs_fp32_bits is None
                or self.numerical_summary.global_l2_norm_fp64_bits is None
            ):
                raise _invalid_completion("COMPLETION_NUMERICAL_SUMMARY_INVALID")
        elif (
            self.local_delta is not None
            or not isinstance(self.failure_code, str)
            or (_ERROR_CODE.fullmatch(self.failure_code) is None)
        ):
            raise _invalid_completion("INCOMPLETE_CANDIDATE_MUST_BE_ABSENT")
        if not isinstance(self.numerical_summary, NumericalSummary) or not isinstance(
            self.resource_summary, ResourceSummary
        ):
            raise _invalid_completion("COMPLETION_SUMMARY_INVALID")
        if (
            not isinstance(self.producer_version, str)
            or _PRODUCER_VERSION.fullmatch(self.producer_version) is None
        ):
            raise _invalid_completion("COMPLETION_PRODUCER_VERSION_INVALID")
        if self.formal_semantics_id != FORMAL_SEMANTICS_ID:
            raise DeltaError(ErrorCode.FORMAL_SEMANTICS_MISMATCH, "completion semantics mismatch")
        if self.schema_version != "1.0.0":
            raise _invalid_completion("COMPLETION_VERSION_UNSUPPORTED")

    @property
    def fingerprint(self) -> str:
        return sha256_content_id(canonical_json_bytes(self.to_dict()))

    def to_dict(self) -> dict[str, object]:
        return {
            "arithmetic_profile_id": self.arithmetic_profile_id,
            "batch_budget": self.batch_budget,
            "candidate_eligible": self.candidate_eligible,
            "cursor_end": self.cursor_end,
            "cursor_start": self.cursor_start,
            "data_id": self.data_id,
            "data_range_end": self.data_range_end,
            "data_range_start": self.data_range_start,
            "deterministic_seed": self.deterministic_seed,
            "domain_id": self.domain_id,
            "effective_steps": self.effective_steps,
            "failure_code": self.failure_code,
            "formal_semantics_id": self.formal_semantics_id,
            "local_delta": self.local_delta.to_dict() if self.local_delta else None,
            "logical_deadline_ms": self.logical_deadline_ms,
            "micro_steps": self.micro_steps,
            "numerical_summary": self.numerical_summary.to_dict(),
            "optimizer_profile_id": self.optimizer_profile_id,
            "parameter_schema_id": self.parameter_schema_id,
            "parent_model_id": self.parent_model_id,
            "processed_tokens": self.processed_tokens,
            "producer_version": self.producer_version,
            "reason": self.reason.value,
            "schema_version": self.schema_version,
            "status": self.status.value,
            "step_budget": self.step_budget,
            "resource_summary": self.resource_summary.to_dict(),
            "ticket_fingerprint": self.ticket_fingerprint,
            "ticket_id": self.ticket_id,
            "worker_id": self.worker_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise _invalid_completion("COMPLETION_FIELDS_INVALID")
        local_delta = value["local_delta"]
        if local_delta is not None and not isinstance(local_delta, dict):
            raise _invalid_completion("COMPLETION_LOCAL_DELTA_INVALID")
        numerical_summary = value["numerical_summary"]
        resource_summary = value["resource_summary"]
        if not isinstance(numerical_summary, dict) or not isinstance(resource_summary, dict):
            raise _invalid_completion("COMPLETION_SUMMARY_INVALID")
        try:
            return cls(
                arithmetic_profile_id=value["arithmetic_profile_id"],
                batch_budget=value["batch_budget"],
                candidate_eligible=value["candidate_eligible"],
                cursor_end=value["cursor_end"],
                cursor_start=value["cursor_start"],
                data_id=value["data_id"],
                data_range_end=value["data_range_end"],
                data_range_start=value["data_range_start"],
                deterministic_seed=value["deterministic_seed"],
                domain_id=value["domain_id"],
                effective_steps=value["effective_steps"],
                failure_code=value["failure_code"],
                formal_semantics_id=value["formal_semantics_id"],
                local_delta=LocalDelta.from_dict(local_delta) if local_delta else None,
                logical_deadline_ms=value["logical_deadline_ms"],
                micro_steps=value["micro_steps"],
                numerical_summary=NumericalSummary.from_dict(numerical_summary),
                optimizer_profile_id=value["optimizer_profile_id"],
                parameter_schema_id=value["parameter_schema_id"],
                parent_model_id=value["parent_model_id"],
                processed_tokens=value["processed_tokens"],
                producer_version=value["producer_version"],
                reason=CompletionReason(value["reason"]),
                schema_version=value["schema_version"],
                status=CompletionStatus(value["status"]),
                step_budget=value["step_budget"],
                resource_summary=ResourceSummary.from_dict(resource_summary),
                ticket_fingerprint=value["ticket_fingerprint"],
                ticket_id=value["ticket_id"],
                worker_id=value["worker_id"],
            )
        except (TypeError, ValueError) as exc:
            raise _invalid_completion("COMPLETION_TYPES_INVALID") from exc


@dataclass(frozen=True, slots=True)
class NormalizedContributionCandidate:
    ticket_id: str
    domain_id: str
    ticket_fingerprint: str
    completion_id: str
    parent_model_id: str
    parameter_schema_id: str
    optimizer_profile_id: str
    arithmetic_profile_id: str
    effective_steps: int
    step_budget: int
    normalization_denominator: int
    normalized_delta: ArtifactRef
    tensor_order: tuple[str, ...]
    storage_dtype: str = "float32"
    formal_semantics_id: str = FORMAL_SEMANTICS_ID
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _identifier(self.ticket_id, "ticket_id", candidate=True)
        _identifier(self.domain_id, "domain_id", candidate=True)
        for field in (
            "ticket_fingerprint",
            "completion_id",
            "parent_model_id",
            "parameter_schema_id",
            "optimizer_profile_id",
            "arithmetic_profile_id",
        ):
            _content_id(getattr(self, field), field, candidate=True)
        if (
            isinstance(self.effective_steps, bool)
            or not isinstance(self.effective_steps, int)
            or isinstance(self.step_budget, bool)
            or not isinstance(self.step_budget, int)
            or isinstance(self.normalization_denominator, bool)
            or not isinstance(self.normalization_denominator, int)
            or self.effective_steps <= 0
            or self.effective_steps != self.step_budget
            or self.normalization_denominator != self.effective_steps
        ):
            raise _invalid_candidate("CANDIDATE_REQUIRES_A_EQUALS_H")
        if (
            not isinstance(self.normalized_delta, ArtifactRef)
            or self.normalized_delta.schema_id != "SCHEMA-SAFETENSORS-V1"
            or self.normalized_delta.media_type != _SAFETENSORS_MEDIA_TYPE
        ):
            raise _invalid_candidate("CANDIDATE_TENSOR_ARTIFACT_INVALID")
        _tensor_order(self.tensor_order, candidate=True)
        if self.storage_dtype != "float32":
            raise _invalid_candidate("CANDIDATE_DTYPE_INVALID")
        if self.formal_semantics_id != FORMAL_SEMANTICS_ID:
            raise DeltaError(ErrorCode.FORMAL_SEMANTICS_MISMATCH, "candidate semantics mismatch")
        if self.schema_version != "1.0.0":
            raise _invalid_candidate("CANDIDATE_VERSION_UNSUPPORTED")

    def to_dict(self) -> dict[str, object]:
        return {
            "arithmetic_profile_id": self.arithmetic_profile_id,
            "completion_id": self.completion_id,
            "domain_id": self.domain_id,
            "effective_steps": self.effective_steps,
            "formal_semantics_id": self.formal_semantics_id,
            "normalization_denominator": self.normalization_denominator,
            "normalized_delta": self.normalized_delta.to_dict(),
            "optimizer_profile_id": self.optimizer_profile_id,
            "parameter_schema_id": self.parameter_schema_id,
            "parent_model_id": self.parent_model_id,
            "schema_version": self.schema_version,
            "step_budget": self.step_budget,
            "storage_dtype": self.storage_dtype,
            "tensor_order": list(self.tensor_order),
            "ticket_fingerprint": self.ticket_fingerprint,
            "ticket_id": self.ticket_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise _invalid_candidate("CANDIDATE_FIELDS_INVALID")
        tensor_order = value["tensor_order"]
        normalized = value["normalized_delta"]
        if not isinstance(tensor_order, list) or not isinstance(normalized, dict):
            raise _invalid_candidate("CANDIDATE_COLLECTION_FIELDS_INVALID")
        try:
            return cls(
                arithmetic_profile_id=value["arithmetic_profile_id"],
                completion_id=value["completion_id"],
                domain_id=value["domain_id"],
                effective_steps=value["effective_steps"],
                formal_semantics_id=value["formal_semantics_id"],
                normalization_denominator=value["normalization_denominator"],
                normalized_delta=ArtifactRef.from_dict(normalized),
                optimizer_profile_id=value["optimizer_profile_id"],
                parameter_schema_id=value["parameter_schema_id"],
                parent_model_id=value["parent_model_id"],
                schema_version=value["schema_version"],
                step_budget=value["step_budget"],
                storage_dtype=value["storage_dtype"],
                tensor_order=tuple(tensor_order),
                ticket_fingerprint=value["ticket_fingerprint"],
                ticket_id=value["ticket_id"],
            )
        except (TypeError, ValueError) as exc:
            raise _invalid_candidate("CANDIDATE_TYPES_INVALID") from exc
