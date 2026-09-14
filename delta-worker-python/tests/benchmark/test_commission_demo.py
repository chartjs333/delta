from __future__ import annotations

import json
from pathlib import Path

import deltatorrent.benchmark.commission_demo as commission_demo
import pytest
from deltatorrent.benchmark.commission_demo import (
    CommissionDemoError,
    run_commission_demo,
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_commission_demo_runs_training_quorum_wan_and_synthetic_control_plane(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "commission-demo"
    result = run_commission_demo(_repository_root(), destination)
    report = json.loads(result.report_json.read_text(encoding="utf-8"))

    assert result.report_html.is_file()
    assert report["demo_status"] == "DEMO_PASS"
    assert report["authoritative"] is False
    assert report["governance_eligible"] is False
    assert report["execution_authorized"] is False
    assert report["feature_010_go_claimed"] is False
    assert report["controller_quorum"]["keys_cryptographically_valid"] is True
    assert report["controller_quorum"]["valid_for_campaign02_governance"] is False
    assert report["training"]["status"] == "COMPLETED"
    assert report["training"]["artifact_verification"]["status"] == "PASS"
    assert report["wan"]["status"] == "PASS"
    assert report["wan"]["deterministic_replay"] is True
    assert report["wan"]["delivered"] > 0
    assert report["wan"]["faulted"] > 0
    assert report["synthetic_benchmark"]["verification_status"] == "PASS"
    assert report["synthetic_benchmark"]["fixture_class"] == "SYNTHETIC_NOT_PRIMARY_EVIDENCE"
    assert {item["status"] for item in report["checks"]} == {"PASS"}

    html_report = result.report_html.read_text(encoding="utf-8")
    assert "DEMO PASS" in html_report
    assert "does not claim controller appointment" in html_report
    assert "Feature 010 GO" in html_report


def test_commission_demo_refuses_to_overwrite_a_prior_run(tmp_path: Path) -> None:
    destination = tmp_path / "commission-demo"
    destination.mkdir()
    with pytest.raises(CommissionDemoError, match="OUTPUT_ALREADY_EXISTS"):
        run_commission_demo(_repository_root(), destination)


def test_commission_demo_removes_its_partial_output_after_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "commission-demo"

    def fail_controller_generation(_output_dir: Path) -> None:
        raise CommissionDemoError("INJECTED_DEMO_FAILURE")

    monkeypatch.setattr(
        commission_demo,
        "generate_demo_controller_bundle",
        fail_controller_generation,
    )
    with pytest.raises(CommissionDemoError, match="INJECTED_DEMO_FAILURE"):
        run_commission_demo(_repository_root(), destination)
    assert not destination.exists()
