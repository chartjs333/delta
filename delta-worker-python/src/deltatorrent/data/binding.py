"""Immutable data-layer binding proposals, decisions, and resolved sets.

Binding is a pre-model data concern. A BindingProvider may be implemented by a
human workflow, deterministic rule, specialized model, or hardware trigger. It
emits immutable PROPOSED BindingAssertion objects. A BindingAuthority reviews
those proposals and emits ACCEPTED/REJECTED/REVIEW decisions. Dataset providers
materialize training partitions only from accepted decisions.

Delta receives only opaque IDs and hashes derived from the resolved binding set.
It does not interpret intervention semantics.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from deltatorrent.data.base import DatasetProviderError

BINDING_ASSERTION_SCHEMA_VERSION = "1.0.0"
BINDING_ASSERTION_TYPE = "DELTAREDUCE_DATA_BINDING_ASSERTION"
BINDING_DECISION_TYPE = "DELTAREDUCE_DATA_BINDING_DECISION"
RESOLVED_BINDING_SET_TYPE = "DELTAREDUCE_RESOLVED_BINDING_SET"
BINDING_ASSERTION_STATUS_PROPOSED = "PROPOSED"
BINDING_DECISION_ACCEPTED = "ACCEPTED"
BINDING_DECISION_REJECTED = "REJECTED"
BINDING_DECISION_REVIEW = "REVIEW"
VALID_BINDING_RELATIONS: tuple[str, ...] = ("baseline", "post")
VALID_BINDING_PROVIDER_TYPES: tuple[str, ...] = ("HUMAN", "RULE", "MODEL", "TRIGGER")
VALID_BINDING_DECISIONS: tuple[str, ...] = (
    BINDING_DECISION_ACCEPTED,
    BINDING_DECISION_REJECTED,
    BINDING_DECISION_REVIEW,
)


class BindingError(DatasetProviderError):
    """Base error for data binding proposals, authorities, and resolutions."""


class BindingAssertionError(BindingError):
    """Raised when data binding assertion construction or validation fails."""


class BindingDecisionError(BindingError):
    """Raised when data binding authority decisions are invalid."""


class ResolvedBindingSetError(BindingError):
    """Raised when a resolved binding set is invalid or incomplete."""


def is_sha256_content_id(value: str) -> bool:
    """Return True when value is a canonical sha256 content ID."""
    if not value.startswith("sha256:") or len(value) != 71:
        return False
    try:
        int(value[7:], 16)
    except ValueError:
        return False
    return True


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _content_id(value: Mapping[str, object]) -> str:
    return f"sha256:{hashlib.sha256(_canonical_bytes(value)).hexdigest()}"


def _assertion_payload(
    *,
    modality: str,
    dataset_id: str,
    session_id: str,
    intervention_event_id: str,
    data_window_id: str,
    relation: str,
    start_offset_ms: int,
    end_offset_ms: int,
    acquisition_profile_id: str,
    preprocessing_profile_id: str,
    raw_data_hash: str,
    binding_provider_id: str,
    binding_provider_type: str,
) -> dict[str, object]:
    return {
        "acquisition_profile_id": acquisition_profile_id,
        "binding_provider_id": binding_provider_id,
        "binding_provider_type": binding_provider_type,
        "data_window_id": data_window_id,
        "dataset_id": dataset_id,
        "end_offset_ms": end_offset_ms,
        "intervention_event_id": intervention_event_id,
        "modality": modality,
        "preprocessing_profile_id": preprocessing_profile_id,
        "raw_data_hash": raw_data_hash,
        "relation": relation,
        "schema_version": BINDING_ASSERTION_SCHEMA_VERSION,
        "session_id": session_id,
        "start_offset_ms": start_offset_ms,
        "status": BINDING_ASSERTION_STATUS_PROPOSED,
        "type_name": BINDING_ASSERTION_TYPE,
    }


@dataclass(frozen=True, slots=True)
class BindingAssertion:
    """Content-addressed PROPOSED assertion binding one data window to one event."""

    binding_assertion_id: str
    modality: str
    dataset_id: str
    session_id: str
    intervention_event_id: str
    data_window_id: str
    relation: str
    start_offset_ms: int
    end_offset_ms: int
    acquisition_profile_id: str
    preprocessing_profile_id: str
    raw_data_hash: str
    binding_provider_id: str
    binding_provider_type: str
    status: str = BINDING_ASSERTION_STATUS_PROPOSED
    schema_version: str = BINDING_ASSERTION_SCHEMA_VERSION
    type_name: str = BINDING_ASSERTION_TYPE

    @classmethod
    def create(
        cls,
        *,
        modality: str,
        dataset_id: str,
        session_id: str,
        intervention_event_id: str,
        data_window_id: str,
        relation: str,
        start_offset_ms: int,
        end_offset_ms: int,
        acquisition_profile_id: str,
        preprocessing_profile_id: str,
        raw_data_hash: str,
        binding_provider_id: str,
        binding_provider_type: str,
    ) -> BindingAssertion:
        """Construct a deterministic proposed assertion and derive its content ID."""
        payload = _assertion_payload(
            modality=modality,
            dataset_id=dataset_id,
            session_id=session_id,
            intervention_event_id=intervention_event_id,
            data_window_id=data_window_id,
            relation=relation,
            start_offset_ms=start_offset_ms,
            end_offset_ms=end_offset_ms,
            acquisition_profile_id=acquisition_profile_id,
            preprocessing_profile_id=preprocessing_profile_id,
            raw_data_hash=raw_data_hash,
            binding_provider_id=binding_provider_id,
            binding_provider_type=binding_provider_type,
        )
        return cls(
            binding_assertion_id=_content_id(payload),
            modality=modality,
            dataset_id=dataset_id,
            session_id=session_id,
            intervention_event_id=intervention_event_id,
            data_window_id=data_window_id,
            relation=relation,
            start_offset_ms=start_offset_ms,
            end_offset_ms=end_offset_ms,
            acquisition_profile_id=acquisition_profile_id,
            preprocessing_profile_id=preprocessing_profile_id,
            raw_data_hash=raw_data_hash,
            binding_provider_id=binding_provider_id,
            binding_provider_type=binding_provider_type,
        )

    def __post_init__(self) -> None:
        if self.type_name != BINDING_ASSERTION_TYPE:
            raise BindingAssertionError("BINDING_ASSERTION_TYPE_INVALID")
        if self.schema_version != BINDING_ASSERTION_SCHEMA_VERSION:
            raise BindingAssertionError("BINDING_ASSERTION_SCHEMA_VERSION_INVALID")
        if self.status != BINDING_ASSERTION_STATUS_PROPOSED:
            raise BindingAssertionError("BINDING_ASSERTION_STATUS_INVALID")
        if not is_sha256_content_id(self.binding_assertion_id):
            raise BindingAssertionError("BINDING_ASSERTION_ID_INVALID")
        if not self.modality:
            raise BindingAssertionError("BINDING_MODALITY_EMPTY")
        if not self.dataset_id:
            raise BindingAssertionError("BINDING_DATASET_ID_EMPTY")
        if not self.session_id:
            raise BindingAssertionError("BINDING_SESSION_ID_EMPTY")
        if not self.intervention_event_id:
            raise BindingAssertionError("BINDING_INTERVENTION_EVENT_ID_EMPTY")
        if not self.data_window_id:
            raise BindingAssertionError("BINDING_DATA_WINDOW_ID_EMPTY")
        if self.relation not in VALID_BINDING_RELATIONS:
            raise BindingAssertionError(f"BINDING_RELATION_INVALID:{self.relation}")
        if type(self.start_offset_ms) is not int or type(self.end_offset_ms) is not int:
            raise BindingAssertionError("BINDING_OFFSETS_NOT_INTEGER")
        if self.end_offset_ms <= self.start_offset_ms:
            raise BindingAssertionError("BINDING_OFFSET_RANGE_INVALID")
        if self.relation == "baseline" and self.end_offset_ms > 0:
            raise BindingAssertionError("BINDING_BASELINE_AFTER_EVENT")
        if self.relation == "post" and self.start_offset_ms < 0:
            raise BindingAssertionError("BINDING_POST_BEFORE_EVENT")
        if not self.acquisition_profile_id:
            raise BindingAssertionError("BINDING_ACQUISITION_PROFILE_ID_EMPTY")
        if not self.preprocessing_profile_id:
            raise BindingAssertionError("BINDING_PREPROCESSING_PROFILE_ID_EMPTY")
        if not is_sha256_content_id(self.raw_data_hash):
            raise BindingAssertionError("BINDING_RAW_DATA_HASH_INVALID")
        if not self.binding_provider_id:
            raise BindingAssertionError("BINDING_PROVIDER_ID_EMPTY")
        if self.binding_provider_type not in VALID_BINDING_PROVIDER_TYPES:
            raise BindingAssertionError(
                f"BINDING_PROVIDER_TYPE_INVALID:{self.binding_provider_type}"
            )

        expected_id = _content_id(self.canonical_payload())
        if self.binding_assertion_id != expected_id:
            raise BindingAssertionError("BINDING_ASSERTION_ID_MISMATCH")

    def canonical_payload(self) -> dict[str, object]:
        """Return assertion body without the derived binding_assertion_id."""
        return _assertion_payload(
            modality=self.modality,
            dataset_id=self.dataset_id,
            session_id=self.session_id,
            intervention_event_id=self.intervention_event_id,
            data_window_id=self.data_window_id,
            relation=self.relation,
            start_offset_ms=self.start_offset_ms,
            end_offset_ms=self.end_offset_ms,
            acquisition_profile_id=self.acquisition_profile_id,
            preprocessing_profile_id=self.preprocessing_profile_id,
            raw_data_hash=self.raw_data_hash,
            binding_provider_id=self.binding_provider_id,
            binding_provider_type=self.binding_provider_type,
        )


def _decision_payload(
    *,
    binding_assertion_id: str,
    binding_authority_id: str,
    decision: str,
    reason_code: str,
) -> dict[str, object]:
    return {
        "binding_assertion_id": binding_assertion_id,
        "binding_authority_id": binding_authority_id,
        "decision": decision,
        "reason_code": reason_code,
        "schema_version": BINDING_ASSERTION_SCHEMA_VERSION,
        "type_name": BINDING_DECISION_TYPE,
    }


@dataclass(frozen=True, slots=True)
class BindingDecision:
    """Immutable authority decision for one proposed BindingAssertion."""

    binding_decision_id: str
    binding_assertion_id: str
    binding_authority_id: str
    decision: str
    reason_code: str
    schema_version: str = BINDING_ASSERTION_SCHEMA_VERSION
    type_name: str = BINDING_DECISION_TYPE

    @classmethod
    def create(
        cls,
        *,
        binding_assertion_id: str,
        binding_authority_id: str,
        decision: str,
        reason_code: str,
    ) -> BindingDecision:
        """Construct a deterministic authority decision."""
        payload = _decision_payload(
            binding_assertion_id=binding_assertion_id,
            binding_authority_id=binding_authority_id,
            decision=decision,
            reason_code=reason_code,
        )
        return cls(
            binding_decision_id=_content_id(payload),
            binding_assertion_id=binding_assertion_id,
            binding_authority_id=binding_authority_id,
            decision=decision,
            reason_code=reason_code,
        )

    def __post_init__(self) -> None:
        if self.type_name != BINDING_DECISION_TYPE:
            raise BindingDecisionError("BINDING_DECISION_TYPE_INVALID")
        if self.schema_version != BINDING_ASSERTION_SCHEMA_VERSION:
            raise BindingDecisionError("BINDING_DECISION_SCHEMA_VERSION_INVALID")
        if not is_sha256_content_id(self.binding_decision_id):
            raise BindingDecisionError("BINDING_DECISION_ID_INVALID")
        if not is_sha256_content_id(self.binding_assertion_id):
            raise BindingDecisionError("BINDING_DECISION_ASSERTION_ID_INVALID")
        if not self.binding_authority_id:
            raise BindingDecisionError("BINDING_AUTHORITY_ID_EMPTY")
        if self.decision not in VALID_BINDING_DECISIONS:
            raise BindingDecisionError(f"BINDING_DECISION_INVALID:{self.decision}")
        if not self.reason_code:
            raise BindingDecisionError("BINDING_DECISION_REASON_EMPTY")

        expected_id = _content_id(self.canonical_payload())
        if self.binding_decision_id != expected_id:
            raise BindingDecisionError("BINDING_DECISION_ID_MISMATCH")

    def canonical_payload(self) -> dict[str, object]:
        """Return decision body without the derived decision ID."""
        return _decision_payload(
            binding_assertion_id=self.binding_assertion_id,
            binding_authority_id=self.binding_authority_id,
            decision=self.decision,
            reason_code=self.reason_code,
        )

    @property
    def accepted(self) -> bool:
        """Return True if this decision allows materialization."""
        return self.decision == BINDING_DECISION_ACCEPTED


def _resolved_set_payload(
    *,
    binding_authority_id: str,
    assertions: Sequence[BindingAssertion],
    decisions: Sequence[BindingDecision],
) -> dict[str, object]:
    decision_map = decisions_by_assertion_id(decisions)
    for assertion in assertions:
        if assertion.binding_assertion_id not in decision_map:
            raise ResolvedBindingSetError(
                f"MISSING_BINDING_DECISION:{assertion.binding_assertion_id}"
            )
    return {
        "accepted_assertion_ids": [
            assertion.binding_assertion_id
            for assertion in assertions
            if decision_map[assertion.binding_assertion_id].accepted
        ],
        "binding_authority_id": binding_authority_id,
        "decision_ids": [decision.binding_decision_id for decision in decisions],
        "schema_version": BINDING_ASSERTION_SCHEMA_VERSION,
        "type_name": RESOLVED_BINDING_SET_TYPE,
    }


def decisions_by_assertion_id(
    decisions: Sequence[BindingDecision],
) -> dict[str, BindingDecision]:
    """Return decisions keyed by assertion ID, rejecting duplicates."""
    by_id: dict[str, BindingDecision] = {}
    for decision in decisions:
        if decision.binding_assertion_id in by_id:
            raise ResolvedBindingSetError(
                f"DUPLICATE_BINDING_DECISION:{decision.binding_assertion_id}"
            )
        by_id[decision.binding_assertion_id] = decision
    return by_id


@dataclass(frozen=True, slots=True)
class ResolvedBindingSet:
    """Deterministic result of applying one BindingAuthority to proposed assertions."""

    resolved_binding_set_id: str
    binding_authority_id: str
    assertions: tuple[BindingAssertion, ...]
    decisions: tuple[BindingDecision, ...]
    schema_version: str = BINDING_ASSERTION_SCHEMA_VERSION
    type_name: str = RESOLVED_BINDING_SET_TYPE

    @classmethod
    def create(
        cls,
        *,
        binding_authority_id: str,
        assertions: Sequence[BindingAssertion],
        decisions: Sequence[BindingDecision],
    ) -> ResolvedBindingSet:
        """Construct a content-addressed resolved set in deterministic order."""
        seen_assertion_ids: set[str] = set()
        for assertion in assertions:
            if assertion.binding_assertion_id in seen_assertion_ids:
                raise ResolvedBindingSetError(
                    f"DUPLICATE_BINDING_ASSERTION_ID:{assertion.binding_assertion_id}"
                )
            seen_assertion_ids.add(assertion.binding_assertion_id)

        decision_map = decisions_by_assertion_id(decisions)
        for assertion in assertions:
            if assertion.binding_assertion_id not in decision_map:
                raise ResolvedBindingSetError(
                    f"MISSING_BINDING_DECISION:{assertion.binding_assertion_id}"
                )
        if len(decision_map) != len(assertions):
            unmatched = set(decision_map.keys()) - seen_assertion_ids
            raise ResolvedBindingSetError(f"UNMATCHED_BINDING_DECISION:{sorted(unmatched)[0]}")

        accepted_window_ids: set[str] = set()
        for assertion in assertions:
            if decision_map[assertion.binding_assertion_id].accepted:
                if assertion.data_window_id in accepted_window_ids:
                    raise ResolvedBindingSetError(
                        f"DUPLICATE_ACCEPTED_BINDING_FOR_WINDOW:{assertion.data_window_id}"
                    )
                accepted_window_ids.add(assertion.data_window_id)

        sorted_assertions = tuple(sorted(assertions, key=lambda item: item.binding_assertion_id))
        sorted_decisions = tuple(sorted(decisions, key=lambda item: item.binding_assertion_id))
        payload = _resolved_set_payload(
            binding_authority_id=binding_authority_id,
            assertions=sorted_assertions,
            decisions=sorted_decisions,
        )
        return cls(
            resolved_binding_set_id=_content_id(payload),
            binding_authority_id=binding_authority_id,
            assertions=sorted_assertions,
            decisions=sorted_decisions,
        )

    def __post_init__(self) -> None:
        if self.type_name != RESOLVED_BINDING_SET_TYPE:
            raise ResolvedBindingSetError("RESOLVED_BINDING_SET_TYPE_INVALID")
        if self.schema_version != BINDING_ASSERTION_SCHEMA_VERSION:
            raise ResolvedBindingSetError("RESOLVED_BINDING_SET_SCHEMA_VERSION_INVALID")
        if not is_sha256_content_id(self.resolved_binding_set_id):
            raise ResolvedBindingSetError("RESOLVED_BINDING_SET_ID_INVALID")
        if not self.binding_authority_id:
            raise ResolvedBindingSetError("RESOLVED_BINDING_AUTHORITY_ID_EMPTY")
        if tuple(sorted(self.assertions, key=lambda item: item.binding_assertion_id)) != tuple(
            self.assertions
        ):
            raise ResolvedBindingSetError("RESOLVED_BINDING_ASSERTIONS_NOT_SORTED")
        if tuple(sorted(self.decisions, key=lambda item: item.binding_assertion_id)) != tuple(
            self.decisions
        ):
            raise ResolvedBindingSetError("RESOLVED_BINDING_DECISIONS_NOT_SORTED")

        seen_assertion_ids: set[str] = set()
        for assertion in self.assertions:
            if assertion.binding_assertion_id in seen_assertion_ids:
                raise ResolvedBindingSetError(
                    f"DUPLICATE_BINDING_ASSERTION_ID:{assertion.binding_assertion_id}"
                )
            seen_assertion_ids.add(assertion.binding_assertion_id)

        decision_by_id = decisions_by_assertion_id(self.decisions)
        for assertion in self.assertions:
            if assertion.binding_assertion_id not in decision_by_id:
                raise ResolvedBindingSetError(
                    f"MISSING_BINDING_DECISION:{assertion.binding_assertion_id}"
                )
        if set(decision_by_id) != seen_assertion_ids:
            raise ResolvedBindingSetError("RESOLVED_BINDING_DECISION_COVERAGE_INVALID")
        if any(
            decision.binding_authority_id != self.binding_authority_id
            for decision in self.decisions
        ):
            raise ResolvedBindingSetError("RESOLVED_BINDING_DECISION_AUTHORITY_MISMATCH")

        accepted_window_ids: set[str] = set()
        for assertion in self.accepted_assertions:
            if assertion.data_window_id in accepted_window_ids:
                raise ResolvedBindingSetError(
                    f"DUPLICATE_ACCEPTED_BINDING_FOR_WINDOW:{assertion.data_window_id}"
                )
            accepted_window_ids.add(assertion.data_window_id)

        expected_id = _content_id(
            _resolved_set_payload(
                binding_authority_id=self.binding_authority_id,
                assertions=self.assertions,
                decisions=self.decisions,
            )
        )
        if self.resolved_binding_set_id != expected_id:
            raise ResolvedBindingSetError("RESOLVED_BINDING_SET_ID_MISMATCH")

    @property
    def accepted_assertions(self) -> tuple[BindingAssertion, ...]:
        """Return assertions accepted by the authority."""
        decision_by_id = decisions_by_assertion_id(self.decisions)
        return tuple(
            assertion
            for assertion in self.assertions
            if decision_by_id[assertion.binding_assertion_id].accepted
        )

    @property
    def accepted_count(self) -> int:
        """Return number of accepted assertions."""
        return len(self.accepted_assertions)

    @property
    def rejected_count(self) -> int:
        """Return number of rejected assertions."""
        return sum(
            1 for decision in self.decisions if decision.decision == BINDING_DECISION_REJECTED
        )

    @property
    def review_count(self) -> int:
        """Return number of assertions routed to review."""
        return sum(1 for decision in self.decisions if decision.decision == BINDING_DECISION_REVIEW)

    def assertion_for_window(self, data_window_id: str) -> BindingAssertion:
        """Return the accepted assertion for a data window or fail closed."""
        accepted = [
            assertion
            for assertion in self.accepted_assertions
            if assertion.data_window_id == data_window_id
        ]
        if len(accepted) != 1:
            raise ResolvedBindingSetError(
                f"ACCEPTED_BINDING_FOR_WINDOW_NOT_UNIQUE:{data_window_id}"
            )
        return accepted[0]

    def decision_for_assertion_id(self, binding_assertion_id: str) -> BindingDecision:
        """Return the decision for an assertion ID."""
        try:
            return decisions_by_assertion_id(self.decisions)[binding_assertion_id]
        except KeyError as exc:
            raise ResolvedBindingSetError(
                f"UNKNOWN_BINDING_ASSERTION_ID:{binding_assertion_id}"
            ) from exc

    def ticket_context_for_assertion(self, assertion: BindingAssertion) -> dict[str, object]:
        """Return Delta-safe ticket metadata for an accepted assertion only."""
        decision = self.decision_for_assertion_id(assertion.binding_assertion_id)
        if not decision.accepted:
            raise ResolvedBindingSetError(
                f"BINDING_ASSERTION_NOT_ACCEPTED:{assertion.data_window_id}"
            )
        return {
            "acquisition_profile_id": assertion.acquisition_profile_id,
            "binding_assertion_id": assertion.binding_assertion_id,
            "binding_authority_id": self.binding_authority_id,
            "binding_decision_id": decision.binding_decision_id,
            "binding_schema_version": assertion.schema_version,
            "data_window_id": assertion.data_window_id,
            "intervention_event_id": assertion.intervention_event_id,
            "preprocessing_profile_id": assertion.preprocessing_profile_id,
            "raw_data_hash": assertion.raw_data_hash,
            "resolved_binding_set_id": self.resolved_binding_set_id,
            "session_id": assertion.session_id,
        }

    def ticket_context_for_window(self, data_window_id: str) -> dict[str, object]:
        """Return ticket metadata for the accepted assertion bound to one data window."""
        return self.ticket_context_for_assertion(self.assertion_for_window(data_window_id))


@runtime_checkable
class BindingProvider(Protocol):
    """Provider contract for immutable binding proposals."""

    @property
    def binding_provider_id(self) -> str:
        """Stable provider identifier."""
        ...

    @property
    def binding_provider_type(self) -> str:
        """One of HUMAN, RULE, MODEL, or TRIGGER."""
        ...

    def propose_bindings(self, observation_session: object) -> tuple[BindingAssertion, ...]:
        """Return immutable PROPOSED assertions for an observation session."""
        ...


@runtime_checkable
class BindingAuthority(Protocol):
    """Authority contract for resolving binding proposals."""

    @property
    def binding_authority_id(self) -> str:
        """Stable authority identifier."""
        ...

    def resolve(self, proposed_assertions: Sequence[BindingAssertion]) -> ResolvedBindingSet:
        """Resolve proposed assertions as ACCEPTED, REJECTED, or REVIEW."""
        ...


@dataclass(frozen=True, slots=True)
class DeterministicBindingAuthority:
    """Small deterministic authority useful for local demos and tests."""

    binding_authority_id: str
    default_decision: str = BINDING_DECISION_ACCEPTED
    default_reason_code: str = "AUTHORITY_RULE_ACCEPTED"
    decision_overrides: Mapping[str, str] = MappingProxyType({})
    reason_overrides: Mapping[str, str] = MappingProxyType({})

    def __post_init__(self) -> None:
        if not self.binding_authority_id:
            raise BindingDecisionError("BINDING_AUTHORITY_ID_EMPTY")
        if self.default_decision not in VALID_BINDING_DECISIONS:
            raise BindingDecisionError(f"BINDING_DECISION_INVALID:{self.default_decision}")
        if not self.default_reason_code:
            raise BindingDecisionError("BINDING_DECISION_REASON_EMPTY")

    def resolve(self, proposed_assertions: Sequence[BindingAssertion]) -> ResolvedBindingSet:
        """Resolve all proposals deterministically using optional per-assertion overrides."""
        sorted_assertions = tuple(
            sorted(proposed_assertions, key=lambda item: item.binding_assertion_id)
        )
        decisions = tuple(
            BindingDecision.create(
                binding_assertion_id=assertion.binding_assertion_id,
                binding_authority_id=self.binding_authority_id,
                decision=str(
                    self.decision_overrides.get(
                        assertion.binding_assertion_id,
                        self.default_decision,
                    )
                ),
                reason_code=str(
                    self.reason_overrides.get(
                        assertion.binding_assertion_id,
                        self.default_reason_code,
                    )
                ),
            )
            for assertion in sorted_assertions
        )
        return ResolvedBindingSet.create(
            binding_authority_id=self.binding_authority_id,
            assertions=sorted_assertions,
            decisions=decisions,
        )
