"""Generate and verify canonical feature-007 scheduling contracts and fixtures."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from itertools import pairwise
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SCHEMA_VERSION: Final = "1.0.0"
ROUND_CONFIG_ID: Final = "sha256:" + "a" * 64
PARENT_CHECKPOINT_ID: Final = "sha256:" + "b" * 64
PARAMETER_SCHEMA_ID: Final = "sha256:" + "c" * 64
ARITHMETIC_PROFILE_ID: Final = "sha256:" + "d" * 64
DATASET_MANIFEST_ID: Final = "sha256:" + "e" * 64
ELIGIBILITY_POLICY_ID: Final = "sha256:" + "1" * 64
ASSIGNMENT_POLICY_ID: Final = "sha256:" + "2" * 64
SOFTWARE_BUILD_ID: Final = "sha256:" + "3" * 64

SCHEMAS: Final = {
    "capability-profile": (
        "SCHEMA-CAPABILITY-PROFILE-V1",
        "CAPABILITY_PROFILE",
        "application/vnd.deltareduce.capability-profile+json;version=1",
    ),
    "domain-ticket-policy": (
        "SCHEMA-DOMAIN-TICKET-POLICY-V1",
        "DOMAIN_TICKET_POLICY",
        "application/vnd.deltareduce.domain-ticket-policy+json;version=1",
    ),
    "eligibility-decision": (
        "SCHEMA-ELIGIBILITY-DECISION-V1",
        "ELIGIBILITY_DECISION",
        "application/vnd.deltareduce.eligibility-decision+json;version=1",
    ),
    "infeasibility-report": (
        "SCHEMA-INFEASIBILITY-REPORT-V1",
        "INFEASIBILITY_REPORT",
        "application/vnd.deltareduce.infeasibility-report+json;version=1",
    ),
    "lease-timer-token": (
        "SCHEMA-LEASE-TIMER-TOKEN-V1",
        "LEASE_TIMER_TOKEN",
        "application/vnd.deltareduce.lease-timer-token+json;version=1",
    ),
    "round-ticket-plan": (
        "SCHEMA-ROUND-TICKET-PLAN-V1",
        "ROUND_TICKET_PLAN",
        "application/vnd.deltareduce.round-ticket-plan+json;version=1",
    ),
    "ticket-lease": (
        "SCHEMA-TICKET-LEASE-V1",
        "TICKET_LEASE",
        "application/vnd.deltareduce.ticket-lease+json;version=1",
    ),
    "work-ticket": (
        "SCHEMA-SCHEDULING-WORK-TICKET-V1",
        "SCHEDULING_WORK_TICKET",
        "application/vnd.deltareduce.scheduling-work-ticket+json;version=1",
    ),
}


class ContractError(RuntimeError):
    """Stable fail-closed feature-007 contract error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ContractError(f"{code}:{detail}" if detail else code)


class SchemaValidationError(ValueError):
    """Small deterministic validator error for the frozen schema subset."""


