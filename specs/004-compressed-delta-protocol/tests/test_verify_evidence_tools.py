from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "specs" / "004-compressed-delta-protocol" / "scripts"
EVIDENCE = ROOT / "specs" / "004-compressed-delta-protocol" / "evidence"


def load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_final_task_parser_is_exact() -> None:
    final = load("verify_final_compatibility")
    semantic = "- [x] T001 valid\n- [ ] T002 open\n- [x] T003 valid\n"
    runtime = "- [x] **HR004-001** valid\n- [ ] **HR004-002** open\n"
    assert final.task_ids(semantic, "T") == {"T001", "T003"}
    assert final.task_ids(runtime, "HR004-") == {"HR004-001"}


def test_native_evidence_fails_closed() -> None:
    native = load("verify_native_execution")
    with pytest.raises(native.NativeExecutionError, match="SCHEMA_VERSION_INVALID"):
        native.verify({})


def test_materializer_has_all_phase_outputs() -> None:
    materializer = load("materialize_phase_evidence")
    assert set(materializer.OUTPUTS) == {
        "direct-q-refinement.json",
        "native-architecture.json",
        "proof-instances.json",
        "protocol-contracts-final.json",
    }


def test_published_final_evidence_when_present() -> None:
    report = EVIDENCE / "final-compatibility.json"
    if not report.is_file():
        return
    for name in (
        "verify_phase_evidence.py",
        "verify_native_execution.py",
        "verify_final_compatibility.py",
    ):
        process = subprocess.run(
            [sys.executable, str(SCRIPTS / name), "--check-only"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert process.returncode == 0, process.stdout + process.stderr
