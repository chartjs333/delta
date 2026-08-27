"""Regression tests for the feature-003 pure-core architecture gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_core_architecture.py"
SPEC = importlib.util.spec_from_file_location("verify_feature003_core_architecture", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_worktree_core_has_no_architecture_findings() -> None:
    result = MODULE.verify(None, "HEAD")

    assert result["status"] == "PASS"
    assert result["finding_count"] == 0
    assert result["pure_core_source_count"] >= 4
    assert "filesystem" not in result["standard_headers"]
    assert "unordered_map" not in result["standard_headers"]


def test_forbidden_patterns_cover_runtime_and_nondeterminism() -> None:
    examples = {
        "SOCKET_OR_NETWORK": "#include <sys/socket.h>",
        "FILESYSTEM_OR_FILE_IO": "#include <filesystem>",
        "WALL_CLOCK": "auto now = std::chrono::system_clock::now();",
        "THREADING": "#include <thread>",
        "JVM": "#include <jni.h>",
        "PYTHON": "#include <Python.h>",
        "NONDETERMINISTIC_RANDOM": "std::random_device source;",
        "FLOATING_POINT": "double accumulator = 0;",
        "UNORDERED_ITERATION": "std::unordered_map<Key, Value> values;",
        "RAW_LAYOUT_SERIALIZATION": "reinterpret_cast<const char*>(value);",
        "PROCESS_ENVIRONMENT": 'getenv("DELTA");',
        "LOCALE_DEPENDENCE": "std::locale::global(value);",
    }

    for identifier, example in examples.items():
        findings = MODULE.scan_text("fixture.cpp", example)
        assert {item["id"] for item in findings} == {identifier}


def test_fast_math_and_dependency_fetch_are_rejected() -> None:
    assert MODULE.CMAKE_FORBIDDEN_PATTERNS["FAST_MATH"].search("-ffast-math")
    assert not MODULE.CMAKE_FORBIDDEN_PATTERNS["FAST_MATH"].search("-fno-fast-math")
    assert MODULE.CMAKE_FORBIDDEN_PATTERNS["THIRD_PARTY_FETCH"].search(
        "FetchContent_Declare(example)"
    )
