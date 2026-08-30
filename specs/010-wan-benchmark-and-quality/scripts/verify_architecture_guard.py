"""Prove Feature 010 cannot mutate protocol authority or formal semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/architecture-guard.json"
BASE: Final = "007eb08aa3aaee849128ba428274a9fbda561bf8"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"

ALLOWED_PREFIXES: Final = (
    ".github/workflows/benchmark.yml",
    "configs/benchmark/",
    "delta-ffi/include/delta_benchmark_abi.h",
    "delta-ffi/src/benchmark_abi.cpp",
    "delta-ffi/tests/benchmark_abi_test.cpp",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/",
    "delta-node-java/src/test/java/io/deltareduce/node/benchmark/",
    "delta-protocol/fixtures/010/",
    "delta-protocol/schemas/010/",
    "delta-runtime-cpp/include/delta/runtime/benchmark.hpp",
    "delta-runtime-cpp/src/benchmark/",
    "delta-runtime-cpp/tests/benchmark_test.cpp",
    "delta-worker-python/src/deltatorrent/benchmark/",
    "delta-worker-python/tests/benchmark/",
    "docs/benchmark-operations.md",
    "reports/benchmark/",
    "specs/010-wan-benchmark-and-quality/",
)
ALLOWED_EXACT: Final = {
    "CMakeLists.txt",
    "Makefile",
    "delta-core-cpp/tests/certificates_test.cpp",
    "delta-protocol/registry.json",
    "delta-worker-python/src/deltatorrent/cli/benchmark.py",
    "delta-worker-python/src/deltatorrent/cli/main.py",
}
FORBIDDEN_PREFIXES: Final = (
    "formal/tla/",
    "formal/proofs/",
    "formal/schemas/",
    "delta-core-cpp/src/",
    "delta-runtime-cpp/src/certificate_runtime.cpp",
    "delta-runtime-cpp/src/runtime.cpp",
    "delta-runtime-cpp/src/wal.cpp",
)
FORBIDDEN_TEXT: Final = {
    "ADAPTIVE_H": re.compile(r"(?i)\badaptive[_ -]?h(?:_i)?\b"),
    "FLOAT_CONSENSUS": re.compile(r"(?i)\b(?:fp16|fp32|fp64|float)\b.{0,40}\bconsensus\b"),
    "MANUAL_GO_OVERRIDE": re.compile(r"(?i)\bmanual[_ -]?(?:go[_ -]?)?override\b"),
    "PICKLE": re.compile(r"(?m)^\s*(?:import pickle|from pickle import)\b"),
    "PROTOCOL_CURRENT_TRUE": re.compile(r'"protocol_current_transition"\s*:\s*true'),
    "THRESHOLD_OVERRIDE": re.compile(r"(?i)\bthreshold[_ -]?override\b"),
}


class ArchitectureGuardError(RuntimeError):
    """Stable architecture-guard failure."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ArchitectureGuardError(f"{code}:{detail}" if detail else code)


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(("git", *arguments), cwd=ROOT, capture_output=True, check=False)
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.decode(errors="replace"))
    return process.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def tracked_bytes(commit: str, path: str) -> bytes:
    require(not Path(path).is_absolute() and ".." not in Path(path).parts, "PATH_INVALID", path)
    return git_bytes("show", f"{commit}:{path}")


def tracked_json(commit: str, path: str) -> dict[str, object]:
    value = json.loads(tracked_bytes(commit, path))
    require(isinstance(value, dict), "JSON_OBJECT_REQUIRED", path)
    return value


def allowed_path(path: str) -> bool:
    return path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)


def scan_text(text: str) -> tuple[str, ...]:
    return tuple(sorted(code for code, pattern in FORBIDDEN_TEXT.items() if pattern.search(text)))


def registry_projection(registry: dict[str, object]) -> dict[str, object]:
    def retained(name: str) -> list[object]:
        values = registry.get(name)
        require(isinstance(values, list), "REGISTRY_COLLECTION_INVALID", name)
        return [
            item
            for item in values
            if isinstance(item, dict)
            and "/010/" not in str(item.get("path", ""))
            and not str(item.get("id", "")).startswith(("BENCHMARK010-", "MEDIA-BENCHMARK"))
            and not (name == "media_types" and "-010-" in str(item.get("schema_id", "")))
        ]

    return {
        "action_registry": registry.get("action_registry"),
        "fixtures": retained("fixtures"),
        "formal_semantics_id": registry.get("formal_semantics_id"),
        "media_types": retained("media_types"),
        "schemas": retained("schemas"),
    }


