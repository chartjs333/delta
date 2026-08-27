"""Regression tests for the feature-004 exact predecessor preflight."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_preflight.py"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "preflight.json"
SPEC = importlib.util.spec_from_file_location("verify_feature004_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_canonical_preflight_evidence_is_accepted() -> None:
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    result = MODULE.verify(document["source"]["commit"])

    assert MODULE.canonical_json_bytes(result) == EVIDENCE.read_bytes()
    assert result["status"] == "PASS"
    assert result["semantic_completeness_claimed"] is False


def test_exact_predecessor_formal_and_architecture_are_accepted() -> None:
    source = MODULE.git_text("rev-parse", "HEAD")

    assert MODULE.verify_feature003(source)["status"] == "PASS"
    assert MODULE.verify_formal(source)["status"] == "PASS"
    assert MODULE.verify_architecture(source)["finding_count"] == 0
    assert MODULE.verify_formal_impact(source)["classification"] == "REFINEMENT_ONLY"


def test_wrong_feature003_compatibility_hash_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = MODULE.git_text("rev-parse", "HEAD")
    monkeypatch.setattr(MODULE, "EXPECTED_FEATURE003_COMPAT_SHA256", "0" * 64)

    with pytest.raises(MODULE.PreflightError, match="FEATURE003_COMPATIBILITY_HASH_MISMATCH"):
        MODULE.verify_feature003(source)


def test_po_a3_worker_rounding_overclaim_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    source = MODULE.git_text("rev-parse", "HEAD")
    original = MODULE.tracked_text

    def changed_text(path: str, revision: str) -> str:
        value = original(path, revision)
        if path.endswith("/plan.md"):
            return value.replace(
                "PO-A3 is not evidence for worker ties-to-even quantization",
                "PO-A3 proves worker ties-to-even quantization",
            )
        return value

    monkeypatch.setattr(MODULE, "tracked_text", changed_text)
    with pytest.raises(MODULE.PreflightError, match="PO_A3_BOUNDARY_UNCLEAR"):
        MODULE.verify_formal_impact(source)
