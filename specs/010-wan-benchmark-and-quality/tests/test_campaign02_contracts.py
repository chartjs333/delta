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
    assert len(module.SCHEMAS) == 69
    assert all(path.read_bytes() == expected for path, expected in outputs.items())
    registry = json.loads(module.REGISTRY_PATH.read_bytes())
    assert registry["registry_version"] == "010.11.0-concentrated-loss-causal-projection"
    assert len(registry["fixtures"]) == 7
    assert registry["semantic_completeness_claimed"] is False
    measured_stage_c = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v2.json"
        ).read_bytes()
    )
    assert measured_stage_c["properties"]["measurement_source"] == {
        "const": "PYTHON_JAVA_NETTY_CPP_OS"
    }
    assert measured_stage_c["properties"]["network_counters"]["minItems"] == 3
    actual_stage_c = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v3.json"
        ).read_bytes()
    )
    assert {"raw_java_receipt_base64", "raw_java_receipt_id"} <= set(actual_stage_c["required"])
    assert {
        "os_rx_bytes_before",
        "os_rx_bytes_after",
        "os_tx_bytes_before",
        "os_tx_bytes_after",
    } <= set(actual_stage_c["properties"]["network_counters"]["items"]["required"])
    assert actual_stage_c["properties"]["fault_results"]["items"]["properties"][
        "observation_source"
    ] == {"const": "ACTUAL_RUNTIME_TRANSITION"}
    causal_stage_c = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v4.json"
        ).read_bytes()
    )
    causal_fault = causal_stage_c["properties"]["fault_results"]["items"]
    assert {
        "aggregate_root_qc_id",
        "apply_work_item_id",
        "apply_qc_id",
        "current_pointer_before",
        "current_pointer_after",
        "message_delivery_ticks",
        "per_domain_remaining_tickets",
    } <= set(causal_fault["required"])
    concentrated_stage_c = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v5.json"
        ).read_bytes()
    )
    assert concentrated_stage_c["properties"]["fault_results"]["minItems"] == 8
    candidate = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/stage-c-candidate-run-v2.json").read_bytes()
    )
    assert candidate["properties"]["plan_count"] == {"const": 15}
    assert candidate["properties"]["execution_authorized"] == {"const": False}
    assert "causal_projection_id" in candidate["properties"]["plan_records"]["items"]["required"]
    assert "causal_root" in candidate["required"]
    candidate_summary = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/stage-c-candidate-summary-v2.json"
        ).read_bytes()
    )
    assert candidate_summary["properties"]["repeat_causal_match"] == {"const": True}
    runtime_lineage = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/qualified-runtime-lineage-v5.json"
        ).read_bytes()
    )
    assert {
        "java_executable_id",
        "native_executable_id",
        "netty_artifact_ids",
        "transport_harness_id",
    } <= set(runtime_lineage["required"])
    stage_c_plan = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/execution-plan-v6.json").read_bytes()
    )
    assert {
        "java_executable_id",
        "native_executable_id",
        "netty_artifact_ids",
        "transport_harness_id",
    } <= set(stage_c_plan["required"])
    bootstrap_mapping = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-mapping-v1.json"
        ).read_bytes()
    )
    assert bootstrap_mapping["properties"]["execution_authorized"] == {"const": False}
    assert "definition_id" not in bootstrap_mapping["properties"]
    registration = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/workflow-registration-receipt-v3.json"
        ).read_bytes()
    )
    assert {
        "api_evidence_root",
        "registration_artifact_archive_digest",
        "registration_artifact_id",
        "registration_artifact_name",
        "registration_run_attempt",
        "registration_run_completed_at",
        "registration_run_conclusion",
        "registration_run_created_at",
        "registration_run_id",
        "registration_run_status",
        "registration_run_updated_at",
        "registration_workflow_id",
    } <= set(registration["required"])
    registration_signature = json.loads(
        (
            ROOT / "delta-protocol/schemas/010/campaign-02/workflow-registration-signature-v2.json"
        ).read_bytes()
    )
    assert {
        "api_evidence_root",
        "registration_receipt_id",
        "registration_run_status",
        "registration_run_conclusion",
        "registration_run_completed_at",
        "registration_artifact_created_at",
        "registration_artifact_expires_at",
        "registration_artifact_name",
        "signature_base64",
    } <= set(registration_signature["required"])
    replacement_definition = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/benchmark-definition-v5.json").read_bytes()
    )
    assert "bootstrap_mapping_id" in replacement_definition["required"]
    stage_a_workflow = (ROOT / ".github/workflows/benchmark-campaign02-stage-a.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_call:" in stage_a_workflow
    assert "job.workflow_sha" in stage_a_workflow
    assert ".run_attempt" in stage_a_workflow
    assert ".digest" in stage_a_workflow
    assert "--registration-api-evidence" in stage_a_workflow
    assert "--registration-vote" in stage_a_workflow
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
