"""Token/domain/environment identity reconciliation before any comparison."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from deltatorrent.benchmark.arms import RunObservation
from deltatorrent.benchmark.definition import BenchmarkDefinition


class ReconciliationError(ValueError):
    """Stable run-set identity mismatch."""


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    run_ids: tuple[str, ...]
    token_match: bool
    domain_match: bool
    status: str


def reconcile(
    definition: BenchmarkDefinition,
    runs: tuple[RunObservation, ...],
) -> ReconciliationResult:
    expected = Counter({arm_id: definition.repetitions for arm_id in definition.arm_ids})
    actual = Counter(run.arm.content_id for run in runs)
    if actual != expected:
        raise ReconciliationError("RUN_REPETITION_SET_MISMATCH")
    if any(run.processed_tokens != definition.B for run in runs):
        raise ReconciliationError("RUN_TOKEN_EXPOSURE_MISMATCH")
    expected_domains = tuple(item.domain_id for item in definition.domain_weights)
    for run in runs:
        actual_domains = tuple(domain for domain, _ in run.domain_ticket_counts)
        if actual_domains != expected_domains:
            raise ReconciliationError("RUN_DOMAIN_EXPOSURE_MISMATCH")
    environment_ids = {run.environment_manifest_id for run in runs}
    if len(environment_ids) != 1:
        raise ReconciliationError("RUN_ENVIRONMENT_DRIFT")
    return ReconciliationResult(
        run_ids=tuple(run.content_id for run in runs),
        token_match=True,
        domain_match=True,
        status="PASS",
    )
