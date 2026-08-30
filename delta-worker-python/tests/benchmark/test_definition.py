from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from deltatorrent.benchmark.definition import BenchmarkDefinition, DefinitionError

ROOT = Path(__file__).parents[3]
FIXTURE = ROOT / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json"


def definition_value() -> dict[str, object]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    value = document["artifacts"]["definition"]["value"]
    assert isinstance(value, dict)
    return value


def test_complete_definition_is_canonical_and_pinned() -> None:
    definition = BenchmarkDefinition.from_dict(definition_value())

    assert definition.B == 8
    assert definition.H == 2
    assert definition.repetitions == 2
    assert len(definition.seeds) == 2
    assert len(definition.arm_ids) == 3
    assert definition.content_id.startswith("sha256:")
    assert not definition.primary


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (
            lambda value: value["metric_definitions"][0].pop("pass_threshold"),
            "METRIC_DEFINITION_FIELDS_INVALID",
        ),
        (lambda value: value.__setitem__("source_commit", "main"), "SOURCE_IDENTITY_NOT_PINNED"),
        (
            lambda value: value.__setitem__("missing_run_policy", "IGNORE"),
            "MISSING_RUN_POLICY_INVALID",
        ),
        (
            lambda value: value.__setitem__("decision_function", "OPERATOR_OVERRIDE"),
            "DECISION_FUNCTION_INVALID",
        ),
        (
            lambda value: value.__setitem__("adaptive_H", True),
            "BENCHMARK_DEFINITION_FIELDS_INVALID",
        ),
        (lambda value: value["pi_d"][0].__setitem__("denominator", 2), "DOMAIN_WEIGHTS_NOT_ONE"),
    ],
)
def test_definition_mutations_fail_closed(mutate: object, code: str) -> None:
    value = copy.deepcopy(definition_value())
    assert callable(mutate)
    mutate(value)

    with pytest.raises(DefinitionError, match=code):
        BenchmarkDefinition.from_dict(value)
