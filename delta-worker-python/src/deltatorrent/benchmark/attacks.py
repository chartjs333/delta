"""Mandatory production-attack vocabulary and deterministic rejection records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID

MANDATORY_ATTACK_IDS: Final = frozenset(
    {
        "ac-mutation",
        "certificate-downgrade",
        "commitment-equivocation",
        "conflicting-apply",
        "conflicting-config",
        "current-without-applyqc",
        "duplicate-root",
        "frankenstein-shard",
        "incomplete-root",
        "seed-before-isc",
        "unsafe-accumulator",
        "vote-equivocation",
        "wrong-epoch",
    }
)

PRODUCTION_ATTACK_BOUNDARIES: Final = {
    "ac-mutation": (
        "delta::certificates::ChainVerifier::verify_eligibility",
        "PARENT_MISMATCH",
    ),
    "certificate-downgrade": (
        "delta::distribution::evaluate_applied_checkpoint",
        "APPLY_POLICY_MISMATCH",
    ),
    "commitment-equivocation": (
        "delta::runtime::Runtime::submit",
        "REQUEST_CONFLICT",
    ),
    "conflicting-apply": (
        "delta::runtime::CurrentPointerStore::advance",
        "REQUEST_CONFLICT",
    ),
    "conflicting-config": (
        "delta::certificates::ChainVerifier::verify_seed",
        "CONTEXT_MISMATCH",
    ),
    "current-without-applyqc": (
        "delta::certificates::ChainVerifier::verify_apply",
        "QUORUM_INVALID",
    ),
    "duplicate-root": (
        "delta::certificates::ChainVerifier::verify_root",
        "COVERAGE_INCOMPLETE",
    ),
    "frankenstein-shard": (
        "delta::certificates::ChainVerifier::verify_root",
        "CONTEXT_MISMATCH",
    ),
    "incomplete-root": (
        "delta::certificates::ChainVerifier::verify_root",
        "COVERAGE_INCOMPLETE",
    ),
    "seed-before-isc": (
        "delta::certificates::ChainVerifier::verify_seed",
        "PARENT_MISMATCH",
    ),
    "unsafe-accumulator": (
        "delta::robust::exact_squared_norm",
        "ARITHMETIC_INVALID",
    ),
    "vote-equivocation": (
        "delta::runtime::CertificateVoteRuntime::persist_and_expose",
        "CONFLICTING_VOTE",
    ),
    "wrong-epoch": (
        "delta::certificates::ChainVerifier::verify_root",
        "CONTEXT_MISMATCH",
    ),
}


class ProductionAttackError(ValueError):
    """Stable rejection for incomplete or detached attack evidence."""


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


def production_rejection_corpus(document: Mapping[str, object]) -> tuple[AttackOutcome, ...]:
    """Validate outcomes emitted by the native production-module attack runner."""
    if set(document) != {
        "attacks",
        "formal_semantics_id",
        "mutation_scope",
        "schema_version",
        "status",
        "type_name",
    }:
        raise ProductionAttackError("PRODUCTION_ATTACK_REPORT_FIELDS")
    if (
        document.get("schema_version") != "1.0.0"
        or document.get("type_name") != "PRODUCTION_ATTACK_REPORT"
        or document.get("mutation_scope") != "PRODUCTION_MODULE_BOUNDARY"
        or document.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
        or document.get("status") != "PASS"
    ):
        raise ProductionAttackError("PRODUCTION_ATTACK_REPORT_IDENTITY")
    values = document.get("attacks")
    if not isinstance(values, list):
        raise ProductionAttackError("PRODUCTION_ATTACK_REPORT_ITEMS")
    outcomes: list[AttackOutcome] = []
    observed: set[str] = set()
    for value in values:
        if not isinstance(value, dict) or set(value) != {
            "attack_id",
            "boundary",
            "current_unchanged",
            "error_code",
            "rejected",
        }:
            raise ProductionAttackError("PRODUCTION_ATTACK_ITEM_FIELDS")
        attack_id = value.get("attack_id")
        if not isinstance(attack_id, str) or attack_id in observed:
            raise ProductionAttackError("PRODUCTION_ATTACK_ITEM_ID")
        observed.add(attack_id)
        try:
            expected_boundary, expected_error = PRODUCTION_ATTACK_BOUNDARIES[attack_id]
        except KeyError as exc:
            raise ProductionAttackError("PRODUCTION_ATTACK_ITEM_UNKNOWN") from exc
        if value.get("boundary") != expected_boundary or value.get("error_code") != expected_error:
            raise ProductionAttackError("PRODUCTION_ATTACK_BOUNDARY_MISMATCH")
        rejected = value.get("rejected") is True
        current_unchanged = value.get("current_unchanged") is True
        expected_outcome = f"REJECTED:{expected_error}"
        outcomes.append(
            AttackOutcome(
                attack_id=attack_id,
                expected_outcome=expected_outcome,
                actual_outcome=expected_outcome if rejected else f"ACCEPTED:{expected_error}",
                rejected=rejected,
                current_unchanged=current_unchanged,
            )
        )
    if observed != MANDATORY_ATTACK_IDS:
        raise ProductionAttackError("PRODUCTION_ATTACK_CORPUS_INCOMPLETE")
    return tuple(sorted(outcomes, key=lambda item: item.attack_id))
