from __future__ import annotations

from dataclasses import replace

import pytest
from deltatorrent.qlora.preflight import (
    CompatibilityProfile,
    PreflightError,
    RuntimeObservation,
    RuntimePeak,
    estimate_memory,
    validate_preflight,
    validate_runtime_peak,
)


def _profile() -> CompatibilityProfile:
    return CompatibilityProfile(
        backend="MOCK_INT4",
        backend_version="fixture-1",
        compute_dtype="FLOAT32",
        accelerator="CPU",
        kernel="REFERENCE",
        sequence_length=2,
        microbatch_size=2,
        gradient_accumulation_steps=1,
        hard_max_reserved_bytes=1_000_000,
        required_headroom_bytes=100_000,
        required_minimum_available_at_start_bytes=500_000,
    )


def _observation() -> RuntimeObservation:
    return RuntimeObservation(
        backend="MOCK_INT4",
        backend_version="fixture-1",
        compute_dtype="FLOAT32",
        accelerator="CPU",
        kernel="REFERENCE",
        sequence_length=2,
        microbatch_size=2,
        gradient_accumulation_steps=1,
        available_memory_bytes=800_000,
        total_memory_bytes=2_000_000,
    )


def test_exact_preflight_and_runtime_peak_pass() -> None:
    profile = _profile()
    estimate = estimate_memory(
        base_parameter_count=100,
        adapter_parameter_count=8,
        hidden_size=2,
        profile=profile,
    )
    validate_preflight(profile, _observation(), estimate)
    validate_runtime_peak(profile, RuntimePeak(200_000, 300_000, 0))


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("backend_version", "wrong", "PREFLIGHT_BACKEND_VERSION_MISMATCH"),
        ("compute_dtype", "FLOAT16", "PREFLIGHT_COMPUTE_DTYPE_MISMATCH"),
        ("accelerator", "CUDA", "PREFLIGHT_ACCELERATOR_MISMATCH"),
        ("kernel", "UNSUPPORTED", "PREFLIGHT_KERNEL_MISMATCH"),
        ("sequence_length", 3, "PREFLIGHT_SEQUENCE_LENGTH_MISMATCH"),
        ("microbatch_size", 3, "PREFLIGHT_MICROBATCH_SIZE_MISMATCH"),
    ],
)
def test_preflight_rejects_compatibility_mismatch(
    field: str, value: object, code: str
) -> None:
    profile = _profile()
    observation = replace(_observation(), **{field: value})
    estimate = estimate_memory(
        base_parameter_count=100,
        adapter_parameter_count=8,
        hidden_size=2,
        profile=profile,
    )
    with pytest.raises(PreflightError, match=code):
        validate_preflight(profile, observation, estimate)


def test_preflight_and_runtime_budget_excess_are_terminal() -> None:
    profile = _profile()
    estimate = estimate_memory(
        base_parameter_count=3_000_000,
        adapter_parameter_count=8,
        hidden_size=2,
        profile=profile,
    )
    with pytest.raises(PreflightError, match="PREFLIGHT_ESTIMATE_EXCEEDS_BUDGET"):
        validate_preflight(profile, _observation(), estimate)
    with pytest.raises(PreflightError, match="RUNTIME_RESERVED_MEMORY_EXCEEDED"):
        validate_runtime_peak(profile, RuntimePeak(900_000, 1_000_001, 0))
    with pytest.raises(PreflightError, match="RUNTIME_HOST_OFFLOAD_EXCEEDED"):
        validate_runtime_peak(profile, RuntimePeak(100, 200, 1))
