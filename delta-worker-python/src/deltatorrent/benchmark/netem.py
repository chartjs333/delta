"""Optional Linux tc/netem adapter for an already validated network profile."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Protocol

from deltatorrent.benchmark.network_profiles import NetworkProfile

_INTERFACE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")


class NetemError(ValueError):
    """Stable tc/netem planning or execution error."""


class CommandRunner(Protocol):
    def __call__(self, command: tuple[str, ...]) -> None: ...


def _percent(ppm: int) -> str:
    return f"{ppm // 10_000}.{ppm % 10_000:04d}%"


@dataclass(frozen=True, slots=True)
class NetemPlan:
    interface: str
    profile_id: str
    apply: tuple[str, ...]
    disconnect: tuple[str, ...] | None
    disconnect_duration_ms: int
    restore: tuple[str, ...]
    clear: tuple[str, ...]

    def execute(self, runner: CommandRunner | None = None) -> None:
        execute = runner or _run
        execute(self.apply)


def _run(command: tuple[str, ...]) -> None:
    try:
        subprocess.run(command, check=True, shell=False)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise NetemError("NETEM_COMMAND_FAILED") from exc


def plan(profile: NetworkProfile, interface: str, *, tc_binary: str = "tc") -> NetemPlan:
    if _INTERFACE.fullmatch(interface) is None:
        raise NetemError("NETEM_INTERFACE_INVALID")
    if not tc_binary or any(character.isspace() for character in tc_binary):
        raise NetemError("NETEM_BINARY_INVALID")
    normal = (
        tc_binary,
        "qdisc",
        "replace",
        "dev",
        interface,
        "root",
        "netem",
        "delay",
        f"{profile.rtt_ms * 500}us",
        f"{profile.jitter_ms * 1000}us",
        "loss",
        _percent(profile.loss_ppm),
        "duplicate",
        _percent(profile.duplication_ppm),
        "reorder",
        _percent(profile.reordering_ppm),
        "rate",
        f"{profile.bandwidth_kbps}kbit",
    )
    disconnect = (
        tc_binary,
        "qdisc",
        "replace",
        "dev",
        interface,
        "root",
        "netem",
        "loss",
        "100.0000%",
    )
    return NetemPlan(
        interface=interface,
        profile_id=profile.profile_id,
        apply=normal,
        disconnect=disconnect if profile.disconnect_ms else None,
        disconnect_duration_ms=profile.disconnect_ms,
        restore=normal,
        clear=(tc_binary, "qdisc", "delete", "dev", interface, "root"),
    )
