"""Immutable data-layer binding assertions for third-party dataset plugins.

Binding assertions are created before model training. They bind one physiological
data window to one concrete intervention event using only stable IDs, offsets,
profile IDs, and content hashes. ModelPlugin code receives only DataPartition
objects and must not create or reinterpret these bindings.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from deltatorrent.data.base import DatasetProviderError

BINDING_ASSERTION_SCHEMA_VERSION = "1.0.0"
BINDING_ASSERTION_TYPE = "DELTAREDUCE_DATA_BINDING_ASSERTION"
VALID_BINDING_RELATIONS: tuple[str, ...] = ("baseline", "post")


class BindingAssertionError(DatasetProviderError):
    """Raised when data binding assertion construction or validation fails."""


def is_sha256_content_id(value: str) -> bool:
    """Return True when value is a canonical sha256 content ID."""
    if not value.startswith("sha256:") or len(value) != 71:
        return False
    try:
        int(value[7:], 16)
    except ValueError:
        return False
    return True


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _content_id(value: dict[str, object]) -> str:
    return f"sha256:{hashlib.sha256(_canonical_bytes(value)).hexdigest()}"


def _binding_payload(
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
) -> dict[str, object]:
    return {
        "acquisition_profile_id": acquisition_profile_id,
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
        "type_name": BINDING_ASSERTION_TYPE,
    }


@dataclass(frozen=True, slots=True)
class BindingAssertion:
    """Content-addressed assertion binding one data window to one event."""

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
    ) -> BindingAssertion:
        """Construct a deterministic assertion and derive its content ID."""
        payload = _binding_payload(
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
        )

    def __post_init__(self) -> None:
        if self.type_name != BINDING_ASSERTION_TYPE:
            raise BindingAssertionError("BINDING_ASSERTION_TYPE_INVALID")
        if self.schema_version != BINDING_ASSERTION_SCHEMA_VERSION:
            raise BindingAssertionError("BINDING_ASSERTION_SCHEMA_VERSION_INVALID")
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

        expected_id = _content_id(self.canonical_payload())
        if self.binding_assertion_id != expected_id:
            raise BindingAssertionError("BINDING_ASSERTION_ID_MISMATCH")

    def canonical_payload(self) -> dict[str, object]:
        """Return assertion body without the derived binding_assertion_id."""
        return _binding_payload(
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
        )

    def ticket_context(self) -> dict[str, object]:
        """Return ModelPlugin/Delta-safe IDs and hashes only."""
        payload = self.canonical_payload()
        return {
            "acquisition_profile_id": payload["acquisition_profile_id"],
            "binding_assertion_id": self.binding_assertion_id,
            "binding_schema_version": payload["schema_version"],
            "data_window_id": payload["data_window_id"],
            "end_offset_ms": payload["end_offset_ms"],
            "intervention_event_id": payload["intervention_event_id"],
            "preprocessing_profile_id": payload["preprocessing_profile_id"],
            "raw_data_hash": payload["raw_data_hash"],
            "relation": payload["relation"],
            "session_id": payload["session_id"],
            "start_offset_ms": payload["start_offset_ms"],
        }
