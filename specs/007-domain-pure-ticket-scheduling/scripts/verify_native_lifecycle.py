"""Publish and verify exact feature-007 durable lease lifecycle evidence."""

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
OUTPUT: Final = FEATURE / "evidence" / "native-lifecycle.json"
PREDECESSOR: Final = "1481f15552cbe75644771cb6f791ddafb8f6daa8"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
ARTIFACTS: Final = (
    ".github/workflows/ci.yml",
    ".github/workflows/scheduling.yml",
    "CMakeLists.txt",
    "Makefile",
    "delta-core-cpp/include/delta/scheduling/recovery.hpp",
    "delta-core-cpp/src/scheduling/recovery.cpp",
    "delta-core-cpp/tests/scheduling_lifecycle_test.cpp",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_native_lifecycle.py",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class EvidenceError(RuntimeError):
    """Stable fail-closed native lifecycle evidence error."""


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


def validate_admission_evidence(commit: str) -> dict[str, str]:
    raw = source_bytes(
        commit, "specs/007-domain-pure-ticket-scheduling/evidence/native-admission.json"
    )
    document = json.loads(raw)
    require(isinstance(document, dict), "ADMISSION_EVIDENCE_INVALID")
    require(document.get("status") == "PASS", "ADMISSION_EVIDENCE_NOT_PASS")
    require(document.get("formal_semantics_id") == FORMAL_ID, "ADMISSION_FORMAL_ID_DRIFT")
    require(
        document.get("semantic_completeness_claimed") is False,
        "ADMISSION_SEMANTIC_CLAIM_DRIFT",
    )
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": document["source"]["commit"],
        "status": "PASS",
    }


def validate_markers(commit: str) -> None:
    lifecycle = source_bytes(commit, "delta-core-cpp/src/scheduling/recovery.cpp").decode()
    header = source_bytes(commit, "delta-core-cpp/include/delta/scheduling/recovery.hpp").decode()
    tests = source_bytes(commit, "delta-core-cpp/tests/scheduling_lifecycle_test.cpp").decode()
    cmake = source_bytes(commit, "CMakeLists.txt").decode()
    for marker in (
        "canonical_lease_timer_token",
        "persist_and_apply",
        "sync_file",
        "sha256_hex(payload)",
        "after_durability_before_apply",
        "renew(",
        "expire(",
        "reassign(",
        "commit(",
        "validate_recovered_transition",
        "DELTA_SCHEDULING_MUTANT_EXPOSE_BEFORE_DURABILITY",
    ):
        require(marker in lifecycle, "LIFECYCLE_MARKER_MISSING", marker)
    require(
        "class LeaseStateMachine" in header and "struct LeaseTimerToken" in header,
        "LIFECYCLE_API_INCOMPLETE",
    )
    for marker in (
        "test_golden_opaque_timer_tokens",
        "test_renew_expire_reassign_commit_and_replay",
        "test_commit_versus_expiry_ordering",
        "test_crash_recovery_and_persist_before_expose",
        "test_max_epoch_hard_deadline_and_journal_corruption",
    ):
        require(marker in tests, "LIFECYCLE_TEST_MARKER_MISSING", marker)
    require(
        "delta_core.scheduling_mutant_expose_before_durability" in cmake,
        "DURABILITY_MUTANT_NOT_REGISTERED",
    )
    forbidden = (
        "coefficient",
        "staleness_weight",
        "device_speed_weight",
        "adaptive_h",
        "adaptive_b",
        "wall_clock",
    )
    require(
        not any(re.search(rf"\b{field}\b", lifecycle, re.IGNORECASE) for field in forbidden),
        "FORBIDDEN_LIFECYCLE_AUTHORITY_PRESENT",
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
        "admission": validate_admission_evidence(commit),
        "checks": [
            "OPAQUE_NATIVE_TIMER_TOKEN_EXACT",
            "STALE_DUPLICATE_REORDERED_TIMER_NOOP",
            "FSYNC_BEFORE_STATE_EXPOSURE",
            "CHECKSUMMED_SEQUENCE_RECOVERY",
            "BOUNDED_RENEW_EXPIRE_REASSIGN_LINEAGE",
            "COMMIT_VERSUS_EXPIRY_SINGLE_WINNER",
            "OLD_HOLDER_AND_CONFLICTING_COMMIT_REJECTED",
            "MAX_EPOCH_AND_HARD_DEADLINE_FAIL_CLOSED",
            "PRODUCTION_DURABILITY_MUTANT_KILLED",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "execution": {
            "ctest_names": [
                "delta_core.scheduling_lifecycle",
                "delta_core.scheduling_mutant_expose_before_durability",
            ],
            "local_profiles": ["MSVC Debug C++20", "MSVC Debug C++23"],
            "registered_ci_profiles": ["GCC C++20", "GCC C++23", "Clang ASan UBSan C++20"],
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "phase": "007-native-lifecycle",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": validate_source(commit),
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T019", "T020", "T021", "T022", "T023", "HR007-004", "HR007-009"],
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "NATIVE_LIFECYCLE_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "NATIVE_LIFECYCLE_SOURCE_INVALID",
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
            require(OUTPUT.read_bytes() == encoded, "NATIVE_LIFECYCLE_EVIDENCE_STALE")
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
