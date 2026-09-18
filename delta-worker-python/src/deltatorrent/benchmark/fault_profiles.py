"""Deterministic fault/churn traces with explicit expected terminal outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class FaultProfileError(ValueError):
    """Stable fault-profile validation error."""


@dataclass(frozen=True, slots=True)
class FaultEvent:
    event_id: str
    actor_class: str
    action: str
    at_step: int
    assumptions_hold: bool
    expected_outcome: str


@dataclass(frozen=True, slots=True)
class FaultProfile:
    profile_id: str
    events: tuple[FaultEvent, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> FaultProfile:
        required = {
            "events",
            "formal_semantics_id",
            "profile_id",
            "schema_version",
            "type_name",
        }
        if set(value) != required or value.get("type_name") != "FAULT_PROFILE":
            raise FaultProfileError("FAULT_PROFILE_FIELDS_INVALID")
        events_raw = value["events"]
        if not isinstance(events_raw, list):
            raise FaultProfileError("FAULT_PROFILE_EVENTS_INVALID")
        events: list[FaultEvent] = []
        ids: set[str] = set()
        for item in events_raw:
            if not isinstance(item, dict) or set(item) != {
                "action",
                "actor_class",
                "assumptions_hold",
                "at_step",
                "event_id",
                "expected_outcome",
            }:
                raise FaultProfileError("FAULT_EVENT_FIELDS_INVALID")
            event_id = item["event_id"]
            at_step = item["at_step"]
            assumptions = item["assumptions_hold"]
            if (
                not isinstance(event_id, str)
                or not event_id
                or event_id in ids
                or isinstance(at_step, bool)
                or not isinstance(at_step, int)
                or at_step < 0
                or not isinstance(assumptions, bool)
            ):
                raise FaultProfileError("FAULT_EVENT_INVALID")
            ids.add(event_id)
            events.append(
                FaultEvent(
                    event_id=event_id,
                    actor_class=str(item["actor_class"]),
                    action=str(item["action"]),
                    at_step=at_step,
                    assumptions_hold=assumptions,
                    expected_outcome=str(item["expected_outcome"]),
                )
            )
        return cls(
            str(value["profile_id"]),
            tuple(sorted(events, key=lambda item: (item.at_step, item.event_id))),
        )
