from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "delta-protocol"
WORKER_SOURCE = ROOT / "delta-worker-python" / "src"
PLACEHOLDERS = (
    "delta-core-cpp",
    "delta-runtime-cpp",
    "delta-ffi",
    "delta-node-java",
)
FORBIDDEN_IMPORT_PREFIXES = (
    "delta_core_cpp",
    "delta_runtime_cpp",
    "delta_ffi",
    "delta_node_java",
    "netty",
)


def test_protocol_is_data_only() -> None:
    unexpected = [
        path.relative_to(ROOT).as_posix()
        for path in PROTOCOL.rglob("*")
        if path.is_file() and path.suffix not in {".json", ".md"}
    ]
    assert unexpected == []


def test_worker_does_not_import_native_or_jvm_components() -> None:
    violations: list[str] = []
    for path in WORKER_SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(f"{path.relative_to(ROOT).as_posix()}:{name}")
    assert violations == []


def test_native_and_jvm_components_are_documentation_only() -> None:
    for directory in PLACEHOLDERS:
        files = sorted(
            path.relative_to(ROOT / directory).as_posix()
            for path in (ROOT / directory).rglob("*")
            if path.is_file()
        )
        assert files == ["README.md"]
