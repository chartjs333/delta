"""Strict immutable contracts for the Feature 010 foundation.

The models in this module describe benchmark governance and evidence.  They are
not runtime certificates and cannot authorize execution or advance current state.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Final, cast

from deltatorrent.benchmark.canonical import canonical_bytes, content_id, load_json_bytes

FORMAL_SEMANTICS_ID: Final = (
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
)
SCHEMA_VERSION: Final = "1.0.0"
AUTHORITY_SCOPE: Final = "BENCHMARK_GOVERNANCE_ONLY"
NON_PROMOTABLE_CLASSES: Final = {"FOUNDATION_ONLY", "TEST_FIXTURE"}
REQUIRED_METRIC_PHASES: Final = (
    "compute",
    "upload",
    "availability",
    "certificate",
    "reduce",
    "apply",
    "p2p",
    "wait",
)
REQUIRED_BYTE_COUNTERS: Final = (
    "duplicate_bytes",
    "global_bytes",
    "p2p_bytes",
    "regional_bytes",
    "retry_bytes",
    "storage_bytes",
    "validator_bytes",
    "worker_bytes",
)
FAULT_EXPECTED_TERMINALS: Final = {
    "CONCENTRATED_CHURN": "SAFE_ABORT",
    "DISPERSED_CHURN": "CONTINUE",
    "REGION_PARTITION": "SAFE_ABORT",
    "REGION_RESTORE": "RECOVER",
    "STORAGE_CRASH": "CONTINUE",
    "STORAGE_RESTART": "RECOVER",
    "VALIDATOR_CRASH": "CONTINUE",
    "VALIDATOR_RESTART": "RECOVER",
    "WORKER_CRASH": "CONTINUE",
    "WORKER_RESTART": "RECOVER",
}

_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_ID = re.compile(r"^[0-9a-f]{40}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SCHEMA_ID = re.compile(r"^SCHEMA-[A-Z0-9-]+-010-V1$")
_MAX_I64 = (1 << 63) - 1


class ContractError(ValueError):
    """Stable fail-closed validation error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise ContractError(code)


