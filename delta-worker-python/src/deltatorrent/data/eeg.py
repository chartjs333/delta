"""EEG Window DatasetProvider and deterministic signal processing.

Implements temporal windowing and spectral feature extraction for physiological signals.
Enforces the federated EEG invariant: raw EEG time-series remain local to the provider/worker;
only canonical extracted feature tensors and model parameters cross into consensus.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import numpy as np

from deltatorrent.data.base import (
    DataPartition,
    DatasetDescriptor,
    DatasetProvider,
    DatasetProviderError,
)
from deltatorrent.data.binding import (
    BINDING_DECISION_ACCEPTED,
    BindingAssertion,
    BindingAuthority,
    BindingDecision,
    BindingProvider,
    DeterministicBindingAuthority,
    ResolvedBindingSet,
    is_sha256_content_id,
)

DEFAULT_EEG_CHANNELS: tuple[str, ...] = ("F3", "F4", "C3", "C4")
DEFAULT_EEG_FREQUENCY_BANDS: tuple[tuple[str, float, float], ...] = (
    ("delta", 0.5, 4.0),
    ("theta", 4.0, 8.0),
    ("alpha", 8.0, 13.0),
    ("beta", 13.0, 30.0),
)
DEFAULT_EEG_PROFILE_ID: str = "bci-standard-4ch-v1"
DEFAULT_EEG_ACQUISITION_PROFILE_ID: str = "eeg-250hz-4ch-v1"
EEG_DATASET_ID: str = "eeg-synthetic-bci-v1"
EEG_SAMPLE_KIND: str = "eeg/bandpower-4ch-4band"
EEG_TARGET_KIND: str = "class-id/0-1"
VALID_INTERVENTION_LATERALITY: tuple[str, ...] = (
    "left",
    "right",
    "bilateral",
    "midline",
    "none",
)
VALID_WINDOW_RELATIONS: tuple[str, ...] = ("baseline", "post")
DEFAULT_EEG_BINDING_PROVIDER_ID = "eeg-window-rule-provider-v1"
DEFAULT_EEG_BINDING_AUTHORITY_ID = "eeg-demo-binding-authority-v1"

DEMO_EEG_PARTITIONS: tuple[str, ...] = (
    "demo-eeg-worker-01",
    "demo-eeg-worker-02",
    "demo-eeg-worker-03",
    "demo-eeg-worker-04",
)


class EegDataError(DatasetProviderError):
    """Raised when EEG signal, window, or profile parameters are invalid."""


def eeg_raw_data_hash(raw_signal: np.ndarray) -> str:
    """Return a deterministic content ID for raw physiological samples."""
    contiguous = np.ascontiguousarray(raw_signal)
    digest = hashlib.sha256()
    digest.update(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.dtype.str.encode("ascii"))
    digest.update(contiguous.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _binding_assertion_for_window(
    dataset_id: str,
    window: PhysiologicalWindow,
    *,
    binding_provider_id: str = DEFAULT_EEG_BINDING_PROVIDER_ID,
    binding_provider_type: str = "RULE",
) -> BindingAssertion:
    """Create a dataset-layer assertion for one physiological window."""
    return BindingAssertion.create(
        modality="eeg",
        dataset_id=dataset_id,
        session_id=window.session_id,
        intervention_event_id=window.intervention_event_id,
        data_window_id=window.window_id,
        relation=window.relation,
        start_offset_ms=window.start_offset_ms,
        end_offset_ms=window.end_offset_ms,
        acquisition_profile_id=window.acquisition_profile_id,
        preprocessing_profile_id=window.preprocessing_profile_id,
        raw_data_hash=window.raw_data_hash,
        binding_provider_id=binding_provider_id,
        binding_provider_type=binding_provider_type,
    )


def _validate_binding_assertion_for_window(
    assertion: BindingAssertion,
    *,
    dataset_id: str,
    window: PhysiologicalWindow,
) -> None:
    """Fail closed if a pre-training binding assertion does not match its window."""
    if (
        assertion.modality != "eeg"
        or assertion.dataset_id != dataset_id
        or assertion.session_id != window.session_id
        or assertion.intervention_event_id != window.intervention_event_id
        or assertion.data_window_id != window.window_id
        or assertion.relation != window.relation
        or assertion.start_offset_ms != window.start_offset_ms
        or assertion.end_offset_ms != window.end_offset_ms
        or assertion.acquisition_profile_id != window.acquisition_profile_id
        or assertion.preprocessing_profile_id != window.preprocessing_profile_id
        or assertion.raw_data_hash != window.raw_data_hash
    ):
        raise EegDataError("BINDING_ASSERTION_WINDOW_MISMATCH")


@dataclass(frozen=True, slots=True)
class InterventionEvent:
    """One concrete intervention event in one observation session."""

    intervention_event_id: str
    session_id: str
    intervention_type: str
    point_id: str
    laterality: str
    timestamp_ms: int
    operator_id: str
    protocol_id: str
    substance_id: str | None = None
    metadata: Mapping[str, object] = MappingProxyType({})

    def __post_init__(self) -> None:
        if not self.intervention_event_id:
            raise EegDataError("INTERVENTION_EVENT_ID_EMPTY")
        if not self.session_id:
            raise EegDataError("INTERVENTION_SESSION_ID_EMPTY")
        if not self.intervention_type:
            raise EegDataError("INTERVENTION_TYPE_EMPTY")
        if not self.point_id:
            raise EegDataError("INTERVENTION_POINT_ID_EMPTY")
        if self.laterality not in VALID_INTERVENTION_LATERALITY:
            raise EegDataError(f"INTERVENTION_LATERALITY_INVALID:{self.laterality}")
        if type(self.timestamp_ms) is not int or self.timestamp_ms < 0:
            raise EegDataError("INTERVENTION_TIMESTAMP_INVALID")
        if not self.operator_id:
            raise EegDataError("INTERVENTION_OPERATOR_ID_EMPTY")
        if not self.protocol_id:
            raise EegDataError("INTERVENTION_PROTOCOL_ID_EMPTY")


@dataclass(frozen=True, slots=True, kw_only=True)
class PhysiologicalWindow:
    """Immutable temporal link between physiological data and an intervention event."""

    window_id: str
    session_id: str
    intervention_event_id: str
    relation: str
    start_offset_ms: int
    end_offset_ms: int
    acquisition_profile_id: str
    preprocessing_profile_id: str
    raw_data_hash: str
    metadata: Mapping[str, object] = MappingProxyType({})

    def __post_init__(self) -> None:
        if not self.window_id:
            raise EegDataError("WINDOW_ID_EMPTY")
        if not self.session_id:
            raise EegDataError("WINDOW_SESSION_ID_EMPTY")
        if not self.intervention_event_id:
            raise EegDataError("WINDOW_INTERVENTION_EVENT_ID_EMPTY")
        if self.relation not in VALID_WINDOW_RELATIONS:
            raise EegDataError(f"WINDOW_RELATION_INVALID:{self.relation}")
        if type(self.start_offset_ms) is not int or type(self.end_offset_ms) is not int:
            raise EegDataError("WINDOW_OFFSETS_NOT_INTEGER")
        if self.end_offset_ms <= self.start_offset_ms:
            raise EegDataError("WINDOW_OFFSET_RANGE_INVALID")
        if self.relation == "baseline" and self.end_offset_ms > 0:
            raise EegDataError("BASELINE_WINDOW_AFTER_EVENT")
        if self.relation == "post" and self.start_offset_ms < 0:
            raise EegDataError("POST_WINDOW_BEFORE_EVENT")
        if not self.acquisition_profile_id:
            raise EegDataError("WINDOW_ACQUISITION_PROFILE_ID_EMPTY")
        if not self.preprocessing_profile_id:
            raise EegDataError("WINDOW_PREPROCESSING_PROFILE_ID_EMPTY")
        if not is_sha256_content_id(self.raw_data_hash):
            raise EegDataError("WINDOW_RAW_DATA_HASH_INVALID")


@dataclass(frozen=True, slots=True, kw_only=True)
class EegWindow(PhysiologicalWindow):
    """EEG-specific physiological window with sample and channel binding."""

    start_sample: int
    end_sample: int
    channels: tuple[str, ...]

    def __post_init__(self) -> None:
        PhysiologicalWindow.__post_init__(self)
        if self.start_sample < 0 or self.end_sample <= self.start_sample:
            raise EegDataError("WINDOW_SAMPLE_RANGE_INVALID")
        if not self.channels:
            raise EegDataError("WINDOW_CHANNELS_EMPTY")


@dataclass(frozen=True, slots=True)
class ObservationSession:
    """One subject/session pseudonym plus intervention events and physiological windows."""

    session_id: str
    subject_pseudonym: str
    acquisition_profile_id: str
    preprocessing_profile_id: str
    intervention_events: tuple[InterventionEvent, ...]
    physiological_windows: tuple[PhysiologicalWindow, ...]
    metadata: Mapping[str, object] = MappingProxyType({})

    def __post_init__(self) -> None:
        if not self.session_id:
            raise EegDataError("OBSERVATION_SESSION_ID_EMPTY")
        if not self.subject_pseudonym:
            raise EegDataError("OBSERVATION_SUBJECT_PSEUDONYM_EMPTY")
        if not self.acquisition_profile_id:
            raise EegDataError("OBSERVATION_ACQUISITION_PROFILE_ID_EMPTY")
        if not self.preprocessing_profile_id:
            raise EegDataError("OBSERVATION_PREPROCESSING_PROFILE_ID_EMPTY")

        event_ids: set[str] = set()
        for event in self.intervention_events:
            if event.session_id != self.session_id:
                raise EegDataError("INTERVENTION_SESSION_MISMATCH")
            if event.intervention_event_id in event_ids:
                raise EegDataError(f"DUPLICATE_INTERVENTION_EVENT_ID:{event.intervention_event_id}")
            event_ids.add(event.intervention_event_id)

        window_ids: set[str] = set()
        for window in self.physiological_windows:
            if window.session_id != self.session_id:
                raise EegDataError("WINDOW_SESSION_MISMATCH")
            if window.window_id in window_ids:
                raise EegDataError(f"DUPLICATE_WINDOW_ID:{window.window_id}")
            if window.intervention_event_id not in event_ids:
                raise EegDataError(f"UNKNOWN_INTERVENTION_EVENT_ID:{window.intervention_event_id}")
            if window.acquisition_profile_id != self.acquisition_profile_id:
                raise EegDataError("WINDOW_ACQUISITION_PROFILE_MISMATCH")
            if window.preprocessing_profile_id != self.preprocessing_profile_id:
                raise EegDataError("WINDOW_PREPROCESSING_PROFILE_MISMATCH")
            window_ids.add(window.window_id)


@dataclass(frozen=True, slots=True)
class ResponseAnalysisInput:
    """Input contract for response analyzers outside the Delta consensus spine."""

    intervention_event: InterventionEvent
    baseline_windows: tuple[EegWindow, ...]
    post_windows: tuple[EegWindow, ...]
    model_outputs: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.baseline_windows:
            raise EegDataError("RESPONSE_BASELINE_WINDOWS_EMPTY")
        if not self.post_windows:
            raise EegDataError("RESPONSE_POST_WINDOWS_EMPTY")
        event_id = self.intervention_event.intervention_event_id
        for window in self.baseline_windows:
            if window.intervention_event_id != event_id or window.relation != "baseline":
                raise EegDataError("RESPONSE_BASELINE_WINDOW_MISMATCH")
        for window in self.post_windows:
            if window.intervention_event_id != event_id or window.relation != "post":
                raise EegDataError("RESPONSE_POST_WINDOW_MISMATCH")


@dataclass(frozen=True, slots=True)
class EegWindowBindingProvider(BindingProvider):
    """Deterministic EEG BindingProvider that proposes window/event bindings."""

    dataset_id: str = EEG_DATASET_ID
    binding_provider_id: str = DEFAULT_EEG_BINDING_PROVIDER_ID
    binding_provider_type: str = "RULE"

    def propose_bindings(self, observation_session: object) -> tuple[BindingAssertion, ...]:
        """Return PROPOSED assertions for every physiological window in one session."""
        if not isinstance(observation_session, ObservationSession):
            raise EegDataError("EEG_BINDING_PROVIDER_SESSION_TYPE_INVALID")
        proposals = [
            _binding_assertion_for_window(
                self.dataset_id,
                window,
                binding_provider_id=self.binding_provider_id,
                binding_provider_type=self.binding_provider_type,
            )
            for window in observation_session.physiological_windows
        ]
        return tuple(sorted(proposals, key=lambda item: item.binding_assertion_id))


@dataclass(frozen=True, slots=True)
class ResponseAnalysisResult:
    """Observation-only response analysis result with no clinical recommendation."""

    intervention_event_id: str
    baseline_window_count: int
    post_window_count: int
    alpha_delta_ppm: int
    beta_delta_ppm: int
    observation: str
    clinical_conclusion_claimed: bool = False
    recommendation_claimed: bool = False
    type_name: str = "DELTAREDUCE_EEG_RESPONSE_ANALYSIS_RESULT"

    def document(self) -> dict[str, object]:
        """Return a JSON-safe response document."""
        return {
            "alpha_delta_ppm": self.alpha_delta_ppm,
            "baseline_window_count": self.baseline_window_count,
            "beta_delta_ppm": self.beta_delta_ppm,
            "clinical_conclusion_claimed": self.clinical_conclusion_claimed,
            "intervention_event_id": self.intervention_event_id,
            "observation": self.observation,
            "post_window_count": self.post_window_count,
            "recommendation_claimed": self.recommendation_claimed,
            "type_name": self.type_name,
        }


class EegBandpowerResponseAnalyzer:
    """Observation-only analyzer for baseline/post EEG bandpower summaries."""

    analyzer_id = "eeg-bandpower-response-analyzer-v1"

    def analyze(self, analysis_input: ResponseAnalysisInput) -> ResponseAnalysisResult:
        """Summarize observed baseline/post changes without medical interpretation."""
        alpha_delta_ppm = self._required_int_output(
            analysis_input.model_outputs,
            "alpha_delta_ppm",
        )
        beta_delta_ppm = self._required_int_output(
            analysis_input.model_outputs,
            "beta_delta_ppm",
        )
        if alpha_delta_ppm > 0:
            direction = "increased"
        elif alpha_delta_ppm < 0:
            direction = "decreased"
        else:
            direction = "unchanged"
        return ResponseAnalysisResult(
            intervention_event_id=analysis_input.intervention_event.intervention_event_id,
            baseline_window_count=len(analysis_input.baseline_windows),
            post_window_count=len(analysis_input.post_windows),
            alpha_delta_ppm=alpha_delta_ppm,
            beta_delta_ppm=beta_delta_ppm,
            observation=f"Alpha bandpower {direction} in observed post-event windows.",
        )

    @staticmethod
    def _required_int_output(model_outputs: Mapping[str, object], key: str) -> int:
        if key not in model_outputs:
            raise EegDataError(f"RESPONSE_MODEL_OUTPUT_MISSING:{key}")
        value = model_outputs[key]
        if type(value) is not int:
            raise EegDataError(f"RESPONSE_MODEL_OUTPUT_NOT_INTEGER:{key}")
        return value


@dataclass(frozen=True, slots=True)
class DataWindow:
    """Bounded temporal window defining an interval of multi-channel physiological data."""

    window_id: str
    session_id: str
    start_sample: int
    end_sample: int
    channels: tuple[str, ...]
    preprocessing_profile_id: str
    metadata: Mapping[str, object] = MappingProxyType({})

    def __post_init__(self) -> None:
        if not self.window_id:
            raise EegDataError("WINDOW_ID_EMPTY")
        if not self.session_id:
            raise EegDataError("SESSION_ID_EMPTY")
        if self.start_sample < 0 or self.end_sample <= self.start_sample:
            raise EegDataError("WINDOW_SAMPLE_RANGE_INVALID")
        if not self.channels:
            raise EegDataError("WINDOW_CHANNELS_EMPTY")
        if not self.preprocessing_profile_id:
            raise EegDataError("WINDOW_PREPROCESSING_PROFILE_ID_EMPTY")


@dataclass(frozen=True, slots=True)
class EegPreprocessingProfile:
    """Immutable parameter specification for deterministic EEG signal preprocessing."""

    profile_id: str
    sampling_rate_hz: int
    channels: tuple[str, ...]
    frequency_bands: tuple[tuple[str, float, float], ...]
    window_samples: int
    window_overlap_samples: int
    relative_power: bool = True

    def __post_init__(self) -> None:
        if self.sampling_rate_hz <= 0:
            raise EegDataError(f"INVALID_SAMPLING_RATE: {self.sampling_rate_hz}")
        if not self.channels:
            raise EegDataError("EMPTY_CHANNELS")
        if not self.frequency_bands:
            raise EegDataError("EMPTY_FREQUENCY_BANDS")
        if self.window_samples <= 0:
            raise EegDataError(f"INVALID_WINDOW_SAMPLES: {self.window_samples}")
        if self.window_overlap_samples < 0 or self.window_overlap_samples >= self.window_samples:
            raise EegDataError(f"INVALID_WINDOW_OVERLAP: {self.window_overlap_samples}")


DEFAULT_EEG_PROFILE = EegPreprocessingProfile(
    profile_id=DEFAULT_EEG_PROFILE_ID,
    sampling_rate_hz=250,
    channels=DEFAULT_EEG_CHANNELS,
    frequency_bands=DEFAULT_EEG_FREQUENCY_BANDS,
    window_samples=500,  # 2.0 seconds at 250 Hz
    window_overlap_samples=250,  # 50% overlap
    relative_power=True,
)

EEG_DATASET_DESCRIPTOR = DatasetDescriptor(
    dataset_id=EEG_DATASET_ID,
    display_name="Synthetic BCI EEG 4-Channel Bandpower",
    sample_kind=EEG_SAMPLE_KIND,
    target_kind=EEG_TARGET_KIND,
    deterministic=True,
    supports_offline_cache=True,
    description=(
        "Deterministic 4-channel windowed EEG bandpower features (delta, theta, alpha, beta) "
        "for binary rest vs. motor imagery classification."
    ),
    version="1.0.0",
)


def compute_window_bandpower(
    window_data: np.ndarray,
    profile: EegPreprocessingProfile,
) -> np.ndarray:
    """Compute relative bandpower features for a single multi-channel EEG window.

    window_data: 2D array of shape (n_channels, window_samples)
    returns: 1D array of shape (n_channels * n_bands,) with relative powers in [0.0, 1.0].
    """
    if window_data.ndim != 2:
        raise EegDataError(f"WINDOW_SHAPE_INVALID: expected 2D array, got {window_data.ndim}D")
    n_channels, n_samples = window_data.shape
    if n_channels != len(profile.channels):
        raise EegDataError(
            f"CHANNEL_COUNT_MISMATCH: expected {len(profile.channels)}, got {n_channels}"
        )
    if n_samples != profile.window_samples:
        raise EegDataError(
            f"WINDOW_LENGTH_MISMATCH: expected {profile.window_samples}, got {n_samples}"
        )
    if not np.all(np.isfinite(window_data)):
        raise EegDataError("WINDOW_VALUES_NOT_FINITE")

    window = np.hanning(n_samples)
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / profile.sampling_rate_hz)
    win_sum_sq = float(np.sum(window**2))
    freq_step = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0

    features: list[float] = []
    for ch_idx in range(n_channels):
        signal = window_data[ch_idx] * window
        fft_vals = np.fft.rfft(signal)
        psd = (np.abs(fft_vals) ** 2) / (profile.sampling_rate_hz * win_sum_sq)

        band_powers: list[float] = []
        for _name, f_low, f_high in profile.frequency_bands:
            mask = (freqs >= f_low) & (freqs < f_high)
            power = float(np.sum(psd[mask]) * freq_step) if np.any(mask) else 0.0
            band_powers.append(power)

        if profile.relative_power:
            total_power = sum(band_powers)
            if total_power > 0.0:
                band_powers = [bp / total_power for bp in band_powers]
            else:
                band_powers = [0.0] * len(band_powers)

        features.extend(band_powers)

    return np.ascontiguousarray(features, dtype=np.float64)


def generate_synthetic_raw_eeg(
    *,
    n_channels: int,
    n_samples: int,
    sampling_rate_hz: int,
    class_label: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate biologically realistic multi-channel EEG with distinct rest/task spectral power.

    - Class 0 (Rest / Relaxed): Dominant alpha rhythm (8-13 Hz) in posterior channels.
    - Class 1 (Task / Motor Imagery): Alpha suppression (ERD) + elevated beta rhythm (13-30 Hz).
    """
    time = np.arange(n_samples, dtype=np.float64) / sampling_rate_hz
    raw = np.zeros((n_channels, n_samples), dtype=np.float64)

    # 1/f-like pink noise baseline
    white = rng.standard_normal(size=(n_channels, n_samples))
    pink = np.cumsum(white, axis=1) * 0.05
    raw += pink

    for ch in range(n_channels):
        if class_label == 0:
            # High alpha (10 Hz), low beta (20 Hz)
            alpha_amp = 1.5 + rng.uniform(-0.2, 0.2)
            beta_amp = 0.3 + rng.uniform(-0.1, 0.1)
        else:
            # Suppressed alpha, elevated beta
            alpha_amp = 0.3 + rng.uniform(-0.1, 0.1)
            beta_amp = 1.6 + rng.uniform(-0.2, 0.2)

        alpha_phase = rng.uniform(0, 2 * np.pi)
        beta_phase = rng.uniform(0, 2 * np.pi)

        alpha_wave = alpha_amp * np.sin(2.0 * np.pi * 10.0 * time + alpha_phase)
        beta_wave = beta_amp * np.sin(2.0 * np.pi * 20.0 * time + beta_phase)

        raw[ch] += alpha_wave + beta_wave

    return raw


