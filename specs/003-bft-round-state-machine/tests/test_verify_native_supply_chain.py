"""Regression tests for the feature-003 native supply-chain manifest."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_native_supply_chain.py"
SPEC = importlib.util.spec_from_file_location("verify_feature003_native_supply_chain", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_worktree_supply_chain_is_content_addressed() -> None:
    result = MODULE.verify(None, "HEAD")

    assert result["status"] == "PASS"
    assert result["dependency_manifest"]["runtime_dependency_count"] == 0
    assert len(result["source_manifest"]) >= 10
    assert len(result["license_manifest"]["external_components"]) == 7
    assert not result["license_manifest"]["project_source"]["redistribution_granted"]


def test_all_source_records_use_lowercase_sha256() -> None:
    result = MODULE.verify(None, "HEAD")

    for artifact in result["source_manifest"]:
        assert len(artifact["sha256"]) == 64
        assert artifact["sha256"] == artifact["sha256"].lower()
