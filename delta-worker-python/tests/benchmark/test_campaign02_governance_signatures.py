from __future__ import annotations

import base64
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    GovernanceSignatureError,
    SignedDefinitionVote,
    create_definition_vote,
    definition_vote_message,
    finalize_definition_attestation,
    verify_definition_attestation,
    verify_definition_vote,
)
from deltatorrent.protocol.canonical import sha256_content_id

DEFINITION_ID = "sha256:" + "a" * 64
NOW = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _id(label: str) -> str:
    return sha256_content_id(label.encode())


def _validator_material() -> tuple[BenchmarkReviewValidatorSet, tuple[Ed25519PrivateKey, ...]]:
    keys = tuple(Ed25519PrivateKey.generate() for _ in range(4))
    validators = []
    for index, key in enumerate(keys):
        public_key = key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        validators.append(
            {
                "controller_id": f"controller-{index}",
                "key_custody_statement_id": _id(f"custody-{index}"),
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "public_key_id": sha256_content_id(
                    b"deltareduce.010.benchmark-review-key.v1\0" + public_key
                ),
                "signature_algorithm": "ED25519",
                "valid_from": "2026-08-01T00:00:00Z",
                "valid_until": None,
                "validator_id": f"benchmark-validator-{index}",
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
    return validator_set, keys


def _votes() -> tuple[
    BenchmarkReviewValidatorSet,
    tuple[Ed25519PrivateKey, ...],
    tuple[SignedDefinitionVote, ...],
]:
    validator_set, keys = _validator_material()
    votes = tuple(
        create_definition_vote(
            benchmark_definition_id=DEFINITION_ID,
            validator_set=validator_set,
            signer_id=f"benchmark-validator-{index}",
            submitted_at=NOW,
            private_key=keys[index],
        )
        for index in range(3)
    )
    return validator_set, keys, votes


def test_campaign02_detached_votes_form_verified_exact_quorum() -> None:
    validator_set, _, votes = _votes()
    attestation = finalize_definition_attestation(
        benchmark_definition_id=DEFINITION_ID,
        validator_set=validator_set,
        votes=votes,
        verified_at=NOW,
    )
    assert attestation.quorum_threshold == 3
    assert len(attestation.ordered_vote_ids) == 3
    assert attestation.document["independent_approval"] is True
    by_id = {item.content_id: item for item in votes}
    assert (
        verify_definition_attestation(
            attestation.document,
            validator_set=validator_set,
            votes=by_id,
        ).content_id
        == attestation.content_id
    )


def test_campaign02_forged_signature_is_rejected() -> None:
    validator_set, _, votes = _votes()
    forged = replace(
        votes[0], signature=bytes([votes[0].signature[0] ^ 1]) + votes[0].signature[1:]
    )
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_DEFINITION_SIGNATURE_INVALID"):
        verify_definition_vote(forged, validator_set, DEFINITION_ID)


def test_campaign02_vote_for_wrong_definition_is_rejected() -> None:
    validator_set, _, votes = _votes()
    with pytest.raises(
        GovernanceSignatureError, match="BENCHMARK_DEFINITION_VOTE_CONTEXT_MISMATCH"
    ):
        verify_definition_vote(votes[0], validator_set, _id("wrong-definition"))


def test_campaign02_vote_for_wrong_validator_set_is_rejected() -> None:
    _, _, votes = _votes()
    other_set, _ = _validator_material()
    with pytest.raises(
        GovernanceSignatureError, match="BENCHMARK_DEFINITION_VOTE_CONTEXT_MISMATCH"
    ):
        verify_definition_vote(votes[0], other_set, DEFINITION_ID)


def test_campaign02_duplicate_key_and_controller_are_rejected() -> None:
    validator_set, _ = _validator_material()
    duplicate_key = validator_set.document
    validators = duplicate_key["validators"]
    assert isinstance(validators, list)
    validators[1]["public_key"] = validators[0]["public_key"]
    validators[1]["public_key_id"] = validators[0]["public_key_id"]
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_REVIEW_KEY_DUPLICATE"):
        BenchmarkReviewValidatorSet.from_dict(duplicate_key)

    duplicate_controller = validator_set.document
    controllers = duplicate_controller["validators"]
    assert isinstance(controllers, list)
    controllers[1]["controller_id"] = controllers[0]["controller_id"]
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_REVIEW_CONTROLLER_DUPLICATE"):
        BenchmarkReviewValidatorSet.from_dict(duplicate_controller)


def test_campaign02_unknown_custody_statement_identifier_is_rejected() -> None:
    validator_set, _ = _validator_material()
    unknown_custody = validator_set.document
    validators = unknown_custody["validators"]
    assert isinstance(validators, list)
    validators[0]["key_custody_statement_id"] = "unknown-custody-statement"
    with pytest.raises(
        GovernanceSignatureError,
        match="BENCHMARK_REVIEW_KEY_CUSTODY_ID_INVALID",
    ):
        BenchmarkReviewValidatorSet.from_dict(unknown_custody)


def test_campaign02_unknown_signer_is_rejected() -> None:
    validator_set, _, votes = _votes()
    unknown = replace(votes[0], signer_id="benchmark-validator-unknown")
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_REVIEW_SIGNER_UNKNOWN"):
        verify_definition_vote(unknown, validator_set, DEFINITION_ID)


def test_campaign02_insufficient_quorum_is_rejected() -> None:
    validator_set, _, votes = _votes()
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_DEFINITION_QUORUM_INVALID"):
        finalize_definition_attestation(
            benchmark_definition_id=DEFINITION_ID,
            validator_set=validator_set,
            votes=votes[:2],
            verified_at=NOW,
        )


def test_campaign02_signature_over_noncanonical_bytes_is_rejected() -> None:
    validator_set, keys, votes = _votes()
    canonical_message = definition_vote_message(
        DEFINITION_ID,
        validator_set.content_id,
        votes[0].signer_id,
        votes[0].public_key_id,
        votes[0].submitted_at,
    )
    noncanonical_signature = keys[0].sign(canonical_message + b" ")
    noncanonical = replace(votes[0], signature=noncanonical_signature)
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_DEFINITION_SIGNATURE_INVALID"):
        verify_definition_vote(noncanonical, validator_set, DEFINITION_ID)


def test_campaign02_changed_submitted_at_invalidates_signature() -> None:
    validator_set, _, votes = _votes()
    tampered = replace(votes[0], submitted_at=datetime(2026, 9, 1, 12, 1, tzinfo=UTC))
    with pytest.raises(
        GovernanceSignatureError, match="BENCHMARK_DEFINITION_VOTE_MESSAGE_MISMATCH"
    ):
        verify_definition_vote(tampered, validator_set, DEFINITION_ID)


def test_campaign02_duplicate_vote_is_rejected() -> None:
    validator_set, _, votes = _votes()
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_DEFINITION_SIGNER_DUPLICATE"):
        finalize_definition_attestation(
            benchmark_definition_id=DEFINITION_ID,
            validator_set=validator_set,
            votes=(votes[0], votes[0], votes[1]),
            verified_at=NOW,
        )


def test_campaign02_noncanonical_base64_is_rejected() -> None:
    _, _, votes = _votes()
    value = votes[0].document
    value["signature"] = str(value["signature"]).rstrip("=")
    with pytest.raises(GovernanceSignatureError, match="BENCHMARK_DEFINITION_SIGNATURE_INVALID"):
        SignedDefinitionVote.from_dict(value)
