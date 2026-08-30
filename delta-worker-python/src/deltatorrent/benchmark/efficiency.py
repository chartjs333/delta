"""Deterministic byte/time/zero-copy accounting for benchmark arms."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from deltatorrent.benchmark.arms import RunObservation
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition


class EfficiencyError(ValueError):
    """Stable efficiency accounting error."""


@dataclass(frozen=True, slots=True)
class EfficiencyResult:
    document: dict[str, object]
    status: str


def analyze_efficiency(
    definition: BenchmarkDefinition,
    definition_id: str,
    runs: tuple[RunObservation, ...],
) -> EfficiencyResult:
    if (
        not runs
        or any(run.total_us <= 0 or run.useful_compute_us > run.total_us for run in runs)
        or sum(run.processed_tokens for run in runs) <= 0
    ):
        raise EfficiencyError("EFFICIENCY_TIME_ACCOUNTING_INVALID")
    total = sum(run.total_us for run in runs)
    useful = sum(run.useful_compute_us for run in runs)
    network_share_ppm = (total - useful) * 1_000_000 // total
    bytes_per_token = sum(run.bytes_sent for run in runs) // sum(
        run.processed_tokens for run in runs
    )
    gpu_utilization_ppm = int(median(run.gpu_utilization_ppm for run in runs))
    metrics = [
        {"metric_id": "bytes_per_token", "unit": "bytes", "value": bytes_per_token},
        {
            "metric_id": "gpu_utilization_ppm",
            "unit": "ppm",
            "value": gpu_utilization_ppm,
        },
        {"metric_id": "network_share_ppm", "unit": "ppm", "value": network_share_ppm},
    ]
    phase_values: dict[str, list[int]] = {}
    for run in runs:
        for phase, value in run.phase_latencies_us:
            phase_values.setdefault(phase, []).append(value)
    phase_latencies = [
        {
            "metric_id": f"{phase}_mean_us",
            "unit": "microseconds",
            "value": sum(values) // len(values),
        }
        for phase, values in sorted(phase_values.items())
    ]
    measured = {
        "bytes_per_token": bytes_per_token,
        "gpu_utilization_ppm": gpu_utilization_ppm,
        "network_share_ppm": network_share_ppm,
    }
    targets = {
        item.metric_id: item
        for item in definition.metric_definitions
        if item.metric_id in measured and item.mandatory
    }
    declared = set(targets)
    required = set(measured) if definition.primary else declared
    passed = (
        bool(declared)
        and declared == required
        and all(
            (item.direction == "LOWER" and measured[metric_id] <= item.pass_threshold)
            or (item.direction == "HIGHER" and measured[metric_id] >= item.pass_threshold)
            or (item.direction == "EXACT" and measured[metric_id] == item.pass_threshold)
            for metric_id, item in targets.items()
        )
    )
    eligible = sum(run.zero_copy_eligible for run in runs)
    hits = sum(run.zero_copy_hits for run in runs)
    status = "PASS" if passed else "FAIL"
    document: dict[str, object] = {
        "benchmark_definition_id": definition_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "metrics": metrics,
        "phase_latencies": phase_latencies,
        "schema_version": "1.0.0",
        "status": status,
        "type_name": "EFFICIENCY_EVIDENCE",
        "zero_copy_fallback_bytes": sum(run.copy_fallback_bytes for run in runs),
        "zero_copy_hit_rate_ppm": hits * 1_000_000 // eligible if eligible else 0,
    }
    return EfficiencyResult(document, status)
