"""Regression tests for strict native protocol execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_core_protocol_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "core-protocol-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_core_protocol", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_protocol_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["task_ids"] == ["T016", "T017", "HR003-004"]


def test_artifact_drift_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["artifacts"][0]["sha256"] = "0" * 64

    with pytest.raises(MODULE.CoreProtocolEvidenceError, match="ARTIFACT_SET_INVALID"):
        MODULE.verify(changed)
