from __future__ import annotations

import json
from pathlib import Path

from deltatorrent.benchmark.fault_profiles import FaultProfile
from deltatorrent.benchmark.network_profiles import NetworkProfile, simulate

ROOT = Path(__file__).parents[3]
FIXTURE = ROOT / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json"


def artifacts() -> dict[str, object]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = document["artifacts"]
    assert isinstance(result, dict)
    return result


def test_network_trace_is_deterministic_and_bounded() -> None:
    value = artifacts()["network_profile"]
    assert isinstance(value, dict)
    profile = NetworkProfile.from_dict(value["value"])

    first = simulate(profile, 100)
    second = simulate(profile, 100)

    assert first == second
    assert len(first) == 100
    assert all(event.delay_ms >= 0 for event in first)


def test_fault_trace_has_unique_ordered_events() -> None:
    value = artifacts()["fault_profile"]
    assert isinstance(value, dict)
    profile = FaultProfile.from_dict(value["value"])

    assert [item.event_id for item in profile.events] == [
        "worker-loss-10pct",
        "validator-restart",
    ]
    assert all(item.assumptions_hold for item in profile.events)
