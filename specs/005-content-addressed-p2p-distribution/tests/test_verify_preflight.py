from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/005-content-addressed-p2p-distribution/scripts/verify_preflight.py"


def load_preflight():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("feature005_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_feature004_document(module):  # type: ignore[no-untyped-def]
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
            "commitment_root": module.COMMITMENT_ROOT,
            "fixedpoint_config_id": module.CONFIG_ID,
            "profile_id": module.PROFILE_ID,
            "proof_instance_id": module.PROOF_ID,
        },
        "semantic_completeness_claimed": False,
        "source": {"commit": module.FEATURE004_SOURCE},
        "status": "PASS",
    }


def test_feature004_document_accepts_exact_boundary() -> None:
    module = load_preflight()
    module.validate_feature004_document(valid_feature004_document(module))


def test_feature004_document_rejects_identity_drift() -> None:
    module = load_preflight()
    document = valid_feature004_document(module)
    document["identities"]["commitment_root"] = "sha256:" + "0" * 64
    with pytest.raises(module.PreflightError, match="FEATURE004_IDENTITIES_DRIFT"):
        module.validate_feature004_document(document)


def test_feature004_document_rejects_formal_action_extension() -> None:
    module = load_preflight()
    document = valid_feature004_document(module)
    document["formal"]["new_action_ids"] = ["ACT-JAVA-ALLOW"]
    with pytest.raises(module.PreflightError, match="FEATURE004_FORMAL_DRIFT"):
        module.validate_feature004_document(document)


def test_task_topology_is_exact() -> None:
    text = (ROOT / "specs/005-content-addressed-p2p-distribution/tasks.md").read_text()
    identifiers = [f"T{index:03d}" for index in range(33)]
    assert all(text.count(identifier) >= 1 for identifier in identifiers)
    runtime = (ROOT / "specs/005-content-addressed-p2p-distribution/runtime-tasks.md").read_text()
    assert all(f"HR005-{index:03d}" in runtime for index in range(1, 14))
