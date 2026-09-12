from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from deltatorrent.benchmark.campaign02_binding import QualifiedRuntimeLineage
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/benchmark/campaign-02"
REPORTS = ROOT / "reports/benchmark/campaigns/campaign-02"
EVIDENCE = ROOT / "specs/010-wan-benchmark-and-quality/evidence"
SCRIPT = (
    ROOT / "specs/010-wan-benchmark-and-quality/scripts/campaign02_runner_provenance_definition.py"
)
SOURCE = "b97fd541a7ef7f100b8ff1ccf4ced61aa2880de2"
TREE = "354bd4cae74e568b8489b667aeb4e88f36de57e0"
SUPERSEDED = "sha256:3844edbdcfc402ca3fbd54f9a2e4dfab965a8a7280a6ccd3dad70611e88ee803"
DEFINITION_V4 = "sha256:26830d3199482873832f4030641c20a0758c4f474abebacbc668de35d56dfdf9"


def load(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    assert isinstance(value, dict)
    assert raw == canonical_json_bytes(value) + b"\n"
    return value


def tracked_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def test_definition_v4_outputs_are_reproducible_and_schema_complete() -> None:
    subprocess.run(["uv", "run", "python", str(SCRIPT)], cwd=ROOT, check=True)
    mappings = {
        "definition-v4.json": "benchmark-definition-v4.json",
        "qualified-runtime-lineage-v4.json": "qualified-runtime-lineage-v4.json",
        "stage-execution-identities-v3.json": "stage-execution-identities-v3.json",
    }
    for value_name, schema_name in mappings.items():
        value = load(CONFIG / value_name)
        schema = json.loads(
            (ROOT / "delta-protocol/schemas/010/campaign-02" / schema_name).read_bytes()
        )
        assert isinstance(schema, dict)
        assert set(value) == set(schema["required"]) == set(schema["properties"])
        assert schema["additionalProperties"] is False


def test_definition_v4_binds_verified_executable_identities_and_lineage() -> None:
    definition = BenchmarkDefinition.from_dict(load(CONFIG / "definition-v4.json"))
    lineage = QualifiedRuntimeLineage.from_dict(load(CONFIG / "qualified-runtime-lineage-v4.json"))
    identities = StageExecutionIdentityManifest.from_dict(
        load(CONFIG / "stage-execution-identities-v3.json")
    )
    assert definition.content_id == DEFINITION_V4
    assert definition.content_id != SUPERSEDED
    assert definition.source_commit == lineage.source_commit == identities.source_commit == SOURCE
    assert definition.source_tree == lineage.source_tree == identities.source_tree == TREE
    assert definition.qualified_runtime_lineage_id == lineage.content_id
    assert definition.stage_execution_identities_id == identities.content_id
    assert lineage.stage_execution_identities_id == identities.content_id
    assert lineage.schema_version == "4.0.0"
    assert identities.schema_version == "3.0.0"
    for name in ("exactness_runner", "network_fault_runner", "stage_gate_analyzer"):
        identity = identities.identity(name)
        entries = [
            item
            for field in ("executable_hashes", "workflow_hashes")
            for item in identity.value[field]  # type: ignore[union-attr]
        ]
        assert entries
        assert all(
            sha256_content_id(tracked_bytes(SOURCE, str(item["path"]))) == item["content_id"]
            for item in entries
        )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_IDENTITY_FILE_HASH_MISMATCH"):
        identities.verify_files("exactness_runner", ROOT)


def test_definition_v4_production_identities_are_role_and_class_bound() -> None:
    identities = StageExecutionIdentityManifest.from_dict(
        load(CONFIG / "stage-execution-identities-v3.json")
    )
    exactness = identities.identity("exactness_runner").value
    network = identities.identity("network_fault_runner").value
    analyzer = identities.identity("stage_gate_analyzer").value
    assert exactness["role"] == "EXACTNESS_RUNNER"
    assert exactness["source_class"] == "MEASURED_CI_WORKFLOW"
    assert exactness["implementation_class"].endswith("Campaign02ExactnessEvidenceRunner")  # type: ignore[union-attr]
    assert exactness["workflow_repository"] == "chartjs333/delta"
    assert exactness["workflow_default_ref"] == "refs/heads/main"
    assert network["role"] == "NETWORK_FAULT_RUNNER"
    assert network["source_class"] == "MEASURED_HARDWARE"
    assert network["implementation_class"].endswith("Campaign02NetworkFaultRunner")  # type: ignore[union-attr]
    assert analyzer["source_class"] == "MEASURED_CONTROL_PLANE"
    assert analyzer["implementation_class"].endswith("Campaign02StageGateFinalizer")  # type: ignore[union-attr]


def test_definition_v4_receipt_and_readiness_preserve_governance_stop() -> None:
    receipt_path = EVIDENCE / "campaign-02-runner-provenance-exact-source-ci-receipt.json"
    exact_path = EVIDENCE / "campaign-02-runner-provenance-exact-source-qualification.json"
    hardware_path = EVIDENCE / "campaign-02-runner-provenance-hardware-qualification.json"
    receipt = load(receipt_path)
    readiness = load(REPORTS / "definition-readiness-v4.json")
    authorization = readiness["authorization"]
    assert receipt["status"] == "PASS"
    assert receipt["workflow_run_id"] == 33662489371
    assert receipt["source"] == {"commit": SOURCE, "tree": TREE}
    assert receipt["exact_source_qualification_id"] == sha256_content_id(exact_path.read_bytes())
    assert receipt["hardware_qualification_id"] == sha256_content_id(hardware_path.read_bytes())
    assert receipt["primary_execution_authorized"] is False
    assert receipt["primary_scientific_execution_count"] == 0
    assert receipt["scientific_observations_created"] is False
    assert isinstance(authorization, dict)
    assert authorization and all(value is False for value in authorization.values())
    assert readiness["primary_observations_created"] == 0
    assert readiness["execution_authorization"] == "ABSENT"
    assert readiness["c2_024_status"] == "NOT_AUTHORIZED"
    assert readiness["stage_a_default_branch_registration"] == "REQUIRED_BEFORE_C2_024"
    assert readiness["plan_catalog"]["authoritative_catalog_created"] is False  # type: ignore[index]


def test_definition_v3_and_source_supersession_record_remain_immutable() -> None:
    paths = (
        "configs/benchmark/campaign-02/definition-v3.json",
        "configs/benchmark/campaign-02/qualified-runtime-lineage-v3.json",
        "configs/benchmark/campaign-02/stage-execution-identities-v2.json",
        "reports/benchmark/campaigns/campaign-02/definition-readiness-v3.json",
        "reports/benchmark/campaigns/campaign-02/definition-supersession-executable-provenance.json",
    )
    for path in paths:
        commit = SOURCE if path.endswith("executable-provenance.json") else "c9a2da4"
        assert (ROOT / path).read_bytes() == tracked_bytes(commit, path)
    resolution = load(REPORTS / "definition-supersession-executable-provenance-resolution.json")
    assert resolution["superseded_definition_id"] == SUPERSEDED
    assert resolution["replacement_definition_id"] == DEFINITION_V4
    assert resolution["votes"] == resolution["observations"] == 0
    assert resolution["attestation"] == "ABSENT"


def test_definition_v4_package_creates_no_authority_or_observation() -> None:
    forbidden = (
        CONFIG / "definition-v4-attestation.json",
        CONFIG / "definition-v4-votes.json",
        REPORTS / "stage-a-gate-receipt.json",
        REPORTS / "stage-b-gate-receipt.json",
        REPORTS / "stage-c-gate-receipt.json",
        REPORTS / "benchmark-result-qc.json",
    )
    assert all(not path.exists() for path in forbidden)
