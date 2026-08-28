from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "specs/005-content-addressed-p2p-distribution/scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_gate_passes() -> None:
    verifier = load("verify_protocol_contracts")
    assert verifier.verify()["status"] == "PASS"


def test_manifest_rejects_coverage_gap() -> None:
    generator = load("distribution_contracts")
    verifier = load("verify_protocol_contracts")
    payload = generator.source_bytes(2 * 1048576 + 17)
    golden = generator.golden_fixture()
    manifest = copy.deepcopy(golden["manifest"])
    manifest["value"]["pieces"][1]["offset"] += 1
    encoded = generator.canonical_json_bytes(manifest["value"])
    manifest["bytes_hex"] = encoded.hex()
    manifest["content_id"] = generator.domain_hash("deltareduce.005.object-manifest.v1", encoded)
    policy = golden["policy_registry"]["value"]["policies"][0]
    with pytest.raises(verifier.ContractError, match="PIECE_COVERAGE_INVALID"):
        verifier.validate_manifest(manifest, payload, golden["piece_profile"], policy)


def test_manifest_rejects_merkle_root_drift() -> None:
    generator = load("distribution_contracts")
    verifier = load("verify_protocol_contracts")
    payload = generator.source_bytes(2 * 1048576 + 17)
    golden = generator.golden_fixture()
    manifest = copy.deepcopy(golden["manifest"])
    manifest["value"]["piece_tree_root"] = "sha256:" + "f" * 64
    encoded = generator.canonical_json_bytes(manifest["value"])
    manifest["bytes_hex"] = encoded.hex()
    manifest["content_id"] = generator.domain_hash("deltareduce.005.object-manifest.v1", encoded)
    policy = golden["policy_registry"]["value"]["policies"][0]
    with pytest.raises(verifier.ContractError, match="PIECE_ROOT_MISMATCH"):
        verifier.validate_manifest(manifest, payload, golden["piece_profile"], policy)


def test_policy_registry_keeps_apply_inactive() -> None:
    generator = load("distribution_contracts")
    policies = generator.components()["policy_registry"]["value"]["policies"]
    assert policies[0]["value"]["active"] is True
    assert policies[0]["value"]["can_make_current"] is False
    assert policies[1]["value"]["active"] is False
    assert policies[1]["value"]["future_feature"] == "008-certificates-and-consensus"
