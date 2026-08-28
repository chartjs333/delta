from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/006-regional-hierarchical-reduce/scripts/verify_preflight.py"


def load_preflight():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("feature006_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_feature005_document(module):  # type: ignore[no-untyped-def]
    return {
        "classification": "REFINEMENT_ONLY",
        "formal": {
            "formal_semantics_id": module.FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "identities": {
            "manifest_id": module.MANIFEST_ID,
            "piece_profile_id": module.PIECE_PROFILE_ID,
            "policy_registry_id": module.POLICY_REGISTRY_ID,
        },
        "phase_evidence": {"source": {"commit": module.FEATURE005_SOURCE}, "status": "PASS"},
        "semantic_completeness_claimed": False,
        "source": {"commit": module.FEATURE005_SOURCE},
        "status": "PASS",
    }


def valid_theorem_reports(module):  # type: ignore[no-untyped-def]
    formal = {
        "theorem_checks": [
            {"id": theorem_id, "mandatory": True, "status": "PASS", "verified": True}
            for theorem_id in module.THEOREM_CONJUNCTS
        ]
    }
    lean = {
        "theorems": [
            {
                "id": theorem_id,
                "normative_conjuncts": [
                    {
                        "conjunct": conjunct,
                        "proof_obligation_id": theorem_id,
                        "source": (
                            "formal/proofs/DeltaReduce/Hierarchy.lean"
                            if theorem_id.startswith("PO-H")
                            else "formal/proofs/DeltaReduce/FixedPoint.lean"
                        ),
                        "source_sha256": (
                            "09da61bf15ff8b82f6b901ec699070a229589960f874240a90a9553e0ae8eb0a"
                            if theorem_id.startswith("PO-H")
                            else "6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736"
                        ),
                        "status": "PASS",
                    }
                    for conjunct in sorted(conjuncts)
                ],
                "source": (
                    "formal/proofs/DeltaReduce/Hierarchy.lean"
                    if theorem_id.startswith("PO-H")
                    else "formal/proofs/DeltaReduce/FixedPoint.lean"
                ),
                "source_sha256": (
                    "09da61bf15ff8b82f6b901ec699070a229589960f874240a90a9553e0ae8eb0a"
                    if theorem_id.startswith("PO-H")
                    else "6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736"
                ),
                "status": "PASS",
            }
            for theorem_id, conjuncts in module.THEOREM_CONJUNCTS.items()
        ]
    }
    return formal, lean


def test_feature005_document_accepts_exact_boundary() -> None:
    module = load_preflight()
    module.validate_feature005_document(valid_feature005_document(module))


def test_feature005_document_rejects_identity_drift() -> None:
    module = load_preflight()
    document = valid_feature005_document(module)
    document["identities"]["manifest_id"] = "sha256:" + "0" * 64
    with pytest.raises(module.PreflightError, match="FEATURE005_IDENTITIES_DRIFT"):
        module.validate_feature005_document(document)


def test_feature005_document_rejects_formal_action_extension() -> None:
    module = load_preflight()
    document = valid_feature005_document(module)
    document["formal"]["new_action_ids"] = ["ACT-REGIONAL-FALLBACK"]
    with pytest.raises(module.PreflightError, match="FEATURE005_FORMAL_DRIFT"):
        module.validate_feature005_document(document)


def test_required_theorems_accept_exact_normative_conjuncts() -> None:
    module = load_preflight()
    formal, lean = valid_theorem_reports(module)
    result = module.validate_required_theorems(formal, lean)
    assert [item["id"] for item in result] == list(module.THEOREM_CONJUNCTS)


def test_required_theorems_reject_missing_rounding_conjunct() -> None:
    module = load_preflight()
    formal, lean = valid_theorem_reports(module)
    po_a3 = next(item for item in lean["theorems"] if item["id"] == "PO-A3")
    po_a3["normative_conjuncts"] = [
        item
        for item in po_a3["normative_conjuncts"]
        if item["conjunct"] != "rounding-deterministic"
    ]
    with pytest.raises(module.PreflightError, match="LEAN_CONJUNCT_COVERAGE_DRIFT:PO-A3"):
        module.validate_required_theorems(formal, lean)


def test_task_topology_is_exact() -> None:
    tasks = (ROOT / "specs/006-regional-hierarchical-reduce/tasks.md").read_text()
    assert all(f"T{index:03d}" in tasks for index in range(31))
    runtime = (ROOT / "specs/006-regional-hierarchical-reduce/runtime-tasks.md").read_text()
    assert all(f"HR006-{index:03d}" in runtime for index in range(1, 12))
    assert "HR006-012" not in runtime
