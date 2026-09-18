from __future__ import annotations

from copy import deepcopy

import pytest
from deltatorrent.benchmark.process_profiles import (
    ProcessProfileError,
    analyze_process_profiles,
)

SOURCE = "a" * 40


def raw_profile(*, embedded_restart: int = 0, sidecar_restart: int = 500) -> bytes:
    lines = []
    for repetition in range(5):
        lines.append(
            f"PROCESS_PROFILE EMBEDDED_FFM 19 19 {10 + repetition} "
            f"{11 + repetition} {embedded_restart}"
        )
        lines.append(
            f"PROCESS_PROFILE ISOLATED_SIDECAR 16 16 {100 + repetition} "
            f"{110 + repetition} {sidecar_restart + repetition}"
        )
        lines.append("CROSS_LANGUAGE 19 sha256:" + "c" * 64)
    return ("\n".join(lines) + "\n").encode()


def test_process_profiles_select_crash_contained_sidecar() -> None:
    evidence = analyze_process_profiles(
        {25: raw_profile(), 26: raw_profile()}, source_commit=SOURCE
    )

    assert evidence["status"] == "PASS"
    assert evidence["selected_profile"] == "ISOLATED_SIDECAR"
    assert evidence["pilot_selection_rule"].startswith("REQUIRE_CRASH_CONTAINMENT")
    assert len(evidence["summaries"]) == 4
    assert len(evidence["artifacts"]) == 2


@pytest.mark.parametrize(
    "measurements,reason",
    [
        ({25: raw_profile()}, "PROCESS_PROFILE_JDK_SET_INVALID"),
        (
            {25: raw_profile(), 26: raw_profile().replace(b" 19 19 ", b" 19 18 ", 1)},
            "PROCESS_PROFILE_MEASUREMENT_INVALID",
        ),
        (
            {25: raw_profile(), 26: raw_profile(embedded_restart=1)},
            "PROCESS_PROFILE_MEASUREMENT_INVALID",
        ),
        (
            {25: raw_profile(), 26: raw_profile(sidecar_restart=0)},
            "PROCESS_PROFILE_MEASUREMENT_INVALID",
        ),
        (
            {25: raw_profile(), 26: b"\n".join(raw_profile().splitlines()[:-1]) + b"\n"},
            "PROCESS_PROFILE_CROSS_LANGUAGE_INVALID",
        ),
        (
            {
                25: raw_profile(),
                26: raw_profile().replace(b"CROSS_LANGUAGE 19", b"CROSS_LANGUAGE 18", 1),
            },
            "PROCESS_PROFILE_CROSS_LANGUAGE_INVALID",
        ),
    ],
)
def test_process_profile_evidence_fails_closed(measurements: dict[int, bytes], reason: str) -> None:
    with pytest.raises(ProcessProfileError, match=reason):
        analyze_process_profiles(deepcopy(measurements), source_commit=SOURCE)
