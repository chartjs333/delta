"""Regression tests for the feature-003 final cross-artifact verifier."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_final_compatibility.py"
SPEC = importlib.util.spec_from_file_location("verify_feature003_final", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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
