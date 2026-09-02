"""Exact protocol-hash and mandatory attack rejection analysis."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.arms import RunObservation
from deltatorrent.benchmark.attacks import MANDATORY_ATTACK_IDS, AttackOutcome
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID


@dataclass(frozen=True, slots=True)
class SafetyResult:
    document: dict[str, object]
    status: str


def analyze_safety(
    definition_id: str,
    runs: tuple[RunObservation, ...],
    attacks: tuple[AttackOutcome, ...],
    *,
    formal_regression_passed: bool,
) -> SafetyResult:
    by_seed: dict[int, set[str]] = {}
    for run in runs:
        if run.arm.deployment_profile != "PYTHON":
            by_seed.setdefault(run.seed, set()).add(run.protocol_hash)
    exact = bool(by_seed) and all(len(values) == 1 for values in by_seed.values())
    attack_map = {item.attack_id: item for item in attacks}
    attacks_pass = set(attack_map) == MANDATORY_ATTACK_IDS and all(
        item.rejected and item.current_unchanged and item.actual_outcome == item.expected_outcome
        for item in attack_map.values()
    )
    status = "PASS" if exact and attacks_pass and formal_regression_passed else "FAIL"
    document: dict[str, object] = {
        "attacks": [attack_map[key].to_dict() for key in sorted(attack_map)],
        "benchmark_definition_id": definition_id,
        "exact_hashes_match": exact,
        "formal_regression_status": "PASS" if formal_regression_passed else "FAIL",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": "1.0.0",
        "status": status,
        "type_name": "SAFETY_EVIDENCE",
    }
    return SafetyResult(document, status)
