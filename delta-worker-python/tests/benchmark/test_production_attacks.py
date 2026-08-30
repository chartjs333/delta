from __future__ import annotations

from copy import deepcopy

import pytest
from deltatorrent.benchmark.attacks import (
    PRODUCTION_ATTACK_BOUNDARIES,
    ProductionAttackError,
    production_rejection_corpus,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID


def report() -> dict[str, object]:
    return {
        "attacks": [
            {
                "attack_id": attack_id,
                "boundary": boundary,
                "current_unchanged": True,
                "error_code": error_code,
                "rejected": True,
            }
            for attack_id, (boundary, error_code) in sorted(
                PRODUCTION_ATTACK_BOUNDARIES.items()
            )
        ],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "mutation_scope": "PRODUCTION_MODULE_BOUNDARY",
        "schema_version": "1.0.0",
        "status": "PASS",
        "type_name": "PRODUCTION_ATTACK_REPORT",
    }


def test_native_production_attack_report_is_admitted_exactly() -> None:
    outcomes = production_rejection_corpus(report())

    assert len(outcomes) == 13
    assert all(item.rejected and item.current_unchanged for item in outcomes)
    assert all(item.actual_outcome == item.expected_outcome for item in outcomes)


@pytest.mark.parametrize("mutation", ["missing", "boundary", "accepted", "formal"])
def test_production_attack_report_fails_closed(mutation: str) -> None:
    value = deepcopy(report())
    attacks = value["attacks"]
    assert isinstance(attacks, list)
    first = attacks[0]
    assert isinstance(first, dict)
    if mutation == "missing":
        attacks.pop()
    elif mutation == "boundary":
        first["boundary"] = "deltareduce.benchmark.synthetic"
    elif mutation == "accepted":
        first["rejected"] = False
    else:
        value["formal_semantics_id"] = "sha256:" + "0" * 64

    if mutation == "accepted":
        outcomes = production_rejection_corpus(value)
        assert any(not item.rejected for item in outcomes)
    else:
        with pytest.raises(ProductionAttackError):
            production_rejection_corpus(value)
