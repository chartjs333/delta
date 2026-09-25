"""Inventory exact legacy body preimages; never certify a missing body projection."""

import hashlib
import json
from pathlib import Path

from derive_public_arithmetic_inputs import SOURCE, SOURCE_SHA256
from formal_artifacts import (
    canonical_json_bytes,
    load_json_strict,
    sha256_file,
    write_canonical_json,
)
from public_native_projection import PUBLIC, PUBLIC_SHA256, PinnedFixtureSources
from public_state_projection import ROOT, require

LABELS = {
    "ACT-ISC-VOTE": "normal-isc-body",
    "ACT-EC-VOTE": "normal-ec-body",
    "ACT-APC-VOTE": "normal-apc-body",
    "ACT-ROOT-VOTE": "normal-root-body",
}
KINDS = {
    "ACT-ISC-VOTE": "ISC_PROJECTION",
    "ACT-EC-VOTE": "EC_PROJECTION",
    "ACT-APC-VOTE": "APC_PROJECTION",
    "ACT-ROOT-VOTE": "AGGREGATE_PROJECTION",
}
TARGET = ROOT / "formal/proposals/evidence/public-durable-prefix/legacy-body-scope.json"


def sha_id(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def audit(public: Path = PUBLIC, native: Path = SOURCE):
    sources = PinnedFixtureSources(public, native)
    bundle = load_json_strict(native)
    artifacts = {key: json.loads(raw) for key, raw in bundle["artifacts"].items()}
    records = []
    for event in sources.trace["events"]:
        if not event["action_id"].endswith("-VOTE") or event["actor_id"] != "validator-1":
            continue
        action = event["action_id"]
        item = {
            "action": action,
            "sequence": event["durable_sequence"],
            "body_id": event["body_hash"],
            "parents": event["parent_hashes"],
            "context": event["vote_context_id"],
        }
        if action in LABELS:
            label = LABELS[action]
            require(sha_id(label.encode("ascii")) == event["body_hash"], "LABEL_PREIMAGE")
            candidates = [key for key, value in artifacts.items() if value["kind"] == KINDS[action]]
            require(candidates and event["body_hash"] not in candidates, "DIFFERENT_GRAPH_IDS")
            item.update(
                status="LABEL_PREIMAGE_ONLY_NOT_CANONICAL_CERTIFICATE_BODY",
                label_preimage_ascii=label,
                graph_projection_ids=candidates,
                graph_payload_fields={key: sorted(artifacts[key]["payload"]) for key in candidates},
                original_vote_parents_empty=event["parent_hashes"] == [],
            )
        elif action == "ACT-CONFIG-VOTE":
            config = sources.trace["round_contract"]["round_config"]
            payload = {key: value for key, value in config.items() if key != "body_hash"}
            require(sha_id(canonical_json_bytes(payload)) == event["body_hash"], "CONFIG_PREIMAGE")
            item.update(status="CANONICAL_ROUND_CONTRACT_PROJECTION_NOT_NATIVE_CONFIG_QC")
        else:
            witness = event["arithmetic_witness"]
            command = json.loads(witness["command_ascii"])
            from native_trace_witness import n

            require(
                n.digest(n.canonical(command["payload"])) == event["body_hash"],
                "ARITHMETIC_PREIMAGE",
            )
            item.update(status="CANONICAL_ARITHMETIC_BODY_REDERIVED_BY_PINNED_CHECKER")
        records.append(item)
    require(
        [item["sequence"] for item in records] == list(range(1, 9)), "FULL_EIGHT_SLOT_INVENTORY"
    )
    return {
        "status": "MIXED_PREFIX_BODY_PROVENANCE_INCOMPLETE",
        "full_prefix_bridge_pass": False,
        "native_execution": False,
        "native_export_authenticated": False,
        "legacy_refinement": sources.checked,
        "public_sha256": PUBLIC_SHA256,
        "native_sha256": SOURCE_SHA256,
        "records": records,
        "source_inputs": [
            {"path": path, "sha256": sha256_file(ROOT / path)}
            for path in [
                "formal/scripts/generate_trace_fixtures.py",
                "formal/scripts/native_trace_fixture.py",
                "delta-core-cpp/include/delta/certificates/contracts.hpp",
            ]
        ],
        "limits": [
            "A known label preimage supplies no canonical certificate fields or parent edges.",
            "Minimal arithmetic graph projections differ from native certificate contracts.",
            "Rehashing new bodies would change original envelopes, receipts and journal roots.",
            "A new version needs a checked field-level relation and independent provenance.",
            "The legacy fixture is preserved and cannot qualify the complete-prefix bridge.",
        ],
    }


if __name__ == "__main__":
    result = audit()
    write_canonical_json(TARGET, result)
    print(result["status"], len(result["records"]), "original per-actor slots")
