from __future__ import annotations

import base64
import copy
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.campaign02_binding import compile_campaign02_plan_catalog
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    create_definition_vote,
    finalize_definition_attestation,
)

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


def test_definition_outputs_are_current_and_schema_valid() -> None:
    MODULE.check_outputs()
    definition = load(MODULE.DEFINITION_PATH)
    lineage = load(MODULE.LINEAGE_PATH)
    definition_schema = load(
        ROOT / "delta-protocol/schemas/010/campaign-02/benchmark-definition-v2.json"
    )
    lineage_schema = load(
        ROOT / "delta-protocol/schemas/010/campaign-02/qualified-runtime-lineage-v2.json"
    )
    assert definition_schema["additionalProperties"] is False
    assert lineage_schema["additionalProperties"] is False
    assert set(definition) == set(definition_schema["required"])
    assert set(lineage) == set(lineage_schema["required"])


def test_definition_is_new_and_binds_exact_qualified_source() -> None:
    definition = MODULE.BenchmarkDefinition.from_dict(load(MODULE.DEFINITION_PATH))
    assert definition.content_id == (
        "sha256:b263e77766599426dbf13574b05f2104ace1acf2d866e6ca5d9a3abef66f5dd5"
    )
    assert definition.content_id not in MODULE.FORBIDDEN_DEFINITION_IDS
    assert definition.source_commit == MODULE.QUALIFIED_SOURCE
    assert definition.source_tree == MODULE.QUALIFIED_TREE
    assert definition.workload_contract_id == (
        "sha256:a0ae49350b977b1d06ed667672551e88ff3d72cee6bac2c99c1ebe7f7933a92b"
    )
    assert definition.raw["domain_manifest_id"] == (
        "sha256:0e901e0a151d5d38006b801f9771e0f0b47d0faa0685a95a95343285e4e67f93"
    )
    assert definition.ticket_plan_id == (
        "sha256:d8f9e375ffa4987040dbc18184e3f815ff3708eb964cecc7a30993a22e6cef6e"
    )


def test_workload_and_methodology_remain_frozen() -> None:
    definition = MODULE.BenchmarkDefinition.from_dict(load(MODULE.DEFINITION_PATH))
    diff = load(MODULE.METHODOLOGY_PATH)
    assert definition.B == 32_768
    assert definition.H == 32
    assert definition.repetitions == 3
    assert definition.seeds == (2026090101, 2026090102, 2026090103)
    assert len(definition.arm_ids) == 5
    assert diff["status"] == "PASS"
    assert diff["replacement_definition_id"] == definition.content_id
    assert diff["scientific_observations_used_to_change_methodology"] == 0
    assert all(value is False for value in diff["prohibited_result_driven_changes"].values())


def test_all_stage_execution_implementations_are_content_addressed() -> None:
    identities = load(MODULE.IDENTITIES_PATH)
    values = identities["identities"]
    required = {
        "evaluation_runner",
        "exactness_runner",
        "multi_role_runner",
        "native_feature008_verifier",
        "network_fault_runner",
        "observation_writer",
        "scientific_runner",
        "signed_stage_authorization_verifier",
        "stage_gate_analyzer",
        "typed_gate_receipt_verifier",
    }
    assert set(values) == required
    assert len({value["content_id"] for value in values.values()}) == len(required)
    assert identities["source_commit"] == MODULE.QUALIFIED_SOURCE
    assert identities["source_tree"] == MODULE.QUALIFIED_TREE
    for name in ("exactness_runner", "network_fault_runner"):
        identity = values[name]["value"]
        assert identity["execution_authorized"] is False
        assert identity["source_commit"] == MODULE.QUALIFIED_SOURCE
        assert identity["source_tree"] == MODULE.QUALIFIED_TREE
        assert identity["executable_hashes"]
        assert identity["workflow_hashes"]
        assert all(
            item["path"] != ".github/workflows/benchmark.yml"
            for item in identity["workflow_hashes"]
        )


def test_runtime_lineage_has_36_independent_stage_contexts() -> None:
    exact, _ = MODULE.qualification()
    workload = MODULE.load_workload_contract(MODULE.CONFIG / "workload-v2.json")
    arms_document = MODULE.arms_document(workload.content_id)
    arms = MODULE.arm_specs(arms_document)
    identities = MODULE.component_identities(exact)
    lineage = MODULE.runtime_lineage(exact, identities, arms)
    assert lineage.content_id == load(MODULE.DEFINITION_PATH)["qualified_runtime_lineage_id"]
    assert len(lineage.certified_plan_bindings) == 36
    contexts = {
        (
            item.policy.round_id,
            item.policy.height,
            item.policy.view,
            item.policy.validator_epoch_id,
        )
        for item in lineage.certified_plan_bindings
    }
    assert len(contexts) == 36
    assert {item.gate_stage for item in lineage.certified_plan_bindings} == set(
        MODULE.CAMPAIGN02_GATE_STAGES
    )