def verify(commit: str) -> dict[str, object]:
    process = subprocess.run(
        ("git", "merge-base", "--is-ancestor", BASE, commit), cwd=ROOT, check=False
    )
    require(process.returncode == 0, "BASE_NOT_ANCESTOR")
    paths = tuple(git_text("diff", "--name-only", BASE, commit).splitlines())
    unexpected = tuple(path for path in paths if not allowed_path(path))
    require(not unexpected, "UNEXPECTED_SOURCE_PATH", ",".join(unexpected))
    forbidden_paths = tuple(path for path in paths if path.startswith(FORBIDDEN_PREFIXES))
    require(not forbidden_paths, "PROTOCOL_AUTHORITY_SOURCE_CHANGED", ",".join(forbidden_paths))

    before = tracked_json(BASE, "delta-protocol/registry.json")
    after = tracked_json(commit, "delta-protocol/registry.json")
    require(before.get("formal_semantics_id") == FORMAL_ID, "BASE_FORMAL_ID_DRIFT")
    require(after.get("formal_semantics_id") == FORMAL_ID, "SOURCE_FORMAL_ID_DRIFT")
    require(
        registry_projection(before) == registry_projection(after), "NON_BENCHMARK_REGISTRY_DRIFT"
    )

    result_qc = tracked_json(commit, "delta-protocol/schemas/010/benchmark-result-qc-v1.json")
    qc_properties = result_qc.get("properties")
    require(isinstance(qc_properties, dict), "RESULT_QC_SCHEMA_INVALID")
    require(
        qc_properties.get("governance_only") == {"const": True}
        and qc_properties.get("protocol_current_transition") == {"const": False},
        "RESULT_QC_PROTOCOL_BOUNDARY_INVALID",
    )

    text_paths = tuple(
        path
        for path in paths
        if path.endswith((".cpp", ".h", ".java", ".json", ".md", ".py", ".yml"))
        and path.startswith(
            (
                "configs/benchmark/",
                "delta-ffi/include/delta_benchmark_abi.h",
                "delta-ffi/src/benchmark_abi.cpp",
                "delta-node-java/src/main/java/io/deltareduce/node/benchmark/",
                "delta-protocol/schemas/010/",
                "delta-runtime-cpp/src/benchmark/",
                "delta-worker-python/src/deltatorrent/benchmark/",
                "delta-worker-python/src/deltatorrent/cli/benchmark.py",
            )
        )
    )
    findings: dict[str, tuple[str, ...]] = {}
    for path in text_paths:
        detected = scan_text(tracked_bytes(commit, path).decode(errors="replace"))
        if detected:
            findings[path] = detected
    require(not findings, "FORBIDDEN_BENCHMARK_SEMANTICS", json.dumps(findings, sort_keys=True))

    source_artifacts = [
        {
            "path": path,
            "sha256": hashlib.sha256(tracked_bytes(commit, path)).hexdigest(),
        }
        for path in sorted(paths)
    ]
    return {
        "checks": [
            "NO_FORMAL_SOURCE_DIFF",
            "NO_PROTOCOL_AUTHORITY_IMPLEMENTATION_DIFF",
            "NO_NON_BENCHMARK_REGISTRY_DRIFT",
            "GOVERNANCE_QC_CANNOT_CHANGE_CURRENT",
            "NO_FORBIDDEN_BENCHMARK_SEMANTICS",
        ],
        "classification": "REGRESSION_ONLY",
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": source_artifacts,
            "commit": commit,
            "tree": git_text("show", "-s", "--format=%T", commit),
        },
        "status": "PASS",
        "task_ids": ["T053"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.check_only:
            recorded = json.loads(OUTPUT.read_text(encoding="utf-8"))
            commit = recorded.get("source", {}).get("commit")
            require(isinstance(commit, str), "ARCHITECTURE_EVIDENCE_SOURCE_INVALID")
            result = verify(commit)
            require(recorded == result, "ARCHITECTURE_EVIDENCE_STALE")
        else:
            require(not git_text("status", "--porcelain"), "SOURCE_TREE_NOT_CLEAN")
            result = verify(git_text("rev-parse", "HEAD"))
            OUTPUT.write_text(
                json.dumps(result, separators=(",", ":"), sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 0
    except (ArchitectureGuardError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error_code": str(error), "status": "FAIL"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
