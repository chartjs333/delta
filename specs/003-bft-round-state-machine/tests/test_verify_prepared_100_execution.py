"""Regression tests for the canonical prepared-100 execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_prepared_100_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "prepared-100-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_prepared_100", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_prepared_100_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["task_ids"] == ["T024"]


def test_changed_expected_result_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["checks"][5] = "ORDER_DEPENDENT"

    with pytest.raises(MODULE.Prepared100EvidenceError, match="CHECK_SET_INVALID"):
        MODULE.verify(changed)
