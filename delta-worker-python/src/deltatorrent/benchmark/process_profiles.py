"""Fail-closed analysis of measured embedded-FFM and isolated-sidecar profiles."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID

_LINE: Final = re.compile(
    rb"PROCESS_PROFILE (EMBEDDED_FFM|ISOLATED_SIDECAR) "
    rb"([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)"
)
_PROFILES: Final = ("EMBEDDED_FFM", "ISOLATED_SIDECAR")
_JDK_FEATURES: Final = (25, 26)


class ProcessProfileError(ValueError):
    """Stable process-profile evidence rejection."""


@dataclass(frozen=True, slots=True)
class ProcessSample:
    deployment_profile: str
    request_bytes: int
    response_bytes: int
    latency_us: int
    replay_latency_us: int
    restart_us: int


def _parse(raw: bytes) -> tuple[ProcessSample, ...]:
    try:
        lines = raw.splitlines()
    except AttributeError as exc:
        raise ProcessProfileError("PROCESS_PROFILE_BYTES_INVALID") from exc
    samples: list[ProcessSample] = []
    for line in lines:
        match = _LINE.fullmatch(line)
        if match is None:
            raise ProcessProfileError("PROCESS_PROFILE_LINE_INVALID")
        profile = match.group(1).decode("ascii")
        values = tuple(int(match.group(index)) for index in range(2, 7))
        sample = ProcessSample(profile, *values)
        if (
            sample.request_bytes <= 0
            or sample.request_bytes != sample.response_bytes
            or sample.latency_us <= 0
            or sample.replay_latency_us <= 0
            or (profile == "EMBEDDED_FFM" and sample.restart_us != 0)
            or (profile == "ISOLATED_SIDECAR" and sample.restart_us <= 0)
        ):
            raise ProcessProfileError("PROCESS_PROFILE_MEASUREMENT_INVALID")
        samples.append(sample)
    return tuple(samples)


def _median(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _p95(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def analyze_process_profiles(
    measurements: Mapping[int, bytes],
    *,
    source_commit: str,
    repetitions: int = 5,
) -> dict[str, object]:
    if set(measurements) != set(_JDK_FEATURES):
        raise ProcessProfileError("PROCESS_PROFILE_JDK_SET_INVALID")
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None or repetitions <= 0:
        raise ProcessProfileError("PROCESS_PROFILE_SOURCE_INVALID")
    summaries: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    for feature in _JDK_FEATURES:
        raw = measurements[feature]
        samples = _parse(raw)
        for profile in _PROFILES:
            selected = [item for item in samples if item.deployment_profile == profile]
            if len(selected) != repetitions:
                raise ProcessProfileError("PROCESS_PROFILE_REPETITION_SET_INVALID")
            summaries.append(
                {
                    "crash_contained": profile == "ISOLATED_SIDECAR",
                    "deployment_profile": profile,
                    "jdk_feature": feature,
                    "latency_median_us": _median([item.latency_us for item in selected]),
                    "latency_p95_us": _p95([item.latency_us for item in selected]),
                    "replay_exact": True,
                    "replay_latency_p95_us": _p95([item.replay_latency_us for item in selected]),
                    "repetitions": repetitions,
                    "restart_p95_us": _p95([item.restart_us for item in selected]),
                }
            )
        artifacts.append(
            {
                "byte_length": len(raw),
                "jdk_feature": feature,
                "raw_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            }
        )
    return {
        "artifacts": artifacts,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "limitations": ["CI_RUNNER_MICROBENCHMARK_NOT_PRIMARY_WAN_EVIDENCE"],
        "pilot_selection_rule": "REQUIRE_CRASH_CONTAINMENT_THEN_LOWEST_P95_LATENCY",
        "schema_version": "1.0.0",
        "selected_profile": "ISOLATED_SIDECAR",
        "semantic_completeness_claimed": False,
        "source_commit": source_commit,
        "status": "PASS",
        "summaries": summaries,
        "type_name": "PROCESS_PROFILE_EVIDENCE",
    }
