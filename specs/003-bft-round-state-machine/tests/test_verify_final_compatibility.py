"""Regression tests for the feature-003 final cross-artifact verifier."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_final_compatibility.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "final-compatibility.json"
SPEC = importlib.util.spec_from_file_location("verify_feature003_final", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_exact_final_evidence_is_accepted() -> None:
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    result = MODULE.verify(document["source"]["commit"], run_nested=False)

    assert MODULE.canonical_json_bytes(result) == EVIDENCE.read_bytes()
    assert result["status"] == "PASS"
    assert result["semantic_completeness_claimed"] is False
    assert result["task_counts"] == {"HR003": 24, "T": 53}


def test_formal_protocol_abi_and_documentation_are_consistent() -> None:
    source = MODULE.git_text("rev-parse", "HEAD")

    assert MODULE.verify_formal_binding(source)["decision"] == "GO"
    assert MODULE.verify_protocol_and_abi(source)["feature003_fixture_count"] == 3
    assert len(MODULE.verify_constitution(source)) == 11
    MODULE.verify_documentation(source)


def test_registry_hash_mutation_is_rejected() -> None:
    source = MODULE.git_text("rev-parse", "HEAD")
    changed = {
        "id": "REGISTRY-BFT-003-V1",
        "path": "schemas/003/registry-v1.json",
        "sha256": "0" * 64,
    }

    with pytest.raises(MODULE.FinalCompatibilityError, match="REGISTRY_HASH_MISMATCH"):
        MODULE.verify_registered_record(changed, source)


def test_incomplete_final_task_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    source = MODULE.git_text("rev-parse", "HEAD")
    original = MODULE.tracked_text

    def changed_text(path: str, revision: str) -> str:
        value = original(path, revision)
        if path.endswith("/tasks.md") and not path.endswith("/runtime-tasks.md"):
            return value.replace("- [x] T052", "- [ ] T052", 1)
        return value

    monkeypatch.setattr(MODULE, "tracked_text", changed_text)
    with pytest.raises(MODULE.FinalCompatibilityError, match="SEMANTIC_TASK_SET_INCOMPLETE"):
        MODULE.verify_completed_scope(source)
