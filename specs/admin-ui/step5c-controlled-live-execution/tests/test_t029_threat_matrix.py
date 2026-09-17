"""Regression checks for the Step 5C T029 threat matrix."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "security" / "t029-threat-negative-test-matrix.json"
EVIDENCE = ROOT / "evidence" / "t029-threat-matrix.json"

REQUIRED_CATEGORIES = {
    "RCE",
    "PATH_MODULE_INJECTION",
    "MALICIOUS_JSON_JCS",
    "REPLAY",
    "FORGED_ADMISSION",
    "CONFUSED_DEPUTY",
    "ROLE_SPOOFING",
    "QUOTA_RESOURCE_EXHAUSTION",
    "STALE_CATALOG",
    "FORGED_LINEAGE",
}

ALLOWED_OWNERS = {
    "contracts",
    "controller",
    "worker-adapter",
    "admin-ui-live",
    "security",
}


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_t029_matrix_covers_required_categories() -> None:
    matrix = _load(MATRIX)
    cases = matrix["test_cases"]

    categories = {case["category"] for case in cases}
    assert REQUIRED_CATEGORIES <= categories
    assert set(matrix["required_categories"]) == REQUIRED_CATEGORIES


def test_t029_matrix_cases_are_unique_and_actionable() -> None:
    matrix = _load(MATRIX)
    cases = matrix["test_cases"]
    ids = [case["id"] for case in cases]

    assert len(ids) == len(set(ids))
    assert len(cases) >= 20

    for case in cases:
        assert str(case["id"]).startswith("S5C-T029-")
        assert case["category"] in REQUIRED_CATEGORIES
        assert case["severity"] in {"CRITICAL", "HIGH", "MEDIUM"}
        assert case["attack_vector"]
        assert case["expected_result"]
        assert case["owner_tasks"]
        assert case["executable_after"]
        assert set(case["production_fix_owner"]) <= ALLOWED_OWNERS


def test_t029_evidence_points_to_matrix_and_blocks_executables_on_contracts() -> None:
    evidence = _load(EVIDENCE)

    assert evidence["task_id"] == "step5c:T029"
    assert evidence["status"] == "DESIGN_READY_EXECUTABLES_BLOCKED_ON_T005_T009"
    assert evidence["contract_freeze_sha"] == "66e3e7e5bb07a48aadbee8d9c4683144b812d229"
    assert set(evidence["covers_required_categories"]) == REQUIRED_CATEGORIES

    blocked = evidence["blocked_executable_tests"]
    assert blocked["required_upstream_tasks"] == [
        "step5c:T005",
        "step5c:T006",
        "step5c:T007",
        "step5c:T008",
        "step5c:T009",
    ]
