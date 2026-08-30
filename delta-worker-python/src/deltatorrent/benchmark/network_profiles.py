"""Deterministic unprivileged WAN profile simulation without public network access."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


class NetworkProfileError(ValueError):
    """Stable network-profile validation error."""


@dataclass(frozen=True, slots=True)
class NetworkProfile:
    profile_id: str
    rtt_ms: int
    bandwidth_kbps: int
    jitter_ms: int
    loss_ppm: int
    reordering_ppm: int
    duplication_ppm: int
    disconnect_ms: int
    seed: int

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> NetworkProfile:
        required = {
            "bandwidth_kbps",
            "disconnect_ms",
            "duplication_ppm",
            "formal_semantics_id",
            "jitter_ms",
            "loss_ppm",
            "profile_id",
            "reordering_ppm",
            "rtt_ms",
            "schema_version",
            "seed",
            "type_name",
        }
        if set(value) != required or value.get("type_name") != "NETWORK_PROFILE":
            raise NetworkProfileError("NETWORK_PROFILE_FIELDS_INVALID")
        counters = {
            key: value[key]
            for key in (
                "bandwidth_kbps",
                "disconnect_ms",
                "duplication_ppm",
                "jitter_ms",
                "loss_ppm",
                "reordering_ppm",
                "rtt_ms",
                "seed",
            )
        }
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in counters.values()
        ):
            raise NetworkProfileError("NETWORK_PROFILE_COUNTER_INVALID")
        if counters["bandwidth_kbps"] == 0:
            raise NetworkProfileError("NETWORK_PROFILE_BANDWIDTH_INVALID")
        if any(
            counters[key] > 1_000_000 for key in ("loss_ppm", "reordering_ppm", "duplication_ppm")
        ):
            raise NetworkProfileError("NETWORK_PROFILE_PROBABILITY_INVALID")
        profile_id = value["profile_id"]
        if not isinstance(profile_id, str) or not profile_id:
            raise NetworkProfileError("NETWORK_PROFILE_ID_INVALID")
        return cls(profile_id=profile_id, **counters)


@dataclass(frozen=True, slots=True)
class NetworkEvent:
    packet_index: int
    delay_ms: int
    dropped: bool
    duplicated: bool
    reordered: bool


def simulate(profile: NetworkProfile, packet_count: int) -> tuple[NetworkEvent, ...]:
    if packet_count < 0:
        raise NetworkProfileError("PACKET_COUNT_INVALID")
    events: list[NetworkEvent] = []
    for packet_index in range(packet_count):
        digest = hashlib.sha256(f"{profile.seed}:{packet_index}".encode()).digest()
        loss_draw = int.from_bytes(digest[0:4], "big") % 1_000_000
        duplicate_draw = int.from_bytes(digest[4:8], "big") % 1_000_000
        reorder_draw = int.from_bytes(digest[8:12], "big") % 1_000_000
        jitter_span = 2 * profile.jitter_ms + 1
        jitter = int.from_bytes(digest[12:16], "big") % jitter_span - profile.jitter_ms
        events.append(
            NetworkEvent(
                packet_index=packet_index,
                delay_ms=max(0, profile.rtt_ms // 2 + jitter),
                dropped=loss_draw < profile.loss_ppm,
                duplicated=duplicate_draw < profile.duplication_ppm,
                reordered=reorder_draw < profile.reordering_ppm,
            )
        )
    return tuple(events)