def _exact(value: object, fields: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        _fail(code)
    return cast(dict[str, Any], value)


def _string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(code)
    return cast(str, value)


def _identifier(value: object, code: str) -> str:
    result = _string(value, code)
    if _IDENTIFIER.fullmatch(result) is None:
        _fail(code)
    return result


def _integer(value: object, code: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > _MAX_I64:
        _fail(code)
    return cast(int, value)


def _boolean(value: object, code: str) -> bool:
    if not isinstance(value, bool):
        _fail(code)
    return cast(bool, value)


def _content_id(value: object, code: str) -> str:
    result = _string(value, code)
    if _CONTENT_ID.fullmatch(result) is None:
        _fail(code)
    return result


def _git_id(value: object, code: str) -> str:
    result = _string(value, code)
    if _GIT_ID.fullmatch(result) is None:
        _fail(code)
    return result


def _strings(
    value: object,
    code: str,
    *,
    minimum: int = 0,
    sorted_unique: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) < minimum:
        _fail(code)
    items = cast(list[object], value)
    result = tuple(_string(item, code) for item in items)
    if len(set(result)) != len(result):
        _fail(f"{code}_DUPLICATE")
    if sorted_unique and result != tuple(sorted(result)):
        _fail(f"{code}_NOT_SORTED")
    return result


def _content_ids(
    value: object,
    code: str,
    *,
    minimum: int = 0,
    sorted_unique: bool = False,
) -> tuple[str, ...]:
    result = _strings(value, code, minimum=minimum, sorted_unique=sorted_unique)
    if any(_CONTENT_ID.fullmatch(item) is None for item in result):
        _fail(code)
    return result


def _base(document: dict[str, Any], type_name: str) -> None:
    if document.get("schema_version") != SCHEMA_VERSION:
        _fail("SCHEMA_VERSION_MISMATCH")
    if document.get("type_name") != type_name:
        _fail("TYPE_NAME_MISMATCH")
    if document.get("formal_semantics_id") != FORMAL_SEMANTICS_ID:
        _fail("FORMAL_SEMANTICS_MISMATCH")
    if document.get("authority_scope") != AUTHORITY_SCOPE:
        _fail("AUTHORITY_SCOPE_INVALID")


def _non_promotable(document: dict[str, Any]) -> None:
    if document.get("evidence_class") not in NON_PROMOTABLE_CLASSES:
        _fail("EVIDENCE_CLASS_PROMOTION_FORBIDDEN")
    if document.get("primary_eligible") is not False:
        _fail("PRIMARY_ELIGIBILITY_FORBIDDEN")
    if document.get("gate_eligible") is not False:
        _fail("GATE_ELIGIBILITY_FORBIDDEN")


def _fixture_only(document: dict[str, Any]) -> None:
    if document.get("evidence_class") != "TEST_FIXTURE":
        _fail("TEST_FIXTURE_EVIDENCE_REQUIRED")


def _rational(value: object, code: str) -> tuple[int, int]:
    item = _exact(value, {"denominator", "numerator"}, code)
    numerator = _integer(item["numerator"], code)
    denominator = _integer(item["denominator"], code, minimum=1)
    if math.gcd(numerator, denominator) != 1:
        _fail(f"{code}_NOT_REDUCED")
    return numerator, denominator


def _validate_runtime_identity(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "abi_header_id",
            "abi_schema_id",
            "authority_scope",
            "binary_build_id",
            "compiler_lock_id",
            "cpp_core_id",
            "cuda_profile_id",
            "deployment_profile",
            "evidence_class",
            "fixture_corpus_id",
            "formal_report_id",
            "formal_semantics_id",
            "gate_eligible",
            "java_dependency_lock_id",
            "java_toolchain_id",
            "native_runtime_id",
            "netty_profile_id",
            "primary_eligible",
            "protocol_registry_id",
            "python_lock_id",
            "python_profile_id",
            "sbom_id",
            "schema_version",
            "source_commit",
            "source_tree",
            "type_name",
        },
        "RUNTIME_IDENTITY_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_RUNTIME_IDENTITY")
    _non_promotable(document)
    _git_id(document["source_commit"], "SOURCE_COMMIT_INVALID")
    _git_id(document["source_tree"], "SOURCE_TREE_INVALID")
    for field in (
        "abi_header_id",
        "abi_schema_id",
        "binary_build_id",
        "compiler_lock_id",
        "cpp_core_id",
        "cuda_profile_id",
        "fixture_corpus_id",
        "formal_report_id",
        "java_dependency_lock_id",
        "java_toolchain_id",
        "native_runtime_id",
        "netty_profile_id",
        "protocol_registry_id",
        "python_lock_id",
        "python_profile_id",
        "sbom_id",
    ):
        _content_id(document[field], f"{field.upper()}_INVALID")
    if document["deployment_profile"] not in {"EMBEDDED_FFM", "ISOLATED_SIDECAR"}:
        _fail("DEPLOYMENT_PROFILE_INVALID")


def _validate_scientific_profile(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "dataset_id",
            "domain_tokens",
            "evaluator_ids",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "model_id",
            "model_mode",
            "optimizer_id",
            "primary_eligible",
            "repetitions",
            "schema_version",
            "seeds",
            "ticket_ids",
            "ticket_plan_id",
            "tokenizer_id",
            "total_eligible_tokens",
            "type_name",
        },
        "SCIENTIFIC_PROFILE_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_SCIENTIFIC_PROFILE")
    _non_promotable(document)
    for field in ("dataset_id", "model_id", "optimizer_id", "ticket_plan_id", "tokenizer_id"):
        _content_id(document[field], f"{field.upper()}_INVALID")
    _content_ids(document["evaluator_ids"], "EVALUATOR_IDS_INVALID", minimum=1, sorted_unique=True)
    if document["model_mode"] not in {"FULL_MODEL", "QLORA_ADAPTER"}:
        _fail("MODEL_MODE_INVALID")
    repetitions = _integer(document["repetitions"], "REPETITIONS_INVALID", minimum=1)
    seeds = document["seeds"]
    if not isinstance(seeds, list) or len(seeds) != repetitions:
        _fail("SEED_COUNT_MISMATCH")
    seed_values = tuple(_integer(item, "SEED_INVALID") for item in seeds)
    if len(set(seed_values)) != len(seed_values):
        _fail("SEED_DUPLICATE")
    _content_ids(
        document["ticket_ids"],
        "SCIENTIFIC_TICKET_IDS_INVALID",
        minimum=1,
        sorted_unique=True,
    )
    domain_tokens = document["domain_tokens"]
    if not isinstance(domain_tokens, dict) or not domain_tokens:
        _fail("DOMAIN_TOKENS_INVALID")
    if list(domain_tokens) != sorted(domain_tokens):
        _fail("DOMAIN_TOKENS_NOT_SORTED")
    total = sum(
        _integer(item, "DOMAIN_TOKEN_COUNT_INVALID", minimum=1) for item in domain_tokens.values()
    )
    if total != _integer(document["total_eligible_tokens"], "TOTAL_TOKEN_COUNT_INVALID", minimum=1):
        _fail("TOKEN_TOTAL_MISMATCH")


