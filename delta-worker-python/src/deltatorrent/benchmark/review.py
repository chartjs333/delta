"""Quorum-governed benchmark attestations outside the runtime certificate graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id


class ReviewError(ValueError):
    """Stable rejection for invalid benchmark governance votes."""


@dataclass(frozen=True, slots=True)
class GovernanceVote:
    signer_id: str
    validator_set_id: str
    body_id: str
    purpose: Literal["DEFINITION", "RESULT"]

    @property
    def context_id(self) -> str:
        return sha256_content_id(
            canonical_json_bytes(
                {
                    "body_id": self.body_id,
                    "purpose": self.purpose,
                    "signer_id": self.signer_id,
                    "validator_set_id": self.validator_set_id,
                }
            )
        )


@dataclass(frozen=True, slots=True)
class GovernanceAttestation:
    body_id: str
    validator_set_id: str
    purpose: Literal["DEFINITION", "RESULT"]
    f_b: int
    ordered_signers: tuple[str, ...]

    @classmethod
    def finalize(
        cls,
        *,
        body_id: str,
        validator_set_id: str,
        purpose: Literal["DEFINITION", "RESULT"],
        validator_ids: tuple[str, ...],
        f_b: int,
        votes: tuple[GovernanceVote, ...],
    ) -> GovernanceAttestation:
        if (
            f_b < 0
            or len(validator_ids) != 3 * f_b + 1
            or len(set(validator_ids)) != len(validator_ids)
        ):
            raise ReviewError("BENCHMARK_VALIDATOR_SET_INVALID")
        signers: list[str] = []
        for vote in votes:
            if (
                vote.body_id != body_id
                or vote.validator_set_id != validator_set_id
                or vote.purpose != purpose
            ):
                raise ReviewError("BENCHMARK_VOTE_CONTEXT_MISMATCH")
            if vote.signer_id not in validator_ids:
                raise ReviewError("BENCHMARK_VOTE_SIGNER_INVALID")
            signers.append(vote.signer_id)
        if len(signers) != len(set(signers)):
            raise ReviewError("BENCHMARK_VOTE_DUPLICATE")
        threshold = 2 * f_b + 1
        if len(signers) < threshold:
            raise ReviewError("BENCHMARK_QUORUM_INSUFFICIENT")
        return cls(body_id, validator_set_id, purpose, f_b, tuple(sorted(signers)))

    @property
    def quorum_threshold(self) -> int:
        return 2 * self.f_b + 1

    def to_dict(self, *, decision: str | None = None) -> dict[str, object]:
        common: dict[str, object] = {
            "f_b": self.f_b,
            "formal_semantics_id": (
                "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
            ),
            "governance_only": True,
            "ordered_signers": list(self.ordered_signers),
            "quorum_threshold": self.quorum_threshold,
            "schema_version": "1.0.0",
        }
        if self.purpose == "DEFINITION":
            return {
                **common,
                "benchmark_definition_id": self.body_id,
                "type_name": "BENCHMARK_DEFINITION_ATTESTATION",
                "validator_set_id": self.validator_set_id,
            }
        if decision not in {"GO", "NO_GO"}:
            raise ReviewError("BENCHMARK_RESULT_DECISION_INVALID")
        return {
            **common,
            "benchmark_result_id": self.body_id,
            "decision": decision,
            "evaluator_set_id": self.validator_set_id,
            "protocol_current_transition": False,
            "type_name": "BENCHMARK_RESULT_QC",
        }
