"""Seeded logical faulty stream requiring neither sockets nor privileges."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from deltatorrent.domain.network import FaultKind, NetworkProfile


@dataclass(frozen=True, slots=True)
class Delivery:
    sequence: int
    sent_at_ms: int
    delivered_at_ms: int | None
    payload: bytes | None
    events: tuple[FaultKind, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "delivered_at_ms": self.delivered_at_ms,
            "events": [item.value for item in self.events],
            "payload_sha256": (
                hashlib.sha256(self.payload).hexdigest() if self.payload is not None else None
            ),
            "sent_at_ms": self.sent_at_ms,
            "sequence": self.sequence,
        }


class SimulatedFaultyStream:
    def __init__(self, profile: NetworkProfile) -> None:
        self.profile = profile
        self._available_at_ms = 0

    def transmit(self, payload: bytes, *, sequence: int, sent_at_ms: int) -> Delivery:
        if sequence < 0 or sent_at_ms < 0:
            raise ValueError("STREAM_POSITION_INVALID")
        digest = hashlib.sha256(
            b"deltareduce.netem.v1\x00"
            + self.profile.seed.to_bytes(8, "big")
            + sequence.to_bytes(8, "big")
            + payload
        ).digest()
        serialization_ms = max(
            1,
            (len(payload) * 1000 + self.profile.bandwidth_bytes_per_second - 1)
            // self.profile.bandwidth_bytes_per_second,
        )
        jitter_width = 2 * self.profile.jitter_ms + 1
        jitter = int.from_bytes(digest[0:4], "big") % jitter_width - self.profile.jitter_ms
        start = max(sent_at_ms, self._available_at_ms)
        delivered_at = start + max(0, self.profile.latency_ms + jitter) + serialization_ms
        self._available_at_ms = start + serialization_ms

        if any(
            window.start_ms < delivered_at and sent_at_ms < window.end_ms
            for window in self.profile.disconnect_windows
        ):
            return Delivery(sequence, sent_at_ms, None, None, (FaultKind.DISCONNECT,))
        loss_roll = int.from_bytes(digest[4:8], "big") % 1_000_000
        if loss_roll < self.profile.loss_ppm:
            return Delivery(sequence, sent_at_ms, None, None, (FaultKind.DROP,))
        events: list[FaultKind] = [FaultKind.DELAY]
        reorder_roll = int.from_bytes(digest[8:12], "big") % 1_000_000
        if reorder_roll < self.profile.reorder_ppm:
            delivered_at += self.profile.latency_ms + self.profile.jitter_ms + 1
            events.append(FaultKind.REORDER)
        if delivered_at - sent_at_ms > self.profile.operation_deadline_ms:
            return Delivery(sequence, sent_at_ms, None, None, (*events, FaultKind.TIMEOUT))
        events.append(FaultKind.DELIVER)
        return Delivery(sequence, sent_at_ms, delivered_at, bytes(payload), tuple(events))

    def transmit_stream(self, frames: tuple[tuple[int, bytes], ...]) -> tuple[Delivery, ...]:
        deliveries = tuple(
            self.transmit(payload, sequence=sequence, sent_at_ms=sent_at)
            for sequence, (sent_at, payload) in enumerate(frames)
        )
        return tuple(
            sorted(
                deliveries,
                key=lambda item: (
                    item.delivered_at_ms is None,
                    item.delivered_at_ms if item.delivered_at_ms is not None else 0,
                    item.sequence,
                ),
            )
        )
