"""Unit tests for immutable data-layer BindingAssertion objects."""

from __future__ import annotations

import pytest
from deltatorrent.data import (
    BINDING_ASSERTION_SCHEMA_VERSION,
    BINDING_ASSERTION_TYPE,
    BindingAssertion,
    BindingAssertionError,
)


def _valid_assertion() -> BindingAssertion:
    return BindingAssertion.create(
        modality="eeg",
        dataset_id="eeg-synthetic-bci-v1",
        session_id="obs-alpha",
        intervention_event_id="evt-alpha",
        data_window_id="eegwin-alpha",
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
        acquisition_profile_id="eeg-250hz-4ch-v1",
        preprocessing_profile_id="bci-standard-4ch-v1",
        raw_data_hash="sha256:" + "1" * 64,
    )


def test_binding_assertion_content_id_is_stable() -> None:
    first = _valid_assertion()
    second = _valid_assertion()

    assert first == second
    assert first.binding_assertion_id == second.binding_assertion_id
    assert first.binding_assertion_id.startswith("sha256:")
    assert first.schema_version == BINDING_ASSERTION_SCHEMA_VERSION
    assert first.type_name == BINDING_ASSERTION_TYPE


def test_binding_assertion_rejects_mismatched_content_id() -> None:
    assertion = _valid_assertion()
    payload = assertion.canonical_payload()

    with pytest.raises(BindingAssertionError, match="BINDING_ASSERTION_ID_MISMATCH"):
        BindingAssertion(
            binding_assertion_id="sha256:" + "0" * 64,
            modality=str(payload["modality"]),
            dataset_id=str(payload["dataset_id"]),
            session_id=str(payload["session_id"]),
            intervention_event_id=str(payload["intervention_event_id"]),
            data_window_id=str(payload["data_window_id"]),
            relation=str(payload["relation"]),
            start_offset_ms=int(payload["start_offset_ms"]),
            end_offset_ms=int(payload["end_offset_ms"]),
            acquisition_profile_id=str(payload["acquisition_profile_id"]),
            preprocessing_profile_id=str(payload["preprocessing_profile_id"]),
            raw_data_hash=str(payload["raw_data_hash"]),
        )


def test_binding_assertion_fail_closed_validation() -> None:
    with pytest.raises(BindingAssertionError, match="BINDING_RELATION_INVALID"):
        BindingAssertion.create(
            modality="eeg",
            dataset_id="eeg-synthetic-bci-v1",
            session_id="obs-alpha",
            intervention_event_id="evt-alpha",
            data_window_id="eegwin-alpha",
            relation="during",
            start_offset_ms=30_000,
            end_offset_ms=60_000,
            acquisition_profile_id="eeg-250hz-4ch-v1",
            preprocessing_profile_id="bci-standard-4ch-v1",
            raw_data_hash="sha256:" + "1" * 64,
        )

    with pytest.raises(BindingAssertionError, match="BINDING_POST_BEFORE_EVENT"):
        BindingAssertion.create(
            modality="eeg",
            dataset_id="eeg-synthetic-bci-v1",
            session_id="obs-alpha",
            intervention_event_id="evt-alpha",
            data_window_id="eegwin-alpha",
            relation="post",
            start_offset_ms=-1,
            end_offset_ms=60_000,
            acquisition_profile_id="eeg-250hz-4ch-v1",
            preprocessing_profile_id="bci-standard-4ch-v1",
            raw_data_hash="sha256:" + "1" * 64,
        )

    with pytest.raises(BindingAssertionError, match="BINDING_RAW_DATA_HASH_INVALID"):
        BindingAssertion.create(
            modality="eeg",
            dataset_id="eeg-synthetic-bci-v1",
            session_id="obs-alpha",
            intervention_event_id="evt-alpha",
            data_window_id="eegwin-alpha",
            relation="baseline",
            start_offset_ms=-120_000,
            end_offset_ms=0,
            acquisition_profile_id="eeg-250hz-4ch-v1",
            preprocessing_profile_id="bci-standard-4ch-v1",
            raw_data_hash="not-a-content-id",
        )


def test_ticket_context_contains_only_delta_safe_ids_and_hashes() -> None:
    context = _valid_assertion().ticket_context()

    assert set(context) == {
        "acquisition_profile_id",
        "binding_assertion_id",
        "binding_schema_version",
        "data_window_id",
        "end_offset_ms",
        "intervention_event_id",
        "preprocessing_profile_id",
        "raw_data_hash",
        "relation",
        "session_id",
        "start_offset_ms",
    }
    assert str(context["binding_assertion_id"]).startswith("sha256:")
    assert context["binding_schema_version"] == BINDING_ASSERTION_SCHEMA_VERSION
    assert "point_id" not in context
    assert "intervention_type" not in context
