from __future__ import annotations

import base64
import hashlib
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.campaign02_bootstrap import (
    BootstrapRuntimeProvenance,
    BootstrapValidatorSet,
    Campaign02BootstrapError,
    SignedBootstrapMappingVote,
    SignedWorkflowRegistrationVote,
    VerifiedBootstrapMapping,
    WorkflowBootstrapMapping,
    WorkflowRegistrationApiEvidence,
    WorkflowRegistrationReceipt,
    verify_bootstrap_mapping,
    verify_bootstrap_runtime,
    verify_registration_receipt,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

BOOTSTRAP_WORKFLOW = b"name: inert campaign 02 bootstrap\n"


def _blob_id(value: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()


def _id(character: str) -> str:
    return "sha256:" + character * 64


def _mapping(**updates: object) -> WorkflowBootstrapMapping:
    value: dict[str, object] = {
        "bootstrap_commit": "1" * 40,
        "bootstrap_workflow_blob_id": _blob_id(BOOTSTRAP_WORKFLOW),
        "bootstrap_workflow_content_id": sha256_content_id(BOOTSTRAP_WORKFLOW),
        "bootstrap_workflow_path": ".github/workflows/campaign02-stage-a-bootstrap.yml",
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "qualified_source_commit": "5" * 40,
        "qualified_source_tree": "6" * 40,
        "repository": "chartjs333/delta",
        "schema_version": "1.0.0",
        "source_stage_a_workflow_content_id": _id("7"),
        "source_stage_a_workflow_path": ".github/workflows/benchmark-campaign02-stage-a.yml",
        "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_MAPPING",
    }
    value.update(updates)
    return WorkflowBootstrapMapping.from_dict(value)


def _verified_mapping():
    mapping = _mapping()
    keys = [Ed25519PrivateKey.generate() for _ in range(4)]
    validator_set = BootstrapValidatorSet.from_dict(
        {
            "execution_authorized": False,
            "f_b": 1,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "quorum_threshold": 3,
            "schema_version": "1.0.0",
            "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET",
            "validators": [
                {
                    "controller_id": f"controller-{index}",
                    "public_key_base64": base64.b64encode(
                        key.public_key().public_bytes(
                            serialization.Encoding.Raw,
                            serialization.PublicFormat.Raw,
                        )
                    ).decode("ascii"),
                    "signer_id": f"validator-{index}",
                }
                for index, key in enumerate(keys)
            ],
        }
    )
    votes = []
    submitted_at = datetime(2026, 9, 3, 10, tzinfo=UTC)
    for index, key in enumerate(keys[:3]):
        unsigned = SignedBootstrapMappingVote(
            mapping_id=mapping.content_id,
            validator_set_id=validator_set.content_id,
            signer_id=f"validator-{index}",
            submitted_at=submitted_at,
            signature=b"\0" * 64,
        )
        votes.append(
            SignedBootstrapMappingVote(
                mapping_id=unsigned.mapping_id,
                validator_set_id=unsigned.validator_set_id,
                signer_id=unsigned.signer_id,
                submitted_at=unsigned.submitted_at,
                signature=key.sign(unsigned.message),
            )
        )
    return mapping, validator_set, tuple(votes), tuple(keys)


def _provenance() -> BootstrapRuntimeProvenance:
    return BootstrapRuntimeProvenance(
        repository="chartjs333/delta",
        workflow_id=123,
        workflow_path=".github/workflows/campaign02-stage-a-bootstrap.yml",
        workflow_ref=(
            "chartjs333/delta/.github/workflows/campaign02-stage-a-bootstrap.yml@refs/heads/main"
        ),
        workflow_sha="1" * 40,
        workflow_blob_id=_blob_id(BOOTSTRAP_WORKFLOW),
        workflow_content_id=sha256_content_id(BOOTSTRAP_WORKFLOW),
        run_id=456,
        run_attempt=2,
        event_name="workflow_dispatch",
        dispatch_ref="refs/heads/main",
        github_sha="8" * 40,
        qualified_source_commit="5" * 40,
        qualified_source_tree="6" * 40,
        source_stage_a_workflow_content_id=_id("7"),
    )


def _snapshot(endpoint: str, value: dict[str, object]) -> dict[str, object]:
    raw = canonical_json_bytes(value)
    return {
        "endpoint": endpoint,
        "response_base64": base64.b64encode(raw).decode("ascii"),
        "response_sha256": sha256_content_id(raw),
        "status_code": 200,
    }


def _api_evidence(
    mapping: WorkflowBootstrapMapping,
    *,
    workflow_updates: dict[str, object] | None = None,
    ref_updates: dict[str, object] | None = None,
    file_updates: dict[str, object] | None = None,
    run_updates: dict[str, object] | None = None,
    artifact_updates: dict[str, object] | None = None,
) -> WorkflowRegistrationApiEvidence:
    prefix = f"https://api.github.com/repos/{mapping.repository}"
    workflow: dict[str, object] = {
        "id": 123,
        "path": mapping.bootstrap_workflow_path,
        "state": "active",
    }
    default_ref: dict[str, object] = {
        "object": {"sha": mapping.bootstrap_commit},
        "ref": "refs/heads/main",
    }
    workflow_file: dict[str, object] = {
        "content": base64.b64encode(BOOTSTRAP_WORKFLOW).decode("ascii"),
        "encoding": "base64",
        "path": mapping.bootstrap_workflow_path,
        "sha": mapping.bootstrap_workflow_blob_id,
    }
    run: dict[str, object] = {
        "conclusion": "success",
        "created_at": "2026-09-03T09:55:00+00:00",
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_sha": mapping.bootstrap_commit,
        "id": 456,
        "path": mapping.bootstrap_workflow_path,
        "repository": {"full_name": mapping.repository},
        "run_attempt": 2,
        "status": "completed",
        "updated_at": "2026-09-03T09:58:00+00:00",
        "workflow_id": 123,
    }
    artifact: dict[str, object] = {
        "created_at": "2026-09-03T09:57:00+00:00",
        "digest": _id("9"),
        "expired": False,
        "expires_at": "2026-12-03T09:57:00+00:00",
        "id": 789,
        "name": "campaign02-bootstrap-registration-456-attempt-2",
        "workflow_run": {
            "head_branch": "main",
            "head_sha": mapping.bootstrap_commit,
            "id": 456,
        },
    }
    for target, updates in (
        (workflow, workflow_updates),
        (default_ref, ref_updates),
        (workflow_file, file_updates),
        (run, run_updates),
        (artifact, artifact_updates),
    ):
        if updates:
            target.update(updates)
    return WorkflowRegistrationApiEvidence.from_dict(
        {
            "collected_at": "2026-09-03T09:59:00+00:00",
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "repository": mapping.repository,
            "schema_version": "1.0.0",
            "snapshots": {
                "bootstrap_workflow_file": _snapshot(
                    f"{prefix}/contents/{mapping.bootstrap_workflow_path}"
                    f"?ref={mapping.bootstrap_commit}",
                    workflow_file,
                ),
                "default_branch_ref": _snapshot(f"{prefix}/git/ref/heads/main", default_ref),
                "registration_artifact_metadata": _snapshot(
                    f"{prefix}/actions/artifacts/789", artifact
                ),
                "registration_workflow_run": _snapshot(f"{prefix}/actions/runs/456", run),
                "workflow_metadata": _snapshot(f"{prefix}/actions/workflows/123", workflow),
            },
            "type_name": "CAMPAIGN02_WORKFLOW_REGISTRATION_API_EVIDENCE",
        }
    )


def _registration(
    mapping: WorkflowBootstrapMapping,
    api_evidence: WorkflowRegistrationApiEvidence,
    **updates: object,
):
    value: dict[str, object] = {
        "authority_bundle_supplied": False,
        "bootstrap_commit": mapping.bootstrap_commit,
        "bootstrap_commit_on_default_branch": True,
        "bootstrap_mapping_id": mapping.content_id,
        "bootstrap_workflow_blob_id": mapping.bootstrap_workflow_blob_id,
        "bootstrap_workflow_content_id": mapping.bootstrap_workflow_content_id,
        "checked_at": "2026-09-03T10:00:00+00:00",
        "default_branch_ref": "refs/heads/main",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "api_evidence_root": api_evidence.content_id,
        "execution_artifact_count": 0,
        "execution_count": 0,
        "observation_count": 0,
        "qualified_source_commit": mapping.qualified_source_commit,
        "qualified_source_exists": True,
        "qualified_source_tree": mapping.qualified_source_tree,
        "repository": mapping.repository,
        "registration_artifact_archive_digest": _id("9"),
        "registration_artifact_created_at": "2026-09-03T09:57:00+00:00",
        "registration_artifact_expires_at": "2026-12-03T09:57:00+00:00",
        "registration_artifact_id": 789,
        "registration_artifact_name": "campaign02-bootstrap-registration-456-attempt-2",
        "registration_run_attempt": 2,
        "registration_run_completed_at": "2026-09-03T09:58:00+00:00",
        "registration_run_conclusion": "success",
        "registration_run_created_at": "2026-09-03T09:55:00+00:00",
        "registration_run_event": "workflow_dispatch",
        "registration_run_head_sha": mapping.bootstrap_commit,
        "registration_run_id": 456,
        "registration_run_ref": "refs/heads/main",
        "registration_run_status": "completed",
        "registration_run_updated_at": "2026-09-03T09:58:00+00:00",
        "registration_workflow_id": 123,
        "schema_version": "3.0.0",
        "stage_a_plans_executed": 0,
        "stage_gate_receipt_emitted": False,
        "type_name": "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT",
        "workflow_id": 123,
        "workflow_path": mapping.bootstrap_workflow_path,
        "workflow_state": "active",
        "workflow_visible_on_default_branch": True,
    }
    value.update(updates)
    return WorkflowRegistrationReceipt.from_dict(value)


def _registration_votes(
    mapping: WorkflowBootstrapMapping,
    validator_set: BootstrapValidatorSet,
    keys: tuple[Ed25519PrivateKey, ...],
    receipt: WorkflowRegistrationReceipt,
    evidence: WorkflowRegistrationApiEvidence,
) -> tuple[SignedWorkflowRegistrationVote, ...]:
    submitted_at = datetime(2026, 9, 3, 10, tzinfo=UTC)
    votes = []
    for index, key in enumerate(keys[:3]):
        unsigned = SignedWorkflowRegistrationVote(
            registration_receipt_id=receipt.content_id,
            api_evidence_root=evidence.content_id,
            mapping_id=mapping.content_id,
            validator_set_id=validator_set.content_id,
            registration_run_status=receipt.registration_run_status,
            registration_run_conclusion=receipt.registration_run_conclusion,
            registration_run_created_at=receipt.registration_run_created_at,
            registration_run_updated_at=receipt.registration_run_updated_at,
            registration_run_completed_at=receipt.registration_run_completed_at,
            registration_artifact_name=receipt.registration_artifact_name,
            registration_artifact_created_at=receipt.registration_artifact_created_at,
            registration_artifact_expires_at=receipt.registration_artifact_expires_at,
            signer_id=f"validator-{index}",
            submitted_at=submitted_at,
            signature=b"\0" * 64,
        )
        votes.append(replace(unsigned, signature=key.sign(unsigned.message)))
    return tuple(votes)


def test_signed_mapping_binds_distinct_bootstrap_dispatch_and_source_commits() -> None:
    mapping, validator_set, votes, _keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=votes)
    provenance = _provenance()

    assert provenance.workflow_sha != provenance.github_sha
    assert provenance.workflow_sha != provenance.qualified_source_commit
    assert "definition_id" not in mapping.document
    verify_bootstrap_runtime(verified, provenance)


def test_bootstrap_mapping_never_authorizes_execution() -> None:
    with pytest.raises(Campaign02BootstrapError, match="MAPPING_HEADER_INVALID"):
        _mapping(execution_authorized=True)


def test_verified_mapping_cannot_be_caller_constructed() -> None:
    with pytest.raises(Campaign02BootstrapError, match="CONSTRUCTION_FORBIDDEN"):
        VerifiedBootstrapMapping(object(), _mapping(), _id("8"), ("validator-0",))


def test_wrong_mapping_signature_is_rejected() -> None:
    mapping, validator_set, votes, _keys = _verified_mapping()
    forged = (*votes[:-1], replace(votes[-1], signature=b"x" * 64))
    with pytest.raises(Campaign02BootstrapError, match="SIGNATURE_INVALID"):
        verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=forged)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository", "attacker/repository"),
        ("workflow_sha", "9" * 40),
        ("workflow_blob_id", "9" * 40),
        ("workflow_content_id", _id("9")),
        ("qualified_source_commit", "9" * 40),
        ("qualified_source_tree", "9" * 40),
        ("source_stage_a_workflow_content_id", _id("9")),
        ("dispatch_ref", "refs/heads/dev"),
        ("event_name", "push"),
        ("run_attempt", 0),
    ],
)
def test_runtime_provenance_mismatch_is_rejected(field: str, value: object) -> None:
    mapping, validator_set, votes, _keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=votes)
    provenance = _provenance()
    changed = replace(provenance, **{field: value})
    with pytest.raises(Campaign02BootstrapError, match="RUNTIME_PROVENANCE_INVALID"):
        verify_bootstrap_runtime(verified, changed)


