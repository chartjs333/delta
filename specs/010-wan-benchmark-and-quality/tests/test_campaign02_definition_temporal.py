from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_campaign02_definition_temporal.py"
)
SPEC = importlib.util.spec_from_file_location("campaign02_definition_temporal", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_campaign02_definition_and_attestation_have_distinct_ordered_commits() -> None:
    head = MODULE.git("rev-parse", "HEAD")
    definition_commit = MODULE.first_commit(MODULE.DEFINITION_PATH, head)
    attestation_commit = MODULE.first_commit(MODULE.ATTESTATION_PATH, head)
    assert definition_commit != attestation_commit
    assert MODULE.is_ancestor(MODULE.REMEDIATION_MERGE, definition_commit)
    assert MODULE.is_ancestor(definition_commit, attestation_commit)


def test_campaign02_path_classifier_finds_every_prohibited_class() -> None:
    prefix = "reports/benchmark/campaigns/campaign-02/"
    counts = MODULE.prohibited_counts(
        [
            prefix + "benchmark-result-qc.json",
            prefix + "execution-authorization.json",
            prefix + "observations/one.json",
            prefix + "real-wan/one.json",
            prefix + "stage-a/receipt.json",
            prefix + "stage-b/observation.json",
            prefix + "stage-c/observation.json",
        ]
    )
    assert counts == {
        "benchmark_result_qc": 1,
        "execution_authorizations": 1,
        "primary_observations": 1,
        "real_wan_observations": 1,
        "scientific_observations": 1,
        "stage_a_receipts": 1,
        "stage_c_observations": 1,
    }


def test_campaign02_current_tree_has_no_prohibited_execution_artifacts() -> None:
    head = MODULE.git("rev-parse", "HEAD")
    counts = MODULE.prohibited_counts(MODULE.campaign_paths(head))
    assert counts
    assert all(value == 0 for value in counts.values())


def test_campaign02_temporal_evidence_is_current_and_fail_closed() -> None:
    current = MODULE.json.loads(MODULE.OUTPUT_PATH.read_bytes())
    expected = MODULE.build(current["verified_head"])
    assert MODULE.OUTPUT_PATH.read_bytes() == MODULE.canonical_json_bytes(expected) + b"\n"
    assert current["status"] == "PASS_AWAITING_SEPARATE_C2_016_GOVERNANCE"
    assert current["definition_created_commit"] == ("a2eaf47e17c616e78a4ec4666fcb33c030a765e6")
    assert current["definition_attestation_finalized_commit"] == (
        "d2c8576857f684e1eacbc952756fc59f3cfcf40f"
    )
    assert current["verifier_commit"] == "d68907453d898161066c472d48527527f9458812"
    assert all(value == 0 for value in current["observation_counts"].values())
    assert current["benchmark_result_qc"] == "ABSENT"
    assert current["execution_authorization"] == "ABSENT"
    assert all(value is False for value in current["authorization"].values())


def test_campaign02_terminal_receipt_verifies_actual_checkout_head() -> None:
    head = MODULE.git("rev-parse", "HEAD")
    receipt = MODULE.build_terminal_receipt(head, "LOCAL_TEST")
    assert receipt["actual_head"] == head
    assert receipt["snapshot_verified_head"] == ("d68907453d898161066c472d48527527f9458812")
    assert receipt["status"] == "PASS_TERMINAL_HEAD_NO_EXECUTION"
    assert all(value == 0 for value in receipt["prohibited_artifact_counts"].values())


def test_campaign02_observation_after_old_snapshot_rejects_terminal_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    head = MODULE.git("rev-parse", "HEAD")
    campaign_paths = MODULE.campaign_paths
    current_paths = campaign_paths(head)
    monkeypatch.setattr(
        MODULE,
        "campaign_paths",
        lambda commit: (
            [
                *current_paths,
                "reports/benchmark/campaigns/campaign-02/observations/post-snapshot.json",
            ]
            if commit == head
            else campaign_paths(commit)
        ),
    )
    with pytest.raises(MODULE.TemporalIntegrityError, match="TERMINAL_HEAD_ARTIFACT_PRESENT"):
        MODULE.build_terminal_receipt(head, "LOCAL_TEST")