def test_ephemeral_signatures_cannot_revive_superseded_definition() -> None:
    definition = MODULE.BenchmarkDefinition.from_dict(load(MODULE.DEFINITION_PATH))
    exact, _ = MODULE.qualification()
    workload = MODULE.load_workload_contract(MODULE.CONFIG / "workload-v2.json")
    domain_manifest = MODULE.load_domain_manifest(MODULE.CONFIG / "domain-manifest-v1.json")
    ticket_plan = MODULE.load_ticket_plan(
        MODULE.CONFIG / "ticket-plan-v1.json", workload, domain_manifest
    )
    arms = MODULE.arm_specs(MODULE.arms_document(workload.content_id))
    lineage = MODULE.runtime_lineage(exact, MODULE.component_identities(exact), arms)
    keys = tuple(Ed25519PrivateKey.generate() for _ in range(4))
    validators = []
    for index, key in enumerate(keys):
        public_key = key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        validators.append(
            {
                "controller_id": f"test-controller-{index}",
                "key_custody_statement_id": MODULE.object_id({"test-custody": index}),
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "public_key_id": MODULE.sha256_content_id(
                    b"deltareduce.010.benchmark-review-key.v1\0" + public_key
                ),
                "signature_algorithm": "ED25519",
                "valid_from": "2026-09-02T00:00:00Z",
                "valid_until": None,
                "validator_id": f"test-validator-{index}",
            }
        )
    validator_set = BenchmarkReviewValidatorSet.from_dict(
        {
            "campaign_id": "campaign-02",
            "f_b": 1,
            "formal_semantics_id": MODULE.FORMAL_SEMANTICS_ID,
            "purpose": "BENCHMARK_DEFINITION_REVIEW",
            "schema_version": "1.0.0",
            "type_name": "BENCHMARK_REVIEW_VALIDATOR_SET",
            "validators": validators,
        }
    )
    submitted_at = datetime(2026, 9, 2, 14, 0, tzinfo=UTC)
    votes = tuple(
        create_definition_vote(
            benchmark_definition_id=definition.content_id,
            validator_set=validator_set,
            signer_id=f"test-validator-{index}",
            submitted_at=submitted_at,
            private_key=keys[index],
        )
        for index in range(3)
    )
    attestation = finalize_definition_attestation(
        benchmark_definition_id=definition.content_id,
        validator_set=validator_set,
        votes=votes,
        verified_at=datetime(2026, 9, 2, 14, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_DEFINITION_SUPERSEDED_BEFORE_ATTESTATION"):
        compile_campaign02_plan_catalog(
            definition=definition,
            attestation_document=attestation.document,
            validator_set=validator_set,
            votes=votes,
            workload=workload,
            domain_manifest=domain_manifest,
            ticket_plan=ticket_plan,
            arms=arms,
            runtime_lineage=lineage,
            stage_identities=None,  # type: ignore[arg-type]
        )


def test_definition_package_rejects_source_or_runner_substitution() -> None:
    exact, _ = MODULE.qualification()
    workload = MODULE.load_workload_contract(MODULE.CONFIG / "workload-v2.json")
    arms_document = MODULE.arms_document(workload.content_id)
    arms = MODULE.arm_specs(arms_document)
    identities = MODULE.component_identities(exact)
    lineage = MODULE.runtime_lineage(exact, identities, arms)
    definition_value = load(MODULE.DEFINITION_PATH)
    source_mutation = copy.deepcopy(definition_value)
    source_mutation["source_commit"] = "c460f3003277bb81db86f9afc1d7211e27870001"
    with pytest.raises(MODULE.Campaign02DefinitionError, match="RUNTIME_LINEAGE"):
        MODULE.validate_package(
            MODULE.BenchmarkDefinition.from_dict(source_mutation),
            lineage,
            identities,
            arms,
        )
    identity_mutation = copy.deepcopy(identities)
    identity_mutation["identities"]["multi_role_runner"]["content_id"] = "sha256:" + "0" * 64
    with pytest.raises(MODULE.Campaign02DefinitionError, match="STAGE_RUNTIME_IDENTITY"):
        MODULE.validate_package(
            MODULE.BenchmarkDefinition.from_dict(definition_value),
            lineage,
            identity_mutation,
            arms,
        )


def test_construction_authorization_and_readiness_fail_closed() -> None:
    authorization = load(MODULE.AUTHORIZATION_PATH)
    readiness = load(MODULE.READINESS_PATH)
    assert authorization["status"] == "APPROVED_FOR_MERGE_AND_C2_022_ONLY"
    assert authorization["approved_task_ids"] == ["C2-022"]
    assert authorization["definition_construction_authorized"] is True
    assert all(value is False for value in authorization["execution_authorization"].values())
    assert readiness["status"] == "IMMUTABLE_DEFINITION_CREATED_AWAITING_C2_023"
    assert readiness["c2_023"]["definition_attestation"] == "ABSENT"
    assert readiness["c2_023"]["independent_votes_present"] == 0
    assert readiness["plan_catalog"]["authoritative_catalog_created"] is False
    assert readiness["execution_authorization"] == "ABSENT"
    assert readiness["primary_observations_created"] == 0
    assert all(value is False for value in readiness["authorization"].values())


def test_c2_022_does_not_create_attestation_votes_or_execution_artifacts() -> None:
    forbidden_paths = (
        MODULE.CONFIG / "definition-attestation-v2.json",
        MODULE.CONFIG / "definition-votes-v1.json",
        MODULE.CONFIG / "stage-execution-authorization-v2.json",
        MODULE.REPORTS / "stage-a-gate-receipt.json",
    )
    assert all(not path.exists() for path in forbidden_paths)
