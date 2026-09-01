from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/campaign02_definition.py"
SPEC = importlib.util.spec_from_file_location("campaign02_definition", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_bytes())
    assert isinstance(value, dict)
    return value


def test_campaign02_definition_outputs_are_current() -> None:
    MODULE.check_outputs(MODULE.definition_outputs())


def test_campaign02_definition_is_new_and_source_qualified() -> None:
    definition, workload, arms, metrics, lineage = MODULE.load_definition_outputs()
    assert definition.content_id not in MODULE.FORBIDDEN_DEFINITION_IDS
    assert definition.source_commit == MODULE.QUALIFIED_SOURCE
    assert definition.source_tree == MODULE.QUALIFIED_TREE
    assert len(definition.arm_ids) == 5
    assert len(definition.seeds) == 3
    assert definition.ticket_plan_id == MODULE.object_id(workload)
    assert definition.raw["native_build_id"] == MODULE.object_id(lineage)
    assert definition.raw["metric_definitions"] == metrics["metrics"]
    assert [MODULE.object_id(item) for item in arms["arms"]] == list(definition.arm_ids)


def test_campaign02_lineage_binds_merge_qualifications_and_stop() -> None:
    lineage = load(MODULE.LINEAGE_PATH)
    authorization = load(MODULE.DEFINITION_AUTHORIZATION_PATH)
    assert lineage["qualified_source"] == {
        "commit": MODULE.QUALIFIED_SOURCE,
        "tree": MODULE.QUALIFIED_TREE,
    }
    assert lineage["remediation_merge"]["merge_commit"] == MODULE.REMEDIATION_MERGE
    assert lineage["evidence"]["hardware_qualification_id"] == MODULE.HARDWARE_QUALIFICATION_ID
    assert (
        lineage["evidence"]["exact_source_qualification_id"] == MODULE.EXACT_SOURCE_QUALIFICATION_ID
    )
    assert set(lineage["forbidden_predecessor_definition_ids"]) == set(
        MODULE.FORBIDDEN_DEFINITION_IDS
    )
    assert lineage["definition_construction_authorization_id"] == MODULE.object_id(authorization)
    assert all(value is False for value in lineage["authorization"].values())
    assert lineage["primary_scientific_execution_count"] == 0
    assert lineage["scientific_observations_created"] is False


def test_campaign02_definition_authorization_excludes_execution() -> None:
    authorization = load(MODULE.DEFINITION_AUTHORIZATION_PATH)
    assert authorization["status"] == "APPROVED_FOR_MERGE_AND_DEFINITION_CONSTRUCTION_ONLY"
    assert authorization["approved_task_ids"] == ["C2-013", "C2-014", "C2-015"]
    assert authorization["definition_construction_authorized"] is True
    assert all(value is False for value in authorization["execution_authorization"].values())


def test_campaign02_workload_reconciles_ticket_and_arm_tokens() -> None:
    workload = load(MODULE.WORKLOAD_PATH)
    assert workload["B"] == workload["tokens_per_ticket"] == 32_768
    assert workload["H"] == workload["optimizer_steps_per_ticket"] == 32
    assert workload["tokens_per_optimizer_step"] == 1_024
    assert workload["tokens_per_ticket"] == (workload["H"] * workload["tokens_per_optimizer_step"])
    assert workload["total_tokens_per_arm_run"] == (
        workload["ticket_count"] * workload["tokens_per_ticket"]
    )


def test_campaign02_scientific_methodology_is_unchanged() -> None:
    definition, workload, arms, metrics, lineage = MODULE.load_definition_outputs()
    diff = MODULE.methodology_diff(definition, workload, arms, metrics, lineage)
    assert diff["status"] == "PASS"
    assert diff["scientific_observations_used_to_change_methodology"] == 0
    assert all(value is False for value in diff["prohibited_result_driven_changes"].values())
    assert diff["required_blocker_remediation"]["tokens_per_ticket"] == 32_768
    assert diff["required_blocker_remediation"]["total_tokens_per_arm_run"] == 1_048_576