def test_registration_receipt_proves_zero_execution_only() -> None:
    mapping, validator_set, mapping_votes, keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=mapping_votes)
    evidence = _api_evidence(mapping)
    receipt = _registration(mapping, evidence)
    registration_votes = _registration_votes(mapping, validator_set, keys, receipt, evidence)
    attestation = verify_registration_receipt(
        verified,
        receipt,
        api_evidence=evidence,
        validator_set=validator_set,
        votes=registration_votes,
    )
    assert receipt.document["observation_count"] == 0
    assert receipt.document["stage_gate_receipt_emitted"] is False
    assert attestation.signer_ids == ("validator-0", "validator-1", "validator-2")
    assert receipt.registration_run_status == "completed"
    assert receipt.registration_run_conclusion == "success"


@pytest.mark.parametrize(
    ("run_updates", "receipt_updates"),
    [
        ({"conclusion": "failure"}, {}),
        ({"conclusion": "cancelled"}, {}),
        ({"conclusion": "timed_out"}, {}),
        ({"status": "in_progress", "conclusion": None}, {}),
        (
            {"conclusion": "failure"},
            {"registration_run_conclusion": "success"},
        ),
    ],
)
def test_non_successful_registration_run_is_rejected(
    run_updates: dict[str, object], receipt_updates: dict[str, object]
) -> None:
    mapping, validator_set, mapping_votes, keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=mapping_votes)
    evidence = _api_evidence(mapping, run_updates=run_updates)
    receipt = _registration(mapping, evidence, **receipt_updates)
    votes = _registration_votes(mapping, validator_set, keys, receipt, evidence)
    with pytest.raises(Campaign02BootstrapError, match="API_SEMANTICS_INVALID"):
        verify_registration_receipt(
            verified,
            receipt,
            api_evidence=evidence,
            validator_set=validator_set,
            votes=votes,
        )


