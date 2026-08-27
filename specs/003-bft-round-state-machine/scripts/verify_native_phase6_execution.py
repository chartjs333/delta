"""Verify immutable refinement, four-runtime, sanitizer and fuzz execution evidence."""

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
DEFAULT_EVIDENCE = FEATURE / "evidence" / "native-phase6-execution.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_REPOSITORY = "chartjs333/delta"
TASK_IDS = [
    "T040",
    "T041",
    "T042",
    "T043",
    "T044",
    "T045",
    "T046",
    "T047",
    "T048",
    "HR003-020",
    "HR003-021",
    "HR003-022",
    "HR003-023",
]
ARTIFACT_PATHS = (
    ".github/workflows/native-verification.yml",
    ".github/workflows/native.yml",
    "CMakeLists.txt",
    "delta-core-cpp/src/transition.cpp",
    "delta-ffi/src/delta_abi.cpp",
    "delta-ffi/tests/fuzz_smoke_test.cpp",
    "delta-runtime-cpp/src/runtime.cpp",
    "delta-runtime-cpp/tests/native_exit_test.cpp",
    "delta-runtime-cpp/tests/native_mutant_test.cpp",
    "delta-runtime-cpp/tests/trace_exporter.cpp",
    "delta-runtime-cpp/tests/trace_support.hpp",
    "formal/schemas/formal-trace.schema.json",
    "formal/scripts/check-refinement.py",
    "specs/003-bft-round-state-machine/evidence/mutants/native-effect-before-durability.json",
    "specs/003-bft-round-state-machine/evidence/mutants/native-view-without-qc.json",
    "specs/003-bft-round-state-machine/evidence/traces/native-certified-abort.json",
    "specs/003-bft-round-state-machine/evidence/traces/native-crash-recovery.json",
    "specs/003-bft-round-state-machine/evidence/traces/native-normal.json",
    "specs/003-bft-round-state-machine/evidence/traces/native-view-change.json",
    "specs/003-bft-round-state-machine/scripts/run_native_phase6.sh",
    "specs/003-bft-round-state-machine/scripts/run_native_sanitizers.sh",
)
COMPILER_JOBS = {
    "gcc-14.2.0 C++20/C++23": "Compile and test both language modes offline",
    "clang-20.1.8 C++20/C++23": "Compile and test both language modes offline",
    "JDK 25 runtime descriptor": "Compile and verify descriptor with offline execution policy",
    "JDK 26 runtime descriptor": "Compile and verify descriptor with offline execution policy",
}
SANITIZER_JOBS = {
    "Clang ASan UBSan core runtime ABI fuzz": "Run ASan and UBSan offline",
    "GCC TSan reactor recovery": "Run TSan offline",
}
EXPECTED_CHECKS = [
    "FOUR_INDEPENDENT_NATIVE_RUNTIMES_100_TICKETS",
    "STATE_EFFECT_WAL_HASHES_BYTE_IDENTICAL",
    "CRASH_RESTART_EQUALS_UNINTERRUPTED",
    "NORMAL_VIEW_ABORT_CRASH_RECOVERY_TRACE_REPRODUCTION",
    "FEATURE000_REFINEMENT_ACCEPTS_ALL_NATIVE_LEGAL_TRACES",
    "REAL_VIEW_AND_DURABILITY_MUTANTS_REJECTED",
    "CLANG_ASAN_UBSAN_CORE_RUNTIME_ABI_FUZZ_SUCCESS",
    "GCC_TSAN_REACTOR_RECOVERY_SUCCESS",
    "BOUNDED_PARSER_ABI_FUZZ_2052_CASES",
    "GCC_CLANG_CPP20_CPP23_SUCCESS",
    "STATIC_ARCHITECTURE_AND_FORBIDDEN_PATH_GATE_SUCCESS",
]
EXPECTED_EXIT_RESULT = {
    "effect_transcript_sha256": "11d4f62cba6b96eb17710e023c910ff67da69eebaf3896b275f551c443a3147d",
    "final_state_id": "sha256:c6fcf9131d0a481aee2918bf894dbebc62442dcb26be3c559630841f4d26f967",
    "runtime_count": 4,
    "status": "PASS",
    "ticket_count": 100,
    "wal_file_sha256": "cc08e6944772f16e460495963ae4bdd630abeb7afb7126e13b95a636e3c54f90",
    "wal_transcript_sha256": "9ddb1ff79eb2ef556e1310aa9cf057fadbe9dd50e952307473bbcd9775b72a06",
}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class NativePhase6EvidenceError(RuntimeError):
    """Stable fail-closed native phase-6 evidence error."""


