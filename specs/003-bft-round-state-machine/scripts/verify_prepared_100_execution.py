"""Verify exact native execution evidence for the canonical 100-ticket prepared fixture."""

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
DEFAULT_EVIDENCE = FEATURE / "evidence" / "prepared-100-execution.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_REPOSITORY = "chartjs333/delta"
ARTIFACT_PATHS = (
    ".github/workflows/native.yml",
    "CMakeLists.txt",
    "delta-core-cpp/include/delta/core/arithmetic.hpp",
    "delta-core-cpp/include/delta/core/consensus.hpp",
    "delta-core-cpp/src/arithmetic.cpp",
    "delta-core-cpp/src/consensus.cpp",
    "delta-core-cpp/src/protocol.cpp",
    "delta-core-cpp/src/transition.cpp",
    "delta-core-cpp/tests/prepared_100_test.cpp",
    "delta-protocol/fixtures/003/cross-language/prepared-100-v1.json",
    "formal/tla/DeltaReduce.tla",
)
EXPECTED_JOBS = {
    "gcc-14.2.0 C++20/C++23": "Compile and test both language modes offline",
    "clang-20.1.8 C++20/C++23": "Compile and test both language modes offline",
}
EXPECTED_CHECKS = [
    "CANONICAL_100_PREPARED_ENVELOPES",
    "ONE_COMMITMENT_ROOT_PER_CONFIGURED_TICKET",
    "EXACT_AVAILABILITY_COVERAGE_BEFORE_FREEZE",
    "IMMUTABLE_CANONICALLY_ORDERED_INPUT_FREEZE",
    "CHECKED_INT128_PREPARED_REDUCTION",
    "FORWARD_REVERSE_ARRIVAL_EXACT_IDENTITY",
    "EXACT_TRANSCRIPT_AND_ELIGIBLE_STATE_IDS",
    "GCC_CLANG_CPP20_CPP23_SUCCESS",
]
EXPECTED_FIXTURE = {
    "availability_threshold": 3,
    "expected_eligible_state_id": (
        "sha256:c6fcf9131d0a481aee2918bf894dbebc62442dcb26be3c559630841f4d26f967"
    ),
    "expected_frozen_input_transcript_sha256": (
        "41837be4d6f4a722b463fe10660bc7c93fe91a79767f8b4fc247aba36b1e81f1"
    ),
    "expected_prepared_transcript_sha256": (
        "4de854f3940f017a994795a229a91a0369b8624ec5b8de039402b2e9685f7701"
    ),
    "expected_sum_0_high": "0",
    "expected_sum_0_low": "200",
    "expected_sum_1_high": "0",
    "expected_sum_1_low": "400",
    "expected_sum_2_high": "0",
    "expected_sum_2_low": "0",
    "expected_sum_3_high": "0",
    "expected_sum_3_low": "0",
    "formal_semantics_id": EXPECTED_FORMAL_ID,
    "formula_id": "prepared-100-linear-alternating-v1",
    "integer_profile_id": "bft-int-fixture-v1",
    "parameter_id": "decoder.bias",
    "round_id": "round-003-fixture",
    "schema_version": "1.0.0",
    "semantic_completeness_claimed": False,
    "shard_id": "shard-000",
    "ticket_count": 100,
    "ticket_id_pattern": "ticket-%03u",
    "value_count": 4,
}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class Prepared100EvidenceError(RuntimeError):
    """Stable fail-closed prepared-100 evidence error."""


def reject(code: str, detail: str = "") -> None:
    raise Prepared100EvidenceError(f"{code}:{detail}" if detail else code)


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


def verify(document: dict[str, Any]) -> dict[str, Any]:
    require(document.get("schema_version") == "1.0.0", "SCHEMA_VERSION_INVALID")
    require(document.get("status") == "PASS", "EVIDENCE_STATUS_NOT_PASS")
    require(document.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "FORMAL_ID_INVALID")
    require(document.get("formal_impact") == "REFINEMENT_ONLY", "FORMAL_IMPACT_INVALID")
    require(document.get("task_ids") == ["T024"], "TASK_IDS_INVALID")
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

    fixture = json.loads(
        git_bytes(
            "show", f"{commit}:delta-protocol/fixtures/003/cross-language/prepared-100-v1.json"
        )
    )
    for key, value in EXPECTED_FIXTURE.items():
        require(fixture.get(key) == value, "FIXTURE_VALUE_INVALID", key)
    require(
        fixture.get("attester_ids") == ["storage-1", "storage-2", "storage-3", "storage-4"],
        "FIXTURE_ATTESTERS_INVALID",
    )

    tests = git_bytes("show", f"{commit}:delta-core-cpp/tests/prepared_100_test.cpp").decode()
    for fragment in (
        "protocol::parse_prepared_integer_shard(bytes) == shard",
        "ledger.record_commitment",
        "ledger.record_availability",
        "const auto frozen = ledger.freeze()",
        "arithmetic::checked_multiply",
        "arithmetic::checked_add",
        "run_fixture(fixture, false)",
        "run_fixture(fixture, true)",
        "forward == reverse",
        "FINALIZE_INPUT_FREEZE",
    ):
        require(fragment in tests, "PREPARED_TEST_SET_INCOMPLETE", fragment)
    workflow = git_bytes("show", f"{commit}:.github/workflows/native.yml").decode()
    require("delta-core-prepared-100" in workflow, "PREPARED_CI_MISSING")

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
    except (Prepared100EvidenceError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
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
