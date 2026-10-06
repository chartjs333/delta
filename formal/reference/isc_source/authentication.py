"""Concrete ISC cryptographic/source-byte binding, not history-origin authority.

Bootstrap is an independent input on the trust side, never decoded from G or
from a snapshot. Signatures do not establish sender durability or producer legality.
"""

from __future__ import annotations

from dataclasses import dataclass

from formal.reference.isc_crypto.codec import (
    ARTIFACT_DOMAIN,
    EVIDENCE_DOMAIN,
    KEY_DOMAIN,
    REGISTRY_DOMAIN,
    VOTE_DOMAIN,
    Vote,
    _require,
    content_id,
    decode_artifact,
    decode_vote,
    encode_evidence,
    encode_key,
    encode_registry,
    preimage,
)
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.isc_source.identity import Body, body_id, body_preimage, vote_context_id
from formal.reference.isc_w1.codec import Delivery


@dataclass(frozen=True)
class Bootstrap:
    """Only primitive fixed-epoch inputs; no legal-origin/refinement-success flag."""

    formal_semantics_id: str
    origin_id: str
    validator_epoch_id: str
    validators: tuple[tuple[str, bytes], ...]


@dataclass(frozen=True)
class AuthenticatedVote:
    original_artifact: bytes
    original_vote: bytes
    original_body: Body
    vote: Vote
    vote_id: str
    artifact_id: str


def registry(bootstrap: Bootstrap) -> tuple[str, dict[str, tuple[str, bytes]]]:
    _require(type(bootstrap.validators) is tuple, "immutable bootstrap validator set")
    evidence = encode_evidence(bootstrap.formal_semantics_id)
    keys = {}
    validators = []
    resolved = {}
    for validator_id, public_key in bootstrap.validators:
        key = encode_key(public_key)
        key_id = content_id(KEY_DOMAIN, key)
        keys[key_id] = key
        validators.append({"key_ref": key_id, "roles": ["validator"], "validator_id": validator_id})
        resolved[validator_id] = (key_id, public_key)
    document = {
        "evidence_budget_id": content_id(EVIDENCE_DOMAIN, evidence),
        "formal_semantics_id": bootstrap.formal_semantics_id,
        "origin_id": bootstrap.origin_id,
        "quorum_threshold": "3",
        "schema_version": "1.0.0",
        "signature_profile": "SIG-ISC-ED25519-v1",
        "validator_epoch_id": bootstrap.validator_epoch_id,
        "validators": validators,
    }
    raw = encode_registry(document, keys=keys, evidence=evidence)
    return content_id(REGISTRY_DOMAIN, raw), resolved


def authenticate(
    bootstrap: Bootstrap, backend: SodiumReference, raw: bytes, original_body: Body
) -> AuthenticatedVote:
    artifact = decode_artifact(raw)
    vote = decode_vote(artifact.vote_bytes)
    registry_id, validators = registry(bootstrap)
    _require(artifact.registry_id == registry_id, "independent registry binding")
    _require(vote.validator_id in validators, "unknown original validator")
    key_id, key = validators[vote.validator_id]
    _require(artifact.key_id == key_id, "original validator key binding")
    _require(
        vote.formal_semantics_id == bootstrap.formal_semantics_id
        and vote.validator_epoch_id == bootstrap.validator_epoch_id,
        "bootstrap epoch/semantics binding",
    )
    _require(
        vote.formal_semantics_id == original_body.formal_semantics_id
        and vote.height == original_body.height
        and vote.view == original_body.view
        and vote.round_id == original_body.round_id
        and vote.validator_epoch_id == original_body.validator_epoch_id
        and vote.body_hash == body_id(original_body)
        and vote.context_id == vote_context_id(original_body.round_id),
        "original full body/context binding",
    )
    message = preimage(registry_id, key_id, artifact.vote_bytes)
    _require(backend.verify(key, message, artifact.signature), "strict Ed25519 verification")
    return AuthenticatedVote(
        raw,
        artifact.vote_bytes,
        original_body,
        vote,
        content_id(VOTE_DOMAIN, artifact.vote_bytes),
        content_id(ARTIFACT_DOMAIN, raw),
    )


def bind_delivery(verified: AuthenticatedVote, delivery: Delivery) -> None:
    """Check exact duplicate material in W1; relay peer need not be the signer."""
    artifact = decode_artifact(verified.original_artifact)
    _require(
        delivery.vote_frame == verified.original_vote
        and delivery.key_id == artifact.key_id
        and delivery.signature_bytes == artifact.signature
        and delivery.signed_payload
        == preimage(artifact.registry_id, artifact.key_id, artifact.vote_bytes),
        "original W1 delivery bytes mismatch",
    )


def delivered_signers(body: Body, inventory: tuple[AuthenticatedVote, ...]) -> tuple[str, ...]:
    """All matching original signers; no first-q choice, arrival ordering or new IDs.

    Caller retains every authenticated source event. This projection alone is
    neither proof of delivery occurrence nor a FinalizeISC production transition.
    """
    target, exact = body_id(body), body_preimage(body)
    return tuple(
        sorted(
            {
                value.vote.validator_id
                for value in inventory
                if value.vote.body_hash == target and body_preimage(value.original_body) == exact
            }
        )
    )
