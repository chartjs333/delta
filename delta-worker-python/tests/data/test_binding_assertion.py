"""Unit tests for immutable data-layer binding proposals and decisions."""

from __future__ import annotations

import pytest
from deltatorrent.data import (
    BINDING_ASSERTION_SCHEMA_VERSION,
    BINDING_ASSERTION_STATUS_PROPOSED,
    BINDING_ASSERTION_TYPE,
    BINDING_DECISION_ACCEPTED,
    BINDING_DECISION_REJECTED,
    BindingAssertion,
    BindingAssertionError,
    BindingDecision,
    BindingError,
    DeterministicBindingAuthority,
    ResolvedBindingSet,
    ResolvedBindingSetError,
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
        binding_provider_id="provider-rule-v1",
        binding_provider_type="RULE",
    )


def test_binding_assertion_content_id_is_stable_and_proposed() -> None:
    first = _valid_assertion()
    second = _valid_assertion()

    assert first == second
    assert first.binding_assertion_id == second.binding_assertion_id
    assert first.binding_assertion_id.startswith("sha256:")
    assert first.schema_version == BINDING_ASSERTION_SCHEMA_VERSION
    assert first.status == BINDING_ASSERTION_STATUS_PROPOSED
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
            binding_provider_id=str(payload["binding_provider_id"]),
            binding_provider_type=str(payload["binding_provider_type"]),
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
            binding_provider_id="provider-rule-v1",
            binding_provider_type="RULE",
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
            binding_provider_id="provider-rule-v1",
            binding_provider_type="RULE",
        )

    with pytest.raises(BindingAssertionError, match="BINDING_PROVIDER_TYPE_INVALID"):
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
            raw_data_hash="sha256:" + "1" * 64,
            binding_provider_id="provider-rule-v1",
            binding_provider_type="OTHER",
        )


def test_binding_authority_resolves_accepted_context_without_semantics() -> None:
    assertion = _valid_assertion()
    authority = DeterministicBindingAuthority(binding_authority_id="authority-demo-v1")
    resolved = authority.resolve((assertion,))
    decision = resolved.decision_for_assertion_id(assertion.binding_assertion_id)
    context = resolved.ticket_context_for_assertion(assertion)

    assert resolved.resolved_binding_set_id.startswith("sha256:")
    assert resolved.accepted_count == 1
    assert resolved.rejected_count == 0
    assert decision.decision == BINDING_DECISION_ACCEPTED
    assert set(context) == {
        "acquisition_profile_id",
        "binding_assertion_id",
        "binding_authority_id",
        "binding_decision_id",
        "binding_schema_version",
        "data_window_id",
        "intervention_event_id",
        "preprocessing_profile_id",
        "raw_data_hash",
        "resolved_binding_set_id",
        "session_id",
    }
    assert context["binding_schema_version"] == BINDING_ASSERTION_SCHEMA_VERSION
    assert "point_id" not in context
    assert "intervention_type" not in context
    assert "relation" not in context
    assert "start_offset_ms" not in context


def test_rejected_binding_cannot_materialize_ticket_context() -> None:
    assertion = _valid_assertion()
    authority = DeterministicBindingAuthority(
        binding_authority_id="authority-demo-v1",
        default_decision=BINDING_DECISION_REJECTED,
        default_reason_code="DEMO_REJECTED",
    )
    resolved = authority.resolve((assertion,))

    assert resolved.accepted_count == 0
    assert resolved.rejected_count == 1
    with pytest.raises(ResolvedBindingSetError, match="BINDING_ASSERTION_NOT_ACCEPTED"):
        resolved.ticket_context_for_assertion(assertion)


def test_resolved_binding_set_rejects_duplicate_assertion_ids() -> None:
    assertion = _valid_assertion()
    decision = BindingDecision.create(
        binding_assertion_id=assertion.binding_assertion_id,
        binding_authority_id="authority-demo-v1",
        decision=BINDING_DECISION_ACCEPTED,
        reason_code="OK",
    )
    with pytest.raises(ResolvedBindingSetError, match="DUPLICATE_BINDING_ASSERTION_ID"):
        ResolvedBindingSet.create(
            binding_authority_id="authority-demo-v1",
            assertions=(assertion, assertion),
            decisions=(decision,),
        )


def test_resolved_binding_set_rejects_missing_authority_decision_with_binding_error() -> None:
    assertion1 = _valid_assertion()
    payload = assertion1.canonical_payload()
    assertion2 = BindingAssertion.create(
        modality=str(payload["modality"]),
        dataset_id=str(payload["dataset_id"]),
        session_id=str(payload["session_id"]),
        intervention_event_id=str(payload["intervention_event_id"]),
        data_window_id="eegwin-second",
        relation="post",
        start_offset_ms=60_000,
        end_offset_ms=90_000,
        acquisition_profile_id=str(payload["acquisition_profile_id"]),
        preprocessing_profile_id=str(payload["preprocessing_profile_id"]),
        raw_data_hash=str(payload["raw_data_hash"]),
        binding_provider_id=str(payload["binding_provider_id"]),
        binding_provider_type=str(payload["binding_provider_type"]),
    )
    decision1 = BindingDecision.create(
        binding_assertion_id=assertion1.binding_assertion_id,
        binding_authority_id="authority-demo-v1",
        decision=BINDING_DECISION_ACCEPTED,
        reason_code="OK",
    )
    with pytest.raises(BindingError, match="MISSING_BINDING_DECISION") as excinfo:
        ResolvedBindingSet.create(
            binding_authority_id="authority-demo-v1",
            assertions=(assertion1, assertion2),
            decisions=(decision1,),
        )
    assert isinstance(excinfo.value, BindingError)
    assert not isinstance(excinfo.value, KeyError)


def test_resolved_binding_set_rejects_duplicate_accepted_bindings_for_window() -> None:
    assertion1 = _valid_assertion()
    payload = assertion1.canonical_payload()
    assertion2 = BindingAssertion.create(
        modality=str(payload["modality"]),
        dataset_id=str(payload["dataset_id"]),
        session_id=str(payload["session_id"]),
        intervention_event_id=str(payload["intervention_event_id"]),
        data_window_id=str(payload["data_window_id"]),
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
        acquisition_profile_id=str(payload["acquisition_profile_id"]),
        preprocessing_profile_id=str(payload["preprocessing_profile_id"]),
        raw_data_hash=str(payload["raw_data_hash"]),
        binding_provider_id="provider-model-v2",
        binding_provider_type="MODEL",
    )
    decision1 = BindingDecision.create(
        binding_assertion_id=assertion1.binding_assertion_id,
        binding_authority_id="authority-demo-v1",
        decision=BINDING_DECISION_ACCEPTED,
        reason_code="OK1",
    )
    decision2 = BindingDecision.create(
        binding_assertion_id=assertion2.binding_assertion_id,
        binding_authority_id="authority-demo-v1",
        decision=BINDING_DECISION_ACCEPTED,
        reason_code="OK2",
    )
    with pytest.raises(ResolvedBindingSetError, match="DUPLICATE_ACCEPTED_BINDING_FOR_WINDOW"):
        ResolvedBindingSet.create(
            binding_authority_id="authority-demo-v1",
            assertions=(assertion1, assertion2),
            decisions=(decision1, decision2),
        )
