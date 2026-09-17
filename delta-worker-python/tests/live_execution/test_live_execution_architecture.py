"""C-WA-013, C-WA-027 .. C-WA-032: Architectural AST hygiene and security negative tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from deltatorrent.live_execution.errors import WorkerPreflightError
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "deltatorrent" / "live_execution"


def test_c_wa_013_ast_guard_forbids_eval_exec_shell_dynamic_import() -> None:
    """Static source inspection: no eval, exec, subprocess, os.system in live_execution."""
    forbidden_calls = {"eval", "exec", "system", "popen", "spawn"}
    forbidden_modules = {"subprocess", "shutil", "pty"}

    for py_file in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                    raise AssertionError(f"Forbidden call '{node.func.id}' found in {py_file}")
                if isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_calls:
                    raise AssertionError(f"Forbidden call '{node.func.attr}' found in {py_file}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_modules:
                        raise AssertionError(f"Forbidden import '{alias.name}' in {py_file}")
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in forbidden_modules:
                    raise AssertionError(f"Forbidden import from '{node.module}' in {py_file}")


def test_c_wa_030_local_stage_c_claim_strictly_forbidden() -> None:
    preflight = AuthorizedExecutionPreflight()
    bad_bundle = {
        "schema_version": "1.0.0",
        "intent": {
            "schema_version": "1.0.0",
            "intent_id": "11111111-1111-4111-8111-111111111111",
            "workload": {
                "model_plugin_id": "tabular-10gene-phenotype-v1",
                "dataset_id": "synthetic-10gene-cohort-v1",
                "requested_scope": "STAGE_C_REAL_DRQ1",
            },
        },
        "admission": {
            "schema_version": "1.0.0",
            "admission_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "intent_id": "11111111-1111-4111-8111-111111111111",
        },
    }
    with pytest.raises(WorkerPreflightError):
        preflight.validate(bad_bundle)
