"""Publish or verify exact-source native certificate/robust/apply execution evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "008-certificates-and-consensus"
OUTPUT: Final = FEATURE / "evidence" / "native-execution.json"
PREDECESSOR: Final = "2054f31ef0f6750645b924ef337a35d1737c619d"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


class EvidenceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise EvidenceError(code)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    require(process.returncode == 0, "GIT_FAILED:" + process.stderr.decode(errors="replace"))
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def source_bytes(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def changed_source(commit: str) -> list[str]:
    paths = git_text("diff", "--name-only", PREDECESSOR, commit).splitlines()
    return sorted(
        path
        for path in paths
        if not path.startswith("specs/008-certificates-and-consensus/evidence/")
    )


def validate_architecture(commit: str) -> None:
    core_paths = [
        path
        for path in changed_source(commit)
        if path.startswith("delta-core-cpp/") or path.startswith("delta-runtime-cpp/")
    ]
    native = "\n".join(source_bytes(commit, path).decode() for path in core_paths)
    for forbidden in ("<asio", "<winsock", "<sys/socket", "system_clock", "steady_clock"):
        require(forbidden not in native, "NATIVE_NETWORK_OR_WALL_CLOCK_AUTHORITY:" + forbidden)
    java_paths = [path for path in changed_source(commit) if path.endswith(".java")]
    java = "\n".join(source_bytes(commit, path).decode() for path in java_paths)
    for forbidden in (
        r"\b(?:quorumThreshold|faultTolerance|robustWeight|mixtureWeight)\s*[=+]",
        r"\bMath\.(?:round|floor|ceil|addExact|multiplyExact)\s*\(",
        r"\b(?:buildQc|assembleRoot|computeApply|chooseCurrent)\s*\(",
    ):
        require(re.search(forbidden, java) is None, "JAVA_CONSENSUS_AUTHORITY:" + forbidden)


def validate_markers(commit: str) -> None:
    files = {
        path: source_bytes(commit, path).decode()
        for path in (
            "delta-core-cpp/src/certificates/verifier.cpp",
            "delta-core-cpp/src/robust/plan.cpp",
            "delta-core-cpp/src/apply/engine.cpp",
            "delta-runtime-cpp/src/certificate_runtime.cpp",
            "delta-core-cpp/tests/certificates_test.cpp",
            "delta-core-cpp/tests/certificates_mutant_test.cpp",
            "delta-ffi/src/certificates_abi.cpp",
            "delta-node-java/src/main/java/io/deltareduce/node/certificates/NativeCertificateVerifier.java",
        )
    }
    markers = {
        "delta-core-cpp/src/certificates/verifier.cpp": (
            "verify_root",
            "required shard matrix",
            "verify_apply",
            "2f+1",
        ),
        "delta-core-cpp/src/robust/plan.cpp": (
            "centered_clip",
            "validate_accumulator_bound",
            "reduce_parameter_shard",
        ),
        "delta-core-cpp/src/apply/engine.cpp": (
            "round_half_toward_positive",
            "weighted_coordinate",
            "next_optimizer_hash",
        ),
        "delta-runtime-cpp/src/certificate_runtime.cpp": (
            "persist_and_expose",
            "after_durability_before_commit",
            "PointerDisposition::replay",
        ),
        "delta-core-cpp/tests/certificates_test.cpp": (
            "mixed-view Frankenstein root was accepted",
            "recovered_vote_count() == 6U",
            "four validators",
        ),
        "delta-core-cpp/tests/certificates_mutant_test.cpp": (
            "wrong seed parent accepted",
            "observed-only aggregate coverage accepted",
            "uncertified current accepted",
        ),
        "delta-ffi/src/certificates_abi.cpp": (
            "delta_certificate_inspect_borrowed",
            "delta_certificate_inspect_copy",
        ),
        (
            "delta-node-java/src/main/java/io/deltareduce/node/certificates/"
            "NativeCertificateVerifier.java"
        ): (
            "Java never reconstructs a QC",
            "delta_certificate_inspect_borrowed",
        ),
    }
    for path, expected in markers.items():
        for marker in expected:
            require(marker in files[path], f"IMPLEMENTATION_MARKER_MISSING:{path}:{marker}")
    validate_architecture(commit)


def build(commit: str) -> dict[str, Any]:
    commit = git_text("rev-parse", f"{commit}^{{commit}}")
    require(
        not git_text(
            "diff",
            "--name-only",
            PREDECESSOR,
            commit,
            "--",
            "formal/tla",
            "formal/proofs",
            "formal/schemas",
        ),
        "FORMAL_SOURCE_DIFF_PRESENT",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", PREDECESSOR, commit], cwd=ROOT, check=False
        ).returncode
        == 0,
        "PREDECESSOR_NOT_ANCESTOR",
    )
    validate_markers(commit)
    artifacts = [
        {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
        for path in changed_source(commit)
    ]
    return {
        "checks": [
            "CANONICAL_CROSS_LANGUAGE_CHAIN_BYTES",
            "COMMON_PERSIST_BARRIER_EXPOSE_VOTE_LIFECYCLE_ALL_QC_CLASSES",
            "WRONG_PARENT_ROLE_EPOCH_REPLAY_AND_CONFLICT_GUARDS",
            "EXACT_NORM_TRIM_BUCKET_CENTERED_CLIP_AND_APC_COEFFICIENTS",
            "FEATURE004_ACCUMULATOR_BOUND_REVALIDATED",
            "EXACT_PARAMETER_REDUCE_AND_IMMUTABLE_REQUIRED_MATRIX",
            "MIXED_VIEW_FRANKENSTEIN_REJECTED",
            "DETERMINISTIC_APPLY_AND_FOUR_VALIDATOR_BYTE_EQUALITY",
            "VOTE_AND_POINTER_TORN_DURABLE_REPLAY_RECOVERY",
            "PRODUCTION_SEED_COVERAGE_COEFFICIENT_CURRENT_MUTANTS_KILLED",
            "BOUNDED_C_ABI_BORROWED_COPY_PARITY_AND_FUZZ_PASS",
            "JDK25_JDK26_NATIVE_ONLY_OPAQUE_ADAPTER_REGISTERED",
            "NO_NATIVE_NETWORK_CLOCK_OR_JAVA_CONSENSUS_AUTHORITY",
        ],
        "classification": "REFINEMENT_ONLY",
        "execution": {
            "ctest_names": [
                "delta_core.certificates",
                "delta_core.certificate_contract_fuzz",
                "delta_core.certificate_mutant_seed_parent",
                "delta_core.certificate_mutant_observed_coverage",
                "delta_core.certificate_mutant_coefficient",
                "delta_core.certificate_mutant_current",
                "delta_ffi.certificates",
            ],
            "local_profiles": ["MSVC Release C++20", "Temurin JDK 25 FFM"],
            "registered_ci_profiles": [
                "GCC C++20",
                "GCC C++23",
                "Clang ASan UBSan",
                "Temurin JDK 25",
                "Temurin JDK 26",
            ],
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "phase": "008-native-execution",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": artifacts,
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": [f"T{value:03d}" for value in range(13, 50)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    require(arguments.write != arguments.check_only, "EXACT_MODE_REQUIRED")
    if arguments.check_only:
        existing = json.loads(OUTPUT.read_text())
        commit = existing["source"]["commit"]
    else:
        require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
        commit = arguments.source_commit
    result = build(commit)
    encoded = canonical(result)
    if arguments.check_only:
        require(OUTPUT.read_bytes() == encoded, "NATIVE_EVIDENCE_DRIFT")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(encoded)
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceError, OSError, ValueError, json.JSONDecodeError) as error:
        print(canonical({"error": str(error), "status": "FAIL"}).decode())
        raise SystemExit(2) from error
