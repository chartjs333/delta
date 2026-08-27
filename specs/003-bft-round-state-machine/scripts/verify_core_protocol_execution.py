"""Verify content-addressed execution evidence for strict feature-003 protocol types."""

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
DEFAULT_EVIDENCE = FEATURE / "evidence" / "core-protocol-execution.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_REPOSITORY = "chartjs333/delta"
ARTIFACT_PATHS = (
    ".github/workflows/native.yml",
    "CMakeLists.txt",
    "delta-core-cpp/include/delta/core/protocol.hpp",
    "delta-core-cpp/src/protocol.cpp",
    "delta-core-cpp/tests/protocol_test.cpp",
    "delta-protocol/fixtures/003/cross-language/golden-v1.json",
    "delta-protocol/fixtures/003/invalid/canonical-binary-negative-v1.json",
    "delta-protocol/fixtures/003/valid/protocol-inputs-v1.json",
    "delta-protocol/schemas/003/protocol-types-v1.json",
    "specs/003-bft-round-state-machine/evidence/core-architecture.json",
    "specs/003-bft-round-state-machine/evidence/native-supply-chain.json",
)
EXPECTED_JOBS = {
    "gcc-14.2.0 C++20/C++23": "Compile and test both language modes offline",
    "clang-20.1.8 C++20/C++23": "Compile and test both language modes offline",
}
EXPECTED_CHECKS = [
    "EXPLICIT_COMMAND_STATE_QC_SHARD_TYPES",
    "CANONICAL_ENCODERS_GOLDEN_EXACT",
    "BOUNDED_DECODER_REUSED",
    "EXACT_FIELD_SETS_AND_TYPES",
    "CONTENT_IDS_AND_CONSTANTS_VALIDATED",
    "CANONICAL_DECIMAL_RANGES_VALIDATED",
    "QC_QUORUM_AND_UNIQUENESS_VALIDATED",
    "PREPARED_PROFILE_AND_VALUES_VALIDATED",
    "GCC_CLANG_CPP20_CPP23_SUCCESS",
]

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class CoreProtocolEvidenceError(RuntimeError):
    """Stable fail-closed core protocol evidence error."""


def reject(code: str, detail: str = "") -> None:
    raise CoreProtocolEvidenceError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        reject("GIT_COMMAND_FAILED", completed.stderr.decode(errors="replace").strip())
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def expected_artifacts(commit: str) -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest(),
        }
        for path in ARTIFACT_PATHS
    ]


def verify(document: dict[str, Any]) -> dict[str, Any]:
    require(document.get("schema_version") == "1.0.0", "SCHEMA_VERSION_INVALID")
    require(document.get("status") == "PASS", "EVIDENCE_STATUS_NOT_PASS")
    require(document.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "FORMAL_ID_INVALID")
    require(document.get("formal_impact") == "REFINEMENT_ONLY", "FORMAL_IMPACT_INVALID")
    require(document.get("task_ids") == ["T016", "T017", "HR003-004"], "TASK_IDS_INVALID")
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
        source.get("tree") == git_text("rev-parse", f"{commit}^{{tree}}"), "SOURCE_TREE_INVALID"
    )
    require(document.get("artifacts") == expected_artifacts(commit), "ARTIFACT_SET_INVALID")

    workflow = git_bytes("show", f"{commit}:.github/workflows/native.yml").decode("utf-8")
    for fragment in (
        "docker run --rm --network none",
        "delta-core-cpp/src/protocol.cpp",
        "delta-core-cpp/tests/protocol_test.cpp",
    ):
        require(fragment in workflow, "NATIVE_WORKFLOW_INCOMPLETE", fragment)
    tests = git_bytes("show", f"{commit}:delta-core-cpp/tests/protocol_test.cpp").decode("utf-8")
    for fragment in (
        "test_command_fails_closed",
        "test_state_fails_closed",
        "test_qc_fails_closed",
        "test_prepared_shard_fails_closed",
        "test_decimal_boundaries",
    ):
        require(fragment in tests, "NEGATIVE_TEST_SET_INCOMPLETE", fragment)

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
        value = json.loads(raw.decode("utf-8"))
        require(isinstance(value, dict), "EVIDENCE_ROOT_INVALID")
        result = verify(value)
        canonical = canonical_json_bytes(result)
        require(raw in {canonical, canonical + b"\n"}, "EVIDENCE_NOT_CANONICAL")
    except (CoreProtocolEvidenceError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2
    print(raw.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
