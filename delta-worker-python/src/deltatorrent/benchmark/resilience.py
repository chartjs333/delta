"""Complete-or-safe-abort resilience outcome analysis."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID


@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    scenario_id: str
    expected_outcome: str
    actual_outcome: str
    current_unchanged_on_non_apply: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "actual_outcome": self.actual_outcome,
            "current_unchanged_on_non_apply": self.current_unchanged_on_non_apply,
            "expected_outcome": self.expected_outcome,
            "scenario_id": self.scenario_id,
        }


@dataclass(frozen=True, slots=True)
class ResilienceResult:
    document: dict[str, object]
    status: str


def synthetic_scenarios() -> tuple[ScenarioOutcome, ...]:
    return tuple(
        ScenarioOutcome(name, outcome, outcome, True)
        for name, outcome in (
            ("initial-seed-loss-complete-union", "RECOVERED"),
            ("initial-seed-loss-incomplete-union", "ABORTED"),
            ("worker-loss-10pct-sufficient", "APPLIED"),
            ("worker-loss-concentrated", "ABORTED"),
            ("validator-restart", "RECOVERED"),
            ("storage-loss", "RECOVERED"),
            ("regional-partition", "ABORTED"),
        )
    )


def analyze_resilience(
    definition_id: str, scenarios: tuple[ScenarioOutcome, ...]
) -> ResilienceResult:
    required = {
        "initial-seed-loss-complete-union",
        "initial-seed-loss-incomplete-union",
        "regional-partition",
        "storage-loss",
        "validator-restart",
        "worker-loss-10pct-sufficient",
        "worker-loss-concentrated",
    }
    by_id = {item.scenario_id: item for item in scenarios}
    passed = set(by_id) == required and all(
        item.actual_outcome == item.expected_outcome
        and (item.actual_outcome == "APPLIED" or item.current_unchanged_on_non_apply)
        for item in by_id.values()
    )
    status = "PASS" if passed else "FAIL"
    document: dict[str, object] = {
        "benchmark_definition_id": definition_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "scenarios": [by_id[key].to_dict() for key in sorted(by_id)],
        "schema_version": "1.0.0",
        "status": status,
        "type_name": "RESILIENCE_EVIDENCE",
    }
    return ResilienceResult(document, status)
