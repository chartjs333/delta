"""Entire CONFIG/ISC candidate-list admission with computed proposed ISC bodies.

No policy rewrite or finite candidate table. The supported graph still excludes
finalized certificates. Primitive snapshot authority is not authenticated here.
"""

import native_config_admission as config
import native_isc_admission as isc
import native_policy_codec as codec
from native_admission_snapshot import decode_flat, require


def prepare(policy_raw, state_raw):
    p, s = isc.prepare_graph(policy_raw, state_raw)
    for c in p["candidates"]:
        if c["action"] == 1:
            require(c["body_hash"] == p["round_config_id"], "CONFIG body")
            require(c["body_hash"] in p["snapshot"]["proposed_round_config_ids"], "CONFIG member")
            context = config.context(int(s["height"]), p["validator_epoch_id"])
        elif c["action"] == 2:
            require(c["body_hash"] in p["snapshot"]["closed_input_set_ids"], "ISC member")
            context = isc.context(p["round_id"])
        else:
            raise ValueError("unsupported action: CONFIG/ISC proposals only")
        require(c["context_id"] == context, "computed candidate context")
        require(
            c["height"] == int(s["height"]) and c["view"] == int(s["view"]),
            "candidate coordinates",
        )
        parents = c["parents"]
        require(parents["round_config_id"] == p["round_config_id"], "parent config")
        require(isc.content_id(parents["parent_checkpoint_id"]), "parent checkpoint ID")
        require(all(not parents[k] for k, _ in codec.SCHEMAS["parents"][2:]), "foreign parents")
    return p, s


def check_selected(policy_raw, state_raw, vote_raw, facts):
    p, s = prepare(policy_raw, state_raw)
    v = decode_flat(vote_raw, 3)
    action = {"ROUND_CONFIG": 1, "ISC": 2}.get(v["kind"])
    candidates = [
        c
        for c in p["candidates"]
        if c["action"] == action
        and c["context_id"] == v["context_id"]
        and c["height"] == int(v["height"])
        and c["view"] == int(v["view"])
    ]
    require(len(candidates) == 1, "one exact configured candidate")
    c = candidates[0]
    for field, expected in {
        "validator_id": p["local_validator_id"],
        "validator_epoch_id": p["validator_epoch_id"],
        "round_id": s["round_id"],
        "height": s["height"],
        "view": s["view"],
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
    require(s["phase"] == {1: "TICKETING_OPEN", 2: "AVAILABLE"}[action], "vote phase")
    require(
        type(facts["tick"]) is int and 0 <= facts["tick"] < p["hard_deadline_tick"], "hard deadline"
    )
    require(
        type(facts["expected"]) is int and facts["tick"] < 2**64 and facts["expected"] < 2**64,
        "native widths",
    )
    return v, c


def check(policy_raw, state_raw, vote_raw, facts):
    return check_selected(policy_raw, state_raw, vote_raw, facts)[0]
