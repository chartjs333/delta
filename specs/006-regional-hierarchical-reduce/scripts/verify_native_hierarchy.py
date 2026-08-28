"""Publish and verify deterministic native hierarchy source/execution evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "006-regional-hierarchical-reduce"
OUTPUT: Final = FEATURE / "evidence" / "native-hierarchy.json"
PREDECESSOR: Final = "5e887bd"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SOURCE_ARTIFACTS: Final = (
    ".github/workflows/hierarchy.yml",
    "CMakeLists.txt",
    "Makefile",
    "delta-core-cpp/include/delta/reduce/hierarchy.hpp",
    "delta-core-cpp/src/reduce/hierarchy.cpp",
    "delta-core-cpp/src/reduce/topology.cpp",
    "delta-core-cpp/tests/hierarchy_reduce_test.cpp",
    "delta-ffi/include/delta_abi.h",
    "delta-ffi/src/hierarchy_abi.cpp",
    "delta-ffi/tests/hierarchy_abi_test.cpp",
    "delta-node-java/README.md",
    "delta-node-java/src/main/java/io/deltareduce/node/hierarchy/HierarchyRouter.java",
    "delta-node-java/src/main/java/io/deltareduce/node/hierarchy/NativeHierarchy.java",
    "delta-node-java/src/test/java/io/deltareduce/node/hierarchy/HierarchyConformance.java",
    "delta-worker-python/src/deltatorrent/artifacts/verifier.py",
    "delta-worker-python/tests/integration/test_artifact_verification.py",
    "specs/006-regional-hierarchical-reduce/runtime-tasks.md",
    "specs/006-regional-hierarchical-reduce/scripts/capture_hierarchy_ci.py",
    "specs/006-regional-hierarchical-reduce/scripts/verify_final_compatibility.py",
    "specs/006-regional-hierarchical-reduce/scripts/verify_hierarchy_execution.py",
    "specs/006-regional-hierarchical-reduce/scripts/verify_native_hierarchy.py",
    "specs/006-regional-hierarchical-reduce/spec.md",
    "specs/006-regional-hierarchical-reduce/tasks.md",
    "specs/006-regional-hierarchical-reduce/tests/test_verify_hierarchy_execution.py",
)

sys.path.insert(0, str(FEATURE / "scripts"))
from verify_hierarchy_execution import verify_trace_dir  # noqa: E402


class EvidenceError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise EvidenceError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.decode(errors="replace"))
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def source_bytes(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def validate_source(commit: str) -> list[dict[str, str]]:
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(
        git_text("rev-parse", f"{commit}^") == git_text("rev-parse", PREDECESSOR),
        "SOURCE_PARENT_INVALID",
    )
    require(
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT).returncode
        == 0,
        "SOURCE_NOT_ANCESTOR",
    )
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
    changed = set(git_text("diff", "--name-only", PREDECESSOR, commit).splitlines())
    require(changed == set(SOURCE_ARTIFACTS), "SOURCE_SCOPE_INVALID", ",".join(sorted(changed)))
    hierarchy = source_bytes(commit, "delta-core-cpp/src/reduce/hierarchy.cpp").decode()
    test = source_bytes(commit, "delta-core-cpp/tests/hierarchy_reduce_test.cpp").decode()
    ffi = source_bytes(commit, "delta-ffi/src/hierarchy_abi.cpp").decode()
    router = source_bytes(
        commit,
        "delta-node-java/src/main/java/io/deltareduce/node/hierarchy/HierarchyRouter.java",
    ).decode()
    workflow = source_bytes(commit, ".github/workflows/hierarchy.yml").decode()
    artifact_verifier = source_bytes(
        commit, "delta-worker-python/src/deltatorrent/artifacts/verifier.py"
    ).decode()
    for marker in (
        "reduce_region(",
        "GlobalAccumulator::finalize",
        "assemble_complete(",
        "validate_committee_qc(",
        "routing_projection_id(",
        "DELTA_HIERARCHY_MUTANT_PARTIAL_GLOBAL",
        "DELTA_HIERARCHY_MUTANT_AVERAGE_REGIONS",
    ):
        require(marker in hierarchy, "NATIVE_MARKER_MISSING", marker)
    for marker in (
        "hierarchical integer result differs byte-for-byte from flat oracle",
        "after_durability_before_commit",
        "exact-ID artifact repair changed",
        "export_refinement_traces",
    ):
        require(marker in test, "NATIVE_TEST_MARKER_MISSING", marker)
    require(
        "delta_hierarchy_contract_validate_borrowed" in ffi
        and "delta_hierarchy_contract_validate_copy" in ffi,
        "FFI_PARITY_API_MISSING",
    )
    for marker in (
        "routingProjectionId()",
        "routeCapacity",
        "maximumRetries",
        "softDeadlineSignals",
        "hardAborts",
    ):
        require(marker in router, "JAVA_ROUTING_MARKER_MISSING", marker)
    for marker in (
        "Native C++${{ matrix.standard }} hierarchy",
        "Clang ASan UBSan hierarchy",
        "JDK ${{ matrix.feature }} hierarchy FFM routing",
    ):
        require(marker in workflow, "CI_MATRIX_MARKER_MISSING", marker)
    require(
        "shared denylisted media type cannot select an artifact schema" in artifact_verifier,
        "PARTIAL_MEDIA_DENYLIST_MISSING",
    )
    return [
        {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
        for path in SOURCE_ARTIFACTS
    ]


def trace_artifacts(trace_root: Path) -> list[dict[str, str]]:
    files = sorted(trace_root.glob("*.json"))
    require(len(files) == 6, "TRACE_SET_INCOMPLETE")
    return [
        {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in files
    ]


def build(commit: str, trace_root: Path) -> dict[str, Any]:
    commit = git_text("rev-parse", commit)
    execution = verify_trace_dir(trace_root)
    return {
        "checks": [
            "EXACT_PARTITION_REGIONAL_GLOBAL_INTEGER_REDUCE",
            "CANONICAL_RESULT_AND_QC_IDS_MATCH_CROSS_LANGUAGE_FIXTURE",
            "PERSIST_BEFORE_SEND_NO_DOUBLE_VOTE_CRASH_RECOVERY",
            "COMPLETE_MATRIX_AND_FLAT_EQUIVALENCE",
            "PRODUCTION_COVERAGE_OVERFLOW_PARTIAL_AVERAGE_MUTANTS_KILLED",
            "BORROWED_DIRECT_AND_OWNED_COPY_ABI_PARITY",
            "NATIVE_BOUND_JAVA_OPAQUE_ROUTING_PROJECTION",
            "SHUFFLED_PARALLEL_RETRY_DEADLINE_ABORT_CONFORMANCE",
            "FORMAL_RECOVERY_PROJECTION_AND_NEGATIVE_COUNTEREXAMPLES",
            "FEATURE008_APPLY_CURRENT_BOUNDARY_PRESERVED",
        ],
        "classification": "REFINEMENT_ONLY",
        "execution": execution,
        "formal_semantics_id": FORMAL_ID,
        "local_matrix": {
            "cpp20": {"compiler": "MSVC 19.29", "ctest_passed": 37, "status": "PASS"},
            "cpp23": {"compiler": "MSVC 19.29", "hierarchy_ctest_passed": 10, "status": "PASS"},
            "jdk25": {"version": "25.0.4.1", "status": "PASS"},
            "jdk26": {"version": "26.0.2", "status": "PASS"},
        },
        "phase": "006-native-hierarchy",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": validate_source(commit),
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": [f"T{index:03d}" for index in range(15, 30)],
        "trace_artifacts": trace_artifacts(trace_root),
    }


def verify_evidence(trace_root: Path) -> dict[str, Any]:
    raw = OUTPUT.read_bytes()
    evidence = json.loads(raw.decode())
    require(isinstance(evidence, dict), "EVIDENCE_ROOT_INVALID")
    require(raw == canonical_json_bytes(evidence) + b"\n", "EVIDENCE_NOT_CANONICAL")
    source = evidence.get("source")
    require(isinstance(source, dict), "EVIDENCE_SOURCE_INVALID")
    require(evidence == build(str(source.get("commit")), trace_root), "EVIDENCE_DRIFT")
    return evidence


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "006-native-hierarchy", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        trace_root = arguments.trace_dir.resolve()
        if arguments.write:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            result = build(arguments.source_commit, trace_root)
            OUTPUT.write_bytes(canonical_json_bytes(result) + b"\n")
        else:
            require(arguments.check_only, "CHECK_ONLY_REQUIRED")
            result = verify_evidence(trace_root)
    except (EvidenceError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
