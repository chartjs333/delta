"""Immutable BenchmarkDefinition parsing, validation and canonical identity."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Final

from deltatorrent.protocol.canonical import canonical_json_bytes

FORMAL_SEMANTICS_ID: Final = (
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
)
_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_COMMON_FIELDS: Final = {"formal_semantics_id", "schema_version", "type_name"}
_DEFINITION_FIELDS: Final = _COMMON_FIELDS | {
    "B",
    "H",
    "abi_descriptor_id",
    "apply_profile_id",
    "arm_ids",
    "base_model_id",
    "compiler_profile_id",
    "compatibility_policy_id",
    "dataset_manifest_id",
    "decision_function",
    "dependency_lock_ids",
    "deployment_policy_id",
    "domain_manifest_id",
    "evaluation_ids",
    "exclusions",
    "fault_profile_ids",
    "fixedpoint_profile_id",
    "formal_report_id",
    "formal_trace_schema_id",
    "image_id",
    "isolation_policy",
    "jdk_profile_id",
    "license_policy_id",
    "metric_definitions",
    "missing_run_policy",
    "model_mode",
    "native_build_id",
    "netty_profile_id",
    "network_profile_ids",
    "optimizer_profile_id",
    "pi_d",
    "physical_profile_id",
    "primary",
    "protocol_registry_id",
    "python_profile_id",
    "qlora_profile_id",
    "refinement_evidence_ids",
    "repetitions",
    "robust_profile_id",
    "sbom_id",
    "seeds",
    "source_commit",
    "source_tree",
    "ticket_plan_id",
    "theorem_build_id",
    "tokenizer_id",
}
_METRIC_FIELDS: Final = {
    "aggregation",
    "direction",
    "implementation_id",
    "mandatory",
    "metric_id",
    "missing_run_rule",
    "outlier_rule",
    "pass_threshold",
    "repetitions",
    "statistical_method",
    "unit",
}
_DIRECTIONS: Final = {"EXACT", "HIGHER", "LOWER"}
_AGGREGATIONS: Final = {"ALL", "MEAN", "MEDIAN", "P95", "P99"}
_STATISTICS: Final = {"EXACT", "FIXED_SEED_MEAN", "NON_INFERIORITY"}


class DefinitionError(ValueError):
    """Stable fail-closed rejection for incomplete or mutable methodology."""


def _fail(code: str) -> DefinitionError:
    return DefinitionError(code)


def _integer(value: object, code: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise _fail(code)
    return value


def _string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise _fail(code)
    return value


def _content_id(value: object, code: str) -> str:
    result = _string(value, code)
    if _CONTENT_ID.fullmatch(result) is None:
        raise _fail(code)
    return result


def _strings(value: object, code: str, *, minimum: int = 0) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) < minimum:
        raise _fail(code)
    values = tuple(_string(item, code) for item in value)
    if len(set(values)) != len(values):
        raise _fail(f"{code}_DUPLICATE")
    return values


def _content_ids(value: object, code: str, *, minimum: int = 0) -> tuple[str, ...]:
    values = _strings(value, code, minimum=minimum)
    if any(_CONTENT_ID.fullmatch(item) is None for item in values):
        raise _fail(code)
    return values


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    metric_id: str
    implementation_id: str
    direction: str
    unit: str
    aggregation: str
    repetitions: int
    statistical_method: str
    pass_threshold: int
    missing_run_rule: str
    outlier_rule: str
    mandatory: bool

    @classmethod
    def from_dict(cls, value: object) -> MetricDefinition:
        if not isinstance(value, dict) or set(value) != _METRIC_FIELDS:
            raise _fail("METRIC_DEFINITION_FIELDS_INVALID")
        metric_id = _string(value["metric_id"], "METRIC_ID_INVALID")
        implementation_id = _content_id(
            value["implementation_id"], "METRIC_IMPLEMENTATION_NOT_PINNED"
        )
        direction = _string(value["direction"], "METRIC_DIRECTION_INVALID")
        aggregation = _string(value["aggregation"], "METRIC_AGGREGATION_INVALID")
        statistics = _string(value["statistical_method"], "METRIC_STATISTICS_INVALID")
        if direction not in _DIRECTIONS:
            raise _fail("METRIC_DIRECTION_INVALID")
        if aggregation not in _AGGREGATIONS:
            raise _fail("METRIC_AGGREGATION_INVALID")
        if statistics not in _STATISTICS:
            raise _fail("METRIC_STATISTICS_INVALID")
        missing = _string(value["missing_run_rule"], "METRIC_MISSING_RULE_INVALID")
        if missing not in {"FAIL", "REQUIRE_ALL"}:
            raise _fail("METRIC_MISSING_RULE_INVALID")
        outlier = _string(value["outlier_rule"], "METRIC_OUTLIER_RULE_INVALID")
        if outlier not in {"NONE", "PREDECLARED_IQR"}:
            raise _fail("METRIC_OUTLIER_RULE_INVALID")
        mandatory = value["mandatory"]
        if not isinstance(mandatory, bool):
            raise _fail("METRIC_MANDATORY_INVALID")
        return cls(
            metric_id=metric_id,
            implementation_id=implementation_id,
            direction=direction,
            unit=_string(value["unit"], "METRIC_UNIT_INVALID"),
            aggregation=aggregation,
            repetitions=_integer(value["repetitions"], "METRIC_REPETITIONS_INVALID", minimum=1),
            statistical_method=statistics,
            pass_threshold=_integer(value["pass_threshold"], "METRIC_THRESHOLD_INVALID"),
            missing_run_rule=missing,
            outlier_rule=outlier,
            mandatory=mandatory,
        )


@dataclass(frozen=True, slots=True)
class DomainWeight:
    domain_id: str
    numerator: int
    denominator: int

    @classmethod
    def from_dict(cls, value: object) -> DomainWeight:
        if not isinstance(value, dict) or set(value) != {"denominator", "domain_id", "numerator"}:
            raise _fail("DOMAIN_WEIGHT_FIELDS_INVALID")
        numerator = _integer(value["numerator"], "DOMAIN_WEIGHT_NUMERATOR_INVALID")
        denominator = _integer(value["denominator"], "DOMAIN_WEIGHT_DENOMINATOR_INVALID", minimum=1)
        if math.gcd(numerator, denominator) != 1:
            raise _fail("DOMAIN_WEIGHT_NOT_CANONICAL")
        return cls(_string(value["domain_id"], "DOMAIN_ID_INVALID"), numerator, denominator)


@dataclass(frozen=True, slots=True)
class BenchmarkDefinition:
    B: int
    H: int
    arm_ids: tuple[str, ...]
    network_profile_ids: tuple[str, ...]
    fault_profile_ids: tuple[str, ...]
    evaluation_ids: tuple[str, ...]
    metric_definitions: tuple[MetricDefinition, ...]
    domain_weights: tuple[DomainWeight, ...]
    repetitions: int
    seeds: tuple[int, ...]
    source_commit: str
    source_tree: str
    primary: bool
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, value: object) -> BenchmarkDefinition:
        if not isinstance(value, dict) or set(value) != _DEFINITION_FIELDS:
            raise _fail("BENCHMARK_DEFINITION_FIELDS_INVALID")
        if (
            value["type_name"] != "BENCHMARK_DEFINITION"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
        ):
            raise _fail("BENCHMARK_DEFINITION_VERSION_INVALID")
        try:
            canonical_json_bytes(value)
        except TypeError as exc:
            raise _fail("BENCHMARK_DEFINITION_NOT_CANONICAL") from exc
        if value["decision_function"] != "ALL_MANDATORY":
            raise _fail("DECISION_FUNCTION_INVALID")
        if value["missing_run_policy"] != "FAIL_CLOSED":
            raise _fail("MISSING_RUN_POLICY_INVALID")
        if value["isolation_policy"] != "COMPARE_BOTH":
            raise _fail("ISOLATION_POLICY_INVALID")
        source_commit = _string(value["source_commit"], "SOURCE_COMMIT_INVALID")
        source_tree = _string(value["source_tree"], "SOURCE_TREE_INVALID")
        if _COMMIT_ID.fullmatch(source_commit) is None or _COMMIT_ID.fullmatch(source_tree) is None:
            raise _fail("SOURCE_IDENTITY_NOT_PINNED")
        identity_fields = (
            "abi_descriptor_id",
            "apply_profile_id",
            "base_model_id",
            "compiler_profile_id",
            "compatibility_policy_id",
            "dataset_manifest_id",
            "deployment_policy_id",
            "domain_manifest_id",
            "fixedpoint_profile_id",
            "formal_report_id",
            "formal_trace_schema_id",
            "image_id",
            "jdk_profile_id",
            "license_policy_id",
            "native_build_id",
            "netty_profile_id",
            "optimizer_profile_id",
            "physical_profile_id",
            "protocol_registry_id",
            "python_profile_id",
            "qlora_profile_id",
            "robust_profile_id",
            "sbom_id",
            "ticket_plan_id",
            "theorem_build_id",
            "tokenizer_id",
        )
        for field in identity_fields:
            _content_id(value[field], f"{field.upper()}_INVALID")
        _content_ids(value["dependency_lock_ids"], "DEPENDENCY_LOCK_IDS_INVALID", minimum=1)
        refinement_ids = _content_ids(
            value["refinement_evidence_ids"], "REFINEMENT_EVIDENCE_IDS_INVALID", minimum=7
        )
        if len(refinement_ids) != 7:
            raise _fail("REFINEMENT_EVIDENCE_SET_INVALID")
        if value["model_mode"] not in {"FULL_MODEL", "QLORA_ADAPTER"}:
            raise _fail("MODEL_MODE_INVALID")
        metrics_raw = value["metric_definitions"]
        if not isinstance(metrics_raw, list) or not metrics_raw:
            raise _fail("METRIC_DEFINITIONS_MISSING")
        metrics = tuple(MetricDefinition.from_dict(item) for item in metrics_raw)
        if len({item.metric_id for item in metrics}) != len(metrics):
            raise _fail("METRIC_ID_DUPLICATE")
        repetitions = _integer(value["repetitions"], "REPETITIONS_INVALID", minimum=1)
        if any(item.repetitions != repetitions for item in metrics if item.mandatory):
            raise _fail("METRIC_REPETITION_MISMATCH")
        seeds_raw = value["seeds"]
        if not isinstance(seeds_raw, list) or len(seeds_raw) != repetitions:
            raise _fail("SEED_COUNT_MISMATCH")
        seeds = tuple(_integer(item, "SEED_INVALID") for item in seeds_raw)
        if len(set(seeds)) != len(seeds):
            raise _fail("SEED_DUPLICATE")
        weights_raw = value["pi_d"]
        if not isinstance(weights_raw, list) or not weights_raw:
            raise _fail("DOMAIN_WEIGHTS_MISSING")
        weights = tuple(DomainWeight.from_dict(item) for item in weights_raw)
        if len({item.domain_id for item in weights}) != len(weights):
            raise _fail("DOMAIN_WEIGHT_DUPLICATE")
        if sum((Fraction(item.numerator, item.denominator) for item in weights), Fraction()) != 1:
            raise _fail("DOMAIN_WEIGHTS_NOT_ONE")
        primary = value["primary"]
        if not isinstance(primary, bool):
            raise _fail("PRIMARY_FLAG_INVALID")
        return cls(
            B=_integer(value["B"], "B_INVALID", minimum=1),
            H=_integer(value["H"], "H_INVALID", minimum=1),
            arm_ids=_content_ids(value["arm_ids"], "ARM_IDS_INVALID", minimum=2),
            network_profile_ids=_content_ids(
                value["network_profile_ids"], "NETWORK_PROFILE_IDS_INVALID", minimum=1
            ),
            fault_profile_ids=_content_ids(
                value["fault_profile_ids"], "FAULT_PROFILE_IDS_INVALID", minimum=1
            ),
            evaluation_ids=_content_ids(
                value["evaluation_ids"], "EVALUATION_IDS_INVALID", minimum=1
            ),
            metric_definitions=metrics,
            domain_weights=weights,
            repetitions=repetitions,
            seeds=seeds,
            source_commit=source_commit,
            source_tree=source_tree,
            primary=primary,
            raw=dict(value),
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.raw)

    @property
    def content_id(self) -> str:
        domain = b"deltareduce.010.benchmark-definition.v1\0"
        return "sha256:" + hashlib.sha256(domain + self.canonical_bytes).hexdigest()


def load_definition(path: Path) -> BenchmarkDefinition:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail("BENCHMARK_DEFINITION_JSON_INVALID") from exc
    return BenchmarkDefinition.from_dict(value)
