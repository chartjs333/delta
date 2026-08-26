from __future__ import annotations

import json
from pathlib import Path

import pytest
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.network import NetworkProfile

ROOT = Path(__file__).resolve().parents[3]
PROFILE = ROOT / "configs" / "netem" / "wan-smoke-v1.json"


def test_network_profile_round_trips_strict_integer_schema() -> None:
    profile = NetworkProfile.from_json_file(PROFILE)
    assert NetworkProfile.from_mapping(profile.to_dict()) == profile
    assert all(not isinstance(value, float) for value in profile.to_dict().values())


def test_network_profile_rejects_unknown_fields_and_overlapping_disconnects() -> None:
    value = json.loads(PROFILE.read_text(encoding="utf-8"))
    value["unknown"] = 1
    with pytest.raises(DeltaError) as captured:
        NetworkProfile.from_mapping(value)
    assert captured.value.code is ErrorCode.INVALID_NETWORK_PROFILE

    value.pop("unknown")
    value["disconnect_windows"] = [
        {"end_ms": 20, "start_ms": 5},
        {"end_ms": 25, "start_ms": 10},
    ]
    with pytest.raises(DeltaError, match="overlap"):
        NetworkProfile.from_mapping(value)
