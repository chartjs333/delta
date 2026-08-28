"""Regression tests for the feature-006 execution/refinement verifier."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_hierarchy_execution.py"
SPEC = importlib.util.spec_from_file_location("verify_feature006_hierarchy_execution", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_native_recovery_projection_passes_exact_formal_checker() -> None:
    recovery = {
        "events": [
            {"action": "PERSIST_VOTE", "vote_id": "sha256:" + "1" * 64},
            {"action": "PERSIST_VOTE", "vote_id": "sha256:" + "2" * 64},
        ]
    }

    result = MODULE.verify_formal_projection(recovery)

    assert result["status"] == "PASS"
    assert result["legal"]["terminal_outcome"] == "IN_PROGRESS"
    assert len(result["negative"]) == 5
    assert result["internal_hierarchy_actions"].startswith("STUTTER_")
