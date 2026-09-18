"""Generate exact-source polyglot benchmark-runtime evidence for feature 010."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/runtime-adapters.json"
GOLDEN: Final = ROOT / "delta-protocol/fixtures/010/cross-language/golden-v1.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
TARGETS: Final = (
    "delta_benchmark_sidecar",
    "delta_runtime_benchmark_test",
    "delta_ffi_benchmark_test",
)
FILES: Final = (
    "CMakeLists.txt",
    "delta-runtime-cpp/include/delta/runtime/benchmark.hpp",
    "delta-runtime-cpp/src/benchmark/fault_control.cpp",
    "delta-runtime-cpp/src/benchmark/metrics.cpp",
    "delta-runtime-cpp/src/benchmark/sidecar_main.cpp",
    "delta-runtime-cpp/src/benchmark/sidecar_server.cpp",
    "delta-runtime-cpp/src/benchmark/trace_export.cpp",
    "delta-runtime-cpp/tests/benchmark_test.cpp",
    "delta-ffi/include/delta_benchmark_abi.h",
    "delta-ffi/src/benchmark_abi.cpp",
    "delta-ffi/tests/benchmark_abi_test.cpp",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkContracts.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkTransport.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/EmbeddedFfmRunner.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NettyMetricsCollector.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NetworkFaultController.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/ProcessProfileRunner.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/RuntimeIdentityCollector.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/SidecarRunner.java",
    "delta-node-java/src/test/java/io/deltareduce/node/benchmark/BenchmarkConformance.java",
    "delta-node-java/src/test/java/io/deltareduce/node/benchmark/BenchmarkFfmConformance.java",
    "delta-protocol/fixtures/010/cross-language/golden-v1.json",
    "specs/010-wan-benchmark-and-quality/scripts/verify_runtime_adapters.py",
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def execute(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def run(*args: str) -> str:
    return execute(*args).stdout.strip()


def source_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def content_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def golden_hash_aggregate() -> tuple[int, str]:
    document = json.loads(GOLDEN.read_text(encoding="utf-8"))
    artifacts = document.get("artifacts")
    require(isinstance(artifacts, dict) and len(artifacts) >= 14, "GOLDEN_ARTIFACTS_MISSING")
    hashes: list[str] = []
    for wrapper in artifacts.values():
        require(isinstance(wrapper, dict), "GOLDEN_WRAPPER_INVALID")
        bytes_hex = wrapper.get("bytes_hex")
        require(isinstance(bytes_hex, str), "GOLDEN_BYTES_MISSING")
        value = bytes.fromhex(bytes_hex)
        hashes.append("sha256:" + hashlib.sha256(value).hexdigest())
    aggregate = hashlib.sha256("\n".join(hashes).encode("ascii")).hexdigest()
    return len(hashes), "sha256:" + aggregate


def sidecar_path(preset: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    candidates = sorted((ROOT / "out/build" / preset).rglob("delta_benchmark_sidecar" + suffix))
    require(len(candidates) == 1, f"SIDECAR_BINARY_COUNT:{preset}:{len(candidates)}")
    return candidates[0]


def exercise_native() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for preset in ("cpp20", "cpp23"):
        run("cmake", "--preset", preset)
        run("cmake", "--build", "--preset", preset, "--target", *TARGETS, "--parallel", "4")
        output = run(
            "ctest",
            "--preset",
            preset,
            "-R",
            "delta_(runtime|ffi)\\.benchmark",
            "--output-on-failure",
        )
        require("100% tests passed" in output and "2/2" in output, f"NATIVE_TESTS_FAILED:{preset}")
        require(sidecar_path(preset).is_file(), f"SIDECAR_BINARY_MISSING:{preset}")
        results.append({"preset": preset, "summary": "2/2 passed"})
    return results


def java_sources() -> list[str]:
    main = ROOT / "delta-node-java/src/main/java/io/deltareduce/node/benchmark"
    test = ROOT / "delta-node-java/src/test/java/io/deltareduce/node/benchmark"
    return [
        str(path) for path in sorted((*main.glob("*.java"), test / "BenchmarkConformance.java"))
    ]


def exercise_java(expected_count: int, expected_hash: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="delta-benchmark-010-") as directory:
        temporary = Path(directory)
        classes = temporary / "classes"
        classes.mkdir()
        run(
            "javac", "--release", "17", "-Xlint:all", "-Werror", "-d", str(classes), *java_sources()
        )
        for preset in ("cpp20", "cpp23"):
            journal = temporary / f"{preset}-journal.txt"
            output = run(
                "java",
                "-ea",
                "-cp",
                str(classes),
                "io.deltareduce.node.benchmark.BenchmarkConformance",
                str(sidecar_path(preset)),
                str(journal),
                str(GOLDEN),
            )
            match = re.search(r"^CROSS_LANGUAGE (\d+) (sha256:[0-9a-f]{64})$", output, re.MULTILINE)
            require(match is not None, f"JAVA_GOLDEN_OUTPUT_MISSING:{preset}")
            require(int(match.group(1)) == expected_count, f"JAVA_GOLDEN_COUNT:{preset}")
            require(match.group(2) == expected_hash, f"JAVA_GOLDEN_HASH:{preset}")
            results.append(
                {
                    "golden_aggregate": expected_hash,
                    "preset": preset,
                    "summary": f"{expected_count} exact artifacts; crash/restart replay passed",
                }
            )
    return results


def exercise_python() -> dict[str, str]:
    contracts = run(
        "python",
        "specs/010-wan-benchmark-and-quality/scripts/benchmark_contracts.py",
    )
    contract_result = json.loads(contracts)
    require(contract_result.get("status") == "PASS", "CONTRACT_GENERATOR_FAILED")
    require(contract_result.get("invalid_case_count") == 10, "NEGATIVE_CORPUS_INCOMPLETE")
    tests = run(
        "uv",
        "run",
        "pytest",
        "-q",
        "delta-worker-python/tests/benchmark/test_profiles.py",
        "delta-worker-python/tests/benchmark/test_vertical_slice.py",
    )
    require("14 passed" in tests, "PYTHON_PROFILE_TESTS_FAILED")
    return {"negative_cases": "10/10 rejected", "summary": "14/14 passed"}


def capture_environment() -> dict[str, str]:
    cmake = run("cmake", "--version").splitlines()[0]
    javac = execute("javac", "-version")
    javac_version = (javac.stdout or javac.stderr).strip()
    return {
        "cmake": cmake,
        "host": platform.platform(),
        "java_compiler": javac_version,
        "python": platform.python_version(),
    }


def validate_recorded_environment(value: object) -> dict[str, str]:
    require(isinstance(value, dict), "RECORDED_ENVIRONMENT_MISSING")
    expected_keys = {"cmake", "host", "java_compiler", "python"}
    require(set(value) == expected_keys, "RECORDED_ENVIRONMENT_FIELDS")
    require(
        all(isinstance(item, str) and item for item in value.values()),
        "RECORDED_ENVIRONMENT_INVALID",
    )
    return {str(key): str(item) for key, item in value.items()}


def build(commit: str, environment: dict[str, str] | None = None) -> dict[str, object]:
    formal_diff = run(
        "git",
        "diff",
        "--name-only",
        "origin/main..." + commit,
        "--",
        "formal",
        "specs/000-formal-tla-spec",
    ).splitlines()
    require(not formal_diff, "FORMAL_SOURCE_DIFF")
    count, aggregate = golden_hash_aggregate()
    native = exercise_native()
    java = exercise_java(count, aggregate)
    python = exercise_python()
    return {
        "checks": [
            "CXX20_AND_CXX23_STRICT_BUILD",
            "BOUNDED_BENCHMARK_C_ABI",
            "DETERMINISTIC_UNPRIVILEGED_FAULT_PROFILES",
            "PYTHON_JAVA_CPP_GOLDEN_BYTES_AND_HASHES",
            "TEN_NEGATIVE_CONTRACT_CASES_REJECTED",
            "EMBEDDED_AND_REAL_SIDECAR_PATHS_SEPARATED",
            "CHILD_PROCESS_CRASH_CONTAINED",
            "PERSISTENT_REPLAY_EXACT_AFTER_RESTART",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REGRESSION_ONLY",
        "environment": environment if environment is not None else capture_environment(),
        "formal_semantics_id": FORMAL_ID,
        "golden": {"artifact_count": count, "raw_sha256_aggregate": aggregate},
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
        "task_ids": ["T018", "HR010-004", "HR010-012"],
        "tests": {"java_sidecar": java, "native": native, "python": python},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.check_only:
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        environment = validate_recorded_environment(report.get("environment"))
        expected = build(str(report["source"]["commit"]), environment)
        require(report == expected, "RUNTIME_ADAPTER_EVIDENCE_MISMATCH")
    else:
        require(not run("git", "status", "--porcelain"), "SOURCE_TREE_NOT_CLEAN")
        report = build(run("git", "rev-parse", "HEAD"))
        OUTPUT.write_text(
            json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
