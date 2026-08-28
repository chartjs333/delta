"""Generate frozen feature-006 hierarchy schemas, fixtures and registry entries."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_ROOT = ROOT / "delta-protocol" / "schemas" / "006"
FIXTURE_ROOT = ROOT / "delta-protocol" / "fixtures" / "006"
FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
PROFILE_ID = "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"
SCALE_TABLE_ID = "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205"
SHARD_PLAN_ID = "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1"
CONFIG_ID = "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629"
ACCUMULATOR_PROOF_ID = "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076"
ROUND_CONFIG_ID = "sha256:" + "a" * 64
FROZEN_INPUT_ROOT = "sha256:" + "b" * 64
COEFFICIENT_PLAN_ROOT = "sha256:" + "c" * 64
PARENT_CHECKPOINT_ID = "sha256:" + "d" * 64
HASH_PATTERN = r"^sha256:[0-9a-f]{64}$"
DECIMAL_PATTERN = r"^(0|-?[1-9][0-9]*)$"
REGIONAL_MEDIA = "application/vnd.deltareduce.regional-partial;version=1"
PARAMETER_MEDIA = "application/vnd.deltareduce.parameter-partial;version=1"
INPUT_MEDIA = "application/vnd.deltareduce.input-candidate;version=1"

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def domain_hash(domain: str, value: bytes) -> str:
    return sha256(domain.encode("ascii") + b"\0" + value)


def identified(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    encoded = canonical_json_bytes(value)
    return {"bytes_hex": encoded.hex(), "content_id": domain_hash(domain, encoded), "value": value}


def context() -> dict[str, Any]:
    return {
        "accumulator_proof_instance_id": ACCUMULATOR_PROOF_ID,
        "coefficient_plan_root": COEFFICIENT_PLAN_ROOT,
        "fixedpoint_config_id": CONFIG_ID,
        "formal_semantics_id": FORMAL_ID,
        "frozen_input_root": FROZEN_INPUT_ROOT,
        "parent_checkpoint_id": PARENT_CHECKPOINT_ID,
        "profile_id": PROFILE_ID,
        "round_config_id": ROUND_CONFIG_ID,
        "scale_table_id": SCALE_TABLE_ID,
        "shard_plan_id": SHARD_PLAN_ID,
    }


def region(region_id: str, tickets: list[str], prefix: str) -> dict[str, Any]:
    return {
        "fault_bound": 1,
        "region_id": region_id,
        "tickets": tickets,
        "validator_set": [f"{prefix}-v{index}" for index in range(1, 5)],
    }


def domain(domain_id: str, ticket_count: int, prefix: str) -> dict[str, Any]:
    tickets = [f"{prefix}-ticket-{index:02d}" for index in range(1, ticket_count + 1)]
    split = (1, 3) if ticket_count == 6 else (1, 2)
    return {
        "domain_id": domain_id,
        "global_fault_bound": 1,
        "global_validator_set": [f"{prefix}-global-v{index}" for index in range(1, 5)],
        "regions": [
            region("eu", tickets[: split[0]], f"{prefix}-eu"),
            region("us", tickets[split[0] : split[1]], f"{prefix}-us"),
            region("ap", tickets[split[1] :], f"{prefix}-ap"),
        ],
        "tickets": tickets,
    }


def topology_fixture() -> dict[str, Any]:
    value = {
        **context(),
        "domains": [domain("code", 6, "c"), domain("text", 5, "t")],
        "hard_deadline_tick": 100,
        "schema_version": "1.0.0",
        "shards": [
            {"end_element": 4, "shard_id": "parameter-000", "start_element": 0},
            {"end_element": 8, "shard_id": "parameter-001", "start_element": 4},
        ],
        "soft_deadline_tick": 50,
        "type_name": "REDUCE_TOPOLOGY",
        "validator_epoch": 7,
    }
    return identified("deltareduce.006.reduce-topology.v1", value)


def q_values(ticket_ordinal: int, shard_ordinal: int) -> list[int]:
    base = ticket_ordinal * 7 + shard_ordinal * 3
    return [base + 1, -(base + 2), base + 3, -(base + 4)]


def result_id(value: dict[str, Any], domain: str) -> dict[str, Any]:
    return identified(f"deltareduce.006.{domain}.v1", value)


def hierarchy_proof(topology: dict[str, Any]) -> dict[str, Any]:
    proof_value = {
        **context(),
        "coefficient_abs_max": "6",
        "common_denominator": "1",
        "domain_ticket_counts": {"code": 6, "text": 5},
        "final_abs_bound": "1179612",
        "max_eligible_contributions": 6,
        "product_abs_bound": "196602",
        "q_abs_max": "32767",
        "result": "PASS",
        "schema_version": "1.0.0",
        "selected_accumulator_width_bits": 64,
        "shard_ranges": [[0, 4], [4, 8]],
        "theorems": [
            {"conjuncts": ["exact-partition"], "obligation_id": "PO-H1"},
            {"conjuncts": ["hierarchy-equals-flat"], "obligation_id": "PO-H2"},
            {"conjuncts": ["product-bound"], "obligation_id": "PO-A1"},
            {"conjuncts": ["flat-accumulator-bound"], "obligation_id": "PO-A2"},
            {
                "conjuncts": [
                    "canonical-reduced-input",
                    "input-denominator-divides-common",
                    "numerator-accumulator-bound",
                    "positive-common-denominator",
                    "positive-input-denominator",
                    "round-at-or-above-half",
                    "round-below-half",
                    "round-half-tie-toward-positive",
                    "rounding-deterministic",
                ],
                "obligation_id": "PO-A3",
            },
        ],
        "topology_id": topology["content_id"],
        "type_name": "HIERARCHY_PROOF_INSTANCE",
    }
    return result_id(proof_value, "hierarchy-proof-instance")


def contract_fixture() -> dict[str, Any]:
    topology = topology_fixture()
    proof = hierarchy_proof(topology)
    execution_context = {
        **context(),
        "hierarchy_proof_instance_id": proof["content_id"],
    }
    regional_inputs: list[dict[str, Any]] = []
    regional_results: list[dict[str, Any]] = []
    regional_qcs: list[dict[str, Any]] = []
    global_sets: list[dict[str, Any]] = []
    global_results: list[dict[str, Any]] = []
    global_qcs: list[dict[str, Any]] = []
    aggregate_entries: list[dict[str, Any]] = []
    topology_value = topology["value"]
    for domain_value in topology_value["domains"]:
        all_tickets = domain_value["tickets"]
        for shard_ordinal, shard in enumerate(topology_value["shards"]):
            shard_results: list[dict[str, Any]] = []
            for region_value in domain_value["regions"]:
                contributions = []
                for ticket in region_value["tickets"]:
                    ticket_ordinal = all_tickets.index(ticket) + 1
                    contributions.append(
                        {
                            "coefficient_denominator": "1",
                            "coefficient_numerator": str(ticket_ordinal),
                            "q_values": q_values(ticket_ordinal, shard_ordinal),
                            "ticket_id": ticket,
                            "worker_shard_id": domain_hash(
                                "deltareduce.006.worker-q.v1",
                                f"{domain_value['domain_id']}:{ticket}:{shard['shard_id']}".encode(),
                            ),
                        }
                    )
                input_value = {
                    **execution_context,
                    "committee_epoch": 7,
                    "contributions": contributions,
                    "domain_id": domain_value["domain_id"],
                    "region_id": region_value["region_id"],
                    "schema_version": "1.0.0",
                    "shard_id": shard["shard_id"],
                    "topology_id": topology["content_id"],
                    "type_name": "REGIONAL_INPUT_SET",
                }
                input_set = result_id(input_value, "regional-input-set")
                regional_inputs.append(input_set)
                numerator = [
                    sum(
                        int(item["coefficient_numerator"]) * item["q_values"][index]
                        for item in contributions
                    )
                    for index in range(4)
                ]
                result_value = {
                    **execution_context,
                    "coefficient_denominator": "1",
                    "coefficient_numerator_sum": str(
                        sum(int(item["coefficient_numerator"]) for item in contributions)
                    ),
                    "domain_id": domain_value["domain_id"],
                    "eligible_count": len(contributions),
                    "numerator": [str(value) for value in numerator],
                    "region_id": region_value["region_id"],
                    "regional_input_set_id": input_set["content_id"],
                    "schema_version": "1.0.0",
                    "shard_id": shard["shard_id"],
                    "topology_id": topology["content_id"],
                    "type_name": "REGIONAL_SHARD_RESULT",
                }
                regional_result = result_id(result_value, "regional-shard-result")
                regional_results.append(regional_result)
                shard_results.append(regional_result)
                qc_value = {
                    **execution_context,
                    "body_id": regional_result["content_id"],
                    "committee_epoch": 7,
                    "domain_id": domain_value["domain_id"],
                    "phase": "REGIONAL_RESULT",
                    "quorum_threshold": 3,
                    "region_id": region_value["region_id"],
                    "schema_version": "1.0.0",
                    "shard_id": shard["shard_id"],
                    "signer_ids": region_value["validator_set"][:3],
                    "topology_id": topology["content_id"],
                    "type_name": "REGIONAL_SHARD_QC",
                    "view": 0,
                }
                regional_qcs.append(result_id(qc_value, "regional-shard-qc"))
            set_value = {
                **execution_context,
                "domain_id": domain_value["domain_id"],
                "regional_results": [
                    {
                        "region_id": item["value"]["region_id"],
                        "regional_result_id": item["content_id"],
                    }
                    for item in shard_results
                ],
                "required_regions": [item["region_id"] for item in domain_value["regions"]],
                "schema_version": "1.0.0",
                "shard_id": shard["shard_id"],
                "topology_id": topology["content_id"],
                "type_name": "GLOBAL_REGIONAL_SET",
            }
            global_set = result_id(set_value, "global-regional-set")
            global_sets.append(global_set)
            global_value = {
                **execution_context,
                "coefficient_denominator": "1",
                "coefficient_numerator_sum": str(
                    sum(int(item["value"]["coefficient_numerator_sum"]) for item in shard_results)
                ),
                "domain_id": domain_value["domain_id"],
                "eligible_count": sum(item["value"]["eligible_count"] for item in shard_results),
                "global_regional_set_id": global_set["content_id"],
                "numerator": [
                    str(sum(int(item["value"]["numerator"][index]) for item in shard_results))
                    for index in range(4)
                ],
                "schema_version": "1.0.0",
                "shard_id": shard["shard_id"],
                "topology_id": topology["content_id"],
                "type_name": "GLOBAL_PARAMETER_RESULT",
            }
            global_result = result_id(global_value, "global-parameter-result")
            global_results.append(global_result)
            qc_value = {
                **execution_context,
                "body_id": global_result["content_id"],
                "committee_epoch": 7,
                "domain_id": domain_value["domain_id"],
                "phase": "GLOBAL_PARAMETER_RESULT",
                "quorum_threshold": 3,
                "schema_version": "1.0.0",
                "shard_id": shard["shard_id"],
                "signer_ids": domain_value["global_validator_set"][:3],
                "topology_id": topology["content_id"],
                "type_name": "GLOBAL_PARAMETER_QC",
                "view": 0,
            }
            global_qc = result_id(qc_value, "global-parameter-qc")
            global_qcs.append(global_qc)
            aggregate_entries.append(
                {
                    "domain_id": domain_value["domain_id"],
                    "global_parameter_qc_id": global_qc["content_id"],
                    "global_parameter_result_id": global_result["content_id"],
                    "shard_id": shard["shard_id"],
                }
            )
    aggregate_value = {
        **execution_context,
        "coverage": aggregate_entries,
        "hierarchy_proof_instance_id": proof["content_id"],
        "required_domain_shards": [
            {"domain_id": domain_value["domain_id"], "shard_id": shard["shard_id"]}
            for domain_value in topology_value["domains"]
            for shard in topology_value["shards"]
        ],
        "schema_version": "1.0.0",
        "topology_id": topology["content_id"],
        "type_name": "HIERARCHICAL_AGGREGATE_ROOT",
    }
    aggregate = result_id(aggregate_value, "hierarchical-aggregate-root")
    return {
        "aggregate_root": aggregate,
        "formal_semantics_id": FORMAL_ID,
        "global_parameter_qcs": global_qcs,
        "global_parameter_results": global_results,
        "global_regional_sets": global_sets,
        "hierarchy_proof_instance": proof,
        "regional_input_sets": regional_inputs,
        "regional_shard_qcs": regional_qcs,
        "regional_shard_results": regional_results,
        "schema_version": "1.0.0",
        "topology": topology,
        "type_name": "HIERARCHY_VALID_CONTRACTS",
    }


def invalid_fixture() -> dict[str, Any]:
    cases = [
        ("overlap-ticket", "TOPOLOGY_TICKET_OVERLAP"),
        ("gap-ticket", "TOPOLOGY_TICKET_GAP"),
        ("duplicate-region", "TOPOLOGY_REGION_DUPLICATE"),
        ("shard-overlap", "TOPOLOGY_SHARD_OVERLAP"),
        ("shard-gap", "TOPOLOGY_SHARD_GAP"),
        ("wrong-domain", "CONTEXT_DOMAIN_MISMATCH"),
        ("wrong-topology", "CONTEXT_TOPOLOGY_MISMATCH"),
        ("wrong-profile", "CONTEXT_PROFILE_MISMATCH"),
        ("wrong-proof", "CONTEXT_PROOF_MISMATCH"),
        ("mixed-view", "QC_MIXED_VIEW"),
        ("wrong-epoch", "QC_EPOCH_MISMATCH"),
        ("duplicate-signer", "QC_DUPLICATE_SIGNER"),
        ("insufficient-quorum", "QC_INSUFFICIENT_QUORUM"),
        ("missing-region", "GLOBAL_REGION_GAP"),
        ("duplicate-regional-result", "GLOBAL_REGION_DUPLICATE"),
        ("numerator-overflow", "ARITHMETIC_OVERFLOW"),
        ("post-freeze-exclusion", "TOPOLOGY_IMMUTABLE"),
        ("regional-partial-publish", "MEDIA_FORBIDDEN"),
        ("global-partial-publish", "MEDIA_FORBIDDEN"),
        ("feature008-apply", "FEATURE008_BOUNDARY"),
    ]
    return {
        "cases": [{"expected_code": code, "id": identifier} for identifier, code in cases],
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "type_name": "HIERARCHY_NEGATIVE_CONTRACTS",
    }


def golden_fixture() -> dict[str, Any]:
    value = contract_fixture()
    return {
        **value,
        "expected": {
            "aggregate_root_id": value["aggregate_root"]["content_id"],
            "global_result_count": 4,
            "regional_result_count": 12,
            "status": "ACCEPT",
        },
        "type_name": "HIERARCHY_CROSS_LANGUAGE_GOLDEN",
    }


def strict_schema(
    name: str, title: str, properties: dict[str, Any], defs: dict[str, Any] | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "$id": f"urn:deltareduce:schema:{name}:1",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": sorted(properties),
        "title": title,
        "type": "object",
    }
    if defs:
        result["$defs"] = defs
    return result


def content_id() -> dict[str, Any]:
    return {"pattern": HASH_PATTERN, "type": "string"}


def decimal() -> dict[str, Any]:
    return {"pattern": DECIMAL_PATTERN, "type": "string"}


def string_list(min_items: int = 1) -> dict[str, Any]:
    return {
        "items": {"minLength": 1, "type": "string"},
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }


def base_properties(type_name: str) -> dict[str, Any]:
    return {
        **{key: content_id() for key in context()},
        "schema_version": {"const": "1.0.0"},
        "type_name": {"const": type_name},
    }


def execution_properties(type_name: str) -> dict[str, Any]:
    return {
        **base_properties(type_name),
        "hierarchy_proof_instance_id": content_id(),
    }


def schemas() -> dict[str, dict[str, Any]]:
    topology = strict_schema(
        "reduce-topology",
        "DeltaReduce immutable regional reduce topology v1",
        {
            **base_properties("REDUCE_TOPOLOGY"),
            "domains": {"items": {"type": "object"}, "minItems": 1, "type": "array"},
            "hard_deadline_tick": {"minimum": 1, "type": "integer"},
            "shards": {"items": {"type": "object"}, "minItems": 1, "type": "array"},
            "soft_deadline_tick": {"minimum": 0, "type": "integer"},
            "validator_epoch": {"minimum": 0, "type": "integer"},
        },
    )
    regional_input = strict_schema(
        "regional-input-set",
        "DeltaReduce exact regional input set v1",
        {
            **execution_properties("REGIONAL_INPUT_SET"),
            "committee_epoch": {"minimum": 0, "type": "integer"},
            "contributions": {"items": {"type": "object"}, "minItems": 1, "type": "array"},
            "domain_id": {"minLength": 1, "type": "string"},
            "region_id": {"minLength": 1, "type": "string"},
            "shard_id": {"minLength": 1, "type": "string"},
            "topology_id": content_id(),
        },
    )
    result_properties = {
        **execution_properties("REGIONAL_SHARD_RESULT"),
        "coefficient_denominator": decimal(),
        "coefficient_numerator_sum": decimal(),
        "domain_id": {"minLength": 1, "type": "string"},
        "eligible_count": {"minimum": 1, "type": "integer"},
        "numerator": {"items": decimal(), "minItems": 1, "type": "array"},
        "region_id": {"minLength": 1, "type": "string"},
        "regional_input_set_id": content_id(),
        "shard_id": {"minLength": 1, "type": "string"},
        "topology_id": content_id(),
    }
    qc_common = {
        **{key: content_id() for key in context()},
        "hierarchy_proof_instance_id": content_id(),
        "body_id": content_id(),
        "committee_epoch": {"minimum": 0, "type": "integer"},
        "domain_id": {"minLength": 1, "type": "string"},
        "quorum_threshold": {"minimum": 1, "type": "integer"},
        "schema_version": {"const": "1.0.0"},
        "shard_id": {"minLength": 1, "type": "string"},
        "signer_ids": string_list(3),
        "topology_id": content_id(),
        "view": {"minimum": 0, "type": "integer"},
    }
    global_set = strict_schema(
        "global-regional-set",
        "DeltaReduce exact global regional set v1",
        {
            **execution_properties("GLOBAL_REGIONAL_SET"),
            "domain_id": {"minLength": 1, "type": "string"},
            "regional_results": {"items": {"type": "object"}, "minItems": 1, "type": "array"},
            "required_regions": string_list(),
            "shard_id": {"minLength": 1, "type": "string"},
            "topology_id": content_id(),
        },
    )
    global_result = strict_schema(
        "global-parameter-result",
        "DeltaReduce checked global parameter result v1",
        {
            **execution_properties("GLOBAL_PARAMETER_RESULT"),
            "coefficient_denominator": decimal(),
            "coefficient_numerator_sum": decimal(),
            "domain_id": {"minLength": 1, "type": "string"},
            "eligible_count": {"minimum": 1, "type": "integer"},
            "global_regional_set_id": content_id(),
            "numerator": {"items": decimal(), "minItems": 1, "type": "array"},
            "shard_id": {"minLength": 1, "type": "string"},
            "topology_id": content_id(),
        },
    )
    proof = strict_schema(
        "hierarchy-proof-instance",
        "DeltaReduce concrete hierarchy theorem-precondition instance v1",
        {
            **base_properties("HIERARCHY_PROOF_INSTANCE"),
            "accumulator_proof_instance_id": content_id(),
            "coefficient_abs_max": decimal(),
            "common_denominator": decimal(),
            "domain_ticket_counts": {"type": "object"},
            "final_abs_bound": decimal(),
            "max_eligible_contributions": {"minimum": 1, "type": "integer"},
            "product_abs_bound": decimal(),
            "q_abs_max": decimal(),
            "result": {"const": "PASS"},
            "selected_accumulator_width_bits": {"enum": [64, 128]},
            "shard_ranges": {"items": {"type": "array"}, "minItems": 1, "type": "array"},
            "theorems": {"items": {"type": "object"}, "minItems": 5, "type": "array"},
            "topology_id": content_id(),
        },
    )
    aggregate = strict_schema(
        "hierarchical-aggregate-root",
        "DeltaReduce complete hierarchical aggregate root v1",
        {
            **execution_properties("HIERARCHICAL_AGGREGATE_ROOT"),
            "coverage": {"items": {"type": "object"}, "minItems": 1, "type": "array"},
            "hierarchy_proof_instance_id": content_id(),
            "required_domain_shards": {"items": {"type": "object"}, "minItems": 1, "type": "array"},
            "topology_id": content_id(),
        },
    )
    return {
        "global-parameter-qc-v1.json": strict_schema(
            "global-parameter-qc",
            "DeltaReduce basic global parameter QC envelope v1",
            {
                **qc_common,
                "phase": {"const": "GLOBAL_PARAMETER_RESULT"},
                "type_name": {"const": "GLOBAL_PARAMETER_QC"},
            },
        ),
        "global-parameter-result-v1.json": global_result,
        "global-regional-set-v1.json": global_set,
        "hierarchical-aggregate-root-v1.json": aggregate,
        "hierarchy-proof-instance-v1.json": proof,
        "reduce-topology-v1.json": topology,
        "regional-input-set-v1.json": regional_input,
        "regional-shard-qc-v1.json": strict_schema(
            "regional-shard-qc",
            "DeltaReduce basic regional shard QC envelope v1",
            {
                **qc_common,
                "phase": {"const": "REGIONAL_RESULT"},
                "region_id": {"minLength": 1, "type": "string"},
                "type_name": {"const": "REGIONAL_SHARD_QC"},
            },
        ),
        "regional-shard-result-v1.json": strict_schema(
            "regional-shard-result",
            "DeltaReduce checked regional shard result v1",
            result_properties,
        ),
    }


FIXTURES: dict[str, Callable[[], dict[str, Any]]] = {
    "cross-language/golden-v1.json": golden_fixture,
    "invalid/hierarchy-negative-v1.json": invalid_fixture,
    "valid/hierarchy-contract-v1.json": contract_fixture,
}
SCHEMA_IDS = {
    name: "SCHEMA-" + name.removesuffix("-v1.json").replace("-", "-").upper() + "-V1"
    for name in schemas()
}
FIXTURE_IDS = {
    "cross-language/golden-v1.json": "HIERARCHY006-CROSS-LANGUAGE-GOLDEN-V1",
    "golden-hashes-v1.json": "HIERARCHY006-GOLDEN-HASHES-V1",
    "invalid/hierarchy-negative-v1.json": "HIERARCHY006-NEGATIVE-V1",
    "valid/hierarchy-contract-v1.json": "HIERARCHY006-VALID-CONTRACT-V1",
}
MEDIA_TYPES = [
    {
        "id": "MEDIA-REDUCE-TOPOLOGY-V1",
        "schema_id": SCHEMA_IDS["reduce-topology-v1.json"],
        "value": "application/vnd.deltareduce.reduce-topology+json;version=1",
    },
    {
        "id": "MEDIA-REGIONAL-INPUT-SET-V1",
        "schema_id": SCHEMA_IDS["regional-input-set-v1.json"],
        "value": INPUT_MEDIA,
    },
    {
        "id": "MEDIA-REGIONAL-SHARD-RESULT-V1",
        "schema_id": SCHEMA_IDS["regional-shard-result-v1.json"],
        "value": REGIONAL_MEDIA,
    },
    {
        "id": "MEDIA-REGIONAL-SHARD-QC-V1",
        "schema_id": SCHEMA_IDS["regional-shard-qc-v1.json"],
        "value": REGIONAL_MEDIA,
    },
    {
        "id": "MEDIA-GLOBAL-REGIONAL-SET-V1",
        "schema_id": SCHEMA_IDS["global-regional-set-v1.json"],
        "value": PARAMETER_MEDIA,
    },
    {
        "id": "MEDIA-GLOBAL-PARAMETER-RESULT-V1",
        "schema_id": SCHEMA_IDS["global-parameter-result-v1.json"],
        "value": PARAMETER_MEDIA,
    },
    {
        "id": "MEDIA-GLOBAL-PARAMETER-QC-V1",
        "schema_id": SCHEMA_IDS["global-parameter-qc-v1.json"],
        "value": PARAMETER_MEDIA,
    },
    {
        "id": "MEDIA-HIERARCHICAL-AGGREGATE-ROOT-V1",
        "schema_id": SCHEMA_IDS["hierarchical-aggregate-root-v1.json"],
        "value": PARAMETER_MEDIA,
    },
    {
        "id": "MEDIA-HIERARCHY-PROOF-INSTANCE-V1",
        "schema_id": SCHEMA_IDS["hierarchy-proof-instance-v1.json"],
        "value": "application/vnd.deltareduce.hierarchy-proof+json;version=1",
    },
]


def pretty_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def file_record(identifier: str, relative: str, path: Path) -> dict[str, str]:
    return {
        "id": identifier,
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def write_registries() -> None:
    schema_records = [
        file_record(identifier, f"schemas/006/{relative}", SCHEMA_ROOT / relative)
        for relative, identifier in sorted(SCHEMA_IDS.items())
    ]
    fixture_records = [
        file_record(identifier, f"fixtures/006/{relative}", FIXTURE_ROOT / relative)
        for relative, identifier in sorted(FIXTURE_IDS.items())
    ]
    registry = {
        "artifacts": schema_records,
        "fixtures": fixture_records,
        "formal_semantics_id": FORMAL_ID,
        "media_types": MEDIA_TYPES,
        "registry_version": "006.1.0",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
    }
    registry_path = SCHEMA_ROOT / "registry-v1.json"
    registry_path.write_bytes(pretty_bytes(registry))
    root_path = ROOT / "delta-protocol" / "registry.json"
    baseline = subprocess.run(
        ["git", "show", "HEAD:delta-protocol/registry.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    root = json.loads(baseline.decode())
    root["schemas"] = sorted(
        [item for item in root["schemas"] if not str(item["path"]).startswith("schemas/006/")]
        + schema_records,
        key=lambda item: str(item["path"]),
    )
    root["fixtures"] = sorted(
        [item for item in root["fixtures"] if not str(item["path"]).startswith("fixtures/006/")]
        + fixture_records,
        key=lambda item: str(item["path"]),
    )
    root["extensions"] = [
        item for item in root["extensions"] if item["id"] != "REGISTRY-HIERARCHY-006-V1"
    ] + [file_record("REGISTRY-HIERARCHY-006-V1", "schemas/006/registry-v1.json", registry_path)]
    new_media_ids = {entry["id"] for entry in MEDIA_TYPES}
    root["media_types"] = [
        item for item in root["media_types"] if item["id"] not in new_media_ids
    ] + MEDIA_TYPES
    root_path.write_bytes(pretty_bytes(root))


def write_all() -> None:
    for relative, value in sorted(schemas().items()):
        (SCHEMA_ROOT / relative).write_bytes(pretty_bytes(value))
    for relative, factory in sorted(FIXTURES.items()):
        destination = FIXTURE_ROOT / relative
        destination.write_bytes(canonical_json_bytes(factory()) + b"\n")
    hashes = {
        "artifacts": [
            {
                "path": relative,
                "sha256": hashlib.sha256((FIXTURE_ROOT / relative).read_bytes()).hexdigest(),
            }
            for relative in sorted(FIXTURES)
        ],
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "type_name": "HIERARCHY_GOLDEN_HASH_MANIFEST",
    }
    (FIXTURE_ROOT / "golden-hashes-v1.json").write_bytes(pretty_bytes(hashes))
    write_registries()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-all", action="store_true")
    parser.add_argument("--print", choices=sorted(FIXTURES))
    arguments = parser.parse_args()
    if arguments.write_all:
        write_all()
        return 0
    if arguments.print is not None:
        print(canonical_json_bytes(FIXTURES[arguments.print]()).decode())
        return 0
    parser.error("one of --write-all or --print is required")


if __name__ == "__main__":
    raise SystemExit(main())
