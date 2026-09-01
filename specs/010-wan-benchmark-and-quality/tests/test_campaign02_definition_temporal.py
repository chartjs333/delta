from __future__ import annotations

import importlib.util
from pathlib import Path

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
