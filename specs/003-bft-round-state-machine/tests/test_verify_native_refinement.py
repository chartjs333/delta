"""Regression tests for implementation traces and production mutants."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_native_refinement.py"
SPEC = importlib.util.spec_from_file_location("verify_feature003_native_refinement", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_native_legal_and_mutant_traces_refine_exact_baseline() -> None:
    result = MODULE.verify_all()

    assert result["status"] == "PASS"
    assert len(result["legal"]) == 4
    assert len(result["mutants"]) == 2
    assert result["semantic_completeness_claimed"] is False
