"""Mandatory production-attack vocabulary and deterministic rejection records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

MANDATORY_ATTACK_IDS: Final = frozenset(
    {
        "ac-mutation",
        "certificate-downgrade",
        "conflicting-apply",
        "conflicting-config",
        "frankenstein-shard",
        "incomplete-root",
        "seed-before-isc",
        "unsafe-accumulator",
        "vote-equivocation",
    }
)


@dataclass(frozen=True, slots=True)
class AttackOutcome:
    attack_id: str
    expected_outcome: str
    actual_outcome: str
    rejected: bool
    current_unchanged: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "actual_outcome": self.actual_outcome,
            "attack_id": self.attack_id,
            "current_unchanged": self.current_unchanged,
            "expected_outcome": self.expected_outcome,
            "rejected": self.rejected,
        }


def synthetic_rejection_corpus() -> tuple[AttackOutcome, ...]:
    """Contract smoke corpus; this is explicitly not production attack evidence."""
    return tuple(
        AttackOutcome(attack_id, "REJECTED", "REJECTED", True, True)
        for attack_id in sorted(MANDATORY_ATTACK_IDS)
    )
