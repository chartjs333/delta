from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

from deltatorrent.benchmark.gpu_environment import verify_gpu_environment_outputs

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("campaign02_contracts", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_campaign02_schema_and_registry_outputs_are_exact() -> None:
    module = load_script()
    outputs = module.expected_outputs()
    assert len(module.SCHEMAS) == 30
    assert all(path.read_bytes() == expected for path, expected in outputs.items())
    registry = json.loads(module.REGISTRY_PATH.read_bytes())
    assert registry["registry_version"] == "010.5.0-signed-stage-governance"
    assert len(registry["fixtures"]) == 7
    assert registry["semantic_completeness_claimed"] is False
    observation = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/observation-v2.json").read_bytes()
    )
    assert len(observation["oneOf"]) == 2
    assert len(observation["properties"]["run_result"]["oneOf"]) == 2
    ticket = observation["properties"]["ticket_results"]["items"]
    assert "checkpoint_id" not in ticket["properties"]
    assert "certificate_ids" not in ticket["properties"]
    certified_result = observation["properties"]["run_result"]["oneOf"][1]
    assert "native_chain_admission_receipt_id" in certified_result["properties"]
    assert "native_chain_verifier_id" in certified_result["properties"]
    primary_observation = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/observation-v3.json").read_bytes()
    )
    assert primary_observation["properties"]["execution_class"] == {"const": "PRIMARY_MEASURED"}
    assert {
        "stage_authorization_attestation_id",
        "stage_authorization_id",
        "stage_authorization_proof_artifact_ids",
        "stage_authorization_quorum_threshold",
        "stage_authorization_signature_set_root",
        "stage_authorization_validator_set_id",
        "stage_authorization_vote_ids",
    } <= set(primary_observation["required"])
    execution_plan = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/execution-plan-v2.json").read_bytes()
    )
    assert len(execution_plan["oneOf"]) == 2
    bound_execution_plan = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/execution-plan-v3.json").read_bytes()
    )
    assert len(bound_execution_plan["oneOf"]) == 2
    assert {
        "domain_manifest_id",
        "qualified_runtime_lineage_id",
        "ticket_plan_id",
    } <= set(bound_execution_plan["required"])
    catalog_plan = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/execution-plan-v4.json").read_bytes()
    )
    assert catalog_plan["properties"]["execution_authorized"] == {"const": False}
    assert "gate_stage" in catalog_plan["required"]
    assert "execution_authorization_id" not in catalog_plan["properties"]
    plan_catalog = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/plan-catalog-v1.json").read_bytes()
    )
    assert plan_catalog["properties"]["base_plan_count"] == {"const": 15}
    assert plan_catalog["properties"]["execution_authorized"] == {"const": False}
    stage_authorization = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/stage-execution-authorization-v1.json"
        ).read_bytes()
    )
    assert stage_authorization["additionalProperties"] is False
    assert stage_authorization["properties"]["real_wan_authorized"] == {"const": False}
    assert stage_authorization["properties"]["result_qc_authorized"] == {"const": False}
    signed_stage_authorization = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/stage-execution-authorization-v2.json"
        ).read_bytes()
    )
    assert {
        "issued_at",
        "source_commit",
        "source_tree",
        "validator_set_id",
    } <= set(signed_stage_authorization["required"])
    stage_vote = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/stage-authorization-vote-v1.json"
        ).read_bytes()
    )
    assert stage_vote["properties"]["signature_algorithm"] == {"const": "ED25519"}
    gate_receipt = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/stage-gate-receipt-v1.json").read_bytes()
    )
    assert gate_receipt["additionalProperties"] is False
    assert gate_receipt["properties"]["decision"] == {"enum": ["FAIL", "PASS"]}
    independent_plan = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/execution-plan-v5.json").read_bytes()
    )
    assert independent_plan["properties"]["ticket_identity_scope"] == {
        "const": "ROUND_ID_PLUS_TICKET_TEMPLATE_ID"
    }


def test_gpu_environment_has_separate_hash_locked_platforms_and_cpu_lock() -> None:
    lock = verify_gpu_environment_outputs(ROOT)
    assert lock.document["python"] == "3.12.1"
    assert lock.document["cuda_runtime_id"] == "CUDA_12.4"
    assert lock.document["immutable_resolution"] is True
    assert lock.document["scientific_use"] is True
    assert len(lock.document["platform_locks"]) == 2
    assert lock.sbom["portable_cpu_lock_scientific_use"] is False
    assert lock.document["required_packages"] == {
        "accelerate": "1.14.0",
        "bitsandbytes": "0.50.2",
        "cryptography": "46.0.7",
        "huggingface_hub": "1.29.0",
        "peft": "0.20.0",
        "torch": "2.6.0+cu124",
        "transformers": "5.16.1",
    }


def test_campaign01_closure_and_campaign02_authorization_fail_closed() -> None:
    closure = json.loads(
        (
            ROOT
            / "reports/benchmark/campaigns"
            / "dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244"
            / "closure.json"
        ).read_bytes()
    )
    authorization = json.loads(
        (
            ROOT / "reports/benchmark/campaigns/campaign-02/remediation-authorization.json"
        ).read_bytes()
    )
    assert closure["status"] == "TERMINATED_NO_GO_AFTER_STAGE_A_BEFORE_SCIENTIFIC_EXECUTION"
    assert closure["primary_scientific_execution_count"] == 0
    assert closure["stage_a_transferable_to_new_campaign"] is False
    assert authorization["status"] == "APPROVED_DESIGN_AND_QUALIFICATION_ONLY"
    assert authorization["old_stage_a_reusable"] is False
    assert authorization["primary_execution_authorized"] is False
    assert authorization["stage_c_authorized"] is False
    assert authorization["real_wan_authorized"] is False
    assert authorization["benchmark_result_qc_authorized"] is False
    assert authorization["feature_011_authorized"] is False
