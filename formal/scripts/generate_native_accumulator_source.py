"""Retain recomputed original accumulator fields and the missing008 source edge."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import fixture_store
from native_accumulator_source import (
    VERSION,
    check_request_headroom,
    resolve_apply_accumulator,
    resolve_bound_q_source,
)
from native_source_artifacts import SourceError, require

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "formal/proposals/evidence/native-accumulator-source"
BOUNDARY_PIN = "cc7242f49e0548e368d2b566b8f94adc0b1bc5b125fc1a38b4890d7904f52c87"


def originals() -> dict[str, bytes]:
    raw = (EVIDENCE / "native-source-boundary.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == BOUNDARY_PIN, "BOUNDARY_SUBSTITUTED")
    result = {}
    for row in json.loads(raw)["files"]:
        data = (ROOT / row["retained_path"]).read_bytes()
        require(hashlib.sha256(data).hexdigest() == row["sha256"], "SOURCE_SUBSTITUTED")
        result[row["path"]] = data
    return result


def generate() -> dict:
    originals()
    store, golden, other = fixture_store()
    checked = resolve_bound_q_source(store, golden["manifest"]["content_id"])
    p = checked.accumulator
    check_request_headroom(p, 0)  # original pinned native test's explicit request
    row = other["apply_arithmetic_profile"]
    store[row["content_id"]] = bytes.fromhex(row["bytes_hex"])
    try:
        resolve_apply_accumulator(store, row["content_id"])
    except SourceError as exc:
        gap = str(exc)
    else:
        raise AssertionError("Original008 unexpectedly acquired an accumulator preimage")
    require(
        gap == "MISSING_PREIMAGE:" + row["value"]["accumulator_proof_id"], "EXPECTED_SOURCE_GAP"
    )
    return {
        "projection_version": VERSION,
        "status": "ORIGINAL_ACCUMULATOR_RECOMPUTED_Q_SOURCE_COMPOSED",
        "scope": "PINNED_ORIGINAL_FIXTURES_NOT_NATIVE_EXECUTION_OR_AUTHENTICATION",
        "native_reference_commit": "60c692f6e391f839829dfc64e93380db54cd507b",
        "boundary_sha256": BOUNDARY_PIN,
        "formal_go": False,
        "gate_eligible": False,
        "native_export_authenticated": False,
        "manifest_id": checked.q.manifest_id,
        "accumulator": {**asdict(p), "sources": list(p.sources)},
        "ordered_q_source_rows": list(checked.q.rows),
        "q_source_objects": [s["id"] for s in checked.q.sources],
        "headroom_scope": "UNIQUE_ADMISSIBLE_REQUEST_VALUE_NOT_SERIALIZED_NATIVE_OBSERVATION",
        "original_native_test_headroom": 0,
        "metadata_scope": "HISTORICAL_SOURCE_ID_AND_NAME_MATCH_NOT_PROOF_OR_CURRENT_GO",
        "denominator_scope": "EXACT_POSITIVE_PROOF_VALUE_NOT_BOUND_TO_CERTIFIED_TICKET_WEIGHTS",
        "original008_profile_id": row["content_id"],
        "original008_profile_bytes_hex": row["bytes_hex"],
        "original008_accumulator_id": row["value"]["accumulator_proof_id"],
        "original008_join_failure": gap,
        "apply_quantum_source": "ABSENT_FROM_ORIGINAL008_PROFILE",
        "rounding_stages": {
            "worker_quantization": "ROUND_TO_NEAREST_TIES_TO_EVEN",
            "reduce_conversion_and_apply": "HALF_TOWARD_POSITIVE",
        },
        "original_draft_graph_identity_join": False,
        "full_native_public_refinement": False,
    }


if __name__ == "__main__":
    result = generate()
    write_canonical_json(ROOT / "formal/proposals/native-accumulator-source-vectors.json", result)
    print(json.dumps({k: result[k] for k in ("status", "manifest_id", "original008_join_failure")}))
