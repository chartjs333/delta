#!/usr/bin/env python3
"""Fail-closed verifier for the Feature 010 foundation-only checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

BASE_COMMIT = "ac0e54ffbab4b9a5c20945b17ede2930b78ff080"
IMPLEMENTATION_COMMIT = "6054e35ed627392172f94c2a90dfb7d799d5251e"
IMPLEMENTATION_TREE = "0640a117aba6772b7c0b22ec9cdaa047e507e1d5"
FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FORMAL_REPORT_SHA256 = "3e2e2344a038b2c902b06d275fb3e3820f95e5a780c2750e5c1a367dd82936d7"
PREFLIGHT_MANIFEST_ID = "sha256:fe29fae984c3fb1b27aefd58dbb0a0bf1ff8a4a2d23468de84471a70b38bb627"
TEST_EVIDENCE_SHA256 = "69cee78c4f641491e8768091bb23c1f876b4456397c2a2d0581a7fc3030f21f4"
FEATURE = Path("specs/010-wan-benchmark-and-quality")
TASK_MAP_PATH = FEATURE / "evidence/foundation-task-map.json"
FORMAL_IMPACT_PATH = FEATURE / "evidence/foundation-formal-impact.json"
STATUS_PATH = FEATURE / "evidence/foundation-status.json"
PROTECTED_PREFIXES = (
    "delta-core-cpp/",
    "delta-ffi/",
    "delta-node-java/",
    "delta-runtime-cpp/",
    "formal/",
)
OVERLAY_PATHS = {
    (FEATURE / relative).as_posix()
    for relative in (
        "evidence/foundation-formal-impact.json",
        "evidence/foundation-status.json",
        "evidence/foundation-task-map.json",
        "plan.md",
        "runtime-tasks.md",
        "scripts/verify_foundation_status.py",
        "spec.md",
        "task-map.md",
        "tasks.md",
        "tests/test_foundation_status.py",
    )
}
COMPLETION_CLASSES = {
    "CONTRACT_AND_FIXTURE",
    "FOUNDATION_IMPLEMENTATION_ONLY",
    "OFFLINE_VERIFIER",
    "PLAN_ONLY",
}
EXPECTED_SEMANTIC_CLASSES = {
    "T001": "OFFLINE_VERIFIER",
    "T002": "CONTRACT_AND_FIXTURE",
    "T003": "CONTRACT_AND_FIXTURE",
    "T004": "CONTRACT_AND_FIXTURE",
    "T005": "CONTRACT_AND_FIXTURE",
    "T006": "CONTRACT_AND_FIXTURE",
    "T007": "CONTRACT_AND_FIXTURE",
    "T008": "OFFLINE_VERIFIER",
    "T009": "CONTRACT_AND_FIXTURE",
    "T010": "PLAN_ONLY",
    "T011": "PLAN_ONLY",
    "T012": "CONTRACT_AND_FIXTURE",
    "T013": "FOUNDATION_IMPLEMENTATION_ONLY",
    "T014": "FOUNDATION_IMPLEMENTATION_ONLY",
    "T015": "PLAN_ONLY",
    "T016": "OFFLINE_VERIFIER",
    "T017": "CONTRACT_AND_FIXTURE",
    "T018": "PLAN_ONLY",
    "T019": "PLAN_ONLY",
    "T020": "PLAN_ONLY",
    "T021": "CONTRACT_AND_FIXTURE",
    "T022": "CONTRACT_AND_FIXTURE",
    "T023": "FOUNDATION_IMPLEMENTATION_ONLY",
    "T024": "PLAN_ONLY",
    "T025": "CONTRACT_AND_FIXTURE",
    "T026": "OFFLINE_VERIFIER",
    "T027": "CONTRACT_AND_FIXTURE",
}
EXPECTED_RUNTIME_CLASSES = {
    "HR010-001": "CONTRACT_AND_FIXTURE",
    "HR010-002": "PLAN_ONLY",
    "HR010-003": "FOUNDATION_IMPLEMENTATION_ONLY",
}
EXCLUDED_CLAIMS = [
    "ACTUAL_GOVERNANCE_OR_DEFINITION_EXECUTION_AUTHORIZATION",
    "ACTUAL_RESULT_QC",
    "FEATURE010_GO",
    "LIVE_POLYGLOT_EXECUTION",
    "PRIMARY_SCIENTIFIC_OBSERVATIONS",
    "QUALIFYING_GATE_C",
    "QUALIFYING_GATE_D",
]


class VerificationError(ValueError):
    """A stable fail-closed evidence error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def exact_fields(value: object, fields: set[str], code: str) -> dict[str, Any]:
    require(type(value) is dict, f"{code}_NOT_OBJECT")
    item = value
    require(set(item) == fields, f"{code}_FIELDS_INVALID")
    return item


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_canonical_json_bytes(raw: bytes, name: str) -> dict[str, Any]:
    require(not raw.startswith(b"\xef\xbb\xbf"), f"{name}_BOM_FORBIDDEN")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VerificationError(f"{name}_JSON_INVALID") from error
    require(type(value) is dict, f"{name}_ROOT_INVALID")
    require(raw == canonical_json_bytes(value), f"{name}_BYTES_NOT_CANONICAL")
    return value


