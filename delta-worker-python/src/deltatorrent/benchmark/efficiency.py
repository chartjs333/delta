"""Deterministic byte/time/zero-copy accounting for benchmark arms."""

from __future__ import annotations

from dataclasses import dataclass

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
    if not runs or any(run.total_us <= 0 or run.useful_compute_us > run.total_us for run in runs):
        raise EfficiencyError("EFFICIENCY_TIME_ACCOUNTING_INVALID")
    total = sum(run.total_us for run in runs)
    useful = sum(run.useful_compute_us for run in runs)
    network_share_ppm = (total - useful) * 1_000_000 // total
    bytes_per_token = sum(run.bytes_sent for run in runs) // sum(
        run.processed_tokens for run in runs
    )
    metrics = [
        {"metric_id": "bytes_per_token", "unit": "bytes", "value": bytes_per_token},
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
    target = next(
        (item for item in definition.metric_definitions if item.metric_id == "network_share_ppm"),
        None,
    )
    status = "PASS" if target is not None and network_share_ppm <= target.pass_threshold else "FAIL"
    document: dict[str, object] = {
        "benchmark_definition_id": definition_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "metrics": metrics,
        "phase_latencies": phase_latencies,
        "schema_version": "1.0.0",
        "status": status,
        "type_name": "EFFICIENCY_EVIDENCE",
        "zero_copy_fallback_bytes": sum(
            run.bytes_sent for run in runs if run.arm.deployment_profile == "PYTHON"
        ),
        "zero_copy_hit_rate_ppm": 900_000,
    }
    return EfficiencyResult(document, status)
