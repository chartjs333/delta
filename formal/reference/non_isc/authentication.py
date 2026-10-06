"""Concrete signature verification under independently selected scope-5 codec.

The return type deliberately does not assert candidate legality, certificate
finality, delivery occurrence, durable source origin or R2 refinement.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto.codec import _require, content_id
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.isc_source.authentication import Bootstrap, registry
from formal.reference.non_isc.codec import (
    ARTIFACT_DOMAIN,
    VOTE_DOMAIN,
    NonIscVote,
    decode_artifact,
    decode_vote,
    preimage,
)

CONTRACT = "bb9fce957dae329701a8cd473a7148e198e1ca12:docs/adr/0015-non-isc-authority-binding-v1.md"


@dataclass(frozen=True)
class AuthorityInputs:
    """Trust-side selection, not a field parsed from a snapshot or Gn.

    The reference selects the exact approved codec source contract. A production
    build/manifest/provisioning verifier is neither represented nor deployed here.
    No supplied 'authentication succeeded' flag is accepted.
    """

    bootstrap: Bootstrap
    codec_contract: str


@dataclass(frozen=True)
class VerifiedSignature:
    original_artifact: bytes
    original_vote: bytes
    vote: NonIscVote
    vote_id: str
    artifact_id: str


def authenticate(
    authority: AuthorityInputs, backend: SodiumReference, raw: bytes
) -> VerifiedSignature:
    _require(type(authority) is AuthorityInputs, "independent authority input")
    _require(authority.codec_contract == CONTRACT, "independent closed codec selection")
    artifact = decode_artifact(raw)
    value = decode_vote(artifact.vote_bytes)
    vote = value.original
    bootstrap = authority.bootstrap
    expected_registry, keys = registry(bootstrap)
    _require(artifact.registry_id == expected_registry, "independent registry binding")
    _require(vote.validator_id in keys, "original validator required")
    key_id, key = keys[vote.validator_id]
    _require(artifact.key_id == key_id, "original key ownership")
    _require(
        vote.formal_semantics_id == bootstrap.formal_semantics_id
        and vote.validator_epoch_id == bootstrap.validator_epoch_id,
        "original epoch/semantics",
    )
    # No opaque callback: use exactly the previously pinned strict primitive.
    _require(type(backend) is SodiumReference, "concrete pinned Ed25519 backend")
    _require(
        backend.verify(
            key,
            preimage(expected_registry, key_id, artifact.vote_bytes),
            artifact.signature,
        ),
        "strict Ed25519 signature",
    )
    return VerifiedSignature(
        raw,
        artifact.vote_bytes,
        value,
        content_id(VOTE_DOMAIN, artifact.vote_bytes),
        content_id(ARTIFACT_DOMAIN, raw),
    )
