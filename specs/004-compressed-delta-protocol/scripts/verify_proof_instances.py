"""Verify concrete feature-004 proof instances and their exact Lean bindings."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
SCRIPT_DIR: Final = Path(__file__).resolve().parent
WORKER_SRC: Final = ROOT / "delta-worker-python" / "src"
for import_root in (SCRIPT_DIR, WORKER_SRC):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from deltatorrent.reference.fixedpoint_encoder import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    canonical_json_bytes,
    content_id,
)
from fixedpoint_contracts import LEAN_SOURCE_ID, PARAMETER_SCHEMA_ID, THEOREMS  # noqa: E402
from verify_protocol_contracts import verify_all as verify_protocol_contracts  # noqa: E402

FEATURE_DIR: Final = ROOT / "specs" / "004-compressed-delta-protocol"
VALID_PATH: Final = (
    ROOT / "delta-protocol" / "fixtures" / "004" / "valid" / "fixedpoint-contract-v1.json"
)
NEGATIVE_PATH: Final = (
    ROOT / "delta-protocol" / "fixtures" / "004" / "invalid" / "fixedpoint-negative-v1.json"
)
LEAN_REPORT_PATH: Final = ROOT / "formal" / "reports" / "lean-proof-report.json"
LEAN_SOURCE_PATH: Final = ROOT / "formal" / "proofs" / "DeltaReduce" / "FixedPoint.lean"
EXPECTED_TOOLCHAIN: Final = "leanprover/lean4:v4.32.1"
EXPECTED_DEPENDENCY_LOCK: Final = "b5a0e5a816cce0d971af3ba3230a39e09108332f407e3c7d97588dfa1096a1ab"
EXPECTED_LAKE_MANIFEST: Final = "fcbd8166f017a16726f087a2b80521b707e7cb46808aaf4e8881b7400c8a9d9e"
EXPECTED_AXIOMS: Final = ["Classical.choice", "Quot.sound", "propext"]
THEOREM_FIELD_MAP: Final = {
    "PO-A1": [
        "coefficient_abs_max",
        "product_abs_bound",
        "product_width_bits",
        "q_abs_max",
    ],
    "PO-A2": [
        "final_abs_bound",
        "max_eligible_contributions",
        "max_incremental_prefix_abs",
        "selected_accumulator_width_bits",
    ],
    "PO-A3": ["common_denominator"],
}


class ProofGateError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ProofGateError(f"{code}: {detail}" if detail else code)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "JSON_ROOT_INVALID", str(path))
    return value


def sha256_file(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def identified_id(record: object, domain: str) -> tuple[str, dict[str, object]]:
    require(isinstance(record, dict), "IDENTIFIED_RECORD_INVALID", domain)
    value = record.get("value")
    require(isinstance(value, dict), "IDENTIFIED_VALUE_INVALID", domain)
    encoded = canonical_json_bytes(value)
    expected = content_id(domain, encoded)
    require(record.get("bytes_hex") == encoded.hex(), "IDENTIFIED_BYTES_INVALID", domain)
    require(record.get("content_id") == expected, "IDENTIFIED_ID_INVALID", domain)
    return expected, value


def verify_safe_pair(
    config_record: object,
    proof_record: object,
    *,
    expected_width: int,
) -> tuple[str, str]:
    config_id, config = identified_id(config_record, "deltareduce.004.fixedpoint-config.v1")
    proof_id, proof = identified_id(proof_record, "deltareduce.004.proof-instance.v1")
    require(proof["config_id"] == config_id, "PROOF_CONFIG_BINDING_INVALID")
    require(proof["profile_id"] == config["profile_id"], "PROOF_PROFILE_BINDING_INVALID")
    require(proof["scale_table_id"] == config["scale_table_id"], "PROOF_SCALE_BINDING_INVALID")
    require(config["parameter_schema_id"] == PARAMETER_SCHEMA_ID, "PROOF_SCHEMA_BINDING_INVALID")
    require(config["accumulator_width_bits"] == expected_width, "CONFIG_WIDTH_INVALID")
    require(proof["product_width_bits"] == expected_width, "PRODUCT_WIDTH_INVALID")
    require(proof["selected_accumulator_width_bits"] == expected_width, "FINAL_WIDTH_INVALID")
    require(
        proof["coefficient_abs_max"] == config["coefficient_abs_max"],
        "COEFFICIENT_BINDING_INVALID",
    )
    require(
        proof["max_eligible_contributions"] == config["max_eligible_contributions"],
        "COUNT_BINDING_INVALID",
    )
    require(proof["q_abs_max"] == config["q_abs_max"] == "32767", "Q_BINDING_INVALID")
    require(proof["formal_semantics_id"] == FORMAL_SEMANTICS_ID, "PROOF_FORMAL_ID_INVALID")
    require(config["formal_semantics_id"] == FORMAL_SEMANTICS_ID, "CONFIG_FORMAL_ID_INVALID")
    require(proof["lean_artifact_sha256"] == LEAN_SOURCE_ID, "PROOF_LEAN_SOURCE_INVALID")
    require(proof["theorems"] == THEOREMS, "PROOF_THEOREMS_INVALID")
    q_bound = int(proof["q_abs_max"])
    coefficient = int(proof["coefficient_abs_max"])
    count = int(proof["max_eligible_contributions"])
    product = q_bound * coefficient
    final = product * count
    require(int(proof["product_abs_bound"]) == product, "PROOF_PRODUCT_INVALID")
    require(int(proof["max_incremental_prefix_abs"]) == final, "PROOF_PREFIX_INVALID")
    require(int(proof["final_abs_bound"]) == final, "PROOF_FINAL_INVALID")
    require(product <= (1 << (expected_width - 1)) - 1, "PRODUCT_WIDTH_UNSAFE")
    require(final <= (1 << (expected_width - 1)) - 1, "FINAL_WIDTH_UNSAFE")
    require(proof["result"] == "PASS", "SAFE_PROOF_NOT_PASS")
    return config_id, proof_id


def verify_first_unsafe() -> dict[str, str]:
    negative = load_json(NEGATIVE_PATH)
    cases = negative["cases"]
    require(isinstance(cases, list), "NEGATIVE_CASES_INVALID")
    record = next(
        item for item in cases if isinstance(item, dict) and item.get("id") == "int64-first-unsafe"
    )
    config_id, config = identified_id(
        record["fixedpoint_config"], "deltareduce.004.fixedpoint-config.v1"
    )
    proof = record["proof"]
    require(isinstance(proof, dict), "UNSAFE_PROOF_INVALID")
    require(proof["config_id"] == config_id, "UNSAFE_CONFIG_BINDING_INVALID")
    require(
        proof["coefficient_abs_max"] == config["coefficient_abs_max"],
        "UNSAFE_A_BINDING_INVALID",
    )
    product = int(proof["product_abs_bound"])
    prefix = int(proof["max_incremental_prefix_abs"])
    require(product <= (1 << 63) - 1 < prefix, "FIRST_UNSAFE_NOT_EXACT")
    require(proof["result"] == "REJECT", "FIRST_UNSAFE_NOT_REJECT")
    return {
        "config_id": config_id,
        "reason": "INCREMENTAL_PREFIX_EXCEEDS_INT64",
        "status": "REJECT",
    }


def verify_mutation_invalidation(
    config_record: object,
    proof_record: object,
) -> list[str]:
    original_config_id, config = identified_id(
        config_record, "deltareduce.004.fixedpoint-config.v1"
    )
    original_proof_id, proof = identified_id(proof_record, "deltareduce.004.proof-instance.v1")
    mutations: list[tuple[str, str, object]] = [
        ("profile", "profile_id", "sha256:" + "2" * 64),
        ("scale", "scale_table_id", "sha256:" + "3" * 64),
        ("count", "max_eligible_contributions", "4294967294"),
        ("coefficient", "coefficient_abs_max", "65537"),
        ("parameter-schema", "parameter_schema_id", "sha256:" + "4" * 64),
        ("shard-coverage", "shard_plan_id", "sha256:" + "5" * 64),
    ]
    invalidated: list[str] = []
    for identifier, field, replacement in mutations:
        changed_config = copy.deepcopy(config)
        changed_config[field] = replacement
        changed_config_id = content_id(
            "deltareduce.004.fixedpoint-config.v1", canonical_json_bytes(changed_config)
        )
        require(
            changed_config_id != original_config_id,
            "CONFIG_MUTATION_NOT_INVALIDATING",
            identifier,
        )
        changed_proof = copy.deepcopy(proof)
        changed_proof["config_id"] = changed_config_id
        if field in changed_proof:
            changed_proof[field] = replacement
        changed_proof_id = content_id(
            "deltareduce.004.proof-instance.v1", canonical_json_bytes(changed_proof)
        )
        require(
            changed_proof_id != original_proof_id,
            "PROOF_MUTATION_NOT_INVALIDATING",
            identifier,
        )
        invalidated.append(identifier)
    for identifier, field, replacement in (
        ("schema-version", "schema_version", "1.0.1"),
        ("formal-semantics", "formal_semantics_id", "sha256:" + "6" * 64),
    ):
        changed = copy.deepcopy(proof)
        changed[field] = replacement
        require(
            content_id("deltareduce.004.proof-instance.v1", canonical_json_bytes(changed))
            != original_proof_id,
            "PROOF_MUTATION_NOT_INVALIDATING",
            identifier,
        )
        invalidated.append(identifier)
    changed_theorems = copy.deepcopy(proof)
    changed_theorems["theorems"][0]["theorem_names"][0] = "DeltaReduce.mutatedProductBound"  # type: ignore[index]
    require(
        content_id("deltareduce.004.proof-instance.v1", canonical_json_bytes(changed_theorems))
        != original_proof_id,
        "THEOREM_MUTATION_NOT_INVALIDATING",
    )
    invalidated.append("theorem-map")
    return invalidated


def verify_lean_metadata() -> dict[str, object]:
    report = load_json(LEAN_REPORT_PATH)
    require(report["status"] == "PASS", "LEAN_REPORT_NOT_PASS")
    require(report["lean_toolchain"] == EXPECTED_TOOLCHAIN, "LEAN_TOOLCHAIN_INVALID")
    require(report["dependency_lock_sha256"] == EXPECTED_DEPENDENCY_LOCK, "LEAN_LOCK_INVALID")
    require(report["lake_manifest_sha256"] == EXPECTED_LAKE_MANIFEST, "LEAN_MANIFEST_INVALID")
    require(report["allowed_kernel_axioms"] == EXPECTED_AXIOMS, "LEAN_ALLOWED_AXIOMS_INVALID")
    require(report["reported_kernel_axioms"] == EXPECTED_AXIOMS, "LEAN_REPORTED_AXIOMS_INVALID")
    require("sha256:" + sha256_file(LEAN_SOURCE_PATH) == LEAN_SOURCE_ID, "LEAN_SOURCE_HASH_INVALID")
    conjuncts = report["normative_conjuncts"]
    require(isinstance(conjuncts, list), "LEAN_CONJUNCTS_INVALID")
    source_theorems = {
        str(item["theorem"]): str(item["source_sha256"])
        for item in conjuncts
        if isinstance(item, dict) and item.get("proof_obligation_id") in THEOREM_FIELD_MAP
    }
    required_normative = {
        "DeltaReduce.signedProductBound",
        "DeltaReduce.flatAccumulatorBound",
        *THEOREMS[2]["theorem_names"],
    }
    require(required_normative.issubset(source_theorems), "LEAN_NORMATIVE_THEOREM_MISSING")
    require(
        all(value == LEAN_SOURCE_ID.removeprefix("sha256:") for value in source_theorems.values()),
        "LEAN_THEOREM_SOURCE_HASH_INVALID",
    )
    source = LEAN_SOURCE_PATH.read_text(encoding="utf-8")
    for group in THEOREMS:
        for theorem in group["theorem_names"]:
            require(theorem.rsplit(".", 1)[-1] in source, "LEAN_THEOREM_SOURCE_MISSING", theorem)
    return {
        "allowed_kernel_axioms": EXPECTED_AXIOMS,
        "dependency_lock_sha256": EXPECTED_DEPENDENCY_LOCK,
        "lake_manifest_sha256": EXPECTED_LAKE_MANIFEST,
        "source_sha256": LEAN_SOURCE_ID,
        "theorem_field_map": THEOREM_FIELD_MAP,
        "toolchain": EXPECTED_TOOLCHAIN,
    }


def verify() -> dict[str, object]:
    protocol = verify_protocol_contracts()
    require(protocol["status"] == "PASS", "PROTOCOL_CONTRACT_NOT_PASS")
    valid = load_json(VALID_PATH)
    instances = valid["instances"]
    require(isinstance(instances, dict), "VALID_INSTANCES_INVALID")
    config64_id, proof64_id = verify_safe_pair(
        instances["fixedpoint_config_int64"],
        instances["proof_int64_maximum_safe"],
        expected_width=64,
    )
    config128_id, proof128_id = verify_safe_pair(
        instances["fixedpoint_config_int128"],
        instances["proof_int128"],
        expected_width=128,
    )
    invalidated = verify_mutation_invalidation(
        instances["fixedpoint_config_int64"], instances["proof_int64_maximum_safe"]
    )
    formal = verify_lean_metadata()
    unsafe = verify_first_unsafe()
    paths = [
        VALID_PATH,
        NEGATIVE_PATH,
        LEAN_REPORT_PATH,
        LEAN_SOURCE_PATH,
        ROOT / "delta-protocol" / "schemas" / "004" / "accumulator-proof-instance-v1.json",
        ROOT / "delta-protocol" / "schemas" / "004" / "fixedpoint-config-v1.json",
        ROOT / "delta-core-cpp" / "include" / "delta" / "fixedpoint" / "bounds.hpp",
        ROOT / "delta-core-cpp" / "src" / "fixedpoint" / "bounds.cpp",
        ROOT / "delta-core-cpp" / "tests" / "fixedpoint_test.cpp",
    ]
    return {
        "artifacts": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for path in sorted(paths)
        ],
        "classification": "REFINEMENT_ONLY",
        "first_unsafe_int64": unsafe,
        "formal": formal,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "instances": {
            "int128": {"config_id": config128_id, "proof_id": proof128_id, "status": "PASS"},
            "int64_maximum_safe": {
                "config_id": config64_id,
                "proof_id": proof64_id,
                "status": "PASS",
            },
        },
        "mutation_invalidation": invalidated,
        "phase": "004-concrete-proof-instances",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "tasks": ["T031", "T032", "T033", "T034", "T035"],
    }


def canonical_output(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def fail(error: Exception) -> NoReturn:
    print(
        canonical_output(
            {
                "error": str(error),
                "phase": "004-concrete-proof-instances",
                "schema_version": "1.0.0",
                "status": "FAIL",
            }
        )
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.parse_args()
    try:
        result = verify()
    except (ProofGateError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        fail(exc)
    print(canonical_output(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
