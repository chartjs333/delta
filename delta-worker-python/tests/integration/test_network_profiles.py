from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.adapters.netem.linux_tc import LinuxTcNetem
from deltatorrent.adapters.netem.simulated import SimulatedFaultyStream
from deltatorrent.cli.main import main
from deltatorrent.domain.network import FaultKind, NetworkProfile

ROOT = Path(__file__).resolve().parents[3]
PROFILE = ROOT / "configs" / "netem" / "wan-smoke-v1.json"


def frames() -> tuple[tuple[int, bytes], ...]:
    return tuple((index * 7, f"frame-{index}".encode()) for index in range(8))


def test_fault_schedule_is_seeded_and_reproducible() -> None:
    profile = NetworkProfile.from_json_file(PROFILE)
    first = SimulatedFaultyStream(profile).transmit_stream(frames())
    second = SimulatedFaultyStream(profile).transmit_stream(frames())
    assert first == second
    assert {event for item in first for event in item.events} >= {
        FaultKind.DELAY,
        FaultKind.DELIVER,
        FaultKind.DISCONNECT,
    }


def test_loss_reorder_disconnect_and_deadline_are_bounded() -> None:
    base = NetworkProfile.from_json_file(PROFILE)
    dropped = SimulatedFaultyStream(
        replace(base, loss_ppm=1_000_000, reorder_ppm=0, disconnect_windows=())
    ).transmit(b"x", sequence=0, sent_at_ms=0)
    assert dropped.events == (FaultKind.DROP,)

    reordered = SimulatedFaultyStream(
        replace(base, loss_ppm=0, reorder_ppm=1_000_000, disconnect_windows=())
    ).transmit(b"x", sequence=0, sent_at_ms=0)
    assert FaultKind.REORDER in reordered.events

    timed_out = SimulatedFaultyStream(
        replace(
            base,
            latency_ms=100,
            jitter_ms=0,
            loss_ppm=0,
            reorder_ppm=0,
            disconnect_windows=(),
            operation_deadline_ms=10,
        )
    ).transmit(b"x", sequence=0, sent_at_ms=0)
    assert timed_out.events == (FaultKind.DELAY, FaultKind.TIMEOUT)
    assert timed_out.delivered_at_ms is None


def test_netem_smoke_cli_is_machine_readable_and_repeatable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["netem", "smoke", str(PROFILE)]) == 0
    first = json.loads(capsys.readouterr().out)
    assert main(["netem", "smoke", str(PROFILE)]) == 0
    second = json.loads(capsys.readouterr().out)
    assert first == second
    assert first["status"] == "PASS"
    assert first["schedule_id"].startswith("sha256:")


def test_optional_linux_tc_adapter_always_cleans_up(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = NetworkProfile.from_json_file(PROFILE)
    commands: list[list[str]] = []

    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("shutil.which", lambda name: "/sbin/tc" if name == "tc" else None)
    monkeypatch.setattr("os.geteuid", lambda: 0, raising=False)

    def runner(command: list[str]) -> int:
        commands.append(command)
        return 0

    with pytest.raises(RuntimeError, match="inside"):
        with LinuxTcNetem("lo", profile, runner):
            raise RuntimeError("inside")
    assert commands[0][:4] == ["tc", "qdisc", "replace", "dev"]
    assert commands[-1] == ["tc", "qdisc", "del", "dev", "lo", "root"]
