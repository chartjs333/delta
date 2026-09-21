from __future__ import annotations

import copy

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.canonical import content_id, signing_payload
from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
)
from deltatorrent.benchmark.governance import (
    GovernanceQC,
    GovernanceVote,
    ReviewerSet,
    unsigned_vote_payload,
    verify_vote,
)

from .conftest import (
    arm,
    cid,
    definition,
    fault_profile,
    network_profile,
    runtime_identity,
    scientific_profile,
)


def _reviewer_set(
    role: str = "DEFINITION_REVIEWERS",
) -> tuple[ReviewerSet, dict[str, Ed25519PrivateKey]]:
    private_keys: dict[str, Ed25519PrivateKey] = {}
    members: list[dict[str, object]] = []
    for index in range(1, 5):
        signer_id = f"reviewer-{index}"
        private_key = Ed25519PrivateKey.from_private_bytes(bytes([index]) * 32)
        public_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        private_keys[signer_id] = private_key
        members.append(
            {
                "controller_id": f"controller-{index}",
                "custody_id": f"custody-{index}",
                "key_id": content_id(public_bytes),
                "public_key_hex": public_bytes.hex(),
                "signer_id": signer_id,
                "valid_from_epoch_ms": 1000,
                "valid_until_epoch_ms": 10000,
            }
        )
    reviewer_set = ReviewerSet.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "evidence_class": "TEST_FIXTURE",
            "f": 1,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "members": members,
            "role": role,
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_REVIEWER_SET",
        }
    )
    return reviewer_set, private_keys


def _definition_body(reviewer_set: ReviewerSet) -> CanonicalContract:
    runtime = runtime_identity()
    scientific = scientific_profile()
    arms = (
        arm("reference", kind="REFERENCE", topology="FLAT", deployment_profile="EMBEDDED_FFM"),
        arm(
            "candidate",
            kind="DELTAREDUCE",
            topology="HIERARCHICAL",
            deployment_profile="EMBEDDED_FFM",
        ),
    )
    return definition(
        runtime,
        scientific,
        arms,
        (network_profile(),),
        (fault_profile(),),
        definition_reviewer_set_id=reviewer_set.content_id,
    )


def _vote(
    reviewer_set: ReviewerSet,
    private_keys: dict[str, Ed25519PrivateKey],
    signer_id: str,
    *,
    purpose: str = "BENCHMARK_DEFINITION_VOTE",
    decision: str = "APPROVE",
    timestamp: int = 2000,
    body_id: str | None = None,
) -> GovernanceVote:
    member = next(item for item in reviewer_set.members if item.signer_id == signer_id)
    payload = unsigned_vote_payload(
        purpose=purpose,
        body_id=body_id or cid("definition-body"),
        reviewer_set_id=reviewer_set.content_id,
        signer_id=signer_id,
        key_id=member.key_id,
        decision=decision,
        submitted_at_epoch_ms=timestamp,
    )
    signature = private_keys[signer_id].sign(signing_payload(purpose, payload)).hex()
    return GovernanceVote.from_dict({**payload, "signature_hex": signature})


def test_valid_three_of_four_qc_is_deterministic_and_has_no_runtime_authority() -> None:
    reviewer_set, private_keys = _reviewer_set()
    body = _definition_body(reviewer_set)
    votes = tuple(
        _vote(
            reviewer_set,
            private_keys,
            f"reviewer-{index}",
            timestamp=2000 + index,
            body_id=body.content_id,
        )
        for index in (3, 1, 2)
    )
    qc = GovernanceQC.finalize(reviewer_set, body, votes)
    reordered = GovernanceQC.finalize(reviewer_set, body, tuple(reversed(votes)))
    assert qc.canonical_bytes == reordered.canonical_bytes
    assert [vote.signer_id for vote in qc.votes] == ["reviewer-1", "reviewer-2", "reviewer-3"]
    assert qc.finalized_at_epoch_ms == 2003
    assert qc.to_dict()["execution_authorized"] is False
    assert qc.to_dict()["runtime_certificate_kind"] is None


