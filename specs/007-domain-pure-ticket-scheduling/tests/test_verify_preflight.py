from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/007-domain-pure-ticket-scheduling/scripts/verify_preflight.py"


def load_preflight():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("feature007_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_feature006_document(module):  # type: ignore[no-untyped-def]
    source = {
        "artifacts": [{"path": "unused", "sha256": "unused"}],
        "commit": module.FEATURE006_SOURCE,
        "tree": "tree",
    }
    return {
        "classification": "REFINEMENT_ONLY",
        "formal": {
            "formal_semantics_id": module.FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "hierarchy_ci": {
            "source": {"commit": module.FEATURE006_SOURCE, "tree": "tree"},
            "status": "PASS",
        },
        "native_hierarchy": {"source": source, "status": "PASS"},
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "PASS",
    }


def test_feature006_document_accepts_exact_boundary() -> None:
    module = load_preflight()
    module.validate_feature006_document(valid_feature006_document(module))


def test_feature006_document_rejects_semantic_extension() -> None:
    module = load_preflight()
    document = valid_feature006_document(module)
    document["formal"]["new_action_ids"] = ["ACT-WALL-CLOCK-REASSIGN"]
    with pytest.raises(module.PreflightError, match="FEATURE006_FORMAL_DRIFT"):
        module.validate_feature006_document(document)


def test_feature006_document_rejects_source_drift() -> None:
    module = load_preflight()
    document = valid_feature006_document(module)
    document["source"]["commit"] = "0" * 40
    with pytest.raises(module.PreflightError, match="FEATURE006_SOURCE_DRIFT"):
        module.validate_feature006_document(document)


def test_task_topology_and_runtime_map_are_exact() -> None:
    tasks = (ROOT / "specs/007-domain-pure-ticket-scheduling/tasks.md").read_text()
    assert all(f"T{index:03d}" in tasks for index in range(34))
    runtime = (ROOT / "specs/007-domain-pure-ticket-scheduling/runtime-tasks.md").read_text()
    task_map = (ROOT / "specs/007-domain-pure-ticket-scheduling/task-map.md").read_text()
    assert all(f"HR007-{index:03d}" in runtime for index in range(1, 13))
    assert all(f"HR007-{index:03d}" in task_map for index in range(1, 13))
    assert "HR007-013" not in runtime


def test_required_formal_action_set_is_exact() -> None:
    module = load_preflight()
    assert module.REQUIRED_ACTION_IDS == {
        "ACT-ABORT-FINALIZE",
        "ACT-ABORT-VOTE",
        "ACT-COMMIT",
        "ACT-JOURNAL-RECOVER",
        "ACT-LEASE-EXPIRE",
        "ACT-LEASE-OPEN",
        "ACT-LEASE-REASSIGN",
        "ACT-LEASE-RENEW",
        "ACT-RESTART",
        "ACT-TICKET-ISSUE",
    }
