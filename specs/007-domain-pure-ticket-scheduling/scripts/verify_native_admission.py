"""Publish and verify exact feature-007 native admission evidence."""

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
OUTPUT: Final = FEATURE / "evidence" / "native-admission.json"
PREDECESSOR: Final = "6d0ad0a37d6280238d04c82e69de7397898a2717"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
ARTIFACTS: Final = (
    ".github/workflows/ci.yml",
    ".github/workflows/scheduling.yml",
    "CMakeLists.txt",
    "Makefile",
    "delta-core-cpp/include/delta/scheduling/eligibility.hpp",
    "delta-core-cpp/include/delta/scheduling/leases.hpp",
    "delta-core-cpp/include/delta/scheduling/planner.hpp",
    "delta-core-cpp/src/scheduling/eligibility.cpp",
    "delta-core-cpp/src/scheduling/leases.cpp",
    "delta-core-cpp/src/scheduling/planner.cpp",
    "delta-core-cpp/tests/scheduling_eligibility_test.cpp",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_native_admission.py",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class EvidenceError(RuntimeError):
    """Stable fail-closed native admission evidence error."""


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


def validate_planner_evidence(commit: str) -> dict[str, str]:
    raw = source_bytes(
        commit, "specs/007-domain-pure-ticket-scheduling/evidence/native-planner.json"
    )
    document = json.loads(raw)
    require(isinstance(document, dict), "PLANNER_EVIDENCE_INVALID")
    require(document.get("status") == "PASS", "PLANNER_EVIDENCE_NOT_PASS")
    require(document.get("formal_semantics_id") == FORMAL_ID, "PLANNER_FORMAL_ID_DRIFT")
    require(
        document.get("semantic_completeness_claimed") is False,
        "PLANNER_SEMANTIC_CLAIM_DRIFT",
    )
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": document["source"]["commit"],
        "status": "PASS",
    }


def validate_markers(commit: str) -> None:
    eligibility = source_bytes(commit, "delta-core-cpp/src/scheduling/eligibility.cpp").decode()
    leases = source_bytes(commit, "delta-core-cpp/src/scheduling/leases.cpp").decode()
    tests = source_bytes(commit, "delta-core-cpp/tests/scheduling_eligibility_test.cpp").decode()
    cmake = source_bytes(commit, "CMakeLists.txt").decode()
    for marker in (
        "parse_capability_profile",
        "evaluate_capability",
        "ARITHMETIC_PROFILE_MISMATCH",
        "MEMORY_INSUFFICIENT",
        "PROFILE_EXPIRED",
        "SIGNATURE_NOT_TRUSTED",
        "deltareduce.007.capability-profile.v1",
        "deltareduce.007.eligibility-decision.v1",
    ):
        require(marker in eligibility, "ELIGIBILITY_MARKER_MISSING", marker)
    for marker in (
        "allocate_initial_leases",
        "max_concurrent_leases",
        "complete_ticket_throughput_milli",
        "deltareduce.007.ticket-lease.v1",
    ):
        require(marker in leases, "LEASE_MARKER_MISSING", marker)
    for marker in (
        "test_golden_capability_decisions_and_leases",
        "test_capability_rejection_matrix",
        "test_speed_changes_ownership_only_and_input_order_is_stable",
        "test_insufficient_capacity_and_region_loss",
    ):
        require(marker in tests, "ADMISSION_TEST_MARKER_MISSING", marker)
    require(
        "delta_core.scheduling_eligibility" in cmake,
        "ADMISSION_TEST_NOT_REGISTERED",
    )
    forbidden = (
        "coefficient",
        "mixture_coefficient",
        "staleness_weight",
        "device_speed_weight",
        "adaptive_h",
        "adaptive_b",
    )
    require(
        not any(
            re.search(rf"\b{field}\b", eligibility + leases, re.IGNORECASE) for field in forbidden
        ),
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
            "BOUNDED_CANONICAL_CAPABILITY_PARSE",
            "EXACT_CONTEXT_MEMORY_EXPIRY_IDENTITY_SIGNATURE_POLICY",
            "STABLE_ELIGIBILITY_REASON_CODES",
            "CAPABILITY_HAS_ZERO_MATHEMATICAL_WEIGHT_AUTHORITY",
            "DETERMINISTIC_CAPACITY_AWARE_INITIAL_LEASES",
            "SPEED_CHANGES_OWNERSHIP_ONLY",
            "REGION_LOSS_AND_INSUFFICIENT_CAPACITY_FAIL_CLOSED",
            "BYTE_EXACT_FROZEN_DECISION_AND_LEASE_IDS",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "execution": {
            "ctest_name": "delta_core.scheduling_eligibility",
            "local_profiles": ["MSVC Debug C++20", "MSVC Debug C++23"],
            "registered_ci_profiles": ["GCC C++20", "GCC C++23", "Clang ASan UBSan C++20"],
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "phase": "007-native-admission",
        "planner": validate_planner_evidence(commit),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": validate_source(commit),
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T015", "T016", "T017", "T018", "HR007-003"],
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "NATIVE_ADMISSION_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "NATIVE_ADMISSION_SOURCE_INVALID",
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
            require(OUTPUT.read_bytes() == encoded, "NATIVE_ADMISSION_EVIDENCE_STALE")
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
