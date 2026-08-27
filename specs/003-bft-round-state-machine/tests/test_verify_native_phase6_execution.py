"""Regression tests for native phase-6 execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_native_phase6_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "native-phase6-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_native_phase6", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_native_phase6_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["exit_result"] == MODULE.EXPECTED_EXIT_RESULT


def test_missing_tsan_job_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["runs"]["sanitizer"]["jobs"] = changed["runs"]["sanitizer"]["jobs"][:1]

    with pytest.raises(MODULE.NativePhase6EvidenceError, match="JOB_SET_INVALID"):
        MODULE.verify(changed)


def test_overstated_semantic_claim_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["semantic_completeness_claimed"] = True

    with pytest.raises(MODULE.NativePhase6EvidenceError, match="SEMANTIC_CLAIM_INVALID"):
        MODULE.verify(changed)
