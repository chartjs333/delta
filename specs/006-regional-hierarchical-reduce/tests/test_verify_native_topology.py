from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "verify_native_topology.py"
SPEC = importlib.util.spec_from_file_location("verify_native_topology", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_native_topology_evidence_is_exact() -> None:
    evidence = MODULE.verify_evidence()
    assert evidence["status"] == "PASS"
    assert evidence["execution"]["passed"] == 5
    assert evidence["task_ids"] == ["T011", "T012", "T013", "T014", "HR006-002"]


def test_native_topology_source_is_refinement_only() -> None:
    evidence = MODULE.verify_evidence()
    assert evidence["classification"] == "REFINEMENT_ONLY"
    assert evidence["semantic_completeness_claimed"] is False
    assert len(evidence["source"]["artifacts"]) == 5
