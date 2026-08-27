"""Validate and encode feature-003 runtime-neutral canonical protocol fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
DEFAULT_OUTPUT = FEATURE / "evidence" / "protocol-contracts.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
MAGIC = b"DRC1"
ENCODING_MAJOR = 1
ENCODING_MINOR = 0
MAX_ENVELOPE_BYTES = 16 * 1024 * 1024
MAX_VALUE_BYTES = 4 * 1024 * 1024
MAX_COLLECTION_ITEMS = 100_000
MAX_DEPTH = 32

REGISTRY_PATH = "delta-protocol/schemas/003/registry-v1.json"
TYPES_PATH = "delta-protocol/schemas/003/protocol-types-v1.json"
DOMAINS_PATH = "delta-protocol/schemas/003/hash-domains-v1.json"
VALID_PATH = "delta-protocol/fixtures/003/valid/protocol-inputs-v1.json"
INVALID_PATH = "delta-protocol/fixtures/003/invalid/canonical-binary-negative-v1.json"
GOLDEN_PATH = "delta-protocol/fixtures/003/cross-language/golden-v1.json"
SOURCE_PATHS = (
    "delta-protocol/schemas/003/canonical-binary-v1.md",
    DOMAINS_PATH,
    TYPES_PATH,
    REGISTRY_PATH,
    VALID_PATH,
    INVALID_PATH,
    GOLDEN_PATH,
    "delta-protocol/registry.json",
    "specs/003-bft-round-state-machine/scripts/verify_protocol_contracts.py",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class ContractError(ValueError):
    """Stable canonical protocol rejection."""


def reject(code: str, detail: str = "") -> NoReturn:
    raise ContractError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        reject(
            "GIT_COMMAND_FAILED",
            completed.stderr.decode("utf-8", errors="replace").strip(),
        )
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "UNSAFE_TRACKED_PATH",
        path,
    )
    return git_bytes("show", f"{revision}:{path}")


def strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def parse_json(raw: bytes, path: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_pairs)
    except UnicodeDecodeError as exc:
        reject("JSON_UTF8_INVALID", f"{path}:{exc}")
    except json.JSONDecodeError as exc:
        reject("JSON_INVALID", f"{path}:{exc}")
    require(isinstance(value, dict), "JSON_ROOT_NOT_MAP", path)
    canonical = canonical_json_bytes(value)
    require(raw in {canonical, canonical + b"\n"}, "JSON_NOT_CANONICAL", path)
    return value


def load_json(path: str, revision: str | None) -> dict[str, Any]:
    raw = (ROOT / path).read_bytes() if revision is None else tracked_bytes(path, revision)
    return parse_json(raw, path)


def _ascii(value: object, location: str) -> str:
    require(isinstance(value, str), "TEXT_REQUIRED", location)
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError:
        reject("NON_ASCII_TEXT", location)
    require(all(0x20 <= byte <= 0x7E for byte in encoded), "NON_PRINTABLE_TEXT", location)
    require(len(encoded) <= MAX_VALUE_BYTES, "VALUE_TOO_LARGE", location)
    return value


def validate_decimal(value: object, *, signed: bool, location: str = "$") -> str:
    text = _ascii(value, location)
    pattern = r"(?:0|-[1-9][0-9]*|[1-9][0-9]*)" if signed else r"(?:0|[1-9][0-9]*)"
    require(re.fullmatch(pattern, text) is not None, "DECIMAL_NOT_CANONICAL", location)
    number = int(text)
    lower = -(1 << 63) if signed else 0
    upper = (1 << 63) - 1 if signed else (1 << 64) - 1
    require(lower <= number <= upper, "DECIMAL_OUT_OF_RANGE", location)
    return text


def _validate_kind(
    value: object,
    kind: str,
    records: dict[str, list[dict[str, str]]],
    location: str,
) -> None:
    if kind == "ascii":
        _ascii(value, location)
    elif kind == "content-id":
        text = _ascii(value, location)
        require(
            re.fullmatch(r"sha256:[0-9a-f]{64}", text) is not None, "CONTENT_ID_INVALID", location
        )
    elif kind == "u32":
        require(type(value) is int and 0 <= value <= 0xFFFFFFFF, "U32_INVALID", location)
    elif kind in {"u64-decimal", "i64-decimal"}:
        validate_decimal(value, signed=kind.startswith("i"), location=location)
    elif kind in {"ascii-array", "content-id-array", "i64-decimal-array"}:
        require(isinstance(value, list), "ARRAY_REQUIRED", location)
        require(len(value) <= MAX_COLLECTION_ITEMS, "COLLECTION_TOO_LARGE", location)
        element_kind = kind.removesuffix("-array")
        for index, item in enumerate(value):
            _validate_kind(item, element_kind, records, f"{location}[{index}]")
    elif kind.startswith("record:"):
        _validate_record(value, records[kind.partition(":")[2]], records, location)
    elif kind.startswith("records:"):
        require(isinstance(value, list), "ARRAY_REQUIRED", location)
        require(len(value) <= MAX_COLLECTION_ITEMS, "COLLECTION_TOO_LARGE", location)
        fields = records[kind.partition(":")[2]]
        for index, item in enumerate(value):
            _validate_record(item, fields, records, f"{location}[{index}]")
    else:
        reject("SCHEMA_FIELD_KIND_UNKNOWN", kind)


def _validate_record(
    value: object,
    fields: list[dict[str, str]],
    records: dict[str, list[dict[str, str]]],
    location: str,
) -> None:
    require(isinstance(value, dict), "MAP_REQUIRED", location)
    expected = sorted(field["name"] for field in fields)
    require(sorted(value) == expected, "RECORD_FIELDS_INVALID", location)
    for field in fields:
        name = field["name"]
        _validate_kind(value[name], field["type"], records, f"{location}.{name}")


def _type_tables(
    revision: str | None,
) -> tuple[dict[int, dict[str, Any]], dict[str, str], dict[str, list[dict[str, str]]]]:
    schema = load_json(TYPES_PATH, revision)
    domains = load_json(DOMAINS_PATH, revision)
    require(schema.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "FORMAL_ID_INVALID")
    types = schema.get("types")
    records = schema.get("records")
    require(isinstance(types, list) and isinstance(records, dict), "TYPE_SCHEMA_INVALID")
    by_code = {item["type_code"]: item for item in types if isinstance(item, dict)}
    domain_records = domains.get("domains")
    require(isinstance(domain_records, list), "HASH_DOMAINS_INVALID")
    by_name = {
        item["type_name"]: item["value"] for item in domain_records if isinstance(item, dict)
    }
    require(
        [(item["type_code"], item["type_name"]) for item in types]
        == [(code, by_code[code]["type_name"]) for code in range(1, 11)],
        "TYPE_CODE_SET_INVALID",
    )
    require(set(by_name) == {item["type_name"] for item in types}, "HASH_DOMAIN_SET_INVALID")
    return by_code, by_name, records


def validate_qc(payload: dict[str, Any]) -> None:
    signers = payload["signer_ids"]
    votes = payload["vote_ids"]
    threshold = payload["quorum_threshold"]
    require(signers == sorted(set(signers)), "SIGNERS_NOT_CANONICAL")
    require(votes == sorted(set(votes)), "VOTES_NOT_CANONICAL")
    require(len(signers) == len(votes), "QC_VOTE_SIGNER_COUNT_MISMATCH")
    require(len(signers) >= threshold, "QUORUM_INSUFFICIENT")


def validate_payload(type_code: int, payload: object, revision: str | None) -> dict[str, Any]:
    by_code, _, records = _type_tables(revision)
    require(type_code in by_code, "TYPE_CODE_UNKNOWN", str(type_code))
    item = by_code[type_code]
    _validate_record(payload, item["fields"], records, "$")
    assert isinstance(payload, dict)
    require(payload["type_name"] == item["type_name"], "TYPE_NAME_MISMATCH")
    require(payload.get("schema_version") == "1.0.0", "SCHEMA_VERSION_INVALID")
    require(payload.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "FORMAL_ID_INVALID")
    if type_code == 1:
        validators = payload["validator_ids"]
        fault = payload["fault_tolerance"]
        require(validators == sorted(set(validators)), "VALIDATORS_NOT_CANONICAL")
        require(len(validators) == 3 * fault + 1, "VALIDATOR_SET_SIZE_INVALID")
        require(payload["quorum_threshold"] == 2 * fault + 1, "QUORUM_THRESHOLD_INVALID")
        require(
            payload["availability_threshold"] >= payload["quorum_threshold"],
            "AVAILABILITY_THRESHOLD_INVALID",
        )
        require(
            int(payload["soft_deadline_tick"]) < int(payload["hard_deadline_tick"]),
            "DEADLINE_ORDER_INVALID",
        )
        require(
            sum(item["ticket_count"] for item in payload["domain_ticket_counts"])
            == payload["ticket_count"],
            "TICKET_COUNT_INVALID",
        )
    elif type_code == 2:
        require(int(payload["cursor_start"]) < int(payload["cursor_end"]), "TICKET_RANGE_INVALID")
        require(payload["batch_budget"] > 0 and payload["step_budget"] > 0, "TICKET_BUDGET_INVALID")
    elif type_code == 4:
        validate_qc(payload)
    elif type_code == 5:
        require(
            payload["available_ticket_count"]
            <= payload["committed_ticket_count"]
            <= payload["ticket_count"],
            "STATE_COUNT_INVALID",
        )
    elif type_code == 10:
        profile = payload["integer_profile"]
        require(
            profile
            == {
                "accumulator_bits": 128,
                "byte_order": "BIG_ENDIAN",
                "profile_id": "bft-int-fixture-v1",
                "value_bits": 64,
            },
            "INTEGER_PROFILE_INVALID",
        )
    return payload


def encode_value(value: object, *, depth: int = 0) -> bytes:
    require(depth <= MAX_DEPTH, "NESTING_TOO_DEEP")
    if value is False:
        return b"\x01"
    if value is True:
        return b"\x02"
    if type(value) is int:
        if 0 <= value <= (1 << 64) - 1:
            return b"\x10" + value.to_bytes(8, "big", signed=False)
        if -(1 << 63) <= value < 0:
            return b"\x11" + value.to_bytes(8, "big", signed=True)
        reject("INTEGER_OUT_OF_RANGE")
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        require(len(raw) <= MAX_VALUE_BYTES, "VALUE_TOO_LARGE")
        return b"\x20" + struct.pack(">I", len(raw)) + raw
    if isinstance(value, str):
        raw = _ascii(value, "$").encode("ascii")
        return b"\x21" + struct.pack(">I", len(raw)) + raw
    if isinstance(value, float):
        reject("FLOAT_NOT_ALLOWED")
    if isinstance(value, list):
        require(len(value) <= MAX_COLLECTION_ITEMS, "COLLECTION_TOO_LARGE")
        return (
            b"\x30"
            + struct.pack(">I", len(value))
            + b"".join(encode_value(item, depth=depth + 1) for item in value)
        )
    if isinstance(value, dict):
        require(len(value) <= MAX_COLLECTION_ITEMS, "COLLECTION_TOO_LARGE")
        keys = sorted(value)
        for key in keys:
            require(isinstance(key, str), "MAP_KEY_NOT_TEXT")
            require(re.fullmatch(r"[a-z][a-z0-9_]*", key) is not None, "MAP_KEY_INVALID", key)
        pairs = b"".join(
            encode_value(key, depth=depth + 1) + encode_value(value[key], depth=depth + 1)
            for key in keys
        )
        return b"\x31" + struct.pack(">I", len(keys)) + pairs
    reject("VALUE_TYPE_UNSUPPORTED", type(value).__name__)


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0

    def take(self, count: int) -> bytes:
        require(count >= 0 and self.offset + count <= len(self.data), "VALUE_TRUNCATED")
        result = self.data[self.offset : self.offset + count]
        self.offset += count
        return result

    def u32(self) -> int:
        return int.from_bytes(self.take(4), "big")


def decode_value(reader: Reader, *, depth: int = 0) -> object:
    require(depth <= MAX_DEPTH, "NESTING_TOO_DEEP")
    tag = reader.take(1)[0]
    if tag == 0x01:
        return False
    if tag == 0x02:
        return True
    if tag == 0x10:
        return int.from_bytes(reader.take(8), "big", signed=False)
    if tag == 0x11:
        return int.from_bytes(reader.take(8), "big", signed=True)
    if tag in {0x20, 0x21}:
        length = reader.u32()
        require(length <= MAX_VALUE_BYTES, "VALUE_TOO_LARGE")
        raw = reader.take(length)
        if tag == 0x20:
            return raw
        try:
            value = raw.decode("ascii")
        except UnicodeDecodeError:
            reject("NON_ASCII_TEXT")
        _ascii(value, "$")
        return value
    if tag == 0x30:
        count = reader.u32()
        require(count <= MAX_COLLECTION_ITEMS, "COLLECTION_TOO_LARGE")
        return [decode_value(reader, depth=depth + 1) for _ in range(count)]
    if tag == 0x31:
        count = reader.u32()
        require(count <= MAX_COLLECTION_ITEMS, "COLLECTION_TOO_LARGE")
        result: dict[str, object] = {}
        prior: bytes | None = None
        for _ in range(count):
            require(reader.take(1) == b"\x21", "MAP_KEY_TAG_INVALID")
            length = reader.u32()
            raw = reader.take(length)
            require(prior is None or prior < raw, "MAP_KEYS_NOT_CANONICAL")
            prior = raw
            try:
                key = raw.decode("ascii")
            except UnicodeDecodeError:
                reject("NON_ASCII_TEXT")
            require(re.fullmatch(r"[a-z][a-z0-9_]*", key) is not None, "MAP_KEY_INVALID", key)
            result[key] = decode_value(reader, depth=depth + 1)
        return result
    reject("VALUE_TAG_UNKNOWN", f"{tag:02x}")


def encode_envelope(type_code: int, payload: object, revision: str | None = None) -> bytes:
    validate_payload(type_code, payload, revision)
    encoded = encode_value(payload)
    envelope = (
        MAGIC
        + bytes([ENCODING_MAJOR, ENCODING_MINOR])
        + struct.pack(">HI", type_code, len(encoded))
        + encoded
    )
    require(len(envelope) <= MAX_ENVELOPE_BYTES, "ENVELOPE_TOO_LARGE")
    return envelope


def decode_envelope(envelope: bytes, revision: str | None = None) -> tuple[int, dict[str, Any]]:
    require(len(envelope) >= 12, "ENVELOPE_TRUNCATED")
    require(len(envelope) <= MAX_ENVELOPE_BYTES, "ENVELOPE_TOO_LARGE")
    require(envelope[:4] == MAGIC, "ENVELOPE_MAGIC_INVALID")
    require(envelope[4:6] == bytes([ENCODING_MAJOR, ENCODING_MINOR]), "ENCODING_VERSION_INVALID")
    type_code, length = struct.unpack(">HI", envelope[6:12])
    by_code, _, _ = _type_tables(revision)
    require(type_code in by_code, "TYPE_CODE_UNKNOWN", str(type_code))
    require(length == len(envelope) - 12, "ENVELOPE_LENGTH_INVALID")
    reader = Reader(envelope[12:])
    payload = decode_value(reader)
    require(reader.offset == len(reader.data), "ENVELOPE_TRAILING_BYTES")
    require(isinstance(payload, dict), "PAYLOAD_ROOT_NOT_MAP")
    return type_code, validate_payload(type_code, payload, revision)


def content_id(type_code: int, envelope: bytes, revision: str | None = None) -> str:
    by_code, domains, _ = _type_tables(revision)
    require(type_code in by_code, "TYPE_CODE_UNKNOWN", str(type_code))
    domain = domains[by_code[type_code]["type_name"]].encode("ascii")
    return f"sha256:{sha256_bytes(domain + b'\x00' + envelope)}"


def golden_document(revision: str | None) -> dict[str, Any]:
    valid = load_json(VALID_PATH, revision)
    documents = valid.get("documents")
    require(isinstance(documents, list) and len(documents) == 10, "VALID_FIXTURE_SET_INVALID")
    vectors: list[dict[str, Any]] = []
    for document in documents:
        require(isinstance(document, dict), "VALID_FIXTURE_RECORD_INVALID")
        type_code = document.get("type_code")
        type_name = document.get("type_name")
        payload = document.get("payload")
        require(type(type_code) is int and isinstance(type_name, str), "FIXTURE_TYPE_INVALID")
        envelope = encode_envelope(type_code, payload, revision)
        decoded_code, decoded_payload = decode_envelope(envelope, revision)
        require(decoded_code == type_code and decoded_payload == payload, "ROUNDTRIP_MISMATCH")
        vectors.append(
            {
                "content_id": content_id(type_code, envelope, revision),
                "envelope_hex": envelope.hex(),
                "envelope_sha256": sha256_bytes(envelope),
                "type_code": type_code,
                "type_name": type_name,
            }
        )
    return {
        "encoding_id": "delta-canonical-binary-v1",
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "schema_version": "1.0.0",
        "vectors": vectors,
    }


def _capture_error(action: Callable[[], object]) -> str:
    try:
        action()
    except ContractError as exc:
        return str(exc).partition(":")[0]
    reject("NEGATIVE_CASE_ACCEPTED")


def _execute_negative(case: dict[str, Any], revision: str | None) -> object:
    operation = case["operation"]
    if operation == "PARSE_SOURCE_JSON":
        return json.loads(case["source_json"], object_pairs_hook=strict_pairs)
    if operation == "ENCODE_VALUE":
        value = json.loads(case["source_json"]) if "source_json" in case else case["value"]
        return encode_value(value)
    if operation == "VALIDATE_DECIMAL":
        return validate_decimal(case["value"], signed=case["signed"])
    if operation == "DECODE_ENVELOPE":
        return decode_envelope(bytes.fromhex(case["envelope_hex"]), revision)
    if operation == "VALIDATE_QC":
        return validate_qc(
            {
                "quorum_threshold": case["threshold"],
                "signer_ids": case["signer_ids"],
                "vote_ids": case["vote_ids"],
            }
        )
    reject("NEGATIVE_OPERATION_UNKNOWN", operation)


def verify_negative(revision: str | None) -> int:
    document = load_json(INVALID_PATH, revision)
    cases = document.get("cases")
    require(isinstance(cases, list) and len(cases) >= 9, "NEGATIVE_FIXTURE_SET_INVALID")
    for case in cases:
        require(isinstance(case, dict), "NEGATIVE_FIXTURE_INVALID")
        actual = _capture_error(lambda case=case: _execute_negative(case, revision))
        require(actual == case["expected_error"], "NEGATIVE_ERROR_MISMATCH", case["id"])
    return len(cases)


def verify_registry(revision: str | None) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH, revision)
    require(registry.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "REGISTRY_FORMAL_ID_INVALID")
    artifacts = registry.get("artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 3, "REGISTRY_ARTIFACT_SET_INVALID")
    for item in artifacts:
        require(isinstance(item, dict), "REGISTRY_ARTIFACT_INVALID")
        raw = (
            (ROOT / "delta-protocol" / item["path"]).read_bytes()
            if revision is None
            else tracked_bytes(f"delta-protocol/{item['path']}", revision)
        )
        require(sha256_bytes(raw) == item["sha256"], "REGISTRY_ARTIFACT_HASH_INVALID", item["path"])

    root_path = "delta-protocol/registry.json"
    root_raw = (
        (ROOT / root_path).read_bytes() if revision is None else tracked_bytes(root_path, revision)
    )
    try:
        root = json.loads(root_raw.decode("utf-8"), object_pairs_hook=strict_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("ROOT_REGISTRY_INVALID", str(exc))
    require(isinstance(root, dict), "ROOT_REGISTRY_INVALID")
    required_ids = {
        "BFT003-CANONICAL-NEGATIVE-V1",
        "BFT003-CROSS-LANGUAGE-GOLDEN-V1",
        "BFT003-PROTOCOL-INPUTS-V1",
        "ENCODING-DELTA-CANONICAL-BINARY-V1",
        "HASH-DOMAINS-BFT-003-V1",
        "REGISTRY-BFT-003-V1",
        "SCHEMA-BFT-PROTOCOL-TYPES-V1",
    }
    found_ids: set[str] = set()
    for group in ("extensions", "fixtures", "schemas"):
        records_in_group = root.get(group)
        require(isinstance(records_in_group, list), "ROOT_REGISTRY_GROUP_INVALID", group)
        paths = [item.get("path") for item in records_in_group if isinstance(item, dict)]
        require(paths == sorted(paths), "ROOT_REGISTRY_PATH_ORDER_INVALID", group)
        for item in records_in_group:
            require(isinstance(item, dict), "ROOT_REGISTRY_RECORD_INVALID", group)
            found_ids.add(item["id"])
            path = f"delta-protocol/{item['path']}"
            raw = (ROOT / path).read_bytes() if revision is None else tracked_bytes(path, revision)
            require(
                sha256_bytes(raw) == item["sha256"],
                "ROOT_REGISTRY_HASH_INVALID",
                item["path"],
            )
    require(required_ids <= found_ids, "ROOT_REGISTRY_IDS_MISSING")
    media = root.get("media_types")
    require(isinstance(media, list), "ROOT_MEDIA_TYPES_INVALID")
    require(
        any(
            isinstance(item, dict)
            and item.get("id") == "MEDIA-BFT-CANONICAL-BINARY-V1"
            and item.get("schema_id") == "SCHEMA-BFT-PROTOCOL-TYPES-V1"
            for item in media
        ),
        "ROOT_MEDIA_TYPE_MISSING",
    )
    return {
        "artifact_count": len(artifacts),
        "registered_feature003_ids": len(required_ids),
        "registry_version": registry["registry_version"],
    }


def verify(revision: str | None) -> dict[str, Any]:
    registry = verify_registry(revision)
    expected = golden_document(revision)
    golden = load_json(GOLDEN_PATH, revision)
    require(golden == expected, "GOLDEN_FIXTURE_STALE")
    negative_count = verify_negative(revision)
    artifacts = []
    for path in SOURCE_PATHS:
        raw = (ROOT / path).read_bytes() if revision is None else tracked_bytes(path, revision)
        artifacts.append({"path": path, "sha256": sha256_bytes(raw)})
    return {
        "artifacts": artifacts,
        "checks": [
            "TYPE_CODES_AND_HASH_DOMAINS_FROZEN",
            "VALID_PAYLOADS_SCHEMA_CHECKED",
            "CANONICAL_BINARY_ROUNDTRIP_EXACT",
            "CROSS_LANGUAGE_GOLDEN_BYTES_EXACT",
            "INVALID_CORPUS_REJECTED",
            "ROOT_PROTOCOL_REGISTRY_BOUND",
        ],
        "errors": [],
        "formal_impact": "REFINEMENT_ONLY",
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "golden_vector_count": len(expected["vectors"]),
        "negative_case_count": negative_count,
        "registry": registry,
        "schema_version": "1.0.0",
        "status": "PASS",
        "task_ids": ["T004", "T005", "T006", "T007", "T008", "T009", "T010"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-golden", action="store_true")
    parser.add_argument("--write-golden", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def source_revision(output: Path, check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(output.is_file(), "PROTOCOL_EVIDENCE_MISSING")
    try:
        document = json.loads(output.read_text(encoding="utf-8"))
        revision = document["source_tree"]["commit"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        reject("PROTOCOL_EVIDENCE_INVALID", str(exc))
    require(
        isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision),
        "PROTOCOL_SOURCE_INVALID",
    )
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0, "PROTOCOL_SOURCE_NOT_ANCESTOR")
    return revision


def main() -> int:
    args = parse_args()
    try:
        if args.emit_golden:
            print(canonical_json_bytes(golden_document(None)).decode("utf-8"))
            return 0
        if args.write_golden:
            encoded = canonical_json_bytes(golden_document(None)) + b"\n"
            path = ROOT / GOLDEN_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(encoded)
            print(encoded.decode("utf-8"), end="")
            return 0
        output = args.output.resolve()
        revision = source_revision(output, args.check_only)
        result = verify(revision)
        result["source_tree"] = {
            "commit": revision,
            "tree": git_text("rev-parse", f"{revision}^{{tree}}"),
        }
        encoded = canonical_json_bytes(result)
        if args.check_only:
            require(output.read_bytes() == encoded, "PROTOCOL_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (ContractError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
