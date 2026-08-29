from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/008-certificates-and-consensus/scripts/certificate_contracts.py"


def load_contracts():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("feature008_contracts", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_full_chain_fixture_validates() -> None:
    module = load_contracts()
    result = module.validate_contract(module.contract_fixture())
    assert result["status"] == "PASS"
    assert result["required_key_count"] == 4
    assert result["shard_qc_count"] == 4


def test_all_canonical_schemas_are_closed() -> None:
    module = load_contracts()
    schemas = module.schema_documents()
    assert len(schemas) == 11
    assert all(schema["additionalProperties"] is False for schema in schemas.values())


def test_early_seed_fails_schema() -> None:
    module = load_contracts()
    fixture = module.contract_fixture()
    seed = fixture["seed_transcript"]["value"].copy()
    seed["input_set_certificate_id"] = "NONE"
    with pytest.raises(module.SchemaValidationError, match="PATTERN"):
        module.validate_schema(seed, module.schema_documents()["seed-transcript"])


def test_exact_requirement_matrix_not_observed_subset() -> None:
    module = load_contracts()
    fixture = module.contract_fixture()
    fixture["aggregate_root_qc"]["value"]["leaves"] = fixture["aggregate_root_qc"]["value"][
        "leaves"
    ][:-1]
    fixture["aggregate_root_qc"] = module.identified(
        "deltareduce.008.aggregate-root-qc.v1", fixture["aggregate_root_qc"]["value"]
    )
    with pytest.raises(module.ContractError, match="AGGREGATE_COVERAGE_DRIFT"):
        module.validate_contract(fixture)


def test_invalid_matrix_names_and_reasons_are_exact() -> None:
    module = load_contracts()
    results = module.validate_invalid(module.invalid_fixture(module.contract_fixture()))
    assert len(results) == 6
    assert all(item["status"] == "PASS" for item in results)