def _validate_environment_manifest(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "binary_ids",
            "capture_epoch_ms",
            "dependency_lock_ids",
            "environment_variable_names",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "hardware_inventory_id",
            "image_id",
            "primary_eligible",
            "runtime_identity_id",
            "sbom_id",
            "schema_version",
            "source_commit",
            "source_tree",
            "type_name",
        },
        "ENVIRONMENT_MANIFEST_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_ENVIRONMENT_MANIFEST")
    _non_promotable(document)
    _git_id(document["source_commit"], "ENVIRONMENT_SOURCE_COMMIT_INVALID")
    _git_id(document["source_tree"], "ENVIRONMENT_SOURCE_TREE_INVALID")
    for field in ("hardware_inventory_id", "image_id", "runtime_identity_id", "sbom_id"):
        _content_id(document[field], f"{field.upper()}_INVALID")
    _content_ids(
        document["binary_ids"],
        "ENVIRONMENT_BINARY_IDS_INVALID",
        minimum=1,
        sorted_unique=True,
    )
    _content_ids(
        document["dependency_lock_ids"],
        "ENVIRONMENT_LOCK_IDS_INVALID",
        minimum=1,
        sorted_unique=True,
    )
    names = _strings(
        document["environment_variable_names"],
        "ENVIRONMENT_VARIABLE_NAMES_INVALID",
        sorted_unique=True,
    )
    sensitive = ("SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "PRIVATE_KEY")
    if any(any(marker in name.upper() for marker in sensitive) for name in names):
        _fail("SENSITIVE_ENVIRONMENT_NAME_FORBIDDEN")
    _integer(document["capture_epoch_ms"], "ENVIRONMENT_CAPTURE_TIME_INVALID")


def _validate_network_profile(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "adapter",
            "authority_scope",
            "bandwidth_bytes_per_second",
            "disconnect_after_ms",
            "duplicate_ppm",
            "duration_ms",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "jitter_ms",
            "label",
            "loss_ppm",
            "partition_after_ms",
            "primary_eligible",
            "reorder_ppm",
            "rtt_ms",
            "schema_version",
            "seed",
            "type_name",
        },
        "NETWORK_PROFILE_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_NETWORK_PROFILE")
    _non_promotable(document)
    if document["label"] != "SIMULATED":
        _fail("NETWORK_LABEL_MUST_BE_SIMULATED")
    if document["adapter"] not in {"UNPRIVILEGED_LOGICAL", "OPTIONAL_TC_NETEM"}:
        _fail("NETWORK_ADAPTER_INVALID")
    for field in (
        "bandwidth_bytes_per_second",
        "duration_ms",
        "rtt_ms",
        "seed",
    ):
        _integer(document[field], f"{field.upper()}_INVALID", minimum=1)
    for field in ("duplicate_ppm", "jitter_ms", "loss_ppm", "reorder_ppm"):
        value = _integer(document[field], f"{field.upper()}_INVALID")
        if field.endswith("ppm") and value > 1_000_000:
            _fail(f"{field.upper()}_INVALID")
    duration = int(document["duration_ms"])
    for field in ("disconnect_after_ms", "partition_after_ms"):
        value = document[field]
        if value is not None and _integer(value, f"{field.upper()}_INVALID", minimum=1) >= duration:
            _fail(f"{field.upper()}_INVALID")


def _validate_fault_profile(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "duration_ms",
            "events",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "label",
            "primary_eligible",
            "schema_version",
            "seed",
            "type_name",
        },
        "FAULT_PROFILE_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_FAULT_PROFILE")
    _non_promotable(document)
    if document["label"] != "SIMULATED":
        _fail("FAULT_LABEL_MUST_BE_SIMULATED")
    duration = _integer(document["duration_ms"], "FAULT_DURATION_INVALID", minimum=1)
    _integer(document["seed"], "FAULT_SEED_INVALID")
    events = document["events"]
    if not isinstance(events, list) or not events:
        _fail("FAULT_EVENTS_INVALID")
    order: list[tuple[int, str]] = []
    identifiers: set[str] = set()
    for raw in events:
        event = _exact(
            raw,
            {"at_ms", "event_id", "expected_terminal", "kind", "target"},
            "FAULT_EVENT_FIELDS_INVALID",
        )
        event_id = _identifier(event["event_id"], "FAULT_EVENT_ID_INVALID")
        if event_id in identifiers:
            _fail("FAULT_EVENT_DUPLICATE")
        identifiers.add(event_id)
        at_ms = _integer(event["at_ms"], "FAULT_EVENT_TIME_INVALID")
        if at_ms >= duration:
            _fail("FAULT_EVENT_TIME_INVALID")
        if event["kind"] not in {
            "WORKER_CRASH",
            "WORKER_RESTART",
            "VALIDATOR_CRASH",
            "VALIDATOR_RESTART",
            "STORAGE_CRASH",
            "STORAGE_RESTART",
            "REGION_PARTITION",
            "REGION_RESTORE",
            "DISPERSED_CHURN",
            "CONCENTRATED_CHURN",
        }:
            _fail("FAULT_EVENT_KIND_INVALID")
        _identifier(event["target"], "FAULT_EVENT_TARGET_INVALID")
        if event["expected_terminal"] not in {"CONTINUE", "SAFE_ABORT", "RECOVER"}:
            _fail("FAULT_EXPECTED_TERMINAL_INVALID")
        if event["expected_terminal"] != FAULT_EXPECTED_TERMINALS[event["kind"]]:
            _fail("FAULT_EXPECTED_TERMINAL_MISMATCH")
        order.append((at_ms, event_id))
    if order != sorted(order):
        _fail("FAULT_EVENTS_NOT_SORTED")


