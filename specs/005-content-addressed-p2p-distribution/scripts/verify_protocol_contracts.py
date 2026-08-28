"""Verify frozen feature-005 schemas, fixtures, identities and registry closure."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "005-content-addressed-p2p-distribution"
SCRIPT_DIR = FEATURE / "scripts"
SCHEMA_ROOT = ROOT / "delta-protocol" / "schemas" / "005"
FIXTURE_ROOT = ROOT / "delta-protocol" / "fixtures" / "005"
EVIDENCE = FEATURE / "evidence" / "protocol-contracts.json"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import distribution_contracts as contracts  # noqa: E402


class ContractError(RuntimeError):
    """Stable fail-closed contract error."""


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


def validate_manifest(
    manifest: dict[str, Any], payload: bytes, profile: dict[str, Any], policy: dict[str, Any]
) -> None:
    validate_identified(manifest, "deltareduce.005.object-manifest.v1", "MANIFEST_IDENTITY_INVALID")
    value = manifest["value"]
    profile_value = profile["value"]
    require(value["piece_profile_id"] == profile["content_id"], "MANIFEST_PROFILE_MISMATCH")
    require(value["certificate_policy_id"] == policy["content_id"], "MANIFEST_POLICY_MISMATCH")
    require(value["total_length"] == len(payload), "MANIFEST_LENGTH_MISMATCH")
    require(value["payload_sha256"] == contracts.sha256(payload), "MANIFEST_PAYLOAD_HASH_MISMATCH")
    pieces = value["pieces"]
    require(isinstance(pieces, list), "MANIFEST_PIECES_INVALID")
    if not payload:
        require(pieces == [], "EMPTY_OBJECT_HAS_PIECES")
    offset = 0
    target = int(profile_value["target_piece_bytes"])
    seen: set[int] = set()
    for ordinal, piece in enumerate(pieces):
        require(isinstance(piece, dict), "PIECE_INVALID")
        require(piece["ordinal"] == ordinal and ordinal not in seen, "PIECE_ORDINAL_INVALID")
        seen.add(ordinal)
        require(piece["offset"] == offset, "PIECE_COVERAGE_INVALID")
        length = int(piece["length"])
        require(length > 0 and length <= target, "PIECE_LENGTH_INVALID")
        if ordinal + 1 < len(pieces):
            require(length == target, "PIECE_NONFINAL_SHORT")
        current = payload[offset : offset + length]
        require(len(current) == length, "PIECE_TRUNCATED")
        require(piece["content_id"] == contracts.piece_id(current), "PIECE_HASH_MISMATCH")
        offset += length
    require(offset == len(payload), "PIECE_COVERAGE_INVALID")
    require(value["piece_tree_root"] == contracts.merkle_root(pieces), "PIECE_ROOT_MISMATCH")


def schema_registry() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
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
        require(
            schema.get("required") == sorted(properties), "SCHEMA_REQUIRED_SET_INVALID", path.name
        )
        identifier = schema.get("$id")
        require(
            isinstance(identifier, str) and identifier not in registry,
            "SCHEMA_ID_INVALID",
            path.name,
        )
        registry[identifier] = schema
    return registry


def validate_schema_value(
    schema: dict[str, Any], value: Any, registry: dict[str, dict[str, Any]], code: str
) -> None:
    reference = schema.get("$ref")
    if reference is not None:
        require(isinstance(reference, str) and reference in registry, "SCHEMA_REF_INVALID", code)
        validate_schema_value(registry[reference], value, registry, code)
        return
    expected_type = schema.get("type")
    if expected_type == "object":
        require(isinstance(value, dict), "SCHEMA_TYPE_INVALID", code)
        properties = schema.get("properties")
        if isinstance(properties, dict):
            required = schema.get("required", [])
            require(all(key in value for key in required), "SCHEMA_REQUIRED_MISSING", code)
            if schema.get("additionalProperties") is False:
                require(set(value) <= set(properties), "SCHEMA_ADDITIONAL_PROPERTY", code)
            for key, child in properties.items():
                if key in value:
                    require(isinstance(child, dict), "SCHEMA_CHILD_INVALID", f"{code}:{key}")
                    validate_schema_value(child, value[key], registry, f"{code}:{key}")
    elif expected_type == "array":
        require(isinstance(value, list), "SCHEMA_TYPE_INVALID", code)
        require(len(value) >= int(schema.get("minItems", 0)), "SCHEMA_MIN_ITEMS", code)
        if "maxItems" in schema:
            require(len(value) <= int(schema["maxItems"]), "SCHEMA_MAX_ITEMS", code)
        if schema.get("uniqueItems") is True:
            encoded = [contracts.canonical_json_bytes(item) for item in value]
            require(len(encoded) == len(set(encoded)), "SCHEMA_UNIQUE_ITEMS", code)
        child = schema.get("items")
        if isinstance(child, dict):
            for index, item in enumerate(value):
                validate_schema_value(child, item, registry, f"{code}:{index}")
    elif expected_type == "string":
        require(isinstance(value, str), "SCHEMA_TYPE_INVALID", code)
        require(len(value) >= int(schema.get("minLength", 0)), "SCHEMA_MIN_LENGTH", code)
        if "pattern" in schema:
            require(re.fullmatch(str(schema["pattern"]), value) is not None, "SCHEMA_PATTERN", code)
    elif expected_type == "integer":
        require(isinstance(value, int) and not isinstance(value, bool), "SCHEMA_TYPE_INVALID", code)
        if "minimum" in schema:
            require(value >= int(schema["minimum"]), "SCHEMA_MINIMUM", code)
        if "maximum" in schema:
            require(value <= int(schema["maximum"]), "SCHEMA_MAXIMUM", code)
    if "const" in schema:
        require(value == schema["const"], "SCHEMA_CONST", code)
    if "enum" in schema:
        require(value in schema["enum"], "SCHEMA_ENUM", code)


def validate_schemas(golden: dict[str, Any], registry: dict[str, dict[str, Any]]) -> None:
    instances = {
        "certification-policy-v1.json": golden["policy_registry"]["value"],
        "download-journal-v1.json": golden["verified_journal"],
        "object-manifest-v1.json": golden["manifest"]["value"],
        "peer-advertisement-v1.json": golden["peer_advertisement"],
        "piece-profile-v1.json": golden["piece_profile"]["value"],
        "transport-envelope-v1.json": golden["transport_envelope"],
    }
    for name, instance in instances.items():
        validate_schema_value(read_json(SCHEMA_ROOT / name), instance, registry, name)
    piece_schema = read_json(SCHEMA_ROOT / "piece-descriptor-v1.json")
    for index, piece in enumerate(golden["manifest"]["value"]["pieces"]):
        validate_schema_value(piece_schema, piece, registry, f"piece:{index}")


def verify_registry() -> dict[str, Any]:
    registry = read_json(SCHEMA_ROOT / "registry-v1.json")
    root = read_json(ROOT / "delta-protocol" / "registry.json")
    expected_schema_ids = set(contracts.SCHEMA_IDS.values())
    expected_fixture_ids = set(contracts.FIXTURE_IDS.values())
    require(
        {item["id"] for item in registry["artifacts"]} == expected_schema_ids,
        "SCHEMA_REGISTRY_SET_INVALID",
    )
    require(
        {item["id"] for item in registry["fixtures"]} == expected_fixture_ids,
        "FIXTURE_REGISTRY_SET_INVALID",
    )
    for collection, base in (
        (registry["artifacts"], ROOT / "delta-protocol"),
        (registry["fixtures"], ROOT / "delta-protocol"),
    ):
        for item in collection:
            path = base / item["path"]
            require(path.is_file(), "REGISTRY_ARTIFACT_MISSING", item["path"])
            require(
                hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"],
                "REGISTRY_HASH_DRIFT",
                item["path"],
            )
    root_schema_ids = {item["id"] for item in root["schemas"]}
    root_fixture_ids = {item["id"] for item in root["fixtures"]}
    require(expected_schema_ids <= root_schema_ids, "ROOT_SCHEMA_REGISTRY_INCOMPLETE")
    require(expected_fixture_ids <= root_fixture_ids, "ROOT_FIXTURE_REGISTRY_INCOMPLETE")
    extension = [
        item for item in root["extensions"] if item["id"] == "REGISTRY-DISTRIBUTION-005-V1"
    ]
    require(len(extension) == 1, "ROOT_EXTENSION_INVALID")
    require(
        extension[0]["sha256"]
        == hashlib.sha256((SCHEMA_ROOT / "registry-v1.json").read_bytes()).hexdigest(),
        "ROOT_EXTENSION_HASH_DRIFT",
    )
    return {"fixture_count": len(expected_fixture_ids), "schema_count": len(expected_schema_ids)}


def verify() -> dict[str, Any]:
    for relative, factory in sorted(contracts.FIXTURES.items()):
        expected = contracts.canonical_json_bytes(factory()) + b"\n"
        require((FIXTURE_ROOT / relative).read_bytes() == expected, "FIXTURE_DRIFT", relative)
    for relative, schema in sorted(contracts.schemas().items()):
        require(
            (SCHEMA_ROOT / relative).read_bytes() == contracts.pretty_bytes(schema),
            "SCHEMA_DRIFT",
            relative,
        )

    golden = read_json(FIXTURE_ROOT / "cross-language" / "golden-v1.json")
    profile = golden["piece_profile"]
    policies = golden["policy_registry"]
    validate_identified(profile, "deltareduce.005.piece-profile.v1", "PROFILE_INVALID")
    validate_identified(policies, "deltareduce.005.policy-registry.v1", "POLICY_REGISTRY_INVALID")
    aggregate_policy, apply_policy = policies["value"]["policies"]
    validate_identified(
        aggregate_policy, "deltareduce.005.certification-policy.v1", "AGGREGATE_POLICY_INVALID"
    )
    validate_identified(
        apply_policy, "deltareduce.005.certification-policy.v1", "APPLY_POLICY_INVALID"
    )
    require(aggregate_policy["value"]["active"] is True, "AGGREGATE_POLICY_INACTIVE")
    require(
        aggregate_policy["value"]["can_make_current"] is False, "AGGREGATE_POLICY_CURRENT_INVALID"
    )
    require(apply_policy["value"]["active"] is False, "APPLY_POLICY_ACTIVE_TOO_EARLY")
    require(
        apply_policy["value"]["future_feature"] == "008-certificates-and-consensus",
        "APPLY_POLICY_OWNER_INVALID",
    )
    forbidden = set(policies["value"]["forbidden_media_types"])
    allowed = {
        media
        for item in policies["value"]["policies"]
        for media in item["value"]["allowed_media_types"]
    }
    require(not forbidden & allowed, "POLICY_ALLOW_DENY_OVERLAP")

    payload = contracts.source_bytes(int(golden["source"]["length"]))
    validate_manifest(golden["manifest"], payload, profile, aggregate_policy)
    validate_manifest(golden["empty_object"], b"", profile, aggregate_policy)
    validate_identified(
        golden["certificate"], "deltareduce.005.aggregate-certificate.v1", "CERTIFICATE_INVALID"
    )
    require(
        golden["certificate"]["value"]["certificate_root"] == contracts.CERTIFICATE_ROOT,
        "CERTIFICATE_ROOT_DRIFT",
    )
    require(
        golden["certificate"]["value"]["source_state_root"] == contracts.SOURCE_STATE_ROOT,
        "CERTIFICATE_STATE_DRIFT",
    )
    validate_schemas(golden, schema_registry())

    negative = read_json(FIXTURE_ROOT / "invalid" / "distribution-negative-v1.json")
    expected_codes = {
        "CERTIFICATE_ROOT_MISMATCH",
        "CURRENT_REQUIRES_APPLY_QC",
        "MANIFEST_TOO_LARGE",
        "MEDIA_FORBIDDEN",
        "PATH_TRAVERSAL",
        "PIECE_COUNT_LIMIT",
        "PIECE_DUPLICATE_ORDINAL",
        "PIECE_RANGE_GAP",
        "PIECE_RANGE_OVERLAP",
        "PIECE_UNAVAILABLE",
        "POLICY_INACTIVE",
        "POLICY_UNKNOWN",
        "SOURCE_STATE_ROOT_MISMATCH",
        "SYMLINK_REJECTED",
        "TRANSPORT_HEADER_TOO_LARGE",
        "TRANSPORT_PAYLOAD_TOO_LARGE",
        "TRANSPORT_TRUNCATED",
    }
    require(
        {item["expected_code"] for item in negative["cases"]} == expected_codes,
        "NEGATIVE_CODE_SET_INVALID",
    )
    registry_result = verify_registry()
    return {
        "checks": [
            "CANONICAL_OBJECT_AND_POLICY_IDS",
            "EXACT_PIECE_COVERAGE_AND_MERKLE_ROOT",
            "EMPTY_AND_SHORT_FINAL_PIECE_RULES",
            "IMMUTABLE_ACTIVE_AGGREGATE_POLICY",
            "INACTIVE_FUTURE_APPLY_POLICY",
            "FORBIDDEN_MEDIA_DENYLIST",
            "BOUNDED_SCHEMAS_AND_NEGATIVE_CORPUS",
            "ROOT_REGISTRY_CLOSURE",
        ],
        "formal_semantics_id": contracts.FORMAL_ID,
        "identities": {
            "aggregate_policy_id": aggregate_policy["content_id"],
            "empty_object_id": golden["empty_object"]["content_id"],
            "object_id": golden["manifest"]["content_id"],
            "piece_profile_id": profile["content_id"],
            "policy_registry_id": policies["content_id"],
        },
        "registry": registry_result,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "task_ids": [f"T{index:03d}" for index in range(5, 11)],
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


def evidence_document(source_commit: str) -> dict[str, Any]:
    commit = git_text("rev-parse", source_commit)
    paths = [
        "delta-protocol/registry.json",
        *[
            f"delta-protocol/schemas/005/{name}"
            for name in sorted([*contracts.SCHEMA_IDS, "registry-v1.json"])
        ],
        *[f"delta-protocol/fixtures/005/{name}" for name in sorted(contracts.FIXTURE_IDS)],
        "specs/005-content-addressed-p2p-distribution/scripts/distribution_contracts.py",
        "specs/005-content-addressed-p2p-distribution/scripts/verify_protocol_contracts.py",
        "specs/005-content-addressed-p2p-distribution/tests/test_verify_protocol_contracts.py",
    ]
    result = verify()
    result["artifacts"] = [
        {
            "path": path,
            "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest(),
        }
        for path in paths
    ]
    result["source"] = {
        "commit": commit,
        "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--write-evidence", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write_evidence:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            require(
                git_text("rev-parse", "HEAD") == git_text("rev-parse", arguments.source_commit),
                "SOURCE_NOT_HEAD",
            )
            require(
                not git_text("status", "--porcelain", "--untracked-files=all"),
                "SOURCE_TREE_NOT_CLEAN",
            )
            result = evidence_document(arguments.source_commit)
            EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
            EVIDENCE.write_bytes(contracts.canonical_json_bytes(result) + b"\n")
        elif arguments.check_only:
            require(EVIDENCE.is_file(), "CONTRACT_EVIDENCE_MISSING")
            document = read_json(EVIDENCE)
            source = document.get("source")
            require(isinstance(source, dict), "CONTRACT_EVIDENCE_SOURCE_INVALID")
            result = evidence_document(str(source.get("commit")))
            require(document == result, "CONTRACT_EVIDENCE_DRIFT")
            require(
                EVIDENCE.read_bytes() == contracts.canonical_json_bytes(document) + b"\n",
                "CONTRACT_EVIDENCE_NOT_CANONICAL",
            )
        else:
            result = verify()
    except (ContractError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"error": str(exc), "phase": "005-contracts", "status": "FAIL"}, sort_keys=True
            )
        )
        return 2
    print(contracts.canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
