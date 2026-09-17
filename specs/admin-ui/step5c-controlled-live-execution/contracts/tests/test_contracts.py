from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "scripts" / "contract_tools.py"


def load_tools():
    spec = importlib.util.spec_from_file_location("step5c_contract_tools", TOOLS)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_materialized_contract_pack_verifies() -> None:
    tools = load_tools()
    report = tools.verify_all(write_report=False)
    assert report["passed"] is True
    assert report["validated_valid_fixture_count"] >= 7
    assert report["validated_invalid_fixture_count"] >= 7


def test_authorized_execution_fixture_parity_and_signature() -> None:
    tools = load_tools()
    bundle = tools.read_json(ROOT / "fixtures" / "valid" / "authorized-execution.train-ticket.json")
    assert tools.verify_authorized_parity(bundle) is True


def test_one_field_tamper_breaks_intent_digest() -> None:
    tools = load_tools()
    intent = tools.read_json(ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json")
    intent["operation_payload"]["ticket_id"] = "ticket_A-9999"
    assert tools.verify_intent_digest(intent) is False


def test_one_field_tamper_breaks_admission_signature() -> None:
    tools = load_tools()
    admission = tools.read_json(ROOT / "fixtures" / "valid" / "admission-record.train-ticket.json")
    admission["resource_grants"]["allow_downloads"] = True
    assert tools.verify_admission_signature(admission) is False


def test_train_ticket_scope_matrix_rejects_dataset_binding_only() -> None:
    tools = load_tools()
    bad = tools.read_json(
        ROOT / "fixtures" / "invalid" / "execution-intent.train-ticket-wrong-scope.json"
    )
    errors = tools.validate_schema_doc("execution-intent", bad)
    assert errors


def test_receipt_lineage_rejects_local_consensus_claims() -> None:
    tools = load_tools()
    bad = tools.read_json(ROOT / "fixtures" / "invalid" / "receipt-lineage.consensus-field.json")
    errors = tools.validate_schema_doc("execution-receipt-lineage-extension", bad)
    assert errors
