"""Shared immutable identities and canonical measured-evaluation evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from pathlib import Path
from typing import Any, Final, Protocol, runtime_checkable

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_PROFILE_FIELDS: Final = {
    "dataset_id",
    "evaluator_id",
    "formal_semantics_id",
    "method",
    "schema_version",
    "tokenizer_id",
    "type_name",
}


class EvaluatorContractError(ValueError):
    """Stable fail-closed evaluator rejection."""


def fail(code: str) -> EvaluatorContractError:
    return EvaluatorContractError(code)


def require_content_id(value: object, code: str) -> str:
    if not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None:
        raise fail(code)
    return value


@runtime_checkable
class ScoringBackend(Protocol):
    """Minimal causal-LM boundary used by every measured evaluator."""

    @property
    def model_id(self) -> str: ...

    @property
    def tokenizer_id(self) -> str: ...

    def encode(self, text: str, *, add_bos: bool, add_eos: bool) -> tuple[int, ...]: ...

    def encode_continuation(
        self, prefix: str, continuation: str
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Tokenize joined text and assign boundary-overlap tokens to continuation."""
        ...

    def token_log_probabilities(self, input_ids: tuple[int, ...]) -> tuple[Decimal, ...]:
        """Return log P(input_ids[i+1] | input_ids[:i+1]) for every i."""
        ...

    def greedy_tokens(self, prefix_ids: tuple[int, ...], count: int) -> tuple[int, ...]: ...


@dataclass(frozen=True, slots=True)
class EvaluatorProfile:
    evaluator_id: str
    tokenizer_id: str
    dataset_id: str
    method: dict[str, Any]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, value: object) -> EvaluatorProfile:
        if not isinstance(value, dict) or set(value) != _PROFILE_FIELDS:
            raise fail("EVALUATOR_PROFILE_FIELDS_INVALID")
        if (
            value.get("type_name") != "EVALUATOR_PROFILE"
            or value.get("schema_version") != "1.0.0"
            or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            or value.get("evaluator_id") not in {"wikitext", "lambada", "hellaswag"}
        ):
            raise fail("EVALUATOR_PROFILE_HEADER_INVALID")
        method = value.get("method")
        if not isinstance(method, dict):
            raise fail("EVALUATOR_METHOD_INVALID")
        try:
            canonical_json_bytes(value)
        except TypeError as exc:
            raise fail("EVALUATOR_PROFILE_NOT_CANONICAL") from exc
        return cls(
            evaluator_id=str(value["evaluator_id"]),
            tokenizer_id=require_content_id(
                value["tokenizer_id"], "EVALUATOR_TOKENIZER_ID_INVALID"
            ),
            dataset_id=require_content_id(value["dataset_id"], "EVALUATOR_DATASET_ID_INVALID"),
            method=dict(method),
            raw=dict(value),
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.raw)

    @property
    def content_id(self) -> str:
        return sha256_content_id(b"deltareduce.010.evaluator-profile.v1\0" + self.canonical_bytes)


def load_evaluator_profile(path: Path) -> EvaluatorProfile:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise fail("EVALUATOR_PROFILE_JSON_INVALID") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) + b"\n" != raw:
        raise fail("EVALUATOR_PROFILE_CANONICAL_BYTES_INVALID")
    return EvaluatorProfile.from_dict(value)


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    execution_plan_id: str
    checkpoint_id: str
    model_id: str
    tokenizer_id: str
    dataset_id: str
    environment_id: str
    evaluator_profile_id: str
    evaluator_implementation_id: str

    def __post_init__(self) -> None:
        values = (
            self.execution_plan_id,
            self.checkpoint_id,
            self.model_id,
            self.tokenizer_id,
            self.dataset_id,
            self.environment_id,
            self.evaluator_profile_id,
            self.evaluator_implementation_id,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in values):
            raise fail("EVALUATION_CONTEXT_IDENTITY_INVALID")


@dataclass(frozen=True, slots=True)
class MetricValue:
    metric_id: str
    value: int
    unit: str

    def __post_init__(self) -> None:
        if not self.metric_id or not self.unit or self.value < 0:
            raise fail("MEASURED_METRIC_INVALID")

    @property
    def document(self) -> dict[str, object]:
        return {"metric_id": self.metric_id, "unit": self.unit, "value": self.value}


@dataclass(frozen=True, slots=True)
class MeasuredEvaluation:
    evaluator_id: str
    context: EvaluationContext
    item_count: int
    scored_token_count: int
    metrics: tuple[MetricValue, ...]
    item_evidence_root: str
    method_observation: dict[str, object]

    def __post_init__(self) -> None:
        if self.evaluator_id not in {"wikitext", "lambada", "hellaswag"}:
            raise fail("MEASURED_EVALUATOR_ID_INVALID")
        if self.item_count < 1 or self.scored_token_count < 0 or not self.metrics:
            raise fail("MEASURED_EVALUATION_ACCOUNTING_INVALID")
        if len({item.metric_id for item in self.metrics}) != len(self.metrics):
            raise fail("MEASURED_METRIC_DUPLICATE")
        require_content_id(self.item_evidence_root, "MEASURED_ITEM_ROOT_INVALID")
        canonical_json_bytes(self.method_observation)

    @property
    def document(self) -> dict[str, object]:
        return {
            "checkpoint_id": self.context.checkpoint_id,
            "dataset_id": self.context.dataset_id,
            "environment_id": self.context.environment_id,
            "evaluator_id": self.evaluator_id,
            "evaluator_implementation_id": self.context.evaluator_implementation_id,
            "evaluator_profile_id": self.context.evaluator_profile_id,
            "execution_plan_id": self.context.execution_plan_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "item_count": self.item_count,
            "item_evidence_root": self.item_evidence_root,
            "method_observation": self.method_observation,
            "metrics": [item.document for item in self.metrics],
            "model_id": self.context.model_id,
            "schema_version": "1.0.0",
            "scored_token_count": self.scored_token_count,
            "source_class": "MEASURED_MODEL_INFERENCE",
            "tokenizer_id": self.context.tokenizer_id,
            "type_name": "MEASURED_EVALUATION",
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.document)

    @property
    def content_id(self) -> str:
        return sha256_content_id(b"deltareduce.010.measured-evaluation.v1\0" + self.canonical_bytes)


def validate_context(
    profile: EvaluatorProfile,
    context: EvaluationContext,
    backend: ScoringBackend,
) -> None:
    if (
        context.evaluator_profile_id != profile.content_id
        or context.tokenizer_id != profile.tokenizer_id
        or context.dataset_id != profile.dataset_id
        or backend.tokenizer_id != profile.tokenizer_id
        or backend.model_id != context.model_id
    ):
        raise fail("EVALUATOR_IDENTITY_MISMATCH")


def decimal_sum(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext() as context:
        context.prec = 50
        return sum(values, Decimal(0))


def scaled_decimal(value: Decimal, scale: int) -> int:
    with localcontext() as context:
        context.prec = 50
        context.rounding = ROUND_HALF_EVEN
        scaled = (value * Decimal(scale)).quantize(Decimal(1))
    result = int(scaled)
    if result < 0:
        raise fail("MEASURED_METRIC_NEGATIVE")
    return result


def evidence_root(items: list[dict[str, object]]) -> str:
    return sha256_content_id(b"deltareduce.010.evaluator-items.v1\0" + canonical_json_bytes(items))
