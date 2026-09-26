"""CONFIG admission for singleton candidates and an empty certificate graph.

Uses the complete DVPOL codec and bounded diagnostic DRC1 readers. This is a
strict supported subdomain, not all-policy admission or native equivalence.
"""

import hashlib
import re

import native_policy_codec as codec
from generate_native_state_vectors import decode_state
from native_admission_snapshot import decode_flat, require, state_id


def content_id(s):
    return isinstance(s, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", s) is not None


def context(height, epoch):
    raw = epoch.encode("ascii")
    preimage = b"deltareduce.vote-context.config.v1\0" + height.to_bytes(8, "big")
    preimage += len(raw).to_bytes(8, "big") + raw
    return "sha256:" + hashlib.sha256(preimage).hexdigest()


def prepare(policy_raw, state_raw):
    p = codec.decode(policy_raw)
    s = decode_state(state_raw)
    require(len(p["candidates"]) == 1, "supported singleton candidate")
    snap = p["snapshot"]
    require(all(not snap[k] for k, _ in codec.SCHEMAS["snapshot"][6:]), "supported empty graph")
    require(bool(p["local_validator_id"]) and content_id(p["validator_epoch_id"]), "identity")
    require(all(p["validator_ids"]) and len(p["validator_ids"]) % 3 == 1, "3f+1")
    require(p["local_validator_id"] in p["validator_ids"], "local committee member")
    require(re.fullmatch(r"[a-zA-Z0-9._:-]{1,128}", p["round_id"]) is not None, "round label")
    require(content_id(p["round_config_id"]), "config ID")
    require(p["soft_deadline_tick"] < p["hard_deadline_tick"], "ordered deadlines")
    require(
        s["round_id"] == p["round_id"] and s["config_id"] == p["round_config_id"], "state context"
    )
    require(int(s["height"]) > 0, "positive certificate height")
    require(snap["state_id"] == state_id(state_raw), "exact state bytes")
    require(
        content_id(snap["parameter_schema_id"]) and content_id(snap["arithmetic_profile_id"]),
        "profiles",
    )
    require(
        not snap["required_accumulator_proof_id"]
        or content_id(snap["required_accumulator_proof_id"]),
        "accumulator",
    )
    for key in ["proposed_round_config_ids", "finalized_round_config_ids"]:
        ids = snap[key]
        require(
            ids == sorted(set(ids)) and all(x == p["round_config_id"] for x in ids), "config sets"
        )
    c = p["candidates"][0]
    require(c["action"] == 1 and c["body_hash"] == p["round_config_id"], "CONFIG body")
    require(c["body_hash"] in snap["proposed_round_config_ids"], "proposed membership")
    require(
        c["height"] == int(s["height"]) and c["view"] == int(s["view"]), "candidate coordinates"
    )
    require(c["context_id"] == context(c["height"], p["validator_epoch_id"]), "computed context")
    parents = c["parents"]
    require(parents["round_config_id"] == p["round_config_id"], "parent config")
    require(content_id(parents["parent_checkpoint_id"]), "parent checkpoint ID")
    require(all(not parents[k] for k, _ in codec.SCHEMAS["parents"][2:]), "no foreign parents")
    return p, s


def check(policy_raw, state_raw, vote_raw, facts):
    p, s = prepare(policy_raw, state_raw)
    v = decode_flat(vote_raw, 3)
    c = p["candidates"][0]
    for field, expected in {
        "kind": "ROUND_CONFIG",
        "validator_id": p["local_validator_id"],
        "validator_epoch_id": p["validator_epoch_id"],
        "round_id": s["round_id"],
        "height": s["height"],
        "view": s["view"],
        "context_id": c["context_id"],
        "body_hash": c["body_hash"],
    }.items():
        require(v[field] == expected, "vote " + field)
    require(c["parents"]["parent_checkpoint_id"] == s["parent_checkpoint_id"], "current parent")
    require(0 < int(v["durable_sequence"]) == facts["expected"], "sequence")
    require(
        all(type(facts[k]) is bool for k in ["recovery", "ready", "invalidated"]), "boolean facts"
    )
    require(facts["recovery"] or facts["ready"], "recovery readiness")
    require(not facts["invalidated"], "authority invalidation")
    require(s["phase"] == "TICKETING_OPEN", "CONFIG phase")
    require(
        type(facts["tick"]) is int and 0 <= facts["tick"] < p["hard_deadline_tick"], "hard deadline"
    )
    require(
        type(facts["expected"]) is int and facts["tick"] < 2**64 and facts["expected"] < 2**64,
        "native widths",
    )
    return v
