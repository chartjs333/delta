from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT / "specs" / "004-compressed-delta-protocol" / "scripts" / "verify_direct_q_refinement.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("verify_direct_q_refinement", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_direct_q_refinement_gate_passes() -> None:
    result = _module().verify()  # type: ignore[attr-defined]
    assert result["status"] == "PASS"
    assert result["legal_trace"]["terminal_outcome"] == "APPLIED"
    assert "UNCHECKED_ARITHMETIC_ACCEPTED" in result["unsafe_trace"]["error"]
    assert result["tasks"] == ["T036", "T037", "T038", "T039", "T040"]
