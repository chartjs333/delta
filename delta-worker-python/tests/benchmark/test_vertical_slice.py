from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.benchmark.decision import GateResult, decide
from deltatorrent.benchmark.report import human_report, machine_report, parse_machine_report
from deltatorrent.benchmark.synthetic import execute_synthetic_fixture
from deltatorrent.benchmark.verifier import OfflineVerifier

ROOT = Path(__file__).parents[3]
FIXTURE = ROOT / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json"


def test_synthetic_vertical_slice_is_complete_but_not_primary(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)

    assert result.benchmark_result.decision == "GO"
    assert result.run_count == 6
    assert result.verification.status == "PASS"
    assert result.fixture_class == "SYNTHETIC_NOT_PRIMARY_EVIDENCE"
    assert result.definition_attestation.purpose == "DEFINITION"
    assert result.result_attestation.purpose == "RESULT"
    assert result.result_attestation.to_dict(decision="GO")["protocol_current_transition"] is False
    encoded = machine_report(result.benchmark_result)
    assert parse_machine_report(encoded)["decision"] == "GO"
    assert "SYNTHETIC_FIXTURE_NOT_PRIMARY_EVIDENCE" in human_report(result.benchmark_result)


@pytest.mark.parametrize(
    ("gates", "decision"),
    [
        ((GateResult("A", True, "PASS", "OK"),), "GO"),
        ((GateResult("A", True, "FAIL", "FAILED"),), "NO_GO"),
        ((GateResult("A", False, "FAIL", "OPTIONAL"),), "GO"),
    ],
)
def test_decision_is_all_mandatory(gates: tuple[GateResult, ...], decision: str) -> None:
    result = decide(
        definition_id="sha256:" + "a" * 64,
        evidence_manifest_id="sha256:" + "b" * 64,
        run_ids=("sha256:" + "c" * 64, "sha256:" + "d" * 64),
        gates=gates,
        limitations=(),
    )

    assert result.decision == decision


def test_offline_verifier_detects_mutated_object(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    reference = result.evidence_bundle.evidence_refs[0][1]
    target = tmp_path / "objects" / Path(reference.locator)
    target.write_text("{}", encoding="utf-8")

    with pytest.raises(Exception, match="artifact bytes do not match"):
        OfflineVerifier(tmp_path / "objects").verify(result.evidence_bundle)


def test_offline_verifier_detects_missing_object(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    reference = result.evidence_bundle.run_refs[0]
    (tmp_path / "objects" / Path(reference.locator)).unlink()

    with pytest.raises(Exception, match="referenced artifact does not exist"):
        OfflineVerifier(tmp_path / "objects").verify(result.evidence_bundle)


def test_offline_verifier_reconstructs_complete_graph_from_manifest_id(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)

    verified = OfflineVerifier(tmp_path / "objects").verify_manifest(
        result.evidence_bundle.manifest_ref.content_id
    )

    assert verified.definition_id == result.evidence_bundle.definition_id
    assert verified.verified_object_count == 1 + result.run_count + 5


def test_offline_verifier_requires_stored_formal_evidence(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    formal_ref = next(
        reference for kind, reference in result.evidence_bundle.evidence_refs if kind == "FORMAL"
    )
    (tmp_path / "objects" / Path(formal_ref.locator)).unlink()

    with pytest.raises(Exception, match="EVIDENCE_OBJECT_MISSING"):
        OfflineVerifier(tmp_path / "objects").verify_manifest(
            result.evidence_bundle.manifest_ref.content_id
        )


def test_offline_verifier_rejects_reordered_run_graph(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    reordered = replace(
        result.evidence_bundle, run_refs=tuple(reversed(result.evidence_bundle.run_refs))
    )

    with pytest.raises(Exception, match="EVIDENCE_MANIFEST_RUN_SET_MISMATCH"):
        OfflineVerifier(tmp_path / "objects").verify(reordered)


def test_offline_verifier_rejects_incompatible_definition(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    incompatible = replace(result.evidence_bundle, definition_id="sha256:" + "f" * 64)

    with pytest.raises(Exception, match="EVIDENCE_MANIFEST_DEFINITION_MISMATCH"):
        OfflineVerifier(tmp_path / "objects").verify(incompatible)


def test_run_and_efficiency_evidence_uses_observed_identities_and_counters(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    efficiency_ref = next(
        reference
        for kind, reference in result.evidence_bundle.evidence_refs
        if kind == "EFFICIENCY"
    )
    efficiency = json.loads((tmp_path / "objects" / efficiency_ref.locator).read_bytes())
    assert efficiency["zero_copy_hit_rate_ppm"] == 500_000
    assert efficiency["zero_copy_fallback_bytes"] == 5_000
    assert {item["metric_id"] for item in efficiency["metrics"]} == {
        "bytes_per_token",
        "gpu_utilization_ppm",
        "network_share_ppm",
    }

    run_ref = result.evidence_bundle.run_refs[-1]
    run = json.loads((tmp_path / "objects" / run_ref.locator).read_bytes())
    assert run["ticket_plan_id"].startswith("sha256:")
    assert run["parent_checkpoint_id"].startswith("sha256:")
    assert len(run["output_ids"]) >= 10
    assert len(run["output_ids"]) == len(set(run["output_ids"]))


def test_machine_report_is_canonical(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    document = json.loads(machine_report(result.benchmark_result))

    assert document["decision"] == "GO"
    assert document["limitations"] == ["SYNTHETIC_FIXTURE_NOT_PRIMARY_EVIDENCE"]
