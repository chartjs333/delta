"""Token/domain-matched deterministic scientific-quality analysis."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.arms import RunObservation
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.reconciliation import ReconciliationResult


class QualityError(ValueError):
    """Stable scientific-quality analysis error."""


@dataclass(frozen=True, slots=True)
class QualityResult:
    document: dict[str, object]
    status: str


def analyze_quality(
    definition: BenchmarkDefinition,
    definition_id: str,
    runs: tuple[RunObservation, ...],
    reconciliation: ReconciliationResult,
) -> QualityResult:
    if reconciliation.status != "PASS":
        raise QualityError("QUALITY_RECONCILIATION_NOT_PASS")
    samples: dict[str, list[int]] = {}
    units: dict[str, str] = {}
    for run in runs:
        for sample in run.samples:
            samples.setdefault(sample.metric_id, []).append(sample.value)
            prior = units.setdefault(sample.metric_id, sample.unit)
            if prior != sample.unit:
                raise QualityError("QUALITY_METRIC_UNIT_DRIFT")
    quality_metrics = [
        item
        for item in definition.metric_definitions
        if item.metric_id.startswith(
            ("validation_", "downstream_", "post_training_", "per_domain_")
        )
    ]
    if not quality_metrics:
        raise QualityError("QUALITY_METRIC_DEFINITION_MISSING")
    measured: list[dict[str, object]] = []
    passed = True
    for metric in quality_metrics:
        values = samples.get(metric.metric_id, [])
        if len(values) != len(runs):
            if metric.mandatory:
                passed = False
            continue
        value = sum(values) // len(values)
        if metric.direction == "LOWER":
            metric_pass = value <= metric.pass_threshold
        elif metric.direction == "HIGHER":
            metric_pass = value >= metric.pass_threshold
        else:
            metric_pass = value == metric.pass_threshold
        passed = passed and (metric_pass or not metric.mandatory)
        measured.append({"metric_id": metric.metric_id, "unit": metric.unit, "value": value})
    status = (
        "PASS" if passed and reconciliation.token_match and reconciliation.domain_match else "FAIL"
    )
    document: dict[str, object] = {
        "benchmark_definition_id": definition_id,
        "domain_match": reconciliation.domain_match,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "metrics": measured,
        "run_ids": list(reconciliation.run_ids),
        "schema_version": "1.0.0",
        "status": status,
        "token_match": reconciliation.token_match,
        "type_name": "QUALITY_EVIDENCE",
    }
    return QualityResult(document, status)