class EegWindowDatasetProvider(DatasetProvider):
    """DatasetProvider serving windowed multi-channel EEG bandpower features.

    Implements the standard DatasetProvider protocol while maintaining explicit
    temporal DataWindow structures and preprocessing profiles.
    """

    def __init__(
        self,
        *,
        profile: EegPreprocessingProfile = DEFAULT_EEG_PROFILE,
        windows_per_session: int = 40,
        seed: int = 42,
        binding_provider: BindingProvider | None = None,
        binding_authority: BindingAuthority | None = None,
    ) -> None:
        if windows_per_session <= 0:
            raise EegDataError("WINDOWS_PER_SESSION_INVALID")
        self._profile = profile
        self._windows_per_session = windows_per_session
        self._seed = seed
        self._binding_provider = binding_provider or EegWindowBindingProvider()
        self._binding_authority = binding_authority or DeterministicBindingAuthority(
            binding_authority_id=DEFAULT_EEG_BINDING_AUTHORITY_ID,
            default_reason_code="RULE_EVENT_WINDOW_CONTEXT_MATCH",
        )
        self._materialized = False
        self._sessions: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._partition_window_contexts: dict[str, tuple[dict[str, object], ...]] = {}
        self._observation_sessions: dict[str, ObservationSession] = {}
        self._intervention_events: dict[str, InterventionEvent] = {}
        self._binding_assertions_by_window: dict[str, BindingAssertion] = {}
        self._binding_decisions_by_window: dict[str, BindingDecision] = {}
        self._resolved_binding_set: ResolvedBindingSet | None = None
        self._windows_by_event: dict[str, tuple[EegWindow, ...]] = {}
        self._eval_data: tuple[np.ndarray, np.ndarray] | None = None

    @property
    def dataset_id(self) -> str:
        return EEG_DATASET_ID

    def descriptor(self) -> DatasetDescriptor:
        return EEG_DATASET_DESCRIPTOR

    @property
    def profile(self) -> EegPreprocessingProfile:
        return self._profile

    def materialize(
        self,
        cache_dir: Path | None = None,
        *,
        allow_download: bool = True,
    ) -> Mapping[str, object]:
        """Materialize deterministic synthetic EEG sessions."""
        if not self._materialized:
            self._generate_sessions()
            self._materialized = True
        assert self._resolved_binding_set is not None
        return {
            "acquisition_profile_id": DEFAULT_EEG_ACQUISITION_PROFILE_ID,
            "accepted_binding_count": self._resolved_binding_set.accepted_count,
            "binding_assertion_count": len(self._resolved_binding_set.assertions),
            "binding_authority_id": self._resolved_binding_set.binding_authority_id,
            "binding_provider_id": self._binding_provider.binding_provider_id,
            "binding_provider_type": self._binding_provider.binding_provider_type,
            "rejected_binding_count": self._resolved_binding_set.rejected_count,
            "resolved_binding_set_id": self._resolved_binding_set.resolved_binding_set_id,
            "review_binding_count": self._resolved_binding_set.review_count,
            "dataset_id": self.dataset_id,
            "intervention_event_count": len(self._intervention_events),
            "observation_session_count": len(self._observation_sessions),
            "physiological_window_count": sum(
                len(value) for value in self._windows_by_event.values()
            ),
            "profile_id": self._profile.profile_id,
            "sessions": list(self._sessions.keys()),
            "status": "materialized",
            "windows_per_session": self._windows_per_session,
        }

    def _ensure_materialized(self) -> None:
        if not self._materialized:
            self.materialize()

    def _validate_proposed_assertions_for_session(
        self,
        session: ObservationSession,
        proposals: Sequence[BindingAssertion],
    ) -> None:
        windows_by_id = {win.window_id: win for win in session.physiological_windows}
        events_by_id = {evt.intervention_event_id: evt for evt in session.intervention_events}

        for assertion in proposals:
            # 1. session_id belongs to current ObservationSession
            if assertion.session_id != session.session_id:
                raise EegDataError(
                    f"BINDING_ASSERTION_SESSION_MISMATCH:{assertion.session_id}!={session.session_id}"
                )
            # 2. physiological_window_id exists
            if assertion.data_window_id not in windows_by_id:
                raise EegDataError(f"UNKNOWN_PHYSIOLOGICAL_WINDOW_ID:{assertion.data_window_id}")
            # 3. intervention_event_id exists
            if assertion.intervention_event_id not in events_by_id:
                raise EegDataError(
                    f"UNKNOWN_INTERVENTION_EVENT_ID:{assertion.intervention_event_id}"
                )
            # 4. assertion references the same event/window/session relation, modality, and dataset
            window = windows_by_id[assertion.data_window_id]
            _validate_binding_assertion_for_window(
                assertion,
                dataset_id=self.dataset_id,
                window=window,
            )

    def _validate_resolved_binding_set(
        self,
        *,
        all_materialized_windows: Sequence[EegWindow],
        proposed_assertions: Sequence[BindingAssertion],
        resolved_set: ResolvedBindingSet,
    ) -> None:
        proposed_by_id = {a.binding_assertion_id: a for a in proposed_assertions}
        window_ids = {w.window_id for w in all_materialized_windows}

        # 1. No foreign accepted assertions may enter ResolvedBindingSet/evidence counts
        for accepted in resolved_set.accepted_assertions:
            if accepted.binding_assertion_id not in proposed_by_id:
                raise EegDataError(
                    f"FOREIGN_ACCEPTED_BINDING_ASSERTION:{accepted.binding_assertion_id}"
                )
            if accepted.data_window_id not in window_ids:
                raise EegDataError(f"FOREIGN_ACCEPTED_BINDING_WINDOW:{accepted.data_window_id}")
            if accepted != proposed_by_id[accepted.binding_assertion_id]:
                raise EegDataError(
                    f"MUTATED_ACCEPTED_BINDING_ASSERTION:{accepted.binding_assertion_id}"
                )

        # 2. Check accepted binding cardinality: exactly one accepted binding
        # per materialized EEG window.
        accepted_by_window: dict[str, list[BindingAssertion]] = {}
        for accepted in resolved_set.accepted_assertions:
            accepted_by_window.setdefault(accepted.data_window_id, []).append(accepted)

        for window in all_materialized_windows:
            accepted_list = accepted_by_window.get(window.window_id, [])
            if len(accepted_list) == 0:
                raise EegDataError(f"WINDOW_BINDING_REJECTED_OR_MISSING:{window.window_id}")
            if len(accepted_list) > 1:
                raise EegDataError(
                    f"WINDOW_BINDING_AMBIGUOUS:{window.window_id}:count={len(accepted_list)}"
                )

        if resolved_set.accepted_count != len(all_materialized_windows):
            raise EegDataError(
                f"ACCEPTED_BINDING_COUNT_MISMATCH:accepted={resolved_set.accepted_count}!={len(all_materialized_windows)}"
            )

    def _generate_sessions(self) -> None:
        """Generate reproducible multi-channel EEG sessions with label-skewed worker partitions."""
        rng = np.random.Generator(np.random.PCG64(self._seed))
        n_channels = len(self._profile.channels)
        win_samples = self._profile.window_samples
        window_duration_ms = win_samples * 1000 // self._profile.sampling_rate_hz

        # Partition 0: mostly class 0 (Rest)
        # Partition 1: mostly class 1 (Task)
        # Partition 2: balanced
        # Partition 3: balanced
        rest_heavy = max(1, round(self._windows_per_session * 0.8))
        task_heavy = self._windows_per_session - rest_heavy
        balanced_rest = self._windows_per_session // 2
        balanced_task = self._windows_per_session - balanced_rest
        partition_class_distributions = [
            [0] * rest_heavy + [1] * task_heavy,
            [0] * task_heavy + [1] * rest_heavy,
            [0] * balanced_rest + [1] * balanced_task,
            [0] * balanced_rest + [1] * balanced_task,
        ]
        partition_windows: dict[str, tuple[EegWindow, ...]] = {}
        partition_samples: dict[str, tuple[np.ndarray, ...]] = {}
        partition_targets: dict[str, tuple[int, ...]] = {}
        proposed_assertions: list[BindingAssertion] = []

        for p_idx, p_name in enumerate(DEMO_EEG_PARTITIONS):
            labels_list = partition_class_distributions[p_idx % len(partition_class_distributions)]
            samples_list: list[np.ndarray] = []
            session_id = f"obs-demo-eeg-{p_idx + 1:02d}"
            event = InterventionEvent(
                intervention_event_id=f"evt-demo-eeg-{p_idx + 1:02d}",
                session_id=session_id,
                intervention_type="acupuncture_injection",
                point_id="TCM-ST36",
                laterality="left",
                timestamp_ms=1_800_000_000_000 + p_idx * 60_000,
                operator_id="operator-demo-local",
                protocol_id="protocol-demo-eeg-st36-v1",
                substance_id="substance-demo-saline-v1",
            )
            windows: list[EegWindow] = []
            baseline_index = 0
            post_index = 0
            for lbl in labels_list:
                raw = generate_synthetic_raw_eeg(
                    n_channels=n_channels,
                    n_samples=win_samples,
                    sampling_rate_hz=self._profile.sampling_rate_hz,
                    class_label=lbl,
                    rng=rng,
                )
                if lbl == 0:
                    relation = "baseline"
                    end_offset_ms = -baseline_index * window_duration_ms
                    start_offset_ms = end_offset_ms - window_duration_ms
                    baseline_index += 1
                else:
                    relation = "post"
                    start_offset_ms = 30_000 + post_index * window_duration_ms
                    end_offset_ms = start_offset_ms + window_duration_ms
                    post_index += 1
                window = EegWindow(
                    window_id=f"eegwin-demo-{p_idx + 1:02d}-{len(windows):03d}",
                    session_id=session_id,
                    intervention_event_id=event.intervention_event_id,
                    relation=relation,
                    start_offset_ms=start_offset_ms,
                    end_offset_ms=end_offset_ms,
                    acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
                    preprocessing_profile_id=self._profile.profile_id,
                    raw_data_hash=eeg_raw_data_hash(raw),
                    start_sample=0,
                    end_sample=win_samples,
                    channels=self._profile.channels,
                )
                windows.append(window)
                features = compute_window_bandpower(raw, self._profile)
                samples_list.append(features)

            partition_samples[p_name] = tuple(samples_list)
            partition_targets[p_name] = tuple(int(label) for label in labels_list)
            self._intervention_events[event.intervention_event_id] = event
            self._windows_by_event[event.intervention_event_id] = tuple(windows)
            observation_session = ObservationSession(
                session_id=session_id,
                subject_pseudonym=f"subject-demo-{p_idx + 1:02d}",
                acquisition_profile_id=DEFAULT_EEG_ACQUISITION_PROFILE_ID,
                preprocessing_profile_id=self._profile.profile_id,
                intervention_events=(event,),
                physiological_windows=tuple(windows),
            )
            self._observation_sessions[session_id] = observation_session
            partition_windows[p_name] = tuple(windows)
            session_proposals = self._binding_provider.propose_bindings(observation_session)
            self._validate_proposed_assertions_for_session(observation_session, session_proposals)
            proposed_assertions.extend(session_proposals)

        self._resolved_binding_set = self._binding_authority.resolve(proposed_assertions)

        all_materialized_windows: list[EegWindow] = []
        for wins in partition_windows.values():
            all_materialized_windows.extend(wins)

        self._validate_resolved_binding_set(
            all_materialized_windows=all_materialized_windows,
            proposed_assertions=proposed_assertions,
            resolved_set=self._resolved_binding_set,
        )

        for assertion in self._resolved_binding_set.accepted_assertions:
            self._binding_assertions_by_window[assertion.data_window_id] = assertion
            self._binding_decisions_by_window[assertion.data_window_id] = (
                self._resolved_binding_set.decision_for_assertion_id(
                    assertion.binding_assertion_id,
                )
            )

        for partition_id, partition_eeg_windows in partition_windows.items():
            accepted_contexts: list[dict[str, object]] = []
            accepted_samples: list[np.ndarray] = []
            accepted_targets: list[int] = []
            for index, window in enumerate(partition_eeg_windows):
                context = self._resolved_binding_set.ticket_context_for_window(
                    window.window_id,
                )
                accepted_contexts.append(context)
                accepted_samples.append(partition_samples[partition_id][index])
                accepted_targets.append(partition_targets[partition_id][index])
            if len(accepted_samples) != len(partition_eeg_windows):
                raise EegDataError(
                    f"PARTITION_SAMPLE_COUNT_SHRUNK:{partition_id}:"
                    f"{len(accepted_samples)}!={len(partition_eeg_windows)}"
                )
            self._sessions[partition_id] = (
                np.stack(accepted_samples, axis=0).astype(np.float64),
                np.array(accepted_targets, dtype=np.uint8),
            )
            self._partition_window_contexts[partition_id] = tuple(accepted_contexts)

        # Generate evaluation session (40 balanced windows)
        eval_labels_list = [0] * 20 + [1] * 20
        eval_samples_list: list[np.ndarray] = []
        eval_rng = np.random.Generator(np.random.PCG64(self._seed + 999))
        for lbl in eval_labels_list:
            raw = generate_synthetic_raw_eeg(
                n_channels=n_channels,
                n_samples=win_samples,
                sampling_rate_hz=self._profile.sampling_rate_hz,
                class_label=lbl,
                rng=eval_rng,
            )
            features = compute_window_bandpower(raw, self._profile)
            eval_samples_list.append(features)

        self._eval_data = (
            np.stack(eval_samples_list, axis=0).astype(np.float64),
            np.array(eval_labels_list, dtype=np.uint8),
        )

    def training_partition(self, partition_id: str) -> DataPartition:
        """Return the training data partition assigned to the specified ticket or worker."""
        self._ensure_materialized()
        if partition_id not in self._sessions:
            raise EegDataError(
                f"UNKNOWN_PARTITION: '{partition_id}'. Available: {list(self._sessions.keys())}"
            )
        samples, targets = self._sessions[partition_id]
        metadata: dict[str, object] = {
            "acquisition_profile_id": DEFAULT_EEG_ACQUISITION_PROFILE_ID,
            "intervention_event_ids": sorted(
                {
                    str(context["intervention_event_id"])
                    for context in self._partition_window_contexts[partition_id]
                }
            ),
            "partition_id": partition_id,
            "preprocessing_profile_id": self._profile.profile_id,
            "sample_count": int(targets.size),
            "sample_kind": EEG_SAMPLE_KIND,
            "target_kind": EEG_TARGET_KIND,
            "ticket_context": [
                dict(item) for item in self._partition_window_contexts[partition_id]
            ],
        }
        return DataPartition(
            partition_id=partition_id,
            samples=samples,
            targets=targets,
            metadata=metadata,
        )

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Return evaluation features and ground truth targets."""
        self._ensure_materialized()
        assert self._eval_data is not None
        return self._eval_data

    def observation_session(self, session_id: str) -> ObservationSession:
        """Return an immutable observation session by ID."""
        self._ensure_materialized()
        try:
            return self._observation_sessions[session_id]
        except KeyError as exc:
            raise EegDataError(f"UNKNOWN_OBSERVATION_SESSION_ID:{session_id}") from exc

    def intervention_event(self, intervention_event_id: str) -> InterventionEvent:
        """Return one concrete intervention event by ID."""
        self._ensure_materialized()
        try:
            return self._intervention_events[intervention_event_id]
        except KeyError as exc:
            raise EegDataError(f"UNKNOWN_INTERVENTION_EVENT_ID:{intervention_event_id}") from exc

    def windows_for_event(
        self,
        intervention_event_id: str,
        *,
        relation: str | None = None,
    ) -> tuple[EegWindow, ...]:
        """Return EEG windows bound to one intervention event, optionally filtered by relation."""
        self._ensure_materialized()
        if relation is not None and relation not in VALID_WINDOW_RELATIONS:
            raise EegDataError(f"WINDOW_RELATION_INVALID:{relation}")
        try:
            windows = self._windows_by_event[intervention_event_id]
        except KeyError as exc:
            raise EegDataError(f"UNKNOWN_INTERVENTION_EVENT_ID:{intervention_event_id}") from exc
        if relation is None:
            return windows
        return tuple(window for window in windows if window.relation == relation)

    def binding_assertion(self, data_window_id: str) -> BindingAssertion:
        """Return the accepted immutable binding assertion for one physiological window."""
        self._ensure_materialized()
        try:
            return self._binding_assertions_by_window[data_window_id]
        except KeyError as exc:
            raise EegDataError(f"UNKNOWN_BINDING_ASSERTION_WINDOW_ID:{data_window_id}") from exc

    def binding_decision(self, data_window_id: str) -> BindingDecision:
        """Return the authority decision for one accepted physiological window."""
        self._ensure_materialized()
        try:
            return self._binding_decisions_by_window[data_window_id]
        except KeyError as exc:
            raise EegDataError(f"UNKNOWN_BINDING_DECISION_WINDOW_ID:{data_window_id}") from exc

    def resolved_binding_set(self) -> ResolvedBindingSet:
        """Return the deterministic resolved binding set for this provider materialization."""
        self._ensure_materialized()
        assert self._resolved_binding_set is not None
        return self._resolved_binding_set

    def response_analysis_input(
        self,
        intervention_event_id: str,
        *,
        model_outputs: Mapping[str, object],
    ) -> ResponseAnalysisInput:
        """Build the analyzer input for one intervention event outside Delta consensus."""
        return ResponseAnalysisInput(
            intervention_event=self.intervention_event(intervention_event_id),
            baseline_windows=self.windows_for_event(
                intervention_event_id,
                relation="baseline",
            ),
            post_windows=self.windows_for_event(intervention_event_id, relation="post"),
            model_outputs=model_outputs,
        )

    def materialize_window(
        self,
        window: DataWindow | EegWindow,
        raw_signal: np.ndarray,
        label: int = 0,
        *,
        binding_assertion: BindingAssertion | None = None,
        resolved_binding_set: ResolvedBindingSet | None = None,
    ) -> DataPartition:
        """Deterministically extract and preprocess a single explicit DataWindow.

        Bridges the streaming DataWindow abstraction into a standard DataPartition.
        """
        assertion: BindingAssertion | None = None
        decision: BindingDecision | None = None
        if isinstance(window, EegWindow):
            if window.acquisition_profile_id != DEFAULT_EEG_ACQUISITION_PROFILE_ID:
                raise EegDataError("ACQUISITION_PROFILE_MISMATCH")
            if window.raw_data_hash != eeg_raw_data_hash(raw_signal):
                raise EegDataError("RAW_SIGNAL_HASH_MISMATCH")
            assertion = binding_assertion or _binding_assertion_for_window(self.dataset_id, window)
            _validate_binding_assertion_for_window(
                assertion,
                dataset_id=self.dataset_id,
                window=window,
            )
            if resolved_binding_set is None:
                raise EegDataError("RESOLVED_BINDING_SET_REQUIRED")
            decision = resolved_binding_set.decision_for_assertion_id(
                assertion.binding_assertion_id,
            )
            if decision.decision != BINDING_DECISION_ACCEPTED:
                raise EegDataError(f"BINDING_ASSERTION_NOT_ACCEPTED:{window.window_id}")
        if window.preprocessing_profile_id != self._profile.profile_id:
            raise EegDataError(
                f"PROFILE_MISMATCH: window specifies '{window.preprocessing_profile_id}', "
                f"provider uses '{self._profile.profile_id}'"
            )
        if window.channels != self._profile.channels:
            raise EegDataError("WINDOW_CHANNELS_MISMATCH")
        if raw_signal.ndim != 2 or raw_signal.shape[0] != len(self._profile.channels):
            raise EegDataError("RAW_SIGNAL_SHAPE_INVALID")
        if window.end_sample > raw_signal.shape[1]:
            raise EegDataError("WINDOW_OUT_OF_BOUNDS")
        if window.end_sample - window.start_sample != self._profile.window_samples:
            raise EegDataError("WINDOW_LENGTH_MISMATCH")
        if label not in (0, 1):
            raise EegDataError("WINDOW_LABEL_INVALID")
        window_slice = raw_signal[:, window.start_sample : window.end_sample]
        features = compute_window_bandpower(window_slice, self._profile)
        samples = np.expand_dims(features, axis=0)
        targets = np.array([label], dtype=np.uint8)
        metadata: dict[str, object] = {
            "channels": list(window.channels),
            "preprocessing_profile_id": window.preprocessing_profile_id,
            "session_id": window.session_id,
            "window_id": window.window_id,
        }
        if isinstance(window, EegWindow):
            assert assertion is not None
            assert decision is not None
            assert resolved_binding_set is not None
            metadata["ticket_context"] = [
                resolved_binding_set.ticket_context_for_assertion(assertion)
            ]
        return DataPartition(
            partition_id=window.window_id,
            samples=samples,
            targets=targets,
            metadata=metadata,
        )
