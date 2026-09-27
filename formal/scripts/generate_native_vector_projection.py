"""Original 004 vectors plus explicitly synthetic APC/draft authority examples."""

from __future__ import annotations

import copy
import json
import struct
from dataclasses import asdict
from pathlib import Path

import generate_native_available_q as available
import generate_native_plan_weights as plans
import native_source_artifacts as src
from formal_artifacts import write_canonical_json
from native_available_q import observation_bytes
from native_vector_projection import VERSION, check_draft_inputs, draft, project_inputs

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proposals/native-vector-projection-vectors.json"


def rewrite_q(
    store, golden, observation, *, ticket=None, domain=None, proof=None, parent=None, negate=False
):
    """NEW synthetic source, never alteration of retained original fixture bytes."""
    m = copy.deepcopy(golden["manifest"]["value"])
    for key, value in (
        ("ticket_id", ticket),
        ("domain_id", domain),
        ("proof_instance_id", proof),
        ("parent_checkpoint_id", parent),
    ):
        if value is not None:
            m[key] = value
    total = 0
    for row, original in zip(m["shards"], golden["shards"], strict=True):
        h = copy.deepcopy(original["header"])
        h["ticket_id"], h["proof_instance_id"] = m["ticket_id"], m["proof_instance_id"]
        payload = bytes.fromhex(original["payload_hex"])
        if negate:
            values = [-v[0] for v in struct.iter_unpack("<h", payload)]
            payload = struct.pack("<" + "h" * len(values), *values)
        h["payload_sha256"] = src.content_id(payload)
        raw_h = src.canonical(h)
        raw = struct.pack("<4sHHII", b"DRQ1", 1, 0, len(raw_h), len(payload)) + raw_h + payload
        row["leaf_id"], row["envelope_bytes"] = src.content_id(raw, src.DOMAINS["leaf"]), len(raw)
        store[row["leaf_id"]] = raw
        total += len(raw)
    m["total_envelope_bytes"] = total
    m["commitment_root"] = src.merkle_root([r["leaf_id"] for r in m["shards"]])
    raw = src.canonical(m)
    mid = src.content_id(raw, src.DOMAINS["manifest"])
    store[mid] = raw
    obs = copy.deepcopy(observation)
    obs["manifest_id"], obs["permitted_ticket_ids"] = mid, [m["ticket_id"]]
    obs["commitment"]["ticket_id"] = obs["availability"]["ticket_id"] = m["ticket_id"]
    obs["required_leaf_ids"] = sorted(r["leaf_id"] for r in m["shards"])
    obs["availability"]["covered_leaf_ids"] = list(obs["required_leaf_ids"])
    oid, raw = observation_bytes(obs)
    store[oid] = raw
    return oid


def source_fixture(multiple=False):
    store, pid, edges, observations, docs, obs = available.joined_fixture()
    if not multiple:
        return store, pid, edges, observations
    _, golden, _ = available.fixture()
    proof = json.loads(store[docs["APC"]["accumulator_proof_id"]])
    proof["common_denominator"] = "12"  # retain 12, not the minimal denominator 6
    raw = src.canonical(proof)
    proof_id = src.content_id(raw, src.DOMAINS["proof"])
    store[proof_id] = raw
    docs["APC"]["accumulator_proof_id"] = proof_id
    base = obs["commitment"]["ticket_id"]
    for name, key in (
        ("ISC", "tuples"),
        ("EC", "entries"),
        ("NORM", "entries"),
        ("APC", "weights"),
        ("APC", "bucket_assignments"),
    ):
        original = copy.deepcopy(docs[name][key][0])
        docs[name][key] = [{**original, "ticket_id": base + suffix} for suffix in ("", "b", "c")]
    domains = [docs["ISC"]["tuples"][0]["domain_id"]] * 2 + ["domain-z"]
    for i, domain in enumerate(domains):
        docs["ISC"]["tuples"][i]["domain_id"] = domain
        docs["EC"]["entries"][i]["domain_id"] = domain
        docs["EC"]["entries"][i]["gamma"] = {"numerator": "1", "denominator": 7}
    for row, (n, d) in zip(docs["APC"]["weights"], ((1, 3), (1, 2), (0, 1)), strict=True):
        row["alpha"] = {"numerator": str(n), "denominator": d}
    observations = [
        rewrite_q(
            store, golden, obs, ticket=base + suffix, domain=domain, proof=proof_id, negate=(i == 1)
        )
        for i, (suffix, domain) in enumerate(zip(("", "b", "c"), domains, strict=True))
    ]
    pid, edges = plans.put_graph(store, docs)
    return store, pid, edges, observations


