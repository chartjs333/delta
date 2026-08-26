from __future__ import annotations

import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest
from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID
from deltatorrent.domain.parameters import ParameterSchema
from deltatorrent.domain.tickets import DomainPureWorkTicket
from deltatorrent.domain.updates import LocalRoundCompletion, NormalizedContributionCandidate
from deltatorrent.domain.worker_state import LocalRoundState, transition

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "delta-protocol"
FIXTURES = PROTOCOL / "fixtures" / "local-round"
SCHEMAS = PROTOCOL / "schemas"

POSITIVE_FIXTURES = (
    "domain-pure-work-ticket-v1.json",
    "local-round-completion-v1.json",
    "normalized-contribution-candidate-v1.json",
    "parameter-schema-v1.json",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _resolve_pointer(value: Any, pointer: str) -> tuple[Any, str | int]:
    parts = pointer.removeprefix("/").split("/")
    parent = value
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    key: str | int = int(parts[-1]) if isinstance(parent, list) else parts[-1]
    return parent, key


def _mutate(value: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(value)
    parent, key = _resolve_pointer(mutated, mutation["path"])
    if mutation["op"] == "replace":
        parent[key] = mutation["value"]
    elif mutation["op"] == "swap":
        other_parent, other_key = _resolve_pointer(mutated, mutation["with"])
        parent[key], other_parent[other_key] = other_parent[other_key], parent[key]
    else:  # pragma: no cover - fixture vocabulary is asserted below
        raise AssertionError(f"unknown fixture mutation: {mutation['op']}")
    return mutated


def test_positive_fixtures_are_canonical_json_documents() -> None:
    for name in (*POSITIVE_FIXTURES, "negative-v1.json", "traces-v1.json"):
        path = FIXTURES / name
        raw = path.read_bytes()
        value = _load(path)
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
        assert raw[:-1] == canonical_json_bytes(value)


def test_failure_trace_fixture_covers_required_runtime_outcomes() -> None:
    trace = _load(FIXTURES / "traces-v1.json")
    assert trace["formal_semantics_id"] == FORMAL_SEMANTICS_ID
    cases = trace["cases"]
    assert isinstance(cases, list)
    assert {case["id"] for case in cases} == {
        "cancellation",
        "complete",
        "data-exhaustion",
        "exact-replay",
        "oom",
        "partial-accumulation",
    }
    assert all(
        case["expected_candidate"] is (case["expected_status"] == "COMPLETED") for case in cases
    )


def test_positive_contract_lineage_and_exact_round_trips() -> None:
    parameter_value = _load(FIXTURES / "parameter-schema-v1.json")
    ticket_value = _load(FIXTURES / "domain-pure-work-ticket-v1.json")
    completion_value = _load(FIXTURES / "local-round-completion-v1.json")
    candidate_value = _load(FIXTURES / "normalized-contribution-candidate-v1.json")

    parameter_schema = ParameterSchema.from_dict(parameter_value)
    ticket = DomainPureWorkTicket.from_dict(ticket_value)
    completion = LocalRoundCompletion.from_dict(completion_value)
    candidate = NormalizedContributionCandidate.from_dict(candidate_value)

    assert parameter_schema.to_dict() == parameter_value
    assert ticket.to_dict() == ticket_value
    assert completion.to_dict() == completion_value
    assert candidate.to_dict() == candidate_value

    assert ticket.parameter_schema_id == parameter_schema.fingerprint
    assert completion.ticket_fingerprint == ticket.fingerprint
    assert candidate.ticket_fingerprint == ticket.fingerprint
    assert candidate.completion_id == completion.fingerprint
    assert completion.local_delta is not None
    assert completion.local_delta.tensor_order == candidate.tensor_order
    assert completion.parent_model_id == candidate.parent_model_id
    assert completion.optimizer_profile_id == candidate.optimizer_profile_id
    assert completion.arithmetic_profile_id == candidate.arithmetic_profile_id
    assert completion.effective_steps == completion.step_budget
    assert candidate.effective_steps == candidate.step_budget
    assert candidate.normalization_denominator == candidate.effective_steps


@pytest.mark.parametrize(
    ("schema_name", "model"),
    [
        ("domain-pure-work-ticket-v1.json", DomainPureWorkTicket),
        ("local-round-completion-v1.json", LocalRoundCompletion),
        ("normalized-contribution-candidate-v1.json", NormalizedContributionCandidate),
        ("parameter-schema-v1.json", ParameterSchema),
    ],
)
def test_schema_surface_matches_strict_python_model(schema_name: str, model: type[Any]) -> None:
    schema = _load(SCHEMAS / schema_name)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(model.__dataclass_fields__)
    assert set(schema["properties"]) == set(model.__dataclass_fields__)
    formal = schema["properties"].get("formal_semantics_id")
    if formal is not None:
        assert formal["const"] == FORMAL_SEMANTICS_ID


def test_schema_nested_objects_are_closed_and_local_delta_is_fp32() -> None:
    ticket = _load(SCHEMAS / "domain-pure-work-ticket-v1.json")
    parameter = _load(SCHEMAS / "parameter-schema-v1.json")
    completion = _load(SCHEMAS / "local-round-completion-v1.json")
    candidate = _load(SCHEMAS / "normalized-contribution-candidate-v1.json")

    assert ticket["properties"]["data_range"]["additionalProperties"] is False
    assert parameter["properties"]["parameters"]["items"]["additionalProperties"] is False
    assert completion["$defs"]["localDelta"]["additionalProperties"] is False
    assert completion["$defs"]["localDelta"]["properties"]["storage_dtype"]["const"] == "float32"
    assert candidate["properties"]["storage_dtype"]["const"] == "float32"


def test_negative_fixture_mutations_fail_with_declared_stable_code() -> None:
    negative = _load(FIXTURES / "negative-v1.json")
    cases = negative["cases"]
    assert isinstance(cases, list) and len(cases) >= 9
    assert len({case["id"] for case in cases}) == len(cases)
    assert {case["mutation"]["op"] for case in cases} <= {"replace", "swap"}

    parsers = {
        "domain-pure-work-ticket-v1.json": DomainPureWorkTicket.from_dict,
        "local-round-completion-v1.json": LocalRoundCompletion.from_dict,
        "normalized-contribution-candidate-v1.json": (NormalizedContributionCandidate.from_dict),
        "parameter-schema-v1.json": ParameterSchema.from_dict,
    }
    for case in cases:
        source = _load(FIXTURES / case["target"])
        mutated = _mutate(source, case["mutation"])
        with pytest.raises(DeltaError) as raised:
            parsers[case["target"]](mutated)
        assert raised.value.code.value == case["expected_error"], case["id"]


@pytest.mark.parametrize(
    ("fixture_name", "parser"),
    [
        ("domain-pure-work-ticket-v1.json", DomainPureWorkTicket.from_dict),
        ("local-round-completion-v1.json", LocalRoundCompletion.from_dict),
        (
            "normalized-contribution-candidate-v1.json",
            NormalizedContributionCandidate.from_dict,
        ),
        ("parameter-schema-v1.json", ParameterSchema.from_dict),
    ],
)
def test_protocol_models_reject_unknown_fields(fixture_name: str, parser: Any) -> None:
    value = _load(FIXTURES / fixture_name)
    value["unknown"] = "must-fail-closed"
    with pytest.raises(DeltaError):
        parser(value)


def test_domain_contracts_are_immutable() -> None:
    ticket = DomainPureWorkTicket.from_dict(_load(FIXTURES / "domain-pure-work-ticket-v1.json"))
    completion = LocalRoundCompletion.from_dict(_load(FIXTURES / "local-round-completion-v1.json"))
    with pytest.raises(FrozenInstanceError):
        ticket.step_budget = 3  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        completion.candidate_eligible = False  # type: ignore[misc]


def test_worker_state_machine_allows_only_declared_forward_transitions() -> None:
    allowed = {
        LocalRoundState.RECEIVED: {LocalRoundState.ACCEPTED, LocalRoundState.FAILED},
        LocalRoundState.ACCEPTED: {
            LocalRoundState.RUNNING,
            LocalRoundState.CANCELLED,
            LocalRoundState.FAILED,
        },
        LocalRoundState.RUNNING: {
            LocalRoundState.COMPLETED,
            LocalRoundState.CANCELLED,
            LocalRoundState.FAILED,
        },
        LocalRoundState.COMPLETED: set(),
        LocalRoundState.CANCELLED: set(),
        LocalRoundState.FAILED: set(),
    }
    for current in LocalRoundState:
        for target in LocalRoundState:
            if target in allowed[current]:
                assert transition(current, target) is target
            else:
                with pytest.raises(DeltaError) as raised:
                    transition(current, target)
                assert raised.value.code is ErrorCode.INVALID_WORKER_TRANSITION