def _validate_definition(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "B",
            "H",
            "arm_ids",
            "approved_license_ids",
            "authority_scope",
            "decision_function",
            "definition_reviewer_set_id",
            "dependencies",
            "evidence_class",
            "fault_profile_ids",
            "formal_semantics_id",
            "gate_eligible",
            "metrics",
            "missing_run_policy",
            "network_profile_ids",
            "policy",
            "primary_eligible",
            "runtime_identity_id",
            "result_evaluator_set_id",
            "schema_version",
            "scientific_profile_id",
            "type_name",
        },
        "BENCHMARK_DEFINITION_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_DEFINITION")
    _non_promotable(document)
    _integer(document["B"], "B_INVALID", minimum=1)
    _integer(document["H"], "H_INVALID", minimum=1)
    _content_ids(document["arm_ids"], "ARM_IDS_INVALID", minimum=2, sorted_unique=True)
    approved_license_ids = set(
        _content_ids(
            document["approved_license_ids"],
            "APPROVED_LICENSE_IDS_INVALID",
            minimum=1,
            sorted_unique=True,
        )
    )
    _content_ids(
        document["network_profile_ids"],
        "NETWORK_PROFILE_IDS_INVALID",
        minimum=1,
        sorted_unique=True,
    )
    _content_ids(
        document["fault_profile_ids"],
        "FAULT_PROFILE_IDS_INVALID",
        minimum=1,
        sorted_unique=True,
    )
    _content_id(document["runtime_identity_id"], "RUNTIME_IDENTITY_ID_INVALID")
    _content_id(document["scientific_profile_id"], "SCIENTIFIC_PROFILE_ID_INVALID")
    _content_id(
        document["definition_reviewer_set_id"],
        "DEFINITION_REVIEWER_SET_ID_INVALID",
    )
    _content_id(document["result_evaluator_set_id"], "RESULT_EVALUATOR_SET_ID_INVALID")
    if document["definition_reviewer_set_id"] == document["result_evaluator_set_id"]:
        _fail("GOVERNANCE_ROLE_SETS_MUST_DIFFER")
    if document["decision_function"] != "ALL_MANDATORY":
        _fail("DECISION_FUNCTION_INVALID")
    if document["missing_run_policy"] != "FAIL_CLOSED":
        _fail("MISSING_RUN_POLICY_INVALID")
    policy = _exact(
        document["policy"],
        {
            "accept_stale",
            "adaptive_h",
            "consensus_arithmetic",
            "current_authority",
            "threshold_override",
        },
        "DEFINITION_POLICY_FIELDS_INVALID",
    )
    if policy != {
        "accept_stale": False,
        "adaptive_h": False,
        "consensus_arithmetic": "CHECKED_FIXED_POINT",
        "current_authority": "NATIVE_RUNTIME",
        "threshold_override": False,
    }:
        _fail("ZERO_TOLERANCE_POLICY_VIOLATION")
    dependencies = document["dependencies"]
    if not isinstance(dependencies, list) or not dependencies:
        _fail("DEPENDENCIES_INVALID")
    names: list[str] = []
    for raw in dependencies:
        dependency = _exact(
            raw,
            {
                "access_policy",
                "availability",
                "content_id",
                "license_id",
                "locator",
                "name",
            },
            "DEPENDENCY_FIELDS_INVALID",
        )
        names.append(_identifier(dependency["name"], "DEPENDENCY_NAME_INVALID"))
        digest = _content_id(dependency["content_id"], "DEPENDENCY_CONTENT_ID_INVALID")
        license_id = _content_id(dependency["license_id"], "DEPENDENCY_LICENSE_ID_INVALID")
        if license_id not in approved_license_ids:
            _fail("DEPENDENCY_LICENSE_NOT_APPROVED")
        if dependency["access_policy"] not in {"PUBLIC_FIXTURE", "RESTRICTED_LOCAL"}:
            _fail("DEPENDENCY_ACCESS_POLICY_INVALID")
        if dependency["availability"] != "VERIFIED_IMMUTABLE":
            _fail("DEPENDENCY_AVAILABILITY_INVALID")
        locator = _string(dependency["locator"], "DEPENDENCY_LOCATOR_INVALID")
        if locator != f"cas://sha256/{digest.removeprefix('sha256:')}":
            _fail("MUTABLE_DEPENDENCY_FORBIDDEN")
    if names != sorted(names) or len(names) != len(set(names)):
        _fail("DEPENDENCIES_NOT_SORTED_UNIQUE")
    if {
        str(dependency["license_id"]) for dependency in dependencies if isinstance(dependency, dict)
    } != approved_license_ids:
        _fail("APPROVED_LICENSE_SET_NOT_EXACT")
    metrics = document["metrics"]
    if not isinstance(metrics, list) or not metrics:
        _fail("METRICS_INVALID")
    metric_ids: list[str] = []
    for raw in metrics:
        metric = _exact(
            raw,
            {
                "aggregation",
                "direction",
                "mandatory",
                "metric_id",
                "missing_rule",
                "threshold",
            },
            "METRIC_FIELDS_INVALID",
        )
        metric_ids.append(_identifier(metric["metric_id"], "METRIC_ID_INVALID"))
        if metric["direction"] not in {"EXACT", "HIGHER", "LOWER"}:
            _fail("METRIC_DIRECTION_INVALID")
        if metric["aggregation"] not in {"ALL", "MEAN", "MEDIAN", "P95", "P99"}:
            _fail("METRIC_AGGREGATION_INVALID")
        if metric["missing_rule"] != "FAIL":
            _fail("METRIC_MISSING_RULE_INVALID")
        _boolean(metric["mandatory"], "METRIC_MANDATORY_INVALID")
        _rational(metric["threshold"], "METRIC_THRESHOLD_INVALID")
    if metric_ids != sorted(metric_ids) or len(metric_ids) != len(set(metric_ids)):
        _fail("METRICS_NOT_SORTED_UNIQUE")


