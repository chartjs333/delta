"""Verify the feature-003 pure C++ core boundary and emit deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
DEFAULT_OUTPUT = FEATURE / "evidence" / "core-architecture.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
CORE_ROOT = "delta-core-cpp"
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}

FORBIDDEN_PATTERNS = {
    "SOCKET_OR_NETWORK": re.compile(
        r"#\s*include\s*[<\"](?:sys/socket|winsock2?|asio|boost/asio|netinet|arpa/inet)"
        r"|\bsocket\s*\(",
        re.IGNORECASE,
    ),
    "FILESYSTEM_OR_FILE_IO": re.compile(r"#\s*include\s*<filesystem>|std::filesystem|<fstream>"),
    "WALL_CLOCK": re.compile(r"<chrono>|system_clock|steady_clock|CLOCK_REALTIME|GetSystemTime"),
    "THREADING": re.compile(r"<(?:thread|mutex|atomic|condition_variable)>|std::(?:thread|mutex)"),
    "JVM": re.compile(r"jni\.h|JNIEnv|JavaVM"),
    "PYTHON": re.compile(r"Python\.h|pybind11|PyObject"),
    "NONDETERMINISTIC_RANDOM": re.compile(r"random_device|<(?:random)>"),
    "FLOATING_POINT": re.compile(r"\b(?:float|double|long\s+double)\b"),
    "UNORDERED_ITERATION": re.compile(r"unordered_(?:map|set)"),
    "RAW_LAYOUT_SERIALIZATION": re.compile(r"reinterpret_cast|\bmem(?:cpy|move|cmp)\s*\("),
    "PROCESS_ENVIRONMENT": re.compile(r"\b(?:getenv|system)\s*\("),
    "LOCALE_DEPENDENCE": re.compile(r"<locale>|std::locale|setlocale"),
}

CMAKE_FORBIDDEN_PATTERNS = {
    "FAST_MATH": re.compile(r"(?<!no-)fast-math|/fp:fast"),
    "THIRD_PARTY_FETCH": re.compile(r"FetchContent|ExternalProject|find_package\s*\("),
}

REQUIRED_CMAKE_FRAGMENTS = (
    "add_library(delta_core STATIC",
    "add_library(delta_runtime INTERFACE)",
    "add_library(delta_ffi INTERFACE)",
    "target_link_libraries(delta_runtime INTERFACE delta::core)",
    "target_link_libraries(delta_ffi INTERFACE delta::runtime)",
    "-fno-fast-math",
    "/fp:strict",
    "DELTA_CXX_STANDARD",
    "delta_core_canonical_test",
    "delta_core_protocol_test",
    "delta_runtime_target_test",
    "delta_ffi_target_test",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class ArchitectureError(RuntimeError):
    """Stable fail-closed pure-core architecture error."""


def reject(code: str, detail: str = "") -> None:
    raise ArchitectureError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        reject(
            "GIT_COMMAND_FAILED",
            completed.stderr.decode("utf-8", errors="replace").strip(),
        )
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def read_bytes(path: str, revision: str | None) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    if revision is None:
        return (ROOT / relative).read_bytes()
    return git_bytes("show", f"{revision}:{path}")


def source_paths(revision: str | None) -> list[str]:
    if revision is None:
        base = ROOT / CORE_ROOT
        return sorted(
            path.relative_to(ROOT).as_posix()
            for path in base.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SOURCE_SUFFIXES
            and "tests" not in path.relative_to(base).parts
        )
    paths = git_text("ls-tree", "-r", "--name-only", revision, "--", CORE_ROOT).splitlines()
    return sorted(
        path
        for path in paths
        if Path(path).suffix.lower() in SOURCE_SUFFIXES
        and "tests" not in Path(path).relative_to(CORE_ROOT).parts
    )


def scan_text(path: str, text: str) -> list[dict[str, str]]:
    findings = []
    for identifier, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            findings.append({"id": identifier, "path": path})
    return findings


def verify_cmake(revision: str | None) -> list[dict[str, str]]:
    text = read_bytes("CMakeLists.txt", revision).decode("utf-8")
    findings: list[dict[str, str]] = []
    for fragment in REQUIRED_CMAKE_FRAGMENTS:
        if fragment not in text:
            findings.append({"id": "CMAKE_TARGET_CONTRACT_MISSING", "path": fragment})
    for identifier, pattern in CMAKE_FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            findings.append({"id": identifier, "path": "CMakeLists.txt"})
    return findings


def verify(content_revision: str | None, source_commit: str) -> dict[str, Any]:
    paths = source_paths(content_revision)
    require(paths, "PURE_CORE_SOURCE_SET_EMPTY")
    findings = verify_cmake(content_revision)
    standard_headers: set[str] = set()
    artifacts = []
    for path in paths:
        raw = read_bytes(path, content_revision)
        text = raw.decode("utf-8")
        findings.extend(scan_text(path, text))
        standard_headers.update(re.findall(r"#\s*include\s*<([^>]+)>", text))
        artifacts.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest()})
    for path in ("CMakeLists.txt", "CMakePresets.json"):
        raw = read_bytes(path, content_revision)
        artifacts.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest()})

    require(not findings, "PURE_CORE_ARCHITECTURE_FINDINGS", json.dumps(findings, sort_keys=True))
    return {
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "checks": [
            "ISOLATED_CMAKE_TARGETS",
            "STANDARD_LIBRARY_ONLY",
            "NO_SOCKET_OR_FILESYSTEM",
            "NO_WALL_CLOCK_OR_THREADS",
            "NO_JVM_OR_PYTHON",
            "NO_FLOATING_POINT_OR_FAST_MATH",
            "NO_UNORDERED_ITERATION",
            "NO_RAW_LAYOUT_SERIALIZATION",
        ],
        "errors": [],
        "finding_count": 0,
        "findings": [],
        "formal_impact": "NONE",
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "pure_core_source_count": len(paths),
        "rules": sorted([*FORBIDDEN_PATTERNS, *CMAKE_FORBIDDEN_PATTERNS]),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source_tree": {
            "commit": source_commit,
            "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
        },
        "standard_headers": sorted(standard_headers),
        "status": "PASS",
        "task_ids": ["T012", "T013", "HR003-003"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    try:
        if args.check_only:
            require(output.is_file(), "CORE_ARCHITECTURE_EVIDENCE_MISSING")
            existing = json.loads(output.read_text(encoding="utf-8"))
            source_commit = existing.get("source_tree", {}).get("commit")
            require(
                isinstance(source_commit, str)
                and re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
                "CORE_ARCHITECTURE_SOURCE_INVALID",
            )
            completed = subprocess.run(
                ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            require(completed.returncode == 0, "CORE_ARCHITECTURE_SOURCE_NOT_ANCESTOR")
            result = verify("HEAD", source_commit)
            encoded = canonical_json_bytes(result)
            require(output.read_bytes() == encoded, "CORE_ARCHITECTURE_EVIDENCE_STALE")
        else:
            require(
                not git_text("status", "--porcelain", "--untracked-files=all"),
                "SOURCE_TREE_NOT_CLEAN",
            )
            source_commit = git_text("rev-parse", "HEAD")
            result = verify("HEAD", source_commit)
            encoded = canonical_json_bytes(result)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (
        ArchitectureError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
