"""Immutable domain-pure work-ticket contract."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID
from deltatorrent.domain.manifests import ArtifactRef

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_WORK_TICKET, message, details)


def _positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _invalid("WORK_TICKET_POSITIVE_INTEGER_REQUIRED", field=field)
    return value


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _invalid("WORK_TICKET_IDENTIFIER_INVALID", field=field)
    return value


def _content_id(value: object, field: str) -> str:
    if not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None:
        raise _invalid("WORK_TICKET_CONTENT_ID_INVALID", field=field)
    return value


@dataclass(frozen=True, slots=True)
class DataRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.start, bool)
            or not isinstance(self.start, int)
            or isinstance(self.end, bool)
            or not isinstance(self.end, int)
            or self.start < 0
            or self.end <= self.start
        ):
            raise _invalid("WORK_TICKET_DATA_RANGE_INVALID")

    def to_dict(self) -> dict[str, int]:
        return {"end": self.end, "start": self.start}


@dataclass(frozen=True, slots=True)
class DomainPureWorkTicket:
    ticket_id: str
    domain_id: str
    data: ArtifactRef
    data_range: DataRange
    batch_budget: int
    step_budget: int
    parent_model: ArtifactRef
    parameter_schema_id: str
    optimizer_profile_id: str
    arithmetic_profile_id: str
    deterministic_seed: int
    logical_deadline_ms: int
    formal_semantics_id: str = FORMAL_SEMANTICS_ID
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _identifier(self.ticket_id, "ticket_id")
        _identifier(self.domain_id, "domain_id")
        if not isinstance(self.data, ArtifactRef) or not isinstance(self.parent_model, ArtifactRef):
            raise _invalid("WORK_TICKET_ARTIFACT_REF_INVALID")
        if not isinstance(self.data_range, DataRange):
            raise _invalid("WORK_TICKET_DATA_RANGE_INVALID")
        _positive(self.batch_budget, "batch_budget")
        _positive(self.step_budget, "step_budget")
        _content_id(self.parameter_schema_id, "parameter_schema_id")
        _content_id(self.optimizer_profile_id, "optimizer_profile_id")
        _content_id(self.arithmetic_profile_id, "arithmetic_profile_id")
        if (
            isinstance(self.deterministic_seed, bool)
            or not isinstance(self.deterministic_seed, int)
            or self.deterministic_seed < 0
        ):
            raise _invalid("WORK_TICKET_SEED_INVALID")
        _positive(self.logical_deadline_ms, "logical_deadline_ms")
        if self.formal_semantics_id != FORMAL_SEMANTICS_ID:
            raise DeltaError(ErrorCode.FORMAL_SEMANTICS_MISMATCH, "work-ticket semantics mismatch")
        if self.schema_version != "1.0.0":
            raise _invalid("WORK_TICKET_VERSION_UNSUPPORTED")

    @property
    def fingerprint(self) -> str:
        return sha256_content_id(canonical_json_bytes(self.to_dict()))

    def to_dict(self) -> dict[str, object]:
        return {
            "arithmetic_profile_id": self.arithmetic_profile_id,
            "batch_budget": self.batch_budget,
            "data": self.data.to_dict(),
            "data_range": self.data_range.to_dict(),
            "deterministic_seed": self.deterministic_seed,
            "domain_id": self.domain_id,
            "formal_semantics_id": self.formal_semantics_id,
            "logical_deadline_ms": self.logical_deadline_ms,
            "optimizer_profile_id": self.optimizer_profile_id,
            "parameter_schema_id": self.parameter_schema_id,
            "parent_model": self.parent_model.to_dict(),
            "schema_version": self.schema_version,
            "step_budget": self.step_budget,
            "ticket_id": self.ticket_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise _invalid(
                "WORK_TICKET_FIELDS_INVALID",
                missing=sorted(expected - set(value)),
                unknown=sorted(set(value) - expected),
            )
        data = value["data"]
        data_range = value["data_range"]
        parent = value["parent_model"]
        if not isinstance(data, dict) or not isinstance(parent, dict):
            raise _invalid("WORK_TICKET_ARTIFACT_REF_INVALID")
        if not isinstance(data_range, dict) or set(data_range) != {"end", "start"}:
            raise _invalid("WORK_TICKET_DATA_RANGE_INVALID")
        try:
            return cls(
                arithmetic_profile_id=value["arithmetic_profile_id"],
                batch_budget=value["batch_budget"],
                data=ArtifactRef.from_dict(data),
                data_range=DataRange(start=data_range["start"], end=data_range["end"]),
                deterministic_seed=value["deterministic_seed"],
                domain_id=value["domain_id"],
                formal_semantics_id=value["formal_semantics_id"],
                logical_deadline_ms=value["logical_deadline_ms"],
                optimizer_profile_id=value["optimizer_profile_id"],
                parameter_schema_id=value["parameter_schema_id"],
                parent_model=ArtifactRef.from_dict(parent),
                schema_version=value["schema_version"],
                step_budget=value["step_budget"],
                ticket_id=value["ticket_id"],
            )
        except TypeError as exc:
            raise _invalid("WORK_TICKET_TYPES_INVALID") from exc
