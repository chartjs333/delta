from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/stage_a_primary_exactness.py"
SPEC = importlib.util.spec_from_file_location("stage_a_primary_exactness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

HEAD = "1" * 40
AUTHORIZATION_ID = "sha256:" + "a" * 64
RESULT_ID = "sha256:" + "b" * 64


def process_result() -> dict[str, object]:
    value: dict[str, object] = {
        field: RESULT_ID
        for field in MODULE.PROCESS_RESULT_FIELDS
        if field.endswith("_id") or field.endswith("_sha256")
    }
    value.update(
        {
            "committee_qc_ids": ["sha256:" + character * 64 for character in "cdef0"],
            "benchmark_definition_id": MODULE.DEFINITION_ID,
            "flat_result_id": RESULT_ID,
            "formal_semantics_id": MODULE.FORMAL_ID,
            "hierarchical_result_id": RESULT_ID,
            "primary_ticket_count": 32,
            "primary_token_budget": 32_768,
            "primary_tokens_per_ticket": 1_024,
            "schema_version": "1.0.0",
            "status": "PASS",
            "type_name": "PRIMARY_EXACTNESS_PROCESS_RESULT",
        }
    )
    return value


def common_lane() -> dict[str, object]:
    return {
        "authorization_id": AUTHORIZATION_ID,
        "benchmark_definition_id": MODULE.DEFINITION_ID,
        "control_head": HEAD,
        "formal_semantics_id": MODULE.FORMAL_ID,
        "schema_version": "1.0.0",
        "source_commit": MODULE.SOURCE_COMMIT,
        "source_tree": MODULE.SOURCE_TREE,
        "status": "PASS",
    }


def valid_lanes() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    result = process_result()
    process_output_id = MODULE.sha256_id(MODULE.canonical_bytes(result) + b"\n")
    native = []
    for compiler, standard in MODULE.NATIVE_MATRIX:
        lane = common_lane()
        lane.update(
            {
                "compiler": compiler,
                "ctest_junit_sha256": RESULT_ID,
                "independent_process_count": 4,
                "native_tests": sorted(MODULE.REQUIRED_NATIVE_TESTS),
                "process_output_sha256": process_output_id,
                "process_result": result,
                "standard": standard,
                "type_name": "PRIMARY_EXACTNESS_NATIVE_LANE",
            }
        )
        native.append(lane)
    java = []
    for feature, expected in MODULE.JDK_MATRIX.items():
        lane = common_lane()
        lane.update(
            {
                "archive_sha256": expected["archive_sha256"],
                "checks": sorted(MODULE.REQUIRED_JAVA_CHECKS),
                "jdk_feature": feature,
                "jdk_version": expected["version"],
                "log_sha256": RESULT_ID,
                "type_name": "PRIMARY_EXACTNESS_JAVA_LANE",
            }
        )
        java.append(lane)
    return native, java


def test_complete_matrix_admits_only_stage_b_entry_condition() -> None:
    native, java = valid_lanes()
    report = MODULE.aggregate_documents(native, java, workflow_run_id="123", workflow_head=HEAD)
    assert report["status"] == "PASS"
    assert report["stage_b_entry_condition_satisfied"] is True
    assert report["primary_scientific_execution_count"] == 0
    assert report["feature_010_decision"] == "NO_GO"
    assert report["result_qc_authorized"] is False


def test_missing_native_lane_fails_closed() -> None:
    native, java = valid_lanes()
    with pytest.raises(MODULE.StageAError, match="NATIVE_LANE_COUNT:3"):
        MODULE.aggregate_documents(native[:-1], java, workflow_run_id="123", workflow_head=HEAD)


def test_cross_compiler_result_drift_fails_closed() -> None:
    native, java = valid_lanes()
    mutated = copy.deepcopy(native)
    mutated[0]["process_output_sha256"] = "sha256:" + "9" * 64
    with pytest.raises(MODULE.StageAError, match="CROSS_COMPILER_OUTPUT_DRIFT"):
        MODULE.aggregate_documents(mutated, java, workflow_run_id="123", workflow_head=HEAD)


def test_incomplete_java_negative_matrix_fails_closed() -> None:
    native, java = valid_lanes()
    java[0]["checks"] = java[0]["checks"][:-1]
    with pytest.raises(MODULE.StageAError, match="JAVA_CHECK_SET_INCOMPLETE"):
        MODULE.aggregate_documents(native, java, workflow_run_id="123", workflow_head=HEAD)
