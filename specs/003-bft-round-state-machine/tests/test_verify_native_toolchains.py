"""Regression tests for frozen feature-003 toolchain locks."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_native_toolchains.py"
SPEC = importlib.util.spec_from_file_location("verify_feature003_toolchains", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_toolchain_locks_define_exact_native_matrix() -> None:
    result = MODULE.verify("HEAD")

    assert result["status"] == "PASS"
    assert result["compilers"]["families"] == ["clang", "gcc"]
    assert result["compilers"]["modes"] == ["c++20", "c++23"]
    assert [item["feature"] for item in result["jdks"]] == [25, 26]
    assert result["dependency_count"] == 0


def test_every_download_artifact_requires_hash_size_and_license() -> None:
    valid = {
        "archive_url": "https://github.com/example/project/releases/download/v1/a.tar.gz",
        "archive_sha256": "a" * 64,
        "archive_size_bytes": 1,
        "license": "Apache-2.0",
    }

    MODULE.validate_artifact(valid, "fixture")
