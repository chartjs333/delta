"""Cleanup-safe optional Linux tc/netem adapter."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from collections.abc import Callable
from types import TracebackType

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.network import NetworkProfile

CommandRunner = Callable[[list[str]], int]


class LinuxTcNetem:
    def __init__(
        self,
        interface: str,
        profile: NetworkProfile,
        runner: CommandRunner | None = None,
    ) -> None:
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", interface) is None:
            raise ValueError("NETEM_INTERFACE_INVALID")
        self.interface = interface
        self.profile = profile
        self.runner = runner or self._run
        self.active = False

    def __enter__(self) -> LinuxTcNetem:
        if platform.system() != "Linux":
            raise DeltaError(ErrorCode.NETEM_PLATFORM_UNSUPPORTED, "tc/netem requires Linux")
        if shutil.which("tc") is None:
            raise DeltaError(ErrorCode.NETEM_TC_UNAVAILABLE, "tc executable not found")
        if not hasattr(os, "geteuid") or os.geteuid() != 0:
            raise DeltaError(ErrorCode.NETEM_PRIVILEGE_REQUIRED, "tc/netem requires root")
        command = [
            "tc",
            "qdisc",
            "replace",
            "dev",
            self.interface,
            "root",
            "netem",
            "delay",
            f"{self.profile.latency_ms}ms",
            f"{self.profile.jitter_ms}ms",
            "loss",
            f"{self.profile.loss_ppm / 10_000:.4f}%",
            "rate",
            f"{self.profile.bandwidth_bytes_per_second * 8}bit",
        ]
        if self.runner(command) != 0:
            raise RuntimeError("NETEM_APPLY_FAILED")
        self.active = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.active:
            self.runner(["tc", "qdisc", "del", "dev", self.interface, "root"])
            self.active = False

    @staticmethod
    def _run(command: list[str]) -> int:
        return subprocess.run(command, check=False, timeout=10).returncode
