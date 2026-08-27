from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT / "specs" / "004-compressed-delta-protocol" / "scripts" / "verify_protocol_contracts.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("verify_protocol_contracts", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_feature004_contracts_pass() -> None:
    result = _module().verify_all()  # type: ignore[attr-defined]
    assert result["status"] == "PASS"
    assert result["classification"] == "REFINEMENT_ONLY"
    assert result["semantic_completeness_claimed"] is False
    assert result["tasks"] == [f"T{task:03d}" for task in range(5, 13)]


def test_cross_language_identity_is_frozen() -> None:
    result = _module().verify_all()  # type: ignore[attr-defined]
    assert result["golden"] == {
        "commitment_root": (
            "sha256:bbcb9d6e94668eacc8c3f947832b3a0744b1ee65011b6dbee4b02e4619867787"
        ),
        "manifest_id": "sha256:cd1301e234e977079ca84a248b56db8f4560e822342bb9fc9ee420893d1f6c46",
        "profile_id": "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
        "proof_instance_id": (
            "sha256:e09098577825d3a71a4c03c1e5a12d14c3c5646234aae0d37c85e7ec1d3b5793"
        ),
        "q_values": 36,
        "scale_table_id": "sha256:e7409ed79e33407b2df867ab00d1c07fe7ddd6d52049150c34bcc76abe4c9b32",
        "shard_plan_id": "sha256:8d0ab224574404d8100c93e8d91d657b4b646ac77bd039bb4098b44ffc4a665b",
        "shards": 5,
    }
