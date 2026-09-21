#!/usr/bin/env python3
"""Build and verify current-lineage Feature 010 exactness-only evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
PROFILE_DECISION_PATH: Final = (
    ROOT / "specs/010-wan-benchmark-and-quality/profile-risk-decision.json"
)
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
BASE_COMMIT: Final = "6f99ab1622aa4bb96dab29979ce11af8bd4c5f89"
DEFINITION_ID: Final = "sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449"
EXPECTED_CORPUS_IDS: Final = [
    "sha256:476b466992370b989ac24ef63569bb179b1c3ac9e215b8ce01fe68054c5c9b73",
    "sha256:0ce29dfbdab797db41850031ec6ee4fdd01fe8ea34ec1e4e0a63ba31ced39892",
    DEFINITION_ID,
    "sha256:4ae1806f1ce4fb165d698f6d28648e4287b47689332c8859df008695ad8b6308",
    "sha256:50c42bee228b98c5bb58238251ef897fdc2a2286027f4f2f011dfc86b6e8efbb",
    "sha256:1f29322d968fd99538395765dafea1cc37c6d052cdb5160ca543b289d7b95faa",
    "sha256:e837f264cc59a92a1537aa24d44cefe9410008f2c826a5c50e3172455309e2cc",
]
EXPECTED_LANES: Final = {
    ("gcc", 20),
    ("gcc", 23),
    ("clang", 20),
    ("clang", 23),
}
EXPECTED_TOOLCHAINS: Final = {
    "gcc": {
        "image": (
            "docker.io/library/gcc@sha256:"
            "82549aa8f90ada3236a8be70c74543132a76662ef33f0c3271ed802b81584a82"
        ),
        "version_pattern": "g++ (GCC) 14.2.0",
    },
    "clang": {
        "image": (
            "docker.io/silkeh/clang@sha256:"
            "ae2f3deffd84470fbb2904cfb990db208a5f9880b4bcf9d3eae080a50a8900b4"
        ),
        "version_pattern": "clang version 20.1.8",
    },
}
EXPECTED_PROFILE_RISK_DECISION: Final = {
    "authority": {
        "feature010_go": False,
        "pilot_execution_authorized": False,
        "primary_observation_count": 0,
    },
    "available_profile": "EMBEDDED_FFM",
    "comparison_policy": {
        "crash_containment": "EMBEDDED_COFAILURE_ONLY_NO_ISOLATION_CLAIM",
        "latency": "NOT_COMPARABLE_WHEN_SIDECAR_OMITTED",
        "restart_replay": "EMBEDDED_ONLY",
        "throughput": "NOT_COMPARABLE_WHEN_SIDECAR_OMITTED",
    },
    "formal_impact": "NO_SEMANTIC_CHANGE",
    "formal_semantics_id": FORMAL_ID,
    "isolated_sidecar": {
        "implementation_status": "NOT_IMPLEMENTED",
        "omission_reason": (
            "ADDING_CURRENT_LINEAGE_IPC_WOULD_EXPAND_RUNTIME_SCOPE_AND_REQUIRE_SEPARATE_FORMAL_REVIEW"
        ),
        "status": "OMITTED_BY_FORMAL_RISK_DECISION",
    },
    "schema_version": "1.0.0",
    "selected_profile": None,
    "selection_basis": "NO_SELECTION_SIDECAR_NOT_EVALUATED",
    "selection_scope": "BLOCKED_PENDING_IMMUTABLE_COMPARATIVE_BENCHMARK_EVIDENCE",
    "type_name": "FEATURE010_DEPLOYMENT_PROFILE_RISK_DECISION",
}
EXPECTED_TESTS: Final = {
    "delta_core.qlora_certificate_chain",
    "delta_core.qlora_apply",
    "delta_core.certificates",
    "delta_core.certificate_contract_fuzz",
    "delta_core.certificate_mutant_seed_parent",
    "delta_core.certificate_mutant_observed_coverage",
    "delta_core.certificate_mutant_coefficient",
    "delta_core.certificate_mutant_current",
    "delta_core.canonical",
    "delta_core.protocol",
    "delta_core.arithmetic",
    "delta_core.fixedpoint",
    "delta_core.direct_q",
    "delta_core.mutant_unchecked_count",
    "delta_core.shards",
    "delta_core.mutant_unbounded_header",
    "delta_core.mutant_skip_context",
    "delta_core.fixedpoint_parser_fuzz",
    "delta_core.distribution",
    "delta_core.distribution_mutant_allow_downgrade",
    "delta_core.distribution_mutant_allow_forbidden",
    "delta_core.distribution_mutant_allow_noncanonical",
    "delta_core.distribution_parser_fuzz",
    "delta_core.hierarchy",
    "delta_core.hierarchy_mutant_skip_coverage",
    "delta_core.hierarchy_mutant_skip_shard_coverage",
    "delta_core.hierarchy_mutant_unchecked_overflow",
    "delta_core.hierarchy_parser_fuzz",
    "delta_core.hierarchy_reduce",
    "delta_core.hierarchy_trace_export",
    "delta_core.hierarchy_mutant_partial_global",
    "delta_core.hierarchy_mutant_average_regions",
    "delta_core.scheduling_planner",
    "delta_core.scheduling_eligibility",
    "delta_core.scheduling_lifecycle",
    "delta_core.scheduling_trace_export",
    "delta_core.scheduling_mutant_expose_before_durability",
    "delta_core.scheduling_mutant_adapt_work",
    "delta_core.scheduling_mutant_overlap_ranges",
    "delta_core.scheduling_mutant_skip_infeasibility",
    "delta_core.scheduling_contract_fuzz",
    "delta_core.transition",
    "delta_core.consensus",
    "delta_core.portability",
    "delta_core.prepared_100",
    "delta_runtime.target",
    "delta_runtime.behavior",
    "delta_runtime.trace_export",
    "delta_runtime.native_exit",
    "delta_ffi.target",
    "delta_ffi.abi",
    "delta_ffi.distribution",
    "delta_ffi.hierarchy",
    "delta_ffi.certificates",
    "delta_ffi.scheduling",
    "delta_ffi.qlora",
    "delta_ffi.fuzz_smoke",
}
REFINEMENT_FILES: Final = {
    "certificate-refinement.json",
    "hierarchy-refinement.json",
    "native-refinement.json",
    "scheduling-refinement.json",
}
PROCESS_FIELDS: Final = {
    "aggregate_root_qc_id",
    "aggregator_effect_root",
    "aggregator_state_root",
    "apply_candidate_id",
    "apply_effect_root",
    "apply_qc_id",
    "apply_state_root",
    "benchmark_definition_id",
    "current_wal_sha256",
    "declared_B",
    "declared_H",
    "execution_class",
    "feature010_go",
    "flat_result_id",
    "formal_semantics_id",
    "hierarchical_assembly_id",
    "hierarchical_result_id",
    "input_set_certificate_id",
    "parameter_shard_qc_id",
    "primary_observation_count",
    "primary_parameter_shape_bound",
    "processed_q_value_count",
    "protocol_result_id",
    "qualifying_gate_c",
    "qualifying_gate_d",
    "reduction_vector_width",
    "robust_plan_id",
    "schema_version",
    "status",
    "synthetic_contribution_count",
    "type_name",
    "validator_effect_root",
    "validator_process_count",
    "validator_receipts_sha256",
    "validator_state_root",
    "work_ticket_budget_exercised",
}
EXPECTED_GATES: Final = [
    {"gate_id": "XH-CANONICAL", "status": "PASS", "task_ids": ["HR010-004"]},
    {"gate_id": "XH-PORTABILITY", "status": "PASS", "task_ids": ["HR010-005"]},
    {
        "gate_id": "XH-PROCESSES",
        "status": "PASS_FIXTURE_SCALE_ONLY",
        "task_ids": ["T028"],
    },
    {
        "gate_id": "XH-PARITY",
        "status": "PASS_FIXTURE_SCALE_ONLY",
        "task_ids": ["HR010-006"],
    },
    {
        "gate_id": "XH-PRIMARY-SCALE",
        "status": "BLOCKED_MISSING_FROZEN_PRIMARY_PARAMETER_SHAPE",
        "task_ids": ["T028", "T029"],
    },
    {"gate_id": "XH-REFINEMENT", "status": "PASS", "task_ids": ["HR010-007"]},
    {
        "gate_id": "XH-SANITIZERS",
        "status": "REQUIRES_EXACT_HEAD_CI",
        "task_ids": ["HR010-008"],
    },
    {"gate_id": "XH-DURABILITY", "status": "PASS", "task_ids": ["HR010-009"]},
    {
        "gate_id": "XH-NETTY",
        "status": "REQUIRES_EXACT_HEAD_CI",
        "task_ids": ["HR010-010"],
    },
    {
        "gate_id": "XH-ABI",
        "status": "REQUIRES_EXACT_HEAD_CI",
        "task_ids": ["HR010-011"],
    },
    {"gate_id": "XH-ATTACK-30", "status": "PASS", "task_ids": ["T030"]},
    {"gate_id": "XH-ATTACK-31", "status": "PASS", "task_ids": ["T031"]},
    {"gate_id": "XH-ATTACK-32", "status": "PASS", "task_ids": ["T032"]},
    {"gate_id": "XH-ATTACK-33", "status": "PASS", "task_ids": ["T033"]},
    {"gate_id": "XH-ANALYZER", "status": "PASS", "task_ids": ["T034"]},
    {
        "gate_id": "XH-SIDECAR",
        "status": "PASS_PREREGISTERED_OMISSION_RISK_DECISION",
        "task_ids": ["HR010-012"],
    },
    {
        "gate_id": "XH-PROFILES",
        "status": "BLOCKED_SIDECAR_NOT_EVALUATED",
        "task_ids": ["HR010-013"],
    },
    {
        "gate_id": "XH-PILOT",
        "status": "BLOCKED_NO_COMPARATIVE_BENCHMARK_EVIDENCE",
        "task_ids": ["HR010-014"],
    },
]
QUALIFICATION_BLOCKERS: Final = [
    {
        "affected_task_ids": ["T028", "T029"],
        "blocker_id": "PRIMARY_WORKLOAD_SCALE_UNBOUND",
        "formal_escalation": "NOT_REQUIRED_FOR_CURRENT_BLOCKER",
        "owner": "FEATURE010_DEFINITION_AND_EXECUTION_AUTHORITY",
        "reason": (
            "CURRENT_LINEAGE_HAS_DECLARED_B_H_BUT_NO_FROZEN_PRIMARY_PARAMETER_SHAPE_"
            "OR_ELIGIBLE_WORK_TICKET_EXECUTION"
        ),
        "requires_formal_change": False,
        "requires_formal_review": False,
    },
    {
        "affected_task_ids": ["HR010-013", "HR010-014"],
        "blocker_id": "ISOLATED_SIDECAR_NOT_IMPLEMENTED",
        "formal_escalation": "ONLY_IF_NEW_EXTERNALLY_VISIBLE_STATE_OR_OUTCOME_IS_REQUIRED",
        "owner": "RUNTIME_PROFILE_IMPLEMENTATION_AND_EVIDENCE",
        "reason": "CURRENT_LINEAGE_IPC_AND_COMPARATIVE_PROFILE_EVIDENCE_ARE_ABSENT",
        "requires_formal_change": False,
        "requires_formal_review": False,
        "future_formal_review_required": True,
        "formal_review_trigger": "BEFORE_ISOLATED_SIDECAR_IMPLEMENTATION",
    },
]
ATTACK_COVERAGE: Final = [
    {
        "attack_id": "CONFLICTING_CONFIG_COMMIT_OR_VOTE",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T030",
        "tests": ["delta_core.certificates", "delta_core.consensus"],
    },
    {
        "attack_id": "SEED_BEFORE_ISC",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T030",
        "tests": ["delta_core.certificates"],
    },
    {
        "attack_id": "ACCUMULATOR_CERTIFICATE_MUTATION",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T030",
        "tests": ["delta_core.certificate_mutant_coefficient", "delta_core.certificates"],
    },
    {
        "attack_id": "MIXED_VIEW_FRANKENSTEIN",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T031",
        "tests": ["delta_core.certificates", "delta_core.hierarchy_reduce"],
    },
    {
        "attack_id": "INCOMPLETE_OR_DUPLICATE_AGGREGATE",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T031",
        "tests": ["delta_core.certificates", "delta_core.hierarchy_reduce"],
    },
    {
        "attack_id": "WRONG_EPOCH",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T031",
        "tests": ["delta_core.certificates", "delta_core.hierarchy_reduce"],
    },
    {
        "attack_id": "UNSAFE_ACCUMULATOR_OR_RUNTIME_OVERFLOW",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T032",
        "tests": [
            "delta_core.arithmetic",
            "delta_core.hierarchy_mutant_unchecked_overflow",
            "delta_runtime.behavior",
        ],
    },
    {
        "attack_id": "CONFLICTING_APPLY_QC",
        "expected_terminal": "REJECT_PARENT_CURRENT_PRESERVED",
        "status": "PASS",
        "task_id": "T032",
        "tests": ["delta_core.certificates", "delta_runtime.native_exit"],
    },
    {
        "attack_id": "P2P_CERTIFICATE_DOWNGRADE",
        "expected_terminal": "REJECT_NO_DESCENDANT_QC_OR_CURRENT",
        "status": "PASS",
        "task_id": "T033",
        "tests": [
            "delta_core.distribution",
            "delta_core.distribution_mutant_allow_downgrade",
        ],
    },
]


class ExactnessError(RuntimeError):
    """Stable fail-closed exactness evidence error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ExactnessError(f"{code}:{detail}" if detail else code)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_id(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def git_text(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True, text=True
    )
    require(process.returncode == 0, "GIT_FAILED", process.stderr.strip())
    return process.stdout.strip()


def canonical_document(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExactnessError(f"JSON_INVALID:{path.name}") from error
    require(isinstance(value, dict), "JSON_OBJECT_REQUIRED", path.name)
    encoded = canonical_bytes(value)
    require(raw in {encoded, encoded + b"\n"}, "JSON_NOT_CANONICAL", path.name)
    return value, encoded


def validate_process(value: dict[str, Any]) -> None:
    require(set(value) == PROCESS_FIELDS, "PROCESS_FIELDS_INVALID")
    require(value["type_name"] == "FEATURE010_EXACTNESS_PROCESS_RESULT", "PROCESS_TYPE")
    require(value["schema_version"] == "1.0.0", "PROCESS_SCHEMA")
    require(value["status"] == "PASS", "PROCESS_STATUS")
    require(value["formal_semantics_id"] == FORMAL_ID, "PROCESS_FORMAL_ID")
    require(value["execution_class"] == "CONFORMANCE_SAFETY_FAULT_ONLY", "PROCESS_CLASS")
    require(value["declared_B"] == 64 and value["declared_H"] == 16, "PROCESS_DECLARED_SCALE")
    require(
        value["synthetic_contribution_count"] == 16
        and value["reduction_vector_width"] == 4
        and value["processed_q_value_count"] == 64,
        "PROCESS_FIXTURE_SHAPE",
    )
    require(
        value["primary_parameter_shape_bound"] is False
        and value["work_ticket_budget_exercised"] is False,
        "PROCESS_PRIMARY_SCALE_CLAIM_FORBIDDEN",
    )
    require(value["validator_process_count"] == 4, "VALIDATOR_PROCESS_COUNT")
    require(value["benchmark_definition_id"] == DEFINITION_ID, "PROCESS_DEFINITION_ID")
    require(value["flat_result_id"] == value["hierarchical_result_id"], "HIERARCHY_DRIFT")
    require(
        value["validator_state_root"] == value["aggregate_root_qc_id"]
        and value["aggregator_state_root"] == value["aggregate_root_qc_id"],
        "VALIDATOR_AGGREGATOR_STATE_DRIFT",
    )
    require(
        value["validator_effect_root"] == value["apply_candidate_id"]
        and value["aggregator_effect_root"] == value["apply_qc_id"],
        "VALIDATOR_AGGREGATOR_EFFECT_DRIFT",
    )
    require(value["primary_observation_count"] == 0, "PRIMARY_OBSERVATION_FORBIDDEN")
    require(value["qualifying_gate_c"] is False, "GATE_C_FORBIDDEN")
    require(value["qualifying_gate_d"] is False, "GATE_D_FORBIDDEN")
    require(value["feature010_go"] is False, "FEATURE010_GO_FORBIDDEN")
    for key, item in value.items():
        if key.endswith("_id") or key.endswith("_sha256") or key.endswith("_root"):
            require(
                isinstance(item, str) and item.startswith("sha256:") and len(item) == 71,
                "PROCESS_CONTENT_ID_INVALID",
                key,
            )


def validate_corpus(value: dict[str, Any]) -> None:
    require(
        set(value)
        == {
            "artifact_ids",
            "execution_class",
            "formal_semantics_id",
            "negative_statuses",
            "primary_observation_count",
            "schema_version",
            "status",
            "type_name",
        },
        "CORPUS_FIELDS",
    )
    require(value.get("type_name") == "FEATURE010_EXACTNESS_CORPUS", "CORPUS_TYPE")
    require(value.get("schema_version") == "1.0.0", "CORPUS_SCHEMA")
    require(value.get("formal_semantics_id") == FORMAL_ID, "CORPUS_FORMAL_ID")
    require(value.get("execution_class") == "CONFORMANCE_SAFETY_ONLY", "CORPUS_CLASS")
    require(value.get("primary_observation_count") == 0, "CORPUS_PRIMARY_FORBIDDEN")
    require(value.get("status") == "PASS", "CORPUS_STATUS")
    artifact_ids = value.get("artifact_ids")
    require(artifact_ids == EXPECTED_CORPUS_IDS, "CORPUS_IDS")
    require(
        len(set(artifact_ids)) == 7
        and all(
            isinstance(item, str) and item.startswith("sha256:") and len(item) == 71
            for item in artifact_ids
        ),
        "CORPUS_ID_FORMAT",
    )
    negatives = value.get("negative_statuses")
    require(
        negatives
        == [
            {
                "case_id": "definition-leading-space",
                "status": "JSON_BYTES_NOT_CANONICAL",
            },
            {
                "case_id": "run-primary-promotion",
                "status": "PRIMARY_ELIGIBILITY_FORBIDDEN",
            },
        ],
        "CORPUS_NEGATIVES",
    )


def source_identity(source_commit: str) -> dict[str, str]:
    commit = git_text("rev-parse", f"{source_commit}^{{commit}}")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_COMMIT, commit],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0,
        "BASE_NOT_ANCESTOR",
    )
    return {"commit": commit, "tree": git_text("rev-parse", f"{commit}^{{tree}}")}


