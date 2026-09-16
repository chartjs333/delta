"""Unit tests for EegWindowDatasetProvider, DataWindow, and EEG signal preprocessing."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pytest
from deltatorrent.data import (
    BINDING_ASSERTION_SCHEMA_VERSION,
    BINDING_DECISION_ACCEPTED,
    BINDING_DECISION_REJECTED,
    DEFAULT_EEG_ACQUISITION_PROFILE_ID,
    DEFAULT_EEG_PROFILE,
    EEG_DATASET_DESCRIPTOR,
    BindingAssertion,
    BindingDecision,
    DataPartition,
    DatasetProvider,
    DataWindow,
    DeterministicBindingAuthority,
    EegBandpowerResponseAnalyzer,
    EegDataError,
    EegPreprocessingProfile,
    EegWindow,
    EegWindowBindingProvider,
    EegWindowDatasetProvider,
    InterventionEvent,
    ObservationSession,
    ResolvedBindingSet,
    ResolvedBindingSetError,
    ResponseAnalysisInput,
    eeg_raw_data_hash,
)
from deltatorrent.data.eeg import (
    DEFAULT_EEG_PROFILE_ID,
    DEMO_EEG_PARTITIONS,
    EEG_DATASET_ID,
    compute_window_bandpower,
    generate_synthetic_raw_eeg,
)


def test_eeg_provider_descriptor() -> None:
    provider = EegWindowDatasetProvider()
    assert isinstance(provider, DatasetProvider)
    assert provider.dataset_id == "eeg-synthetic-bci-v1"
    desc = provider.descriptor()
    assert desc == EEG_DATASET_DESCRIPTOR
    assert desc.sample_kind == "eeg/bandpower-4ch-4band"
    assert desc.target_kind == "class-id/0-1"
    assert desc.deterministic is True


def test_eeg_preprocessing_profile_validation() -> None:
    with pytest.raises(EegDataError, match="INVALID_SAMPLING_RATE"):
        EegPreprocessingProfile(
            profile_id="bad-fs",
            sampling_rate_hz=0,
            channels=("C3", "C4"),
            frequency_bands=(("alpha", 8.0, 13.0),),
            window_samples=250,
            window_overlap_samples=125,
        )

    with pytest.raises(EegDataError, match="WINDOWS_PER_SESSION_INVALID"):
        EegWindowDatasetProvider(windows_per_session=0)


def test_data_window_validation() -> None:
    profile = DEFAULT_EEG_PROFILE

    with pytest.raises(EegDataError, match="WINDOW_ID_EMPTY"):
        DataWindow(
            window_id="",
            session_id="session-alpha",
            start_sample=0,
            end_sample=profile.window_samples,
            channels=profile.channels,
            preprocessing_profile_id=profile.profile_id,
        )

    with pytest.raises(EegDataError, match="WINDOW_SAMPLE_RANGE_INVALID"):
        DataWindow(
            window_id="win-bad",
            session_id="session-alpha",
            start_sample=100,
            end_sample=100,
            channels=profile.channels,
            preprocessing_profile_id=profile.profile_id,
        )

    with pytest.raises(EegDataError, match="EMPTY_CHANNELS"):
        EegPreprocessingProfile(
            profile_id="no-channels",
            sampling_rate_hz=250,
            channels=(),
            frequency_bands=(("alpha", 8.0, 13.0),),
            window_samples=250,
            window_overlap_samples=125,
        )

    with pytest.raises(EegDataError, match="INVALID_WINDOW_OVERLAP"):
        EegPreprocessingProfile(
            profile_id="bad-overlap",
            sampling_rate_hz=250,
            channels=("C3",),
            frequency_bands=(("alpha", 8.0, 13.0),),
            window_samples=250,
            window_overlap_samples=250,
        )


def _intervention_event(
    event_id: str,
    *,
    session_id: str = "obs-alpha",
    point_id: str = "TCM-ST36",
) -> InterventionEvent:
    return InterventionEvent(
        intervention_event_id=event_id,
        session_id=session_id,
        intervention_type="acupuncture_injection",
        point_id=point_id,
        laterality="left",
        timestamp_ms=1_800_000_000_000,
        operator_id="operator-001",
        protocol_id="protocol-st36-v1",
        substance_id="substance-saline-v1",
    )


def _eeg_window(
    window_id: str,
    event_id: str,
    *,
    relation: str,
    session_id: str = "obs-alpha",
    start_offset_ms: int,
    end_offset_ms: int,
    raw_data_hash: str = "sha256:" + "1" * 64,
) -> EegWindow:
    profile = DEFAULT_EEG_PROFILE
    return EegWindow(
        window_id=window_id,
        session_id=session_id,
        intervention_event_id=event_id,
        relation=relation,
        start_offset_ms=start_offset_ms,
        end_offset_ms=end_offset_ms,
        acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
        preprocessing_profile_id=profile.profile_id,
        raw_data_hash=raw_data_hash,
        start_sample=0,
        end_sample=profile.window_samples,
        channels=profile.channels,
    )


def _accepted_binding_for_window(
    window: EegWindow,
) -> tuple[BindingAssertion, ResolvedBindingSet]:
    assertion = BindingAssertion.create(
        modality="eeg",
        dataset_id="eeg-synthetic-bci-v1",
        session_id=window.session_id,
        intervention_event_id=window.intervention_event_id,
        data_window_id=window.window_id,
        relation=window.relation,
        start_offset_ms=window.start_offset_ms,
        end_offset_ms=window.end_offset_ms,
        acquisition_profile_id=window.acquisition_profile_id,
        preprocessing_profile_id=window.preprocessing_profile_id,
        raw_data_hash=window.raw_data_hash,
        binding_provider_id="test-binding-provider-v1",
        binding_provider_type="HUMAN",
    )
    resolved = DeterministicBindingAuthority(
        binding_authority_id="test-binding-authority-v1",
    ).resolve((assertion,))
    return assertion, resolved


class _RejectFirstWindowAuthority:
    binding_authority_id = "test-reject-first-window-authority-v1"

    def resolve(self, proposed_assertions: Sequence[BindingAssertion]) -> ResolvedBindingSet:
        sorted_assertions = tuple(
            sorted(proposed_assertions, key=lambda item: item.binding_assertion_id)
        )
        decisions = tuple(
            BindingDecision.create(
                binding_assertion_id=assertion.binding_assertion_id,
                binding_authority_id=self.binding_authority_id,
                decision=(
                    BINDING_DECISION_REJECTED
                    if assertion.data_window_id.endswith("-000")
                    else BINDING_DECISION_ACCEPTED
                ),
                reason_code=(
                    "TEST_REJECT_FIRST_WINDOW"
                    if assertion.data_window_id.endswith("-000")
                    else "TEST_ACCEPT_REMAINING_WINDOWS"
                ),
            )
            for assertion in sorted_assertions
        )
        return ResolvedBindingSet.create(
            binding_authority_id=self.binding_authority_id,
            assertions=sorted_assertions,
            decisions=decisions,
        )


def test_intervention_event_to_eeg_window_temporal_provenance() -> None:
    first_event = _intervention_event("evt-st36-001")
    second_event = _intervention_event("evt-st36-002")
    baseline = _eeg_window(
        "eegwin-baseline",
        "evt-st36-001",
        relation="baseline",
        start_offset_ms=-120_000,
        end_offset_ms=0,
    )
    post_a = _eeg_window(
        "eegwin-post-a",
        "evt-st36-001",
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
    )
    post_b = _eeg_window(
        "eegwin-post-b",
        "evt-st36-001",
        relation="post",
        start_offset_ms=60_000,
        end_offset_ms=90_000,
    )

    session = ObservationSession(
        session_id="obs-alpha",
        subject_pseudonym="subject-pseudo-001",
        acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
        preprocessing_profile_id=DEFAULT_EEG_PROFILE.profile_id,
        intervention_events=(first_event, second_event),
        physiological_windows=(baseline, post_a, post_b),
    )

    assert first_event.point_id == second_event.point_id == "TCM-ST36"
    assert len(session.intervention_events) == 2
    assert baseline.intervention_event_id == first_event.intervention_event_id
    assert [window.relation for window in session.physiological_windows] == [
        "baseline",
        "post",
        "post",
    ]


def test_observation_session_rejects_unknown_intervention_event_id() -> None:
    event = _intervention_event("evt-known")
    orphan_window = _eeg_window(
        "eegwin-orphan",
        "evt-missing",
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
    )

    with pytest.raises(EegDataError, match="UNKNOWN_INTERVENTION_EVENT_ID:evt-missing"):
        ObservationSession(
            session_id="obs-alpha",
            subject_pseudonym="subject-pseudo-001",
            acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
            preprocessing_profile_id=DEFAULT_EEG_PROFILE.profile_id,
            intervention_events=(event,),
            physiological_windows=(orphan_window,),
        )


def test_eeg_window_binding_is_immutable_and_offsets_fail_closed() -> None:
    window = _eeg_window(
        "eegwin-fixed",
        "evt-fixed",
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
    )
    with pytest.raises(AttributeError):
        window.intervention_event_id = "evt-other"  # type: ignore[misc]

    with pytest.raises(EegDataError, match="BASELINE_WINDOW_AFTER_EVENT"):
        _eeg_window(
            "eegwin-bad-baseline",
            "evt-fixed",
            relation="baseline",
            start_offset_ms=-1_000,
            end_offset_ms=1,
        )

    with pytest.raises(EegDataError, match="POST_WINDOW_BEFORE_EVENT"):
        _eeg_window(
            "eegwin-bad-post",
            "evt-fixed",
            relation="post",
            start_offset_ms=-1,
            end_offset_ms=2_000,
        )

    with pytest.raises(EegDataError, match="WINDOW_RAW_DATA_HASH_INVALID"):
        _eeg_window(
            "eegwin-bad-hash",
            "evt-fixed",
            relation="post",
            start_offset_ms=30_000,
            end_offset_ms=60_000,
            raw_data_hash="not-a-content-id",
        )


def test_response_analysis_input_receives_event_windows_and_model_outputs() -> None:
    event = _intervention_event("evt-analysis")
    baseline = _eeg_window(
        "eegwin-analysis-baseline",
        event.intervention_event_id,
        relation="baseline",
        start_offset_ms=-120_000,
        end_offset_ms=0,
    )
    post = _eeg_window(
        "eegwin-analysis-post",
        event.intervention_event_id,
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
    )
    analysis = ResponseAnalysisInput(
        intervention_event=event,
        baseline_windows=(baseline,),
        post_windows=(post,),
        model_outputs={"response_score_ppm": 750_000},
    )

    assert analysis.intervention_event.intervention_event_id == "evt-analysis"
    assert analysis.baseline_windows[0].relation == "baseline"
    assert analysis.post_windows[0].relation == "post"
    assert analysis.model_outputs["response_score_ppm"] == 750_000


def test_eeg_compute_window_bandpower_shape_and_bounds() -> None:
    profile = DEFAULT_EEG_PROFILE
    rng = np.random.Generator(np.random.PCG64(12345))
    raw = generate_synthetic_raw_eeg(
        n_channels=4,
        n_samples=profile.window_samples,
        sampling_rate_hz=profile.sampling_rate_hz,
        class_label=0,
        rng=rng,
    )
    features = compute_window_bandpower(raw, profile)
    assert features.shape == (16,)
    assert np.all(features >= 0.0)
    assert np.all(features <= 1.0)

    # Relative bandpower per channel should sum to 1.0 (4 channels -> sum is 4.0)
    for ch_idx in range(4):
        ch_slice = features[ch_idx * 4 : (ch_idx + 1) * 4]
        assert np.isclose(np.sum(ch_slice), 1.0, atol=1e-5)


def test_eeg_compute_window_bandpower_invalid_inputs() -> None:
    profile = DEFAULT_EEG_PROFILE
    with pytest.raises(EegDataError, match="WINDOW_SHAPE_INVALID"):
        compute_window_bandpower(np.zeros((4, 500, 1)), profile)

    with pytest.raises(EegDataError, match="CHANNEL_COUNT_MISMATCH"):
        compute_window_bandpower(np.zeros((3, 500)), profile)

    with pytest.raises(EegDataError, match="WINDOW_LENGTH_MISMATCH"):
        compute_window_bandpower(np.zeros((4, 400)), profile)


def test_eeg_partitions_and_determinism() -> None:
    provider1 = EegWindowDatasetProvider(seed=42)
    provider2 = EegWindowDatasetProvider(seed=42)

    meta1 = provider1.materialize()
    assert meta1["status"] == "materialized"
    assert meta1["dataset_id"] == "eeg-synthetic-bci-v1"
    assert meta1["accepted_binding_count"] == 160
    assert meta1["binding_assertion_count"] == 160
    assert meta1["binding_provider_id"] == "eeg-window-rule-provider-v1"
    assert meta1["binding_provider_type"] == "RULE"
    assert meta1["binding_authority_id"] == "eeg-demo-binding-authority-v1"
    assert str(meta1["resolved_binding_set_id"]).startswith("sha256:")
    assert meta1["rejected_binding_count"] == 0
    assert meta1["review_binding_count"] == 0
    assert meta1["intervention_event_count"] == 4
    assert meta1["observation_session_count"] == 4
    assert meta1["physiological_window_count"] == 160

    for part_name in DEMO_EEG_PARTITIONS:
        part1 = provider1.training_partition(part_name)
        part2 = provider2.training_partition(part_name)

        assert isinstance(part1, DataPartition)
        assert part1.partition_id == part_name
        assert part1.samples.shape == (40, 16)
        assert part1.targets.shape == (40,)
        contexts = part1.metadata["ticket_context"]
        assert isinstance(contexts, list)
        assert len(contexts) == 40
        assert set(contexts[0]) == {
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
        assert contexts[0]["binding_schema_version"] == BINDING_ASSERTION_SCHEMA_VERSION
        assert str(contexts[0]["binding_assertion_id"]).startswith("sha256:")
        assert str(contexts[0]["binding_decision_id"]).startswith("sha256:")
        assert str(contexts[0]["resolved_binding_set_id"]).startswith("sha256:")
        assert "point_id" not in contexts[0]
        assert "intervention_type" not in contexts[0]
        assert "relation" not in contexts[0]
        assert "start_offset_ms" not in contexts[0]
        assert np.array_equal(part1.samples, part2.samples)
        assert np.array_equal(part1.targets, part2.targets)

    with pytest.raises(EegDataError, match="UNKNOWN_PARTITION"):
        provider1.training_partition("nonexistent-worker")


def test_eeg_provider_rejects_rejected_window_and_does_not_silently_shrink_samples() -> None:
    provider = EegWindowDatasetProvider(
        windows_per_session=4,
        binding_authority=_RejectFirstWindowAuthority(),
    )
    # Fail-closed: exactly one accepted binding per window is required.
    # Zero accepted bindings must fail materialization immediately,
    # rather than silently shrinking data.
    with pytest.raises(EegDataError, match="WINDOW_BINDING_REJECTED_OR_MISSING"):
        provider.materialize()


def test_eeg_materialize_window_streaming() -> None:
    provider = EegWindowDatasetProvider()
    profile = provider.profile
    rng = np.random.Generator(np.random.PCG64(99))
    raw_signal = rng.standard_normal((4, 2000))

    window = DataWindow(
        window_id="win-001",
        session_id="session-alpha",
        start_sample=500,
        end_sample=1000,
        channels=profile.channels,
        preprocessing_profile_id=profile.profile_id,
    )

    part = provider.materialize_window(window, raw_signal, label=1)
    assert isinstance(part, DataPartition)
    assert part.partition_id == "win-001"
    assert part.samples.shape == (1, 16)
    assert part.targets.tolist() == [1]

    bad_window = DataWindow(
        window_id="win-002",
        session_id="session-alpha",
        start_sample=0,
        end_sample=500,
        channels=profile.channels,
        preprocessing_profile_id="incompatible-profile-v9",
    )
    with pytest.raises(EegDataError, match="PROFILE_MISMATCH"):
        provider.materialize_window(bad_window, raw_signal)

    wrong_channels = DataWindow(
        window_id="win-003",
        session_id="session-alpha",
        start_sample=0,
        end_sample=500,
        channels=("Cz",),
        preprocessing_profile_id=profile.profile_id,
    )
    with pytest.raises(EegDataError, match="WINDOW_CHANNELS_MISMATCH"):
        provider.materialize_window(wrong_channels, raw_signal)

    with pytest.raises(EegDataError, match="WINDOW_LABEL_INVALID"):
        provider.materialize_window(window, raw_signal, label=2)


def test_eeg_materialize_window_validates_intervention_bound_hash() -> None:
    provider = EegWindowDatasetProvider()
    profile = provider.profile
    rng = np.random.Generator(np.random.PCG64(101))
    raw_signal = rng.standard_normal((4, profile.window_samples))
    window = EegWindow(
        window_id="eegwin-bound",
        session_id="obs-bound",
        intervention_event_id="evt-bound",
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
        acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
        preprocessing_profile_id=profile.profile_id,
        raw_data_hash=eeg_raw_data_hash(raw_signal),
        start_sample=0,
        end_sample=profile.window_samples,
        channels=profile.channels,
    )

    with pytest.raises(EegDataError, match="RESOLVED_BINDING_SET_REQUIRED"):
        provider.materialize_window(window, raw_signal, label=1)

    assertion, resolved = _accepted_binding_for_window(window)
    part = provider.materialize_window(
        window,
        raw_signal,
        label=1,
        binding_assertion=assertion,
        resolved_binding_set=resolved,
    )
    assert part.metadata["ticket_context"][0]["intervention_event_id"] == "evt-bound"
    assert part.metadata["ticket_context"][0]["data_window_id"] == "eegwin-bound"
    assert part.metadata["ticket_context"][0]["raw_data_hash"] == eeg_raw_data_hash(raw_signal)
    assert str(part.metadata["ticket_context"][0]["binding_assertion_id"]).startswith("sha256:")
    assert str(part.metadata["ticket_context"][0]["binding_decision_id"]).startswith("sha256:")
    assert "relation" not in part.metadata["ticket_context"][0]

    forged = EegWindow(
        window_id="eegwin-forged",
        session_id="obs-bound",
        intervention_event_id="evt-bound",
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
        acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
        preprocessing_profile_id=profile.profile_id,
        raw_data_hash="sha256:" + "2" * 64,
        start_sample=0,
        end_sample=profile.window_samples,
        channels=profile.channels,
    )
    with pytest.raises(EegDataError, match="RAW_SIGNAL_HASH_MISMATCH"):
        provider.materialize_window(forged, raw_signal, label=1)

    mismatched_assertion = BindingAssertion.create(
        modality="eeg",
        dataset_id="eeg-synthetic-bci-v1",
        session_id="obs-bound",
        intervention_event_id="evt-other",
        data_window_id="eegwin-bound",
        relation="post",
        start_offset_ms=30_000,
        end_offset_ms=60_000,
        acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
        preprocessing_profile_id=profile.profile_id,
        raw_data_hash=eeg_raw_data_hash(raw_signal),
        binding_provider_id="test-binding-provider-v1",
        binding_provider_type="HUMAN",
    )
    mismatch_resolved = DeterministicBindingAuthority(
        binding_authority_id="test-binding-authority-v1",
    ).resolve((mismatched_assertion,))
    with pytest.raises(EegDataError, match="BINDING_ASSERTION_WINDOW_MISMATCH"):
        provider.materialize_window(
            window,
            raw_signal,
            label=1,
            binding_assertion=mismatched_assertion,
            resolved_binding_set=mismatch_resolved,
        )


def test_eeg_provider_response_analysis_lookup() -> None:
    provider = EegWindowDatasetProvider()
    provider.materialize()
    event_id = "evt-demo-eeg-01"

    event = provider.intervention_event(event_id)
    baseline_windows = provider.windows_for_event(event_id, relation="baseline")
    post_windows = provider.windows_for_event(event_id, relation="post")
    analysis = provider.response_analysis_input(
        event_id,
        model_outputs={"mean_local_accuracy_ppm": 1_000_000},
    )
    first_assertion = provider.binding_assertion("eegwin-demo-01-000")

    assert event.point_id == "TCM-ST36"
    assert len(baseline_windows) > 0
    assert len(post_windows) > 0
    assert analysis.intervention_event == event
    assert analysis.baseline_windows == baseline_windows
    assert analysis.post_windows == post_windows
    assert first_assertion.intervention_event_id == event_id
    assert first_assertion.data_window_id == "eegwin-demo-01-000"
    first_decision = provider.binding_decision("eegwin-demo-01-000")
    resolved = provider.resolved_binding_set()
    first_context = resolved.ticket_context_for_assertion(first_assertion)
    assert first_decision.decision == BINDING_DECISION_ACCEPTED
    assert first_context["data_window_id"] == "eegwin-demo-01-000"
    assert first_context["binding_decision_id"] == first_decision.binding_decision_id
    assert first_context["resolved_binding_set_id"] == resolved.resolved_binding_set_id
    assert "point_id" not in first_context
    assert "relation" not in first_context

    with pytest.raises(EegDataError, match="UNKNOWN_BINDING_ASSERTION_WINDOW_ID"):
        provider.binding_assertion("eegwin-missing")


def test_eeg_evaluation_data() -> None:
    provider = EegWindowDatasetProvider()
    eval_samples, eval_targets = provider.evaluation_data()
    assert eval_samples.shape == (40, 16)
    assert eval_targets.shape == (40,)
    # Exactly balanced 20 rest and 20 task
    assert np.count_nonzero(eval_targets == 0) == 20
    assert np.count_nonzero(eval_targets == 1) == 20


class _InjectForeignAcceptedAuthority:
    binding_authority_id = "test-foreign-authority-v1"

    def resolve(self, proposed_assertions: Sequence[BindingAssertion]) -> ResolvedBindingSet:
        sorted_assertions = tuple(
            sorted(proposed_assertions, key=lambda item: item.binding_assertion_id)
        )
        decisions = [
            BindingDecision.create(
                binding_assertion_id=a.binding_assertion_id,
                binding_authority_id=self.binding_authority_id,
                decision=BINDING_DECISION_ACCEPTED,
                reason_code="OK",
            )
            for a in sorted_assertions
        ]
        foreign_assertion = BindingAssertion.create(
            modality="eeg",
            dataset_id=EEG_DATASET_ID,
            session_id="obs-foreign",
            intervention_event_id="evt-foreign",
            data_window_id="eegwin-foreign-999",
            relation="post",
            start_offset_ms=30_000,
            end_offset_ms=60_000,
            acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
            preprocessing_profile_id=DEFAULT_EEG_PROFILE_ID,
            raw_data_hash="sha256:" + "3" * 64,
            binding_provider_id="provider-foreign",
            binding_provider_type="HUMAN",
        )
        foreign_decision = BindingDecision.create(
            binding_assertion_id=foreign_assertion.binding_assertion_id,
            binding_authority_id=self.binding_authority_id,
            decision=BINDING_DECISION_ACCEPTED,
            reason_code="FOREIGN_ACCEPTED",
        )
        all_assertions = (*sorted_assertions, foreign_assertion)
        all_decisions = (*decisions, foreign_decision)
        return ResolvedBindingSet.create(
            binding_authority_id=self.binding_authority_id,
            assertions=all_assertions,
            decisions=all_decisions,
        )


def test_eeg_provider_rejects_foreign_accepted_binding() -> None:
    provider = EegWindowDatasetProvider(
        windows_per_session=2,
        binding_authority=_InjectForeignAcceptedAuthority(),
    )
    with pytest.raises(EegDataError, match="FOREIGN_ACCEPTED_BINDING_ASSERTION"):
        provider.materialize()


class _UnknownWindowBindingProvider:
    binding_provider_id = "test-unknown-window-provider-v1"
    binding_provider_type = "RULE"

    def propose_bindings(self, observation_session: object) -> tuple[BindingAssertion, ...]:
        assert isinstance(observation_session, ObservationSession)
        real_proposals = EegWindowBindingProvider().propose_bindings(observation_session)
        first = real_proposals[0]
        bad_assertion = BindingAssertion.create(
            modality=first.modality,
            dataset_id=first.dataset_id,
            session_id=first.session_id,
            intervention_event_id=first.intervention_event_id,
            data_window_id="eegwin-unknown-999",
            relation=first.relation,
            start_offset_ms=first.start_offset_ms,
            end_offset_ms=first.end_offset_ms,
            acquisition_profile_id=first.acquisition_profile_id,
            preprocessing_profile_id=first.preprocessing_profile_id,
            raw_data_hash=first.raw_data_hash,
            binding_provider_id=self.binding_provider_id,
            binding_provider_type=self.binding_provider_type,
        )
        return (bad_assertion, *real_proposals[1:])


def test_eeg_provider_rejects_unknown_window_binding() -> None:
    provider = EegWindowDatasetProvider(
        windows_per_session=2,
        binding_provider=_UnknownWindowBindingProvider(),
    )
    with pytest.raises(EegDataError, match="UNKNOWN_PHYSIOLOGICAL_WINDOW_ID"):
        provider.materialize()


class _UnknownEventBindingProvider:
    binding_provider_id = "test-unknown-event-provider-v1"
    binding_provider_type = "RULE"

    def propose_bindings(self, observation_session: object) -> tuple[BindingAssertion, ...]:
        assert isinstance(observation_session, ObservationSession)
        real_proposals = EegWindowBindingProvider().propose_bindings(observation_session)
        first = real_proposals[0]
        bad_assertion = BindingAssertion.create(
            modality=first.modality,
            dataset_id=first.dataset_id,
            session_id=first.session_id,
            intervention_event_id="evt-unknown-999",
            data_window_id=first.data_window_id,
            relation=first.relation,
            start_offset_ms=first.start_offset_ms,
            end_offset_ms=first.end_offset_ms,
            acquisition_profile_id=first.acquisition_profile_id,
            preprocessing_profile_id=first.preprocessing_profile_id,
            raw_data_hash=first.raw_data_hash,
            binding_provider_id=self.binding_provider_id,
            binding_provider_type=self.binding_provider_type,
        )
        return (bad_assertion, *real_proposals[1:])


def test_eeg_provider_rejects_unknown_event_binding() -> None:
    provider = EegWindowDatasetProvider(
        windows_per_session=2,
        binding_provider=_UnknownEventBindingProvider(),
    )
    with pytest.raises(EegDataError, match="UNKNOWN_INTERVENTION_EVENT_ID"):
        provider.materialize()


class _DuplicateWindowBindingProvider:
    binding_provider_id = "test-duplicate-window-provider-v1"
    binding_provider_type = "RULE"

    def propose_bindings(self, observation_session: object) -> tuple[BindingAssertion, ...]:
        assert isinstance(observation_session, ObservationSession)
        real_proposals = EegWindowBindingProvider().propose_bindings(observation_session)
        first = real_proposals[0]
        second = BindingAssertion.create(
            modality=first.modality,
            dataset_id=first.dataset_id,
            session_id=first.session_id,
            intervention_event_id=first.intervention_event_id,
            data_window_id=first.data_window_id,
            relation=first.relation,
            start_offset_ms=first.start_offset_ms,
            end_offset_ms=first.end_offset_ms,
            acquisition_profile_id=first.acquisition_profile_id,
            preprocessing_profile_id=first.preprocessing_profile_id,
            raw_data_hash=first.raw_data_hash,
            binding_provider_id="second-provider-v2",
            binding_provider_type="MODEL",
        )
        return (first, second, *real_proposals[1:])


def test_eeg_provider_rejects_two_accepted_bindings_for_one_window() -> None:
    provider = EegWindowDatasetProvider(
        windows_per_session=2,
        binding_provider=_DuplicateWindowBindingProvider(),
    )
    with pytest.raises(
        (ResolvedBindingSetError, EegDataError),
        match="DUPLICATE_ACCEPTED_BINDING_FOR_WINDOW",
    ):
        provider.materialize()


def test_eeg_response_analyzer_missing_output_rejected() -> None:
    provider = EegWindowDatasetProvider()
    provider.materialize()
    event = provider.intervention_event("evt-demo-eeg-01")
    baseline_windows = provider.windows_for_event("evt-demo-eeg-01", relation="baseline")
    post_windows = provider.windows_for_event("evt-demo-eeg-01", relation="post")

    analyzer = EegBandpowerResponseAnalyzer()

    # Missing alpha_delta_ppm
    input_missing_alpha = ResponseAnalysisInput(
        intervention_event=event,
        baseline_windows=baseline_windows,
        post_windows=post_windows,
        model_outputs={"beta_delta_ppm": 100},
    )
    with pytest.raises(EegDataError, match="RESPONSE_MODEL_OUTPUT_MISSING:alpha_delta_ppm"):
        analyzer.analyze(input_missing_alpha)

    # Missing beta_delta_ppm
    input_missing_beta = ResponseAnalysisInput(
        intervention_event=event,
        baseline_windows=baseline_windows,
        post_windows=post_windows,
        model_outputs={"alpha_delta_ppm": 200},
    )
    with pytest.raises(EegDataError, match="RESPONSE_MODEL_OUTPUT_MISSING:beta_delta_ppm"):
        analyzer.analyze(input_missing_beta)

    # Non-integer value
    input_non_int = ResponseAnalysisInput(
        intervention_event=event,
        baseline_windows=baseline_windows,
        post_windows=post_windows,
        model_outputs={"alpha_delta_ppm": "not_an_int", "beta_delta_ppm": 100},
    )
    with pytest.raises(EegDataError, match="RESPONSE_MODEL_OUTPUT_NOT_INTEGER"):
        analyzer.analyze(input_non_int)


class _WrongModalityBindingProvider:
    binding_provider_id = "test-wrong-modality-provider-v1"
    binding_provider_type = "RULE"

    def propose_bindings(self, observation_session: object) -> tuple[BindingAssertion, ...]:
        assert isinstance(observation_session, ObservationSession)
        real_proposals = EegWindowBindingProvider().propose_bindings(observation_session)
        first = real_proposals[0]
        bad_assertion = BindingAssertion.create(
            modality="ecg",
            dataset_id=first.dataset_id,
            session_id=first.session_id,
            intervention_event_id=first.intervention_event_id,
            data_window_id=first.data_window_id,
            relation=first.relation,
            start_offset_ms=first.start_offset_ms,
            end_offset_ms=first.end_offset_ms,
            acquisition_profile_id=first.acquisition_profile_id,
            preprocessing_profile_id=first.preprocessing_profile_id,
            raw_data_hash=first.raw_data_hash,
            binding_provider_id=self.binding_provider_id,
            binding_provider_type=self.binding_provider_type,
        )
        return (bad_assertion, *real_proposals[1:])


def test_eeg_provider_rejects_wrong_binding_modality() -> None:
    provider = EegWindowDatasetProvider(
        windows_per_session=2,
        binding_provider=_WrongModalityBindingProvider(),
    )
    with pytest.raises(EegDataError, match="BINDING_ASSERTION_WINDOW_MISMATCH"):
        provider.materialize()


class _ForeignDatasetBindingProvider:
    binding_provider_id = "test-foreign-dataset-provider-v1"
    binding_provider_type = "RULE"

    def propose_bindings(self, observation_session: object) -> tuple[BindingAssertion, ...]:
        assert isinstance(observation_session, ObservationSession)
        real_proposals = EegWindowBindingProvider().propose_bindings(observation_session)
        first = real_proposals[0]
        bad_assertion = BindingAssertion.create(
            modality="eeg",
            dataset_id="foreign-dataset-v1",
            session_id=first.session_id,
            intervention_event_id=first.intervention_event_id,
            data_window_id=first.data_window_id,
            relation=first.relation,
            start_offset_ms=first.start_offset_ms,
            end_offset_ms=first.end_offset_ms,
            acquisition_profile_id=first.acquisition_profile_id,
            preprocessing_profile_id=first.preprocessing_profile_id,
            raw_data_hash=first.raw_data_hash,
            binding_provider_id=self.binding_provider_id,
            binding_provider_type=self.binding_provider_type,
        )
        return (bad_assertion, *real_proposals[1:])


def test_eeg_provider_rejects_foreign_binding_dataset() -> None:
    provider = EegWindowDatasetProvider(
        windows_per_session=2,
        binding_provider=_ForeignDatasetBindingProvider(),
    )
    with pytest.raises(EegDataError, match="BINDING_ASSERTION_WINDOW_MISMATCH"):
        provider.materialize()