def test_registration_receipt_before_run_completion_is_rejected() -> None:
    mapping = _mapping()
    evidence = _api_evidence(mapping)
    with pytest.raises(Campaign02BootstrapError, match="REGISTRATION_STOP_INVALID"):
        _registration(mapping, evidence, checked_at="2026-09-03T09:57:59+00:00")


def test_registration_artifact_created_after_receipt_check_is_rejected() -> None:
    mapping = _mapping()
    evidence = _api_evidence(mapping)
    with pytest.raises(Campaign02BootstrapError, match="REGISTRATION_STOP_INVALID"):
        _registration(
            mapping,
            evidence,
            registration_artifact_created_at="2026-09-03T10:00:01+00:00",
        )


def test_registration_artifact_from_prior_failed_attempt_is_rejected() -> None:
    mapping, validator_set, mapping_votes, keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=mapping_votes)
    evidence = _api_evidence(
        mapping,
        artifact_updates={"name": "campaign02-bootstrap-registration-456-attempt-1"},
    )
    receipt = _registration(mapping, evidence)
    votes = _registration_votes(mapping, validator_set, keys, receipt, evidence)
    with pytest.raises(Campaign02BootstrapError, match="API_SEMANTICS_INVALID"):
        verify_registration_receipt(
            verified,
            receipt,
            api_evidence=evidence,
            validator_set=validator_set,
            votes=votes,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authority_bundle_supplied", True),
        ("stage_a_plans_executed", 1),
        ("stage_gate_receipt_emitted", True),
        ("execution_artifact_count", 1),
        ("execution_count", 1),
        ("observation_count", 1),
    ],
)
def test_registration_receipt_containing_execution_is_rejected(field: str, value: object) -> None:
    mapping = _mapping()
    evidence = _api_evidence(mapping)
    with pytest.raises(Campaign02BootstrapError, match="REGISTRATION_STOP_INVALID"):
        _registration(mapping, evidence, **{field: value})


