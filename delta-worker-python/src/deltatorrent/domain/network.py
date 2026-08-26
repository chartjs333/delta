"""Strict deterministic WAN profile and fault-event contracts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Self

from deltatorrent.domain.errors import DeltaError, ErrorCode


class FaultKind(StrEnum):
    DELAY = "DELAY"
    DELIVER = "DELIVER"
    DISCONNECT = "DISCONNECT"
    DROP = "DROP"
    REORDER = "REORDER"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True, slots=True, order=True)
class DisconnectWindow:
    start_ms: int
    end_ms: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.start_ms, bool)
            or not isinstance(self.start_ms, int)
            or isinstance(self.end_ms, bool)
            or not isinstance(self.end_ms, int)
            or self.start_ms < 0
            or self.end_ms <= self.start_ms
        ):
            raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, "disconnect window is invalid")

    def to_dict(self) -> dict[str, int]:
        return {"end_ms": self.end_ms, "start_ms": self.start_ms}


@dataclass(frozen=True, slots=True)
class NetworkProfile:
    profile_id: str
    latency_ms: int
    jitter_ms: int
    bandwidth_bytes_per_second: int
    loss_ppm: int
    reorder_ppm: int
    disconnect_windows: tuple[DisconnectWindow, ...]
    operation_deadline_ms: int
    seed: int
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0.0" or not self.profile_id or len(self.profile_id) > 128:
            raise DeltaError(
                ErrorCode.INVALID_NETWORK_PROFILE, "network profile identity is invalid"
            )
        non_negative = {
            "jitter_ms": self.jitter_ms,
            "latency_ms": self.latency_ms,
            "loss_ppm": self.loss_ppm,
            "reorder_ppm": self.reorder_ppm,
            "seed": self.seed,
        }
        for name, value in non_negative.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, f"{name} is invalid")
        if (
            isinstance(self.bandwidth_bytes_per_second, bool)
            or not isinstance(self.bandwidth_bytes_per_second, int)
            or self.bandwidth_bytes_per_second <= 0
            or isinstance(self.operation_deadline_ms, bool)
            or not isinstance(self.operation_deadline_ms, int)
            or self.operation_deadline_ms <= 0
            or self.loss_ppm > 1_000_000
            or self.reorder_ppm > 1_000_000
        ):
            raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, "network bounds are invalid")
        if tuple(sorted(self.disconnect_windows)) != self.disconnect_windows:
            raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, "disconnect windows are not sorted")
        for prior, current in zip(
            self.disconnect_windows, self.disconnect_windows[1:], strict=False
        ):
            if current.start_ms < prior.end_ms:
                raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, "disconnect windows overlap")

    def to_dict(self) -> dict[str, object]:
        return {
            "bandwidth_bytes_per_second": self.bandwidth_bytes_per_second,
            "disconnect_windows": [item.to_dict() for item in self.disconnect_windows],
            "jitter_ms": self.jitter_ms,
            "latency_ms": self.latency_ms,
            "loss_ppm": self.loss_ppm,
            "operation_deadline_ms": self.operation_deadline_ms,
            "profile_id": self.profile_id,
            "reorder_ppm": self.reorder_ppm,
            "schema_version": self.schema_version,
            "seed": self.seed,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Self:
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, "NETWORK_PROFILE_FIELDS_INVALID")
        windows = value["disconnect_windows"]
        if not isinstance(windows, list) or any(
            not isinstance(item, dict) or set(item) != {"end_ms", "start_ms"} for item in windows
        ):
            raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, "DISCONNECT_WINDOWS_INVALID")
        try:
            return cls(
                bandwidth_bytes_per_second=value["bandwidth_bytes_per_second"],
                disconnect_windows=tuple(
                    DisconnectWindow(item["start_ms"], item["end_ms"]) for item in windows
                ),
                jitter_ms=value["jitter_ms"],
                latency_ms=value["latency_ms"],
                loss_ppm=value["loss_ppm"],
                operation_deadline_ms=value["operation_deadline_ms"],
                profile_id=value["profile_id"],
                reorder_ppm=value["reorder_ppm"],
                schema_version=value["schema_version"],
                seed=value["seed"],
            )
        except TypeError as exc:
            raise DeltaError(
                ErrorCode.INVALID_NETWORK_PROFILE, "NETWORK_PROFILE_TYPE_INVALID"
            ) from exc

    @classmethod
    def from_json_file(cls, path: Path) -> Self:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DeltaError(
                ErrorCode.INVALID_NETWORK_PROFILE, "NETWORK_PROFILE_JSON_INVALID"
            ) from exc
        if not isinstance(value, dict):
            raise DeltaError(ErrorCode.INVALID_NETWORK_PROFILE, "NETWORK_PROFILE_ROOT_INVALID")
        return cls.from_mapping(value)
