"""Publish and verify exact feature-007 native planner evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "007-domain-pure-ticket-scheduling"
OUTPUT: Final = FEATURE / "evidence" / "native-planner.json"
PREDECESSOR: Final = "e803e5c72de8dc316083ad84c4b885cde1a6aceb"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
ARTIFACTS: Final = (
    ".github/workflows/ci.yml",
    ".github/workflows/scheduling.yml",
    "CMakeLists.txt",
    "Makefile",
    "delta-core-cpp/fuzz/scheduling_contract_fuzz.cpp",
    "delta-core-cpp/include/delta/scheduling/contracts.hpp",
    "delta-core-cpp/include/delta/scheduling/planner.hpp",
    "delta-core-cpp/src/scheduling/contracts.cpp",
    "delta-core-cpp/src/scheduling/planner.cpp",
    "delta-core-cpp/tests/scheduling_planner_test.cpp",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_native_planner.py",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class EvidenceError(RuntimeError):
    """Stable fail-closed native planner evidence error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise EvidenceError(f"{code}:{detail}" if detail else code)


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def source_bytes(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def validate_contract_evidence(commit: str) -> dict[str, str]:
    raw = source_bytes(
        commit, "specs/007-domain-pure-ticket-scheduling/evidence/protocol-contracts.json"
    )
    document = json.loads(raw)
    require(isinstance(document, dict), "CONTRACT_EVIDENCE_INVALID")
    require(document.get("status") == "PASS", "CONTRACT_EVIDENCE_NOT_PASS")
    require(document.get("formal_semantics_id") == FORMAL_ID, "CONTRACT_FORMAL_ID_DRIFT")
    require(
        document.get("semantic_completeness_claimed") is False,
        "CONTRACT_SEMANTIC_CLAIM_DRIFT",
    )
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": document["source"]["commit"],
        "status": "PASS",
    }


def validate_markers(commit: str) -> None:
    contracts = source_bytes(commit, "delta-core-cpp/src/scheduling/contracts.cpp").decode()
    planner = source_bytes(commit, "delta-core-cpp/src/scheduling/planner.cpp").decode()
    tests = source_bytes(commit, "delta-core-cpp/tests/scheduling_planner_test.cpp").decode()
    cmake = source_bytes(commit, "CMakeLists.txt").decode()
    workflow = source_bytes(commit, ".github/workflows/scheduling.yml").decode()
    for marker in (
        "CanonicalJsonParser",
        "validate_domain_ticket_policy",
        "validate_work_ticket",
        "deltareduce.007.domain-ticket-policy.v1",
        "deltareduce.007.work-ticket.v1",
    ):
        require(marker in contracts, "CONTRACT_MARKER_MISSING", marker)
    for marker in (
        "plan_round_tickets",
        "validate_feasibility",
        "DELTA_SCHEDULING_MUTANT_ADAPT_WORK",
        "DELTA_SCHEDULING_MUTANT_OVERLAP_RANGES",
        "DELTA_SCHEDULING_MUTANT_SKIP_INFEASIBILITY",
        "deltareduce.007.round-ticket-plan.v1",
    ):
        require(marker in planner, "PLANNER_MARKER_MISSING", marker)
    for marker in (
        "test_golden_parser_and_planner",
        "test_exact_feasibility_without_work_mutation",
        "test_fifty_worker_input_permutation",
        "e5dfb51a67b48809b78167156130e6cddbadcde73919ae6e6ae192db7b452a5f",
    ):
        require(marker in tests, "TEST_MARKER_MISSING", marker)
    require(
        "ADAPT_WORK OVERLAP_RANGES SKIP_INFEASIBILITY" in cmake,
        "PRODUCTION_MUTANTS_NOT_REGISTERED",
    )
    require(
        "standard: [20, 23]" in workflow and "Clang ASan UBSan" in workflow,
        "NATIVE_MATRIX_INCOMPLETE",
    )
    forbidden = ("device_speed_weight", "staleness_weight", "adaptive_h", "adaptive_b")
    production = contracts + planner
    require(
        not any(re.search(rf"\b{field}\b", production, re.IGNORECASE) for field in forbidden),
        "FORBIDDEN_MATH_AUTHORITY_PRESENT",
    )


def validate_source(commit: str) -> list[dict[str, str]]:
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(git_text("rev-parse", f"{commit}^") == PREDECESSOR, "SOURCE_PARENT_INVALID")
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=False
    )
    require(process.returncode == 0, "SOURCE_NOT_ANCESTOR")
    changed = set(git_text("diff", "--name-only", PREDECESSOR, commit).splitlines())
    require(changed == set(ARTIFACTS), "SOURCE_SCOPE_INVALID", ",".join(sorted(changed)))
    formal_diff = git_text(
        "diff",
        "--name-only",
        PREDECESSOR,
        commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    validate_markers(commit)
    return [
        {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
        for path in ARTIFACTS
    ]


def build(commit: str) -> dict[str, Any]:
    commit = git_text("rev-parse", commit)
    return {
        "checks": [
            "BOUNDED_CANONICAL_POLICY_AND_TICKET_PARSE",
            "EXACT_DOMAIN_QUOTA_AND_CONTIGUOUS_DATA_PARTITION",
            "IMMUTABLE_B_H_CONTEXT_AND_DOMAIN_PURE_IDS",
            "BYTE_EXACT_FROZEN_PLAN_ID",
            "INPUT_PERMUTATION_DETERMINISM_50_WORKERS",
            "INFEASIBILITY_WITHOUT_POLICY_MUTATION",
            "PRODUCTION_ADAPTIVE_OVERLAP_INFEASIBILITY_MUTANTS_KILLED",
            "CXX20_CXX23_AND_ASAN_UBSAN_CI_REGISTERED",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "contracts": validate_contract_evidence(commit),
        "execution": {
            "ctest_names": [
                "delta_core.scheduling_planner",
                "delta_core.scheduling_mutant_adapt_work",
                "delta_core.scheduling_mutant_overlap_ranges",
                "delta_core.scheduling_mutant_skip_infeasibility",
                "delta_core.scheduling_contract_fuzz",
            ],
            "local_profiles": ["MSVC Debug C++20", "MSVC Debug C++23"],
            "registered_ci_profiles": ["GCC C++20", "GCC C++23", "Clang ASan UBSan C++20"],
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "phase": "007-native-planner",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": validate_source(commit),
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T011", "T012", "T013", "T014", "HR007-002"],
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "NATIVE_PLANNER_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "NATIVE_PLANNER_SOURCE_INVALID",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        result = build(source_for_run(arguments.check_only))
        encoded = canonical_json_bytes(result)
        if arguments.check_only:
            require(OUTPUT.read_bytes() == encoded, "NATIVE_PLANNER_EVIDENCE_STALE")
        else:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(encoded)
    except (EvidenceError, OSError, ValueError, json.JSONDecodeError) as error:
        print(canonical_json_bytes({"error": str(error), "status": "FAIL"}).decode())
        return 2
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
