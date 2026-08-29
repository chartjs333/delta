from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = ROOT / "specs/007-domain-pure-ticket-scheduling/scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import scheduling_contracts as contracts  # noqa: E402


def test_generated_outputs_are_exact_and_valid() -> None:
    outputs = contracts.build_outputs()
    contracts.check_outputs(outputs)
    result = contracts.validate_outputs(outputs)
    assert result["status"] == "PASS"
    assert result["schema_count"] == 8
    assert result["valid"]["domain_ticket_counts"] == {"code": 2, "text": 1}


def test_all_schemas_are_strict_and_have_no_math_authority_fields() -> None:
    forbidden = {
        "adaptive_h",
        "adaptive_b",
        "coefficient",
        "device_speed_weight",
        "pi_d",
        "staleness_weight",
    }
    for schema in contracts.schema_documents().values():
        assert schema["additionalProperties"] is False
        assert schema["required"] == sorted(schema["properties"])
        assert not (forbidden & set(schema["properties"]))


def test_ticket_fixed_work_mutation_is_rejected() -> None:
    fixture = copy.deepcopy(contracts.contract_fixture())
    fixture["work_tickets"][0]["value"]["step_budget"] += 1
    fixture["work_tickets"][0] = contracts.identified(
        "deltareduce.007.work-ticket.v1", fixture["work_tickets"][0]["value"]
    )
    with pytest.raises(contracts.ContractError, match="TICKET_FIXED_WORK_MUTATED"):
        contracts.validate_contract(fixture)


def test_stale_timer_context_is_rejected() -> None:
    fixture = copy.deepcopy(contracts.contract_fixture())
    fixture["lease_timer_tokens"][0]["value"]["lease_epoch"] = 1
    fixture["lease_timer_tokens"][0] = contracts.identified(
        "deltareduce.007.lease-timer-token.v1",
        fixture["lease_timer_tokens"][0]["value"],
    )
    with pytest.raises(contracts.ContractError, match="TIMER_CONTEXT_DRIFT"):
        contracts.validate_contract(fixture)


def test_forbidden_schema_fields_and_java_reassignment_are_rejected() -> None:
    negative = contracts.invalid_fixture(contracts.contract_fixture())
    result = contracts.validate_invalid(negative)
    assert {item["name"] for item in result} == {
        "adaptive-step-field",
        "device-speed-weight-field",
        "java-reassign-timer",
        "ticket-step-budget-mutation",
        "zero-domain-quota",
    }
