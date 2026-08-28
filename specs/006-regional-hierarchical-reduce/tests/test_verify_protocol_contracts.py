from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = ROOT / "specs/006-regional-hierarchical-reduce/scripts"


def load_module(name: str):  # type: ignore[no-untyped-def]
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"feature006_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_contract_gate_passes() -> None:
    verifier = load_module("verify_protocol_contracts")
    result = verifier.verify()
    assert result["status"] == "PASS"
    assert result["summary"]["regional_result_count"] == 12
    assert result["summary"]["global_result_count"] == 4


def test_topology_rejects_duplicate_ticket_membership() -> None:
    contracts = load_module("hierarchy_contracts")
    verifier = load_module("verify_protocol_contracts")
    value = copy.deepcopy(contracts.topology_fixture()["value"])
    value["domains"][0]["regions"][1]["tickets"].append(
        value["domains"][0]["regions"][0]["tickets"][0]
    )
    topology = contracts.identified("deltareduce.006.reduce-topology.v1", value)
    with pytest.raises(verifier.ContractError, match="TOPOLOGY_TICKET_COVERAGE_INVALID"):
        verifier.validate_topology(topology)


def test_proof_rejects_missing_normative_conjunct() -> None:
    contracts = load_module("hierarchy_contracts")
    verifier = load_module("verify_protocol_contracts")
    topology = contracts.topology_fixture()
    proof = contracts.hierarchy_proof(topology)
    value = copy.deepcopy(proof["value"])
    po_a3 = next(item for item in value["theorems"] if item["obligation_id"] == "PO-A3")
    po_a3["conjuncts"].remove("round-half-tie-toward-positive")
    proof = contracts.identified("deltareduce.006.hierarchy-proof-instance.v1", value)
    with pytest.raises(verifier.ContractError, match="HIERARCHY_THEOREM_BINDINGS_INVALID"):
        verifier.validate_proof(proof, topology["content_id"])


def test_hierarchy_rejects_non_flat_regional_sum() -> None:
    contracts = load_module("hierarchy_contracts")
    verifier = load_module("verify_protocol_contracts")
    golden = contracts.golden_fixture()
    regional = golden["regional_shard_results"][0]
    value = copy.deepcopy(regional["value"])
    value["numerator"][0] = str(int(value["numerator"][0]) + 1)
    golden["regional_shard_results"][0] = contracts.identified(
        "deltareduce.006.regional-shard-result.v1", value
    )
    with pytest.raises(verifier.ContractError, match="REGIONAL_SUM_INVALID"):
        verifier.validate_hierarchy(golden)


def test_feature008_current_state_field_is_rejected() -> None:
    contracts = load_module("hierarchy_contracts")
    verifier = load_module("verify_protocol_contracts")
    golden = contracts.golden_fixture()
    golden["current_checkpoint"] = "sha256:" + "0" * 64
    with pytest.raises(verifier.ContractError, match="FEATURE008_BOUNDARY_VIOLATION"):
        verifier.validate_feature008_boundary(golden)


def test_every_partial_media_type_is_denied() -> None:
    verifier = load_module("verify_protocol_contracts")
    result = verifier.validate_distribution_boundary()
    assert result["status"] == "PASS"
    assert result["denied_media_types"] == [
        "application/vnd.deltareduce.input-candidate;version=1",
        "application/vnd.deltareduce.parameter-partial;version=1",
        "application/vnd.deltareduce.regional-partial;version=1",
    ]