def git_bytes(root: Path, *arguments: str) -> bytes:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise VerificationError(f"GIT_COMMAND_FAILED:{detail}")
    return completed.stdout


def git_text(root: Path, *arguments: str) -> str:
    return git_bytes(root, *arguments).decode("utf-8").strip()


def candidate_bytes(root: Path, path: Path, allow_worktree: bool) -> bytes:
    if allow_worktree:
        return (root / path).read_bytes()
    return git_bytes(root, "show", f"HEAD:{path.as_posix()}")


def sha256_id(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def changed_paths(root: Path, start: str, end: str) -> list[str]:
    output = git_text(root, "diff", "--name-only", start, end, "--")
    return sorted(line.replace("\\", "/") for line in output.splitlines() if line)


def implementation_inventory(root: Path) -> list[dict[str, str]]:
    paths = changed_paths(root, BASE_COMMIT, IMPLEMENTATION_COMMIT)
    inventory: list[dict[str, str]] = []
    for path in paths:
        entry = git_text(root, "ls-tree", IMPLEMENTATION_COMMIT, "--", path)
        require(bool(entry), f"IMPLEMENTATION_TREE_ENTRY_MISSING:{path}")
        metadata, actual_path = entry.split("\t", 1)
        mode, kind, _oid = metadata.split(" ", 2)
        require(mode in {"100644", "100755"} and kind == "blob", "IMPLEMENTATION_ENTRY_INVALID")
        require(actual_path == path, "IMPLEMENTATION_PATH_MISMATCH")
        raw = git_bytes(root, "show", f"{IMPLEMENTATION_COMMIT}:{path}")
        inventory.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest()})
    return inventory


def validate_task_entry(
    root: Path,
    entry: object,
    expected_classes: dict[str, str],
    implementation_paths: set[str],
) -> str:
    item = exact_fields(
        entry,
        {"completion_class", "implementation_paths", "task_id", "test_nodeids"},
        "TASK_ENTRY",
    )
    task_id = item["task_id"]
    require(type(task_id) is str and task_id in expected_classes, "TASK_ID_INVALID")
    completion_class = item["completion_class"]
    require(completion_class in COMPLETION_CLASSES, f"TASK_CLASS_UNKNOWN:{task_id}")
    require(completion_class == expected_classes[task_id], f"TASK_CLASS_MISMATCH:{task_id}")
    paths = item["implementation_paths"]
    require(
        type(paths) is list and paths == sorted(set(paths)) and bool(paths),
        f"TASK_PATHS:{task_id}",
    )
    require(set(paths) <= implementation_paths, f"TASK_PATH_OUTSIDE_IMPLEMENTATION:{task_id}")
    nodeids = item["test_nodeids"]
    require(
        type(nodeids) is list and nodeids == sorted(set(nodeids)) and bool(nodeids),
        f"TASK_TESTS:{task_id}",
    )
    for nodeid in nodeids:
        require(type(nodeid) is str and nodeid.count("::") == 1, f"TASK_NODEID_INVALID:{task_id}")
        test_path, test_name = nodeid.split("::", 1)
        require(test_path in implementation_paths, f"TASK_TEST_PATH_UNKNOWN:{task_id}")
        source = git_bytes(root, "show", f"{IMPLEMENTATION_COMMIT}:{test_path}").decode("utf-8")
        require(
            re.search(rf"^def {re.escape(test_name)}\(", source, flags=re.MULTILINE) is not None,
            f"TASK_TEST_NODEID_UNKNOWN:{task_id}",
        )
    return task_id


