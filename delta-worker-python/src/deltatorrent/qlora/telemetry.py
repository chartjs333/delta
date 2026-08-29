"""Bounded operational telemetry without certificate authority."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_METRIC = re.compile(r"^[a-z0-9_.-]{1,128}$")


@dataclass(slots=True)
class QloraTelemetry:
    counters: dict[str, int] = field(default_factory=dict)

    def add(self, metric: str, value: int) -> None:
        if _METRIC.fullmatch(metric) is None or value < 0:
            raise ValueError("QLORA_TELEMETRY_VALUE_INVALID")
        self.counters[metric] = self.counters.get(metric, 0) + value

    def snapshot(self) -> dict[str, int]:
        return dict(sorted(self.counters.items()))
