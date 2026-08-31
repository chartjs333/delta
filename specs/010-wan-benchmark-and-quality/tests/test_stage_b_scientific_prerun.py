from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_stage_b_scientific_prerun.py"
SPEC = importlib.util.spec_from_file_location("verify_stage_b_scientific_prerun", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_frozen_stage_b_inputs_stop_before_scientific_execution() -> None:
    report = MODULE.build()
    assert report["status"] == "STOP_BEFORE_PRIMARY_SCIENTIFIC_EXECUTION"
    assert report["primary_scientific_execution_count"] == 0
    assert report["tasks_completed"] == []
    assert report["feature_010_decision"] == "NO_GO"
    assert set(report["stop_codes"]) == {
        "APPROVED_MEASURED_RUNNER",
        "PINNED_GPU_SCIENTIFIC_SOFTWARE",
        "PREREGISTERED_EVALUATION_METHODS",
        "WORKLOAD_TICKET_TOKEN_RECONCILIATION",
    }


def test_workload_check_exposes_ticket_and_token_conflict() -> None:
    definition, _ = MODULE.load_canonical(MODULE.DEFINITION)
    workload, _ = MODULE.load_canonical(MODULE.WORKLOAD)
    stage_a, _ = MODULE.load_canonical(MODULE.STAGE_A)
    result = MODULE.workload_check(definition, workload, stage_a)
    assert result["B"] == 32_768
    assert result["ticket_count"] == 32
    assert result["ticket_contract_total_tokens"] == 1_048_576
    assert result["executor_processed_tokens_per_arm_run"] == 32_768
    assert result["status"] == "FAIL"


def test_gpu_lock_and_evaluator_bindings_fail_closed() -> None:
    definition, _ = MODULE.load_canonical(MODULE.DEFINITION)
    dependencies, _ = MODULE.load_canonical(MODULE.DEPENDENCIES)
    profile, _ = MODULE.load_json_object(MODULE.PHYSICAL_PROFILE)
    software = MODULE.software_check(profile)
    evaluation = MODULE.evaluation_check(definition, dependencies)
    assert software["uv_lock_torch_versions"] == ["2.6.0", "2.6.0+cpu"]
    assert software["cuda_torch_bound_by_uv_lock"] is False
    assert software["status"] == "FAIL"
    assert evaluation["evaluation_method_fields_present_in_all_artifacts"] == []
    assert evaluation["status"] == "FAIL"
