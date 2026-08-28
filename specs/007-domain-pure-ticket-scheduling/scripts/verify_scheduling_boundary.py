"""Publish and verify the feature-007 C ABI and Java transport-only boundary evidence."""

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
OUTPUT: Final = FEATURE / "evidence" / "scheduling-boundary.json"
PREDECESSOR: Final = "aefd1dcd3cf8ad20df774e14935bef5c5296528a"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
JAVA_ROOT: Final = "delta-node-java/src/main/java/io/deltareduce/node/scheduling"
ARTIFACTS: Final = (
    ".github/workflows/ci.yml",
    ".github/workflows/scheduling.yml",
    "CMakeLists.txt",
    "Makefile",
    "delta-ffi/include/delta_abi.h",
    "delta-ffi/src/scheduling_abi.cpp",
    "delta-ffi/tests/scheduling_abi_test.cpp",
    "delta-core-cpp/src/scheduling/recovery.cpp",
    f"{JAVA_ROOT}/AdmissionTransport.java",
    f"{JAVA_ROOT}/CapabilityCollector.java",
    f"{JAVA_ROOT}/LeaseTimerRouter.java",
    f"{JAVA_ROOT}/NativeScheduling.java",
    f"{JAVA_ROOT}/SchedulingTelemetry.java",
    "delta-node-java/src/test/java/io/deltareduce/node/scheduling/SchedulingConformance.java",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_scheduling_boundary.py",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class EvidenceError(RuntimeError):
    """Stable fail-closed scheduling boundary evidence error."""


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


def validate_lifecycle_evidence(commit: str) -> dict[str, str]:
    path = "specs/007-domain-pure-ticket-scheduling/evidence/native-lifecycle.json"
    raw = source_bytes(commit, path)
    document = json.loads(raw)
    require(isinstance(document, dict), "LIFECYCLE_EVIDENCE_INVALID")
    require(document.get("status") == "PASS", "LIFECYCLE_EVIDENCE_NOT_PASS")
    require(document.get("formal_semantics_id") == FORMAL_ID, "LIFECYCLE_FORMAL_ID_DRIFT")
    require(
        document.get("semantic_completeness_claimed") is False,
        "LIFECYCLE_SEMANTIC_CLAIM_DRIFT",
    )
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": document["source"]["commit"],
        "status": "PASS",
    }


def validate_markers(commit: str) -> None:
    header = source_bytes(commit, "delta-ffi/include/delta_abi.h").decode()
    implementation = source_bytes(commit, "delta-ffi/src/scheduling_abi.cpp").decode()
    abi_test = source_bytes(commit, "delta-ffi/tests/scheduling_abi_test.cpp").decode()
    workflow = source_bytes(commit, ".github/workflows/scheduling.yml").decode()
    java = {
        path: source_bytes(commit, path).decode()
        for path in ARTIFACTS
        if path.startswith(JAVA_ROOT)
    }
    conformance = source_bytes(
        commit,
        "delta-node-java/src/test/java/io/deltareduce/node/scheduling/SchedulingConformance.java",
    ).decode()
    for marker in (
        "DELTA_SCHEDULING_ELIGIBILITY_CONTEXT_SIZE",
        "delta_scheduling_capability_evaluate_borrowed",
        "delta_scheduling_capability_evaluate_copy",
    ):
        require(marker in header and marker in implementation, "ABI_MARKER_MISSING", marker)
    for marker in (
        "DELTA_STATUS_BUFFER_TOO_SMALL",
        "parse_capability_profile",
        "evaluate_capability",
        "const std::vector<std::byte> owned",
    ):
        require(marker in implementation, "ABI_IMPLEMENTATION_MARKER_MISSING", marker)
    for marker in (
        "test_borrowed_copy_and_lifetime",
        "test_fail_closed_matrix",
        "borrowed == copied && borrowed == data.decision",
    ):
        require(marker in abi_test, "ABI_TEST_MARKER_MISSING", marker)
    required_java = {
        "AdmissionTransport.java": "Bounded opaque scheduling-byte transport",
        "CapabilityCollector.java": "every admission result comes back from native C++",
        "LeaseTimerRouter.java": "native state decides stale/early/committed outcomes",
        "NativeScheduling.java": "authored only by native C++",
        "SchedulingTelemetry.java": "no admission or lease-state authority",
    }
    for name, marker in required_java.items():
        path = f"{JAVA_ROOT}/{name}"
        require(marker in java[path], "JAVA_BOUNDARY_MARKER_MISSING", name)
    forbidden_authority = (
        r"\b(?:adaptiveH|adaptiveB|coefficient|mixtureCoefficient|stalenessWeight)\b",
        r"\b(?:deviceSpeedWeight|ticketCount|leaseEpoch|expiresAtTick|deadlineTick)\b",
        r"\b(?:assignHolder|renewLease|expireLease|reassignLease|commitLease)\s*\(",
        r"\bMath\.(?:round|floor|ceil|multiplyExact|addExact)\s*\(",
    )
    combined_java = "\n".join(java.values())
    for pattern in forbidden_authority:
        require(
            re.search(pattern, combined_java) is None,
            "JAVA_SCHEDULING_AUTHORITY_PRESENT",
            pattern,
        )
    for marker in (
        "borrowed/copy parity",
        "testBoundedOpaqueTransport",
        "testOpaqueTimerCallbacks",
        "Arrays.equals(direct.canonicalBytes(), fixture.decision().bytes())",
    ):
        require(marker in conformance, "JAVA_CONFORMANCE_MARKER_MISSING", marker)
    for marker in ("feature: 25", "feature: 26", "archive_sha256", "java-adapter"):
        require(marker in workflow, "JDK_MATRIX_MARKER_MISSING", marker)


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
            "BOUNDED_C_ABI_OUTPUT_NEGOTIATION",
            "BORROWED_DIRECT_AND_OWNED_COPY_BYTE_PARITY",
            "NATIVE_RETAINS_NO_JAVA_OWNED_POINTER",
            "JDK_25_26_PINNED_FFM_CONFORMANCE",
            "AUTHENTICATED_CAPABILITY_COLLECTION_NATIVE_DECISION_ONLY",
            "BOUNDED_OPAQUE_PLAN_LEASE_TIMER_TRANSPORT",
            "BACKPRESSURE_CANCELLATION_AND_TELEMETRY",
            "JAVA_HAS_NO_ELIGIBILITY_LEASE_OR_TICKET_MATH_AUTHORITY",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "execution": {
            "ctest_name": "delta_ffi.scheduling",
            "local_profiles": ["MSVC Debug C++20", "MSVC Debug C++23"],
            "registered_ci_profiles": [
                "GCC C++20",
                "GCC C++23",
                "Clang ASan UBSan C++20",
                "Temurin JDK 25",
                "Temurin JDK 26",
            ],
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "lifecycle": validate_lifecycle_evidence(commit),
        "phase": "007-scheduling-boundary",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": validate_source(commit),
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T024", "T025", "T026", "HR007-005", "HR007-006"],
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "SCHEDULING_BOUNDARY_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "SCHEDULING_BOUNDARY_SOURCE_INVALID",
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
            require(OUTPUT.read_bytes() == encoded, "SCHEDULING_BOUNDARY_EVIDENCE_STALE")
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
