from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs" / "004-compressed-delta-protocol" / "scripts" / "verify_proof_instances.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("verify_proof_instances", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_concrete_proof_gate_passes() -> None:
    result = _module().verify()  # type: ignore[attr-defined]
    assert result["status"] == "PASS"
    assert result["first_unsafe_int64"]["status"] == "REJECT"
    assert result["semantic_completeness_claimed"] is False
    assert result["tasks"] == ["T031", "T032", "T033", "T034", "T035"]


def test_all_normative_bindings_invalidate_identity() -> None:
    result = _module().verify()  # type: ignore[attr-defined]
    assert set(result["mutation_invalidation"]) == {
        "coefficient",
        "count",
        "formal-semantics",
        "parameter-schema",
        "profile",
        "scale",
        "schema-version",
        "shard-coverage",
        "theorem-map",
    }