def validate_receipt_directory(path: Path, process: dict[str, Any]) -> dict[str, Any]:
    expected_validator_names = {f"validator-{index}.json" for index in range(4)}
    files = {item.name for item in path.iterdir() if item.is_file()}
    require(files == expected_validator_names | {"aggregator.json"}, "RECEIPT_FILE_SET")
    validator_raw: dict[str, bytes] = {}
    validator_hashes = []
    for name in sorted(expected_validator_names):
        receipt, _ = canonical_document(path / name)
        require(
            set(receipt) == {"effect_root", "state_root", "validator_id"},
            "VALIDATOR_RECEIPT_FIELDS",
        )
        validator_id = receipt["validator_id"]
        require(validator_id == name.removesuffix(".json"), "VALIDATOR_RECEIPT_ID")
        require(receipt["state_root"] == process["validator_state_root"], "VALIDATOR_STATE")
        require(receipt["effect_root"] == process["validator_effect_root"], "VALIDATOR_EFFECT")
        raw = (path / name).read_bytes()
        validator_raw[validator_id] = raw
        validator_hashes.append({"path": name, "sha256": sha256_id(raw)})
    transcript = b"".join(
        validator_id.encode("utf-8") + b"\0" + validator_raw[validator_id]
        for validator_id in sorted(validator_raw)
    )
    require(
        sha256_id(transcript) == process["validator_receipts_sha256"],
        "VALIDATOR_RECEIPT_TRANSCRIPT",
    )
    aggregator, _ = canonical_document(path / "aggregator.json")
    require(
        aggregator
        == {
            "aggregator_effect_root": process["aggregator_effect_root"],
            "aggregator_state_root": process["aggregator_state_root"],
            "validator_effect_root": process["validator_effect_root"],
            "validator_process_count": 4,
            "validator_receipts_sha256": process["validator_receipts_sha256"],
            "validator_state_root": process["validator_state_root"],
        },
        "AGGREGATOR_RECEIPT",
    )
    return {
        "aggregator_sha256": sha256_id((path / "aggregator.json").read_bytes()),
        "validator_receipts": validator_hashes,
    }


