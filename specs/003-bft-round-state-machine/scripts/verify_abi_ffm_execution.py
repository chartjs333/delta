"""Verify immutable native C ABI and JDK FFM execution evidence for feature 003."""

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
DEFAULT_EVIDENCE = FEATURE / "evidence" / "abi-ffm-execution.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_REPOSITORY = "chartjs333/delta"
TASK_IDS = [
    "T032",
    "T033",
    "T034",
    "T035",
    "T036",
    "T037",
    "T038",
    "T039",
    "HR003-014",
    "HR003-015",
    "HR003-016",
    "HR003-017",
    "HR003-018",
    "HR003-019",
]
ARTIFACT_PATHS = (
    ".github/workflows/native.yml",
    "CMakeLists.txt",
    "delta-ffi/include/delta_abi.h",
    "delta-ffi/src/delta_abi.cpp",
    "delta-ffi/tests/abi_test.cpp",
    "delta-ffi/tests/header_c_test.c",
    "delta-node-java/src/test/java/io/deltareduce/node/NativeRuntimeFfmConformance.java",
    "delta-protocol/schemas/003/delta-abi-v1.json",
)
EXPECTED_JOBS = {
    "gcc-14.2.0 C++20/C++23": "Compile and test both language modes offline",
    "clang-20.1.8 C++20/C++23": "Compile and test both language modes offline",
    "JDK 25 runtime descriptor": "Compile and verify descriptor with offline execution policy",
    "JDK 26 runtime descriptor": "Compile and verify descriptor with offline execution policy",
}
EXPECTED_CHECKS = [
    "FROZEN_ABI_DESCRIPTOR_AND_STATUS_LAYOUT",
    "C11_HEADER_GCC_CLANG_SUCCESS",
    "EXCEPTION_CONTAINMENT_WITHOUT_PARTIAL_OUTPUT",
    "CALLER_BUFFER_ZERO_CAPACITY_RETRY",
    "SYNCHRONOUS_BORROWED_MEMORY_LIFETIME",
    "OPAQUE_HANDLE_EXPLICIT_IDEMPOTENT_RELEASE",
    "JDK25_JDK26_FFM_SUCCESS",
    "BORROWED_COPY_EFFECT_BYTES_IDENTICAL",
    "ABI_SCHEMA_PROTOCOL_FORMAL_BUILD_MISMATCH_FAIL_CLOSED",
    "GCC_CLANG_CPP20_CPP23_SUCCESS",
]

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class AbiFfmEvidenceError(RuntimeError):
    """Stable fail-closed ABI/FFM evidence error."""


def reject(code: str, detail: str = "") -> None:
    raise AbiFfmEvidenceError(f"{code}:{detail}" if detail else code)


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
        "delta-ffi/include/delta_abi.h",
        (
            "typedef struct delta_runtime delta_runtime_t;",
            "DELTA_ABI_DESCRIPTOR_SIZE UINT32_C(64)",
            "DELTA_ABI_OPEN_OPTIONS_SIZE UINT32_C(128)",
            "DELTA_STATUS_INTERNAL_ERROR = 14",
            "delta_runtime_submit_borrowed",
            "delta_runtime_submit_copy",
            "delta_runtime_release(delta_runtime_t** runtime)",
        ),
        "ABI_HEADER_CONTRACT_INCOMPLETE",
    )
    require_fragments(
        commit,
        "delta-ffi/src/delta_abi.cpp",
        (
            "catch (const delta::runtime::RuntimeError& error)",
            "catch (const std::bad_alloc&)",
            "catch (...)",
            "effect_output->required = 0U",
            "effect_output->written = 0U",
            "auto owned_copy = copy_bytes(command)",
            "*runtime = nullptr",
        ),
        "ABI_BOUNDARY_INCOMPLETE",
    )
    require_fragments(
        commit,
        "delta-ffi/tests/abi_test.cpp",
        (
            "test_frozen_descriptor_and_status_taxonomy",
            "test_startup_mismatch_matrix",
            "test_open_submit_snapshot_release_and_memory_rules",
            "DELTA_STATUS_BUFFER_TOO_SMALL",
            "borrowed_effect == copy_effect",
            "repeated null handle release was not idempotent",
        ),
        "ABI_TEST_SET_INCOMPLETE",
    )
    require_fragments(
        commit,
        "delta-node-java/src/test/java/io/deltareduce/node/NativeRuntimeFfmConformance.java",
        (
            "Linker.nativeLinker()",
            "SymbolLookup.libraryLookup",
            "delta_runtime_submit_borrowed",
            "delta_runtime_submit_copy",
            "Arrays.equals(borrowedEffect, copiedEffect)",
            "repeated FFM release failed",
        ),
        "JDK_FFM_HARNESS_INCOMPLETE",
    )
    workflow = git_bytes("show", f"{commit}:.github/workflows/native.yml").decode()
    for fragment in (
        "-std=c11",
        "docker run --rm --network none",
        "Build native FFM library offline",
        "--enable-native-access=ALL-UNNAMED",
        "NativeRuntimeFfmConformance",
    ):
        require(fragment in workflow, "ABI_FFM_CI_INCOMPLETE", fragment)

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
    job_ids: set[int] = set()
    for name, step in EXPECTED_JOBS.items():
        job = by_name[name]
        job_id = job.get("database_id")
        require(
            isinstance(job_id, int) and job_id > 0 and job_id not in job_ids,
            "JOB_ID_INVALID",
            name,
        )
        job_ids.add(job_id)
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
    except (AbiFfmEvidenceError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
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
