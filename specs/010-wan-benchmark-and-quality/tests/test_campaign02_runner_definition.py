from __future__ import annotations

import base64
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.arms import ArmSpec
from deltatorrent.benchmark.campaign02 import (
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.campaign02_binding import (
    Campaign02BindingError,
    QualifiedRuntimeLineage,
    compile_campaign02_plan_catalog,
)
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    create_definition_vote,
    finalize_definition_attestation,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/benchmark/campaign-02"
REPORTS = ROOT / "reports/benchmark/campaigns/campaign-02"
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/campaign02_runner_definition.py"
SOURCE = "7caad473501a31d95e24408901a6a2236ec03ce6"
TREE = "515d65fbf5a18ab872c8f31187b7a0788a33badc"
SUPERSEDED = "sha256:b263e77766599426dbf13574b05f2104ace1acf2d866e6ca5d9a3abef66f5dd5"
REPLACEMENT = "sha256:3844edbdcfc402ca3fbd54f9a2e4dfab965a8a7280a6ccd3dad70611e88ee803"
NOW = datetime(2026, 9, 2, 16, 0, tzinfo=UTC)


def load(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    assert isinstance(value, dict)
    assert raw in {canonical_json_bytes(value), canonical_json_bytes(value) + b"\n"}
    return value


def test_replacement_definition_outputs_are_current_and_schema_valid() -> None:
    subprocess.run(["uv", "run", "python", str(SCRIPT)], cwd=ROOT, check=True)
    mappings = {
        "definition-v3.json": "benchmark-definition-v3.json",
        "qualified-runtime-lineage-v3.json": "qualified-runtime-lineage-v3.json",
        "stage-execution-identities-v2.json": "stage-execution-identities-v2.json",
    }
    for value_name, schema_name in mappings.items():
        value = load(CONFIG / value_name)
        schema = json.loads(
            (ROOT / "delta-protocol/schemas/010/campaign-02" / schema_name).read_bytes()
        )
        assert isinstance(schema, dict)
        required = schema["required"]
        properties = schema["properties"]
        assert isinstance(required, list) and isinstance(properties, dict)
        assert set(value) == set(required) == set(properties)
        assert schema["additionalProperties"] is False


def test_replacement_definition_binds_exact_stage_identities_and_source() -> None:
    definition = BenchmarkDefinition.from_dict(load(CONFIG / "definition-v3.json"))
    lineage = QualifiedRuntimeLineage.from_dict(load(CONFIG / "qualified-runtime-lineage-v3.json"))
    identities = StageExecutionIdentityManifest.from_dict(
        load(CONFIG / "stage-execution-identities-v2.json")
    )
    assert definition.content_id == REPLACEMENT
    assert definition.content_id != SUPERSEDED
    assert definition.source_commit == lineage.source_commit == identities.source_commit == SOURCE
    assert definition.source_tree == lineage.source_tree == identities.source_tree == TREE
    assert definition.qualified_runtime_lineage_id == lineage.content_id
    assert definition.stage_execution_identities_id == identities.content_id
    assert lineage.stage_execution_identities_id == identities.content_id
    assert lineage.exactness_runner_id == identities.identity_id("exactness_runner")
    assert lineage.scientific_runner_id == identities.identity_id("scientific_runner")
    assert lineage.network_fault_runner_id == identities.identity_id("network_fault_runner")
    assert (
        len(
            {
                lineage.exactness_runner_id,
                lineage.scientific_runner_id,
                lineage.network_fault_runner_id,
                identities.identity_id("multi_role_runner"),
            }
        )
        == 4
    )


def test_definition_v3_is_parseable_but_cannot_compile_after_supersession() -> None:
    definition = BenchmarkDefinition.from_dict(load(CONFIG / "definition-v3.json"))
    lineage = QualifiedRuntimeLineage.from_dict(load(CONFIG / "qualified-runtime-lineage-v3.json"))
    identities = StageExecutionIdentityManifest.from_dict(
        load(CONFIG / "stage-execution-identities-v2.json")
    )
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    domain = load_domain_manifest(CONFIG / "domain-manifest-v1.json")
    ticket_plan = load_ticket_plan(CONFIG / "ticket-plan-v1.json", workload, domain)
    arms_value = load(CONFIG / "definition-arms-v2.json")["arms"]
    assert isinstance(arms_value, list)
    arms = tuple(
        ArmSpec(
            content_id=sha256_content_id(canonical_json_bytes(value)),
            arm_id=str(value["arm_id"]),
            kind=str(value["kind"]),
            deployment_profile=str(value["deployment_profile"]),
            mandatory=value["mandatory"] is True,
            workload_identity=str(value["workload_identity"]),
            runtime_profile_id=sha256_content_id(
                canonical_json_bytes({"deployment_profile": value["deployment_profile"]})
            ),
            topology=str(value["topology"]),
        )
        for value in arms_value
        if isinstance(value, dict)
    )
    private_keys = tuple(Ed25519PrivateKey.generate() for _ in range(4))
    validators = []
    for index, private_key in enumerate(private_keys):
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        validators.append(
            {
                "controller_id": f"replacement-controller-{index}",
                "key_custody_statement_id": sha256_content_id(
                    f"replacement-custody-{index}".encode()
                ),
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "public_key_id": sha256_content_id(
                    b"deltareduce.010.benchmark-review-key.v1\0" + public_key
                ),
                "signature_algorithm": "ED25519",
                "valid_from": "2026-09-01T00:00:00Z",
                "valid_until": None,
                "validator_id": f"replacement-validator-{index}",
            }
        )
    validator_set = BenchmarkReviewValidatorSet.from_dict(
        {
            "campaign_id": "campaign-02",
            "f_b": 1,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "purpose": "BENCHMARK_DEFINITION_REVIEW",
            "schema_version": "1.0.0",
            "type_name": "BENCHMARK_REVIEW_VALIDATOR_SET",
            "validators": validators,
        }
    )
    votes = tuple(
        create_definition_vote(
            benchmark_definition_id=definition.content_id,
            validator_set=validator_set,
            signer_id=f"replacement-validator-{index}",
            submitted_at=NOW,
            private_key=private_keys[index],
        )
        for index in range(3)
    )
    attestation = finalize_definition_attestation(
        benchmark_definition_id=definition.content_id,
        validator_set=validator_set,
        votes=votes,
        verified_at=NOW,
    )
    with pytest.raises(
        Campaign02BindingError,
        match="CAMPAIGN02_DEFINITION_SUPERSEDED_BEFORE_ATTESTATION",
    ):
        compile_campaign02_plan_catalog(
            definition=definition,
            attestation_document=attestation.document,
            validator_set=validator_set,
            votes=votes,
            workload=workload,
            domain_manifest=domain,
            ticket_plan=ticket_plan,
            arms=arms,
            runtime_lineage=lineage,
            stage_identities=identities,
        )


def test_supersession_and_readiness_preserve_governance_stop() -> None:
    superseded_definition = BenchmarkDefinition.from_dict(load(CONFIG / "definition-v2.json"))
    supersession = load(REPORTS / "definition-supersession-runner-binding.json")
    readiness = load(REPORTS / "definition-readiness-v3.json")
    assert superseded_definition.content_id == SUPERSEDED
    assert supersession["superseded_definition_id"] == SUPERSEDED
    assert supersession["replacement_definition_id"] == REPLACEMENT
    assert supersession["status"] == "SUPERSEDED_BEFORE_ATTESTATION"
    assert supersession["votes"] == supersession["observations"] == 0
    assert supersession["attestation"] == "ABSENT"
    assert readiness["benchmark_definition_id"] == REPLACEMENT
    assert readiness["execution_authorization"] == "ABSENT"
    assert readiness["primary_observations_created"] == 0
    assert readiness["plan_catalog"]["authoritative_catalog_created"] is False  # type: ignore[index]
    authorization = readiness["authorization"]
    assert isinstance(authorization, dict)
    assert authorization and all(value is False for value in authorization.values())
    executable_supersession = load(REPORTS / "definition-supersession-executable-provenance.json")
    assert executable_supersession["superseded_definition_id"] == REPLACEMENT
    assert executable_supersession["replacement_definition_id"] is None
    assert executable_supersession["status"] == "SUPERSEDED_BEFORE_ATTESTATION"
    assert executable_supersession["votes"] == executable_supersession["observations"] == 0
    assert executable_supersession["attestation"] == "ABSENT"


def test_construction_creates_no_persisted_votes_attestation_or_execution() -> None:
    forbidden = (
        CONFIG / "definition-v3-attestation.json",
        CONFIG / "definition-v3-votes.json",
        REPORTS / "stage-a-gate-receipt.json",
        REPORTS / "benchmark-result-qc.json",
    )
    assert all(not path.exists() for path in forbidden)