def validate_task_map(root: Path, document: object, implementation_paths: set[str]) -> None:
    item = exact_fields(
        document,
        {
            "boundary",
            "excluded_claims",
            "implementation_commit",
            "implementation_tree",
            "runtime_tasks",
            "schema_version",
            "semantic_tasks",
            "type_name",
        },
        "TASK_MAP",
    )
    require(item["type_name"] == "FEATURE010_FOUNDATION_TASK_MAP", "TASK_MAP_TYPE")
    require(item["schema_version"] == "1.0.0", "TASK_MAP_SCHEMA")
    require(item["implementation_commit"] == IMPLEMENTATION_COMMIT, "TASK_MAP_COMMIT")
    require(item["implementation_tree"] == IMPLEMENTATION_TREE, "TASK_MAP_TREE")
    require(item["excluded_claims"] == EXCLUDED_CLAIMS, "TASK_MAP_EXCLUDED_CLAIMS")
    expected_boundary = {
        "actual_result_qc": None,
        "definition_execution_authorization": None,
        "execution_started": False,
        "feature010_go": False,
        "primary_scientific_observation_count": 0,
        "qualification_complete": False,
        "qualifying_gate_c": False,
        "qualifying_gate_d": False,
    }
    require(item["boundary"] == expected_boundary, "TASK_MAP_AUTHORITY_BOUNDARY")
    semantic_ids = [
        validate_task_entry(root, entry, EXPECTED_SEMANTIC_CLASSES, implementation_paths)
        for entry in item["semantic_tasks"]
    ]
    runtime_ids = [
        validate_task_entry(root, entry, EXPECTED_RUNTIME_CLASSES, implementation_paths)
        for entry in item["runtime_tasks"]
    ]
    require(semantic_ids == list(EXPECTED_SEMANTIC_CLASSES), "SEMANTIC_TASK_SET_INVALID")
    require(runtime_ids == list(EXPECTED_RUNTIME_CLASSES), "RUNTIME_TASK_SET_INVALID")