@pytest.mark.parametrize(
    ("evidence", "error"),
    [
        (lambda mapping: _api_evidence(mapping, workflow_updates={"id": 999}), "SEMANTICS"),
        (
            lambda mapping: _api_evidence(
                mapping, workflow_updates={"path": ".github/workflows/other.yml"}
            ),
            "SEMANTICS",
        ),
        (
            lambda mapping: _api_evidence(mapping, workflow_updates={"state": "disabled_manually"}),
            "SEMANTICS",
        ),
        (
            lambda mapping: _api_evidence(mapping, ref_updates={"ref": "refs/heads/dev"}),
            "SEMANTICS",
        ),
        (lambda mapping: _api_evidence(mapping, run_updates={"workflow_id": 999}), "SEMANTICS"),
        (
            lambda mapping: _api_evidence(
                mapping,
                artifact_updates={
                    "workflow_run": {
                        "id": 999,
                        "head_branch": "main",
                        "head_sha": mapping.bootstrap_commit,
                    }
                },
            ),
            "SEMANTICS",
        ),
    ],
)
def test_registration_api_semantic_fabrications_are_rejected(evidence, error: str) -> None:  # type: ignore[no-untyped-def]
    mapping, validator_set, mapping_votes, keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=mapping_votes)
    api_evidence = evidence(mapping)
    receipt = _registration(mapping, api_evidence)
    registration_votes = _registration_votes(mapping, validator_set, keys, receipt, api_evidence)
    with pytest.raises(Campaign02BootstrapError, match=error):
        verify_registration_receipt(
            verified,
            receipt,
            api_evidence=api_evidence,
            validator_set=validator_set,
            votes=registration_votes,
        )


