from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from campaign02_chain_fixtures import certified_plan, certified_result, content_id, contributions
from deltatorrent.benchmark.feature008_admission import canonical_native_chain_bundle
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = (
    ROOT
    / "delta-protocol"
    / "fixtures"
    / "010"
    / "campaign-02"
    / "native-chain-conformance-v1.json"
)

DOMAINS = {
    "aggregate_root_qc": "deltareduce.008.aggregate-root-qc.v1",
    "aggregation_plan_certificate": "deltareduce.008.aggregation-plan-certificate.v1",
    "apply_arithmetic_profile": "deltareduce.008.apply-arithmetic-profile.v1",
    "apply_candidate": "deltareduce.008.apply-candidate.v1",
    "apply_qc": "deltareduce.008.apply-qc.v1",
    "current_pointer_command": "deltareduce.008.current-pointer-command.v1",
    "eligibility_certificate": "deltareduce.008.eligibility-certificate.v1",
    "input_set_certificate": "deltareduce.008.input-set-certificate.v1",
    "norm_evidence": "deltareduce.008.norm-evidence.v1",
    "parameter_shard_qc": "deltareduce.008.parameter-shard-qc.v1",
    "seed_transcript": "deltareduce.008.seed-transcript.v1",
}


def _artifact_id(name: str, value: dict[str, Any]) -> str:
    return sha256_content_id(DOMAINS[name].encode("ascii") + b"\0" + canonical_json_bytes(value))


def _policy_id(value: dict[str, Any]) -> str:
    return sha256_content_id(
        b"deltareduce.010.certified-round-policy.v1\0" + canonical_json_bytes(value)
    )


def _merkle_root(leaves: list[dict[str, Any]]) -> str:
    level = [
        sha256_content_id(b"deltareduce.008.aggregate-leaf.v1\0" + canonical_json_bytes(leaf))
        for leaf in leaves
    ]
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                next_level.append(level[index])
            else:
                pair = bytes.fromhex(level[index][7:]) + bytes.fromhex(level[index + 1][7:])
                next_level.append(sha256_content_id(b"deltareduce.008.aggregate-node.v1\0" + pair))
        level = next_level
    return level[0]


def _rebind(document: dict[str, Any], *, preserve_wrong_seed_parent: bool = False) -> None:
    isc_id = _artifact_id("input_set_certificate", document["input_set_certificate"])
    seed = document["seed_transcript"]
    if not preserve_wrong_seed_parent:
        seed["input_set_certificate_id"] = isc_id
    norms = document["norm_evidence"]
    norms["input_set_certificate_id"] = isc_id
    seed_id = _artifact_id("seed_transcript", seed)
    norms_id = _artifact_id("norm_evidence", norms)

    eligibility = document["eligibility_certificate"]
    eligibility["input_set_certificate_id"] = isc_id
    eligibility["norm_evidence_id"] = norms_id
    eligibility_id = _artifact_id("eligibility_certificate", eligibility)

    plan = document["aggregation_plan_certificate"]
    plan["input_set_certificate_id"] = isc_id
    plan["eligibility_certificate_id"] = eligibility_id
    plan["seed_transcript_id"] = seed_id
    plan_id = _artifact_id("aggregation_plan_certificate", plan)

    shards = document["parameter_shard_qcs"]
    for shard in shards:
        shard["input_set_certificate_id"] = isc_id
        shard["eligibility_certificate_id"] = eligibility_id
        shard["aggregation_plan_certificate_id"] = plan_id

    root = document["aggregate_root_qc"]
    root["input_set_certificate_id"] = isc_id
    root["eligibility_certificate_id"] = eligibility_id
    root["aggregation_plan_certificate_id"] = plan_id
    for leaf, shard in zip(root["leaves"], shards, strict=True):
        leaf["parameter_shard_qc_id"] = _artifact_id("parameter_shard_qc", shard)
    root["merkle_root"] = _merkle_root(root["leaves"])
    root_id = _artifact_id("aggregate_root_qc", root)

    candidate = document["apply_candidate"]
    candidate["aggregate_root_qc_id"] = root_id
    candidate_id = _artifact_id("apply_candidate", candidate)
    apply_qc = document["apply_qc"]
    apply_qc["aggregate_root_qc_id"] = root_id
    apply_qc["apply_candidate_id"] = candidate_id
    apply_id = _artifact_id("apply_qc", apply_qc)
    document["current_pointer_command"]["apply_qc_id"] = apply_id


