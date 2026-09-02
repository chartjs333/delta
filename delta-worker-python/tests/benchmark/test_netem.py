from __future__ import annotations

import json
from pathlib import Path

import pytest
from deltatorrent.benchmark.netem import NetemError, plan
from deltatorrent.benchmark.network_profiles import NetworkProfile

ROOT = Path(__file__).resolve().parents[3]
PROFILES = ROOT / "configs/benchmark/networks-v1.json"


def profiles() -> tuple[NetworkProfile, ...]:
    values = json.loads(PROFILES.read_text(encoding="utf-8"))["profiles"]
    return tuple(NetworkProfile.from_dict(value) for value in values)


def test_all_primary_profiles_have_exact_netem_plans() -> None:
    planned = tuple(plan(profile, "delta0") for profile in profiles())

    assert [item.profile_id for item in planned] == [
        "lan-control",
        "wan-regional",
        "wan-intercontinental",
    ]
    assert planned[0].apply[8:10] == ("500us", "0us")
    assert planned[1].apply[11] == "0.1000%"
    assert planned[1].apply[13] == "0.0100%"
    assert planned[1].apply[15] == "0.0500%"
    assert planned[2].apply[-1] == "25000kbit"
    assert planned[0].disconnect is None
    assert planned[1].disconnect is not None
    assert planned[1].disconnect_duration_ms == 2_000
    assert planned[1].restore == planned[1].apply
    assert planned[1].clear == ("tc", "qdisc", "delete", "dev", "delta0", "root")


def test_netem_executes_argv_without_a_shell_string() -> None:
    observed: list[tuple[str, ...]] = []
    selected = plan(profiles()[1], "delta0")

    selected.execute(observed.append)

    assert observed == [selected.apply]


@pytest.mark.parametrize("interface", ("", "../eth0", "eth0;reboot", "eth 0"))
def test_netem_rejects_unsafe_interface(interface: str) -> None:
    with pytest.raises(NetemError, match="NETEM_INTERFACE_INVALID"):
        plan(profiles()[0], interface)
