"""Regression tests for feature-003 compiler/JDK execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_toolchain_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "toolchain-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_execution", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_execution_matrix_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert {job["name"] for job in result["run"]["jobs"]} == set(MODULE.EXPECTED_JOBS)


def test_failed_job_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["run"]["jobs"][0]["conclusion"] = "failure"

    with pytest.raises(MODULE.ExecutionEvidenceError, match="JOB_CONCLUSION_INVALID"):
        MODULE.verify(changed)
