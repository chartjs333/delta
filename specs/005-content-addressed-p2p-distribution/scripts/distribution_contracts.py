"""Generate the frozen feature-005 schemas, fixtures and registry entries."""

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
SCHEMA_ROOT = ROOT / "delta-protocol" / "schemas" / "005"
FIXTURE_ROOT = ROOT / "delta-protocol" / "fixtures" / "005"
FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SOURCE_STATE_ROOT = "sha256:c6fcf9131d0a481aee2918bf894dbebc62442dcb26be3c559630841f4d26f967"
CERTIFICATE_ROOT = "sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d"
PROJECT_ID = "deltareduce-pilot-v1"
AGGREGATE_MEDIA = "application/vnd.deltareduce.aggregate-bundle;version=1"
CHECKPOINT_MEDIA = "application/vnd.deltareduce.checkpoint;version=1"
HASH_PATTERN = r"^sha256:[0-9a-f]{64}$"

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def domain_hash(domain: str, value: bytes) -> str:
    return sha256(domain.encode("ascii") + b"\0" + value)


def identified(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    encoded = canonical_json_bytes(value)
    return {"bytes_hex": encoded.hex(), "content_id": domain_hash(domain, encoded), "value": value}


def source_bytes(length: int) -> bytes:
    return bytes(index % 251 for index in range(length))


def piece_id(payload: bytes) -> str:
    return domain_hash("deltareduce.005.piece.v1", payload)


def piece_leaf(ordinal: int, content_id: str) -> str:
    digest = bytes.fromhex(content_id.removeprefix("sha256:"))
    return domain_hash("deltareduce.005.piece-leaf.v1", ordinal.to_bytes(8, "big") + digest)


def merkle_root(pieces: list[dict[str, Any]]) -> str:
    if not pieces:
        return domain_hash("deltareduce.005.piece-empty.v1", b"")
    level = [piece_leaf(int(item["ordinal"]), str(item["content_id"])) for item in pieces]
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                next_level.append(level[index])
                continue
            left = bytes.fromhex(level[index].removeprefix("sha256:"))
            right = bytes.fromhex(level[index + 1].removeprefix("sha256:"))
            next_level.append(domain_hash("deltareduce.005.piece-node.v1", left + right))
        level = next_level
    return level[0]


def piece_profile_value() -> dict[str, Any]:
    return {
        "formal_semantics_id": FORMAL_ID,
        "hash_algorithm": "SHA-256",
        "leaf_domain": "deltareduce.005.piece-leaf.v1",
        "limits": {
            "max_manifest_bytes": 1048576,
            "max_object_bytes": 8589934592,
            "max_parallel_streams": 8,
            "max_piece_bytes": 1048576,
            "max_piece_count": 8192,
            "max_transport_header_bytes": 65536,
            "max_transport_payload_bytes": 1048576,
        },
        "node_domain": "deltareduce.005.piece-node.v1",
        "object_domain": "deltareduce.005.object-manifest.v1",
        "odd_leaf_rule": "PROMOTE_ODD_UNCHANGED",
        "piece_content_domain": "deltareduce.005.piece.v1",
        "profile_name": "piece-1m-sha256-v1",
        "schema_version": "1.0.0",
        "target_piece_bytes": 1048576,
        "type_name": "PIECE_PROFILE",
        "zero_length_rule": "ZERO_PIECES_DOMAIN_SEPARATED_EMPTY_ROOT",
    }


def policy_registry_value() -> dict[str, Any]:
    forbidden = [
        "application/vnd.deltareduce.ac-fragment;version=1",
        "application/vnd.deltareduce.commitment;version=1",
        "application/vnd.deltareduce.input-candidate;version=1",
        "application/vnd.deltareduce.parameter-partial;version=1",
        "application/vnd.deltareduce.regional-partial;version=1",
        "application/vnd.deltareduce.worker-q-shard;version=1",
    ]
    aggregate = identified(
        "deltareduce.005.certification-policy.v1",
        {
            "active": True,
            "allowed_media_types": [AGGREGATE_MEDIA],
            "can_make_current": False,
            "formal_action_id": "ACT-PUBLISH",
            "minimum_strength": 10,
            "policy_name": "aggregated-transition-qc-v1",
            "required_source_state": "AGGREGATED",
            "schema_version": "1.0.0",
            "type_name": "CERTIFICATION_POLICY",
        },
    )
    future_apply = identified(
        "deltareduce.005.certification-policy.v1",
        {
            "active": False,
            "allowed_media_types": [CHECKPOINT_MEDIA],
            "can_make_current": True,
            "formal_action_id": "ACT-APPLY-CURRENT",
            "future_feature": "008-certificates-and-consensus",
            "minimum_strength": 20,
            "policy_name": "apply-qc-v1",
            "required_source_state": "APPLIED",
            "schema_version": "1.0.0",
            "type_name": "CERTIFICATION_POLICY",
        },
    )
    return {
        "formal_semantics_id": FORMAL_ID,
        "forbidden_media_types": forbidden,
        "policies": [aggregate, future_apply],
        "registry_name": "distribution-certification-policies-v1",
        "schema_version": "1.0.0",
        "type_name": "CERTIFICATION_POLICY_REGISTRY",
        "unknown_policy_action": "REJECT",
        "weaker_policy_action": "REJECT",
    }


def components() -> dict[str, Any]:
    profile = identified("deltareduce.005.piece-profile.v1", piece_profile_value())
    policies = identified("deltareduce.005.policy-registry.v1", policy_registry_value())
    aggregate_policy = policies["value"]["policies"][0]
    apply_policy = policies["value"]["policies"][1]
    return {
        "aggregate_policy": aggregate_policy,
        "apply_policy": apply_policy,
        "piece_profile": profile,
        "policy_registry": policies,
    }


def certificate_fixture() -> dict[str, Any]:
    value = {
        "certificate_root": CERTIFICATE_ROOT,
        "formal_semantics_id": FORMAL_ID,
        "source_state": "AGGREGATED",
        "source_state_root": SOURCE_STATE_ROOT,
        "state_height": 4,
        "transition_id": "sha256:" + "a" * 64,
        "type_name": "AGGREGATED_TRANSITION_CERTIFICATE",
        "validator_epoch": 1,
    }
    return identified("deltareduce.005.aggregate-certificate.v1", value)


def build_manifest(payload: bytes) -> dict[str, Any]:
    frozen = components()
    profile = frozen["piece_profile"]
    registry = frozen["policy_registry"]
    policy = frozen["aggregate_policy"]
    size = int(profile["value"]["target_piece_bytes"])
    pieces: list[dict[str, Any]] = []
    for ordinal, offset in enumerate(range(0, len(payload), size)):
        current = payload[offset : offset + size]
        pieces.append(
            {
                "content_id": piece_id(current),
                "length": len(current),
                "offset": offset,
                "ordinal": ordinal,
            }
        )
    value = {
        "certificate_policy_id": policy["content_id"],
        "certificate_root": CERTIFICATE_ROOT,
        "formal_semantics_id": FORMAL_ID,
        "media_type": AGGREGATE_MEDIA,
        "payload_sha256": sha256(payload),
        "piece_profile_id": profile["content_id"],
        "piece_tree_root": merkle_root(pieces),
        "pieces": pieces,
        "policy_registry_id": registry["content_id"],
        "project_id": PROJECT_ID,
        "schema_version": "1.0.0",
        "source_state": "AGGREGATED",
        "source_state_root": SOURCE_STATE_ROOT,
        "total_length": len(payload),
        "type_name": "OBJECT_MANIFEST",
    }
    return identified("deltareduce.005.object-manifest.v1", value)


def golden_fixture() -> dict[str, Any]:
    length = 2 * 1048576 + 17
    payload = source_bytes(length)
    manifest = build_manifest(payload)
    frozen = components()
    advertisement = {
        "available_ordinals": [0, 1, 2],
        "endpoint": "loopback://peer-a",
        "lease_epoch": 3,
        "lease_expires_at_tick": 200,
        "manifest_id": manifest["content_id"],
        "max_streams": 2,
        "peer_id": "peer-a",
        "project_id": PROJECT_ID,
        "request_id": "advertise-001",
        "schema_version": "1.0.0",
        "type_name": "PEER_ADVERTISEMENT",
    }
    journal = {
        "attempts": [{"attempt": 1, "ordinal": 2, "peer_id": "peer-b", "result": "CORRUPT"}],
        "manifest_id": manifest["content_id"],
        "request_id": "fetch-001",
        "schema_version": "1.0.0",
        "type_name": "DOWNLOAD_JOURNAL",
        "verified_pieces": [
            {"content_id": item["content_id"], "ordinal": item["ordinal"]}
            for item in manifest["value"]["pieces"][:2]
        ],
    }
    transport = {
        "declared_payload_bytes": 17,
        "frame_type": "PIECE",
        "manifest_id": manifest["content_id"],
        "ordinal": 2,
        "project_id": PROJECT_ID,
        "request_id": "fetch-001-piece-2",
        "schema_version": "1.0.0",
        "type_name": "TRANSPORT_ENVELOPE",
    }
    return {
        "certificate": certificate_fixture(),
        "empty_object": build_manifest(b""),
        "expected": {"native_policy_code": "OK", "status": "ACCEPT"},
        "formal_semantics_id": FORMAL_ID,
        "manifest": manifest,
        "peer_advertisement": advertisement,
        "piece_profile": frozen["piece_profile"],
        "policy_registry": frozen["policy_registry"],
        "schema_version": "1.0.0",
        "source": {"length": length, "pattern": "COUNTER_MOD_251"},
        "transport_envelope": transport,
        "type_name": "DISTRIBUTION_CROSS_LANGUAGE_GOLDEN",
        "verified_journal": journal,
    }


def valid_fixture() -> dict[str, Any]:
    golden = golden_fixture()
    return {
        "certificate": golden["certificate"],
        "empty_object": golden["empty_object"],
        "manifest": golden["manifest"],
        "piece_profile": golden["piece_profile"],
        "policy_registry": golden["policy_registry"],
        "schema_version": "1.0.0",
        "type_name": "DISTRIBUTION_VALID_CONTRACTS",
    }


def invalid_fixture() -> dict[str, Any]:
    return {
        "cases": [
            {
                "expected_code": "POLICY_UNKNOWN",
                "id": "unknown-policy",
                "replacement": "sha256:" + "0" * 64,
            },
            {
                "expected_code": "POLICY_INACTIVE",
                "id": "future-apply-inactive",
                "policy_name": "apply-qc-v1",
            },
            {
                "expected_code": "CURRENT_REQUIRES_APPLY_QC",
                "id": "aggregate-as-current",
                "media_type": CHECKPOINT_MEDIA,
            },
            {
                "expected_code": "CERTIFICATE_ROOT_MISMATCH",
                "id": "wrong-certificate-root",
                "replacement": "sha256:" + "1" * 64,
            },
            {
                "expected_code": "SOURCE_STATE_ROOT_MISMATCH",
                "id": "wrong-source-state",
                "replacement": "sha256:" + "2" * 64,
            },
            {
                "expected_code": "MEDIA_FORBIDDEN",
                "id": "worker-q-shard",
                "media_type": "application/vnd.deltareduce.worker-q-shard;version=1",
            },
            {
                "expected_code": "MEDIA_FORBIDDEN",
                "id": "commitment",
                "media_type": "application/vnd.deltareduce.commitment;version=1",
            },
            {
                "expected_code": "MEDIA_FORBIDDEN",
                "id": "ac-fragment",
                "media_type": "application/vnd.deltareduce.ac-fragment;version=1",
            },
            {
                "expected_code": "MEDIA_FORBIDDEN",
                "id": "regional-partial",
                "media_type": "application/vnd.deltareduce.regional-partial;version=1",
            },
            {
                "expected_code": "MEDIA_FORBIDDEN",
                "id": "parameter-partial",
                "media_type": "application/vnd.deltareduce.parameter-partial;version=1",
            },
            {"expected_code": "PIECE_DUPLICATE_ORDINAL", "id": "duplicate-ordinal"},
            {"expected_code": "PIECE_RANGE_OVERLAP", "id": "piece-overlap"},
            {"expected_code": "PIECE_RANGE_GAP", "id": "piece-gap"},
            {"expected_code": "PIECE_COUNT_LIMIT", "id": "too-many-pieces", "declared": 8193},
            {
                "expected_code": "MANIFEST_TOO_LARGE",
                "id": "oversized-manifest",
                "declared": 1048577,
            },
            {
                "expected_code": "TRANSPORT_HEADER_TOO_LARGE",
                "id": "oversized-header",
                "declared": 65537,
            },
            {
                "expected_code": "TRANSPORT_PAYLOAD_TOO_LARGE",
                "id": "endless-stream",
                "declared": 1048577,
            },
            {"expected_code": "TRANSPORT_TRUNCATED", "id": "truncated-frame"},
            {"expected_code": "PATH_TRAVERSAL", "id": "dot-dot-path", "path": "../object"},
            {"expected_code": "SYMLINK_REJECTED", "id": "symlink-target"},
            {
                "expected_code": "PIECE_UNAVAILABLE",
                "id": "incomplete-peer-union",
                "missing_ordinal": 2,
            },
        ],
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "type_name": "DISTRIBUTION_NEGATIVE_CONTRACTS",
    }


def object_schema() -> dict[str, Any]:
    piece = {"$ref": "urn:deltareduce:schema:piece-descriptor:1"}
    properties = {
        "certificate_policy_id": {"pattern": HASH_PATTERN, "type": "string"},
        "certificate_root": {"pattern": HASH_PATTERN, "type": "string"},
        "formal_semantics_id": {"const": FORMAL_ID},
        "media_type": {"minLength": 1, "type": "string"},
        "payload_sha256": {"pattern": HASH_PATTERN, "type": "string"},
        "piece_profile_id": {"pattern": HASH_PATTERN, "type": "string"},
        "piece_tree_root": {"pattern": HASH_PATTERN, "type": "string"},
        "pieces": {"items": piece, "maxItems": 8192, "type": "array"},
        "policy_registry_id": {"pattern": HASH_PATTERN, "type": "string"},
        "project_id": {"minLength": 1, "type": "string"},
        "schema_version": {"const": "1.0.0"},
        "source_state": {"enum": ["AGGREGATED", "APPLIED"]},
        "source_state_root": {"pattern": HASH_PATTERN, "type": "string"},
        "total_length": {"maximum": 8589934592, "minimum": 0, "type": "integer"},
        "type_name": {"const": "OBJECT_MANIFEST"},
    }
    return strict_schema("object-manifest", "DeltaReduce object manifest v1", properties)


def strict_schema(name: str, title: str, properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$id": f"urn:deltareduce:schema:{name}:1",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": sorted(properties),
        "title": title,
        "type": "object",
    }


def schemas() -> dict[str, dict[str, Any]]:
    return {
        "certification-policy-v1.json": strict_schema(
            "certification-policy",
            "DeltaReduce certification policy registry v1",
            {
                "formal_semantics_id": {"const": FORMAL_ID},
                "forbidden_media_types": {
                    "items": {"type": "string"},
                    "minItems": 1,
                    "type": "array",
                    "uniqueItems": True,
                },
                "policies": {"items": {"type": "object"}, "minItems": 2, "type": "array"},
                "registry_name": {"const": "distribution-certification-policies-v1"},
                "schema_version": {"const": "1.0.0"},
                "type_name": {"const": "CERTIFICATION_POLICY_REGISTRY"},
                "unknown_policy_action": {"const": "REJECT"},
                "weaker_policy_action": {"const": "REJECT"},
            },
        ),
        "download-journal-v1.json": strict_schema(
            "download-journal",
            "DeltaReduce download journal v1",
            {
                "attempts": {"items": {"type": "object"}, "type": "array"},
                "manifest_id": {"pattern": HASH_PATTERN, "type": "string"},
                "request_id": {"minLength": 1, "type": "string"},
                "schema_version": {"const": "1.0.0"},
                "type_name": {"const": "DOWNLOAD_JOURNAL"},
                "verified_pieces": {"items": {"type": "object"}, "maxItems": 8192, "type": "array"},
            },
        ),
        "object-manifest-v1.json": object_schema(),
        "peer-advertisement-v1.json": strict_schema(
            "peer-advertisement",
            "DeltaReduce peer advertisement v1",
            {
                "available_ordinals": {
                    "items": {"minimum": 0, "type": "integer"},
                    "maxItems": 8192,
                    "type": "array",
                    "uniqueItems": True,
                },
                "endpoint": {"minLength": 1, "type": "string"},
                "lease_epoch": {"minimum": 0, "type": "integer"},
                "lease_expires_at_tick": {"minimum": 0, "type": "integer"},
                "manifest_id": {"pattern": HASH_PATTERN, "type": "string"},
                "max_streams": {"maximum": 8, "minimum": 1, "type": "integer"},
                "peer_id": {"minLength": 1, "type": "string"},
                "project_id": {"minLength": 1, "type": "string"},
                "request_id": {"minLength": 1, "type": "string"},
                "schema_version": {"const": "1.0.0"},
                "type_name": {"const": "PEER_ADVERTISEMENT"},
            },
        ),
        "piece-descriptor-v1.json": strict_schema(
            "piece-descriptor",
            "DeltaReduce piece descriptor v1",
            {
                "content_id": {"pattern": HASH_PATTERN, "type": "string"},
                "length": {"maximum": 1048576, "minimum": 1, "type": "integer"},
                "offset": {"maximum": 8589934592, "minimum": 0, "type": "integer"},
                "ordinal": {"maximum": 8191, "minimum": 0, "type": "integer"},
            },
        ),
        "piece-profile-v1.json": strict_schema(
            "piece-profile",
            "DeltaReduce piece profile v1",
            {
                "formal_semantics_id": {"const": FORMAL_ID},
                "hash_algorithm": {"const": "SHA-256"},
                "leaf_domain": {"const": "deltareduce.005.piece-leaf.v1"},
                "limits": {"type": "object"},
                "node_domain": {"const": "deltareduce.005.piece-node.v1"},
                "object_domain": {"const": "deltareduce.005.object-manifest.v1"},
                "odd_leaf_rule": {"const": "PROMOTE_ODD_UNCHANGED"},
                "piece_content_domain": {"const": "deltareduce.005.piece.v1"},
                "profile_name": {"const": "piece-1m-sha256-v1"},
                "schema_version": {"const": "1.0.0"},
                "target_piece_bytes": {"const": 1048576},
                "type_name": {"const": "PIECE_PROFILE"},
                "zero_length_rule": {"const": "ZERO_PIECES_DOMAIN_SEPARATED_EMPTY_ROOT"},
            },
        ),
        "transport-envelope-v1.json": strict_schema(
            "transport-envelope",
            "DeltaReduce bounded transport envelope v1",
            {
                "declared_payload_bytes": {"maximum": 1048576, "minimum": 0, "type": "integer"},
                "frame_type": {"enum": ["MANIFEST", "AVAILABILITY", "PIECE", "CANCEL"]},
                "manifest_id": {"pattern": HASH_PATTERN, "type": "string"},
                "ordinal": {"maximum": 8191, "minimum": 0, "type": "integer"},
                "project_id": {"minLength": 1, "type": "string"},
                "request_id": {"minLength": 1, "type": "string"},
                "schema_version": {"const": "1.0.0"},
                "type_name": {"const": "TRANSPORT_ENVELOPE"},
            },
        ),
    }


FIXTURES: dict[str, Callable[[], dict[str, Any]]] = {
    "cross-language/golden-v1.json": golden_fixture,
    "invalid/distribution-negative-v1.json": invalid_fixture,
    "valid/distribution-contract-v1.json": valid_fixture,
}


SCHEMA_IDS = {
    "certification-policy-v1.json": "SCHEMA-CERTIFICATION-POLICY-V1",
    "download-journal-v1.json": "SCHEMA-DOWNLOAD-JOURNAL-V1",
    "object-manifest-v1.json": "SCHEMA-OBJECT-MANIFEST-V1",
    "peer-advertisement-v1.json": "SCHEMA-PEER-ADVERTISEMENT-V1",
    "piece-descriptor-v1.json": "SCHEMA-PIECE-DESCRIPTOR-V1",
    "piece-profile-v1.json": "SCHEMA-PIECE-PROFILE-V1",
    "transport-envelope-v1.json": "SCHEMA-TRANSPORT-ENVELOPE-V1",
}


FIXTURE_IDS = {
    "cross-language/golden-v1.json": "DISTRIBUTION005-CROSS-LANGUAGE-GOLDEN-V1",
    "golden-hashes-v1.json": "DISTRIBUTION005-GOLDEN-HASHES-V1",
    "invalid/distribution-negative-v1.json": "DISTRIBUTION005-NEGATIVE-V1",
    "valid/distribution-contract-v1.json": "DISTRIBUTION005-VALID-CONTRACT-V1",
}


MEDIA_TYPES = [
    {
        "id": "MEDIA-CERTIFICATION-POLICY-V1",
        "schema_id": "SCHEMA-CERTIFICATION-POLICY-V1",
        "value": "application/vnd.deltareduce.certification-policy+json;version=1",
    },
    {
        "id": "MEDIA-DOWNLOAD-JOURNAL-V1",
        "schema_id": "SCHEMA-DOWNLOAD-JOURNAL-V1",
        "value": "application/vnd.deltareduce.download-journal+json;version=1",
    },
    {
        "id": "MEDIA-OBJECT-MANIFEST-V1",
        "schema_id": "SCHEMA-OBJECT-MANIFEST-V1",
        "value": "application/vnd.deltareduce.object-manifest+json;version=1",
    },
    {
        "id": "MEDIA-PEER-ADVERTISEMENT-V1",
        "schema_id": "SCHEMA-PEER-ADVERTISEMENT-V1",
        "value": "application/vnd.deltareduce.peer-advertisement+json;version=1",
    },
    {
        "id": "MEDIA-PIECE-PROFILE-V1",
        "schema_id": "SCHEMA-PIECE-PROFILE-V1",
        "value": "application/vnd.deltareduce.piece-profile+json;version=1",
    },
    {
        "id": "MEDIA-TRANSPORT-ENVELOPE-V1",
        "schema_id": "SCHEMA-TRANSPORT-ENVELOPE-V1",
        "value": "application/vnd.deltareduce.transport-envelope+json;version=1",
    },
]


def pretty_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def file_record(identifier: str, relative: str, path: Path) -> dict[str, str]:
    return {
        "id": identifier,
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def write_registries() -> None:
    fixture_records = [
        file_record(identifier, f"fixtures/005/{relative}", FIXTURE_ROOT / relative)
        for relative, identifier in sorted(FIXTURE_IDS.items())
    ]
    schema_records = [
        file_record(identifier, f"schemas/005/{relative}", SCHEMA_ROOT / relative)
        for relative, identifier in sorted(SCHEMA_IDS.items())
    ]
    registry = {
        "artifacts": schema_records,
        "fixtures": fixture_records,
        "formal_semantics_id": FORMAL_ID,
        "media_types": MEDIA_TYPES,
        "policy_registry_id": components()["policy_registry"]["content_id"],
        "registry_version": "005.1.0",
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
    root = json.loads(baseline.decode("utf-8"))
    root["schemas"] = sorted(
        [item for item in root["schemas"] if not str(item["path"]).startswith("schemas/005/")]
        + schema_records,
        key=lambda item: str(item["path"]),
    )
    root["fixtures"] = sorted(
        [item for item in root["fixtures"] if not str(item["path"]).startswith("fixtures/005/")]
        + fixture_records,
        key=lambda item: str(item["path"]),
    )
    root["extensions"] = [
        item for item in root["extensions"] if item["id"] != "REGISTRY-DISTRIBUTION-005-V1"
    ] + [
        file_record(
            "REGISTRY-DISTRIBUTION-005-V1",
            "schemas/005/registry-v1.json",
            registry_path,
        )
    ]
    new_media_ids = {entry["id"] for entry in MEDIA_TYPES}
    root["media_types"] = [
        item for item in root["media_types"] if item["id"] not in new_media_ids
    ] + MEDIA_TYPES
    root_path.write_bytes(pretty_bytes(root))


def write_all() -> None:
    SCHEMA_ROOT.mkdir(parents=True, exist_ok=True)
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    for relative, value in sorted(schemas().items()):
        (SCHEMA_ROOT / relative).write_bytes(pretty_bytes(value))
    for relative, factory in sorted(FIXTURES.items()):
        destination = FIXTURE_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
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
        "type_name": "DISTRIBUTION_GOLDEN_HASH_MANIFEST",
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
        print(canonical_json_bytes(FIXTURES[arguments.print]()).decode("utf-8"))
        return 0
    parser.error("one of --write-all or --print is required")


if __name__ == "__main__":
    raise SystemExit(main())
