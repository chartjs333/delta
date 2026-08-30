from __future__ import annotations

import json
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


def test_machine_report_is_canonical(tmp_path: Path) -> None:
    result = execute_synthetic_fixture(FIXTURE, tmp_path)
    document = json.loads(machine_report(result.benchmark_result))

    assert document["decision"] == "GO"
    assert document["limitations"] == ["SYNTHETIC_FIXTURE_NOT_PRIMARY_EVIDENCE"]
