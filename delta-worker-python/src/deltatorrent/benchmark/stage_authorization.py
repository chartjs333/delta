"""Signed Campaign 02 stage authorization and typed predecessor-gate contracts.

The benchmark stage decision is governance authority, not a caller-provided
boolean.  Primary execution therefore consumes detached Ed25519 votes and a
canonical attestation, and later stages consume the exact canonical PASS
receipts named by that signed decision.
"""

from __future__ import annotations

import base64
import binascii
import json
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
from deltatorrent.benchmark.governance import BenchmarkReviewValidator
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_STAGES: Final = (
    "STAGE_A_EXACTNESS",
    "STAGE_B_SCIENTIFIC",
    "STAGE_C_EMULATED_WAN",
)
_AUTHORIZATION_FIELDS: Final = {
    "allowed_plan_ids",
    "authorized_stage",
    "authorized_task_ids",
    "benchmark_definition_id",
    "campaign_id",
    "definition_attestation_id",
    "formal_semantics_id",
    "issued_at",
    "plan_catalog_id",
    "real_wan_authorized",
    "required_predecessor_receipt_ids",
    "result_qc_authorized",
    "schema_version",
    "source_commit",
    "source_tree",
    "stage_a_authorized",
    "stage_b_authorized",
    "stage_c_authorized",
    "type_name",
    "validator_set_id",
}
_VALIDATOR_SET_DOMAIN: Final = b"deltareduce.010.stage-authorization-validator-set.v1\0"
_AUTHORIZATION_DOMAIN: Final = b"deltareduce.010.stage-execution-authorization.v2\0"
_VOTE_DOMAIN: Final = b"deltareduce.010.stage-authorization-vote.v1\0"
_VOTE_ID_DOMAIN: Final = b"deltareduce.010.stage-authorization-vote-artifact.v1\0"
_ATTESTATION_DOMAIN: Final = b"deltareduce.010.stage-authorization-attestation.v1\0"
_SIGNATURE_ROOT_DOMAIN: Final = b"deltareduce.010.stage-authorization-signature-set.v1\0"
_GATE_RECEIPT_DOMAIN: Final = b"deltareduce.010.stage-gate-receipt.v1\0"

CAMPAIGN02_STAGE_GATE_ANALYZER_ID: Final = sha256_content_id(
    b"deltareduce.010.campaign02-stage-gate-analyzer.v1\0"
    + canonical_json_bytes(
        {
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "predecessor_policy": "EXACT_TYPED_PASS_RECEIPT",
            "stage_model": "INDEPENDENT_BFT_RUNS",
            "type_name": "CAMPAIGN02_STAGE_GATE_ANALYZER",
        }
    )
)


class StageAuthorizationError(ValueError):
    """Stable fail-closed rejection for Campaign 02 stage governance."""


def _fail(code: str) -> StageAuthorizationError:
    return StageAuthorizationError(code)