def validate_schema(value: object, schema: dict[str, Any], path: str = "$") -> None:
    if "anyOf" in schema:
        for alternative in schema["anyOf"]:
            try:
                validate_schema(value, alternative, path)
                return
            except SchemaValidationError:
                pass
        raise SchemaValidationError(f"{path}:ANY_OF")
    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}:CONST")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}:ENUM")
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            raise SchemaValidationError(f"{path}:OBJECT")
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise SchemaValidationError(f"{path}:REQUIRED:{','.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise SchemaValidationError(f"{path}:ADDITIONAL:{','.join(extra)}")
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], f"{path}.{key}")
    elif expected_type == "array":
        if not isinstance(value, list):
            raise SchemaValidationError(f"{path}:ARRAY")
        if len(value) < int(schema.get("minItems", 0)):
            raise SchemaValidationError(f"{path}:MIN_ITEMS")
        if schema.get("uniqueItems") and len({canonical_json_bytes(item) for item in value}) != len(
            value
        ):
            raise SchemaValidationError(f"{path}:UNIQUE_ITEMS")
        for index, item in enumerate(value):
            validate_schema(item, schema.get("items", {}), f"{path}[{index}]")
    elif expected_type == "string":
        if not isinstance(value, str):
            raise SchemaValidationError(f"{path}:STRING")
        if len(value) < int(schema.get("minLength", 0)):
            raise SchemaValidationError(f"{path}:MIN_LENGTH")
        if len(value) > int(schema.get("maxLength", len(value))):
            raise SchemaValidationError(f"{path}:MAX_LENGTH")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, value) is None:
            raise SchemaValidationError(f"{path}:PATTERN")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise SchemaValidationError(f"{path}:INTEGER")
        if value < int(schema.get("minimum", value)):
            raise SchemaValidationError(f"{path}:MINIMUM")
        if value > int(schema.get("maximum", value)):
            raise SchemaValidationError(f"{path}:MAXIMUM")
    elif expected_type == "boolean" and not isinstance(value, bool):
        raise SchemaValidationError(f"{path}:BOOLEAN")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def file_json_bytes(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def pretty_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identified(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    encoded = canonical_json_bytes(value)
    return {
        "bytes_hex": encoded.hex(),
        "content_id": f"sha256:{hashlib.sha256(domain.encode() + b'\0' + encoded).hexdigest()}",
        "value": value,
    }


def content_id() -> dict[str, Any]:
    return {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}


def ascii_string() -> dict[str, Any]:
    return {"maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9._:-]+$", "type": "string"}


def uint(maximum: int = 2**31 - 1, minimum: int = 0) -> dict[str, Any]:
    return {"maximum": maximum, "minimum": minimum, "type": "integer"}


def ascii_array(min_items: int = 0) -> dict[str, Any]:
    return {
        "items": ascii_string(),
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }


def strict_object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": required if required is not None else sorted(properties),
        "type": "object",
    }


def common_properties(type_name: str) -> dict[str, Any]:
    return {
        "formal_semantics_id": {"const": FORMAL_ID},
        "schema_version": {"const": SCHEMA_VERSION},
        "type_name": {"const": type_name},
    }


def schema_document(name: str, properties: dict[str, Any]) -> dict[str, Any]:
    _, type_name, _ = SCHEMAS[name]
    all_properties = {**common_properties(type_name), **properties}
    return {
        "$id": f"urn:deltareduce:schema:{name}:1",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": all_properties,
        "required": sorted(all_properties),
        "title": f"DeltaReduce {name} v1",
        "type": "object",
    }


def schema_documents() -> dict[str, dict[str, Any]]:
    constraint = strict_object(
        {
            "available_slots": uint(),
            "domain_id": ascii_string(),
            "required_slots": uint(minimum=1),
        }
    )
    plan_policy = strict_object({"domain_id": ascii_string(), "policy_id": content_id()})
    plan_ticket = strict_object({"ticket_content_id": content_id(), "ticket_id": ascii_string()})
    plan_decision = strict_object({"decision_id": content_id(), "worker_id": ascii_string()})
    lease_policy = strict_object(
        {
            "hard_deadline_tick": uint(2**53 - 1, 1),
            "lease_duration_ticks": uint(2**31 - 1, 1),
            "maximum_lease_epochs": uint(1024, 1),
            "maximum_renewals": uint(64),
        }
    )
    return {
        "domain-ticket-policy": schema_document(
            "domain-ticket-policy",
            {
                "allocation_policy": {"enum": ["CONTIGUOUS_NO_OVERLAP"]},
                "arithmetic_profile_id": content_id(),
                "batch_budget": uint(minimum=1),
                "dataset_manifest_id": content_id(),
                "domain_id": ascii_string(),
                "eligibility_policy_id": content_id(),
                "mixture_coefficient_id": content_id(),
                "parameter_schema_id": content_id(),
                "parent_checkpoint_id": content_id(),
                "region_ids": ascii_array(1),
                "round_config_id": content_id(),
                "step_budget": uint(minimum=1),
                "ticket_count": uint(100000, 1),
                "token_cursor_end": uint(2**53 - 1, 1),
                "token_cursor_start": uint(2**53 - 1),
            },
        ),
        "capability-profile": schema_document(
            "capability-profile",
            {
                "arithmetic_profile_id": content_id(),
                "complete_ticket_throughput_milli": uint(2**53 - 1, 1),
                "expires_at_tick": uint(2**53 - 1, 1),
                "identity_epoch": uint(2**31 - 1),
                "max_concurrent_leases": uint(1024, 1),
                "measured_at_tick": uint(2**53 - 1),
                "measurement_artifact_id": content_id(),
                "memory_bytes": uint(2**53 - 1, 1),
                "model_mode": ascii_string(),
                "parameter_schema_id": content_id(),
                "region_id": ascii_string(),
                "round_config_id": content_id(),
                "sample_count": uint(1000000, 1),
                "signature_id": content_id(),
                "software_build_id": content_id(),
                "worker_id": ascii_string(),
            },
        ),
        "eligibility-decision": schema_document(
            "eligibility-decision",
            {
                "allowed_domain_ids": ascii_array(),
                "capability_profile_id": content_id(),
                "decision_tick": uint(2**53 - 1),
                "eligibility_policy_id": content_id(),
                "eligible": {"type": "boolean"},
                "max_concurrent_leases": uint(1024),
                "reason_codes": ascii_array(1),
                "region_route": ascii_string(),
                "round_config_id": content_id(),
                "worker_id": ascii_string(),
            },
        ),
        "work-ticket": schema_document(
            "work-ticket",
            {
                "arithmetic_profile_id": content_id(),
                "batch_budget": uint(minimum=1),
                "domain_id": ascii_string(),
                "normalized_artifact_id": content_id(),
                "parameter_schema_id": content_id(),
                "parent_checkpoint_id": content_id(),
                "policy_id": content_id(),
                "round_config_id": content_id(),
                "step_budget": uint(minimum=1),
                "ticket_id": ascii_string(),
                "token_cursor_end": uint(2**53 - 1, 1),
                "token_cursor_start": uint(2**53 - 1),
            },
        ),
        "round-ticket-plan": schema_document(
            "round-ticket-plan",
            {
                "assignment_policy_id": content_id(),
                "capability_snapshot_root": content_id(),
                "decisions": {"items": plan_decision, "minItems": 1, "type": "array"},
                "lease_policy": lease_policy,
                "parameter_schema_id": content_id(),
                "parent_checkpoint_id": content_id(),
                "policies": {"items": plan_policy, "minItems": 1, "type": "array"},
                "round_config_id": content_id(),
                "tickets": {"items": plan_ticket, "minItems": 1, "type": "array"},
            },
        ),
        "ticket-lease": schema_document(
            "ticket-lease",
            {
                "expiry_tick": uint(2**53 - 1, 1),
                "issue_tick": uint(2**53 - 1),
                "lease_epoch": uint(1024),
                "plan_id": content_id(),
                "prior_lease_id": {"anyOf": [{"const": "NONE"}, content_id()]},
                "region_route": ascii_string(),
                "renewal_count": uint(64),
                "round_config_id": content_id(),
                "state": {"enum": ["ACTIVE"]},
                "ticket_content_id": content_id(),
                "ticket_id": ascii_string(),
                "worker_id": ascii_string(),
            },
        ),
        "lease-timer-token": schema_document(
            "lease-timer-token",
            {
                "effect_kind": {"const": "LEASE_EXPIRY"},
                "expiry_tick": uint(2**53 - 1, 1),
                "lease_epoch": uint(1024),
                "lease_id": content_id(),
                "plan_id": content_id(),
                "round_config_id": content_id(),
                "ticket_id": ascii_string(),
                "token_nonce": content_id(),
                "worker_id": ascii_string(),
            },
        ),
        "infeasibility-report": schema_document(
            "infeasibility-report",
            {
                "assignment_policy_id": content_id(),
                "hard_deadline_tick": uint(2**53 - 1, 1),
                "immutable_policy_ids": {
                    "items": content_id(),
                    "minItems": 1,
                    "type": "array",
                    "uniqueItems": True,
                },
                "outcome": {"const": "INFEASIBLE"},
                "reason_codes": ascii_array(1),
                "round_config_id": content_id(),
                "unmet_constraints": {"items": constraint, "minItems": 1, "type": "array"},
            },
        ),
    }


def base(type_name: str) -> dict[str, Any]:
    return {
        "formal_semantics_id": FORMAL_ID,
        "schema_version": SCHEMA_VERSION,
        "type_name": type_name,
    }


def policy(domain_id: str, ticket_count: int, batch: int, steps: int, end: int) -> dict[str, Any]:
    value = {
        **base("DOMAIN_TICKET_POLICY"),
        "allocation_policy": "CONTIGUOUS_NO_OVERLAP",
        "arithmetic_profile_id": ARITHMETIC_PROFILE_ID,
        "batch_budget": batch,
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "domain_id": domain_id,
        "eligibility_policy_id": ELIGIBILITY_POLICY_ID,
        "mixture_coefficient_id": "sha256:" + ("4" if domain_id == "code" else "5") * 64,
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "parent_checkpoint_id": PARENT_CHECKPOINT_ID,
        "region_ids": ["eu", "us"],
        "round_config_id": ROUND_CONFIG_ID,
        "step_budget": steps,
        "ticket_count": ticket_count,
        "token_cursor_end": end,
        "token_cursor_start": 0,
    }
    return identified("deltareduce.007.domain-ticket-policy.v1", value)


def capability(worker: str, region: str, throughput: int, concurrency: int) -> dict[str, Any]:
    ordinal = "6" if worker == "worker-a" else "7"
    value = {
        **base("CAPABILITY_PROFILE"),
        "arithmetic_profile_id": ARITHMETIC_PROFILE_ID,
        "complete_ticket_throughput_milli": throughput,
        "expires_at_tick": 80,
        "identity_epoch": 7,
        "max_concurrent_leases": concurrency,
        "measured_at_tick": 10,
        "measurement_artifact_id": "sha256:" + ordinal * 64,
        "memory_bytes": 8_589_934_592,
        "model_mode": "QLORA-8GB",
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "region_id": region,
        "round_config_id": ROUND_CONFIG_ID,
        "sample_count": 8,
        "signature_id": "sha256:" + ("8" if worker == "worker-a" else "9") * 64,
        "software_build_id": SOFTWARE_BUILD_ID,
        "worker_id": worker,
    }
    return identified("deltareduce.007.capability-profile.v1", value)


def contract_fixture() -> dict[str, Any]:
    policies = [policy("code", 2, 1024, 8, 4096), policy("text", 1, 2048, 4, 2048)]
    profiles = [capability("worker-a", "eu", 2400, 2), capability("worker-b", "us", 900, 1)]
    decisions = []
    for profile in profiles:
        value = {
            **base("ELIGIBILITY_DECISION"),
            "allowed_domain_ids": ["code", "text"],
            "capability_profile_id": profile["content_id"],
            "decision_tick": 12,
            "eligibility_policy_id": ELIGIBILITY_POLICY_ID,
            "eligible": True,
            "max_concurrent_leases": profile["value"]["max_concurrent_leases"],
            "reason_codes": ["ELIGIBLE"],
            "region_route": profile["value"]["region_id"],
            "round_config_id": ROUND_CONFIG_ID,
            "worker_id": profile["value"]["worker_id"],
        }
        decisions.append(identified("deltareduce.007.eligibility-decision.v1", value))
    tickets = []
    ticket_specs = [
        (policies[0], "ticket-code-000", 0, 2048),
        (policies[0], "ticket-code-001", 2048, 4096),
        (policies[1], "ticket-text-000", 0, 2048),
    ]
    for policy_value, ticket_id, start, end in ticket_specs:
        p = policy_value["value"]
        value = {
            **base("SCHEDULING_WORK_TICKET"),
            "arithmetic_profile_id": p["arithmetic_profile_id"],
            "batch_budget": p["batch_budget"],
            "domain_id": p["domain_id"],
            "normalized_artifact_id": "sha256:" + "0" * 64,
            "parameter_schema_id": p["parameter_schema_id"],
            "parent_checkpoint_id": p["parent_checkpoint_id"],
            "policy_id": policy_value["content_id"],
            "round_config_id": ROUND_CONFIG_ID,
            "step_budget": p["step_budget"],
            "ticket_id": ticket_id,
            "token_cursor_end": end,
            "token_cursor_start": start,
        }
        tickets.append(identified("deltareduce.007.work-ticket.v1", value))
    plan_value = {
        **base("ROUND_TICKET_PLAN"),
        "assignment_policy_id": ASSIGNMENT_POLICY_ID,
        "capability_snapshot_root": "sha256:" + "f" * 64,
        "decisions": [
            {"decision_id": item["content_id"], "worker_id": item["value"]["worker_id"]}
            for item in decisions
        ],
        "lease_policy": {
            "hard_deadline_tick": 100,
            "lease_duration_ticks": 20,
            "maximum_lease_epochs": 3,
            "maximum_renewals": 1,
        },
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "parent_checkpoint_id": PARENT_CHECKPOINT_ID,
        "policies": [
            {"domain_id": item["value"]["domain_id"], "policy_id": item["content_id"]}
            for item in policies
        ],
        "round_config_id": ROUND_CONFIG_ID,
        "tickets": [
            {"ticket_content_id": item["content_id"], "ticket_id": item["value"]["ticket_id"]}
            for item in tickets
        ],
    }
    plan = identified("deltareduce.007.round-ticket-plan.v1", plan_value)
    leases = []
    timers = []
    assignments = [
        (tickets[0], "worker-a", "eu"),
        (tickets[1], "worker-a", "eu"),
        (tickets[2], "worker-b", "us"),
    ]
    for ticket, worker, region in assignments:
        lease_value = {
            **base("TICKET_LEASE"),
            "expiry_tick": 35,
            "issue_tick": 15,
            "lease_epoch": 0,
            "plan_id": plan["content_id"],
            "prior_lease_id": "NONE",
            "region_route": region,
            "renewal_count": 0,
            "round_config_id": ROUND_CONFIG_ID,
            "state": "ACTIVE",
            "ticket_content_id": ticket["content_id"],
            "ticket_id": ticket["value"]["ticket_id"],
            "worker_id": worker,
        }
        lease = identified("deltareduce.007.ticket-lease.v1", lease_value)
        leases.append(lease)
        timer_value = {
            **base("LEASE_TIMER_TOKEN"),
            "effect_kind": "LEASE_EXPIRY",
            "expiry_tick": lease_value["expiry_tick"],
            "lease_epoch": lease_value["lease_epoch"],
            "lease_id": lease["content_id"],
            "plan_id": plan["content_id"],
            "round_config_id": ROUND_CONFIG_ID,
            "ticket_id": lease_value["ticket_id"],
            "token_nonce": "sha256:" + hashlib.sha256(lease["content_id"].encode()).hexdigest(),
            "worker_id": worker,
        }
        timers.append(identified("deltareduce.007.lease-timer-token.v1", timer_value))
    infeasibility_value = {
        **base("INFEASIBILITY_REPORT"),
        "assignment_policy_id": ASSIGNMENT_POLICY_ID,
        "hard_deadline_tick": 100,
        "immutable_policy_ids": [item["content_id"] for item in policies],
        "outcome": "INFEASIBLE",
        "reason_codes": ["DOMAIN_CAPACITY_INSUFFICIENT"],
        "round_config_id": ROUND_CONFIG_ID,
        "unmet_constraints": [{"available_slots": 0, "domain_id": "text", "required_slots": 1}],
    }
    infeasibility = identified("deltareduce.007.infeasibility-report.v1", infeasibility_value)
    return {
        "capability_profiles": profiles,
        "domain_policies": policies,
        "eligibility_decisions": decisions,
        "expected": {
            "domain_ticket_counts": {"code": 2, "text": 1},
            "formal_semantics_id": FORMAL_ID,
            "infeasibility_outcome": "INFEASIBLE",
            "lease_count": 3,
            "plan_id": plan["content_id"],
            "status": "ACCEPT",
        },
        "formal_semantics_id": FORMAL_ID,
        "infeasibility_report": infeasibility,
        "lease_timer_tokens": timers,
        "plan": plan,
        "schema_version": SCHEMA_VERSION,
        "ticket_leases": leases,
        "work_tickets": tickets,
    }


def invalid_fixture(golden: dict[str, Any]) -> dict[str, Any]:
    adaptive = copy.deepcopy(golden["domain_policies"][0]["value"])
    adaptive["adaptive_h"] = True
    weighted = copy.deepcopy(golden["capability_profiles"][0]["value"])
    weighted["device_speed_weight"] = "2"
    empty_quota = copy.deepcopy(golden["domain_policies"][0]["value"])
    empty_quota["ticket_count"] = 0
    bad_timer = copy.deepcopy(golden["lease_timer_tokens"][0]["value"])
    bad_timer["effect_kind"] = "JAVA_REASSIGN"
    mutation = copy.deepcopy(golden)
    mutation["work_tickets"][0]["value"]["step_budget"] += 1
    mutation["work_tickets"][0] = identified(
        "deltareduce.007.work-ticket.v1", mutation["work_tickets"][0]["value"]
    )
    return {
        "cases": [
            {
                "expected_reason": "SCHEMA_ADDITIONAL_PROPERTY",
                "name": "adaptive-step-field",
                "schema": "domain-ticket-policy",
                "validation_layer": "schema",
                "value": adaptive,
            },
            {
                "expected_reason": "SCHEMA_ADDITIONAL_PROPERTY",
                "name": "device-speed-weight-field",
                "schema": "capability-profile",
                "validation_layer": "schema",
                "value": weighted,
            },
            {
                "expected_reason": "SCHEMA_MINIMUM",
                "name": "zero-domain-quota",
                "schema": "domain-ticket-policy",
                "validation_layer": "schema",
                "value": empty_quota,
            },
            {
                "expected_reason": "SCHEMA_CONST",
                "name": "java-reassign-timer",
                "schema": "lease-timer-token",
                "validation_layer": "schema",
                "value": bad_timer,
            },
            {
                "expected_reason": "TICKET_FIXED_WORK_MUTATED",
                "name": "ticket-step-budget-mutation",
                "validation_layer": "semantic",
                "value": mutation,
            },
        ],
        "formal_semantics_id": FORMAL_ID,
        "schema_version": SCHEMA_VERSION,
    }


def unwrap(item: dict[str, Any], domain: str) -> dict[str, Any]:
    value = item.get("value")
    require(isinstance(value, dict), "IDENTIFIED_VALUE_INVALID")
    expected = identified(domain, value)
    require(item == expected, "IDENTIFIED_BYTES_OR_ID_DRIFT", value.get("type_name", "UNKNOWN"))
    return value


def validate_contract(document: dict[str, Any]) -> dict[str, Any]:
    schemas = schema_documents()
    groups = {
        "capability_profiles": ("capability-profile", "deltareduce.007.capability-profile.v1"),
        "domain_policies": ("domain-ticket-policy", "deltareduce.007.domain-ticket-policy.v1"),
        "eligibility_decisions": (
            "eligibility-decision",
            "deltareduce.007.eligibility-decision.v1",
        ),
        "lease_timer_tokens": ("lease-timer-token", "deltareduce.007.lease-timer-token.v1"),
        "ticket_leases": ("ticket-lease", "deltareduce.007.ticket-lease.v1"),
        "work_tickets": ("work-ticket", "deltareduce.007.work-ticket.v1"),
    }
    values: dict[str, list[dict[str, Any]]] = {}
    for group, (schema_name, domain) in groups.items():
        items = document.get(group)
        require(isinstance(items, list) and items, "FIXTURE_GROUP_INVALID", group)
        values[group] = []
        for item in items:
            value = unwrap(item, domain)
            validate_schema(value, schemas[schema_name])
            values[group].append(value)
    plan = unwrap(document["plan"], "deltareduce.007.round-ticket-plan.v1")
    validate_schema(plan, schemas["round-ticket-plan"])
    infeasibility = unwrap(
        document["infeasibility_report"], "deltareduce.007.infeasibility-report.v1"
    )
    validate_schema(infeasibility, schemas["infeasibility-report"])
    policies = {item["domain_id"]: item for item in values["domain_policies"]}
    policy_ids = {
        item["value"]["domain_id"]: item["content_id"] for item in document["domain_policies"]
    }
    tickets_by_domain: dict[str, list[dict[str, Any]]] = {domain: [] for domain in policies}
    for ticket in values["work_tickets"]:
        require(ticket["domain_id"] in policies, "TICKET_DOMAIN_UNKNOWN")
        p = policies[ticket["domain_id"]]
        require(ticket["policy_id"] == policy_ids[ticket["domain_id"]], "TICKET_POLICY_DRIFT")
        require(
            (ticket["batch_budget"], ticket["step_budget"])
            == (p["batch_budget"], p["step_budget"]),
            "TICKET_FIXED_WORK_MUTATED",
            ticket["ticket_id"],
        )
        tickets_by_domain[ticket["domain_id"]].append(ticket)
    for domain, p in policies.items():
        tickets = sorted(tickets_by_domain[domain], key=lambda item: item["token_cursor_start"])
        require(len(tickets) == p["ticket_count"], "DOMAIN_TICKET_COUNT_DRIFT", domain)
        require(
            tickets[0]["token_cursor_start"] == p["token_cursor_start"],
            "DOMAIN_CURSOR_START_DRIFT",
            domain,
        )
        require(
            tickets[-1]["token_cursor_end"] == p["token_cursor_end"],
            "DOMAIN_CURSOR_END_DRIFT",
            domain,
        )
        require(
            all(
                left["token_cursor_end"] == right["token_cursor_start"]
                for left, right in pairwise(tickets)
            ),
            "DOMAIN_CURSOR_GAP_OR_OVERLAP",
            domain,
        )
    ticket_ids = [item["ticket_id"] for item in values["work_tickets"]]
    require(
        ticket_ids == sorted(ticket_ids) and len(ticket_ids) == len(set(ticket_ids)),
        "TICKET_ORDER_OR_DUPLICATE",
    )
    plan_ticket_ids = [item["ticket_id"] for item in plan["tickets"]]
    require(plan_ticket_ids == ticket_ids, "PLAN_TICKET_SET_DRIFT")
    eligible_workers = {
        item["worker_id"] for item in values["eligibility_decisions"] if item["eligible"]
    }
    plan_id = document["plan"]["content_id"]
    leases = values["ticket_leases"]
    require(len({item["ticket_id"] for item in leases}) == len(leases), "LEASE_DUPLICATE_TICKET")
    for lease in leases:
        require(lease["plan_id"] == plan_id, "LEASE_PLAN_DRIFT")
        require(lease["worker_id"] in eligible_workers, "LEASE_WORKER_INELIGIBLE")
        require(lease["ticket_id"] in ticket_ids, "LEASE_TICKET_UNKNOWN")
        require(lease["issue_tick"] < lease["expiry_tick"], "LEASE_DEADLINE_INVALID")
    lease_by_id = {item["content_id"]: item["value"] for item in document["ticket_leases"]}
    for timer in values["lease_timer_tokens"]:
        lease = lease_by_id.get(timer["lease_id"])
        require(lease is not None, "TIMER_LEASE_UNKNOWN")
        require(
            (
                timer["plan_id"],
                timer["ticket_id"],
                timer["worker_id"],
                timer["lease_epoch"],
                timer["expiry_tick"],
            )
            == (
                lease["plan_id"],
                lease["ticket_id"],
                lease["worker_id"],
                lease["lease_epoch"],
                lease["expiry_tick"],
            ),
            "TIMER_CONTEXT_DRIFT",
        )
    require(infeasibility["outcome"] == "INFEASIBLE", "INFEASIBILITY_OUTCOME_INVALID")
    require(
        set(infeasibility["immutable_policy_ids"]) == set(policy_ids.values()),
        "INFEASIBILITY_POLICY_SET_DRIFT",
    )
    return {
        "capability_profile_count": len(values["capability_profiles"]),
        "decision_count": len(values["eligibility_decisions"]),
        "domain_ticket_counts": {
            key: len(value) for key, value in sorted(tickets_by_domain.items())
        },
        "lease_count": len(leases),
        "plan_id": plan_id,
        "status": "PASS",
        "timer_count": len(values["lease_timer_tokens"]),
    }


def validate_invalid(document: dict[str, Any]) -> list[dict[str, str]]:
    schemas = schema_documents()
    results = []
    for case in document["cases"]:
        name = case["name"]
        if case["validation_layer"] == "schema":
            try:
                validate_schema(case["value"], schemas[case["schema"]])
            except SchemaValidationError:
                results.append(
                    {"expected_reason": case["expected_reason"], "name": name, "status": "PASS"}
                )
                continue
            raise ContractError(f"INVALID_FIXTURE_ACCEPTED:{name}")
        try:
            validate_contract(case["value"])
        except ContractError as error:
            require(str(error).startswith(case["expected_reason"]), "INVALID_REASON_DRIFT", name)
            results.append(
                {"expected_reason": case["expected_reason"], "name": name, "status": "PASS"}
            )
            continue
        raise ContractError(f"INVALID_FIXTURE_ACCEPTED:{name}")
    return results


def registry_document(outputs: dict[str, bytes]) -> dict[str, Any]:
    artifacts = []
    media_types = []
    for name, (schema_id, _, media_type) in sorted(SCHEMAS.items()):
        path = f"schemas/007/{name}-v1.json"
        artifacts.append({"id": schema_id, "path": path, "sha256": sha256_bytes(outputs[path])})
        media_types.append(
            {
                "id": schema_id.replace("SCHEMA-", "MEDIA-"),
                "schema_id": schema_id,
                "value": media_type,
            }
        )
    fixtures = []
    for fixture_id, path in (
        ("SCHEDULING007-CROSS-LANGUAGE-GOLDEN-V1", "fixtures/007/cross-language/golden-v1.json"),
        ("SCHEDULING007-NEGATIVE-V1", "fixtures/007/invalid/scheduling-negative-v1.json"),
        ("SCHEDULING007-VALID-CONTRACT-V1", "fixtures/007/valid/scheduling-contract-v1.json"),
    ):
        fixtures.append({"id": fixture_id, "path": path, "sha256": sha256_bytes(outputs[path])})
    return {
        "artifacts": artifacts,
        "fixtures": fixtures,
        "formal_semantics_id": FORMAL_ID,
        "media_types": media_types,
        "registry_version": "007.1.0",
        "schema_version": SCHEMA_VERSION,
        "semantic_completeness_claimed": False,
    }


def replace_prefixed(
    items: list[dict[str, Any]], prefixes: tuple[str, ...], new: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    kept = [
        item for item in items if not any(str(item.get("id", "")).startswith(p) for p in prefixes)
    ]
    return [*kept, *new]


def global_registry(outputs: dict[str, bytes], local: dict[str, Any]) -> dict[str, Any]:
    process = subprocess.run(
        ["git", "show", "HEAD:delta-protocol/registry.json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, "BASE_REGISTRY_READ_FAILED")
    document = json.loads(process.stdout)
    registry_path = "schemas/007/registry-v1.json"
    document["extensions"] = sorted(
        replace_prefixed(
            document["extensions"],
            ("REGISTRY-SCHEDULING-007-",),
            [
                {
                    "id": "REGISTRY-SCHEDULING-007-V1",
                    "path": registry_path,
                    "sha256": sha256_bytes(outputs[registry_path]),
                }
            ],
        ),
        key=lambda item: item["path"],
    )
    document["fixtures"] = sorted(
        replace_prefixed(document["fixtures"], ("SCHEDULING007-",), local["fixtures"]),
        key=lambda item: item["path"],
    )
    document["schemas"] = sorted(
        replace_prefixed(
            document["schemas"],
            tuple(item[0].replace("-V1", "-") for item in SCHEMAS.values()),
            local["artifacts"],
        ),
        key=lambda item: item["path"],
    )
    document["media_types"] = replace_prefixed(
        document["media_types"],
        tuple(
            item[0].replace("SCHEMA-", "MEDIA-").replace("-V1", "-") for item in SCHEMAS.values()
        ),
        local["media_types"],
    )
    return document


def build_outputs() -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    for name, document in schema_documents().items():
        outputs[f"schemas/007/{name}-v1.json"] = pretty_json_bytes(document)
    golden = contract_fixture()
    valid = copy.deepcopy(golden)
    invalid = invalid_fixture(golden)
    outputs["fixtures/007/cross-language/golden-v1.json"] = file_json_bytes(golden)
    outputs["fixtures/007/valid/scheduling-contract-v1.json"] = file_json_bytes(valid)
    outputs["fixtures/007/invalid/scheduling-negative-v1.json"] = file_json_bytes(invalid)
    local = registry_document(outputs)
    outputs["schemas/007/registry-v1.json"] = pretty_json_bytes(local)
    outputs["registry.json"] = pretty_json_bytes(global_registry(outputs, local))
    return outputs


def validate_outputs(outputs: dict[str, bytes]) -> dict[str, Any]:
    golden = json.loads(outputs["fixtures/007/cross-language/golden-v1.json"])
    valid = json.loads(outputs["fixtures/007/valid/scheduling-contract-v1.json"])
    invalid = json.loads(outputs["fixtures/007/invalid/scheduling-negative-v1.json"])
    require(golden == valid, "VALID_FIXTURE_DRIFT")
    valid_result = validate_contract(golden)
    invalid_result = validate_invalid(invalid)
    registry = json.loads(outputs["registry.json"])
    for key in ("extensions", "fixtures", "media_types", "schemas"):
        ids = [item["id"] for item in registry[key]]
        require(len(ids) == len(set(ids)), "REGISTRY_DUPLICATE_ID", key)
    scheduling_media = [
        item["value"]
        for item in registry["media_types"]
        if str(item["id"]).startswith("MEDIA-")
        and item["schema_id"] in {entry[0] for entry in SCHEMAS.values()}
    ]
    require(
        len(scheduling_media) == len(SCHEMAS) == len(set(scheduling_media)),
        "SCHEDULING_MEDIA_TYPE_COLLISION",
    )
    return {
        "formal_semantics_id": FORMAL_ID,
        "invalid_cases": invalid_result,
        "output_count": len(outputs),
        "schema_count": len(SCHEMAS),
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "valid": valid_result,
    }


def write_outputs(outputs: dict[str, bytes]) -> None:
    for relative, content in outputs.items():
        path = ROOT / "delta-protocol" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def check_outputs(outputs: dict[str, bytes]) -> None:
    for relative, expected in outputs.items():
        path = ROOT / "delta-protocol" / relative
        require(path.is_file(), "CONTRACT_OUTPUT_MISSING", relative)
        require(path.read_bytes() == expected, "CONTRACT_OUTPUT_DRIFT", relative)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    require(arguments.check ^ arguments.write, "EXACTLY_ONE_MODE_REQUIRED")
    outputs = build_outputs()
    result = validate_outputs(outputs)
    if arguments.write:
        write_outputs(outputs)
    else:
        check_outputs(outputs)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