def validate_scientific_dependencies(
    definition: CanonicalContract,
    scientific_profile: CanonicalContract,
) -> None:
    """Join every immutable scientific input to one approved dependency entry."""

    if definition.type_name != "BENCHMARK_DEFINITION":
        _fail("DEPENDENCY_JOIN_DEFINITION_TYPE_INVALID")
    if scientific_profile.type_name != "BENCHMARK_SCIENTIFIC_PROFILE":
        _fail("DEPENDENCY_JOIN_SCIENCE_TYPE_INVALID")
    definition_document = definition.to_dict()
    science = scientific_profile.to_dict()
    expected: dict[str, str] = {
        "dataset": str(science["dataset_id"]),
        "model": str(science["model_id"]),
        "optimizer": str(science["optimizer_id"]),
        "ticket-plan": str(science["ticket_plan_id"]),
        "tokenizer": str(science["tokenizer_id"]),
    }
    expected.update(
        {
            f"evaluator-{index:03d}": str(identifier)
            for index, identifier in enumerate(science["evaluator_ids"])
        }
    )
    expected.update(
        {
            f"ticket-{index:03d}": str(identifier)
            for index, identifier in enumerate(science["ticket_ids"])
        }
    )
    actual = {
        str(item["name"]): str(item["content_id"]) for item in definition_document["dependencies"]
    }
    if actual != expected:
        _fail("SCIENTIFIC_DEPENDENCY_JOIN_MISMATCH")


def _validate_arm(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "adapter_id",
            "arm_kind",
            "authority_scope",
            "deployment_profile",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "model_mode",
            "primary_eligible",
            "schema_version",
            "topology",
            "type_name",
        },
        "BENCHMARK_ARM_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_ARM")
    _non_promotable(document)
    _content_id(document["adapter_id"], "ARM_ADAPTER_ID_INVALID")
    if document["arm_kind"] not in {"REFERENCE", "DELTAREDUCE"}:
        _fail("ARM_KIND_INVALID")
    if document["model_mode"] not in {"FULL_MODEL", "QLORA_ADAPTER"}:
        _fail("ARM_MODEL_MODE_INVALID")
    if document["deployment_profile"] not in {"EMBEDDED_FFM", "ISOLATED_SIDECAR"}:
        _fail("ARM_DEPLOYMENT_PROFILE_INVALID")
    if document["topology"] not in {"FLAT", "HIERARCHICAL"}:
        _fail("ARM_TOPOLOGY_INVALID")


def _validate_bound_artifact(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "artifact_id",
            "artifact_kind",
            "authority_scope",
            "byte_length",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "license_id",
            "media_type",
            "name",
            "primary_eligible",
            "schema_version",
            "type_name",
        },
        "BOUND_ARTIFACT_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_BOUND_ARTIFACT")
    _non_promotable(document)
    _fixture_only(document)
    _content_id(document["artifact_id"], "BOUND_ARTIFACT_ID_INVALID")
    _identifier(document["artifact_kind"], "BOUND_ARTIFACT_KIND_INVALID")
    _integer(document["byte_length"], "BOUND_ARTIFACT_LENGTH_INVALID")
    _identifier(document["name"], "BOUND_ARTIFACT_NAME_INVALID")
    if document["media_type"] != "application/octet-stream":
        _fail("BOUND_ARTIFACT_MEDIA_TYPE_INVALID")
    license_id = document["license_id"]
    if license_id is not None:
        _content_id(license_id, "BOUND_ARTIFACT_LICENSE_ID_INVALID")


def _validate_run_manifest(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "arm_id",
            "authority_scope",
            "benchmark_definition_id",
            "environment_manifest_id",
            "evidence_class",
            "execution_authorization_id",
            "execution_mode",
            "fault_profile_id",
            "formal_semantics_id",
            "gate_eligible",
            "network_profile_id",
            "primary_eligible",
            "repetition",
            "run_id",
            "schema_version",
            "scientific_profile_id",
            "seed",
            "stage_receipt_ids",
            "status",
            "ticket_ids",
            "type_name",
        },
        "RUN_MANIFEST_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_RUN_MANIFEST")
    _non_promotable(document)
    for field in (
        "arm_id",
        "benchmark_definition_id",
        "environment_manifest_id",
        "fault_profile_id",
        "network_profile_id",
        "scientific_profile_id",
    ):
        _content_id(document[field], f"{field.upper()}_INVALID")
    _identifier(document["run_id"], "RUN_ID_INVALID")
    _integer(document["seed"], "RUN_SEED_INVALID")
    _integer(document["repetition"], "RUN_REPETITION_INVALID", minimum=1)
    _content_ids(document["ticket_ids"], "RUN_TICKET_IDS_INVALID", minimum=1, sorted_unique=True)
    receipts = _content_ids(document["stage_receipt_ids"], "RUN_RECEIPTS_INVALID")
    if document["status"] == "PLANNED":
        if (
            receipts
            or document["execution_authorization_id"] is not None
            or document["execution_mode"] != "PLAN_ONLY"
        ):
            _fail("PLANNED_RUN_CANNOT_HAVE_EXECUTION_EVIDENCE")
    elif document["status"] == "FIXTURE_COMPLETE":
        if len(receipts) != 3:
            _fail("FIXTURE_RUN_RECEIPT_CHAIN_INCOMPLETE")
        if len(document["ticket_ids"]) != 1:
            _fail("FIXTURE_RUN_REQUIRES_ONE_TICKET")
        if document["execution_authorization_id"] is not None:
            _fail("FIXTURE_EXECUTION_AUTHORITY_FORBIDDEN")
        if document["execution_mode"] != "CONFORMANCE_FIXTURE":
            _fail("FIXTURE_EXECUTION_MODE_INVALID")
    else:
        _fail("RUN_STATUS_INVALID")
    if document["execution_mode"] not in {"PLAN_ONLY", "CONFORMANCE_FIXTURE"}:
        _fail("RUN_EXECUTION_MODE_FORBIDDEN")


