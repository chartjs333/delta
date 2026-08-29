from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs" / "009-qlora-8gb-mode" / "scripts" / "qlora_contracts.py"
SPEC = importlib.util.spec_from_file_location("feature009_contracts", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_generated_contracts_are_current() -> None:
    for path, expected in MODULE.expected_outputs().items():
        assert path.read_bytes() == expected


def test_all_schemas_are_closed_and_keep_existing_certificate_graph() -> None:
    schemas = MODULE.schema_documents()

    assert len(schemas) == 11
    assert all(schema["additionalProperties"] is False for schema in schemas.values())
    serialized = json.dumps(schemas, sort_keys=True)
    assert "QLORA_APPLY_QC" not in serialized
    assert "QLORA_AGGREGATE_ROOT_QC" not in serialized
    assert "QLORA_INPUT_SET_CERTIFICATE" not in serialized


def test_valid_chain_is_canonical_and_linked() -> None:
    schemas = MODULE.schema_documents()
    fixture = MODULE.fixture_documents()["valid"]
    artifacts = fixture["artifacts"]

    for name, wrapper in artifacts.items():
        MODULE.validate_identified(name, wrapper, schemas)
    result = MODULE.validate_chain(artifacts)

    assert result == {
        "adapter_parameter_count": 2,
        "artifact_count": 11,
        "status": "PASS",
    }
    assert fixture["semantic_completeness_claimed"] is False


def test_negative_matrix_rejects_exact_reasons() -> None:
    schemas = MODULE.schema_documents()
    fixtures = MODULE.fixture_documents()

    assert len(fixtures["invalid"]["cases"]) == 7
    for case in fixtures["invalid"]["cases"]:
        MODULE.validate_negative(case, fixtures["valid"]["artifacts"], schemas)


def test_adapter_schema_uses_explicit_ordered_names() -> None:
    schema = MODULE.fixture_documents()["valid"]["artifacts"]["adapter_parameter_schema"]["value"]

    targets = schema["ordered_target_modules"]
    parameters = schema["ordered_parameters"]
    assert targets == ["model.layer0"]
    assert [item["name"] for item in parameters] == [
        "model.layer0.lora_A",
        "model.layer0.lora_B",
    ]
    assert all("*" not in name and "?" not in name for name in targets)


def test_root_registry_binds_every_009_schema_and_fixture() -> None:
    registry = json.loads((ROOT / "delta-protocol" / "registry.json").read_text(encoding="utf-8"))
    schema_ids = {entry["id"] for entry in registry["schemas"]}
    fixture_ids = {entry["id"] for entry in registry["fixtures"]}

    assert {schema_id for schema_id, _ in MODULE.SCHEMAS.values()} <= schema_ids
    assert {
        "QLORA009-VALID-CONTRACT-V1",
        "QLORA009-CROSS-LANGUAGE-GOLDEN-V1",
        "QLORA009-NEGATIVE-V1",
        "QLORA009-TINY-OFFLINE-V1",
    } <= fixture_ids
