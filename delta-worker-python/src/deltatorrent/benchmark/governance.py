"""Cryptographically verified benchmark-definition governance votes.

Private keys never enter repository artifacts.  A Definition attestation is
constructed only from detached Ed25519 votes whose public keys are registered
in one content-addressed validator-set manifest.
"""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_VOTE_DOMAIN: Final = b"deltareduce.010.benchmark-definition-vote.v1\0"
_VOTE_ID_DOMAIN: Final = b"deltareduce.010.benchmark-definition-vote-artifact.v1\0"
_VALIDATOR_SET_DOMAIN: Final = b"deltareduce.010.benchmark-review-validator-set.v1\0"
_KEY_ID_DOMAIN: Final = b"deltareduce.010.benchmark-review-key.v1\0"
_ATTESTATION_DOMAIN: Final = b"deltareduce.010.benchmark-definition-attestation.v2\0"
_SIGNATURE_ROOT_DOMAIN: Final = b"deltareduce.010.benchmark-signature-set.v1\0"


class GovernanceSignatureError(ValueError):
    """Stable fail-closed rejection for signed benchmark governance."""


def _fail(code: str) -> GovernanceSignatureError:
    return GovernanceSignatureError(code)


def _text(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise _fail(code)
    return value


def _content_id(value: object, code: str) -> str:
    result = _text(value, code)
    if _CONTENT_ID.fullmatch(result) is None:
        raise _fail(code)
    return result


def _timestamp(value: object, code: str) -> datetime:
    text = _text(value, code)
    if not text.endswith("Z"):
        raise _fail(code)
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise _fail(code) from exc
    if parsed.tzinfo != UTC or parsed.isoformat().replace("+00:00", "Z") != text:
        raise _fail(code)
    return parsed


def _base64_bytes(value: object, code: str) -> bytes:
    text = _text(value, code)
    try:
        decoded = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise _fail(code) from exc
    if base64.b64encode(decoded).decode("ascii") != text:
        raise _fail(code)
    return decoded


@dataclass(frozen=True, slots=True)
class BenchmarkReviewValidator:
    validator_id: str
    controller_id: str
    public_key_id: str
    public_key: bytes
    key_custody_statement_id: str
    valid_from: datetime
    valid_until: datetime | None

    @classmethod
    def from_dict(cls, value: object) -> BenchmarkReviewValidator:
        fields = {
            "controller_id",
            "key_custody_statement_id",
            "public_key",
            "public_key_id",
            "signature_algorithm",
            "valid_from",
            "valid_until",
            "validator_id",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("BENCHMARK_REVIEW_VALIDATOR_FIELDS_INVALID")
        if value["signature_algorithm"] != "ED25519":
            raise _fail("BENCHMARK_REVIEW_SIGNATURE_ALGORITHM_INVALID")
        public_key = _base64_bytes(value["public_key"], "BENCHMARK_REVIEW_PUBLIC_KEY_INVALID")
        if len(public_key) != 32:
            raise _fail("BENCHMARK_REVIEW_PUBLIC_KEY_INVALID")
        expected_key_id = sha256_content_id(_KEY_ID_DOMAIN + public_key)
        public_key_id = _content_id(
            value["public_key_id"], "BENCHMARK_REVIEW_PUBLIC_KEY_ID_INVALID"
        )
        if public_key_id != expected_key_id:
            raise _fail("BENCHMARK_REVIEW_PUBLIC_KEY_ID_MISMATCH")
        valid_from = _timestamp(value["valid_from"], "BENCHMARK_REVIEW_VALID_FROM_INVALID")
        valid_until_raw = value["valid_until"]
        valid_until = (
            None
            if valid_until_raw is None
            else _timestamp(valid_until_raw, "BENCHMARK_REVIEW_VALID_UNTIL_INVALID")
        )
        if valid_until is not None and valid_until <= valid_from:
            raise _fail("BENCHMARK_REVIEW_KEY_WINDOW_INVALID")
        return cls(
            validator_id=_text(value["validator_id"], "BENCHMARK_REVIEW_VALIDATOR_ID_INVALID"),
            controller_id=_text(value["controller_id"], "BENCHMARK_REVIEW_CONTROLLER_ID_INVALID"),
            public_key_id=public_key_id,
            public_key=public_key,
            key_custody_statement_id=_content_id(
                value["key_custody_statement_id"],
                "BENCHMARK_REVIEW_KEY_CUSTODY_ID_INVALID",
            ),
            valid_from=valid_from,
            valid_until=valid_until,
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "controller_id": self.controller_id,
            "key_custody_statement_id": self.key_custody_statement_id,
            "public_key": base64.b64encode(self.public_key).decode("ascii"),
            "public_key_id": self.public_key_id,
            "signature_algorithm": "ED25519",
            "valid_from": self.valid_from.isoformat().replace("+00:00", "Z"),
            "valid_until": (
                None
                if self.valid_until is None
                else self.valid_until.isoformat().replace("+00:00", "Z")
            ),
            "validator_id": self.validator_id,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkReviewValidatorSet:
    campaign_id: str
    f_b: int
    validators: tuple[BenchmarkReviewValidator, ...]

    @classmethod
    def from_dict(cls, value: object) -> BenchmarkReviewValidatorSet:
        fields = {
            "campaign_id",
            "f_b",
            "formal_semantics_id",
            "purpose",
            "schema_version",
            "type_name",
            "validators",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("BENCHMARK_REVIEW_VALIDATOR_SET_FIELDS_INVALID")
        if (
            value["type_name"] != "BENCHMARK_REVIEW_VALIDATOR_SET"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["campaign_id"] != "campaign-02"
            or value["purpose"] != "BENCHMARK_DEFINITION_REVIEW"
        ):
            raise _fail("BENCHMARK_REVIEW_VALIDATOR_SET_HEADER_INVALID")
        f_b = value["f_b"]
        raw_validators = value["validators"]
        if (
            isinstance(f_b, bool)
            or not isinstance(f_b, int)
            or f_b < 0
            or not isinstance(raw_validators, list)
        ):
            raise _fail("BENCHMARK_REVIEW_VALIDATOR_SET_INVALID")
        validators = tuple(BenchmarkReviewValidator.from_dict(item) for item in raw_validators)
        if len(validators) != 3 * f_b + 1:
            raise _fail("BENCHMARK_REVIEW_VALIDATOR_SET_INVALID")
        if validators != tuple(sorted(validators, key=lambda item: item.validator_id)):
            raise _fail("BENCHMARK_REVIEW_VALIDATOR_SET_ORDER_INVALID")
        for values, code in (
            ({item.validator_id for item in validators}, "BENCHMARK_REVIEW_VALIDATOR_DUPLICATE"),
            ({item.public_key_id for item in validators}, "BENCHMARK_REVIEW_KEY_DUPLICATE"),
            ({item.controller_id for item in validators}, "BENCHMARK_REVIEW_CONTROLLER_DUPLICATE"),
        ):
            if len(values) != len(validators):
                raise _fail(code)
        return cls("campaign-02", f_b, validators)

    @property
    def document(self) -> dict[str, object]:
        return {
            "campaign_id": self.campaign_id,
            "f_b": self.f_b,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "purpose": "BENCHMARK_DEFINITION_REVIEW",
            "schema_version": "1.0.0",
            "type_name": "BENCHMARK_REVIEW_VALIDATOR_SET",
            "validators": [item.document for item in self.validators],
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_VALIDATOR_SET_DOMAIN + canonical_json_bytes(self.document))

    @property
    def quorum_threshold(self) -> int:
        return 2 * self.f_b + 1

    def validator(self, validator_id: str) -> BenchmarkReviewValidator:
        for validator in self.validators:
            if validator.validator_id == validator_id:
                return validator
        raise _fail("BENCHMARK_REVIEW_SIGNER_UNKNOWN")


def definition_vote_message(benchmark_definition_id: str, validator_set_id: str) -> bytes:
    payload = {
        "benchmark_definition_id": _content_id(
            benchmark_definition_id, "BENCHMARK_DEFINITION_ID_INVALID"
        ),
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "purpose": "BENCHMARK_DEFINITION_REVIEW",
        "validator_set_id": _content_id(
            validator_set_id, "BENCHMARK_REVIEW_VALIDATOR_SET_ID_INVALID"
        ),
    }
    return _VOTE_DOMAIN + canonical_json_bytes(payload)


@dataclass(frozen=True, slots=True)
class SignedDefinitionVote:
    benchmark_definition_id: str
    validator_set_id: str
    signer_id: str
    public_key_id: str
    submitted_at: datetime
    signed_message_sha256: str
    signature: bytes

    @classmethod
    def from_dict(cls, value: object) -> SignedDefinitionVote:
        fields = {
            "benchmark_definition_id",
            "formal_semantics_id",
            "public_key_id",
            "purpose",
            "signature",
            "signature_algorithm",
            "signed_message_sha256",
            "signer_id",
            "submitted_at",
            "validator_set_id",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("BENCHMARK_DEFINITION_VOTE_FIELDS_INVALID")
        if (
            value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["purpose"] != "BENCHMARK_DEFINITION_REVIEW"
            or value["signature_algorithm"] != "ED25519"
        ):
            raise _fail("BENCHMARK_DEFINITION_VOTE_HEADER_INVALID")
        signature = _base64_bytes(value["signature"], "BENCHMARK_DEFINITION_SIGNATURE_INVALID")
        if len(signature) != 64:
            raise _fail("BENCHMARK_DEFINITION_SIGNATURE_INVALID")
        return cls(
            benchmark_definition_id=_content_id(
                value["benchmark_definition_id"], "BENCHMARK_DEFINITION_ID_INVALID"
            ),
            validator_set_id=_content_id(
                value["validator_set_id"], "BENCHMARK_REVIEW_VALIDATOR_SET_ID_INVALID"
            ),
            signer_id=_text(value["signer_id"], "BENCHMARK_REVIEW_SIGNER_ID_INVALID"),
            public_key_id=_content_id(
                value["public_key_id"], "BENCHMARK_REVIEW_PUBLIC_KEY_ID_INVALID"
            ),
            submitted_at=_timestamp(
                value["submitted_at"], "BENCHMARK_DEFINITION_VOTE_TIMESTAMP_INVALID"
            ),
            signed_message_sha256=_content_id(
                value["signed_message_sha256"], "BENCHMARK_DEFINITION_MESSAGE_ID_INVALID"
            ),
            signature=signature,
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "benchmark_definition_id": self.benchmark_definition_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "public_key_id": self.public_key_id,
            "purpose": "BENCHMARK_DEFINITION_REVIEW",
            "signature": base64.b64encode(self.signature).decode("ascii"),
            "signature_algorithm": "ED25519",
            "signed_message_sha256": self.signed_message_sha256,
            "signer_id": self.signer_id,
            "submitted_at": self.submitted_at.isoformat().replace("+00:00", "Z"),
            "validator_set_id": self.validator_set_id,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_VOTE_ID_DOMAIN + canonical_json_bytes(self.document))


def create_definition_vote(
    *,
    benchmark_definition_id: str,
    validator_set: BenchmarkReviewValidatorSet,
    signer_id: str,
    submitted_at: datetime,
    private_key: Ed25519PrivateKey,
) -> SignedDefinitionVote:
    if submitted_at.tzinfo != UTC:
        raise _fail("BENCHMARK_DEFINITION_VOTE_TIMESTAMP_INVALID")
    validator = validator_set.validator(signer_id)
    message = definition_vote_message(benchmark_definition_id, validator_set.content_id)
    return SignedDefinitionVote(
        benchmark_definition_id=benchmark_definition_id,
        validator_set_id=validator_set.content_id,
        signer_id=signer_id,
        public_key_id=validator.public_key_id,
        submitted_at=submitted_at,
        signed_message_sha256=sha256_content_id(message),
        signature=private_key.sign(message),
    )


def verify_definition_vote(
    vote: SignedDefinitionVote,
    validator_set: BenchmarkReviewValidatorSet,
    benchmark_definition_id: str,
) -> None:
    if (
        vote.benchmark_definition_id != benchmark_definition_id
        or vote.validator_set_id != validator_set.content_id
    ):
        raise _fail("BENCHMARK_DEFINITION_VOTE_CONTEXT_MISMATCH")
    validator = validator_set.validator(vote.signer_id)
    if vote.public_key_id != validator.public_key_id:
        raise _fail("BENCHMARK_DEFINITION_VOTE_KEY_MISMATCH")
    if vote.submitted_at < validator.valid_from or (
        validator.valid_until is not None and vote.submitted_at >= validator.valid_until
    ):
        raise _fail("BENCHMARK_DEFINITION_VOTE_KEY_EXPIRED")
    message = definition_vote_message(benchmark_definition_id, validator_set.content_id)
    if vote.signed_message_sha256 != sha256_content_id(message):
        raise _fail("BENCHMARK_DEFINITION_VOTE_MESSAGE_MISMATCH")
    try:
        Ed25519PublicKey.from_public_bytes(validator.public_key).verify(vote.signature, message)
    except InvalidSignature as exc:
        raise _fail("BENCHMARK_DEFINITION_SIGNATURE_INVALID") from exc


@dataclass(frozen=True, slots=True)
class VerifiedDefinitionAttestation:
    benchmark_definition_id: str
    validator_set_id: str
    f_b: int
    ordered_signers: tuple[str, ...]
    ordered_vote_ids: tuple[str, ...]
    signature_set_root: str
    verified_at: datetime

    @property
    def quorum_threshold(self) -> int:
        return 2 * self.f_b + 1

    @property
    def document(self) -> dict[str, object]:
        return {
            "benchmark_definition_id": self.benchmark_definition_id,
            "f_b": self.f_b,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "governance_only": True,
            "independent_approval": True,
            "ordered_signers": list(self.ordered_signers),
            "ordered_vote_ids": list(self.ordered_vote_ids),
            "quorum_threshold": self.quorum_threshold,
            "schema_version": "2.0.0",
            "signature_set_root": self.signature_set_root,
            "type_name": "BENCHMARK_DEFINITION_ATTESTATION",
            "validator_set_id": self.validator_set_id,
            "verified_at": self.verified_at.isoformat().replace("+00:00", "Z"),
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_ATTESTATION_DOMAIN + canonical_json_bytes(self.document))


def finalize_definition_attestation(
    *,
    benchmark_definition_id: str,
    validator_set: BenchmarkReviewValidatorSet,
    votes: tuple[SignedDefinitionVote, ...],
    verified_at: datetime,
) -> VerifiedDefinitionAttestation:
    if verified_at.tzinfo != UTC:
        raise _fail("BENCHMARK_DEFINITION_ATTESTATION_TIMESTAMP_INVALID")
    if len(votes) != validator_set.quorum_threshold:
        raise _fail("BENCHMARK_DEFINITION_QUORUM_INVALID")
    for vote in votes:
        verify_definition_vote(vote, validator_set, benchmark_definition_id)
        if vote.submitted_at > verified_at:
            raise _fail("BENCHMARK_DEFINITION_VOTE_AFTER_ATTESTATION")
    ordered = tuple(sorted(votes, key=lambda item: item.signer_id))
    for values, code in (
        ({item.signer_id for item in ordered}, "BENCHMARK_DEFINITION_SIGNER_DUPLICATE"),
        ({item.public_key_id for item in ordered}, "BENCHMARK_DEFINITION_KEY_DUPLICATE"),
        ({item.content_id for item in ordered}, "BENCHMARK_DEFINITION_VOTE_DUPLICATE"),
    ):
        if len(values) != len(ordered):
            raise _fail(code)
    controller_ids = {validator_set.validator(item.signer_id).controller_id for item in ordered}
    if len(controller_ids) != len(ordered):
        raise _fail("BENCHMARK_DEFINITION_CONTROLLER_DUPLICATE")
    vote_ids = tuple(item.content_id for item in ordered)
    signature_set_root = sha256_content_id(
        _SIGNATURE_ROOT_DOMAIN + canonical_json_bytes({"ordered_vote_ids": list(vote_ids)})
    )
    return VerifiedDefinitionAttestation(
        benchmark_definition_id=benchmark_definition_id,
        validator_set_id=validator_set.content_id,
        f_b=validator_set.f_b,
        ordered_signers=tuple(item.signer_id for item in ordered),
        ordered_vote_ids=vote_ids,
        signature_set_root=signature_set_root,
        verified_at=verified_at,
    )


def verify_definition_attestation(
    value: object,
    *,
    validator_set: BenchmarkReviewValidatorSet,
    votes: Mapping[str, SignedDefinitionVote],
) -> VerifiedDefinitionAttestation:
    fields = {
        "benchmark_definition_id",
        "f_b",
        "formal_semantics_id",
        "governance_only",
        "independent_approval",
        "ordered_signers",
        "ordered_vote_ids",
        "quorum_threshold",
        "schema_version",
        "signature_set_root",
        "type_name",
        "validator_set_id",
        "verified_at",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise _fail("BENCHMARK_DEFINITION_ATTESTATION_FIELDS_INVALID")
    if (
        value["type_name"] != "BENCHMARK_DEFINITION_ATTESTATION"
        or value["schema_version"] != "2.0.0"
        or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
        or value["governance_only"] is not True
        or value["independent_approval"] is not True
        or value["validator_set_id"] != validator_set.content_id
        or value["f_b"] != validator_set.f_b
        or value["quorum_threshold"] != validator_set.quorum_threshold
    ):
        raise _fail("BENCHMARK_DEFINITION_ATTESTATION_HEADER_INVALID")
    vote_ids_raw = value["ordered_vote_ids"]
    signer_ids_raw = value["ordered_signers"]
    if (
        not isinstance(vote_ids_raw, list)
        or not isinstance(signer_ids_raw, list)
        or any(not isinstance(item, str) for item in vote_ids_raw)
        or any(not isinstance(item, str) for item in signer_ids_raw)
    ):
        raise _fail("BENCHMARK_DEFINITION_ATTESTATION_QUORUM_INVALID")
    try:
        selected_votes = tuple(
            votes[_content_id(item, "BENCHMARK_DEFINITION_VOTE_ID_INVALID")]
            for item in vote_ids_raw
        )
    except KeyError as exc:
        raise _fail("BENCHMARK_DEFINITION_VOTE_MISSING") from exc
    attestation = finalize_definition_attestation(
        benchmark_definition_id=_content_id(
            value["benchmark_definition_id"], "BENCHMARK_DEFINITION_ID_INVALID"
        ),
        validator_set=validator_set,
        votes=selected_votes,
        verified_at=_timestamp(
            value["verified_at"], "BENCHMARK_DEFINITION_ATTESTATION_TIMESTAMP_INVALID"
        ),
    )
    if attestation.document != value:
        raise _fail("BENCHMARK_DEFINITION_ATTESTATION_MISMATCH")
    return attestation