def test_campaign02_methodology_diff_rejects_threshold_drift() -> None:
    definition, workload, arms, metrics, lineage = MODULE.load_definition_outputs()
    mutated_value = copy.deepcopy(definition.raw)
    mutated_value["metric_definitions"][1]["pass_threshold"] += 1
    mutated = MODULE.BenchmarkDefinition.from_dict(mutated_value)
    with pytest.raises(MODULE.Campaign02DefinitionError, match="DEFINITION_METRIC_BINDING_DRIFT"):
        MODULE.methodology_diff(mutated, workload, arms, metrics, lineage)


def test_campaign02_methodology_diff_rejects_coordinated_threshold_drift() -> None:
    definition, workload, arms, metrics, lineage = MODULE.load_definition_outputs()
    mutated_value = copy.deepcopy(definition.raw)
    mutated_metrics = copy.deepcopy(metrics)
    mutated_value["metric_definitions"][1]["pass_threshold"] += 1
    mutated_metrics["metrics"][1]["pass_threshold"] += 1
    mutated = MODULE.BenchmarkDefinition.from_dict(mutated_value)
    with pytest.raises(MODULE.Campaign02DefinitionError, match="METRIC_SCIENTIFIC_FIELD_DRIFT"):
        MODULE.methodology_diff(mutated, workload, arms, mutated_metrics, lineage)


def test_campaign02_attestation_outputs_are_current() -> None:
    readiness = load(MODULE.READINESS_PATH)
    outputs = MODULE.attestation_outputs(readiness["definition_created_commit"])
    MODULE.check_outputs(outputs)


def test_campaign02_definition_attestation_has_exact_quorum() -> None:
    definition, *_ = MODULE.load_definition_outputs()
    attestation = load(MODULE.ATTESTATION_PATH)
    assert attestation["type_name"] == "BENCHMARK_DEFINITION_ATTESTATION"
    assert attestation["benchmark_definition_id"] == definition.content_id
    assert attestation["governance_only"] is True
    assert attestation["f_b"] == 1
    assert attestation["quorum_threshold"] == 3
    assert attestation["ordered_signers"] == [
        "benchmark-validator-0",
        "benchmark-validator-1",
        "benchmark-validator-2",
    ]


def test_campaign02_methodology_diff_separates_allowed_changes() -> None:
    diff = load(MODULE.METHODOLOGY_DIFF_PATH)
    assert diff["campaign_transition"] == "CAMPAIGN_01_TO_CAMPAIGN_02"
    assert diff["status"] == "PASS"
    assert diff["predecessor_definition_id"] == MODULE.FORBIDDEN_DEFINITION_IDS[0]
    assert diff["replacement_definition_id"] not in MODULE.FORBIDDEN_DEFINITION_IDS
    assert diff["scientific_observations_used_to_change_methodology"] == 0
    assert all(value is False for value in diff["prohibited_result_driven_changes"].values())
    assert diff["required_blocker_remediation"]["gpu_environment_id"] == (MODULE.GPU_ENVIRONMENT_ID)


def test_campaign02_readiness_is_definition_only() -> None:
    definition, *_ = MODULE.load_definition_outputs()
    attestation = load(MODULE.ATTESTATION_PATH)
    diff = load(MODULE.METHODOLOGY_DIFF_PATH)
    readiness = load(MODULE.READINESS_PATH)
    assert readiness["definition_id"] == definition.content_id
    assert readiness["definition_attestation_id"] == MODULE.object_id(attestation)
    assert readiness["methodology_diff_id"] == MODULE.object_id(diff)
    assert readiness["definition_created_commit"] == ("a2eaf47e17c616e78a4ec4666fcb33c030a765e6")
    assert readiness["c2_016_status"] == "OPEN_REQUIRES_SEPARATE_GOVERNANCE_DECISION"
    assert readiness["execution_plan"]["execution_allowed"] is False
    assert readiness["execution_plan"]["missing_run_policy"] == "FAIL_CLOSED"
    assert all(value is False for value in readiness["authorization"].values())
    assert readiness["primary_observations_created"] == 0