def _validate_stage_receipt(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "arm_id",
            "authority_scope",
            "benchmark_definition_id",
            "component_identity_id",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "input_ids",
            "native_opaque_refs",
            "output_ids",
            "previous_receipt_id",
            "primary_eligible",
            "run_id",
            "schema_version",
            "sequence",
            "source_commit",
            "stage",
            "ticket_id",
            "type_name",
        },
        "STAGE_RECEIPT_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_STAGE_RECEIPT")
    _non_promotable(document)
    _fixture_only(document)
    for field in ("arm_id", "benchmark_definition_id", "component_identity_id", "ticket_id"):
        _content_id(document[field], f"{field.upper()}_INVALID")
    _identifier(document["run_id"], "RECEIPT_RUN_ID_INVALID")
    _git_id(document["source_commit"], "RECEIPT_SOURCE_COMMIT_INVALID")
    _content_ids(document["input_ids"], "RECEIPT_INPUT_IDS_INVALID", minimum=1, sorted_unique=True)
    _content_ids(
        document["output_ids"], "RECEIPT_OUTPUT_IDS_INVALID", minimum=1, sorted_unique=True
    )
    stages = {"WORKER_PYTHON": 1, "TRANSPORT_JAVA_NETTY": 2, "NATIVE_CPP_WAL": 3}
    stage = document["stage"]
    if stage not in stages or document["sequence"] != stages[stage]:
        _fail("RECEIPT_STAGE_SEQUENCE_INVALID")
    previous = document["previous_receipt_id"]
    if stage == "WORKER_PYTHON":
        if previous is not None:
            _fail("FIRST_RECEIPT_PREDECESSOR_FORBIDDEN")
    else:
        _content_id(previous, "RECEIPT_PREDECESSOR_INVALID")
    native_refs = document["native_opaque_refs"]
    if stage == "NATIVE_CPP_WAL":
        refs = _exact(
            native_refs,
            {
                "checkpoint_id",
                "durability_evidence_id",
                "effect_id",
                "state_root_id",
                "submit_receipt_id",
                "wal_record_id",
            },
            "NATIVE_OPAQUE_REFS_INVALID",
        )
        for field, value in refs.items():
            _content_id(value, f"NATIVE_{field.upper()}_INVALID")
    elif native_refs != {}:
        _fail("NATIVE_OPAQUE_REFS_STAGE_INVALID")


def _validate_evidence_node(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "benchmark_definition_id",
            "dependencies",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "kind",
            "media_type",
            "ordinal",
            "payload_id",
            "primary_eligible",
            "run_id",
            "schema_id",
            "schema_version",
            "type_name",
        },
        "EVIDENCE_NODE_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_EVIDENCE_NODE")
    _non_promotable(document)
    _fixture_only(document)
    _content_id(document["benchmark_definition_id"], "EVIDENCE_DEFINITION_ID_INVALID")
    _identifier(document["run_id"], "EVIDENCE_RUN_ID_INVALID")
    _content_id(document["payload_id"], "EVIDENCE_PAYLOAD_ID_INVALID")
    _content_ids(document["dependencies"], "EVIDENCE_DEPENDENCIES_INVALID", sorted_unique=True)
    _identifier(document["kind"], "EVIDENCE_KIND_INVALID")
    _integer(document["ordinal"], "EVIDENCE_ORDINAL_INVALID")
    _string(document["media_type"], "EVIDENCE_MEDIA_TYPE_INVALID")
    schema_id = _string(document["schema_id"], "EVIDENCE_SCHEMA_ID_INVALID")
    if _SCHEMA_ID.fullmatch(schema_id) is None:
        _fail("EVIDENCE_SCHEMA_ID_INVALID")


