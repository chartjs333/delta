"""Verify frozen feature-004 schemas, identities and independent golden contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
WORKER_SRC: Final = ROOT / "delta-worker-python" / "src"
SCRIPT_DIR: Final = Path(__file__).resolve().parent
for import_root in (WORKER_SRC, SCRIPT_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from deltatorrent.reference.fixedpoint_encoder import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    ContractError,
    Rational,
    canonical_json_bytes,
    content_id,
    encode_payload,
    leaf_id,
    merkle_root,
    quantize,
)
from fixedpoint_contracts import (  # noqa: E402
    FIXTURES,
    LEAN_SOURCE_ID,
    PARAMETER_SCHEMA_ID,
    THEOREMS,
    TICKET_ID,
)

FEATURE_DIR: Final = ROOT / "specs" / "004-compressed-delta-protocol"
PROTOCOL_DIR: Final = ROOT / "delta-protocol"
SCHEMA_DIR: Final = PROTOCOL_DIR / "schemas" / "004"
FIXTURE_DIR: Final = PROTOCOL_DIR / "fixtures" / "004"
REGISTRY_PATH: Final = SCHEMA_DIR / "registry-v1.json"
ROOT_REGISTRY_PATH: Final = PROTOCOL_DIR / "registry.json"
HASH_MANIFEST_PATH: Final = FIXTURE_DIR / "golden-hashes-v1.json"
EVIDENCE_PATH: Final = FEATURE_DIR / "evidence" / "protocol-contracts.json"

EXPECTED_SCHEMA_IDS: Final = {
    "accumulator-proof-instance-v1.json": "urn:deltareduce:schema:accumulator-proof-instance:1",
    "encoded-contribution-manifest-v1.json": (
        "urn:deltareduce:schema:encoded-contribution-manifest:1"
    ),
    "encoded-shard-v1.json": "urn:deltareduce:schema:encoded-shard:1",
    "fixed-point-profile-v1.json": "urn:deltareduce:schema:fixed-point-profile:1",
    "fixedpoint-config-v1.json": "urn:deltareduce:schema:fixedpoint-config:1",
    "scale-table-v1.json": "urn:deltareduce:schema:scale-table:1",
    "shard-plan-v1.json": "urn:deltareduce:schema:shard-plan:1",
}
EXPECTED_NEGATIVE_IDS: Final = {
    "duplicate-ordinal",
    "first-negative-out-of-range",
    "first-positive-out-of-range",
    "float-profile",
    "gap",
    "huge-scaled-numerator",
    "int64-first-unsafe",
    "nan",
    "non-canonical-zero",
    "non-reduced",
    "overlap",
    "oversized-header",
    "positive-infinity",
    "raw-minus-32768",
    "residual-field",
    "too-many-shards",
    "trailing-data",
    "truncated-prefix",
    "worker-dynamic-scale",
    "wrong-profile",
    "wrong-schema",
    "wrong-ticket",
    "zero-denominator",
}


class VerificationError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise VerificationError(f"{code}{suffix}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    require(isinstance(value, dict), "JSON_ROOT_INVALID", str(path))
    return value


def sha256_file(path: Path) -> str:
    raw = path.read_bytes()
    if b"\x00" not in raw:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def _git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def _canonical_hash(raw: bytes) -> str:
    if b"\x00" not in raw:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def verify_schemas() -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for name, schema_id in sorted(EXPECTED_SCHEMA_IDS.items()):
        path = SCHEMA_DIR / name
        schema = load_json(path)
        require(
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            "SCHEMA_DRAFT_INVALID",
            name,
        )
        require(schema.get("$id") == schema_id, "SCHEMA_ID_INVALID", name)
        require(schema.get("type") == "object", "SCHEMA_ROOT_TYPE_INVALID", name)
        require(schema.get("additionalProperties") is False, "SCHEMA_UNKNOWN_FIELDS_ALLOWED", name)
        required = schema.get("required")
        properties = schema.get("properties")
        require(isinstance(required, list) and required, "SCHEMA_REQUIRED_MISSING", name)
        require(isinstance(properties, dict), "SCHEMA_PROPERTIES_MISSING", name)
        require(set(required).issubset(properties), "SCHEMA_REQUIRED_UNKNOWN", name)
        artifacts.append(
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256_file(path)}
        )
    document = SCHEMA_DIR / "canonical-fixedpoint-v1.md"
    text = document.read_text(encoding="utf-8")
    for token in (
        "[-32767, 32767]",
        "round_ties_even",
        "deltareduce.004.merkle-node.v1",
        "PO-A3",
        "not claimed",
    ):
        require(token.lower() in text.lower(), "ENCODING_DOCUMENT_INCOMPLETE", token)
    artifacts.append(
        {
            "path": str(document.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(document),
        }
    )
    return artifacts


def verify_fixtures() -> tuple[dict[str, object], list[dict[str, str]]]:
    artifacts: list[dict[str, str]] = []
    for relative, factory in sorted(FIXTURES.items()):
        path = FIXTURE_DIR / relative
        raw = path.read_bytes()
        expected = canonical_json_bytes(factory()) + b"\n"
        require(raw == expected, "FIXTURE_NOT_DETERMINISTIC", relative)
        artifacts.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    golden = load_json(FIXTURE_DIR / "cross-language" / "golden-v1.json")
    negative = load_json(FIXTURE_DIR / "invalid" / "fixedpoint-negative-v1.json")
    cases = negative.get("cases")
    require(isinstance(cases, list), "NEGATIVE_CASES_INVALID")
    require(
        {case["id"] for case in cases if isinstance(case, dict)} == EXPECTED_NEGATIVE_IDS,
        "NEGATIVE_CORPUS_INCOMPLETE",
    )
    unsafe = next(
        case for case in cases if isinstance(case, dict) and case["id"] == "int64-first-unsafe"
    )
    proof = unsafe["proof"]
    require(isinstance(proof, dict), "FIRST_UNSAFE_PROOF_INVALID")
    product = int(proof["product_abs_bound"])
    final = int(proof["final_abs_bound"])
    require(product <= (1 << 63) - 1 < final, "FIRST_UNSAFE_BOUNDARY_INVALID")
    require(
        proof["selected_accumulator_width_bits"] == 64 and proof["result"] == "REJECT",
        "FIRST_UNSAFE_RESULT_INVALID",
    )
    return golden, artifacts


def _verify_identified(record: object, domain: str) -> Mapping[str, object]:
    require(isinstance(record, dict), "IDENTIFIED_RECORD_INVALID", domain)
    require(
        set(record) == {"bytes_hex", "content_id", "value"}, "IDENTIFIED_FIELDS_INVALID", domain
    )
    encoded = canonical_json_bytes(record["value"])
    require(record["bytes_hex"] == encoded.hex(), "IDENTIFIED_BYTES_INVALID", domain)
    require(record["content_id"] == content_id(domain, encoded), "IDENTIFIED_HASH_INVALID", domain)
    return record


def verify_quantization_boundaries() -> None:
    quantum = Rational(1, 1)
    cases = [
        (Rational(0, 1), 0),
        (Rational(1, 2), 0),
        (Rational(3, 2), 2),
        (Rational(-1, 2), 0),
        (Rational(-3, 2), -2),
        (Rational(32_767, 1), 32_767),
        (Rational(-32_767, 1), -32_767),
    ]
    for source, expected in cases:
        require(quantize(source, quantum) == expected, "ROUNDING_BOUNDARY_INVALID", str(source))
    require(
        encode_payload([0, 1, -1, 32_767, -32_767]).hex() == "00000100ffffff7f0180",
        "LITTLE_ENDIAN_PAYLOAD_INVALID",
    )
    for value in (Rational(32_768, 1), Rational(-32_768, 1)):
        try:
            quantize(value, quantum)
        except ContractError as exc:
            require(exc.code == "QUANTIZATION_RANGE_EXCEEDED", "RANGE_STATUS_INVALID")
        else:
            require(False, "OUT_OF_RANGE_ACCEPTED", str(value))
    try:
        quantize(Rational((1 << 63) - 1, 1), Rational(1, 0xFFFFFFFF))
    except ContractError as exc:
        require(exc.code == "QUANTIZATION_INTERMEDIATE_OVERFLOW", "OVERFLOW_STATUS_INVALID")
    else:
        require(False, "INTERMEDIATE_OVERFLOW_ACCEPTED")


def verify_proof(record: Mapping[str, object], *, expected_width: int) -> None:
    value = record["value"]
    require(isinstance(value, dict), "PROOF_VALUE_INVALID")
    q_bound = int(value["q_abs_max"])
    coefficient = int(value["coefficient_abs_max"])
    count = int(value["max_eligible_contributions"])
    product = q_bound * coefficient
    final = product * count
    require(int(value["product_abs_bound"]) == product, "PROOF_PRODUCT_INVALID")
    require(int(value["max_incremental_prefix_abs"]) == final, "PROOF_PREFIX_INVALID")
    require(int(value["final_abs_bound"]) == final, "PROOF_FINAL_INVALID")
    require(value["product_width_bits"] == expected_width, "PROOF_PRODUCT_WIDTH_INVALID")
    require(
        value["selected_accumulator_width_bits"] == expected_width,
        "PROOF_ACCUMULATOR_WIDTH_INVALID",
    )
    require(value["lean_artifact_sha256"] == LEAN_SOURCE_ID, "PROOF_LEAN_ID_INVALID")
    require(value["theorems"] == THEOREMS, "PROOF_THEOREM_MAP_INVALID")
    limit = (1 << (expected_width - 1)) - 1
    require(product <= limit and final <= limit, "PROOF_BOUND_UNSAFE")


def _decode_envelope(envelope: bytes) -> tuple[dict[str, object], bytes]:
    require(len(envelope) >= 16, "SHARD_TRUNCATED")
    require(envelope[:4] == b"DRQ1", "SHARD_MAGIC_INVALID")
    major, minor, header_length, payload_length = struct.unpack("<HHII", envelope[4:16])
    require((major, minor) == (1, 0), "SHARD_VERSION_INVALID")
    require(header_length <= 65_536, "SHARD_HEADER_TOO_LARGE")
    require(payload_length <= 1_048_576, "SHARD_PAYLOAD_TOO_LARGE")
    expected_length = 16 + header_length + payload_length
    require(len(envelope) == expected_length, "SHARD_LENGTH_OR_TRAILING_INVALID")
    header_bytes = envelope[16 : 16 + header_length]
    header = json.loads(header_bytes, object_pairs_hook=_reject_duplicate_keys)
    require(isinstance(header, dict), "SHARD_HEADER_INVALID")
    require(canonical_json_bytes(header) == header_bytes, "SHARD_HEADER_NOT_CANONICAL")
    payload = envelope[16 + header_length :]
    require(payload_length == 2 * int(header["element_count"]), "SHARD_ELEMENT_LENGTH_INVALID")
    require(
        header["payload_sha256"] == "sha256:" + hashlib.sha256(payload).hexdigest(),
        "SHARD_PAYLOAD_HASH_INVALID",
    )
    return header, payload


def verify_golden(golden: dict[str, object]) -> dict[str, str]:
    profile = _verify_identified(golden["profile"], "deltareduce.004.profile.v1")
    scale = _verify_identified(golden["scale_table"], "deltareduce.004.scale-table.v1")
    plan = _verify_identified(golden["shard_plan"], "deltareduce.004.shard-plan.v1")
    proof = _verify_identified(golden["proof_instance"], "deltareduce.004.proof-instance.v1")
    config = _verify_identified(golden["fixedpoint_config"], "deltareduce.004.fixedpoint-config.v1")
    manifest = _verify_identified(golden["manifest"], "deltareduce.004.manifest.v1")
    verify_proof(proof, expected_width=64)
    valid = load_json(FIXTURE_DIR / "valid" / "fixedpoint-contract-v1.json")
    proof128 = valid["instances"]["proof_int128"]  # type: ignore[index]
    require(isinstance(proof128, dict), "INT128_PROOF_INVALID")
    _verify_identified(proof128, "deltareduce.004.proof-instance.v1")
    verify_proof(proof128, expected_width=128)
    profile_value = profile["value"]
    require(isinstance(profile_value, dict), "PROFILE_VALUE_INVALID")
    require(
        profile_value["q_min"] == -32_767 and profile_value["q_max"] == 32_767,
        "PROFILE_RANGE_INVALID",
    )
    require(profile_value["residual_mode"] == "FORBIDDEN", "RESIDUAL_PROFILE_ACCEPTED")
    scale_value = scale["value"]
    plan_value = plan["value"]
    require(
        isinstance(scale_value, dict) and isinstance(plan_value, dict), "CONTRACT_VALUE_INVALID"
    )
    require(scale_value["profile_id"] == profile["content_id"], "SCALE_PROFILE_MISMATCH")
    require(plan_value["scale_table_id"] == scale["content_id"], "PLAN_SCALE_MISMATCH")
    config_value = config["value"]
    require(isinstance(config_value, dict), "FIXEDPOINT_CONFIG_VALUE_INVALID")
    require(config_value["profile_id"] == profile["content_id"], "CONFIG_PROFILE_MISMATCH")
    require(config_value["scale_table_id"] == scale["content_id"], "CONFIG_SCALE_MISMATCH")
    require(config_value["shard_plan_id"] == plan["content_id"], "CONFIG_PLAN_MISMATCH")
    require(config_value["parameter_schema_id"] == PARAMETER_SCHEMA_ID, "CONFIG_SCHEMA_MISMATCH")
    proof_value = proof["value"]
    require(isinstance(proof_value, dict), "PROOF_VALUE_INVALID")
    require(proof_value["config_id"] == config["content_id"], "PROOF_CONFIG_MISMATCH")
    entries = plan_value["entries"]
    require(isinstance(entries, list) and len(entries) == 5, "PLAN_ENTRY_COUNT_INVALID")
    cursor = 0
    for ordinal, entry in enumerate(entries):
        require(isinstance(entry, dict), "PLAN_ENTRY_INVALID")
        require(entry["ordinal"] == ordinal, "PLAN_ORDINAL_INVALID")
        require(entry["element_start"] == cursor, "PLAN_GAP_OR_OVERLAP")
        require(entry["payload_bytes"] == 2 * int(entry["element_count"]), "PLAN_LENGTH_INVALID")
        cursor += int(entry["element_count"])
    require(cursor == plan_value["total_elements"] == 36, "PLAN_COVERAGE_INVALID")
    boundary_vectors = golden["boundary_vectors"]
    require(isinstance(boundary_vectors, list), "BOUNDARY_VECTORS_INVALID")
    require(
        {item["id"] for item in boundary_vectors if isinstance(item, dict)}
        == {
            "negative-half-even-two",
            "negative-half-even-zero",
            "negative-maximum",
            "negative-zero",
            "positive-half-even-two",
            "positive-half-even-zero",
            "positive-maximum",
            "positive-zero",
            "smallest-negative-nonzero",
            "smallest-positive-nonzero",
        },
        "BOUNDARY_CORPUS_INCOMPLETE",
    )
    for vector in boundary_vectors:
        require(isinstance(vector, dict), "BOUNDARY_VECTOR_INVALID")
        source_value = Rational.parse(vector["normalized_source"])
        quantum_value = Rational.parse(vector["quantum"], positive=True)
        expected_q = quantize(source_value, quantum_value)
        require(expected_q == vector["expected_q"], "BOUNDARY_Q_INVALID", str(vector["id"]))
        require(
            encode_payload([expected_q]).hex() == vector["expected_payload_hex"],
            "BOUNDARY_PAYLOAD_INVALID",
            str(vector["id"]),
        )
        if vector["id"] in {"positive-zero", "negative-zero"}:
            require(
                vector["normalized_source"] == {"denominator": 1, "numerator": "0"},
                "SIGNED_ZERO_NOT_CANONICAL",
            )
    source = golden["normalized_source"]
    q_values = golden["q_values"]
    require(isinstance(source, list) and isinstance(q_values, list), "GOLDEN_VECTOR_INVALID")
    require(len(source) == len(q_values) == 36, "GOLDEN_VECTOR_LENGTH_INVALID")
    recomputed_q: list[int] = []
    for item in source:
        require(isinstance(item, dict), "SOURCE_ITEM_INVALID")
        parsed = Rational.parse(
            {"denominator": item["denominator"], "numerator": item["numerator"]}
        )
        quantum = Rational(1, 4) if item["segment_id"] == "decoder.bias" else Rational(1, 16)
        recomputed_q.append(quantize(parsed, quantum))
    require(recomputed_q == q_values, "GOLDEN_Q_INVALID")
    shards = golden["shards"]
    require(isinstance(shards, list) and len(shards) == len(entries), "GOLDEN_SHARDS_INVALID")
    leaves: list[str] = []
    for entry, shard in zip(entries, shards, strict=True):
        require(isinstance(shard, dict), "GOLDEN_SHARD_INVALID")
        envelope = bytes.fromhex(str(shard["envelope_hex"]))
        header, payload = _decode_envelope(envelope)
        require(header == shard["header"], "GOLDEN_HEADER_INVALID")
        require(payload.hex() == shard["payload_hex"], "GOLDEN_PAYLOAD_INVALID")
        require(header["formal_semantics_id"] == FORMAL_SEMANTICS_ID, "SHARD_FORMAL_ID_INVALID")
        require(header["profile_id"] == profile["content_id"], "SHARD_PROFILE_INVALID")
        require(header["scale_table_id"] == scale["content_id"], "SHARD_SCALE_INVALID")
        require(header["shard_plan_id"] == plan["content_id"], "SHARD_PLAN_INVALID")
        require(header["proof_instance_id"] == proof["content_id"], "SHARD_PROOF_INVALID")
        require(header["parameter_schema_id"] == PARAMETER_SCHEMA_ID, "SHARD_SCHEMA_INVALID")
        require(header["round_config_id"] == config["content_id"], "SHARD_CONFIG_INVALID")
        require(header["ticket_id"] == TICKET_ID, "SHARD_TICKET_INVALID")
        require(header["ordinal"] == entry["ordinal"], "SHARD_ORDINAL_INVALID")
        current_leaf = leaf_id(envelope)
        require(current_leaf == shard["leaf_id"], "GOLDEN_LEAF_INVALID")
        leaves.append(current_leaf)
    root = merkle_root(leaves)
    manifest_value = manifest["value"]
    require(isinstance(manifest_value, dict), "MANIFEST_VALUE_INVALID")
    require(root == manifest_value["commitment_root"], "GOLDEN_ROOT_INVALID")
    require(
        [item["leaf_id"] for item in manifest_value["shards"]] == leaves,
        "MANIFEST_SHARD_ORDER_INVALID",
    )
    return {
        "commitment_root": root,
        "fixedpoint_config_id": str(config["content_id"]),
        "manifest_id": str(manifest["content_id"]),
        "profile_id": str(profile["content_id"]),
        "proof_instance_id": str(proof["content_id"]),
        "scale_table_id": str(scale["content_id"]),
        "shard_plan_id": str(plan["content_id"]),
    }


def _records(value: object, name: str) -> list[dict[str, object]]:
    require(isinstance(value, list), "REGISTRY_SECTION_INVALID", name)
    require(all(isinstance(item, dict) for item in value), "REGISTRY_RECORD_INVALID", name)
    return value  # type: ignore[return-value]


def verify_registries(identities: Mapping[str, str]) -> list[dict[str, str]]:
    registry = load_json(REGISTRY_PATH)
    require(registry["formal_semantics_id"] == FORMAL_SEMANTICS_ID, "REGISTRY_FORMAL_ID_INVALID")
    require(registry["encoding_id"] == "delta-fixedpoint-shard-v1", "REGISTRY_ENCODING_INVALID")
    require(registry["semantic_completeness_claimed"] is False, "SEMANTIC_CLAIM_OVERSTATED")
    artifacts: list[dict[str, str]] = []
    for section in ("artifacts", "fixtures"):
        for item in _records(registry[section], section):
            path = PROTOCOL_DIR / str(item["path"])
            require(path.is_file(), "REGISTRY_PATH_MISSING", str(path))
            require(item["sha256"] == sha256_file(path), "REGISTRY_HASH_INVALID", str(item["path"]))
            artifacts.append(
                {
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": str(item["sha256"]),
                }
            )
    hash_manifest = load_json(HASH_MANIFEST_PATH)
    require(
        hash_manifest["semantic_completeness_claimed"] is False, "HASH_MANIFEST_CLAIM_OVERSTATED"
    )
    require(hash_manifest["identities"] == identities, "HASH_MANIFEST_IDENTITIES_INVALID")
    for item in _records(hash_manifest["artifacts"], "hash-manifest artifacts"):
        require(
            item["sha256"] == sha256_file(PROTOCOL_DIR / str(item["path"])),
            "HASH_MANIFEST_ARTIFACT_INVALID",
            str(item["path"]),
        )
    root_registry = load_json(ROOT_REGISTRY_PATH)
    root_items: dict[str, dict[str, object]] = {}
    for section in ("extensions", "fixtures", "schemas"):
        for item in _records(root_registry[section], section):
            require(
                str(item["id"]) not in root_items, "ROOT_REGISTRY_DUPLICATE_ID", str(item["id"])
            )
            root_items[str(item["id"])] = item
    for item in [
        *_records(registry["artifacts"], "artifacts"),
        *_records(registry["fixtures"], "fixtures"),
    ]:
        registry_id = str(item["id"])
        if (
            registry_id == "ENCODING-FIXEDPOINT-004-V1"
            or registry_id.startswith("SCHEMA-")
            or registry_id.startswith("FIXEDPOINT004-")
        ):
            require(
                root_items.get(registry_id) == item, "ROOT_REGISTRY_RECORD_INVALID", registry_id
            )
    extension = root_items.get("REGISTRY-FIXEDPOINT-004-V1")
    require(extension is not None, "ROOT_REGISTRY_004_MISSING")
    require(extension["sha256"] == sha256_file(REGISTRY_PATH), "ROOT_REGISTRY_004_HASH_INVALID")
    feature_media = {
        str(item["id"]): item for item in _records(registry["media_types"], "media_types")
    }
    root_media = {
        str(item["id"]): item for item in _records(root_registry["media_types"], "media_types")
    }
    require(
        all(root_media.get(key) == item for key, item in feature_media.items()),
        "ROOT_MEDIA_TYPES_INVALID",
    )
    artifacts.extend(
        [
            {
                "path": str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(REGISTRY_PATH),
            },
            {
                "path": str(ROOT_REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(ROOT_REGISTRY_PATH),
            },
            {
                "path": str(HASH_MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(HASH_MANIFEST_PATH),
            },
        ]
    )
    return artifacts


def verify_bindings() -> list[dict[str, str]]:
    preflight = load_json(FEATURE_DIR / "evidence" / "preflight.json")
    require(preflight["status"] == "PASS", "PREFLIGHT_NOT_PASS")
    require(
        preflight["formal"]["formal_semantics_id"] == FORMAL_SEMANTICS_ID,
        "PREFLIGHT_FORMAL_ID_INVALID",
    )  # type: ignore[index]
    parameter_fixture = load_json(
        PROTOCOL_DIR / "fixtures" / "local-round" / "parameter-schema-v1.json"
    )
    parameter_bytes = canonical_json_bytes(parameter_fixture)
    require(
        "sha256:" + hashlib.sha256(parameter_bytes).hexdigest() == PARAMETER_SCHEMA_ID,
        "PARAMETER_SCHEMA_ID_INVALID",
    )
    proof_report = load_json(ROOT / "formal" / "reports" / "lean-proof-report.json")
    conjuncts = proof_report["normative_conjuncts"]
    require(isinstance(conjuncts, list), "LEAN_CONJUNCTS_INVALID")
    reported_names = {
        item["theorem"]
        for item in conjuncts
        if isinstance(item, dict) and item.get("proof_obligation_id") in {"PO-A1", "PO-A2", "PO-A3"}
    }
    required_names = {name for group in THEOREMS for name in group["theorem_names"]}
    lean_source = (ROOT / "formal" / "proofs" / "DeltaReduce" / "FixedPoint.lean").read_text(
        encoding="utf-8"
    )
    for theorem_name in required_names:
        short = theorem_name.rsplit(".", 1)[-1]
        require(short in lean_source, "LEAN_THEOREM_SOURCE_MISSING", theorem_name)
    report_required = {
        "DeltaReduce.signedProductBound",
        "DeltaReduce.flatAccumulatorBound",
        *next(group["theorem_names"] for group in THEOREMS if group["obligation_id"] == "PO-A3"),
    }
    require(report_required.issubset(reported_names), "LEAN_REPORT_THEOREM_MISSING")
    task_map = (FEATURE_DIR / "task-map.md").read_text(encoding="utf-8")
    tasks = (FEATURE_DIR / "tasks.md").read_text(encoding="utf-8")
    for task in range(5, 13):
        require(f"T{task:03d}" in tasks, "TASK_MISSING", f"T{task:03d}")
    require(
        "T005" in task_map
        and "T012" in task_map
        and "HR004-002" in task_map
        and "HR004-006" in task_map,
        "TASK_MAP_INVALID",
    )
    feature003_registry = load_json(PROTOCOL_DIR / "schemas" / "003" / "registry-v1.json")
    require(
        feature003_registry["formal_semantics_id"] == FORMAL_SEMANTICS_ID,
        "FEATURE003_REGISTRY_DRIFT",
    )
    paths = [
        FEATURE_DIR / "task-map.md",
        FEATURE_DIR / "tasks.md",
        ROOT / "formal" / "proofs" / "DeltaReduce" / "FixedPoint.lean",
        ROOT / "formal" / "reports" / "lean-proof-report.json",
        PROTOCOL_DIR / "fixtures" / "local-round" / "parameter-schema-v1.json",
        PROTOCOL_DIR / "schemas" / "003" / "registry-v1.json",
    ]
    return [
        {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256_file(path)}
        for path in paths
    ]


def verify_published_evidence() -> None:
    evidence = load_json(EVIDENCE_PATH)
    require(evidence["status"] == "PASS", "CONTRACT_EVIDENCE_NOT_PASS")
    require(evidence["classification"] == "REFINEMENT_ONLY", "EVIDENCE_CLASS_INVALID")
    require(
        evidence["formal_semantics_id"] == FORMAL_SEMANTICS_ID,
        "EVIDENCE_FORMAL_ID_INVALID",
    )
    require(
        evidence["semantic_completeness_claimed"] is False,
        "EVIDENCE_CLAIM_OVERSTATED",
    )
    require(
        evidence["tasks"] == [f"T{task:03d}" for task in range(5, 13)],
        "EVIDENCE_TASKS_INVALID",
    )
    source_commit = evidence["source_commit"]
    require(
        isinstance(source_commit, str) and len(source_commit) == 40,
        "EVIDENCE_SOURCE_INVALID",
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    require(ancestor.returncode == 0, "EVIDENCE_SOURCE_NOT_ANCESTOR")
    artifacts = evidence["artifacts"]
    require(isinstance(artifacts, list) and artifacts, "EVIDENCE_ARTIFACTS_INVALID")
    for artifact in artifacts:
        require(isinstance(artifact, dict), "EVIDENCE_ARTIFACT_INVALID")
        path = str(artifact["path"])
        raw = _git_bytes("show", f"{source_commit}:{path}")
        require(
            artifact["sha256"] == _canonical_hash(raw),
            "EVIDENCE_ARTIFACT_HASH_INVALID",
            path,
        )
    require(
        EVIDENCE_PATH.read_bytes() == canonical_json_bytes(evidence) + b"\n",
        "CONTRACT_EVIDENCE_NOT_CANONICAL",
    )


def verify_all(source_commit: str | None = None) -> dict[str, object]:
    schema_artifacts = verify_schemas()
    golden, fixture_artifacts = verify_fixtures()
    verify_quantization_boundaries()
    identities = verify_golden(golden)
    registry_artifacts = verify_registries(identities)
    binding_artifacts = verify_bindings()
    if source_commit is not None:
        require(_git("rev-parse", source_commit) == source_commit, "SOURCE_COMMIT_NOT_CANONICAL")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
            cwd=ROOT,
            check=False,
        )
        require(ancestor.returncode == 0, "SOURCE_COMMIT_NOT_ANCESTOR")
    elif EVIDENCE_PATH.is_file():
        verify_published_evidence()
    artifacts_by_path = {
        item["path"]: item
        for item in [*schema_artifacts, *fixture_artifacts, *registry_artifacts, *binding_artifacts]
    }
    if source_commit is not None:
        artifacts_by_path = {
            path: {
                "path": path,
                "sha256": _canonical_hash(_git_bytes("show", f"{source_commit}:{path}")),
            }
            for path in artifacts_by_path
        }
    return {
        "artifacts": [artifacts_by_path[path] for path in sorted(artifacts_by_path)],
        "classification": "REFINEMENT_ONLY",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "golden": {**identities, "q_values": 36, "shards": 5},
        "independent_oracle": (
            "delta-worker-python/src/deltatorrent/reference/fixedpoint_encoder.py"
        ),
        "phase": "004-runtime-neutral-contracts",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source_commit": source_commit,
        "status": "PASS",
        "tasks": [f"T{task:03d}" for task in range(5, 13)],
    }


def _fail(error: Exception) -> NoReturn:
    failure = {
        "error": str(error),
        "phase": "004-runtime-neutral-contracts",
        "schema_version": "1.0.0",
        "status": "FAIL",
    }
    print(canonical_json_bytes(failure).decode("utf-8"))
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    try:
        result = verify_all(args.source_commit)
        encoded = canonical_json_bytes(result)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(encoded + b"\n")
        if args.check_only or args.output is None:
            print(encoded.decode("utf-8"))
        return 0
    except (ContractError, OSError, VerificationError, ValueError) as exc:
        _fail(exc)


if __name__ == "__main__":
    raise SystemExit(main())