def validate_formal_impact(root: Path, document: object) -> None:
    item = exact_fields(
        document,
        {
            "formal_baseline",
            "formal_impact_classification",
            "governance_boundary",
            "implementation",
            "implementation_boundary_classification",
            "new_runtime_semantics",
            "protected_diff",
            "schema_version",
            "type_name",
        },
        "FORMAL_IMPACT",
    )
    require(item["type_name"] == "FEATURE010_FOUNDATION_FORMAL_IMPACT", "FORMAL_TYPE")
    require(item["schema_version"] == "1.0.0", "FORMAL_SCHEMA")
    require(item["formal_impact_classification"] == "NO_SEMANTIC_CHANGE", "FORMAL_CLASS")
    require(item["implementation_boundary_classification"] == "REFINEMENT_ONLY", "BOUNDARY_CLASS")
    require(
        item["implementation"]
        == {
            "base_commit": BASE_COMMIT,
            "commit": IMPLEMENTATION_COMMIT,
            "tree": IMPLEMENTATION_TREE,
        },
        "FORMAL_IMPLEMENTATION_BINDING",
    )
    require(
        item["formal_baseline"]
        == {
            "formal_report_path": "formal/reports/formal-verification-report.json",
            "formal_report_sha256": FORMAL_REPORT_SHA256,
            "formal_semantics_id": FORMAL_ID,
        },
        "FORMAL_BASELINE_BINDING",
    )
    require(
        hashlib.sha256(
            git_bytes(
                root,
                "show",
                f"{IMPLEMENTATION_COMMIT}:formal/reports/formal-verification-report.json",
            )
        ).hexdigest()
        == FORMAL_REPORT_SHA256,
        "FORMAL_REPORT_HASH_MISMATCH",
    )
    semantics = exact_fields(
        item["new_runtime_semantics"],
        {
            "actions",
            "arithmetic_preconditions",
            "availability_rules",
            "certificate_parent_edges",
            "current_state_transitions",
            "durability_outcomes",
            "failure_terminals",
            "qc_types",
            "vote_contexts",
        },
        "RUNTIME_SEMANTICS",
    )
    require(all(value == [] for value in semantics.values()), "NEW_RUNTIME_SEMANTICS_FORBIDDEN")
    governance = item["governance_boundary"]
    require(
        governance
        == {
            "authority_scope": "BENCHMARK_GOVERNANCE_ONLY",
            "execution_authority": False,
            "governance_qc_types": ["BENCHMARK_DEFINITION_QC", "BENCHMARK_RESULT_QC"],
            "governance_vote_types": ["BENCHMARK_DEFINITION_VOTE", "BENCHMARK_RESULT_VOTE"],
            "runtime_certificate_graph_member": False,
            "runtime_state_transition_authority": False,
        },
        "GOVERNANCE_BOUNDARY_INVALID",
    )
    protected = [
        path
        for path in changed_paths(root, BASE_COMMIT, IMPLEMENTATION_COMMIT)
        if path.startswith(PROTECTED_PREFIXES)
    ]
    require(
        item["protected_diff"] == {"paths": protected, "prefixes": list(PROTECTED_PREFIXES)},
        "PROTECTED_DIFF_MISMATCH",
    )
    require(not protected, "PROTECTED_DIFF_NOT_EMPTY")


def validate_checklists(tasks_text: str, runtime_text: str) -> None:
    semantic = [
        (marker, int(task_id))
        for marker, task_id in re.findall(r"^- \[([ x])\] T(\d{3})\b", tasks_text, re.MULTILINE)
    ]
    runtime = [
        (marker, int(task_id))
        for marker, task_id in re.findall(
            r"^- \[([ x])\] \*\*HR010-(\d{3})\*\*", runtime_text, re.MULTILINE
        )
    ]
    expected_semantic = [("x", value) for value in range(28)]
    expected_semantic.extend((" ", value) for value in range(28, 55))
    expected_runtime = [("x", value) for value in range(1, 4)]
    expected_runtime.extend((" ", value) for value in range(4, 19))
    require(
        semantic == expected_semantic,
        "SEMANTIC_CHECKLIST_STATE_INVALID",
    )
    require(
        runtime == expected_runtime,
        "RUNTIME_CHECKLIST_STATE_INVALID",
    )