def _validate_metrics(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "byte_counters",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "gpu_metrics",
            "phase_timings",
            "primary_eligible",
            "resource_metrics",
            "run_id",
            "schema_version",
            "type_name",
        },
        "METRICS_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_METRICS")
    _non_promotable(document)
    _fixture_only(document)
    _identifier(document["run_id"], "METRICS_RUN_ID_INVALID")
    phases = document["phase_timings"]
    if not isinstance(phases, list) or not phases:
        _fail("PHASE_TIMINGS_INVALID")
    previous_end = 0
    phase_names: set[str] = set()
    for raw in phases:
        phase = _exact(raw, {"end_ns", "phase", "start_ns"}, "PHASE_TIMING_FIELDS_INVALID")
        name = _identifier(phase["phase"], "PHASE_NAME_INVALID")
        start = _integer(phase["start_ns"], "PHASE_START_INVALID")
        end = _integer(phase["end_ns"], "PHASE_END_INVALID", minimum=1)
        if name in phase_names or start < previous_end or end <= start:
            _fail("PHASE_TIMINGS_OVERLAP_OR_ORDER_INVALID")
        phase_names.add(name)
        previous_end = end
    if tuple(str(raw["phase"]) for raw in phases) != REQUIRED_METRIC_PHASES:
        _fail("PHASE_TIMING_SET_INVALID")
    counters = document["byte_counters"]
    if not isinstance(counters, dict) or tuple(counters) != REQUIRED_BYTE_COUNTERS:
        _fail("BYTE_COUNTERS_INVALID")
    for value in counters.values():
        _integer(value, "BYTE_COUNTER_VALUE_INVALID")
    gpu = _exact(
        document["gpu_metrics"],
        {"device_id", "memory_peak_bytes", "sample_count", "utilization_basis_points"},
        "GPU_METRICS_FIELDS_INVALID",
    )
    _content_id(gpu["device_id"], "GPU_DEVICE_ID_INVALID")
    _integer(gpu["memory_peak_bytes"], "GPU_MEMORY_INVALID")
    _integer(gpu["sample_count"], "GPU_SAMPLE_COUNT_INVALID")
    if _integer(gpu["utilization_basis_points"], "GPU_UTILIZATION_INVALID") > 10_000:
        _fail("GPU_UTILIZATION_INVALID")
    resources = _exact(
        document["resource_metrics"],
        {"cpu_time_ns", "peak_rss_bytes", "p2p_bytes"},
        "RESOURCE_METRICS_FIELDS_INVALID",
    )
    for field, value in resources.items():
        _integer(value, f"RESOURCE_{field.upper()}_INVALID")
    if resources["p2p_bytes"] != counters["p2p_bytes"]:
        _fail("METRICS_P2P_BYTES_MISMATCH")


def _validate_evidence_manifest(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "benchmark_definition_id",
            "definition_reviewer_set_id",
            "definition_qc_id",
            "evidence_class",
            "formal_semantics_id",
            "gate_eligible",
            "node_ids",
            "primary_eligible",
            "required_kinds",
            "run_ids",
            "schema_version",
            "type_name",
        },
        "EVIDENCE_MANIFEST_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_EVIDENCE_MANIFEST")
    _non_promotable(document)
    _fixture_only(document)
    _content_id(document["benchmark_definition_id"], "MANIFEST_DEFINITION_ID_INVALID")
    reviewer_set_id = document["definition_reviewer_set_id"]
    definition_qc_id = document["definition_qc_id"]
    _content_id(reviewer_set_id, "MANIFEST_DEFINITION_REVIEWER_SET_ID_INVALID")
    if definition_qc_id is not None:
        _content_id(definition_qc_id, "MANIFEST_DEFINITION_QC_ID_INVALID")
    _content_ids(document["node_ids"], "MANIFEST_NODE_IDS_INVALID", minimum=1, sorted_unique=True)
    _strings(
        document["required_kinds"],
        "MANIFEST_REQUIRED_KINDS_INVALID",
        minimum=1,
        sorted_unique=True,
    )
    _strings(document["run_ids"], "MANIFEST_RUN_IDS_INVALID", minimum=1, sorted_unique=True)


def _validate_result(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "benchmark_definition_id",
            "commentary",
            "decision",
            "evidence_class",
            "evidence_manifest_id",
            "failed_gates",
            "formal_semantics_id",
            "gate_eligible",
            "gate_table",
            "limitations",
            "missing_evidence",
            "primary_eligible",
            "result_evaluator_set_id",
            "run_ids",
            "schema_version",
            "type_name",
        },
        "BENCHMARK_RESULT_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_RESULT")
    _non_promotable(document)
    _fixture_only(document)
    _content_id(document["benchmark_definition_id"], "RESULT_DEFINITION_ID_INVALID")
    _content_id(document["evidence_manifest_id"], "RESULT_MANIFEST_ID_INVALID")
    _content_id(document["result_evaluator_set_id"], "RESULT_EVALUATOR_SET_ID_INVALID")
    _strings(document["run_ids"], "RESULT_RUN_IDS_INVALID", minimum=1, sorted_unique=True)
    for field in ("failed_gates", "limitations", "missing_evidence"):
        _strings(document[field], f"RESULT_{field.upper()}_INVALID", sorted_unique=True)
    if document["decision"] not in {"GO", "NO_GO", "NOT_EVALUATED"}:
        _fail("RESULT_DECISION_INVALID")
    if document["decision"] == "GO":
        _fail("NON_PROMOTABLE_RESULT_GO_FORBIDDEN")
    _string(document["commentary"], "RESULT_COMMENTARY_INVALID")
    gates = document["gate_table"]
    if not isinstance(gates, list) or not gates:
        _fail("RESULT_GATE_TABLE_INVALID")
    gate_ids: list[str] = []
    failed_gate_ids: list[str] = []
    missing_gate_ids: list[str] = []
    mandatory_incomplete = False
    for raw in gates:
        gate = _exact(raw, {"gate_id", "mandatory", "status"}, "RESULT_GATE_FIELDS_INVALID")
        gate_ids.append(_identifier(gate["gate_id"], "RESULT_GATE_ID_INVALID"))
        mandatory = _boolean(gate["mandatory"], "RESULT_GATE_MANDATORY_INVALID")
        if gate["status"] not in {"PASS", "FAIL", "MISSING"}:
            _fail("RESULT_GATE_STATUS_INVALID")
        if gate["status"] == "FAIL":
            failed_gate_ids.append(gate_ids[-1])
        elif gate["status"] == "MISSING":
            missing_gate_ids.append(gate_ids[-1])
        if mandatory and gate["status"] != "PASS":
            mandatory_incomplete = True
    if gate_ids != sorted(gate_ids) or len(gate_ids) != len(set(gate_ids)):
        _fail("RESULT_GATES_NOT_SORTED_UNIQUE")
    if tuple(document["failed_gates"]) != tuple(failed_gate_ids):
        _fail("RESULT_FAILED_GATES_MISMATCH")
    if tuple(document["missing_evidence"]) != tuple(missing_gate_ids):
        _fail("RESULT_MISSING_EVIDENCE_MISMATCH")
    expected_decision = "NO_GO" if mandatory_incomplete else "NOT_EVALUATED"
    if document["decision"] != expected_decision:
        _fail("RESULT_DECISION_MISMATCH")