def draft_example(projected, change=None):
    """Synthetic complete draft wrapper. Model/profile/certificate sources NOT authenticated."""
    store = dict(projected.artifacts)
    source = projected.source.plan.members.plan
    m = projected.source.inputs[0].source.q.manifest
    size = len(projected.schema["coordinates"])
    domains = [d["domain_id"] for d in projected.source.plan.domains]
    profile = {
        "accumulator_bits": projected.source.plan.accumulator.accumulator_bits,
        "apply_quantum": [1, 1],
        "domain_weights": [{"domain": domain, "weight": [1, len(domains)]} for domain in domains],
        "learning_rate": [1, 1],
        "momentum": [0, 1],
        "weight_decay": [0, 1],
        "rounding": "HALF_TOWARD_POSITIVE",
        "nesterov": True,
        "output_range": "FULL_SIGNED_INT64",
    }
    schema = copy.deepcopy(projected.schema)
    assignments = [
        {**copy.deepcopy(a), "context": f"parameter-{i:010d}"}
        for i, a in enumerate(projected.assignments)
    ]
    context = {
        "round": source["round_id"],
        "height": source["height"],
        "view": source["view"],
        "epoch": source["validator_epoch_id"],
        "hard_deadline": 100,
        "parent_checkpoint": m["parent_checkpoint_id"],
    }
    model, optimizer = [20] * size, [2] * size
    data = {
        "schema": schema,
        "assignments": assignments,
        "profile": profile,
        "context": context,
        "model": model,
        "optimizer": optimizer,
    }
    if change:
        change(data, store)
    schema_ref = draft.put(store, "SCHEMA", schema)
    profile_ref = draft.put(store, "PROFILE", profile)
    model_ref = draft.put(
        store, "MODEL", {"schema": schema_ref, "quantum": [1, 1], "values": model}
    )
    optimizer_ref = draft.put(
        store, "OPTIMIZER", {"schema": schema_ref, "quantum": [1, 1], "values": optimizer}
    )
    plan = draft.put(
        store,
        "PLAN",
        {
            "schema": schema_ref,
            "profile": profile_ref,
            "tickets": list(projected.tickets),
            "assignments": assignments,
        },
    )
    commitments = []
    for ticket in projected.tickets:
        contributions = [
            (a, c) for a in assignments for c in a["contributions"] if c["ticket"] == ticket["id"]
        ]
        commitments.append(
            {
                "ticket": ticket["id"],
                "domain": ticket["domain"],
                "leaves": [{"shard": a["shard"], "q": c["q"]} for a, c in contributions],
            }
        )
    isc = draft.put(
        store,
        "ISC_PROJECTION",
        {"members": [t["id"] for t in projected.tickets], "commitments": commitments},
    )
    ec = draft.put(
        store, "EC_PROJECTION", {"isc": isc, "eligible": [t["id"] for t in projected.tickets]}
    )
    apc = draft.put(store, "APC_PROJECTION", {"ec": ec, "plan": plan})
    authority = draft.put(
        store,
        "AUTHORITY",
        {
            "context": context,
            "schema": schema_ref,
            "profile": profile_ref,
            "plan": plan,
            "model": model_ref,
            "optimizer": optimizer_ref,
            "parents": {"isc": isc, "ec": ec, "apc": apc},
        },
    )
    anchor = draft.NativeAnchor(
        authority["id"],
        draft.arithmetic.value_hash("model", tuple(model)),
        draft.arithmetic.value_hash("optimizer", tuple(optimizer)),
        context["round"],
        context["height"],
        context["view"],
        context["epoch"],
        1,
        context["hard_deadline"],
        "PARAMETER",
        True,
        context["parent_checkpoint"],
    )
    return store, anchor, authority


def generate():
    examples = []
    for multiple in (False, True):
        store, pid, edges, observations = source_fixture(multiple)
        projected = project_inputs(store, pid, edges, observations)
        ds, anchor, authority = draft_example(projected)
        result = check_draft_inputs(store, pid, edges, observations, ds, anchor, authority)
        examples.append(
            {
                "source_kind": "NEW_SYNTHETIC_MULTITICKET_GRAPH"
                if multiple
                else "ORIGINAL004_Q_SYNTHETIC_APC_AND_DRAFT",
                "source_plan_id": pid,
                "ec_seed_bindings": edges,
                "observation_ids": observations,
                "source_store": {k: v.hex() for k, v in sorted(store.items())},
                "draft_store": {k: v.hex() for k, v in sorted(ds.items())},
                "anchor": asdict(anchor),
                "schema": projected.schema,
                "locations": list(projected.locations),
                "numeric_results": list(projected.results),
                "join": result,
            }
        )
    return {
        "version": VERSION,
        "native_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
        "full_authority_binding": False,
        "examples": examples,
    }


if __name__ == "__main__":
    write_canonical_json(TARGET, generate())
    print("Generated two source-bound vector input examples; no native execution or authority.")
