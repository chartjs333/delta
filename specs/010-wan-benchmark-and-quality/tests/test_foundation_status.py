from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_foundation_status.py"
SPEC = importlib.util.spec_from_file_location("verify_foundation_status", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def load(name: str) -> dict[str, object]:
    path = ROOT / "specs/010-wan-benchmark-and-quality/evidence" / name
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_bytes(name: str) -> bytes:
    return (ROOT / "specs/010-wan-benchmark-and-quality/evidence" / name).read_bytes()


def implementation_inventory() -> list[dict[str, str]]:
    return verifier.implementation_inventory(ROOT)


def test_foundation_status_worktree_passes_without_reading_unrelated_untracked_files() -> None:
    result = verifier.validate_repository(ROOT, allow_worktree=True)

    assert result["status"] == "PASS_FOUNDATION_ONLY"
    assert result["implementation_artifact_count"] == 54


def test_task_map_rejects_missing_exact_task() -> None:
    document = load("foundation-task-map.json")
    document["semantic_tasks"] = document["semantic_tasks"][:-1]

    with pytest.raises(verifier.VerificationError, match="SEMANTIC_TASK_SET_INVALID"):
        verifier.validate_task_map(
            ROOT, document, {entry["path"] for entry in implementation_inventory()}
        )


def test_task_map_rejects_nonexistent_test_nodeid() -> None:
    document = load("foundation-task-map.json")
    document["semantic_tasks"][0]["test_nodeids"] = [
        "delta-worker-python/tests/benchmark/test_foundation_contracts.py::test_not_real"
    ]

    with pytest.raises(verifier.VerificationError, match="TASK_TEST_NODEID_UNKNOWN:T001"):
        verifier.validate_task_map(
            ROOT, document, {entry["path"] for entry in implementation_inventory()}
        )


def test_formal_impact_rejects_new_runtime_vote_context() -> None:
    document = load("foundation-formal-impact.json")
    document["new_runtime_semantics"]["vote_contexts"] = ["BENCHMARK_VOTE"]

    with pytest.raises(verifier.VerificationError, match="NEW_RUNTIME_SEMANTICS_FORBIDDEN"):
        verifier.validate_formal_impact(ROOT, document)


def test_status_rejects_primary_observation_claim() -> None:
    document = load("foundation-status.json")
    document["authority_claims"]["primary_scientific_observation_count"] = 1

    with pytest.raises(verifier.VerificationError, match="ZERO_AUTHORITY_CLAIMS_INVALID"):
        verifier.validate_status(
            ROOT,
            document,
            evidence_bytes("foundation-task-map.json"),
            evidence_bytes("foundation-formal-impact.json"),
            implementation_inventory(),
        )


def test_status_rejects_implementation_artifact_hash_mutation() -> None:
    document = load("foundation-status.json")
    document["implementation"]["artifacts"][0]["sha256"] = "0" * 64

    with pytest.raises(verifier.VerificationError, match="IMPLEMENTATION_INVENTORY_MISMATCH"):
        verifier.validate_status(
            ROOT,
            document,
            evidence_bytes("foundation-task-map.json"),
            evidence_bytes("foundation-formal-impact.json"),
            implementation_inventory(),
        )


def test_status_rejects_recorded_test_result_mutation() -> None:
    document = load("foundation-status.json")
    document["test_evidence"][0]["result"] = "320 passed, 2 skipped"

    with pytest.raises(verifier.VerificationError, match="TEST_EVIDENCE_EXACT_RESULT_MISMATCH"):
        verifier.validate_status(
            ROOT,
            document,
            evidence_bytes("foundation-task-map.json"),
            evidence_bytes("foundation-formal-impact.json"),
            implementation_inventory(),
        )


def test_checklists_reject_foundation_mark_beyond_t027() -> None:
    tasks = (ROOT / "specs/010-wan-benchmark-and-quality/tasks.md").read_text(encoding="utf-8")
    runtime = (ROOT / "specs/010-wan-benchmark-and-quality/runtime-tasks.md").read_text(
        encoding="utf-8"
    )
    mutated = tasks.replace("- [ ] T028", "- [x] T028", 1)

    with pytest.raises(verifier.VerificationError, match="SEMANTIC_CHECKLIST_STATE_INVALID"):
        verifier.validate_checklists(mutated, runtime)