def validate_status(
    root: Path,
    document: object,
    task_map_raw: bytes,
    formal_raw: bytes,
    inventory: list[dict[str, str]],
) -> None:
    item = exact_fields(
        document,
        {
            "authority_claims",
            "evidence_links",
            "formal_baseline",
            "foundation_only",
            "implementation",
            "preflight",
            "production_and_protected_diff",
            "qualification_complete",
            "schema_version",
            "status",
            "test_evidence",
            "type_name",
        },
        "STATUS",
    )
    require(item["type_name"] == "FEATURE010_FOUNDATION_STATUS", "STATUS_TYPE")
    require(item["schema_version"] == "1.0.0", "STATUS_SCHEMA")
    require(item["status"] == "PASS_FOUNDATION_ONLY", "STATUS_DECISION")
    require(item["foundation_only"] is True, "FOUNDATION_ONLY_REQUIRED")
    require(item["qualification_complete"] is False, "QUALIFICATION_MUST_BE_FALSE")
    expected_authority = {
        "actual_benchmark_result_qc": None,
        "definition_execution_authorization": None,
        "execution_started": False,
        "feature010_go": False,
        "feature010_go_checkpoint_sha": None,
        "primary_scientific_observation_count": 0,
        "qualifying_gate_c": False,
        "qualifying_gate_c_run_count": 0,
        "qualifying_gate_d": False,
        "qualifying_gate_d_run_count": 0,
    }
    require(item["authority_claims"] == expected_authority, "ZERO_AUTHORITY_CLAIMS_INVALID")
    require(
        item["evidence_links"]
        == {
            "formal_impact_path": FORMAL_IMPACT_PATH.as_posix(),
            "formal_impact_sha256": sha256_id(formal_raw),
            "task_map_path": TASK_MAP_PATH.as_posix(),
            "task_map_sha256": sha256_id(task_map_raw),
        },
        "EVIDENCE_LINK_HASH_MISMATCH",
    )
    require(
        item["formal_baseline"]
        == {
            "formal_report_sha256": FORMAL_REPORT_SHA256,
            "formal_semantics_id": FORMAL_ID,
            "prerequisite_result": "PASS_ON_CLEAN_LF_DETACHED_RECONCILIATION_WORKTREE",
        },
        "STATUS_FORMAL_BASELINE_INVALID",
    )
    implementation = item["implementation"]
    require(
        implementation
        == {
            "artifact_count": len(inventory),
            "artifacts": inventory,
            "base_commit": BASE_COMMIT,
            "commit": IMPLEMENTATION_COMMIT,
            "tree": IMPLEMENTATION_TREE,
        },
        "IMPLEMENTATION_INVENTORY_MISMATCH",
    )
    expected_preflight = {
        "finding_count": 0,
        "policy_id": "feature010-zero-tolerance-v1",
        "scanned_path_count": 46,
        "source_commit": IMPLEMENTATION_COMMIT,
        "source_manifest_id": PREFLIGHT_MANIFEST_ID,
        "source_tree": IMPLEMENTATION_TREE,
        "status": "PASS",
    }
    require(item["preflight"] == expected_preflight, "PREFLIGHT_EVIDENCE_INVALID")
    sys.path.insert(0, str(root / "delta-worker-python/src"))
    try:
        from deltatorrent.benchmark.preflight import run_required_preflight

        try:
            report = run_required_preflight(
                root, source_commit=IMPLEMENTATION_COMMIT, expected_tree=IMPLEMENTATION_TREE
            )
        except Exception as error:
            raise VerificationError(
                f"PREFLIGHT_INVOCATION_FAILED:{type(error).__name__}"
            ) from error
    finally:
        sys.path.pop(0)
    require(report.status == "PASS", "PREFLIGHT_FAILED")
    require(report.policy_id == expected_preflight["policy_id"], "PREFLIGHT_POLICY_MISMATCH")
    require(report.source_manifest_id == PREFLIGHT_MANIFEST_ID, "PREFLIGHT_MANIFEST_MISMATCH")
    require(len(report.scanned_paths) == 46 and not report.findings, "PREFLIGHT_RESULT_MISMATCH")
    offline_source_paths = sorted(
        entry["path"]
        for entry in inventory
        if entry["path"].startswith("delta-worker-python/src/deltatorrent/benchmark/")
    )
    expected_diff = {
        "native_java_consensus_runtime_paths": [],
        "offline_foundation_source_paths": offline_source_paths,
        "protected_paths": [],
        "protected_prefixes": list(PROTECTED_PREFIXES),
        "runtime_semantic_paths": [],
    }
    require(item["production_and_protected_diff"] == expected_diff, "RUNTIME_DIFF_INVALID")
    commands = item["test_evidence"]
    require(type(commands) is list and len(commands) == 12, "TEST_EVIDENCE_COUNT_INVALID")
    for evidence in commands:
        exact_fields(evidence, {"command", "result", "scope"}, "TEST_EVIDENCE")
        require(
            all(type(evidence[key]) is str and evidence[key] for key in evidence),
            "TEST_EVIDENCE_VALUE",
        )
    require(
        hashlib.sha256(canonical_json_bytes(commands)).hexdigest() == TEST_EVIDENCE_SHA256,
        "TEST_EVIDENCE_EXACT_RESULT_MISMATCH",
    )


