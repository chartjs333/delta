"""Signed benchmark-governance attestations outside runtime certificate lineage."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from deltatorrent.benchmark.canonical import canonical_bytes, content_id, signing_payload
from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
)

_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_PUBLIC_KEY_HEX = re.compile(r"^[0-9a-f]{64}$")
_SIGNATURE_HEX = re.compile(r"^[0-9a-f]{128}$")
_MAX_I64 = (1 << 63) - 1


def _fail(code: str) -> None:
    raise ContractError(code)


def _exact(value: object, fields: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        _fail(code)
    return cast(dict[str, Any], value)


def _identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        _fail(code)
    return cast(str, value)


def _content(value: object, code: str) -> str:
    if not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None:
        _fail(code)
    return cast(str, value)


def _integer(value: object, code: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > _MAX_I64:
        _fail(code)
    return cast(int, value)


def _base(value: dict[str, Any], expected_type: str) -> None:
    if value.get("schema_version") != SCHEMA_VERSION:
        _fail("GOVERNANCE_SCHEMA_VERSION_INVALID")
    if value.get("type_name") != expected_type:
        _fail("GOVERNANCE_TYPE_INVALID")
    if value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID:
        _fail("GOVERNANCE_FORMAL_ID_INVALID")
    if value.get("authority_scope") != AUTHORITY_SCOPE:
        _fail("GOVERNANCE_AUTHORITY_SCOPE_INVALID")
    if value.get("evidence_class") not in {"FOUNDATION_ONLY", "TEST_FIXTURE"}:
        _fail("GOVERNANCE_EVIDENCE_CLASS_INVALID")


@dataclass(frozen=True, slots=True)
class Reviewer:
    signer_id: str
    controller_id: str
    custody_id: str
    key_id: str
    public_key_hex: str
    valid_from_epoch_ms: int
    valid_until_epoch_ms: int

    @classmethod
    def from_dict(cls, value: object) -> Reviewer:
        item = _exact(
            value,
            {
                "controller_id",
                "custody_id",
                "key_id",
                "public_key_hex",
                "signer_id",
                "valid_from_epoch_ms",
                "valid_until_epoch_ms",
            },
            "REVIEWER_FIELDS_INVALID",
        )
        signer_id = _identifier(item["signer_id"], "REVIEWER_SIGNER_ID_INVALID")
        controller_id = _identifier(item["controller_id"], "REVIEWER_CONTROLLER_ID_INVALID")
        custody_id = _identifier(item["custody_id"], "REVIEWER_CUSTODY_ID_INVALID")
        key_id = _content(item["key_id"], "REVIEWER_KEY_ID_INVALID")
        public_key_hex = item["public_key_hex"]
        if not isinstance(public_key_hex, str) or _PUBLIC_KEY_HEX.fullmatch(public_key_hex) is None:
            _fail("REVIEWER_PUBLIC_KEY_INVALID")
        try:
            public_key = bytes.fromhex(public_key_hex)
        except ValueError as exc:
            raise ContractError("REVIEWER_PUBLIC_KEY_INVALID") from exc
        if len(public_key) != 32 or content_id(public_key) != key_id:
            _fail("REVIEWER_PUBLIC_KEY_INVALID")
        valid_from = _integer(item["valid_from_epoch_ms"], "REVIEWER_VALID_FROM_INVALID")
        valid_until = _integer(
            item["valid_until_epoch_ms"], "REVIEWER_VALID_UNTIL_INVALID", minimum=1
        )
        if valid_until <= valid_from:
            _fail("REVIEWER_VALIDITY_WINDOW_INVALID")
        return cls(
            signer_id,
            controller_id,
            custody_id,
            key_id,
            public_key_hex,
            valid_from,
            valid_until,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "controller_id": self.controller_id,
            "custody_id": self.custody_id,
            "key_id": self.key_id,
            "public_key_hex": self.public_key_hex,
            "signer_id": self.signer_id,
            "valid_from_epoch_ms": self.valid_from_epoch_ms,
            "valid_until_epoch_ms": self.valid_until_epoch_ms,
        }


@dataclass(frozen=True, slots=True)
class ReviewerSet:
    f: int
    members: tuple[Reviewer, ...]
    evidence_class: str
    role: str

    @classmethod
    def from_dict(cls, value: object) -> ReviewerSet:
        item = _exact(
            value,
            {
                "authority_scope",
                "evidence_class",
                "f",
                "formal_semantics_id",
                "members",
                "role",
                "schema_version",
                "type_name",
            },
            "REVIEWER_SET_FIELDS_INVALID",
        )
        _base(item, "BENCHMARK_REVIEWER_SET")
        role = item["role"]
        if role not in {"DEFINITION_REVIEWERS", "RESULT_EVALUATORS"}:
            _fail("REVIEWER_SET_ROLE_INVALID")
        f = _integer(item["f"], "REVIEWER_SET_F_INVALID", minimum=1)
        raw_members = item["members"]
        if not isinstance(raw_members, list):
            _fail("REVIEWER_SET_MEMBERS_INVALID")
        members = tuple(Reviewer.from_dict(member) for member in raw_members)
        if len(members) != 3 * f + 1:
            _fail("REVIEWER_SET_CARDINALITY_INVALID")
        if tuple(member.signer_id for member in members) != tuple(
            sorted(member.signer_id for member in members)
        ):
            _fail("REVIEWER_SET_NOT_SORTED")
        for values, code in (
            ((member.signer_id for member in members), "REVIEWER_SIGNER_DUPLICATE"),
            ((member.controller_id for member in members), "REVIEWER_CONTROLLER_DUPLICATE"),
            ((member.custody_id for member in members), "REVIEWER_CUSTODY_DUPLICATE"),
            ((member.key_id for member in members), "REVIEWER_KEY_DUPLICATE"),
        ):
            materialized = tuple(values)
            if len(set(materialized)) != len(materialized):
                _fail(code)
        return cls(
            f=f,
            members=members,
            evidence_class=str(item["evidence_class"]),
            role=str(role),
        )

    @property
    def type_name(self) -> str:
        return "BENCHMARK_REVIEWER_SET"

    @property
    def quorum(self) -> int:
        return 2 * self.f + 1

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_bytes(self.to_dict())

    @property
    def content_id(self) -> str:
        return content_id(self.canonical_bytes)

    def to_dict(self) -> dict[str, object]:
        return {
            "authority_scope": AUTHORITY_SCOPE,
            "evidence_class": self.evidence_class,
            "f": self.f,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "members": [member.to_dict() for member in self.members],
            "role": self.role,
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_REVIEWER_SET",
        }


def unsigned_vote_payload(
    *,
    purpose: str,
    body_id: str,
    reviewer_set_id: str,
    signer_id: str,
    key_id: str,
    decision: str,
    submitted_at_epoch_ms: int,
) -> dict[str, object]:
    if purpose not in {"BENCHMARK_DEFINITION_VOTE", "BENCHMARK_RESULT_VOTE"}:
        _fail("VOTE_PURPOSE_INVALID")
    _content(body_id, "VOTE_BODY_ID_INVALID")
    _content(reviewer_set_id, "VOTE_REVIEWER_SET_ID_INVALID")
    _identifier(signer_id, "VOTE_SIGNER_ID_INVALID")
    _content(key_id, "VOTE_KEY_ID_INVALID")
    if decision not in (
        {"APPROVE"} if purpose == "BENCHMARK_DEFINITION_VOTE" else {"NO_GO", "NOT_EVALUATED"}
    ):
        _fail("VOTE_DECISION_INVALID")
    _integer(submitted_at_epoch_ms, "VOTE_SUBMITTED_AT_INVALID")
    return {
        "body_id": body_id,
        "decision": decision,
        "key_id": key_id,
        "purpose": purpose,
        "reviewer_set_id": reviewer_set_id,
        "signer_id": signer_id,
        "submitted_at_epoch_ms": submitted_at_epoch_ms,
    }


@dataclass(frozen=True, slots=True)
class GovernanceVote:
    body_id: str
    decision: str
    key_id: str
    purpose: str
    reviewer_set_id: str
    signer_id: str
    submitted_at_epoch_ms: int
    signature_hex: str

    @classmethod
    def from_dict(cls, value: object) -> GovernanceVote:
        item = _exact(
            value,
            {
                "body_id",
                "decision",
                "key_id",
                "purpose",
                "reviewer_set_id",
                "signature_hex",
                "signer_id",
                "submitted_at_epoch_ms",
            },
            "VOTE_FIELDS_INVALID",
        )
        payload = unsigned_vote_payload(
            purpose=item["purpose"],
            body_id=item["body_id"],
            reviewer_set_id=item["reviewer_set_id"],
            signer_id=item["signer_id"],
            key_id=item["key_id"],
            decision=item["decision"],
            submitted_at_epoch_ms=item["submitted_at_epoch_ms"],
        )
        signature = item["signature_hex"]
        if not isinstance(signature, str) or _SIGNATURE_HEX.fullmatch(signature) is None:
            _fail("VOTE_SIGNATURE_INVALID")
        try:
            signature_bytes = bytes.fromhex(signature)
        except ValueError as exc:
            raise ContractError("VOTE_SIGNATURE_INVALID") from exc
        if len(signature_bytes) != 64:
            _fail("VOTE_SIGNATURE_INVALID")
        return cls(
            body_id=str(payload["body_id"]),
            decision=str(payload["decision"]),
            key_id=str(payload["key_id"]),
            purpose=str(payload["purpose"]),
            reviewer_set_id=str(payload["reviewer_set_id"]),
            signer_id=str(payload["signer_id"]),
            submitted_at_epoch_ms=cast(int, payload["submitted_at_epoch_ms"]),
            signature_hex=signature,
        )

    @property
    def signing_bytes(self) -> bytes:
        return signing_payload(self.purpose, self.unsigned_dict())

    def unsigned_dict(self) -> dict[str, object]:
        return unsigned_vote_payload(
            purpose=self.purpose,
            body_id=self.body_id,
            reviewer_set_id=self.reviewer_set_id,
            signer_id=self.signer_id,
            key_id=self.key_id,
            decision=self.decision,
            submitted_at_epoch_ms=self.submitted_at_epoch_ms,
        )

    def to_dict(self) -> dict[str, object]:
        return {**self.unsigned_dict(), "signature_hex": self.signature_hex}


def verify_vote(vote: GovernanceVote, reviewer_set: ReviewerSet) -> None:
    if vote.reviewer_set_id != reviewer_set.content_id:
        _fail("VOTE_REVIEWER_SET_MISMATCH")
    matching = [member for member in reviewer_set.members if member.signer_id == vote.signer_id]
    if len(matching) != 1:
        _fail("VOTE_SIGNER_UNKNOWN")
    member = matching[0]
    if member.key_id != vote.key_id:
        _fail("VOTE_KEY_MISMATCH")
    if not member.valid_from_epoch_ms <= vote.submitted_at_epoch_ms < member.valid_until_epoch_ms:
        _fail("VOTE_KEY_EXPIRED")
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(member.public_key_hex)).verify(
            bytes.fromhex(vote.signature_hex), vote.signing_bytes
        )
    except (InvalidSignature, ValueError) as exc:
        raise ContractError("VOTE_SIGNATURE_INVALID") from exc


@dataclass(frozen=True, slots=True)
class GovernanceQC:
    purpose: str
    body_id: str
    decision: str
    reviewer_set_id: str
    votes: tuple[GovernanceVote, ...]
    finalized_at_epoch_ms: int
    evidence_class: str = "TEST_FIXTURE"

    @classmethod
    def finalize(
        cls,
        reviewer_set: ReviewerSet,
        body: CanonicalContract,
        votes: tuple[GovernanceVote, ...],
    ) -> GovernanceQC:
        if not votes:
            _fail("QC_VOTES_MISSING")
        for vote in votes:
            verify_vote(vote, reviewer_set)
        ordered = tuple(sorted(votes, key=lambda vote: vote.signer_id))
        if len({vote.signer_id for vote in ordered}) != len(ordered):
            _fail("QC_SIGNER_DUPLICATE")
        if len(ordered) < reviewer_set.quorum:
            _fail("QC_QUORUM_NOT_REACHED")
        identities = {
            (vote.purpose, vote.body_id, vote.decision, vote.reviewer_set_id) for vote in ordered
        }
        if len(identities) != 1:
            _fail("QC_VOTE_CONTEXT_MISMATCH")
        purpose, body_id, decision, reviewer_set_id = identities.pop()
        if body_id != body.content_id:
            _fail("QC_BODY_ID_MISMATCH")
        body_document = body.to_dict()
        if purpose == "BENCHMARK_DEFINITION_VOTE":
            if body.type_name != "BENCHMARK_DEFINITION":
                _fail("QC_BODY_TYPE_MISMATCH")
            if reviewer_set.role != "DEFINITION_REVIEWERS":
                _fail("QC_REVIEWER_SET_ROLE_MISMATCH")
            declared_set_id = body_document["definition_reviewer_set_id"]
            expected_decision = "APPROVE"
        else:
            if body.type_name != "BENCHMARK_RESULT":
                _fail("QC_BODY_TYPE_MISMATCH")
            if reviewer_set.role != "RESULT_EVALUATORS":
                _fail("QC_REVIEWER_SET_ROLE_MISMATCH")
            declared_set_id = body_document["result_evaluator_set_id"]
            expected_decision = body_document["decision"]
            if expected_decision == "GO":
                _fail("FOUNDATION_RESULT_GO_FORBIDDEN")
        if reviewer_set_id != reviewer_set.content_id or declared_set_id != reviewer_set.content_id:
            _fail("QC_REVIEWER_SET_MISMATCH")
        if decision != expected_decision:
            _fail("QC_DECISION_BODY_MISMATCH")
        return cls(
            purpose=purpose,
            body_id=body_id,
            decision=decision,
            reviewer_set_id=reviewer_set_id,
            votes=ordered,
            finalized_at_epoch_ms=max(vote.submitted_at_epoch_ms for vote in ordered),
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_bytes(self.to_dict())

    @property
    def content_id(self) -> str:
        return content_id(self.canonical_bytes)

    def to_dict(self) -> dict[str, object]:
        qc_type = (
            "BENCHMARK_DEFINITION_QC"
            if self.purpose == "BENCHMARK_DEFINITION_VOTE"
            else "BENCHMARK_RESULT_QC"
        )
        return {
            "authority_scope": AUTHORITY_SCOPE,
            "body_id": self.body_id,
            "decision": self.decision,
            "evidence_class": self.evidence_class,
            "execution_authorized": False,
            "finalized_at_epoch_ms": self.finalized_at_epoch_ms,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "reviewer_set_id": self.reviewer_set_id,
            "runtime_certificate_kind": None,
            "schema_version": SCHEMA_VERSION,
            "type_name": qc_type,
            "votes": [vote.to_dict() for vote in self.votes],
        }


def qc_from_bytes(
    value: bytes,
    reviewer_set: ReviewerSet,
    body: CanonicalContract,
) -> GovernanceQC:
    try:
        document = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("QC_JSON_INVALID") from exc
    item = _exact(
        document,
        {
            "authority_scope",
            "body_id",
            "decision",
            "evidence_class",
            "execution_authorized",
            "finalized_at_epoch_ms",
            "formal_semantics_id",
            "reviewer_set_id",
            "runtime_certificate_kind",
            "schema_version",
            "type_name",
            "votes",
        },
        "QC_FIELDS_INVALID",
    )
    if canonical_bytes(item) != value:
        _fail("QC_BYTES_NOT_CANONICAL")
    _base(item, str(item["type_name"]))
    if item["type_name"] not in {"BENCHMARK_DEFINITION_QC", "BENCHMARK_RESULT_QC"}:
        _fail("QC_TYPE_INVALID")
    if item["execution_authorized"] is not False or item["runtime_certificate_kind"] is not None:
        _fail("QC_RUNTIME_AUTHORITY_FORBIDDEN")
    raw_votes = item["votes"]
    if not isinstance(raw_votes, list):
        _fail("QC_VOTES_INVALID")
    qc = GovernanceQC.finalize(
        reviewer_set,
        body,
        tuple(GovernanceVote.from_dict(vote) for vote in raw_votes),
    )
    if qc.to_dict() != item:
        _fail("QC_DERIVATION_MISMATCH")
    return qc
