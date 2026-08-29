from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs" / "009-qlora-8gb-mode" / "scripts" / "verify_protocol_contracts.py"
SPEC = importlib.util.spec_from_file_location("feature009_protocol_contracts", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_exact_preflight_is_revalidated() -> None:
    result = MODULE.verify_preflight("HEAD")

    assert result["status"] == "PASS"
    assert result["hardware_status"] == "IDENTIFIED_PROFILE_FROZEN"


def test_contract_outputs_and_negative_matrix_are_revalidated() -> None:
    result = MODULE.verify_contracts("HEAD")

    assert result == {
        "artifact_count": 11,
        "invalid_case_count": 7,
        "output_count": 17,
        "schema_count": 11,
        "status": "PASS",
    }


def test_contract_source_boundary_has_no_runtime_or_formal_source() -> None:
    result = MODULE.verify_source_boundary("HEAD")

    assert result["status"] == "PASS"
    assert result["runtime_source_count"] == 0
    assert result["formal_source_diff"] == []
