"""Regression tests for native ABI and JDK FFM execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_abi_ffm_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "abi-ffm-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_abi_ffm", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_abi_ffm_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["task_ids"] == MODULE.TASK_IDS


def test_missing_jdk_lane_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["run"]["jobs"] = [
        job for job in changed["run"]["jobs"] if job["name"] != "JDK 26 runtime descriptor"
    ]

    with pytest.raises(MODULE.AbiFfmEvidenceError, match="JOB_SET_INVALID"):
        MODULE.verify(changed)


def test_overstated_semantic_claim_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["semantic_completeness_claimed"] = True

    with pytest.raises(MODULE.AbiFfmEvidenceError, match="SEMANTIC_CLAIM_INVALID"):
        MODULE.verify(changed)
