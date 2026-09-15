"""Unit tests for EegWindowDatasetProvider, DataWindow, and EEG signal preprocessing."""

from __future__ import annotations

import numpy as np
import pytest
from deltatorrent.data import (
    BINDING_ASSERTION_SCHEMA_VERSION,
    DEFAULT_EEG_ACQUISITION_PROFILE_ID,
    DEFAULT_EEG_PROFILE,
    EEG_DATASET_DESCRIPTOR,
    BindingAssertion,
    DataPartition,
    DatasetProvider,
    DataWindow,
    EegDataError,
    EegPreprocessingProfile,
    EegWindow,
    EegWindowDatasetProvider,
    InterventionEvent,
    ObservationSession,
    ResponseAnalysisInput,
    eeg_raw_data_hash,
)
from deltatorrent.data.eeg import (
    DEMO_EEG_PARTITIONS,
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
    assert meta1["binding_assertion_count"] == 160
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
        assert contexts[0]["binding_schema_version"] == BINDING_ASSERTION_SCHEMA_VERSION
        assert str(contexts[0]["binding_assertion_id"]).startswith("sha256:")
        assert "point_id" not in contexts[0]
        assert "intervention_type" not in contexts[0]
        assert np.array_equal(part1.samples, part2.samples)
        assert np.array_equal(part1.targets, part2.targets)

    with pytest.raises(EegDataError, match="UNKNOWN_PARTITION"):
        provider1.training_partition("nonexistent-worker")


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

    part = provider.materialize_window(window, raw_signal, label=1)
    assert part.metadata["ticket_context"][0]["intervention_event_id"] == "evt-bound"
    assert part.metadata["ticket_context"][0]["data_window_id"] == "eegwin-bound"
    assert part.metadata["ticket_context"][0]["raw_data_hash"] == eeg_raw_data_hash(raw_signal)
    assert str(part.metadata["ticket_context"][0]["binding_assertion_id"]).startswith("sha256:")

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
    )
    with pytest.raises(EegDataError, match="BINDING_ASSERTION_WINDOW_MISMATCH"):
        provider.materialize_window(
            window,
            raw_signal,
            label=1,
            binding_assertion=mismatched_assertion,
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
    assert first_assertion.ticket_context()["data_window_id"] == "eegwin-demo-01-000"

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
