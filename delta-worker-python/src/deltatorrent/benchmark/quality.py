"""Token/domain-matched deterministic scientific-quality analysis."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.arms import RunObservation
from deltatorrent.benchmark.campaign02 import CampaignExecutionPlan
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.evaluators.common import MeasuredEvaluation, MetricValue
from deltatorrent.benchmark.reconciliation import ReconciliationResult
from deltatorrent.protocol.canonical import canonical_json_bytes


class QualityError(ValueError):
    """Stable scientific-quality analysis error."""


@dataclass(frozen=True, slots=True)
class QualityResult:
    document: dict[str, object]
    status: str


@dataclass(frozen=True, slots=True)
class VerifiedMeasuredOutput:
    """Evaluator-produced, identity-checked inputs safe for later quality aggregation."""

    execution_plan_id: str
    evaluation_ids: tuple[str, ...]
    metrics: tuple[MetricValue, ...]


def verify_measured_outputs(
    plan: CampaignExecutionPlan,
    evaluations: tuple[MeasuredEvaluation, ...],
) -> VerifiedMeasuredOutput:
    """Verify measured evaluator outputs without recomputing or accepting manual metrics."""
    if len(evaluations) != len(plan.evaluation_profile_ids):
        raise QualityError("QUALITY_MEASURED_EVALUATION_SET_INCOMPLETE")
    required = {"wikitext", "lambada", "hellaswag"}
    if {item.evaluator_id for item in evaluations} != required:
        raise QualityError("QUALITY_MEASURED_EVALUATOR_SET_INVALID")
    metrics: list[MetricValue] = []
    evaluation_ids: list[str] = []
    expected = zip(
        plan.dataset_ids,
        plan.evaluation_profile_ids,
        plan.evaluation_implementation_ids,
        evaluations,
        strict=True,
    )
    for dataset_id, profile_id, implementation_id, evaluation in expected:
        context = evaluation.context
        if (
            context.execution_plan_id != plan.content_id
            or context.evaluator_profile_id != profile_id
            or context.environment_id != plan.environment_id
            or context.tokenizer_id != plan.tokenizer_id
            or context.dataset_id != dataset_id
            or context.evaluator_implementation_id != implementation_id
            or canonical_json_bytes(evaluation.document) != evaluation.canonical_bytes
            or evaluation.document.get("source_class") != "MEASURED_MODEL_INFERENCE"
        ):
            raise QualityError("QUALITY_MEASURED_EVALUATION_IDENTITY_INVALID")
        evaluation_ids.append(evaluation.content_id)
        metrics.extend(evaluation.metrics)
    if len({item.metric_id for item in metrics}) != len(metrics):
        raise QualityError("QUALITY_MEASURED_METRIC_DUPLICATE")
    required_metrics = {
        "validation_loss_micro",
        "validation_perplexity_micro",
        "per_domain_wikitext_loss_micro",
        "downstream_lambada_accuracy_ppm",
        "post_training_hellaswag_accuracy_ppm",
    }
    if not required_metrics <= {item.metric_id for item in metrics}:
        raise QualityError("QUALITY_MEASURED_METRIC_SET_INCOMPLETE")
    return VerifiedMeasuredOutput(
        execution_plan_id=plan.content_id,
        evaluation_ids=tuple(evaluation_ids),
        metrics=tuple(metrics),
    )


def analyze_quality(
    definition: BenchmarkDefinition,
    definition_id: str,
    runs: tuple[RunObservation, ...],
    reconciliation: ReconciliationResult,
) -> QualityResult:
    """Legacy Campaign 01 aggregation; Campaign 02 uses ``verify_measured_outputs`` first."""
    if reconciliation.status != "PASS":
        raise QualityError("QUALITY_RECONCILIATION_NOT_PASS")
    samples: dict[str, dict[str, list[int]]] = {}
    units: dict[str, str] = {}
    for run in runs:
        for sample in run.samples:
            samples.setdefault(sample.metric_id, {}).setdefault(run.arm.content_id, []).append(
                sample.value
            )
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
    reference_arms = {run.arm.content_id for run in runs if run.arm.kind == "SCIENTIFIC_REFERENCE"}
    if len(reference_arms) != 1:
        raise QualityError("QUALITY_REFERENCE_ARM_INVALID")
    reference_id = next(iter(reference_arms))
    primary_ids = sorted({run.arm.content_id for run in runs} - reference_arms)
    if not primary_ids:
        raise QualityError("QUALITY_PRIMARY_ARMS_MISSING")
    measured: list[dict[str, object]] = []
    passed = True
    for metric in quality_metrics:
        by_arm = samples.get(metric.metric_id, {})
        reference_values = by_arm.get(reference_id, [])
        if len(reference_values) != definition.repetitions:
            passed = passed and not metric.mandatory
            continue
        reference_value = sum(reference_values) // len(reference_values)
        for arm_id in primary_ids:
            values = by_arm.get(arm_id, [])
            if len(values) != definition.repetitions:
                passed = passed and not metric.mandatory
                continue
            value = sum(values) // len(values)
            if metric.statistical_method == "NON_INFERIORITY":
                degradation = (
                    value - reference_value
                    if metric.direction == "LOWER"
                    else reference_value - value
                )
                metric_pass = degradation <= metric.pass_threshold
            elif metric.direction == "LOWER":
                degradation = value
                metric_pass = value <= metric.pass_threshold
            elif metric.direction == "HIGHER":
                degradation = value
                metric_pass = value >= metric.pass_threshold
            else:
                degradation = value
                metric_pass = value == metric.pass_threshold
            passed = passed and (metric_pass or not metric.mandatory)
            measured.append(
                {
                    "arm_id": arm_id,
                    "degradation": degradation,
                    "metric_id": metric.metric_id,
                    "reference_value": reference_value,
                    "unit": metric.unit,
                    "value": value,
                }
            )
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
