"""Regression tests for checked native arithmetic execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_core_arithmetic_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "core-arithmetic-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_core_arithmetic", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_arithmetic_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["task_ids"] == ["T018", "T019", "HR003-005"]


def test_failed_compiler_job_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["run"]["jobs"][0]["conclusion"] = "failure"

    with pytest.raises(MODULE.CoreArithmeticEvidenceError, match="JOB_CONCLUSION_INVALID"):
        MODULE.verify(changed)