def _reverse_weights(value: dict[str, Any]) -> None:
    value["aggregation_plan_certificate"]["weights"].reverse()


def _reverse_seed_shares(value: dict[str, Any]) -> None:
    value["seed_transcript"]["share_ids"].reverse()


def _reverse_norm_entries(value: dict[str, Any]) -> None:
    value["norm_evidence"]["entries"].reverse()


def _unreduced_rational(value: dict[str, Any]) -> None:
    value["aggregation_plan_certificate"]["weights"][0]["alpha"] = {
        "denominator": 4,
        "numerator": "2",
    }


def _zero_denominator(value: dict[str, Any]) -> None:
    value["aggregation_plan_certificate"]["weights"][0]["alpha"]["denominator"] = 0


def _noncanonical_squared_norm(value: dict[str, Any]) -> None:
    value["norm_evidence"]["entries"][0]["squared_norm"] = "01"


def _unordered_signers(value: dict[str, Any]) -> None:
    value["input_set_certificate"]["signer_ids"].reverse()


def _invalid_nested_content_id(value: dict[str, Any]) -> None:
    value["parameter_shard_qcs"][0]["input_leaf_ids"][0] = "invalid-content-id"


def _wrong_required_key_order(value: dict[str, Any]) -> None:
    value["aggregate_root_qc"]["required_keys"].reverse()


def _wrong_seed_parent(value: dict[str, Any]) -> None:
    value["seed_transcript"]["input_set_certificate_id"] = content_id("wrong-seed-parent")


def _incomplete_shard_coverage(value: dict[str, Any]) -> None:
    value["parameter_shard_qcs"] = value["parameter_shard_qcs"][:1]
    value["aggregate_root_qc"]["leaves"] = value["aggregate_root_qc"]["leaves"][:1]
    value["aggregate_root_qc"]["required_keys"] = value["aggregate_root_qc"]["required_keys"][:1]


Mutation = Callable[[dict[str, Any]], None]


def _case(
    base: dict[str, Any],
    name: str,
    expected: str,
    mutation: Mutation | None = None,
) -> dict[str, Any]:
    document = copy.deepcopy(base)
    if mutation is not None:
        mutation(document)
    _rebind(document, preserve_wrong_seed_parent=name == "wrong-seed-parent")
    return {
        "bundle_bytes_hex": canonical_json_bytes(document).hex(),
        "c_abi": expected,
        "checkpoint_wal_sha256": document["checkpoint_wal_sha256"],
        "effect_set_id": document["effect_set_id"],
        "execution_plan_id": document["execution_plan_id"],
        "expected": expected,
        "final_checkpoint_id": document["final_checkpoint_id"],
        "name": name,
        "native_chain_verifier": expected,
        "parent_checkpoint_id": document["parent_checkpoint_id"],
        "policy_id": _policy_id(document["policy"]),
        "python_admission": expected,
        "runtime_state_id": document["runtime_state_id"],
        "runtime_wal_sha256": document["runtime_wal_sha256"],
    }


def main() -> None:
    plan, _ = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured)
    base = json.loads(canonical_native_chain_bundle(plan, measured, result))
    cases = [
        _case(base, "valid-complete-chain", "ACCEPT"),
        _case(base, "reversed-apc-weights", "REJECT", _reverse_weights),
        _case(base, "unordered-seed-shares", "REJECT", _reverse_seed_shares),
        _case(base, "unordered-norm-entries", "REJECT", _reverse_norm_entries),
        _case(base, "unreduced-rational", "REJECT", _unreduced_rational),
        _case(base, "zero-denominator", "REJECT", _zero_denominator),
        _case(base, "noncanonical-squared-norm", "REJECT", _noncanonical_squared_norm),
        _case(base, "unordered-signers", "REJECT", _unordered_signers),
        _case(base, "invalid-nested-content-id", "REJECT", _invalid_nested_content_id),
        _case(base, "wrong-required-key-order", "REJECT", _wrong_required_key_order),
        _case(base, "wrong-seed-parent", "REJECT", _wrong_seed_parent),
        _case(base, "incomplete-shard-coverage", "REJECT", _incomplete_shard_coverage),
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(
        canonical_json_bytes(
            {
                "cases": cases,
                "corpus_version": "1.0.0",
                "type_name": "CAMPAIGN02_NATIVE_CHAIN_CONFORMANCE_CORPUS",
            }
        )
        + b"\n"
    )


if __name__ == "__main__":
    main()