def validate_repository(root: Path, *, allow_worktree: bool) -> dict[str, object]:
    require(
        git_text(root, "rev-parse", f"{IMPLEMENTATION_COMMIT}^{{tree}}") == IMPLEMENTATION_TREE,
        "IMPLEMENTATION_TREE_MISMATCH",
    )
    require(
        git_text(root, "rev-parse", f"{IMPLEMENTATION_COMMIT}^") == BASE_COMMIT,
        "IMPLEMENTATION_PARENT_MISMATCH",
    )
    candidate = "WORKTREE" if allow_worktree else git_text(root, "rev-parse", "HEAD")
    if not allow_worktree:
        require(candidate != IMPLEMENTATION_COMMIT, "OVERLAY_COMMIT_REQUIRED")
        require(
            git_text(root, "rev-parse", f"{candidate}^") == IMPLEMENTATION_COMMIT,
            "OVERLAY_PARENT_MISMATCH",
        )
        require(
            set(changed_paths(root, IMPLEMENTATION_COMMIT, candidate)) == OVERLAY_PATHS,
            "OVERLAY_PATH_SET_INVALID",
        )
    inventory = implementation_inventory(root)
    require(len(inventory) == 54, "IMPLEMENTATION_ARTIFACT_COUNT_INVALID")
    implementation_paths = {entry["path"] for entry in inventory}
    if not allow_worktree:
        relevant_paths = sorted(implementation_paths | OVERLAY_PATHS | set(PROTECTED_PREFIXES))
        require(
            not git_text(
                root,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--",
                *relevant_paths,
            ),
            "RELEVANT_WORKTREE_NOT_CLEAN",
        )
    task_map_raw = candidate_bytes(root, TASK_MAP_PATH, allow_worktree)
    formal_raw = candidate_bytes(root, FORMAL_IMPACT_PATH, allow_worktree)
    status_raw = candidate_bytes(root, STATUS_PATH, allow_worktree)
    task_map = load_canonical_json_bytes(task_map_raw, "TASK_MAP")
    formal = load_canonical_json_bytes(formal_raw, "FORMAL_IMPACT")
    status = load_canonical_json_bytes(status_raw, "STATUS")
    validate_task_map(root, task_map, implementation_paths)
    validate_formal_impact(root, formal)
    validate_status(root, status, task_map_raw, formal_raw, inventory)
    tasks_text = candidate_bytes(root, FEATURE / "tasks.md", allow_worktree).decode("utf-8")
    runtime_text = candidate_bytes(root, FEATURE / "runtime-tasks.md", allow_worktree).decode(
        "utf-8"
    )
    validate_checklists(tasks_text, runtime_text)
    for path, phrase in (
        (FEATURE / "task-map.md", "T028 and HR010-004 are the next open gates"),
        (FEATURE / "spec.md", "T028+, HR010-004+ and every"),
        (FEATURE / "plan.md", "It is not Feature 010 GO and cannot authorize execution"),
    ):
        text = candidate_bytes(root, path, allow_worktree).decode("utf-8")
        require(phrase in text, f"FOUNDATION_BOUNDARY_TEXT_MISSING:{path.as_posix()}")
    if not allow_worktree:
        protected = [
            path
            for path in changed_paths(root, BASE_COMMIT, candidate)
            if path.startswith(PROTECTED_PREFIXES)
        ]
        require(not protected, "CANDIDATE_PROTECTED_DIFF_NOT_EMPTY")
    return {
        "candidate": candidate,
        "implementation_artifact_count": len(inventory),
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "implementation_tree": IMPLEMENTATION_TREE,
        "preflight_manifest_id": PREFLIGHT_MANIFEST_ID,
        "status": "PASS_FOUNDATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-worktree",
        action="store_true",
        help="Validate the expected overlay files before commit; exact-head mode is the default.",
    )
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    try:
        result = validate_repository(root, allow_worktree=arguments.allow_worktree)
    except (OSError, TypeError, VerificationError) as error:
        print(
            json.dumps(
                {"error": f"{type(error).__name__}:{error}", "status": "FAIL"},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
