"""Execute and aggregate the authorized Stage A primary-exactness evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
AUTHORIZATION: Final = ROOT / "reports/benchmark/primary-execution-authorization.json"
DEFINITION: Final = ROOT / "configs/benchmark/primary.yaml"
ATTESTATION: Final = ROOT / "configs/benchmark/primary-definition-attestation.json"
DEFAULT_OUTPUT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/primary-exactness.json"

DEFINITION_ID: Final = "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244"
ATTESTATION_ID: Final = "sha256:3b92d83ae0e4e98f52ff9126b5efb4381e26d8977b5cf64eb2762f0533207fe5"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SOURCE_COMMIT: Final = "c460f3003277bb81db86f9afc1d7211e27870001"
SOURCE_TREE: Final = "d34d6b5b434bd5a81b7b202380ac500435c9b75d"
EXECUTOR_MERGE_COMMIT: Final = "ab71af60d3731a55f98b27c8d787be40c3b7a171"
EXECUTOR_WORKFLOW_RUN: Final = 33358317458

NATIVE_MATRIX: Final = frozenset(
    {("g++", "20"), ("g++", "23"), ("clang++", "20"), ("clang++", "23")}
)
JDK_MATRIX: Final = {
    "25": {
        "archive_sha256": "dbb698396d478e7fa2b1e50f4103324b2a99b90569ee27c33f2261f9215cf41e",
        "version": "25.0.4.1",
    },
    "26": {
        "archive_sha256": "56f768372f6ca1e2eb4c5f46b78f627949e8dcfe9c9723926cf45a45faf35802",
        "version": "26.0.2",
    },
}
REQUIRED_NATIVE_TESTS: Final = frozenset(
    {
        "delta_core.certificates",
        "delta_ffi.abi",
        "delta_ffi.certificates",
        "delta_ffi.hierarchy",
        "delta_ffi.scheduling",
        "delta_runtime.behavior",
    }
)
REQUIRED_JAVA_CHECKS: Final = frozenset(
    {
        "BenchmarkConformance",
        "CertificatesConformance",
        "HierarchyConformance",
        "NativeRuntimeFfmConformance",
        "SchedulingConformance",
    }
)
PROCESS_RESULT_FIELDS: Final = frozenset(
    {
        "aggregate_root_qc_id",
        "apply_candidate_id",
        "apply_qc_id",
        "benchmark_definition_id",
        "checkpoint_id",
        "checkpoint_wal_sha256",
        "committee_qc_ids",
        "effect_set_id",
        "flat_result_id",
        "formal_semantics_id",
        "hierarchical_assembly_id",
        "hierarchical_result_id",
        "input_set_certificate_id",
        "parameter_shard_qc_id",
        "primary_ticket_count",
        "primary_token_budget",
        "primary_tokens_per_ticket",
        "protocol_result_id",
        "robust_plan_id",
        "runtime_state_id",
        "runtime_wal_sha256",
        "schema_version",
        "status",
        "type_name",
    }
)


class StageAError(RuntimeError):
    """Stable fail-closed Stage A error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise StageAError(f"{code}:{detail}" if detail else code)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def sha256_id(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical_document(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    require(isinstance(value, dict), "JSON_OBJECT_REQUIRED", str(path))
    require(
        raw in {canonical_bytes(value), canonical_bytes(value) + b"\n"}, "NONCANONICAL", str(path)
    )
    return value


def write_create_only(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def git(source_root: Path, *arguments: str) -> str:
    process = subprocess.run(
        ("git", "-C", str(source_root), *arguments),
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(process.returncode == 0, "GIT_FAILED", process.stderr.strip())
    return process.stdout.strip()


def verify_exact_source(source_root: Path) -> None:
    require(source_root.is_dir(), "SOURCE_ROOT_MISSING", str(source_root))
    require(git(source_root, "rev-parse", "HEAD") == SOURCE_COMMIT, "SOURCE_COMMIT_MISMATCH")
    require(
        git(source_root, "show", "-s", "--format=%T", "HEAD") == SOURCE_TREE,
        "SOURCE_TREE_MISMATCH",
    )
    require(not git(source_root, "status", "--porcelain"), "SOURCE_TREE_DIRTY")


def verify_control() -> str:
    authorization_raw = AUTHORIZATION.read_bytes()
    authorization = canonical_document(AUTHORIZATION)
    definition = canonical_document(DEFINITION)
    attestation = canonical_document(ATTESTATION)
    require(authorization.get("status") == "APPROVED_STAGED", "AUTHORIZATION_STATUS")
    require(
        authorization.get("benchmark_definition_id") == DEFINITION_ID,
        "AUTHORIZATION_DEFINITION_ID",
    )
    require(
        authorization.get("definition_attestation_id") == ATTESTATION_ID,
        "AUTHORIZATION_ATTESTATION_ID",
    )
    require(authorization.get("formal_semantics_id") == FORMAL_ID, "AUTHORIZATION_FORMAL_ID")
    require(
        authorization.get("qualified_source_commit") == SOURCE_COMMIT,
        "AUTHORIZATION_SOURCE_COMMIT",
    )
    require(
        authorization.get("qualified_source_tree") == SOURCE_TREE,
        "AUTHORIZATION_SOURCE_TREE",
    )
    require(
        authorization.get("executor_merge_commit") == EXECUTOR_MERGE_COMMIT,
        "AUTHORIZATION_EXECUTOR_COMMIT",
    )
    require(
        authorization.get("executor_qualification_workflow") == EXECUTOR_WORKFLOW_RUN,
        "AUTHORIZATION_EXECUTOR_WORKFLOW",
    )
    require(authorization.get("real_wan_authorized") is False, "REAL_WAN_MUST_REMAIN_FALSE")
    require(
        authorization.get("benchmark_result_qc_authorized") is False,
        "RESULT_QC_MUST_REMAIN_FALSE",
    )
    require(
        authorization.get("feature_011_authorized") is False,
        "FEATURE_011_MUST_REMAIN_FALSE",
    )
    require(definition.get("source_commit") == SOURCE_COMMIT, "DEFINITION_SOURCE_COMMIT")
    require(definition.get("source_tree") == SOURCE_TREE, "DEFINITION_SOURCE_TREE")
    require(definition.get("formal_semantics_id") == FORMAL_ID, "DEFINITION_FORMAL_ID")
    require(attestation.get("benchmark_definition_id") == DEFINITION_ID, "ATTESTATION_DEFINITION")
    require(sha256_id(canonical_bytes(attestation)) == ATTESTATION_ID, "ATTESTATION_CONTENT_ID")
    require(
        not (ROOT / "reports/benchmark/primary/benchmark-result-qc.json").exists(),
        "BENCHMARK_RESULT_QC_FORBIDDEN",
    )
    return sha256_id(authorization_raw)


def verify_process_result(raw: bytes) -> dict[str, object]:
    require(raw.endswith(b"\n"), "PROCESS_RESULT_NEWLINE_MISSING")
    value = json.loads(raw)
    require(isinstance(value, dict), "PROCESS_RESULT_OBJECT_REQUIRED")
    require(set(value) == PROCESS_RESULT_FIELDS, "PROCESS_RESULT_FIELDS")
    require(raw == canonical_bytes(value) + b"\n", "PROCESS_RESULT_NONCANONICAL")
    require(value.get("schema_version") == "1.0.0", "PROCESS_RESULT_SCHEMA")
    require(value.get("type_name") == "PRIMARY_EXACTNESS_PROCESS_RESULT", "PROCESS_RESULT_TYPE")
    require(value.get("status") == "PASS", "PROCESS_RESULT_STATUS")
    require(value.get("formal_semantics_id") == FORMAL_ID, "PROCESS_RESULT_FORMAL_ID")
    require(value.get("benchmark_definition_id") == DEFINITION_ID, "PROCESS_RESULT_DEFINITION_ID")
    require(value.get("primary_ticket_count") == 32, "PRIMARY_TICKET_COUNT")
    require(value.get("primary_token_budget") == 32_768, "PRIMARY_TOKEN_BUDGET")
    require(value.get("primary_tokens_per_ticket") == 1_024, "PRIMARY_TOKENS_PER_TICKET")
    require(
        int(value["primary_ticket_count"]) * int(value["primary_tokens_per_ticket"])
        == int(value["primary_token_budget"]),
        "PRIMARY_WORKLOAD_RECONCILIATION",
    )
    require(value.get("flat_result_id") == value.get("hierarchical_result_id"), "HIERARCHY_DRIFT")
    for key, item in value.items():
        if key.endswith("_id") or key.endswith("_sha256"):
            require(
                isinstance(item, str) and len(item) == 71 and item.startswith("sha256:"), "ID", key
            )
    committee_ids = value.get("committee_qc_ids")
    require(isinstance(committee_ids, list) and len(committee_ids) == 5, "COMMITTEE_QC_IDS")
    require(len(set(committee_ids)) == 5, "COMMITTEE_QC_IDS_DUPLICATE")
    require(
        all(
            isinstance(item, str) and len(item) == 71 and item.startswith("sha256:")
            for item in committee_ids
        ),
        "COMMITTEE_QC_ID_INVALID",
    )
    return value


def verified_ctest_names(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    names: set[str] = set()
    for case in root.iter("testcase"):
        name = case.attrib.get("name", "")
        require(case.find("failure") is None, "NATIVE_TEST_FAILED", name)
        require(case.find("error") is None, "NATIVE_TEST_ERROR", name)
        require(case.find("skipped") is None, "NATIVE_TEST_SKIPPED", name)
        names.add(name)
    require(names == REQUIRED_NATIVE_TESTS, "NATIVE_TEST_SET", ",".join(sorted(names)))
    return sorted(names)


def native_lane(arguments: argparse.Namespace) -> dict[str, object]:
    authorization_id = verify_control()
    verify_exact_source(arguments.source_root)
    require((arguments.compiler, arguments.standard) in NATIVE_MATRIX, "NATIVE_LANE_INVALID")
    tests = verified_ctest_names(arguments.ctest_junit)
    run_root: Path = arguments.run_root
    run_root.mkdir(parents=True, exist_ok=False)
    raw_results: list[bytes] = []
    for repetition in range(1, 5):
        output_dir = run_root / f"process-{repetition}"
        process = subprocess.run(
            (str(arguments.probe), str(output_dir)),
            check=False,
            capture_output=True,
        )
        require(process.returncode == 0, "PROBE_FAILED", str(repetition))
        require(not process.stderr, "PROBE_STDERR", str(repetition))
        verify_process_result(process.stdout)
        raw_results.append(process.stdout)
    require(len(set(raw_results)) == 1, "INDEPENDENT_PROCESS_DRIFT")
    process_result = verify_process_result(raw_results[0])
    head = git(ROOT, "rev-parse", arguments.control_head)
    report = {
        "authorization_id": authorization_id,
        "benchmark_definition_id": DEFINITION_ID,
        "compiler": arguments.compiler,
        "control_head": head,
        "ctest_junit_sha256": sha256_id(arguments.ctest_junit.read_bytes()),
        "formal_semantics_id": FORMAL_ID,
        "independent_process_count": 4,
        "native_tests": tests,
        "process_output_sha256": sha256_id(raw_results[0]),
        "process_result": process_result,
        "schema_version": "1.0.0",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "standard": arguments.standard,
        "status": "PASS",
        "type_name": "PRIMARY_EXACTNESS_NATIVE_LANE",
    }
    write_create_only(arguments.output, report)
    print(canonical_bytes(report).decode())
    return report


def java_lane(arguments: argparse.Namespace) -> dict[str, object]:
    authorization_id = verify_control()
    verify_exact_source(arguments.source_root)
    expected = JDK_MATRIX.get(arguments.feature)
    require(expected is not None, "JDK_FEATURE_INVALID", arguments.feature)
    require(arguments.version == expected["version"], "JDK_VERSION_MISMATCH")
    require(arguments.archive_sha256 == expected["archive_sha256"], "JDK_ARCHIVE_MISMATCH")
    log = arguments.log.read_bytes()
    require(bool(log), "JAVA_LOG_EMPTY")
    decoded_log = log.decode("utf-8", errors="strict")
    require(arguments.version in decoded_log, "JDK_VERSION_LOG_MISSING")
    prefix = "STAGE_A_JAVA_PASS "
    markers = [line[len(prefix) :] for line in decoded_log.splitlines() if line.startswith(prefix)]
    checks = set(markers)
    require(checks == REQUIRED_JAVA_CHECKS, "JAVA_CHECK_SET", ",".join(sorted(checks)))
    require(len(markers) == len(REQUIRED_JAVA_CHECKS), "JAVA_CHECK_DUPLICATE")
    head = git(ROOT, "rev-parse", arguments.control_head)
    report = {
        "archive_sha256": arguments.archive_sha256,
        "authorization_id": authorization_id,
        "benchmark_definition_id": DEFINITION_ID,
        "checks": sorted(checks),
        "control_head": head,
        "formal_semantics_id": FORMAL_ID,
        "jdk_feature": arguments.feature,
        "jdk_version": arguments.version,
        "log_sha256": sha256_id(log),
        "schema_version": "1.0.0",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "status": "PASS",
        "type_name": "PRIMARY_EXACTNESS_JAVA_LANE",
    }
    write_create_only(arguments.output, report)
    print(canonical_bytes(report).decode())
    return report


def lane_content_id(lane: dict[str, object]) -> str:
    return sha256_id(canonical_bytes(lane))


def aggregate_documents(
    native: list[dict[str, object]],
    java: list[dict[str, object]],
    *,
    workflow_run_id: str,
    workflow_head: str,
) -> dict[str, object]:
    require(len(native) == 4, "NATIVE_LANE_COUNT", str(len(native)))
    require(len(java) == 2, "JAVA_LANE_COUNT", str(len(java)))
    native_matrix = {(str(item.get("compiler")), str(item.get("standard"))) for item in native}
    require(native_matrix == NATIVE_MATRIX, "NATIVE_MATRIX_INCOMPLETE")
    java_matrix = {str(item.get("jdk_feature")) for item in java}
    require(java_matrix == set(JDK_MATRIX), "JDK_MATRIX_INCOMPLETE")
    all_lanes = native + java
    for lane in all_lanes:
        require(lane.get("status") == "PASS", "LANE_STATUS")
        require(lane.get("benchmark_definition_id") == DEFINITION_ID, "LANE_DEFINITION")
        require(lane.get("formal_semantics_id") == FORMAL_ID, "LANE_FORMAL")
        require(lane.get("source_commit") == SOURCE_COMMIT, "LANE_SOURCE_COMMIT")
        require(lane.get("source_tree") == SOURCE_TREE, "LANE_SOURCE_TREE")
        require(lane.get("control_head") == workflow_head, "LANE_CONTROL_HEAD")
        require(lane.get("schema_version") == "1.0.0", "LANE_SCHEMA")
    authorization_ids = {str(item.get("authorization_id")) for item in all_lanes}
    require(len(authorization_ids) == 1, "AUTHORIZATION_ID_DRIFT")
    output_ids = {str(item.get("process_output_sha256")) for item in native}
    require(len(output_ids) == 1, "CROSS_COMPILER_OUTPUT_DRIFT")
    results = [item.get("process_result") for item in native]
    require(all(result == results[0] for result in results), "CROSS_COMPILER_RESULT_DRIFT")
    require(isinstance(results[0], dict), "PROCESS_RESULT_MISSING")
    verify_process_result(canonical_bytes(results[0]) + b"\n")
    for lane in native:
        require(lane.get("type_name") == "PRIMARY_EXACTNESS_NATIVE_LANE", "NATIVE_LANE_TYPE")
        require(lane.get("independent_process_count") == 4, "NATIVE_PROCESS_COUNT")
        native_tests = lane.get("native_tests")
        require(isinstance(native_tests, list), "NATIVE_TEST_SET_TYPE")
        require(set(native_tests) == REQUIRED_NATIVE_TESTS, "NATIVE_TEST_SET")
        require(
            lane.get("process_output_sha256")
            == sha256_id(canonical_bytes(lane["process_result"]) + b"\n"),
            "PROCESS_OUTPUT_DIGEST",
        )
        require(
            isinstance(lane.get("ctest_junit_sha256"), str)
            and len(str(lane["ctest_junit_sha256"])) == 71,
            "CTEST_DIGEST",
        )
    for lane in java:
        require(lane.get("type_name") == "PRIMARY_EXACTNESS_JAVA_LANE", "JAVA_LANE_TYPE")
        checks = lane.get("checks")
        require(isinstance(checks, list), "JAVA_CHECK_SET_TYPE")
        require(set(checks) == REQUIRED_JAVA_CHECKS, "JAVA_CHECK_SET_INCOMPLETE")
        expected = JDK_MATRIX[str(lane["jdk_feature"])]
        require(lane.get("jdk_version") == expected["version"], "JDK_VERSION_DRIFT")
        require(lane.get("archive_sha256") == expected["archive_sha256"], "JDK_ARCHIVE_DRIFT")
        require(
            isinstance(lane.get("log_sha256"), str) and len(str(lane["log_sha256"])) == 71,
            "JAVA_LOG_DIGEST",
        )
    return {
        "authorization_id": next(iter(authorization_ids)),
        "benchmark_definition_id": DEFINITION_ID,
        "checks": {
            "abi_schema_formal_mismatch_negatives": "PASS",
            "cross_compiler_standard_exactness": "PASS",
            "direct_copy_ffm_parity": "PASS",
            "flat_hierarchy_exactness": "PASS",
            "independent_process_exactness": "PASS",
            "netty_boundary_negative_matrix": "PASS",
            "pointer_lifetime_negatives": "PASS",
            "runtime_wal_effect_current_recovery": "PASS",
        },
        "control_head": workflow_head,
        "feature_010_decision": "NO_GO",
        "feature_011_authorized": False,
        "formal_semantics_id": FORMAL_ID,
        "java_lanes": [
            {"content_id": lane_content_id(item), "jdk_feature": item["jdk_feature"]}
            for item in sorted(java, key=lambda value: str(value["jdk_feature"]))
        ],
        "limitations": [
            "NO_PRIMARY_SCIENTIFIC_RUNS_EXECUTED",
            "NO_PRIMARY_EMULATED_MULTI_HOST_RUNS_EXECUTED",
            "NO_APPROVED_REAL_WAN_EXECUTION",
            "NO_BENCHMARK_RESULT_QC",
        ],
        "native_lanes": [
            {
                "compiler": item["compiler"],
                "content_id": lane_content_id(item),
                "standard": item["standard"],
            }
            for item in sorted(
                native, key=lambda value: (str(value["compiler"]), str(value["standard"]))
            )
        ],
        "primary_exactness_result": results[0],
        "primary_scientific_execution_count": 0,
        "real_wan_authorized": False,
        "result_qc_authorized": False,
        "schema_version": "1.0.0",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "stage_b_entry_condition_satisfied": True,
        "status": "PASS",
        "task_ids": ["T028", "T029", "HR010-006", "HR010-010", "HR010-011"],
        "type_name": "PRIMARY_EXACTNESS_EVIDENCE",
        "workflow_run_id": workflow_run_id,
    }


def aggregate(arguments: argparse.Namespace) -> dict[str, object]:
    authorization_id = verify_control()
    native_paths = sorted(arguments.lanes_dir.rglob("stage-a-native-lane.json"))
    java_paths = sorted(arguments.lanes_dir.rglob("stage-a-java-lane.json"))
    native = [canonical_document(path) for path in native_paths]
    java = [canonical_document(path) for path in java_paths]
    workflow_head = git(ROOT, "rev-parse", arguments.workflow_head)
    report = aggregate_documents(
        native,
        java,
        workflow_run_id=arguments.workflow_run_id,
        workflow_head=workflow_head,
    )
    require(report["authorization_id"] == authorization_id, "CONTROL_AUTHORIZATION_ID_DRIFT")
    write_create_only(arguments.output, report)
    print(canonical_bytes(report).decode())
    return report


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    native = commands.add_parser("native-lane")
    native.add_argument("--source-root", type=Path, required=True)
    native.add_argument("--probe", type=Path, required=True)
    native.add_argument("--compiler", required=True)
    native.add_argument("--standard", required=True)
    native.add_argument("--ctest-junit", type=Path, required=True)
    native.add_argument("--run-root", type=Path, required=True)
    native.add_argument("--control-head", required=True)
    native.add_argument("--output", type=Path, required=True)
    native.set_defaults(function=native_lane)

    java = commands.add_parser("java-lane")
    java.add_argument("--source-root", type=Path, required=True)
    java.add_argument("--feature", required=True)
    java.add_argument("--version", required=True)
    java.add_argument("--archive-sha256", required=True)
    java.add_argument("--log", type=Path, required=True)
    java.add_argument("--control-head", required=True)
    java.add_argument("--output", type=Path, required=True)
    java.set_defaults(function=java_lane)

    aggregate_parser = commands.add_parser("aggregate")
    aggregate_parser.add_argument("--lanes-dir", type=Path, required=True)
    aggregate_parser.add_argument("--workflow-run-id", required=True)
    aggregate_parser.add_argument("--workflow-head", required=True)
    aggregate_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    aggregate_parser.set_defaults(function=aggregate)
    return root


def main() -> int:
    arguments = parser().parse_args()
    try:
        arguments.function(arguments)
    except (FileExistsError, json.JSONDecodeError, OSError, StageAError, ET.ParseError) as error:
        print(f"STAGE_A_STOP:{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