def reject(code: str, detail: str = "") -> None:
    raise NativePhase6EvidenceError(f"{code}:{detail}" if detail else code)


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


def verify_run(
    run: Any,
    commit: str,
    expected_jobs: dict[str, str],
) -> None:
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
    require(isinstance(jobs, list) and len(jobs) == len(expected_jobs), "JOB_SET_INVALID")
    by_name = {job.get("name"): job for job in jobs if isinstance(job, dict)}
    require(set(by_name) == set(expected_jobs), "JOB_NAMES_INVALID")
    job_ids: set[int] = set()
    for name, step in expected_jobs.items():
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


def verify(document: dict[str, Any]) -> dict[str, Any]:
    require(document.get("schema_version") == "1.0.0", "SCHEMA_VERSION_INVALID")
    require(document.get("status") == "PASS", "EVIDENCE_STATUS_NOT_PASS")
    require(document.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "FORMAL_ID_INVALID")
    require(document.get("formal_impact") == "REFINEMENT_ONLY", "FORMAL_IMPACT_INVALID")
    require(document.get("task_ids") == TASK_IDS, "TASK_IDS_INVALID")
    require(document.get("checks") == EXPECTED_CHECKS, "CHECK_SET_INVALID")
    require(document.get("exit_result") == EXPECTED_EXIT_RESULT, "EXIT_RESULT_INVALID")
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
        "delta-runtime-cpp/tests/native_exit_test.cpp",
        (
            "validator <= 4U",
            "command_set.size() == 201U",
            "verify_crash_equivalence",
            "wal_file_sha256",
        ),
        "NATIVE_EXIT_CONTRACT_INCOMPLETE",
    )
    require_fragments(
        commit,
        "specs/003-bft-round-state-machine/scripts/run_native_phase6.sh",
        (
            "native-exit",
            "trace-exporter",
            "fuzz-smoke",
            "view-mutant",
            "durability-mutant",
            "cmp",
        ),
        "NATIVE_PHASE6_CI_INCOMPLETE",
    )
    require_fragments(
        commit,
        "specs/003-bft-round-state-machine/scripts/run_native_sanitizers.sh",
        (
            "-fsanitize=address,undefined",
            "-fsanitize=thread",
            "fuzz-sanitized",
            "runtime-tsan",
        ),
        "SANITIZER_CONTRACT_INCOMPLETE",
    )
    native_workflow = git_bytes("show", f"{commit}:.github/workflows/native.yml").decode()
    sanitizer_workflow = git_bytes(
        "show", f"{commit}:.github/workflows/native-verification.yml"
    ).decode()
    require(
        "run_native_phase6.sh" in native_workflow
        and "docker run --rm --network none" in native_workflow,
        "NATIVE_WORKFLOW_POLICY_INVALID",
    )
    require(
        "run_native_sanitizers.sh" in sanitizer_workflow
        and sanitizer_workflow.count("docker run --rm --network none") == 2,
        "SANITIZER_WORKFLOW_POLICY_INVALID",
    )

    runs = document.get("runs")
    require(isinstance(runs, dict) and set(runs) == {"compiler", "sanitizer"}, "RUN_SET_INVALID")
    verify_run(runs["compiler"], commit, COMPILER_JOBS)
    verify_run(runs["sanitizer"], commit, SANITIZER_JOBS)
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
    except (NativePhase6EvidenceError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        failure = {
            "error_code": str(error),
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
