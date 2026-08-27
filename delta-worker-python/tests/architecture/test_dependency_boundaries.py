from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "delta-protocol"
WORKER_SOURCE = ROOT / "delta-worker-python" / "src"
COMPONENT_FORBIDDEN_SUFFIXES = {
    "delta-core-cpp": {".class", ".jar", ".java", ".py"},
    "delta-runtime-cpp": {".class", ".jar", ".java", ".py"},
    "delta-ffi": {".class", ".jar", ".java", ".py"},
    "delta-node-java": {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".py"},
}
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


def test_native_and_jvm_components_preserve_language_ownership() -> None:
    violations: list[str] = []
    for directory, forbidden_suffixes in COMPONENT_FORBIDDEN_SUFFIXES.items():
        component = ROOT / directory
        assert (component / "README.md").is_file()
        violations.extend(
            path.relative_to(ROOT).as_posix()
            for path in component.rglob("*")
            if path.is_file() and path.suffix.lower() in forbidden_suffixes
        )
    assert violations == []
