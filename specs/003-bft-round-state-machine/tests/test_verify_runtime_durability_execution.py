"""Regression tests for native runtime durability execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_runtime_durability_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "runtime-durability-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_runtime_durability", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_runtime_durability_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["task_ids"] == MODULE.TASK_IDS


def test_missing_crash_boundary_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["checks"].remove("ALL_APPEND_DURABILITY_COMMIT_EFFECT_CRASH_POINTS")

    with pytest.raises(MODULE.RuntimeDurabilityEvidenceError, match="CHECK_SET_INVALID"):
        MODULE.verify(changed)