def emit_native_lane(arguments: argparse.Namespace) -> dict[str, Any]:
    source = source_identity(arguments.source_commit)
    require((arguments.compiler, arguments.standard) in EXPECTED_LANES, "LANE_ID_INVALID")
    require(arguments.architecture == "x86_64", "LANE_ARCHITECTURE_INVALID")
    toolchain = EXPECTED_TOOLCHAINS[arguments.compiler]
    require(arguments.compiler_image == toolchain["image"], "LANE_COMPILER_IMAGE")
    require(
        toolchain["version_pattern"] in arguments.compiler_version,
        "LANE_COMPILER_VERSION",
    )
    require(arguments.elapsed_ns > 0, "LANE_DURATION_INVALID")
    require(len(arguments.process_output) == 4, "PROCESS_REPETITION_COUNT")
    require(
        len({path.resolve() for path in arguments.process_output}) == 4,
        "PROCESS_OUTPUT_PATHS_NOT_INDEPENDENT",
    )
    process_documents = [canonical_document(path) for path in arguments.process_output]
    for document, _ in process_documents:
        validate_process(document)
    process_encodings = {encoded for _, encoded in process_documents}
    require(len(process_encodings) == 1, "INDEPENDENT_PROCESS_DRIFT")
    process_encoded = process_encodings.pop()
    require(len(arguments.receipt_dir) == 4, "RECEIPT_DIRECTORY_COUNT")
    require(
        len({path.resolve() for path in arguments.receipt_dir}) == 4,
        "RECEIPT_DIRECTORIES_NOT_INDEPENDENT",
    )
    process_receipts = [
        validate_receipt_directory(path, process_documents[index][0])
        for index, path in enumerate(arguments.receipt_dir)
    ]
    corpus, corpus_encoded = canonical_document(arguments.corpus_output)
    validate_corpus(corpus)
    result = {
        "architecture": arguments.architecture,
        "compiler": arguments.compiler,
        "compiler_image": arguments.compiler_image,
        "compiler_version": arguments.compiler_version,
        "cpp_standard": arguments.standard,
        "diagnostic_elapsed_ns": arguments.elapsed_ns,
        "formal_semantics_id": FORMAL_ID,
        "process_output": process_documents[0][0],
        "process_output_sha256": sha256_id(process_encoded),
        "process_receipts": process_receipts,
        "process_repetitions": 4,
        "schema_version": "1.0.0",
        "shared_corpus_sha256": sha256_id(corpus_encoded),
        "source": source,
        "status": "PASS",
        "type_name": "FEATURE010_NATIVE_EXACTNESS_LANE",
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(canonical_bytes(result) + b"\n")
    return result


def junit_tests(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    names: set[str] = set()
    for case in root.iter("testcase"):
        name = case.attrib.get("name", "")
        require(bool(name), "JUNIT_NAME_MISSING")
        require(case.find("failure") is None, "JUNIT_FAILURE", name)
        require(case.find("error") is None, "JUNIT_ERROR", name)
        require(case.find("skipped") is None, "JUNIT_SKIPPED", name)
        require(name not in names, "JUNIT_DUPLICATE", name)
        names.add(name)
    require(names == EXPECTED_TESTS, "JUNIT_TEST_SET", ",".join(sorted(names ^ EXPECTED_TESTS)))
    return sorted(names)


def pass_document(path: Path) -> dict[str, str]:
    value, encoded = canonical_document(path)
    require(value.get("status") == "PASS", "REFINEMENT_NOT_PASS", path.name)
    require(value.get("formal_semantics_id") == FORMAL_ID, "REFINEMENT_FORMAL_ID", path.name)
    return {"path": path.name, "sha256": sha256_id(encoded), "status": "PASS"}


def load_lanes(root: Path) -> list[dict[str, Any]]:
    paths = sorted(root.rglob("lane.json"))
    require(len(paths) == 4, "LANE_FILE_COUNT", str(len(paths)))
    lanes = []
    for path in paths:
        value, _ = canonical_document(path)
        require(value.get("type_name") == "FEATURE010_NATIVE_EXACTNESS_LANE", "LANE_TYPE")
        require(value.get("status") == "PASS", "LANE_STATUS")
        require(value.get("formal_semantics_id") == FORMAL_ID, "LANE_FORMAL_ID")
        validate_process(value["process_output"])
        lanes.append(value)
    require(
        {(value["compiler"], value["cpp_standard"]) for value in lanes} == EXPECTED_LANES,
        "LANE_MATRIX_INCOMPLETE",
    )
    return lanes


def aggregate(arguments: argparse.Namespace) -> dict[str, Any]:
    source = source_identity(arguments.source_commit)
    lanes = load_lanes(arguments.lanes_dir)
    require(all(value["source"] == source for value in lanes), "LANE_SOURCE_DIVERGENCE")
    process_hashes = {value["process_output_sha256"] for value in lanes}
    require(len(process_hashes) == 1, "COMPILER_PROCESS_DRIFT")
    process_results = {canonical_bytes(value["process_output"]) for value in lanes}
    require(len(process_results) == 1, "COMPILER_RESULT_DRIFT")

    corpus_paths = [
        arguments.python_corpus,
        *sorted(arguments.java_corpus_dir.rglob("corpus.json")),
    ]
    require(len(corpus_paths) == 3, "CROSS_LANGUAGE_CORPUS_COUNT")
    corpus_documents = [canonical_document(path) for path in corpus_paths]
    for document, _ in corpus_documents:
        validate_corpus(document)
    corpus_encodings = {encoded for _, encoded in corpus_documents}
    corpus_hashes = {value["shared_corpus_sha256"] for value in lanes}
    require(len(corpus_encodings) == 1, "PYTHON_JAVA_CORPUS_DRIFT")
    corpus_encoded = corpus_encodings.pop()
    require(corpus_hashes == {sha256_id(corpus_encoded)}, "CPP_CORPUS_DRIFT")

    tests = junit_tests(arguments.safety_junit)
    refinement_paths = sorted(arguments.refinement_dir.glob("*.json"))
    require({path.name for path in refinement_paths} == REFINEMENT_FILES, "REFINEMENT_SET")
    refinement = [pass_document(path) for path in refinement_paths]
    durations = sorted(int(value["diagnostic_elapsed_ns"]) for value in lanes)
    median_duration = int(statistics.median(durations))
    risk_decision, risk_decision_raw = canonical_document(PROFILE_DECISION_PATH)
    require(
        risk_decision == EXPECTED_PROFILE_RISK_DECISION,
        "PROFILE_RISK_DECISION_INVALID",
    )
    profile_decision = {
        "available_profile": "EMBEDDED_FFM",
        "comparison": {
            "embedded_ffm": {
                "crash_containment": "PROCESS_COFAILURE_RISK_ACCEPTED_NO_ISOLATION_CLAIM",
                "diagnostic_four_process_elapsed_ns": durations,
                "median_four_process_elapsed_ns": median_duration,
                "restart_replay": "PASS",
                "status": "QUALIFIED_EXACTNESS_ONLY",
            },
            "isolated_sidecar": {
                "crash_containment": "NOT_EVALUATED",
                "latency_ns": None,
                "reason": "CURRENT_LINEAGE_SIDECAR_NOT_IMPLEMENTED",
                "restart_replay": "NOT_EVALUATED",
                "status": "OMITTED_BY_FORMAL_RISK_DECISION",
                "throughput": None,
            },
            "measurement_class": "NON_PRIMARY_CI_DIAGNOSTIC",
            "performance_superiority_claimed": False,
        },
        "pilot_execution_authorized": False,
        "risk_acceptance": {
            "accepted_risk": "NATIVE_CRASH_MAY_TERMINATE_JAVA_PROCESS",
            "crash_isolation_claimed": False,
            "formal_impact": "NO_SEMANTIC_CHANGE",
            "sidecar_omitted": True,
        },
        "risk_decision_sha256": sha256_id(risk_decision_raw),
        "selected_profile": None,
        "selection_basis": "NO_SELECTION_SIDECAR_NOT_EVALUATED",
        "selection_scope": "BLOCKED_PENDING_IMMUTABLE_COMPARATIVE_BENCHMARK_EVIDENCE",
    }
    result = {
        "architecture_coverage": {
            "aarch64": {
                "reason": "NO_EXACT_PINNED_RUNNER_AVAILABLE",
                "status": "NOT_RUN",
            },
            "x86_64": "PASS",
        },
        "attack_coverage": ATTACK_COVERAGE,
        "authority": {
            "definition_execution_authorized": False,
            "feature010_go": False,
            "primary_observation_count": 0,
            "qualifying_gate_c": False,
            "qualifying_gate_d": False,
            "result_qc": None,
        },
        "cross_language_corpus_sha256": sha256_id(corpus_encoded),
        "formal_semantics_id": FORMAL_ID,
        "gates": EXPECTED_GATES,
        "native_lanes": sorted(
            lanes, key=lambda value: (str(value["compiler"]), int(value["cpp_standard"]))
        ),
        "process_result": lanes[0]["process_output"],
        "profile_decision": profile_decision,
        "qualification_blockers": QUALIFICATION_BLOCKERS,
        "refinement": refinement,
        "safety_tests": tests,
        "safety_junit_sha256": sha256_id(arguments.safety_junit.read_bytes()),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "FAIL",
        "type_name": "FEATURE010_EXACTNESS_EXECUTION",
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(canonical_bytes(result) + b"\n")
    return result


def verify_execution(path: Path) -> dict[str, Any]:
    value, _ = canonical_document(path)
    require(
        set(value)
        == {
            "architecture_coverage",
            "attack_coverage",
            "authority",
            "cross_language_corpus_sha256",
            "formal_semantics_id",
            "gates",
            "native_lanes",
            "process_result",
            "profile_decision",
            "qualification_blockers",
            "refinement",
            "safety_tests",
            "safety_junit_sha256",
            "schema_version",
            "semantic_completeness_claimed",
            "source",
            "status",
            "type_name",
        },
        "EXECUTION_FIELDS",
    )
    require(value.get("type_name") == "FEATURE010_EXACTNESS_EXECUTION", "EXECUTION_TYPE")
    require(value.get("schema_version") == "1.0.0", "EXECUTION_SCHEMA")
    require(value.get("formal_semantics_id") == FORMAL_ID, "EXECUTION_FORMAL_ID")
    require(value.get("status") == "FAIL", "EXECUTION_STATUS")
    require(value.get("semantic_completeness_claimed") is False, "SEMANTIC_CLAIM_FORBIDDEN")
    source = value.get("source")
    require(isinstance(source, dict), "EXECUTION_SOURCE")
    commit = source.get("commit")
    require(isinstance(commit, str), "EXECUTION_SOURCE_COMMIT")
    require(source == source_identity(commit), "EXECUTION_SOURCE_IDENTITY")
    authority = value.get("authority")
    require(
        authority
        == {
            "definition_execution_authorized": False,
            "feature010_go": False,
            "primary_observation_count": 0,
            "qualifying_gate_c": False,
            "qualifying_gate_d": False,
            "result_qc": None,
        },
        "AUTHORITY",
    )
    validate_process(value["process_result"])
    lanes = value.get("native_lanes")
    require(isinstance(lanes, list) and len(lanes) == 4, "EXECUTION_LANES")
    require(
        {(lane["compiler"], lane["cpp_standard"]) for lane in lanes} == EXPECTED_LANES,
        "EXECUTION_LANE_MATRIX",
    )
    process_encoding = canonical_bytes(value["process_result"])
    process_sha256 = sha256_id(process_encoding)
    receipt_encodings: set[bytes] = set()
    corpus_sha256 = value.get("cross_language_corpus_sha256")
    require(
        isinstance(corpus_sha256, str)
        and corpus_sha256.startswith("sha256:")
        and len(corpus_sha256) == 71,
        "EXECUTION_CORPUS_HASH",
    )
    for lane in lanes:
        require(
            set(lane)
            == {
                "architecture",
                "compiler",
                "compiler_image",
                "compiler_version",
                "cpp_standard",
                "diagnostic_elapsed_ns",
                "formal_semantics_id",
                "process_output",
                "process_output_sha256",
                "process_receipts",
                "process_repetitions",
                "schema_version",
                "shared_corpus_sha256",
                "source",
                "status",
                "type_name",
            },
            "EXECUTION_LANE_FIELDS",
        )
        require(lane["type_name"] == "FEATURE010_NATIVE_EXACTNESS_LANE", "LANE_TYPE")
        require(lane["schema_version"] == "1.0.0", "LANE_SCHEMA")
        require(lane["status"] == "PASS", "LANE_STATUS")
        require(lane["formal_semantics_id"] == FORMAL_ID, "LANE_FORMAL_ID")
        require(lane["architecture"] == "x86_64", "LANE_ARCHITECTURE")
        toolchain = EXPECTED_TOOLCHAINS[lane["compiler"]]
        require(lane["compiler_image"] == toolchain["image"], "LANE_TOOLCHAIN_IMAGE")
        require(
            toolchain["version_pattern"] in lane["compiler_version"],
            "LANE_TOOLCHAIN_VERSION",
        )
        require(lane["source"] == source, "LANE_SOURCE")
        require(lane["process_repetitions"] == 4, "LANE_REPETITIONS")
        receipts = lane["process_receipts"]
        require(isinstance(receipts, list) and len(receipts) == 4, "LANE_RECEIPTS")
        require(
            len({canonical_bytes(receipt) for receipt in receipts}) == 1,
            "LANE_RECEIPT_REPETITION_DRIFT",
        )
        receipt_encodings.add(canonical_bytes(receipts[0]))
        for receipt in receipts:
            require(
                isinstance(receipt, dict)
                and set(receipt) == {"aggregator_sha256", "validator_receipts"},
                "LANE_RECEIPT_FIELDS",
            )
            require(
                isinstance(receipt["validator_receipts"], list)
                and len(receipt["validator_receipts"]) == 4,
                "LANE_VALIDATOR_RECEIPTS",
            )
            require(
                isinstance(receipt["aggregator_sha256"], str)
                and receipt["aggregator_sha256"].startswith("sha256:")
                and len(receipt["aggregator_sha256"]) == 71,
                "LANE_AGGREGATOR_HASH",
            )
            validator_receipts = receipt["validator_receipts"]
            require(
                {item.get("path") for item in validator_receipts}
                == {f"validator-{index}.json" for index in range(4)},
                "LANE_VALIDATOR_RECEIPT_PATHS",
            )
            for item in validator_receipts:
                require(set(item) == {"path", "sha256"}, "LANE_VALIDATOR_RECEIPT_FIELDS")
                require(
                    isinstance(item["sha256"], str)
                    and item["sha256"].startswith("sha256:")
                    and len(item["sha256"]) == 71,
                    "LANE_VALIDATOR_RECEIPT_HASH",
                )
        require(
            isinstance(lane["diagnostic_elapsed_ns"], int) and lane["diagnostic_elapsed_ns"] > 0,
            "LANE_DURATION",
        )
        validate_process(lane["process_output"])
        require(lane["process_output"] == value["process_result"], "LANE_PROCESS_DRIFT")
        require(lane["process_output_sha256"] == process_sha256, "LANE_PROCESS_HASH")
        require(lane["shared_corpus_sha256"] == corpus_sha256, "LANE_CORPUS_HASH")
    require(len(receipt_encodings) == 1, "COMPILER_RECEIPT_DRIFT")
    require(value.get("safety_tests") == sorted(EXPECTED_TESTS), "EXECUTION_TESTS")
    safety_junit_sha256 = value.get("safety_junit_sha256")
    require(
        isinstance(safety_junit_sha256, str)
        and safety_junit_sha256.startswith("sha256:")
        and len(safety_junit_sha256) == 71,
        "SAFETY_JUNIT_HASH",
    )
    refinement = value.get("refinement")
    require(isinstance(refinement, list) and len(refinement) == 4, "REFINEMENT_COUNT")
    require({item.get("path") for item in refinement} == REFINEMENT_FILES, "REFINEMENT_SET")
    for item in refinement:
        require(set(item) == {"path", "sha256", "status"}, "REFINEMENT_FIELDS")
        require(item["status"] == "PASS", "REFINEMENT_STATUS")
        require(
            isinstance(item["sha256"], str)
            and item["sha256"].startswith("sha256:")
            and len(item["sha256"]) == 71,
            "REFINEMENT_HASH",
        )
    require(value.get("gates") == EXPECTED_GATES, "EXECUTION_GATES")
    require(
        value.get("qualification_blockers") == QUALIFICATION_BLOCKERS,
        "EXECUTION_QUALIFICATION_BLOCKERS",
    )
    require(value.get("attack_coverage") == ATTACK_COVERAGE, "ATTACK_COVERAGE")
    for attack in ATTACK_COVERAGE:
        require(set(attack["tests"]) <= EXPECTED_TESTS, "ATTACK_TEST_UNKNOWN")
    require(
        value.get("architecture_coverage")
        == {
            "aarch64": {
                "reason": "NO_EXACT_PINNED_RUNNER_AVAILABLE",
                "status": "NOT_RUN",
            },
            "x86_64": "PASS",
        },
        "ARCHITECTURE_COVERAGE",
    )
    profile = value.get("profile_decision", {})
    require(
        set(profile)
        == {
            "available_profile",
            "comparison",
            "pilot_execution_authorized",
            "risk_acceptance",
            "risk_decision_sha256",
            "selected_profile",
            "selection_basis",
            "selection_scope",
        },
        "PROFILE_FIELDS",
    )
    require(profile.get("available_profile") == "EMBEDDED_FFM", "PROFILE_AVAILABLE")
    require(profile.get("selected_profile") is None, "PROFILE_SELECTION_FORBIDDEN")
    require(profile.get("pilot_execution_authorized") is False, "PILOT_AUTHORITY_FORBIDDEN")
    require(
        profile.get("selection_basis") == "NO_SELECTION_SIDECAR_NOT_EVALUATED",
        "PROFILE_SELECTION_BASIS",
    )
    require(
        profile.get("selection_scope")
        == "BLOCKED_PENDING_IMMUTABLE_COMPARATIVE_BENCHMARK_EVIDENCE",
        "PROFILE_SELECTION_SCOPE",
    )
    risk = profile.get("risk_acceptance")
    require(
        risk
        == {
            "accepted_risk": "NATIVE_CRASH_MAY_TERMINATE_JAVA_PROCESS",
            "crash_isolation_claimed": False,
            "formal_impact": "NO_SEMANTIC_CHANGE",
            "sidecar_omitted": True,
        },
        "PROFILE_RISK_DECISION",
    )
    risk_document, risk_raw = canonical_document(PROFILE_DECISION_PATH)
    require(risk_document == EXPECTED_PROFILE_RISK_DECISION, "PROFILE_RISK_DOCUMENT")
    require(
        profile.get("risk_decision_sha256") == sha256_id(risk_raw),
        "PROFILE_RISK_HASH",
    )
    comparison = profile.get("comparison")
    require(
        isinstance(comparison, dict)
        and set(comparison)
        == {
            "embedded_ffm",
            "isolated_sidecar",
            "measurement_class",
            "performance_superiority_claimed",
        },
        "PROFILE_COMPARISON_FIELDS",
    )
    require(comparison["measurement_class"] == "NON_PRIMARY_CI_DIAGNOSTIC", "PROFILE_CLASS")
    require(comparison["performance_superiority_claimed"] is False, "PROFILE_SUPERIORITY")
    durations = sorted(int(lane["diagnostic_elapsed_ns"]) for lane in lanes)
    require(
        comparison["embedded_ffm"]
        == {
            "crash_containment": "PROCESS_COFAILURE_RISK_ACCEPTED_NO_ISOLATION_CLAIM",
            "diagnostic_four_process_elapsed_ns": durations,
            "median_four_process_elapsed_ns": int(statistics.median(durations)),
            "restart_replay": "PASS",
            "status": "QUALIFIED_EXACTNESS_ONLY",
        },
        "EMBEDDED_PROFILE_EVIDENCE",
    )
    require(
        comparison["isolated_sidecar"]
        == {
            "crash_containment": "NOT_EVALUATED",
            "latency_ns": None,
            "reason": "CURRENT_LINEAGE_SIDECAR_NOT_IMPLEMENTED",
            "restart_replay": "NOT_EVALUATED",
            "status": "OMITTED_BY_FORMAL_RISK_DECISION",
            "throughput": None,
        },
        "SIDECAR_PROFILE_EVIDENCE",
    )
    return value


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subcommands = root.add_subparsers(dest="command", required=True)
    lane = subcommands.add_parser("emit-native-lane")
    lane.add_argument("--source-commit", required=True)
    lane.add_argument("--compiler", required=True, choices=("gcc", "clang"))
    lane.add_argument("--compiler-image", required=True)
    lane.add_argument("--compiler-version", required=True)
    lane.add_argument("--standard", required=True, type=int, choices=(20, 23))
    lane.add_argument("--architecture", default="x86_64")
    lane.add_argument("--elapsed-ns", required=True, type=int)
    lane.add_argument("--process-output", action="append", required=True, type=Path)
    lane.add_argument("--receipt-dir", action="append", required=True, type=Path)
    lane.add_argument("--corpus-output", required=True, type=Path)
    lane.add_argument("--output", required=True, type=Path)
    aggregate_parser = subcommands.add_parser("aggregate")
    aggregate_parser.add_argument("--source-commit", required=True)
    aggregate_parser.add_argument("--lanes-dir", required=True, type=Path)
    aggregate_parser.add_argument("--safety-junit", required=True, type=Path)
    aggregate_parser.add_argument("--refinement-dir", required=True, type=Path)
    aggregate_parser.add_argument("--python-corpus", required=True, type=Path)
    aggregate_parser.add_argument("--java-corpus-dir", required=True, type=Path)
    aggregate_parser.add_argument("--output", required=True, type=Path)
    verify = subcommands.add_parser("verify-execution")
    verify.add_argument("path", type=Path)
    return root


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.command == "emit-native-lane":
            result = emit_native_lane(arguments)
        elif arguments.command == "aggregate":
            result = aggregate(arguments)
        else:
            result = verify_execution(arguments.path)
    except (ExactnessError, OSError, ValueError, KeyError, ET.ParseError) as error:
        print(canonical_bytes({"error": str(error), "status": "FAIL"}).decode("utf-8"))
        return 2
    print(canonical_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