def test_two_of_four_and_duplicate_signer_fail_quorum() -> None:
    reviewer_set, private_keys = _reviewer_set()
    body = _definition_body(reviewer_set)
    first = _vote(reviewer_set, private_keys, "reviewer-1", body_id=body.content_id)
    second = _vote(reviewer_set, private_keys, "reviewer-2", body_id=body.content_id)
    with pytest.raises(ContractError, match="QC_QUORUM_NOT_REACHED"):
        GovernanceQC.finalize(reviewer_set, body, (first, second))
    with pytest.raises(ContractError, match="QC_SIGNER_DUPLICATE"):
        GovernanceQC.finalize(reviewer_set, body, (first, first, second))


def test_aliases_cannot_share_key_controller_or_custody() -> None:
    reviewer_set, _ = _reviewer_set()
    value = reviewer_set.to_dict()
    members = value["members"]
    assert isinstance(members, list)
    members[1]["key_id"] = members[0]["key_id"]
    members[1]["public_key_hex"] = members[0]["public_key_hex"]
    with pytest.raises(ContractError, match="REVIEWER_KEY_DUPLICATE"):
        ReviewerSet.from_dict(value)


def test_crypto_encodings_are_lowercase_and_fixture_go_is_unrepresentable() -> None:
    reviewer_set, _ = _reviewer_set()
    value = reviewer_set.to_dict()
    members = value["members"]
    assert isinstance(members, list)
    members[0]["public_key_hex"] = str(members[0]["public_key_hex"]).upper()
    with pytest.raises(ContractError, match="REVIEWER_PUBLIC_KEY_INVALID"):
        ReviewerSet.from_dict(value)
    member = reviewer_set.members[0]
    with pytest.raises(ContractError, match="VOTE_DECISION_INVALID"):
        unsigned_vote_payload(
            purpose="BENCHMARK_RESULT_VOTE",
            body_id=cid("result"),
            reviewer_set_id=reviewer_set.content_id,
            signer_id=member.signer_id,
            key_id=member.key_id,
            decision="GO",
            submitted_at_epoch_ms=2000,
        )


def test_unknown_expired_mutated_and_cross_purpose_votes_fail() -> None:
    reviewer_set, private_keys = _reviewer_set()
    valid = _vote(reviewer_set, private_keys, "reviewer-1")
    verify_vote(valid, reviewer_set)

    expired_doc = valid.to_dict()
    expired_doc["submitted_at_epoch_ms"] = 10000
    expired_payload = {key: value for key, value in expired_doc.items() if key != "signature_hex"}
    expired_doc["signature_hex"] = (
        private_keys["reviewer-1"]
        .sign(signing_payload("BENCHMARK_DEFINITION_VOTE", expired_payload))
        .hex()
    )
    with pytest.raises(ContractError, match="VOTE_KEY_EXPIRED"):
        verify_vote(GovernanceVote.from_dict(expired_doc), reviewer_set)

    mutated = copy.deepcopy(valid.to_dict())
    mutated["signature_hex"] = "00" * 64
    with pytest.raises(ContractError, match="VOTE_SIGNATURE_INVALID"):
        verify_vote(GovernanceVote.from_dict(mutated), reviewer_set)

    replay = valid.to_dict()
    replay["purpose"] = "BENCHMARK_RESULT_VOTE"
    replay["decision"] = "NO_GO"
    with pytest.raises(ContractError, match="VOTE_SIGNATURE_INVALID"):
        verify_vote(GovernanceVote.from_dict(replay), reviewer_set)


def test_post_qc_body_mutation_cannot_reuse_definition_votes() -> None:
    reviewer_set, private_keys = _reviewer_set()
    body = _definition_body(reviewer_set)
    votes = tuple(
        _vote(reviewer_set, private_keys, f"reviewer-{index}", body_id=body.content_id)
        for index in (1, 2, 3)
    )
    qc = GovernanceQC.finalize(reviewer_set, body, votes)
    assert qc.body_id == body.content_id
    changed_body = body.to_dict()
    changed_body["H"] = int(changed_body["H"]) + 1
    with pytest.raises(ContractError, match="QC_BODY_ID_MISMATCH"):
        GovernanceQC.finalize(
            reviewer_set,
            CanonicalContract.from_dict(changed_body),
            votes,
        )
    changed_vote = votes[0].to_dict()
    changed_vote["body_id"] = cid("mutated-definition-body")
    with pytest.raises(ContractError, match="VOTE_SIGNATURE_INVALID"):
        verify_vote(GovernanceVote.from_dict(changed_vote), reviewer_set)
