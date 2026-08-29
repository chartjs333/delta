"""Exact compatibility admission and fail-closed memory evidence."""

from __future__ import annotations

from dataclasses import dataclass


class PreflightError(ValueError):
    """Stable preflight or runtime-budget rejection."""


@dataclass(frozen=True, slots=True)
class CompatibilityProfile:
    backend: str
    backend_version: str
    compute_dtype: str
    accelerator: str
    kernel: str
    sequence_length: int
    microbatch_size: int
    gradient_accumulation_steps: int
    hard_max_reserved_bytes: int
    required_headroom_bytes: int
    required_minimum_available_at_start_bytes: int
    host_offload_limit_bytes: int = 0


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    backend: str
    backend_version: str
    compute_dtype: str
    accelerator: str
    kernel: str
    sequence_length: int
    microbatch_size: int
    gradient_accumulation_steps: int
    available_memory_bytes: int
    total_memory_bytes: int


@dataclass(frozen=True, slots=True)
class MemoryEstimate:
    quantized_base_bytes: int
    adapter_parameter_bytes: int
    optimizer_bytes: int
    activation_bytes: int

    @property
    def total_bytes(self) -> int:
        return (
            self.quantized_base_bytes
            + self.adapter_parameter_bytes
            + self.optimizer_bytes
            + self.activation_bytes
        )


@dataclass(frozen=True, slots=True)
class RuntimePeak:
    peak_allocated_bytes: int
    peak_reserved_bytes: int
    host_offload_peak_bytes: int


def estimate_memory(
    *,
    base_parameter_count: int,
    adapter_parameter_count: int,
    hidden_size: int,
    profile: CompatibilityProfile,
) -> MemoryEstimate:
    if min(base_parameter_count, adapter_parameter_count, hidden_size) <= 0:
        raise PreflightError("MEMORY_ESTIMATE_INPUT_INVALID")
    return MemoryEstimate(
        quantized_base_bytes=(base_parameter_count + 1) // 2,
        adapter_parameter_bytes=adapter_parameter_count * 2,
        optimizer_bytes=adapter_parameter_count * 8,
        activation_bytes=(
            profile.sequence_length
            * profile.microbatch_size
            * hidden_size
            * 2
            * profile.gradient_accumulation_steps
        ),
    )


def validate_preflight(
    profile: CompatibilityProfile,
    observation: RuntimeObservation,
    estimate: MemoryEstimate,
) -> None:
    exact = {
        "backend": (observation.backend, profile.backend),
        "backend_version": (observation.backend_version, profile.backend_version),
        "compute_dtype": (observation.compute_dtype, profile.compute_dtype),
        "accelerator": (observation.accelerator, profile.accelerator),
        "kernel": (observation.kernel, profile.kernel),
        "sequence_length": (observation.sequence_length, profile.sequence_length),
        "microbatch_size": (observation.microbatch_size, profile.microbatch_size),
        "gradient_accumulation_steps": (
            observation.gradient_accumulation_steps,
            profile.gradient_accumulation_steps,
        ),
    }
    for field, (actual, expected) in exact.items():
        if actual != expected:
            raise PreflightError(f"PREFLIGHT_{field.upper()}_MISMATCH")
    if observation.available_memory_bytes < profile.required_minimum_available_at_start_bytes:
        raise PreflightError("PREFLIGHT_AVAILABLE_MEMORY_INSUFFICIENT")
    required_total = profile.hard_max_reserved_bytes + profile.required_headroom_bytes
    if required_total > observation.total_memory_bytes:
        raise PreflightError("PREFLIGHT_HEADROOM_IMPOSSIBLE")
    if estimate.total_bytes > profile.hard_max_reserved_bytes:
        raise PreflightError("PREFLIGHT_ESTIMATE_EXCEEDS_BUDGET")
    if profile.host_offload_limit_bytes != 0:
        raise PreflightError("PREFLIGHT_HOST_OFFLOAD_FORBIDDEN")


def validate_runtime_peak(profile: CompatibilityProfile, peak: RuntimePeak) -> None:
    if peak.peak_allocated_bytes < 0 or peak.peak_reserved_bytes < peak.peak_allocated_bytes:
        raise PreflightError("RUNTIME_MEMORY_COUNTER_INVALID")
    if peak.peak_reserved_bytes > profile.hard_max_reserved_bytes:
        raise PreflightError("RUNTIME_RESERVED_MEMORY_EXCEEDED")
    if peak.host_offload_peak_bytes > profile.host_offload_limit_bytes:
        raise PreflightError("RUNTIME_HOST_OFFLOAD_EXCEEDED")
