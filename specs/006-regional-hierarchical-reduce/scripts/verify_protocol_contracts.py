"""Verify feature-006 hierarchy contracts, exact arithmetic and registry closure."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from itertools import pairwise
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "006-regional-hierarchical-reduce"
SCRIPT_DIR = FEATURE / "scripts"
SCHEMA_ROOT = ROOT / "delta-protocol" / "schemas" / "006"
FIXTURE_ROOT = ROOT / "delta-protocol" / "fixtures" / "006"
EVIDENCE = FEATURE / "evidence" / "protocol-contracts.json"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import hierarchy_contracts as contracts  # noqa: E402


class ContractError(RuntimeError):
    """Stable fail-closed hierarchy contract error."""


def reject(code: str, detail: str = "") -> NoReturn:
    raise ContractError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "JSON_ROOT_INVALID", str(path))
    return value


def validate_identified(item: dict[str, Any], domain: str, code: str) -> None:
    value = item.get("value")
    require(isinstance(value, dict), code, "VALUE_INVALID")
    encoded = contracts.canonical_json_bytes(value)
    require(item.get("bytes_hex") == encoded.hex(), code, "BYTES_DRIFT")
    require(item.get("content_id") == contracts.domain_hash(domain, encoded), code, "ID_DRIFT")


def validate_generated_bytes() -> None:
    for relative, factory in sorted(contracts.FIXTURES.items()):
        expected = contracts.canonical_json_bytes(factory()) + b"\n"
        require((FIXTURE_ROOT / relative).read_bytes() == expected, "FIXTURE_DRIFT", relative)
    for relative, schema in sorted(contracts.schemas().items()):
        require(
            (SCHEMA_ROOT / relative).read_bytes() == contracts.pretty_bytes(schema),
            "SCHEMA_DRIFT",
            relative,
        )


def validate_schemas() -> None:
    for path in sorted(SCHEMA_ROOT.glob("*-v1.json")):
        if path.name == "registry-v1.json":
            continue
        schema = read_json(path)
        require(
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            "SCHEMA_DIALECT_INVALID",
            path.name,
        )
        require(schema.get("type") == "object", "SCHEMA_ROOT_TYPE_INVALID", path.name)
        require(schema.get("additionalProperties") is False, "SCHEMA_OPEN", path.name)
        properties = schema.get("properties")
        require(isinstance(properties, dict), "SCHEMA_PROPERTIES_INVALID", path.name)
        require(schema.get("required") == sorted(properties), "SCHEMA_REQUIRED_INVALID", path.name)


def exact_context(value: dict[str, Any], topology_id: str, proof_id: str | None) -> None:
    for key, expected in contracts.context().items():
        require(value.get(key) == expected, "CONTEXT_DRIFT", key)
    require(value.get("topology_id") == topology_id, "CONTEXT_TOPOLOGY_MISMATCH")
    if proof_id is not None:
        require(
            value.get("hierarchy_proof_instance_id") == proof_id,
            "CONTEXT_HIERARCHY_PROOF_MISMATCH",
        )


def validate_topology(topology: dict[str, Any]) -> dict[str, Any]:
    validate_identified(topology, "deltareduce.006.reduce-topology.v1", "TOPOLOGY_IDENTITY_INVALID")
    value = topology["value"]
    require(value["soft_deadline_tick"] < value["hard_deadline_tick"], "DEADLINE_ORDER_INVALID")
    domains = value["domains"]
    domain_ids = [item["domain_id"] for item in domains]
    require(len(domain_ids) == len(set(domain_ids)), "TOPOLOGY_DOMAIN_DUPLICATE")
    all_ticket_keys: set[tuple[str, str]] = set()
    for domain in domains:
        tickets = domain["tickets"]
        require(len(tickets) == len(set(tickets)), "TOPOLOGY_TICKET_DUPLICATE", domain["domain_id"])
        region_ids = [item["region_id"] for item in domain["regions"]]
        require(len(region_ids) == len(set(region_ids)) == 3, "TOPOLOGY_REGION_INVALID")
        routed = [ticket for region in domain["regions"] for ticket in region["tickets"]]
        require(sorted(routed) == sorted(tickets), "TOPOLOGY_TICKET_COVERAGE_INVALID")
        require(len(routed) == len(set(routed)), "TOPOLOGY_TICKET_OVERLAP")
        for region in domain["regions"]:
            fault_bound = int(region["fault_bound"])
            validators = region["validator_set"]
            require(len(validators) == 3 * fault_bound + 1, "REGIONAL_COMMITTEE_SIZE_INVALID")
            require(len(validators) == len(set(validators)), "REGIONAL_VALIDATOR_DUPLICATE")
        fault_bound = int(domain["global_fault_bound"])
        validators = domain["global_validator_set"]
        require(len(validators) == 3 * fault_bound + 1, "GLOBAL_COMMITTEE_SIZE_INVALID")
        require(len(validators) == len(set(validators)), "GLOBAL_VALIDATOR_DUPLICATE")
        all_ticket_keys |= {(domain["domain_id"], ticket) for ticket in tickets}

    shards = sorted(value["shards"], key=lambda item: int(item["start_element"]))
    require(shards[0]["start_element"] == 0, "TOPOLOGY_SHARD_START_INVALID")
    for previous, current in pairwise(shards):
        require(
            previous["end_element"] == current["start_element"], "TOPOLOGY_SHARD_GAP_OR_OVERLAP"
        )
    shard_ids = [item["shard_id"] for item in shards]
    require(len(shard_ids) == len(set(shard_ids)), "TOPOLOGY_SHARD_DUPLICATE")
    return {
        "domain_count": len(domains),
        "region_count_per_domain": 3,
        "shard_count": len(shards),
        "ticket_count": len(all_ticket_keys),
    }


def validate_proof(proof: dict[str, Any], topology_id: str) -> None:
    validate_identified(
        proof, "deltareduce.006.hierarchy-proof-instance.v1", "HIERARCHY_PROOF_IDENTITY_INVALID"
    )
    value = proof["value"]
    exact_context(value, topology_id, None)
    require(value["result"] == "PASS", "HIERARCHY_PROOF_NOT_PASS")
    expected = {
        "PO-A1": {"product-bound"},
        "PO-A2": {"flat-accumulator-bound"},
        "PO-A3": {
            "canonical-reduced-input",
            "input-denominator-divides-common",
            "numerator-accumulator-bound",
            "positive-common-denominator",
            "positive-input-denominator",
            "round-at-or-above-half",
            "round-below-half",
            "round-half-tie-toward-positive",
            "rounding-deterministic",
        },
        "PO-H1": {"exact-partition"},
        "PO-H2": {"hierarchy-equals-flat"},
    }
    actual = {item["obligation_id"]: set(item["conjuncts"]) for item in value["theorems"]}
    require(actual == expected, "HIERARCHY_THEOREM_BINDINGS_INVALID")
    q_bound = int(value["q_abs_max"])
    coefficient_bound = int(value["coefficient_abs_max"])
    product_bound = int(value["product_abs_bound"])
    final_bound = int(value["final_abs_bound"])
    max_count = int(value["max_eligible_contributions"])
    require(product_bound == q_bound * coefficient_bound, "PRODUCT_BOUND_INVALID")
    require(final_bound == product_bound * max_count, "FINAL_BOUND_INVALID")
    require(final_bound < 2 ** (int(value["selected_accumulator_width_bits"]) - 1), "WIDTH_UNSAFE")
    require(int(value["common_denominator"]) > 0, "DENOMINATOR_INVALID")


def maps_by_value(
    items: list[dict[str, Any]], keys: tuple[str, ...]
) -> dict[tuple[Any, ...], dict[str, Any]]:
    result: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in items:
        value = item["value"]
        key = tuple(value[name] for name in keys)
        require(key not in result, "DUPLICATE_CONTRACT_KEY", repr(key))
        result[key] = item
    return result


def validate_qc(
    qc: dict[str, Any], domain: str, validators: list[str], epoch: int, body_id: str
) -> None:
    validate_identified(qc, domain, "QC_IDENTITY_INVALID")
    value = qc["value"]
    signers = value["signer_ids"]
    threshold = int(value["quorum_threshold"])
    require(len(signers) == len(set(signers)), "QC_DUPLICATE_SIGNER")
    require(set(signers) <= set(validators), "QC_SIGNER_OUTSIDE_COMMITTEE")
    require(len(signers) >= threshold == 3, "QC_INSUFFICIENT_QUORUM")
    require(value["committee_epoch"] == epoch, "QC_EPOCH_MISMATCH")
    require(value["body_id"] == body_id, "QC_BODY_MISMATCH")
    require(value["view"] == 0, "QC_VIEW_INVALID")


def validate_hierarchy(golden: dict[str, Any]) -> dict[str, Any]:
    topology = golden["topology"]
    topology_id = topology["content_id"]
    topology_summary = validate_topology(topology)
    proof = golden["hierarchy_proof_instance"]
    proof_id = proof["content_id"]
    validate_proof(proof, topology_id)
    topology_value = topology["value"]
    domains = {item["domain_id"]: item for item in topology_value["domains"]}
    shard_ids = [item["shard_id"] for item in topology_value["shards"]]

    inputs = maps_by_value(golden["regional_input_sets"], ("domain_id", "region_id", "shard_id"))
    results = maps_by_value(
        golden["regional_shard_results"], ("domain_id", "region_id", "shard_id")
    )
    regional_qcs = maps_by_value(
        golden["regional_shard_qcs"], ("domain_id", "region_id", "shard_id")
    )
    expected_regional_keys = {
        (domain_id, region["region_id"], shard_id)
        for domain_id, domain in domains.items()
        for region in domain["regions"]
        for shard_id in shard_ids
    }
    require(set(inputs) == expected_regional_keys, "REGIONAL_INPUT_COVERAGE_INVALID")
    require(set(results) == expected_regional_keys, "REGIONAL_RESULT_COVERAGE_INVALID")
    require(set(regional_qcs) == expected_regional_keys, "REGIONAL_QC_COVERAGE_INVALID")

    flat: dict[tuple[str, str], list[int]] = {}
    for key in sorted(expected_regional_keys):
        domain_id, region_id, shard_id = key
        domain = domains[domain_id]
        region = next(item for item in domain["regions"] if item["region_id"] == region_id)
        shard_ordinal = shard_ids.index(shard_id)
        input_item = inputs[key]
        validate_identified(
            input_item, "deltareduce.006.regional-input-set.v1", "REGIONAL_INPUT_IDENTITY_INVALID"
        )
        exact_context(input_item["value"], topology_id, proof_id)
        contributions = input_item["value"]["contributions"]
        require(
            sorted(item["ticket_id"] for item in contributions) == sorted(region["tickets"]),
            "REGIONAL_TICKET_SET_INVALID",
        )
        expected_vector = [0, 0, 0, 0]
        expected_coefficient_sum = 0
        for contribution in contributions:
            ticket_ordinal = domain["tickets"].index(contribution["ticket_id"]) + 1
            require(contribution["coefficient_denominator"] == "1", "FRACTION_NOT_CANONICAL")
            require(
                math.gcd(abs(int(contribution["coefficient_numerator"])), 1) == 1,
                "FRACTION_NOT_REDUCED",
            )
            require(
                contribution["q_values"] == contracts.q_values(ticket_ordinal, shard_ordinal),
                "Q_VALUES_DRIFT",
            )
            coefficient = int(contribution["coefficient_numerator"])
            expected_coefficient_sum += coefficient
            for index, q_value in enumerate(contribution["q_values"]):
                expected_vector[index] += coefficient * int(q_value)
        result = results[key]
        validate_identified(
            result, "deltareduce.006.regional-shard-result.v1", "REGIONAL_RESULT_IDENTITY_INVALID"
        )
        exact_context(result["value"], topology_id, proof_id)
        require(
            result["value"]["regional_input_set_id"] == input_item["content_id"],
            "INPUT_PARENT_INVALID",
        )
        require(
            result["value"]["numerator"] == [str(item) for item in expected_vector],
            "REGIONAL_SUM_INVALID",
        )
        require(result["value"]["coefficient_denominator"] == "1", "REGIONAL_DENOMINATOR_INVALID")
        require(
            int(result["value"]["coefficient_numerator_sum"]) == expected_coefficient_sum,
            "REGIONAL_COEFFICIENT_SUM_INVALID",
        )
        require(result["value"]["eligible_count"] == len(contributions), "REGIONAL_COUNT_INVALID")
        qc = regional_qcs[key]
        exact_context(qc["value"], topology_id, proof_id)
        validate_qc(
            qc,
            "deltareduce.006.regional-shard-qc.v1",
            region["validator_set"],
            topology_value["validator_epoch"],
            result["content_id"],
        )
        current = flat.setdefault((domain_id, shard_id), [0, 0, 0, 0])
        for index, value in enumerate(expected_vector):
            current[index] += value

    global_sets = maps_by_value(golden["global_regional_sets"], ("domain_id", "shard_id"))
    global_results = maps_by_value(golden["global_parameter_results"], ("domain_id", "shard_id"))
    global_qcs = maps_by_value(golden["global_parameter_qcs"], ("domain_id", "shard_id"))
    required = {(domain_id, shard_id) for domain_id in domains for shard_id in shard_ids}
    require(
        set(global_sets) == set(global_results) == set(global_qcs) == required,
        "GLOBAL_COVERAGE_INVALID",
    )
    for key in sorted(required):
        domain_id, shard_id = key
        domain = domains[domain_id]
        regional = [
            results[(domain_id, region["region_id"], shard_id)] for region in domain["regions"]
        ]
        regional_set = global_sets[key]
        validate_identified(
            regional_set, "deltareduce.006.global-regional-set.v1", "GLOBAL_SET_IDENTITY_INVALID"
        )
        exact_context(regional_set["value"], topology_id, proof_id)
        require(
            regional_set["value"]["required_regions"]
            == [item["region_id"] for item in domain["regions"]],
            "GLOBAL_REQUIRED_REGIONS_INVALID",
        )
        expected_pairs = [
            {"region_id": item["value"]["region_id"], "regional_result_id": item["content_id"]}
            for item in regional
        ]
        require(
            regional_set["value"]["regional_results"] == expected_pairs, "GLOBAL_REGION_SET_INVALID"
        )
        result = global_results[key]
        validate_identified(
            result, "deltareduce.006.global-parameter-result.v1", "GLOBAL_RESULT_IDENTITY_INVALID"
        )
        exact_context(result["value"], topology_id, proof_id)
        require(
            result["value"]["global_regional_set_id"] == regional_set["content_id"],
            "GLOBAL_SET_PARENT_INVALID",
        )
        require(
            result["value"]["numerator"] == [str(item) for item in flat[key]],
            "HIERARCHY_FLAT_MISMATCH",
        )
        require(result["value"]["coefficient_denominator"] == "1", "GLOBAL_DENOMINATOR_INVALID")
        require(result["value"]["eligible_count"] == len(domain["tickets"]), "GLOBAL_COUNT_INVALID")
        qc = global_qcs[key]
        exact_context(qc["value"], topology_id, proof_id)
        validate_qc(
            qc,
            "deltareduce.006.global-parameter-qc.v1",
            domain["global_validator_set"],
            topology_value["validator_epoch"],
            result["content_id"],
        )

    aggregate = golden["aggregate_root"]
    validate_identified(
        aggregate,
        "deltareduce.006.hierarchical-aggregate-root.v1",
        "AGGREGATE_ROOT_IDENTITY_INVALID",
    )
    exact_context(aggregate["value"], topology_id, proof_id)
    matrix = [
        {"domain_id": domain_id, "shard_id": shard_id}
        for domain_id in domains
        for shard_id in shard_ids
    ]
    require(
        aggregate["value"]["required_domain_shards"] == matrix, "AGGREGATE_REQUIRED_MATRIX_INVALID"
    )
    coverage_keys = [
        (item["domain_id"], item["shard_id"]) for item in aggregate["value"]["coverage"]
    ]
    require(coverage_keys == sorted(required), "AGGREGATE_COVERAGE_INVALID")
    require(len(coverage_keys) == len(set(coverage_keys)), "AGGREGATE_COVERAGE_DUPLICATE")
    for entry in aggregate["value"]["coverage"]:
        key = (entry["domain_id"], entry["shard_id"])
        require(
            entry["global_parameter_result_id"] == global_results[key]["content_id"],
            "AGGREGATE_RESULT_ID_INVALID",
        )
        require(
            entry["global_parameter_qc_id"] == global_qcs[key]["content_id"],
            "AGGREGATE_QC_ID_INVALID",
        )
    return topology_summary | {
        "aggregate_root_id": aggregate["content_id"],
        "global_result_count": len(global_results),
        "hierarchy_proof_instance_id": proof_id,
        "regional_result_count": len(results),
    }


def validate_distribution_boundary() -> dict[str, Any]:
    phase005 = read_json(
        ROOT / "delta-protocol" / "fixtures" / "005" / "cross-language" / "golden-v1.json"
    )
    forbidden = set(phase005["policy_registry"]["value"]["forbidden_media_types"])
    partial_schema_ids = {
        contracts.SCHEMA_IDS[name]
        for name in (
            "global-parameter-qc-v1.json",
            "global-parameter-result-v1.json",
            "global-regional-set-v1.json",
            "hierarchical-aggregate-root-v1.json",
            "regional-input-set-v1.json",
            "regional-shard-qc-v1.json",
            "regional-shard-result-v1.json",
        )
    }
    media = [item for item in contracts.MEDIA_TYPES if item["schema_id"] in partial_schema_ids]
    require(len(media) == len(partial_schema_ids), "PARTIAL_MEDIA_REGISTRY_INCOMPLETE")
    require(all(item["value"] in forbidden for item in media), "PARTIAL_MEDIA_NOT_DENIED")
    return {
        "denied_media_types": sorted({item["value"] for item in media}),
        "parent_policy_registry_id": phase005["policy_registry"]["content_id"],
        "status": "PASS",
    }


def validate_feature008_boundary(golden: dict[str, Any]) -> None:
    encoded = contracts.canonical_json_bytes(golden).decode("utf-8")
    for forbidden in (
        "APPLY_QC",
        "AGGREGATE_ROOT_QC",
        "ELIGIBILITY_CERTIFICATE",
        "INPUT_SET_CERTIFICATE",
        "PARAMETER_SHARD_QC",
        "current_checkpoint",
    ):
        require(forbidden not in encoded, "FEATURE008_BOUNDARY_VIOLATION", forbidden)


def verify_registry() -> dict[str, int]:
    registry = read_json(SCHEMA_ROOT / "registry-v1.json")
    root = read_json(ROOT / "delta-protocol" / "registry.json")
    expected_schemas = set(contracts.SCHEMA_IDS.values())
    expected_fixtures = set(contracts.FIXTURE_IDS.values())
    require(
        {item["id"] for item in registry["artifacts"]} == expected_schemas,
        "SCHEMA_REGISTRY_INVALID",
    )
    require(
        {item["id"] for item in registry["fixtures"]} == expected_fixtures,
        "FIXTURE_REGISTRY_INVALID",
    )
    for item in [*registry["artifacts"], *registry["fixtures"]]:
        path = ROOT / "delta-protocol" / item["path"]
        require(path.is_file(), "REGISTRY_PATH_MISSING", item["path"])
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"],
            "REGISTRY_HASH_DRIFT",
            item["path"],
        )
    require(
        expected_schemas <= {item["id"] for item in root["schemas"]},
        "ROOT_SCHEMA_REGISTRY_INCOMPLETE",
    )
    require(
        expected_fixtures <= {item["id"] for item in root["fixtures"]},
        "ROOT_FIXTURE_REGISTRY_INCOMPLETE",
    )
    extension = [item for item in root["extensions"] if item["id"] == "REGISTRY-HIERARCHY-006-V1"]
    require(len(extension) == 1, "ROOT_EXTENSION_INVALID")
    require(
        extension[0]["sha256"]
        == hashlib.sha256((SCHEMA_ROOT / "registry-v1.json").read_bytes()).hexdigest(),
        "ROOT_EXTENSION_HASH_DRIFT",
    )
    return {"fixture_count": len(expected_fixtures), "schema_count": len(expected_schemas)}


def verify() -> dict[str, Any]:
    validate_generated_bytes()
    validate_schemas()
    golden = read_json(FIXTURE_ROOT / "cross-language" / "golden-v1.json")
    validate_feature008_boundary(golden)
    summary = validate_hierarchy(golden)
    negative = read_json(FIXTURE_ROOT / "invalid" / "hierarchy-negative-v1.json")
    codes = {item["expected_code"] for item in negative["cases"]}
    required_codes = {
        "ARITHMETIC_OVERFLOW",
        "CONTEXT_PROOF_MISMATCH",
        "CONTEXT_TOPOLOGY_MISMATCH",
        "FEATURE008_BOUNDARY",
        "GLOBAL_REGION_DUPLICATE",
        "GLOBAL_REGION_GAP",
        "MEDIA_FORBIDDEN",
        "QC_DUPLICATE_SIGNER",
        "QC_INSUFFICIENT_QUORUM",
        "QC_MIXED_VIEW",
        "TOPOLOGY_IMMUTABLE",
        "TOPOLOGY_SHARD_GAP",
        "TOPOLOGY_SHARD_OVERLAP",
        "TOPOLOGY_TICKET_GAP",
        "TOPOLOGY_TICKET_OVERLAP",
    }
    require(required_codes <= codes, "NEGATIVE_CODE_SET_INCOMPLETE")
    return {
        "checks": [
            "CANONICAL_SCHEMAS_FIXTURES_REPRODUCIBLE",
            "UNEQUAL_THREE_REGION_TWO_DOMAIN_TWO_SHARD_TOPOLOGY_EXACT",
            "PO_H1_H2_A1_A2_A3_PRECONDITIONS_CONTENT_ADDRESSED",
            "REGIONAL_AND_GLOBAL_INTEGER_RESULTS_EQUAL_FLAT_ORACLE",
            "BASIC_QC_QUORUM_CONTEXTS_EXACT",
            "COMPLETE_DOMAIN_SHARD_MATRIX_EXACT",
            "ALL_PARTIAL_MEDIA_TYPES_DENIED_BY_FEATURE005_POLICY",
            "FEATURE008_CERTIFICATE_AND_APPLY_BOUNDARY_PRESERVED",
            "NEGATIVE_CONTRACT_MATRIX_COMPLETE",
            "PROTOCOL_REGISTRY_CLOSED",
        ],
        "distribution": validate_distribution_boundary(),
        "errors": [],
        "formal_semantics_id": contracts.FORMAL_ID,
        "identities": {
            "aggregate_root_id": summary["aggregate_root_id"],
            "hierarchy_proof_instance_id": summary["hierarchy_proof_instance_id"],
            "topology_id": golden["topology"]["content_id"],
        },
        "registry": verify_registry(),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "summary": summary,
        "task_ids": ["T005", "T006", "T007", "T008", "T009", "T010", "HR006-001", "HR006-005"],
    }


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def tracked_artifact(path: str, revision: str) -> dict[str, str]:
    return {
        "path": path,
        "sha256": hashlib.sha256(git_bytes("show", f"{revision}:{path}")).hexdigest(),
    }


def source_paths() -> list[str]:
    return [
        "delta-protocol/registry.json",
        *[
            f"delta-protocol/schemas/006/{name}"
            for name in sorted([*contracts.SCHEMA_IDS, "registry-v1.json"])
        ],
        *[f"delta-protocol/fixtures/006/{name}" for name in sorted(contracts.FIXTURE_IDS)],
        "specs/006-regional-hierarchical-reduce/evidence/preflight.json",
        "specs/006-regional-hierarchical-reduce/scripts/hierarchy_contracts.py",
        "specs/006-regional-hierarchical-reduce/scripts/verify_protocol_contracts.py",
        "specs/006-regional-hierarchical-reduce/tests/test_verify_protocol_contracts.py",
    ]


def evidence_document(source_commit: str) -> dict[str, Any]:
    result = verify()
    result["source"] = {
        "artifacts": [tracked_artifact(path, source_commit) for path in source_paths()],
        "commit": source_commit,
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--write-evidence", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write_evidence:
            require(
                not git_text("status", "--porcelain", "--untracked-files=all"),
                "SOURCE_TREE_NOT_CLEAN",
            )
            source_commit = git_text("rev-parse", "HEAD")
            document = evidence_document(source_commit)
            EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
            EVIDENCE.write_bytes(contracts.canonical_json_bytes(document) + b"\n")
        elif arguments.check_only:
            require(EVIDENCE.is_file(), "CONTRACT_EVIDENCE_MISSING")
            existing = read_json(EVIDENCE)
            source_commit = existing.get("source", {}).get("commit")
            require(
                isinstance(source_commit, str)
                and re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
                "CONTRACT_SOURCE_INVALID",
            )
            document = evidence_document(source_commit)
            require(
                EVIDENCE.read_bytes() == contracts.canonical_json_bytes(document) + b"\n",
                "CONTRACT_EVIDENCE_STALE",
            )
        else:
            document = verify()
    except (ContractError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(
            contracts.canonical_json_bytes(
                {
                    "error_code": str(exc),
                    "formal_semantics_id": contracts.FORMAL_ID,
                    "schema_version": "1.0.0",
                    "status": "FAIL",
                }
            ).decode()
        )
        return 2
    print(contracts.canonical_json_bytes(document).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
