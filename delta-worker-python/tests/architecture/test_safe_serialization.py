from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "delta-worker-python" / "src"
BANNED_MODULES = {"cloudpickle", "dill", "joblib", "pickle"}


def test_runtime_source_has_no_unsafe_deserializer_import() -> None:
    violations: list[str] = []
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = {alias.name.split(".", maxsplit=1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = {node.module.split(".", maxsplit=1)[0]}
            else:
                modules = set()
            for module in modules & BANNED_MODULES:
                violations.append(f"{path.relative_to(ROOT).as_posix()}:{module}")
    assert violations == []


def test_runtime_source_has_no_framework_pickle_load() -> None:
    violations: list[str] = []
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id == "torch" and node.func.attr == "load":
                violations.append(path.relative_to(ROOT).as_posix())
    assert violations == []
