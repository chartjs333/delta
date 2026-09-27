"""Retain original missing-proof result and separately versioned synthetic math."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import generate_native_plan as original_plan
from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import fixture_store
from native_certificate_chain import content_id
from native_plan_weights import VERSION, resolve_members, resolve_plan_weights
from native_source_artifacts import DOMAINS, SourceError, canonical, require
from native_source_artifacts import content_id as artifact_id

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "formal/proposals/evidence/native-plan-weights"
BOUNDARY_PIN = "96261018797ba88f3e58919a89ac22263437266766ccddf3f961826aa54bfc5f"


def original_store():
    plan, _, _, docs, _, _ = original_plan.source()
    store = {content_id(d): canonical(d) for d in docs.values()}
    return store, content_id(plan), {content_id(docs["EC"]): content_id(docs["SEED"])}, docs


def synthetic_case():
    """NEW test graph; no original certificate, snapshot or native run is replaced."""
    store, golden, _ = fixture_store()
    _, _, _, original = original_store()
    docs = copy.deepcopy(original)
    config = copy.deepcopy(golden["fixedpoint_config"]["value"])
    proof = copy.deepcopy(golden["proof_instance"]["value"])
    config.update(coefficient_abs_max="6", max_eligible_contributions="3")
    config_id = artifact_id(canonical(config), DOMAINS["config"])
    store[config_id] = canonical(config)
    proof.update(
        config_id=config_id,
        coefficient_abs_max="6",
        max_eligible_contributions="3",
        common_denominator="12",  # deliberately not minimal LCM(1,3,2)=6
        product_abs_bound=str(6 * 32767),
        max_incremental_prefix_abs=str(18 * 32767),
        final_abs_bound=str(18 * 32767),
    )
    proof_id = artifact_id(canonical(proof), DOMAINS["proof"])
    store[proof_id] = canonical(proof)
    # Resolve schema/base-config *identity* from the actual004 config. This
    # newly constructed context is not the original008 observed context.
    for d in docs.values():
        d["parameter_schema_id"] = config["parameter_schema_id"]
        d["round_config_id"] = config["base_round_config_id"]
    tickets = [
        ("ticket-a", "domain-a"),
        ("ticket-b", "domain-a"),
        ("ticket-c", "domain-b"),
        ("ticket-d", "domain-b"),
    ]
    docs["ISC"]["tuples"] = [
        {**copy.deepcopy(original["ISC"]["tuples"][0]), "ticket_id": t, "domain_id": d}
        for t, d in tickets
    ]
    docs["EC"]["entries"] = [
        {
            **copy.deepcopy(original["EC"]["entries"][0]),
            "ticket_id": t,
            "domain_id": d,
            "accepted": i < 3,
            "gamma": {"numerator": "1", "denominator": 7},
        }
        for i, (t, d) in enumerate(tickets)
    ]
    docs["NORM"]["entries"] = [
        {**copy.deepcopy(original["NORM"]["entries"][0]), "ticket_id": t} for t, _ in tickets
    ]
    docs["APC"]["accumulator_proof_id"] = proof_id
    docs["APC"]["weights"] = [
        {"ticket_id": t, "alpha": {"numerator": str(n), "denominator": d}}
        for t, n, d in (("ticket-a", 0, 1), ("ticket-b", 1, 3), ("ticket-c", 1, 2))
    ]
    docs["APC"]["bucket_assignments"] = [
        {"ticket_id": t, "bucket_id": "bucket-a"} for t, _ in tickets[:3]
    ]
    return store, {k: docs[k] for k in ("ISC", "SEED", "NORM", "EC", "APC")}


def put_graph(store, docs):
    """Rehash a NEW graph in parent order; never mutate a retained original capture."""
    for name in ("ISC", "SEED", "NORM", "EC", "APC"):
        d = docs[name]
        if name != "ISC":
            d["input_set_certificate_id"] = content_id(docs["ISC"])
        if name == "EC":
            d["norm_evidence_id"] = content_id(docs["NORM"])
        if name == "APC":
            d["eligibility_certificate_id"] = content_id(docs["EC"])
            d["seed_transcript_id"] = content_id(docs["SEED"])
        store[content_id(d)] = canonical(d)
    return content_id(docs["APC"]), {content_id(docs["EC"]): content_id(docs["SEED"])}


def generate():
    raw = (EVIDENCE / "native-source-boundary.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == BOUNDARY_PIN, "BOUNDARY_SUBSTITUTED")
    for row in json.loads(raw)["files"]:
        require(
            hashlib.sha256((ROOT / row["retained_path"]).read_bytes()).hexdigest() == row["sha256"],
            "SOURCE_SUBSTITUTED",
        )
    store, plan_id, edges, _ = original_store()
    members = resolve_members(store, plan_id, edges)
    # Include the independent004 fixture store: it still cannot supply bytes
    # for the original APC's different sha256:ffff... proof anchor.
    store.update(fixture_store()[0])
    try:
        resolve_plan_weights(store, plan_id, edges)
    except SourceError as exc:
        failure = str(exc)
    else:
        raise AssertionError("Original APC unexpectedly acquired a proof preimage")
    require(failure == "MISSING_PREIMAGE:" + members.plan["accumulator_proof_id"], "SOURCE_GAP")
    synthetic, docs = synthetic_case()
    new_id, new_edges = put_graph(synthetic, docs)
    checked = resolve_plan_weights(synthetic, new_id, new_edges)
    return {
        "projection_version": VERSION,
        "status": "EXACT_APC_MEMBERS_AND_COMPUTED_WEIGHT_BOUND_RELATION",
        "scope": "ORIGINAL_MEMBERSHIP_PLUS_SEPARATE_SYNTHETIC_BOUND_EXAMPLE",
        "native_reference_commit": "60c692f6e391f839829dfc64e93380db54cd507b",
        "boundary_sha256": BOUNDARY_PIN,
        "formal_go": False,
        "gate_eligible": False,
        "native_export_authenticated": False,
        "original_members": json.loads(json.dumps(asdict(members))),
        "original_weight_join_failure": failure,
        "original_full_weight_join": False,
        "synthetic_case_version": "deltareduce.synthetic-plan-weight-example.v1",
        "synthetic_case": json.loads(json.dumps(asdict(checked))),
        "synthetic_native_execution": False,
        "signatures_or_finality_authenticated": False,
        "count_scope": "GLOBAL_ACCEPTED_COUNT_SUFFICIENT_RESTRICTION_INCLUDING_ZERO_WEIGHTS",
        "coefficient_rule": "APC_ALPHA_ONLY_NO_SECOND_EC_GAMMA_MULTIPLICATION",
        "q_preimage_draft_identity_join": False,
        "full_native_public_refinement": False,
    }


if __name__ == "__main__":
    result = generate()
    write_canonical_json(ROOT / "formal/proposals/native-plan-weight-vectors.json", result)
    print(json.dumps({k: result[k] for k in ("status", "original_weight_join_failure")}))
