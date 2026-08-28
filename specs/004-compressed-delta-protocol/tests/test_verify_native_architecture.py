from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT / "specs" / "004-compressed-delta-protocol" / "scripts" / "verify_native_architecture.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("verify_native_architecture", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_architecture_is_fail_closed() -> None:
    result = _module().verify()  # type: ignore[attr-defined]
    assert result["status"] == "PASS"
    assert result["finding_count"] == 0
    assert result["semantic_completeness_claimed"] is False
    assert result["tasks"] == ["T013", "T014", "T015", "T016"]
