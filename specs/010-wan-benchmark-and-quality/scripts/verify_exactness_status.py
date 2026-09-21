#!/usr/bin/env python3
"""Build and verify the immutable Feature 010 exactness-only checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

from capture_exactness_ci import verify_ci
from exactness_gate import (
    BASE_COMMIT,
    EXPECTED_GATES,
    FORMAL_ID,
    canonical_bytes,
    canonical_document,
    require,
    source_identity,
    verify_execution,
)

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = Path("specs/010-wan-benchmark-and-quality")
CI_PATH: Final = FEATURE / "evidence/exactness-ci.json"
EXECUTION_PATH: Final = FEATURE / "evidence/exactness-execution.json"
STATUS_PATH: Final = FEATURE / "evidence/exactness-status.json"
HISTORICAL_FAIL_COMMIT: Final = "fc012861d8a1577f155abb94877102adef5cbf36"
HISTORICAL_FAIL_TREE: Final = "deeb2bda4c0a7e68015843d2ebe6fe4396edfb7b"
HISTORICAL_SOURCE_PATHS: Final = {
    ".github/workflows/certificates.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/distribution.yml",
    ".github/workflows/feature010-exactness.yml",
    ".github/workflows/hierarchy.yml",
    ".github/workflows/native-verification.yml",
    ".github/workflows/native.yml",
    ".github/workflows/qlora.yml",
    ".github/workflows/scheduling.yml",
    (FEATURE / "conformance/FoundationFixtureConsumer.java").as_posix(),
    (FEATURE / "conformance/foundation_fixture_consumer.cpp").as_posix(),
    (FEATURE / "qualification-harness/CMakeLists.txt").as_posix(),
    (FEATURE / "qualification-harness/exactness_probe.cpp").as_posix(),
    (FEATURE / "profile-risk-decision.json").as_posix(),
    (FEATURE / "scripts/capture_exactness_ci.py").as_posix(),
    (FEATURE / "scripts/build_exactness_probe.sh").as_posix(),
    (FEATURE / "scripts/exactness_gate.py").as_posix(),
    (FEATURE / "scripts/foundation_fixtures.py").as_posix(),
    (FEATURE / "scripts/verify_exactness_status.py").as_posix(),
    (FEATURE / "scripts/verify_foundation_status.py").as_posix(),
    (FEATURE / "tests/test_exactness_gate.py").as_posix(),
}
DESIGN_PATHS: Final = {
    ".github/workflows/feature010-exactness.yml",
    (FEATURE / "isolated-sidecar-refinement.md").as_posix(),
    (FEATURE / "sidecar-refinement-design.json").as_posix(),
    (FEATURE / "scripts/verify_exactness_status.py").as_posix(),
    (FEATURE / "scripts/verify_sidecar_refinement_design.py").as_posix(),
    (FEATURE / "tests/test_sidecar_refinement_design.py").as_posix(),
}
SOURCE_PATHS: Final = HISTORICAL_SOURCE_PATHS | DESIGN_PATHS
OVERLAY_PATHS: Final = {
    CI_PATH.as_posix(),
    EXECUTION_PATH.as_posix(),
    STATUS_PATH.as_posix(),
    (FEATURE / "exactness-safety.md").as_posix(),
    (FEATURE / "plan.md").as_posix(),
    (FEATURE / "runtime-profile.md").as_posix(),
    (FEATURE / "runtime-tasks.md").as_posix(),
    (FEATURE / "tasks.md").as_posix(),
}
PROTECTED_PREFIXES: Final = (
    "delta-core-cpp/",
    "delta-ffi/",
    "delta-node-java/",
    "delta-runtime-cpp/",
    "formal/",
)
EXACT_WORKFLOWS: Final = {path for path in SOURCE_PATHS if path.startswith(".github/workflows/")}
COMPLETED_TASKS: Final = [f"T{value:03d}" for value in range(30, 35)] + [
    f"HR010-{value:03d}" for value in range(4, 13)
]
LIMITATIONS: Final = [
    "AARCH64_NOT_RUN_NO_EXACT_PINNED_RUNNER_AVAILABLE",
    "PRIMARY_WORKLOAD_SCALE_NOT_RUN_MISSING_FROZEN_PARAMETER_SHAPE_AND_WORK_TICKET_EXECUTION",
    "EMBEDDED_FFM_HAS_NO_NATIVE_CRASH_ISOLATION_CLAIM",
    "FEATURE010_GO_IS_FALSE",
    "GATE_C_AND_GATE_D_ARE_NOT_EXECUTED",
    "NO_BENCHMARK_RESULT_QC",
    "NO_PILOT_EXECUTION_AUTHORITY",
    "NO_PRIMARY_SCIENTIFIC_OBSERVATIONS",
    "SIDECAR_PROFILE_METRICS_NONCOMPARABLE_BY_FROZEN_RISK_DECISION",
]
CI_GATE_JOBS: Final = {
    "XH-ABI": [
        ("Native core matrix", "JDK 25 runtime descriptor"),
        ("Native core matrix", "JDK 26 runtime descriptor"),
        ("Feature 005 distribution verification", "JDK 25 Netty/FFM data plane"),
        ("Feature 005 distribution verification", "JDK 26 Netty/FFM data plane"),
    ],
    "XH-NETTY": [
        ("Feature 005 distribution verification", "JDK 25 Netty/FFM data plane"),
        ("Feature 005 distribution verification", "JDK 26 Netty/FFM data plane"),
        ("Feature 007 scheduling verification", "JDK 25 scheduling FFM adapter"),
        ("Feature 007 scheduling verification", "JDK 26 scheduling FFM adapter"),
        ("Feature 008 certificate and Apply verification", "JDK 25 certificate FFM adapter"),
        ("Feature 008 certificate and Apply verification", "JDK 26 certificate FFM adapter"),
    ],
    "XH-PARITY": [
        ("Feature 006 hierarchy verification", "JDK 25 hierarchy FFM routing"),
        ("Feature 006 hierarchy verification", "JDK 26 hierarchy FFM routing"),
    ],
    "XH-SANITIZERS": [
        ("Native sanitizer matrix", "Clang ASan UBSan core runtime ABI fuzz"),
        ("Native sanitizer matrix", "GCC TSan reactor recovery"),
        (
            "Feature 008 certificate and Apply verification",
            "Clang ASan UBSan certificate chain",
        ),
        (
            "Feature 008 certificate and Apply verification",
            "Clang TSan certificate durability",
        ),
    ],
}


def git_text(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True, text=True
    )
    require(process.returncode == 0, "GIT_FAILED", process.stderr.strip())
    return process.stdout.strip()


def changed_paths(start: str, end: str) -> list[str]:
    output = git_text("diff", "--name-only", start, end, "--")
    return sorted(line.replace("\\", "/") for line in output.splitlines() if line)


def commit_bytes(commit: str, path: str) -> bytes:
    process = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=False, capture_output=True
    )
    require(process.returncode == 0, "SOURCE_PATH_MISSING", path)
    return process.stdout


def validate_single_parent(commit: str, expected_parent: str, code: str) -> None:
    lineage = git_text("rev-list", "--parents", "-n", "1", commit).split()
    require(len(lineage) == 2 and lineage[1] == expected_parent, code)


def validate_exact_checkouts(commit: str) -> None:
    head_expression = "ref: ${{ github.event.pull_request.head.sha || github.sha }}"
    feature_expression = "ref: ${{ env.SOURCE_SHA }}"
    for path in sorted(EXACT_WORKFLOWS):
        text = commit_bytes(commit, path).decode("utf-8")
        checkout_count = text.count("uses: actions/checkout@")
        expression = (
            feature_expression if path.endswith("feature010-exactness.yml") else head_expression
        )
        require(checkout_count > 0, "WORKFLOW_CHECKOUT_MISSING", path)
        require(text.count(expression) == checkout_count, "WORKFLOW_NOT_EXACT_HEAD", path)


def validate_no_post_execution_evidence(commit: str) -> None:
    for path in (CI_PATH, EXECUTION_PATH, STATUS_PATH):
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{path.as_posix()}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        ).returncode
        require(exists != 0, "SOURCE_CONTAINS_POST_EXECUTION_EVIDENCE", path.as_posix())


def validate_historical_source() -> None:
    historical = source_identity(HISTORICAL_FAIL_COMMIT)
    require(historical["tree"] == HISTORICAL_FAIL_TREE, "HISTORICAL_SOURCE_TREE")
    validate_single_parent(HISTORICAL_FAIL_COMMIT, BASE_COMMIT, "HISTORICAL_SOURCE_PARENT")
    actual_paths = set(changed_paths(BASE_COMMIT, HISTORICAL_FAIL_COMMIT))
    require(
        actual_paths == HISTORICAL_SOURCE_PATHS,
        "HISTORICAL_SOURCE_PATH_SET",
        ",".join(sorted(actual_paths ^ HISTORICAL_SOURCE_PATHS)),
    )
    protected = sorted(path for path in actual_paths if path.startswith(PROTECTED_PREFIXES))
    require(not protected, "HISTORICAL_SOURCE_PROTECTED_DIFF", ",".join(protected))
    validate_no_post_execution_evidence(HISTORICAL_FAIL_COMMIT)
    validate_exact_checkouts(HISTORICAL_FAIL_COMMIT)


def validate_source(source: dict[str, str]) -> None:
    commit = source["commit"]
    require(source == source_identity(commit), "STATUS_SOURCE_IDENTITY")
    validate_historical_source()
    if commit == HISTORICAL_FAIL_COMMIT:
        return

    validate_single_parent(commit, HISTORICAL_FAIL_COMMIT, "DESIGN_SOURCE_PARENT")
    design_paths = set(changed_paths(HISTORICAL_FAIL_COMMIT, commit))
    require(
        design_paths == DESIGN_PATHS,
        "DESIGN_SOURCE_PATH_SET",
        ",".join(sorted(design_paths ^ DESIGN_PATHS)),
    )
    actual_paths = set(changed_paths(BASE_COMMIT, commit))
    require(
        actual_paths == SOURCE_PATHS,
        "SOURCE_PATH_SET",
        ",".join(sorted(actual_paths ^ SOURCE_PATHS)),
    )
    protected = sorted(path for path in design_paths if path.startswith(PROTECTED_PREFIXES))
    require(not protected, "DESIGN_SOURCE_PROTECTED_DIFF", ",".join(protected))
    require(
        not any("/evidence/" in f"/{path}" for path in design_paths),
        "DESIGN_SOURCE_EVIDENCE_DIFF",
    )
    validate_no_post_execution_evidence(commit)
    validate_exact_checkouts(commit)


def sha256_id(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def final_gates() -> list[dict[str, Any]]:
    result = json.loads(json.dumps(EXPECTED_GATES))
    for gate in result:
        if gate["status"] == "REQUIRES_EXACT_HEAD_CI":
            gate["status"] = "PASS_EXACT_HEAD_CI"
    return result


def ci_gate_bindings(ci: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = []
    for gate_id, jobs in sorted(CI_GATE_JOBS.items()):
        for workflow, job_name in jobs:
            run = ci["runs"][workflow]
            matching = [job for job in run["jobs"] if job["name"] == job_name]
            require(len(matching) == 1, "CI_GATE_JOB_MISSING", f"{gate_id}:{job_name}")
            job = matching[0]
            bindings.append(
                {
                    "gate_id": gate_id,
                    "job_id": job["database_id"],
                    "job_name": job_name,
                    "run_id": run["database_id"],
                    "url": job["url"],
                    "workflow": workflow,
                }
            )
    return bindings


def expected_status(
    execution: dict[str, Any],
    execution_raw: bytes,
    ci: dict[str, Any],
    ci_raw: bytes,
) -> dict[str, Any]:
    source = execution["source"]
    require(ci["source"] == source, "STATUS_EVIDENCE_SOURCE_DIVERGENCE")
    validate_source(source)
    blockers = [
        gate["gate_id"] for gate in final_gates() if str(gate["status"]).startswith("BLOCKED_")
    ]
    require(not blockers, "MANDATORY_EXACTNESS_GATES_BLOCKED", ",".join(blockers))
    return {
        "architecture_coverage": execution["architecture_coverage"],
        "attack_coverage": execution["attack_coverage"],
        "authority": {
            "definition_execution_authorized": False,
            "feature010_go": False,
            "pilot_execution_authorized": False,
            "primary_observation_count": 0,
            "qualifying_gate_c": False,
            "qualifying_gate_d": False,
            "result_qc": None,
        },
        "base_commit": BASE_COMMIT,
        "ci": {
            "artifacts": ci["artifacts"],
            "exact_head": source["commit"],
            "gate_bindings": ci_gate_bindings(ci),
            "required_job_count": ci["required_job_count"],
            "run_ids": {name: value["database_id"] for name, value in sorted(ci["runs"].items())},
            "status": "PASS",
        },
        "completed_tasks": COMPLETED_TASKS,
        "evidence": {
            "ci_path": CI_PATH.as_posix(),
            "ci_sha256": sha256_id(ci_raw),
            "execution_path": EXECUTION_PATH.as_posix(),
            "execution_sha256": sha256_id(execution_raw),
        },
        "formal_impact": {
            "formal_semantics_id": FORMAL_ID,
            "new_externally_visible_transition": False,
            "production_semantics_changed": False,
            "result": "NO_SEMANTIC_CHANGE_REFINEMENT_AND_QUALIFICATION_ONLY",
        },
        "gates": final_gates(),
        "limitations": LIMITATIONS,
        "production_and_protected_diff": {
            "paths": [],
            "protected_prefixes": list(PROTECTED_PREFIXES),
        },
        "profile_decision": execution["profile_decision"],
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "PASS_EXACTNESS_ONLY",
        "type_name": "FEATURE010_EXACTNESS_STATUS",
    }


def checklist_state(text: str, pattern: str) -> list[tuple[str, int]]:
    return [(marker, int(number)) for marker, number in re.findall(pattern, text, re.MULTILINE)]


def validate_overlay(source_commit: str, *, allow_worktree: bool) -> str:
    if allow_worktree:
        require(git_text("rev-parse", "HEAD") == source_commit, "WORKTREE_SOURCE_HEAD")
        tracked = {
            line.replace("\\", "/")
            for line in git_text("diff", "--name-only", source_commit, "--").splitlines()
            if line
        }
        untracked = {
            line.replace("\\", "/")
            for line in git_text(
                "ls-files", "--others", "--exclude-standard", "--", *sorted(OVERLAY_PATHS)
            ).splitlines()
            if line
        }
        actual = tracked | untracked
        require(
            actual == OVERLAY_PATHS,
            "WORKTREE_OVERLAY_PATH_SET",
            ",".join(sorted(actual ^ OVERLAY_PATHS)),
        )
        candidate = "WORKTREE"
    else:
        head = git_text("rev-parse", "HEAD")
        additions = [
            line
            for line in git_text(
                "log",
                "--format=%H",
                "--diff-filter=A",
                head,
                "--",
                STATUS_PATH.as_posix(),
            ).splitlines()
            if line
        ]
        candidates = []
        for commit in additions:
            parent = git_text("rev-parse", f"{commit}^")
            if (
                parent == source_commit
                and set(changed_paths(source_commit, commit)) == OVERLAY_PATHS
            ):
                candidates.append(commit)
        require(len(candidates) == 1, "IMMUTABLE_OVERLAY_COMMIT", ",".join(candidates))
        candidate = candidates[0]
        require(
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", candidate, head],
                cwd=ROOT,
                check=False,
                capture_output=True,
            ).returncode
            == 0,
            "OVERLAY_NOT_ANCESTOR",
        )
        actual = set(changed_paths(source_commit, candidate))
        require(
            actual == OVERLAY_PATHS, "OVERLAY_PATH_SET", ",".join(sorted(actual ^ OVERLAY_PATHS))
        )
        descendant_changes = [
            line
            for line in git_text(
                "log",
                "--format=%H",
                f"{candidate}..{head}",
                "--",
                *sorted(OVERLAY_PATHS),
            ).splitlines()
            if line
        ]
        require(
            not descendant_changes,
            "IMMUTABLE_OVERLAY_MODIFIED",
            ",".join(descendant_changes),
        )
        relevant = sorted(SOURCE_PATHS | OVERLAY_PATHS | set(PROTECTED_PREFIXES))
        require(
            not git_text("status", "--porcelain=v1", "--untracked-files=all", "--", *relevant),
            "RELEVANT_WORKTREE_NOT_CLEAN",
        )
    return candidate


def validate_checklists() -> None:
    tasks = (ROOT / FEATURE / "tasks.md").read_text(encoding="utf-8")
    runtime = (ROOT / FEATURE / "runtime-tasks.md").read_text(encoding="utf-8")
    semantic = checklist_state(tasks, r"^- \[([ x])\] T(\d{3})\b")
    runtime_state = checklist_state(runtime, r"^- \[([ x])\] \*\*HR010-(\d{3})\*\*")
    expected_semantic = [("x", value) for value in range(35)]
    expected_semantic.extend((" ", value) for value in range(35, 55))
    expected_runtime = [("x", value) for value in range(1, 15)]
    expected_runtime.extend((" ", value) for value in range(15, 19))
    require(semantic == expected_semantic, "EXACTNESS_SEMANTIC_CHECKLIST")
    require(runtime_state == expected_runtime, "EXACTNESS_RUNTIME_CHECKLIST")
    required_phrases = {
        FEATURE / "exactness-safety.md": (
            "PASS_EXACTNESS_ONLY",
            "CURRENT_LINEAGE_SIDECAR_NOT_IMPLEMENTED",
            "NO_EXACT_PINNED_RUNNER_AVAILABLE",
        ),
        FEATURE / "plan.md": ("T028-T034", "HR010-004-014", "not Feature 010 GO"),
        FEATURE / "runtime-profile.md": (
            "EMBEDDED_FFM",
            "no crash-isolation claim",
            "pilot configuration only",
        ),
    }
    for path, phrases in required_phrases.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        for phrase in phrases:
            require(phrase in text, "EXACTNESS_BOUNDARY_TEXT", f"{path.as_posix()}:{phrase}")


def load_and_validate() -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    execution, _ = canonical_document(ROOT / EXECUTION_PATH)
    ci, _ = canonical_document(ROOT / CI_PATH)
    execution_raw = (ROOT / EXECUTION_PATH).read_bytes()
    ci_raw = (ROOT / CI_PATH).read_bytes()
    verify_execution(ROOT / EXECUTION_PATH)
    verify_ci(ci, execution_raw)
    return execution, ci, execution_raw, ci_raw


def verify_repository(*, allow_worktree: bool) -> dict[str, Any]:
    execution, ci, execution_raw, ci_raw = load_and_validate()
    status, _ = canonical_document(ROOT / STATUS_PATH)
    expected = expected_status(execution, execution_raw, ci, ci_raw)
    require(status == expected, "EXACTNESS_STATUS_MISMATCH")
    candidate = validate_overlay(execution["source"]["commit"], allow_worktree=allow_worktree)
    validate_checklists()
    return {
        "candidate": candidate,
        "exact_head": execution["source"]["commit"],
        "required_job_count": ci["required_job_count"],
        "status": "PASS_EXACTNESS_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--check-source", action="store_true")
    parser.add_argument("--allow-worktree", action="store_true")
    arguments = parser.parse_args()
    try:
        require(
            sum((arguments.write, arguments.check_only, arguments.check_source)) == 1,
            "EXACT_MODE_REQUIRED",
        )
        if arguments.check_source:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            source = source_identity(arguments.source_commit)
            validate_source(source)
            result = {"source": source, "status": "PASS_EXACTNESS_SOURCE"}
        elif arguments.write:
            require(arguments.allow_worktree, "WRITE_REQUIRES_WORKTREE_MODE")
            execution, ci, execution_raw, ci_raw = load_and_validate()
            require(
                arguments.source_commit == execution["source"]["commit"],
                "WRITE_SOURCE_COMMIT",
            )
            status = expected_status(execution, execution_raw, ci, ci_raw)
            target = ROOT / STATUS_PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(canonical_bytes(status) + b"\n")
            result = verify_repository(allow_worktree=True)
        else:
            result = verify_repository(allow_worktree=arguments.allow_worktree)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RuntimeError) as error:
        print(canonical_bytes({"error": str(error), "status": "FAIL"}).decode("utf-8"))
        return 2
    print(canonical_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
