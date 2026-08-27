"""Verify native reactor, WAL, recovery, idempotency and crash-matrix execution evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
DEFAULT_EVIDENCE = FEATURE / "evidence" / "runtime-durability-execution.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_REPOSITORY = "chartjs333/delta"
TASK_IDS = [
    "T025",
    "T026",
    "T027",
    "T028",
    "T029",
    "T030",
    "T031",
    "HR003-009",
    "HR003-010",
    "HR003-011",
    "HR003-012",
    "HR003-013",
]
ARTIFACT_PATHS = (
    ".github/workflows/native.yml",
    "CMakeLists.txt",
    "delta-core-cpp/src/transition.cpp",
    "delta-runtime-cpp/include/delta/runtime/bounded_mpsc.hpp",
    "delta-runtime-cpp/include/delta/runtime/runtime.hpp",
    "delta-runtime-cpp/src/runtime.cpp",
    "delta-runtime-cpp/src/wal.cpp",
    "delta-runtime-cpp/src/wal.hpp",
    "delta-runtime-cpp/tests/runtime_test.cpp",
    "formal/tla/DeltaReduce.tla",
)
EXPECTED_JOBS = {
    "gcc-14.2.0 C++20/C++23": "Compile and test both language modes offline",
    "clang-20.1.8 C++20/C++23": "Compile and test both language modes offline",
}
EXPECTED_CHECKS = [
    "ONE_REACTOR_OWNER_AND_BOUNDED_MPSC",
    "APPEND_ONLY_CHECKSUMMED_MONOTONIC_WAL",
    "OS_DURABILITY_BARRIER_BEFORE_COMMIT",
    "VERIFIED_SNAPSHOT_AND_EXACT_WAL_REPLAY",
    "VOTE_JOURNAL_RECOVERED_BEFORE_ADMISSION",
    "PERSIST_BEFORE_EFFECT_EXPOSURE",
    "IDEMPOTENT_REQUEST_VOTE_AND_EFFECT_REPLAY",
    "ALL_APPEND_DURABILITY_COMMIT_EFFECT_CRASH_POINTS",
    "TORN_CORRUPT_STALE_DUPLICATE_FAIL_CLOSED",
    "UNINTERRUPTED_REPLAYED_BYTE_IDENTITY",
    "GCC_CLANG_CPP20_CPP23_SUCCESS",
]

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class RuntimeDurabilityEvidenceError(RuntimeError):
    """Stable fail-closed runtime durability evidence error."""


def reject(code: str, detail: str = "") -> None:
    raise RuntimeDurabilityEvidenceError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        reject("GIT_COMMAND_FAILED", completed.stderr.decode(errors="replace").strip())
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def expected_artifacts(commit: str) -> list[dict[str, str]]:
    return [
        {"path": path, "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest()}
        for path in ARTIFACT_PATHS
    ]


def require_fragments(commit: str, path: str, fragments: tuple[str, ...], code: str) -> None:
    text = git_bytes("show", f"{commit}:{path}").decode()
    for fragment in fragments:
        require(fragment in text, code, fragment)


def verify(document: dict[str, Any]) -> dict[str, Any]:
    require(document.get("schema_version") == "1.0.0", "SCHEMA_VERSION_INVALID")
    require(document.get("status") == "PASS", "EVIDENCE_STATUS_NOT_PASS")
    require(document.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "FORMAL_ID_INVALID")
    require(document.get("formal_impact") == "REFINEMENT_ONLY", "FORMAL_IMPACT_INVALID")
    require(document.get("task_ids") == TASK_IDS, "TASK_IDS_INVALID")
    require(document.get("checks") == EXPECTED_CHECKS, "CHECK_SET_INVALID")
    require(document.get("semantic_completeness_claimed") is False, "SEMANTIC_CLAIM_INVALID")

    source = document.get("source")
    require(isinstance(source, dict), "SOURCE_INVALID")
    commit = source.get("commit")
    require(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
        "SOURCE_COMMIT_INVALID",
    )
    require(git_text("merge-base", "--is-ancestor", commit, "HEAD") == "", "SOURCE_NOT_ANCESTOR")
    require(
        source.get("tree") == git_text("rev-parse", f"{commit}^{{tree}}"),
        "SOURCE_TREE_INVALID",
    )
    require(document.get("artifacts") == expected_artifacts(commit), "ARTIFACT_SET_INVALID")

    require_fragments(
        commit,
        "delta-runtime-cpp/include/delta/runtime/bounded_mpsc.hpp",
        ("capacity_", "try_push", "wait_pop", "condition_variable", "mutex"),
        "MPSC_CONTRACT_INCOMPLETE",
    )
    require_fragments(
        commit,
        "delta-runtime-cpp/src/wal.cpp",
        (
            "std::byte{'D'}, std::byte{'R'}, std::byte{'W'}, std::byte{'1'}",
            "core::canonical::sha256_hex",
            "append_u64(output, entry.sequence)",
            "_commit(_fileno(file))",
            "::fsync(::fileno(file))",
            "snapshot checksum mismatch",
            "runtime frame checksum mismatch",
            "resize_file",
        ),
        "WAL_SNAPSHOT_CONTRACT_INCOMPLETE",
    )
    require_fragments(
        commit,
        "delta-runtime-cpp/src/runtime.cpp",
        (
            "reactor_ = std::thread",
            "recover();",
            "accepting_.store(true)",
            "core::transition::apply(recovered_state",
            "vote_journal_.record(vote)",
            "wal_.append_and_sync(entry, false)",
            "after_durability_before_commit",
            "requests_.find(command.request_id)",
        ),
        "RUNTIME_CONTRACT_INCOMPLETE",
    )
    require_fragments(
        commit,
        "delta-runtime-cpp/tests/runtime_test.cpp",
        (
            "test_bounded_mpsc_contract",
            "test_persist_before_expose_and_request_replay",
            "test_vote_journal_recovers_before_admission",
            "test_crash_matrix_and_torn_tail_recovery",
            "test_corruption_fails_closed",
            "test_concurrent_producers_have_one_serial_state",
            "test_stale_command_rejected_without_append",
            "test_uninterrupted_and_replayed_execution_are_identical",
        ),
        "RUNTIME_TEST_SET_INCOMPLETE",
    )
    workflow = git_bytes("show", f"{commit}:.github/workflows/native.yml").decode()
    require("delta-runtime-${standard}" in workflow, "RUNTIME_CI_MISSING")

    run = document.get("run")
    require(isinstance(run, dict), "RUN_INVALID")
    run_id = run.get("database_id")
    require(isinstance(run_id, int) and run_id > 0, "RUN_ID_INVALID")
    require(run.get("repository") == EXPECTED_REPOSITORY, "RUN_REPOSITORY_INVALID")
    require(run.get("event") == "push", "RUN_EVENT_INVALID")
    require(run.get("head_sha") == commit, "RUN_SOURCE_MISMATCH")
    require(run.get("conclusion") == "success", "RUN_CONCLUSION_INVALID")
    run_url = f"https://github.com/{EXPECTED_REPOSITORY}/actions/runs/{run_id}"
    require(run.get("url") == run_url, "RUN_URL_INVALID")
    jobs = run.get("jobs")
    require(isinstance(jobs, list) and len(jobs) == len(EXPECTED_JOBS), "JOB_SET_INVALID")
    by_name = {job.get("name"): job for job in jobs if isinstance(job, dict)}
    require(set(by_name) == set(EXPECTED_JOBS), "JOB_NAMES_INVALID")
    for name, step in EXPECTED_JOBS.items():
        job = by_name[name]
        job_id = job.get("database_id")
        require(isinstance(job_id, int) and job_id > 0, "JOB_ID_INVALID", name)
        require(job.get("conclusion") == "success", "JOB_CONCLUSION_INVALID", name)
        require(job.get("verified_step") == step, "JOB_STEP_INVALID", name)
        require(job.get("url") == f"{run_url}/job/{job_id}", "JOB_URL_INVALID", name)
    return document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        require(args.check_only, "CHECK_ONLY_REQUIRED")
        raw = args.evidence.read_bytes()
        value = json.loads(raw.decode())
        require(isinstance(value, dict), "EVIDENCE_ROOT_INVALID")
        result = verify(value)
        canonical = canonical_json_bytes(result)
        require(raw in {canonical, canonical + b"\n"}, "EVIDENCE_NOT_CANONICAL")
    except (
        RuntimeDurabilityEvidenceError,
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode())
        return 2
    print(raw.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
