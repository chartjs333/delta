from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_preflight.py"

SPEC = importlib.util.spec_from_file_location("feature010_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def feature009_report() -> dict[str, Any]:
    path = ROOT / "specs/009-qlora-8gb-mode/evidence/final-compatibility.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def test_exact_feature_chain_is_valid() -> None:
    chain = MODULE.verify_feature_chain("HEAD")

    assert [item["id"] for item in chain] == [f"{number:03d}" for number in range(3, 10)]
    assert chain[-1]["merge_commit"] == MODULE.PREDECESSOR
    assert chain[-1]["report"]["sha256"] == MODULE.FEATURES[-1]["report_sha256"]


def test_formal_baseline_and_human_reviews_are_valid() -> None:
    formal = MODULE.verify_formal("HEAD")

    assert formal["status"] == "GO"
    assert formal["formal_semantics_id"] == MODULE.FORMAL_ID
    assert formal["independent_reviewers"] == ["ds2020ds", "hm2026-cpu"]
    assert formal["artifact_count"] >= 20


def test_feature_report_mutations_fail_closed() -> None:
    document = copy.deepcopy(feature009_report())
    document["semantic_completeness_claimed"] = True

    with pytest.raises(MODULE.PreflightError, match="SEMANTIC_CLAIM_OVERSTATED"):
        MODULE.validate_feature_report(document, "009", MODULE.FEATURES[-1]["source"])


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("adaptive_h = true", "ADAPTIVE_H"),
        ("manual_go_override: enabled", "MANUAL_GO_OVERRIDE"),
        ("stale update acceptance", "STALE_ACCEPTANCE"),
        ("threshold_override = 0.5", "THRESHOLD_OVERRIDE"),
        ("fp32 consensus fallback", "FLOAT_CONSENSUS"),
        ("single writer owns current", "SINGLE_WRITER_CURRENT"),
    ],
)
def test_forbidden_architecture_patterns_are_detected(text: str, code: str) -> None:
    assert code in MODULE.scan_forbidden_text(text)


def test_governance_qc_language_is_not_flagged_as_runtime_authority() -> None:
    assert MODULE.scan_forbidden_text(
        "BenchmarkResultQC is a governance attestation and cannot change current state."
    ) == []
