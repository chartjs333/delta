"""Reproduce original source preimages and explicitly unclosed 008 references."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formal_artifacts import write_canonical_json
from native_source_artifacts import (
    DOMAINS,
    VERSION,
    canonical,
    content_id,
    require,
    resolve_q_source,
)

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "formal/proposals/evidence/native-source-artifacts"
BOUNDARY_PIN = "4fab4e7c90c1a3a43af8217bbb67bc7b1d273526c0bf222e06247c0dbe8e4702"


def originals() -> dict[str, bytes]:
    raw = (EVIDENCE / "native-source-boundary.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == BOUNDARY_PIN, "BOUNDARY_SUBSTITUTED")
    boundary = json.loads(raw)
    result = {}
    for row in boundary["files"]:
        data = (EVIDENCE / row["copy"]).read_bytes()
        require(hashlib.sha256(data).hexdigest() == row["sha256"], "SOURCE_SUBSTITUTED")
        result[row["path"]] = data
    return result


def fixture_store() -> tuple[dict[str, bytes], dict, dict]:
    files = originals()
    golden = json.loads(files["delta-protocol/fixtures/004/cross-language/golden-v1.json"])
    schema = json.loads(files["delta-protocol/fixtures/local-round/parameter-schema-v1.json"])
    # The fixture file has a terminal LF; the published schema's preimage is its
    # canonical JSON, exactly as ParameterSchema.fingerprint specifies.
    raw_schema = canonical(schema)
    store = {content_id(raw_schema): raw_schema}
    for key, kind in [
        ("profile", "profile"),
        ("scale_table", "scale"),
        ("shard_plan", "plan"),
        ("fixedpoint_config", "config"),
        ("proof_instance", "proof"),
        ("manifest", "manifest"),
    ]:
        row = golden[key]
        raw = bytes.fromhex(row["bytes_hex"])
        require(raw == canonical(row["value"]), "ORIGINAL_VALUE_BYTES")
        require(content_id(raw, DOMAINS[kind]) == row["content_id"], "ORIGINAL_ID")
        require(row["content_id"] not in store, "ORIGINAL_DUPLICATE")
        store[row["content_id"]] = raw
    for row in golden["shards"]:
        raw = bytes.fromhex(row["envelope_hex"])
        require(content_id(raw, DOMAINS["leaf"]) == row["leaf_id"], "ORIGINAL_LEAF")
        require(row["leaf_id"] not in store, "ORIGINAL_DUPLICATE")
        store[row["leaf_id"]] = raw
    other = json.loads(files["delta-protocol/fixtures/008/cross-language/golden-v1.json"])
    return store, golden, other


def generate() -> dict:
    store, golden, other = fixture_store()
    source = resolve_q_source(store, golden["manifest"]["content_id"])
    values = [v for row in source.rows for v in row["values"]]
    require(values == golden["q_values"], "ORIGINAL_DECODED_Q_VALUES")
    original_bytes = [x["bytes_hex"] for x in source.sources]
    require(len(original_bytes) == 12, "ORIGINAL_SOURCE_CLOSURE")
    gaps = []
    first = other["parameter_shard_qcs"][0]["value"]
    for field in ("parameter_schema_id", "arithmetic_profile_id", "round_config_id"):
        identifier = first[field]
        require(identifier not in store, "UNEXPECTED_CROSS_FIXTURE_LINK")
        gaps.append({"kind": field, "id": identifier, "status": "MISSING_IN_RETAINED_SOURCE_STORE"})
    identifier = other["apply_arithmetic_profile"]["value"]["accumulator_proof_id"]
    require(identifier not in store, "UNEXPECTED_ACCUMULATOR_LINK")
    gaps.append(
        {
            "kind": "accumulator_proof_id",
            "id": identifier,
            "status": "MISSING_IN_RETAINED_SOURCE_STORE",
        }
    )
    for item in other["parameter_shard_qcs"]:
        body = item["value"]
        for i, identifier in enumerate(body["input_leaf_ids"]):
            label = f"{body['domain_id']}-{body['shard_id']}-leaf-{i}"
            require(
                content_id(label.encode()) == identifier and identifier not in store,
                "ORIGINAL_LEAF_LABEL_SCOPE_CHANGED",
            )
            gaps.append(
                {
                    "kind": "input_leaf_id",
                    "id": identifier,
                    "fixture_label": label,
                    "status": "LABEL_HASH_WITHOUT_DRQ1_PREIMAGE",
                }
            )
    return {
        "projection_version": VERSION,
        "status": "ORIGINAL_Q_SOURCE_PREIMAGES_CHECKED_PARTIAL_IDENTITY_BRIDGE",
        "formal_go": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
        "scope": "PINNED_ORIGINAL_FIXTURES_NOT_NATIVE_EXECUTION_OR_AUTHENTICATION",
        "native_reference_commit": "60c692f6e391f839829dfc64e93380db54cd507b",
        "boundary_sha256": BOUNDARY_PIN,
        "manifest_id": source.manifest_id,
        "original_sources": list(source.sources),
        "ordered_rows": list(source.rows),
        "coordinate_count": len(values),
        "proof_scope": "BYTES_AND_CONFIG_INPUT_LINKS_ONLY_NOT_THEOREM_OR_BOUND_VALIDATION",
        "unresolved_original004_anchors": {
            "base_round_config_id": golden["fixedpoint_config"]["value"]["base_round_config_id"],
            "parent_checkpoint_id": source.manifest["parent_checkpoint_id"],
        },
        "original008_unresolved": gaps,
        "cross_fixture_source_join": False,
        "draft_graph_schema_q_identity_join": False,
        "note": "Store absence is scoped to these retained fixtures, "
        "not proof of global nonexistence. "
        "Rehashing wrappers cannot authenticate new preimages or create a cross-format identity.",
    }


if __name__ == "__main__":
    result = generate()
    write_canonical_json(ROOT / "formal/proposals/native-source-artifact-vectors.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "sources": len(result["original_sources"]),
                "shards": len(result["ordered_rows"]),
                "coordinates": result["coordinate_count"],
                "unresolved_008": len(result["original008_unresolved"]),
            },
            sort_keys=True,
        )
    )
