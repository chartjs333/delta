"""Regression tests for cross-compiler and endian portability evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_core_portability_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "core-portability-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_core_portability", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_portability_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["task_ids"] == ["T023", "HR003-008"]


def test_changed_wire_order_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["checks"][0] = "HOST_ENDIAN_DEPENDENT"

    with pytest.raises(MODULE.CorePortabilityEvidenceError, match="CHECK_SET_INVALID"):
        MODULE.verify(changed)
