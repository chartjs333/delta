"""Regression tests for native consensus safety execution evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_core_consensus_execution.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "core-consensus-execution.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_core_consensus", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_exact_consensus_execution_is_accepted() -> None:
    result = MODULE.verify(evidence())

    assert result["status"] == "PASS"
    assert result["task_ids"] == ["T022"]


def test_source_mismatch_is_rejected() -> None:
    changed = copy.deepcopy(evidence())
    changed["run"]["head_sha"] = "0" * 40

    with pytest.raises(MODULE.CoreConsensusEvidenceError, match="RUN_SOURCE_MISMATCH"):
        MODULE.verify(changed)
