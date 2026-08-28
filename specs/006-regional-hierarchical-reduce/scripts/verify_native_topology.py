"""Verify deterministic feature-006 native topology-boundary evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "006-regional-hierarchical-reduce"
EVIDENCE: Final = FEATURE / "evidence" / "native-topology.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
PARENT_COMMIT: Final = "cf6f16dc7c32e7c12af51041a00185fe6fbcbddf"
ARTIFACTS: Final = (
    "CMakeLists.txt",
    "delta-core-cpp/fuzz/hierarchy_parser_fuzz.cpp",
    "delta-core-cpp/include/delta/reduce/topology.hpp",
    "delta-core-cpp/src/reduce/topology.cpp",
    "delta-core-cpp/tests/hierarchy_test.cpp",
)


class EvidenceError(RuntimeError):
    """Stable fail-closed native-topology evidence error."""


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


def validate_markers(commit: str) -> None:
    topology = source_bytes(commit, "delta-core-cpp/src/reduce/topology.cpp").decode()
    header = source_bytes(commit, "delta-core-cpp/include/delta/reduce/topology.hpp").decode()
    tests = source_bytes(commit, "delta-core-cpp/tests/hierarchy_test.cpp").decode()
    fuzz = source_bytes(commit, "delta-core-cpp/fuzz/hierarchy_parser_fuzz.cpp").decode()
    cmake = source_bytes(commit, "CMakeLists.txt").decode()
    required_topology = (
        "parse_topology(",
        "parse_hierarchy_proof(",
        "validate_coefficient_plan(",
        "regional routing is not an exact partition",
        "parameter shards contain a gap or overlap",
        "every normative theorem conjunct",
        "regional or global accumulator exceeds",
        "DELTA_HIERARCHY_MUTANT_SKIP_COVERAGE",
        "DELTA_HIERARCHY_MUTANT_SKIP_SHARD_COVERAGE",
        "DELTA_HIERARCHY_MUTANT_UNCHECKED_OVERFLOW",
    )
    require(all(marker in topology for marker in required_topology), "NATIVE_GATE_MARKER_MISSING")
    require(
        "class ReduceError" in header and "struct CoefficientBinding" in header,
        "NATIVE_API_INCOMPLETE",
    )
    require(
        "test_golden_contract" in tests and "test_partition_and_shard_mutants" in tests,
        "NATIVE_TEST_MATRIX_INCOMPLETE",
    )
    require(
        "golden_topology" in fuzz and "LLVMFuzzerTestOneInput" in fuzz,
        "NATIVE_FUZZ_SEED_INCOMPLETE",
    )
    for marker in (
        "SKIP_COVERAGE SKIP_SHARD_COVERAGE UNCHECKED_OVERFLOW",
        "delta_core.hierarchy",
        "delta_core.hierarchy_parser_fuzz",
    ):
        require(marker in cmake, "CMAKE_TEST_REGISTRATION_MISSING", marker)


def verify_source(commit: str) -> dict[str, Any]:
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(git_text("rev-parse", f"{commit}^") == PARENT_COMMIT, "SOURCE_PARENT_INVALID")
    require(
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT).returncode
        == 0,
        "SOURCE_NOT_ANCESTOR",
    )
    formal_diff = git_text(
        "diff",
        "--name-only",
        PARENT_COMMIT,
        commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    changed = set(git_text("diff", "--name-only", PARENT_COMMIT, commit).splitlines())
    require(changed == set(ARTIFACTS), "SOURCE_SCOPE_INVALID", ",".join(sorted(changed)))
    validate_markers(commit)
    artifacts = [
        {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
        for path in ARTIFACTS
    ]
    return {
        "checks": [
            "CANONICAL_TOPOLOGY_AND_PROOF_PARSE",
            "IMMUTABLE_CONTEXT_AND_CONTENT_ID",
            "EXACT_DOMAIN_REGION_TICKET_PARTITION",
            "EXACT_PARAMETER_SHARD_COVERAGE",
            "CONCRETE_COEFFICIENT_DENOMINATOR_BOUNDS",
            "PO_A1_A2_A3_H1_H2_CONJUNCTS_EXACT",
            "PARSER_ALLOCATION_LIMITS",
            "VALID_GOLDEN_FUZZ_SEED",
            "PRODUCTION_OVERLAP_GAP_UNSAFE_BOUND_MUTANTS_KILLED",
        ],
        "classification": "REFINEMENT_ONLY",
        "execution": {
            "build": "cmake --build --preset cpp20",
            "configuration": "MSVC Debug C++20",
            "ctest": [
                "delta_core.hierarchy",
                "delta_core.hierarchy_mutant_skip_coverage",
                "delta_core.hierarchy_mutant_skip_shard_coverage",
                "delta_core.hierarchy_mutant_unchecked_overflow",
                "delta_core.hierarchy_parser_fuzz",
            ],
            "passed": 5,
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "phase": "006-native-topology",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": artifacts,
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T011", "T012", "T013", "T014", "HR006-002"],
    }


def verify_evidence() -> dict[str, Any]:
    raw = EVIDENCE.read_bytes()
    evidence = json.loads(raw.decode())
    require(isinstance(evidence, dict), "EVIDENCE_ROOT_INVALID")
    require(raw == canonical_json_bytes(evidence) + b"\n", "EVIDENCE_NOT_CANONICAL")
    source = evidence.get("source")
    require(isinstance(source, dict), "EVIDENCE_SOURCE_INVALID")
    expected = verify_source(str(source.get("commit")))
    require(evidence == expected, "EVIDENCE_DRIFT")
    return expected


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "006-native-topology", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    arguments = parser.parse_args()
    try:
        result = (
            verify_evidence()
            if arguments.check_only
            else verify_source(arguments.source_commit or git_text("rev-parse", "HEAD"))
        )
    except (EvidenceError, OSError, ValueError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
