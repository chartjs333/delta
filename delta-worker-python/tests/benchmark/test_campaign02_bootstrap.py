from __future__ import annotations

import base64
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
    WorkflowBootstrapMapping,
    verify_bootstrap_mapping,
    verify_bootstrap_runtime,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID


def _id(character: str) -> str:
    return "sha256:" + character * 64


def _mapping(**updates: object) -> WorkflowBootstrapMapping:
    value: dict[str, object] = {
        "bootstrap_commit": "1" * 40,
        "bootstrap_workflow_blob_id": "2" * 40,
        "bootstrap_workflow_content_id": _id("3"),
        "bootstrap_workflow_path": ".github/workflows/campaign02-stage-a-bootstrap.yml",
        "definition_id": _id("4"),
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
    keys = [Ed25519PrivateKey.generate() for _ in range(3)]
    validator_set = BootstrapValidatorSet.from_dict(
        {
            "execution_authorized": False,
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
    for index, key in enumerate(keys):
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
    return mapping, validator_set, tuple(votes)


def _provenance() -> BootstrapRuntimeProvenance:
    return BootstrapRuntimeProvenance(
        repository="chartjs333/delta",
        workflow_id=123,
        workflow_path=".github/workflows/campaign02-stage-a-bootstrap.yml",
        workflow_ref=(
            "chartjs333/delta/.github/workflows/campaign02-stage-a-bootstrap.yml@refs/heads/main"
        ),
        workflow_sha="1" * 40,
        workflow_blob_id="2" * 40,
        workflow_content_id=_id("3"),
        run_id=456,
        run_attempt=2,
        event_name="workflow_dispatch",
        dispatch_ref="refs/heads/main",
        github_sha="8" * 40,
        qualified_source_commit="5" * 40,
        qualified_source_tree="6" * 40,
        source_stage_a_workflow_content_id=_id("7"),
    )


def test_signed_mapping_binds_distinct_bootstrap_dispatch_and_source_commits() -> None:
    mapping, validator_set, votes = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=votes)
    provenance = _provenance()

    assert provenance.workflow_sha != provenance.github_sha
    assert provenance.workflow_sha != provenance.qualified_source_commit
    verify_bootstrap_runtime(verified, provenance)


def test_bootstrap_mapping_never_authorizes_execution() -> None:
    with pytest.raises(Campaign02BootstrapError, match="MAPPING_HEADER_INVALID"):
        _mapping(execution_authorized=True)


def test_wrong_mapping_signature_is_rejected() -> None:
    mapping, validator_set, votes = _verified_mapping()
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
    mapping, validator_set, votes = _verified_mapping()
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=votes)
    provenance = _provenance()
    changed = replace(provenance, **{field: value})
    with pytest.raises(Campaign02BootstrapError, match="RUNTIME_PROVENANCE_INVALID"):
        verify_bootstrap_runtime(verified, changed)
