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
            "sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d"
        ),
        "fixedpoint_config_id": (
            "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629"
        ),
        "manifest_id": "sha256:6b24994dde9f03ccde6acb42abb080ec9dcc2e111a81d781948a3ac1d10446ec",
        "profile_id": "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
        "proof_instance_id": (
            "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076"
        ),
        "q_values": 36,
        "scale_table_id": "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
        "shard_plan_id": "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
        "shards": 5,
    }
