from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/benchmark_contracts.py"
SPEC = importlib.util.spec_from_file_location("feature010_contracts", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_generated_contracts_are_current() -> None:
    for path, expected in MODULE.expected_outputs().items():
        assert path.read_bytes() == expected


def test_schemas_are_closed_and_governance_only() -> None:
    schemas = MODULE.schema_documents()

    assert len(schemas) == 15
    assert all(schema["additionalProperties"] is False for schema in schemas.values())
    serialized = json.dumps(schemas, sort_keys=True)
    assert "protocol_current_transition" in serialized
    assert '"const": false' in serialized
    assert "BENCHMARK_APPLY_QC" not in serialized
    assert "BENCHMARK_CURRENT" not in serialized


def test_valid_fixture_is_linked_and_canonical() -> None:
    schemas = MODULE.schema_documents()
    artifacts = MODULE.fixture_documents()["valid"]["artifacts"]

    for wrapper in artifacts.values():
        MODULE.validate_identified(wrapper, schemas)
    result = MODULE.validate_chain(artifacts)

    assert result["status"] == "PASS"
    assert result["decision"] == "GO"
    assert result["run_count"] == 3
    assert result["artifact_count"] == len(artifacts)


def test_negative_matrix_fails_closed() -> None:
    schemas = MODULE.schema_documents()
    fixtures = MODULE.fixture_documents()

    assert len(fixtures["invalid"]["cases"]) == 10
    for case in fixtures["invalid"]["cases"]:
        MODULE.validate_negative(case, fixtures["valid"]["artifacts"], schemas)


def test_definition_freezes_required_methodology() -> None:
    definition = MODULE.fixture_documents()["valid"]["artifacts"]["definition"]["value"]

    assert definition["decision_function"] == "ALL_MANDATORY"
    assert definition["missing_run_policy"] == "FAIL_CLOSED"
    assert definition["isolation_policy"] == "COMPARE_BOTH"
    assert definition["primary"] is False
    assert all(metric["pass_threshold"] >= 0 for metric in definition["metric_definitions"])


def test_root_registry_binds_every_010_schema_and_fixture() -> None:
    registry = json.loads((ROOT / "delta-protocol/registry.json").read_text(encoding="utf-8"))
    schema_ids = {entry["id"] for entry in registry["schemas"]}
    fixture_ids = {entry["id"] for entry in registry["fixtures"]}

    assert {schema_id for schema_id, _ in MODULE.SCHEMAS.values()} <= schema_ids
    assert {
        "BENCHMARK010-CROSS-LANGUAGE-GOLDEN-V1",
        "BENCHMARK010-NEGATIVE-V1",
        "BENCHMARK010-SYNTHETIC-V1",
        "BENCHMARK010-VALID-CONTRACT-V1",
    } <= fixture_ids
