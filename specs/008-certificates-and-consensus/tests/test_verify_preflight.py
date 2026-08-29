from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/008-certificates-and-consensus/scripts/verify_preflight.py"


def load_preflight():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("feature008_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_feature007_document(module):  # type: ignore[no-untyped-def]
    source = {
        "artifacts": [{"path": "unused", "sha256": "unused"}],
        "commit": module.FEATURE007_SOURCE,
        "tree": "tree",
    }
    child = {"source": source, "status": "PASS"}
    return {
        "classification": "REFINEMENT_ONLY",
        "formal": {
            "formal_semantics_id": module.FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "native_admission": child.copy(),
        "native_lifecycle": child.copy(),
        "native_planner": child.copy(),
        "scheduling_ci": {"status": "PASS"},
        "scheduling_refinement": {"status": "PASS"},
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "PASS",
    }


def test_feature007_document_accepts_exact_boundary() -> None:
    module = load_preflight()
    module.validate_feature007_document(valid_feature007_document(module))


def test_feature007_document_rejects_semantic_extension() -> None:
    module = load_preflight()
    document = valid_feature007_document(module)
    document["formal"]["new_action_ids"] = ["ACT-JAVA-APPLY"]
    with pytest.raises(module.PreflightError, match="FEATURE007_FORMAL_DRIFT"):
        module.validate_feature007_document(document)


def test_feature007_document_rejects_source_drift() -> None:
    module = load_preflight()
    document = valid_feature007_document(module)
    document["source"]["commit"] = "0" * 40
    with pytest.raises(module.PreflightError, match="FEATURE007_SOURCE_DRIFT"):
        module.validate_feature007_document(document)


def test_task_topology_and_runtime_map_are_exact() -> None:
    tasks = (ROOT / "specs/008-certificates-and-consensus/tasks.md").read_text()
    runtime = (ROOT / "specs/008-certificates-and-consensus/runtime-tasks.md").read_text()
    task_map = (ROOT / "specs/008-certificates-and-consensus/task-map.md").read_text()
    assert all(f"T{index:03d}" in tasks for index in range(54))
    assert all(f"HR008-{index:03d}" in runtime for index in range(1, 20))
    assert all(f"HR008-{index:03d}" in task_map for index in range(1, 20))
    assert "HR008-020" not in runtime


def test_required_formal_action_set_covers_full_chain_and_recovery() -> None:
    module = load_preflight()
    assert {
        "ACT-ISC-FINALIZE",
        "ACT-SEED-GENERATE",
        "ACT-EC-FINALIZE",
        "ACT-APC-FINALIZE",
        "ACT-PARAM-FINALIZE",
        "ACT-ROOT-FINALIZE",
        "ACT-APPLY-FINALIZE",
        "ACT-CURRENT-ADVANCE",
        "ACT-JOURNAL-RECOVER",
        "ACT-MESSAGE-DROP",
    }.issubset(module.REQUIRED_ACTION_IDS)


def test_feature007_ticket_plan_identity_is_exact() -> None:
    module = load_preflight()
    result = module.verify_ticket_and_lease_identity()
    assert result["status"] == "PASS"
    assert result["plan_id"] == module.FEATURE007_PLAN_ID
    assert len(result["lease_ids"]) == 3