def test_registration_digest_without_raw_api_bytes_is_rejected() -> None:
    mapping = _mapping()
    evidence = _api_evidence(mapping)
    raw = evidence.document
    snapshots = raw["snapshots"]
    assert isinstance(snapshots, dict)
    workflow = snapshots["workflow_metadata"]
    assert isinstance(workflow, dict)
    workflow["response_base64"] = ""
    with pytest.raises(Campaign02BootstrapError, match="DIGEST_MISMATCH"):
        WorkflowRegistrationApiEvidence.from_dict(raw)


def test_caller_constructed_api_snapshot_cannot_bypass_digest_validation() -> None:
    mapping, validator_set, mapping_votes, keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=mapping_votes)
    evidence = _api_evidence(mapping)
    receipt = _registration(mapping, evidence)
    forged = replace(
        evidence,
        workflow_metadata=replace(
            evidence.workflow_metadata,
            response_sha256="sha256:" + "f" * 64,
        ),
    )
    with pytest.raises(Campaign02BootstrapError, match="SNAPSHOT_DIGEST_MISMATCH"):
        verify_registration_receipt(
            verified,
            receipt,
            api_evidence=forged,
            validator_set=validator_set,
            votes=_registration_votes(mapping, validator_set, keys, receipt, evidence),
        )


def test_registration_attestation_signature_is_required_and_verified() -> None:
    mapping, validator_set, mapping_votes, keys = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=mapping_votes)
    evidence = _api_evidence(mapping)
    receipt = _registration(mapping, evidence)
    votes = _registration_votes(mapping, validator_set, keys, receipt, evidence)
    forged = (*votes[:-1], replace(votes[-1], signature=b"x" * 64))
    with pytest.raises(Campaign02BootstrapError, match="SIGNATURE_INVALID"):
        verify_registration_receipt(
            verified,
            receipt,
            api_evidence=evidence,
            validator_set=validator_set,
            votes=forged,
        )