def _text(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise _fail(code)
    return value


def _content_id(value: object, code: str) -> str:
    result = _text(value, code)
    if _CONTENT_ID.fullmatch(result) is None:
        raise _fail(code)
    return result


def _commit_id(value: object, code: str) -> str:
    result = _text(value, code)
    if _COMMIT_ID.fullmatch(result) is None:
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


def _content_ids(value: object, code: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise _fail(code)
    result = tuple(_content_id(item, code) for item in value)
    if len(set(result)) != len(result):
        raise _fail(code)
    return result


def _texts(value: object, code: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise _fail(code)
    result = tuple(_text(item, code) for item in value)
    if len(set(result)) != len(result):
        raise _fail(code)
    return result


@dataclass(frozen=True, slots=True)
class StageAuthorizationValidatorSet:
    f_b: int
    validators: tuple[BenchmarkReviewValidator, ...]

    @classmethod
    def from_dict(cls, value: object) -> StageAuthorizationValidatorSet:
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
            raise _fail("CAMPAIGN02_STAGE_VALIDATOR_SET_FIELDS_INVALID")
        if (
            value["type_name"] != "BENCHMARK_STAGE_AUTHORIZATION_VALIDATOR_SET"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["campaign_id"] != "campaign-02"
            or value["purpose"] != "BENCHMARK_STAGE_AUTHORIZATION_REVIEW"
        ):
            raise _fail("CAMPAIGN02_STAGE_VALIDATOR_SET_HEADER_INVALID")
        f_b = value["f_b"]
        raw_validators = value["validators"]
        if (
            isinstance(f_b, bool)
            or not isinstance(f_b, int)
            or f_b < 0
            or not isinstance(raw_validators, list)
        ):
            raise _fail("CAMPAIGN02_STAGE_VALIDATOR_SET_INVALID")
        try:
            validators = tuple(BenchmarkReviewValidator.from_dict(item) for item in raw_validators)
        except ValueError as exc:
            raise _fail(f"CAMPAIGN02_STAGE_VALIDATOR_INVALID:{exc}") from exc
        if len(validators) != 3 * f_b + 1:
            raise _fail("CAMPAIGN02_STAGE_VALIDATOR_SET_INVALID")
        if validators != tuple(sorted(validators, key=lambda item: item.validator_id)):
            raise _fail("CAMPAIGN02_STAGE_VALIDATOR_SET_ORDER_INVALID")
        for identities, code in (
            ({item.validator_id for item in validators}, "CAMPAIGN02_STAGE_VALIDATOR_DUPLICATE"),
            ({item.public_key_id for item in validators}, "CAMPAIGN02_STAGE_KEY_DUPLICATE"),
            ({item.controller_id for item in validators}, "CAMPAIGN02_STAGE_CONTROLLER_DUPLICATE"),
        ):
            if len(identities) != len(validators):
                raise _fail(code)
        return cls(f_b=f_b, validators=validators)

    @property
    def document(self) -> dict[str, object]:
        return {
            "campaign_id": "campaign-02",
            "f_b": self.f_b,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "purpose": "BENCHMARK_STAGE_AUTHORIZATION_REVIEW",
            "schema_version": "1.0.0",
            "type_name": "BENCHMARK_STAGE_AUTHORIZATION_VALIDATOR_SET",
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
        raise _fail("CAMPAIGN02_STAGE_SIGNER_UNKNOWN")


@dataclass(frozen=True, slots=True)
class StageAuthorizationDocument:
    allowed_plan_ids: tuple[str, ...]
    authorized_stage: str
    authorized_task_ids: tuple[str, ...]
    benchmark_definition_id: str
    definition_attestation_id: str
    issued_at: datetime
    plan_catalog_id: str
    required_predecessor_receipt_ids: tuple[str, ...]
    source_commit: str
    source_tree: str
    stage_a_authorized: bool
    stage_b_authorized: bool
    stage_c_authorized: bool
    validator_set_id: str

    @classmethod
    def from_dict(cls, value: object) -> StageAuthorizationDocument:
        if not isinstance(value, dict) or set(value) != _AUTHORIZATION_FIELDS:
            raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_FIELDS_INVALID")
        if (
            value["type_name"] != "BENCHMARK_STAGE_EXECUTION_AUTHORIZATION"
            or value["schema_version"] != "2.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["campaign_id"] != "campaign-02"
            or value["real_wan_authorized"] is not False
            or value["result_qc_authorized"] is not False
        ):
            raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_HEADER_INVALID")
        stage = _text(value["authorized_stage"], "CAMPAIGN02_STAGE_INVALID")
        if stage not in _STAGES:
            raise _fail("CAMPAIGN02_STAGE_INVALID")
        flags = tuple(
            value[key]
            for key in (
                "stage_a_authorized",
                "stage_b_authorized",
                "stage_c_authorized",
            )
        )
        if any(not isinstance(item, bool) for item in flags):
            raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_FLAGS_INVALID")
        predecessors = _content_ids(
            value["required_predecessor_receipt_ids"],
            "CAMPAIGN02_STAGE_PREDECESSOR_INVALID",
            allow_empty=True,
        )
        if predecessors != tuple(sorted(predecessors)):
            raise _fail("CAMPAIGN02_STAGE_PREDECESSOR_INVALID")
        return cls(
            allowed_plan_ids=_content_ids(
                value["allowed_plan_ids"], "CAMPAIGN02_STAGE_ALLOWED_PLAN_IDS_INVALID"
            ),
            authorized_stage=stage,
            authorized_task_ids=_texts(
                value["authorized_task_ids"], "CAMPAIGN02_STAGE_TASK_IDS_INVALID"
            ),
            benchmark_definition_id=_content_id(
                value["benchmark_definition_id"], "CAMPAIGN02_STAGE_DEFINITION_ID_INVALID"
            ),
            definition_attestation_id=_content_id(
                value["definition_attestation_id"],
                "CAMPAIGN02_STAGE_DEFINITION_ATTESTATION_ID_INVALID",
            ),
            issued_at=_timestamp(value["issued_at"], "CAMPAIGN02_STAGE_ISSUED_AT_INVALID"),
            plan_catalog_id=_content_id(
                value["plan_catalog_id"], "CAMPAIGN02_STAGE_PLAN_CATALOG_ID_INVALID"
            ),
            required_predecessor_receipt_ids=predecessors,
            source_commit=_commit_id(
                value["source_commit"], "CAMPAIGN02_STAGE_SOURCE_COMMIT_INVALID"
            ),
            source_tree=_commit_id(value["source_tree"], "CAMPAIGN02_STAGE_SOURCE_TREE_INVALID"),
            stage_a_authorized=flags[0],
            stage_b_authorized=flags[1],
            stage_c_authorized=flags[2],
            validator_set_id=_content_id(
                value["validator_set_id"], "CAMPAIGN02_STAGE_VALIDATOR_SET_ID_INVALID"
            ),
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "allowed_plan_ids": list(self.allowed_plan_ids),
            "authorized_stage": self.authorized_stage,
            "authorized_task_ids": list(self.authorized_task_ids),
            "benchmark_definition_id": self.benchmark_definition_id,
            "campaign_id": "campaign-02",
            "definition_attestation_id": self.definition_attestation_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "issued_at": self.issued_at.isoformat().replace("+00:00", "Z"),
            "plan_catalog_id": self.plan_catalog_id,
            "real_wan_authorized": False,
            "required_predecessor_receipt_ids": list(self.required_predecessor_receipt_ids),
            "result_qc_authorized": False,
            "schema_version": "2.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "stage_a_authorized": self.stage_a_authorized,
            "stage_b_authorized": self.stage_b_authorized,
            "stage_c_authorized": self.stage_c_authorized,
            "type_name": "BENCHMARK_STAGE_EXECUTION_AUTHORIZATION",
            "validator_set_id": self.validator_set_id,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_AUTHORIZATION_DOMAIN + canonical_json_bytes(self.document))


def stage_authorization_vote_message(
    authorization: StageAuthorizationDocument,
    *,
    signer_id: str,
    public_key_id: str,
    submitted_at: datetime,
) -> bytes:
    if submitted_at.tzinfo != UTC:
        raise _fail("CAMPAIGN02_STAGE_VOTE_TIMESTAMP_INVALID")
    payload = {
        **authorization.document,
        "public_key_id": _content_id(public_key_id, "CAMPAIGN02_STAGE_PUBLIC_KEY_ID_INVALID"),
        "purpose": "BENCHMARK_STAGE_AUTHORIZATION_REVIEW",
        "signer_id": _text(signer_id, "CAMPAIGN02_STAGE_SIGNER_ID_INVALID"),
        "stage_authorization_id": authorization.content_id,
        "submitted_at": submitted_at.isoformat().replace("+00:00", "Z"),
    }
    return _VOTE_DOMAIN + canonical_json_bytes(payload)


@dataclass(frozen=True, slots=True)
class SignedStageAuthorizationVote:
    stage_authorization_id: str
    validator_set_id: str
    signer_id: str
    public_key_id: str
    submitted_at: datetime
    signed_message_sha256: str
    signature: bytes

    @classmethod
    def from_dict(cls, value: object) -> SignedStageAuthorizationVote:
        fields = {
            "formal_semantics_id",
            "public_key_id",
            "purpose",
            "schema_version",
            "signature",
            "signature_algorithm",
            "signed_message_sha256",
            "signer_id",
            "stage_authorization_id",
            "submitted_at",
            "type_name",
            "validator_set_id",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_STAGE_VOTE_FIELDS_INVALID")
        if (
            value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["purpose"] != "BENCHMARK_STAGE_AUTHORIZATION_REVIEW"
            or value["schema_version"] != "1.0.0"
            or value["signature_algorithm"] != "ED25519"
            or value["type_name"] != "BENCHMARK_STAGE_AUTHORIZATION_VOTE"
        ):
            raise _fail("CAMPAIGN02_STAGE_VOTE_HEADER_INVALID")
        signature = _base64_bytes(value["signature"], "CAMPAIGN02_STAGE_SIGNATURE_INVALID")
        if len(signature) != 64:
            raise _fail("CAMPAIGN02_STAGE_SIGNATURE_INVALID")
        return cls(
            stage_authorization_id=_content_id(
                value["stage_authorization_id"], "CAMPAIGN02_STAGE_AUTHORIZATION_ID_INVALID"
            ),
            validator_set_id=_content_id(
                value["validator_set_id"], "CAMPAIGN02_STAGE_VALIDATOR_SET_ID_INVALID"
            ),
            signer_id=_text(value["signer_id"], "CAMPAIGN02_STAGE_SIGNER_ID_INVALID"),
            public_key_id=_content_id(
                value["public_key_id"], "CAMPAIGN02_STAGE_PUBLIC_KEY_ID_INVALID"
            ),
            submitted_at=_timestamp(
                value["submitted_at"], "CAMPAIGN02_STAGE_VOTE_TIMESTAMP_INVALID"
            ),
            signed_message_sha256=_content_id(
                value["signed_message_sha256"], "CAMPAIGN02_STAGE_MESSAGE_ID_INVALID"
            ),
            signature=signature,
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "public_key_id": self.public_key_id,
            "purpose": "BENCHMARK_STAGE_AUTHORIZATION_REVIEW",
            "schema_version": "1.0.0",
            "signature": base64.b64encode(self.signature).decode("ascii"),
            "signature_algorithm": "ED25519",
            "signed_message_sha256": self.signed_message_sha256,
            "signer_id": self.signer_id,
            "stage_authorization_id": self.stage_authorization_id,
            "submitted_at": self.submitted_at.isoformat().replace("+00:00", "Z"),
            "type_name": "BENCHMARK_STAGE_AUTHORIZATION_VOTE",
            "validator_set_id": self.validator_set_id,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_VOTE_ID_DOMAIN + canonical_json_bytes(self.document))


def create_stage_authorization_vote(
    *,
    authorization: StageAuthorizationDocument,
    validator_set: StageAuthorizationValidatorSet,
    signer_id: str,
    submitted_at: datetime,
    private_key: Ed25519PrivateKey,
) -> SignedStageAuthorizationVote:
    if authorization.validator_set_id != validator_set.content_id:
        raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_VALIDATOR_SET_MISMATCH")
    validator = validator_set.validator(signer_id)
    message = stage_authorization_vote_message(
        authorization,
        signer_id=signer_id,
        public_key_id=validator.public_key_id,
        submitted_at=submitted_at,
    )
    return SignedStageAuthorizationVote(
        stage_authorization_id=authorization.content_id,
        validator_set_id=validator_set.content_id,
        signer_id=signer_id,
        public_key_id=validator.public_key_id,
        submitted_at=submitted_at,
        signed_message_sha256=sha256_content_id(message),
        signature=private_key.sign(message),
    )


def verify_stage_authorization_vote(
    vote: SignedStageAuthorizationVote,
    *,
    authorization: StageAuthorizationDocument,
    validator_set: StageAuthorizationValidatorSet,
) -> None:
    if (
        vote.stage_authorization_id != authorization.content_id
        or vote.validator_set_id != validator_set.content_id
        or authorization.validator_set_id != validator_set.content_id
    ):
        raise _fail("CAMPAIGN02_STAGE_VOTE_CONTEXT_MISMATCH")
    validator = validator_set.validator(vote.signer_id)
    if vote.public_key_id != validator.public_key_id:
        raise _fail("CAMPAIGN02_STAGE_VOTE_KEY_MISMATCH")
    if vote.submitted_at < authorization.issued_at:
        raise _fail("CAMPAIGN02_STAGE_VOTE_BEFORE_AUTHORIZATION")
    if vote.submitted_at < validator.valid_from or (
        validator.valid_until is not None and vote.submitted_at >= validator.valid_until
    ):
        raise _fail("CAMPAIGN02_STAGE_VOTE_KEY_EXPIRED")
    message = stage_authorization_vote_message(
        authorization,
        signer_id=vote.signer_id,
        public_key_id=vote.public_key_id,
        submitted_at=vote.submitted_at,
    )
    if vote.signed_message_sha256 != sha256_content_id(message):
        raise _fail("CAMPAIGN02_STAGE_VOTE_MESSAGE_MISMATCH")
    try:
        Ed25519PublicKey.from_public_bytes(validator.public_key).verify(vote.signature, message)
    except InvalidSignature as exc:
        raise _fail("CAMPAIGN02_STAGE_SIGNATURE_INVALID") from exc


@dataclass(frozen=True, slots=True)
class VerifiedStageAuthorizationAttestation:
    stage_authorization_id: str
    validator_set_id: str
    f_b: int
    ordered_signers: tuple[str, ...]
    ordered_public_key_ids: tuple[str, ...]
    ordered_vote_ids: tuple[str, ...]
    signature_set_root: str
    verified_at: datetime

    @property
    def quorum_threshold(self) -> int:
        return 2 * self.f_b + 1

    @property
    def document(self) -> dict[str, object]:
        return {
            "f_b": self.f_b,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "governance_only": True,
            "independent_approval": True,
            "ordered_public_key_ids": list(self.ordered_public_key_ids),
            "ordered_signers": list(self.ordered_signers),
            "ordered_vote_ids": list(self.ordered_vote_ids),
            "quorum_threshold": self.quorum_threshold,
            "schema_version": "1.0.0",
            "signature_set_root": self.signature_set_root,
            "stage_authorization_id": self.stage_authorization_id,
            "type_name": "BENCHMARK_STAGE_AUTHORIZATION_ATTESTATION",
            "validator_set_id": self.validator_set_id,
            "verified_at": self.verified_at.isoformat().replace("+00:00", "Z"),
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_ATTESTATION_DOMAIN + canonical_json_bytes(self.document))


def finalize_stage_authorization_attestation(
    *,
    authorization: StageAuthorizationDocument,
    validator_set: StageAuthorizationValidatorSet,
    votes: tuple[SignedStageAuthorizationVote, ...],
    verified_at: datetime,
) -> VerifiedStageAuthorizationAttestation:
    if verified_at.tzinfo != UTC:
        raise _fail("CAMPAIGN02_STAGE_ATTESTATION_TIMESTAMP_INVALID")
    if len(votes) != validator_set.quorum_threshold:
        raise _fail("CAMPAIGN02_STAGE_QUORUM_INVALID")
    for vote in votes:
        verify_stage_authorization_vote(
            vote, authorization=authorization, validator_set=validator_set
        )
        if vote.submitted_at > verified_at:
            raise _fail("CAMPAIGN02_STAGE_VOTE_AFTER_ATTESTATION")
    ordered = tuple(sorted(votes, key=lambda item: item.signer_id))
    for identities, code in (
        ({item.signer_id for item in ordered}, "CAMPAIGN02_STAGE_SIGNER_DUPLICATE"),
        ({item.public_key_id for item in ordered}, "CAMPAIGN02_STAGE_KEY_DUPLICATE"),
        ({item.content_id for item in ordered}, "CAMPAIGN02_STAGE_VOTE_DUPLICATE"),
    ):
        if len(identities) != len(ordered):
            raise _fail(code)
    controllers = {validator_set.validator(item.signer_id).controller_id for item in ordered}
    if len(controllers) != len(ordered):
        raise _fail("CAMPAIGN02_STAGE_CONTROLLER_DUPLICATE")
    vote_ids = tuple(item.content_id for item in ordered)
    signature_set_root = sha256_content_id(
        _SIGNATURE_ROOT_DOMAIN + canonical_json_bytes({"ordered_vote_ids": list(vote_ids)})
    )
    return VerifiedStageAuthorizationAttestation(
        stage_authorization_id=authorization.content_id,
        validator_set_id=validator_set.content_id,
        f_b=validator_set.f_b,
        ordered_signers=tuple(item.signer_id for item in ordered),
        ordered_public_key_ids=tuple(item.public_key_id for item in ordered),
        ordered_vote_ids=vote_ids,
        signature_set_root=signature_set_root,
        verified_at=verified_at,
    )


def verify_stage_authorization_attestation(
    value: object,
    *,
    authorization: StageAuthorizationDocument,
    validator_set: StageAuthorizationValidatorSet,
    votes: Mapping[str, SignedStageAuthorizationVote],
) -> VerifiedStageAuthorizationAttestation:
    fields = {
        "f_b",
        "formal_semantics_id",
        "governance_only",
        "independent_approval",
        "ordered_public_key_ids",
        "ordered_signers",
        "ordered_vote_ids",
        "quorum_threshold",
        "schema_version",
        "signature_set_root",
        "stage_authorization_id",
        "type_name",
        "validator_set_id",
        "verified_at",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise _fail("CAMPAIGN02_STAGE_ATTESTATION_FIELDS_INVALID")
    if (
        value["type_name"] != "BENCHMARK_STAGE_AUTHORIZATION_ATTESTATION"
        or value["schema_version"] != "1.0.0"
        or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
        or value["governance_only"] is not True
        or value["independent_approval"] is not True
        or value["stage_authorization_id"] != authorization.content_id
        or value["validator_set_id"] != validator_set.content_id
        or value["f_b"] != validator_set.f_b
        or value["quorum_threshold"] != validator_set.quorum_threshold
    ):
        raise _fail("CAMPAIGN02_STAGE_ATTESTATION_HEADER_INVALID")
    vote_ids = _content_ids(value["ordered_vote_ids"], "CAMPAIGN02_STAGE_VOTE_IDS_INVALID")
    try:
        selected = tuple(votes[item] for item in vote_ids)
    except KeyError as exc:
        raise _fail("CAMPAIGN02_STAGE_VOTE_MISSING") from exc
    attestation = finalize_stage_authorization_attestation(
        authorization=authorization,
        validator_set=validator_set,
        votes=selected,
        verified_at=_timestamp(
            value["verified_at"], "CAMPAIGN02_STAGE_ATTESTATION_TIMESTAMP_INVALID"
        ),
    )
    if attestation.document != value:
        raise _fail("CAMPAIGN02_STAGE_ATTESTATION_MISMATCH")
    return attestation


@dataclass(frozen=True, slots=True)
class StageAuthorizationProof:
    authorization_document: dict[str, object]
    attestation_document: dict[str, object]
    validator_set: StageAuthorizationValidatorSet
    votes: tuple[SignedStageAuthorizationVote, ...]


@dataclass(frozen=True, slots=True)
class VerifiedStageAuthorization:
    authorization: StageAuthorizationDocument
    attestation: VerifiedStageAuthorizationAttestation

    @property
    def content_id(self) -> str:
        return self.attestation.content_id


def verify_stage_authorization_proof(
    proof: StageAuthorizationProof,
) -> VerifiedStageAuthorization:
    authorization = StageAuthorizationDocument.from_dict(proof.authorization_document)
    if authorization.validator_set_id != proof.validator_set.content_id:
        raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_VALIDATOR_SET_MISMATCH")
    vote_map = {item.content_id: item for item in proof.votes}
    if len(vote_map) != len(proof.votes):
        raise _fail("CAMPAIGN02_STAGE_VOTE_DUPLICATE")
    raw_vote_ids = proof.attestation_document.get("ordered_vote_ids")
    if (
        not isinstance(raw_vote_ids, list)
        or any(not isinstance(item, str) for item in raw_vote_ids)
        or set(raw_vote_ids) != set(vote_map)
        or len(raw_vote_ids) != len(vote_map)
    ):
        raise _fail("CAMPAIGN02_STAGE_VOTE_SET_MISMATCH")
    attestation = verify_stage_authorization_attestation(
        proof.attestation_document,
        authorization=authorization,
        validator_set=proof.validator_set,
        votes=vote_map,
    )
    return VerifiedStageAuthorization(authorization=authorization, attestation=attestation)


@dataclass(frozen=True, slots=True)
class StageGateReceipt:
    accepted_plan_ids: tuple[str, ...]
    benchmark_definition_id: str
    completed_stage: str
    definition_attestation_id: str
    evidence_root: str
    finalized_at: datetime
    gate_analyzer_id: str
    gate_qc_id: str
    gate_result_id: str
    plan_catalog_id: str
    qualified_runtime_lineage_id: str
    required_plan_ids: tuple[str, ...]
    source_commit: str
    source_tree: str
    stage_authorization_attestation_id: str
    decision: str
    runner_id: str | None = None
    runner_environment_id: str | None = None
    runner_implementation_id: str | None = None
    runner_role: str | None = None
    runner_source_class: str | None = None

    @classmethod
    def from_dict(cls, value: object) -> StageGateReceipt:
        common_fields = {
            "accepted_plan_ids",
            "benchmark_definition_id",
            "campaign_id",
            "completed_stage",
            "decision",
            "definition_attestation_id",
            "evidence_root",
            "finalized_at",
            "formal_semantics_id",
            "gate_analyzer_id",
            "gate_qc_id",
            "gate_result_id",
            "plan_catalog_id",
            "qualified_runtime_lineage_id",
            "required_plan_ids",
            "schema_version",
            "source_commit",
            "source_tree",
            "stage_authorization_attestation_id",
            "type_name",
        }
        if not isinstance(value, dict):
            raise _fail("CAMPAIGN02_STAGE_GATE_RECEIPT_FIELDS_INVALID")
        version = value.get("schema_version")
        version_fields = {
            "1.0.0": set(),
            "2.0.0": {"runner_id"},
            "3.0.0": {
                "runner_environment_id",
                "runner_id",
                "runner_implementation_id",
                "runner_role",
                "runner_source_class",
            },
        }
        fields = common_fields | version_fields.get(str(version), set())
        if version not in version_fields or set(value) != fields:
            raise _fail("CAMPAIGN02_STAGE_GATE_RECEIPT_FIELDS_INVALID")
        if (
            value["type_name"] != "BENCHMARK_STAGE_GATE_RECEIPT"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["campaign_id"] != "campaign-02"
            or value["decision"] not in {"PASS", "FAIL"}
        ):
            raise _fail("CAMPAIGN02_STAGE_GATE_RECEIPT_HEADER_INVALID")
        completed_stage = _text(value["completed_stage"], "CAMPAIGN02_GATE_STAGE_INVALID")
        if completed_stage not in _STAGES:
            raise _fail("CAMPAIGN02_GATE_STAGE_INVALID")
        return cls(
            accepted_plan_ids=_content_ids(
                value["accepted_plan_ids"], "CAMPAIGN02_GATE_ACCEPTED_PLANS_INVALID"
            ),
            benchmark_definition_id=_content_id(
                value["benchmark_definition_id"], "CAMPAIGN02_GATE_DEFINITION_ID_INVALID"
            ),
            completed_stage=completed_stage,
            definition_attestation_id=_content_id(
                value["definition_attestation_id"],
                "CAMPAIGN02_GATE_DEFINITION_ATTESTATION_ID_INVALID",
            ),
            evidence_root=_content_id(value["evidence_root"], "CAMPAIGN02_GATE_EVIDENCE_INVALID"),
            finalized_at=_timestamp(value["finalized_at"], "CAMPAIGN02_GATE_FINALIZED_AT_INVALID"),
            gate_analyzer_id=_content_id(
                value["gate_analyzer_id"], "CAMPAIGN02_GATE_ANALYZER_ID_INVALID"
            ),
            gate_qc_id=_content_id(value["gate_qc_id"], "CAMPAIGN02_GATE_QC_ID_INVALID"),
            gate_result_id=_content_id(
                value["gate_result_id"], "CAMPAIGN02_GATE_RESULT_ID_INVALID"
            ),
            plan_catalog_id=_content_id(
                value["plan_catalog_id"], "CAMPAIGN02_GATE_PLAN_CATALOG_ID_INVALID"
            ),
            qualified_runtime_lineage_id=_content_id(
                value["qualified_runtime_lineage_id"],
                "CAMPAIGN02_GATE_RUNTIME_LINEAGE_ID_INVALID",
            ),
            required_plan_ids=_content_ids(
                value["required_plan_ids"], "CAMPAIGN02_GATE_REQUIRED_PLANS_INVALID"
            ),
            source_commit=_commit_id(value["source_commit"], "CAMPAIGN02_GATE_SOURCE_INVALID"),
            source_tree=_commit_id(value["source_tree"], "CAMPAIGN02_GATE_SOURCE_INVALID"),
            stage_authorization_attestation_id=_content_id(
                value["stage_authorization_attestation_id"],
                "CAMPAIGN02_GATE_STAGE_ATTESTATION_ID_INVALID",
            ),
            decision=str(value["decision"]),
            runner_id=(
                _content_id(value["runner_id"], "CAMPAIGN02_GATE_RUNNER_ID_INVALID")
                if version in {"2.0.0", "3.0.0"}
                else None
            ),
            runner_environment_id=(
                _content_id(
                    value["runner_environment_id"],
                    "CAMPAIGN02_GATE_RUNNER_ENVIRONMENT_ID_INVALID",
                )
                if version == "3.0.0"
                else None
            ),
            runner_implementation_id=(
                _content_id(
                    value["runner_implementation_id"],
                    "CAMPAIGN02_GATE_RUNNER_IMPLEMENTATION_ID_INVALID",
                )
                if version == "3.0.0"
                else None
            ),
            runner_role=(
                _text(value["runner_role"], "CAMPAIGN02_GATE_RUNNER_ROLE_INVALID")
                if version == "3.0.0"
                else None
            ),
            runner_source_class=(
                _text(
                    value["runner_source_class"],
                    "CAMPAIGN02_GATE_RUNNER_SOURCE_CLASS_INVALID",
                )
                if version == "3.0.0"
                else None
            ),
        )

    @classmethod
    def from_canonical_bytes(cls, raw: bytes) -> StageGateReceipt:
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _fail("CAMPAIGN02_STAGE_GATE_RECEIPT_CANONICAL_BYTES_INVALID") from exc
        if not isinstance(value, dict) or canonical_json_bytes(value) + b"\n" != raw:
            raise _fail("CAMPAIGN02_STAGE_GATE_RECEIPT_CANONICAL_BYTES_INVALID")
        return cls.from_dict(value)

    @property
    def document(self) -> dict[str, object]:
        document: dict[str, object] = {
            "accepted_plan_ids": list(self.accepted_plan_ids),
            "benchmark_definition_id": self.benchmark_definition_id,
            "campaign_id": "campaign-02",
            "completed_stage": self.completed_stage,
            "decision": self.decision,
            "definition_attestation_id": self.definition_attestation_id,
            "evidence_root": self.evidence_root,
            "finalized_at": self.finalized_at.isoformat().replace("+00:00", "Z"),
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_analyzer_id": self.gate_analyzer_id,
            "gate_qc_id": self.gate_qc_id,
            "gate_result_id": self.gate_result_id,
            "plan_catalog_id": self.plan_catalog_id,
            "qualified_runtime_lineage_id": self.qualified_runtime_lineage_id,
            "required_plan_ids": list(self.required_plan_ids),
            "schema_version": (
                "3.0.0"
                if self.runner_implementation_id is not None
                else "2.0.0"
                if self.runner_id is not None
                else "1.0.0"
            ),
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "stage_authorization_attestation_id": self.stage_authorization_attestation_id,
            "type_name": "BENCHMARK_STAGE_GATE_RECEIPT",
        }
        if self.runner_id is not None:
            document["runner_id"] = self.runner_id
        if self.runner_implementation_id is not None:
            if not all(
                isinstance(item, str) and item
                for item in (
                    self.runner_environment_id,
                    self.runner_role,
                    self.runner_source_class,
                )
            ):
                raise _fail("CAMPAIGN02_GATE_RUNNER_BINDING_INCOMPLETE")
            document.update(
                {
                    "runner_environment_id": self.runner_environment_id,
                    "runner_implementation_id": self.runner_implementation_id,
                    "runner_role": self.runner_role,
                    "runner_source_class": self.runner_source_class,
                }
            )
        return document

    @property
    def content_id(self) -> str:
        domain = (
            b"deltareduce.010.campaign02-stage-gate-receipt.v3\0"
            if self.runner_implementation_id is not None
            else b"deltareduce.010.campaign02-stage-gate-receipt.v2\0"
            if self.runner_id is not None
            else _GATE_RECEIPT_DOMAIN
        )
        return sha256_content_id(domain + canonical_json_bytes(self.document))

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.document) + b"\n"