def _validate_attestation_manifest(document: dict[str, Any]) -> None:
    _exact(
        document,
        {
            "authority_scope",
            "benchmark_result_id",
            "benchmark_result_qc_id",
            "definition_reviewer_set_id",
            "evidence_class",
            "evidence_manifest_id",
            "formal_semantics_id",
            "gate_eligible",
            "primary_eligible",
            "result_evaluator_set_id",
            "schema_version",
            "type_name",
        },
        "ATTESTATION_MANIFEST_FIELDS_INVALID",
    )
    _base(document, "BENCHMARK_ATTESTATION_MANIFEST")
    _non_promotable(document)
    _fixture_only(document)
    for field in (
        "benchmark_result_id",
        "definition_reviewer_set_id",
        "evidence_manifest_id",
        "result_evaluator_set_id",
    ):
        _content_id(document[field], f"ATTESTATION_{field.upper()}_INVALID")
    result_qc_id = document["benchmark_result_qc_id"]
    if result_qc_id is not None:
        _content_id(result_qc_id, "ATTESTATION_RESULT_QC_ID_INVALID")


_VALIDATORS = {
    "BENCHMARK_ARM": _validate_arm,
    "BENCHMARK_ATTESTATION_MANIFEST": _validate_attestation_manifest,
    "BENCHMARK_BOUND_ARTIFACT": _validate_bound_artifact,
    "BENCHMARK_DEFINITION": _validate_definition,
    "BENCHMARK_ENVIRONMENT_MANIFEST": _validate_environment_manifest,
    "BENCHMARK_EVIDENCE_MANIFEST": _validate_evidence_manifest,
    "BENCHMARK_EVIDENCE_NODE": _validate_evidence_node,
    "BENCHMARK_FAULT_PROFILE": _validate_fault_profile,
    "BENCHMARK_NETWORK_PROFILE": _validate_network_profile,
    "BENCHMARK_RESULT": _validate_result,
    "BENCHMARK_RUN_MANIFEST": _validate_run_manifest,
    "BENCHMARK_RUNTIME_IDENTITY": _validate_runtime_identity,
    "BENCHMARK_METRICS": _validate_metrics,
    "BENCHMARK_SCIENTIFIC_PROFILE": _validate_scientific_profile,
    "BENCHMARK_STAGE_RECEIPT": _validate_stage_receipt,
}


@dataclass(frozen=True, slots=True)
class CanonicalContract:
    """Validated contract stored as immutable canonical bytes."""

    _bytes: bytes

    @classmethod
    def from_dict(cls, document: object) -> CanonicalContract:
        if not isinstance(document, dict):
            _fail("CONTRACT_ROOT_INVALID")
        typed_document = cast(dict[str, Any], document)
        type_name = typed_document.get("type_name")
        if not isinstance(type_name, str) or type_name not in _VALIDATORS:
            _fail("CONTRACT_TYPE_UNSUPPORTED")
        validated_type = cast(str, type_name)
        try:
            encoded = canonical_bytes(typed_document)
        except ValueError as exc:
            raise ContractError("CONTRACT_NOT_CANONICALIZABLE") from exc
        # Round-trip through the strict loader to prevent non-JSON Python values.
        decoded = load_json_bytes(encoded)
        _VALIDATORS[validated_type](decoded)
        return cls(encoded)

    @classmethod
    def from_bytes(cls, value: bytes) -> CanonicalContract:
        return cls.from_dict(load_json_bytes(value))

    @property
    def canonical_bytes(self) -> bytes:
        return self._bytes

    @property
    def content_id(self) -> str:
        return content_id(self._bytes)

    @property
    def type_name(self) -> str:
        return str(self.to_dict()["type_name"])

    def to_dict(self) -> dict[str, Any]:
        value = json.loads(self._bytes)
        if not isinstance(value, dict):
            raise AssertionError("validated contract root changed")
        return value


def validate_contract(document: object) -> CanonicalContract:
    return CanonicalContract.from_dict(document)
