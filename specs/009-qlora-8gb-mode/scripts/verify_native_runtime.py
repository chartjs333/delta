"""Generate exact-source C++/C ABI evidence for feature 009."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/009-qlora-8gb-mode/evidence/native-runtime.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FILES: Final = (
    "CMakeLists.txt",
    "delta-core-cpp/include/delta/qlora/adapter_apply.hpp",
    "delta-core-cpp/include/delta/qlora/context.hpp",
    "delta-core-cpp/src/qlora/adapter_apply.cpp",
    "delta-core-cpp/src/qlora/context.cpp",
    "delta-core-cpp/tests/qlora_apply_test.cpp",
    "delta-core-cpp/tests/qlora_certificate_chain_test.cpp",
    "delta-ffi/include/delta_abi.h",
    "delta-ffi/src/qlora_abi.cpp",
    "delta-ffi/tests/qlora_abi_test.cpp",
    "specs/009-qlora-8gb-mode/scripts/verify_native_runtime.py",
)
TARGETS: Final = (
    "delta_qlora_certificate_chain_test",
    "delta_qlora_apply_test",
    "delta_ffi_qlora_test",
)


def run(*args: str) -> str:
    return subprocess.run(
        args, cwd=ROOT, check=True, capture_output=True, encoding="utf-8", errors="replace"
    ).stdout.strip()


def source_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def exercise_native() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for preset in ("cpp20", "cpp23"):
        run("cmake", "--preset", preset)
        run("cmake", "--build", "--preset", preset, "--target", *TARGETS, "--parallel", "4")
        output = run("ctest", "--preset", preset, "-R", "qlora", "--output-on-failure")
        if "100% tests passed" not in output or "3/3" not in output:
            raise RuntimeError(f"NATIVE_QLORA_TESTS_FAILED:{preset}")
        results.append(
            {
                "compiler_contract": "/W4 /WX /permissive- /fp:strict",
                "preset": preset,
                "summary": "3/3 passed",
            }
        )
    return results


def build(commit: str) -> dict[str, object]:
    formal_diff = run(
        "git",
        "diff",
        "--name-only",
        "origin/main..." + commit,
        "--",
        "formal",
        "specs/000-formal-tla-spec",
    ).splitlines()
    if formal_diff:
        raise RuntimeError("FORMAL_SOURCE_DIFF")
    tests = exercise_native()
    return {
        "checks": [
            "EXISTING_CERTIFICATE_GRAPH_BOUND_BY_QLORA_ROUND_CONFIG",
            "NO_PARALLEL_QLORA_QC_TYPES",
            "EXISTING_ROBUST_NORM_BUCKET_CLIP_ON_ADAPTER_Q",
            "IMMUTABLE_DOMAIN_PARAMETER_REQUIRED_MATRIX",
            "DIRECT_FIXEDPOINT_ADAPTER_REDUCE_EQUALITY",
            "BASE_INJECTION_AND_COVERAGE_MUTATIONS_REJECTED",
            "ADAPTER_ONLY_OUTER_APPLY",
            "FOUR_VALIDATOR_BYTE_HASH_EFFECT_EQUALITY",
            "EXISTING_APPLY_QC_WAL_CAS_REPLAY",
            "BOUNDED_C_ABI_PARITY",
            "CXX20_AND_CXX23_STRICT_BUILD",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": [
                {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
                for path in FILES
            ],
            "commit": commit,
            "tree": run("git", "show", "-s", "--format=%T", commit),
        },
        "status": "PASS",
        "task_ids": [
            *[f"T{index:03d}" for index in range(21, 32)],
            "HR009-005",
            "HR009-006",
            "HR009-008",
            "HR009-009",
        ],
        "tests": tests,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.check_only:
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expected = build(str(report["source"]["commit"]))
        if report != expected:
            raise RuntimeError("NATIVE_RUNTIME_EVIDENCE_MISMATCH")
    else:
        if run("git", "status", "--porcelain"):
            raise RuntimeError("SOURCE_TREE_NOT_CLEAN")
        report = build(run("git", "rev-parse", "HEAD"))
        OUTPUT.write_text(
            json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
