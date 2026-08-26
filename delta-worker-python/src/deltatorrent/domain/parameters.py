"""Canonical runtime-neutral parameter-schema contract."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Self

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.domain.errors import DeltaError, ErrorCode

_PARAMETER_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,255}$")


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_PARAMETER_SCHEMA, message, details)


class LogicalDType(StrEnum):
    BFLOAT16 = "bfloat16"
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    FLOAT64 = "float64"


class FrozenOmissionPolicy(StrEnum):
    INCLUDE_ALL = "INCLUDE_ALL"
    OMIT_FROZEN = "OMIT_FROZEN"


@dataclass(frozen=True, slots=True, order=True)
class ParameterSpec:
    name: str
    shape: tuple[int, ...]
    logical_dtype: LogicalDType
    trainable: bool

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or _PARAMETER_NAME.fullmatch(self.name) is None:
            raise _invalid("PARAMETER_NAME_INVALID")
        if not isinstance(self.logical_dtype, LogicalDType):
            raise _invalid("PARAMETER_DTYPE_INVALID", name=self.name)
        if not isinstance(self.trainable, bool):
            raise _invalid("PARAMETER_TRAINABLE_INVALID", name=self.name)
        if not isinstance(self.shape, tuple) or any(
            isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in self.shape
        ):
            raise _invalid("PARAMETER_SHAPE_INVALID", name=self.name)

    def to_dict(self) -> dict[str, object]:
        return {
            "logical_dtype": self.logical_dtype.value,
            "name": self.name,
            "shape": list(self.shape),
            "trainable": self.trainable,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        if set(value) != {"logical_dtype", "name", "shape", "trainable"}:
            raise _invalid("PARAMETER_FIELDS_INVALID")
        shape = value["shape"]
        if not isinstance(shape, list):
            raise _invalid("PARAMETER_SHAPE_INVALID")
        try:
            return cls(
                logical_dtype=LogicalDType(value["logical_dtype"]),
                name=value["name"],
                shape=tuple(shape),
                trainable=value["trainable"],
            )
        except (TypeError, ValueError) as exc:
            raise _invalid("PARAMETER_TYPES_INVALID") from exc


@dataclass(frozen=True, slots=True)
class ParameterSchema:
    parameters: tuple[ParameterSpec, ...]
    tied_aliases: Mapping[str, str]
    frozen_omission_policy: FrozenOmissionPolicy
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0.0":
            raise _invalid("PARAMETER_SCHEMA_VERSION_UNSUPPORTED")
        if (
            not isinstance(self.parameters, tuple)
            or not self.parameters
            or any(not isinstance(item, ParameterSpec) for item in self.parameters)
        ):
            raise _invalid("PARAMETER_SET_EMPTY_OR_INVALID")
        if tuple(sorted(self.parameters, key=lambda item: item.name)) != self.parameters:
            raise _invalid("PARAMETERS_NOT_CANONICALLY_ORDERED")
        names = {item.name for item in self.parameters}
        if len(names) != len(self.parameters):
            raise _invalid("PARAMETER_NAME_DUPLICATE")
        if not isinstance(self.frozen_omission_policy, FrozenOmissionPolicy):
            raise _invalid("FROZEN_OMISSION_POLICY_INVALID")
        if not isinstance(self.tied_aliases, Mapping):
            raise _invalid("TIED_ALIASES_INVALID")
        aliases = dict(self.tied_aliases)
        if any(
            not isinstance(alias, str)
            or _PARAMETER_NAME.fullmatch(alias) is None
            or not isinstance(owner, str)
            or owner not in names
            or alias in names
            for alias, owner in aliases.items()
        ):
            raise _invalid("TIED_ALIAS_INVALID")
        object.__setattr__(self, "tied_aliases", MappingProxyType(dict(sorted(aliases.items()))))

    @property
    def fingerprint(self) -> str:
        return sha256_content_id(canonical_json_bytes(self.to_dict()))

    def to_dict(self) -> dict[str, object]:
        return {
            "frozen_omission_policy": self.frozen_omission_policy.value,
            "parameters": [item.to_dict() for item in self.parameters],
            "schema_version": self.schema_version,
            "tied_aliases": dict(self.tied_aliases),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        if set(value) != {
            "frozen_omission_policy",
            "parameters",
            "schema_version",
            "tied_aliases",
        }:
            raise _invalid("PARAMETER_SCHEMA_FIELDS_INVALID")
        parameters = value["parameters"]
        aliases = value["tied_aliases"]
        if not isinstance(parameters, list) or any(
            not isinstance(item, dict) for item in parameters
        ):
            raise _invalid("PARAMETER_SET_INVALID")
        if not isinstance(aliases, dict):
            raise _invalid("TIED_ALIASES_INVALID")
        try:
            return cls(
                frozen_omission_policy=FrozenOmissionPolicy(value["frozen_omission_policy"]),
                parameters=tuple(ParameterSpec.from_dict(item) for item in parameters),
                schema_version=value["schema_version"],
                tied_aliases=aliases,
            )
        except (TypeError, ValueError) as exc:
            raise _invalid("PARAMETER_SCHEMA_TYPES_INVALID") from exc
