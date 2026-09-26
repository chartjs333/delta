"""Computed CONFIG/command observed replay in the singleton empty-graph subdomain.

This does not grant readiness, physical durability, network exposure or GO.
"""

import native_config_admission as admission
import native_proposal_admission as proposals
from generate_native_state_vectors import decode_command, decode_state
from generate_native_transition_vectors import identifier, outputs
from native_admission_snapshot import decode_flat, require
from native_command_replay import retry as retry_command
from native_policy_wal import bind_vote_entry, snapshot, wal_entries


def key(vote):
    return tuple(vote[k] for k in ["validator_id", "validator_epoch_id", "context_id"])


def receipt_bytes(frame, vote, vote_id):
    fields = [frame, vote_id.encode("ascii"), vote["context_id"].encode("ascii")]
    raw = b"DVREC001\x00\x01" + b"\0" * 6
    action = {"ROUND_CONFIG": 1, "ISC": 2}.get(vote["kind"])
    require(action is not None, "supported native receipt action")
    raw += action.to_bytes(4, "big") + b"\0" * 4
    raw += int(vote["durable_sequence"]).to_bytes(8, "big")
    raw += b"".join(len(f).to_bytes(4, "big") + f for f in fields)
    require(len(frame) <= 16 * 1024 * 1024 - 8192, "receipt frame bound")
    require(len(fields[1]) <= 71 and len(fields[2]) <= 4096, "receipt identity bounds")
    return raw


def _replay(policy, initial, wal, snap, proposal_scope):
    require(type(proposal_scope) is bool, "closed computed replay scope")
    p, state = (
        proposals.prepare(policy, initial) if proposal_scope else admission.prepare(policy, initial)
    )
    current, tick, invalidated = initial, p["initial_logical_tick"], False
    requests, votes = {}, {}
    checkpoint = snapshot(snap) if snap else None
    if checkpoint:
        decode_state(checkpoint["state"])
    matched = checkpoint is None or checkpoint["sequence"] == 0
    entries = wal_entries(wal)
    for entry in entries:
        if entry["kind"] == 1:
            command = decode_command(entry["command"])
            require(int(command["logical_tick"]) >= tick, "clock backwards")
            computed, state, _, _ = outputs(state, command)
            require(
                all(entry[k].hex() == computed[k + "_hex"] for k in ["state", "effects", "record"]),
                "computed journal output",
            )
            request = command["request_id"]
            require(request not in requests, "duplicate request")
            requests[request] = {
                **{k: computed[k] for k in ["state_hex", "effects_hex", "record_hex"]},
                **{k: computed[k] for k in ["next_id", "effects_id", "record_id", "command_id"]},
                "sequence": entry["sequence"],
                "replay": False,
            }
            current, tick, invalidated = entry["state"], int(command["logical_tick"]), True
        else:
            bind_vote_entry(entry, policy)
            facts = dict(
                tick=tick,
                ready=False,
                invalidated=invalidated,
                recovery=True,
                expected=entry["sequence"],
            )
            if proposal_scope:
                v, candidate = proposals.check_selected(policy, current, entry["command"], facts)
            else:
                v = admission.check(policy, current, entry["command"], facts)
                candidate = p["candidates"][0]
            require(key(v) not in votes, "duplicate/conflicting vote context")
            vote_id = identifier("vote", entry["command"])
            votes[key(v)] = {
                "vote": v,
                "frame_hex": entry["command"].hex(),
                "vote_id": vote_id,
                "sequence": entry["sequence"],
                "parents": candidate["parents"],
                "receipt_hex": receipt_bytes(entry["command"], v, vote_id).hex(),
            }
        if checkpoint and checkpoint["sequence"] == entry["sequence"]:
            require(checkpoint["state"] == current, "snapshot exact replay state")
            matched = True
    require(matched, "snapshot position absent")
    require(not checkpoint or checkpoint["sequence"] <= len(entries), "snapshot ahead")
    require(len(requests) + len(votes) == len(entries), "complete distinct cache partition")
    return dict(
        state_hex=current.hex(),
        sequence=len(entries),
        tick=tick,
        invalidated=invalidated,
        requests=requests,
        votes=votes,
    )


def replay(policy, initial, wal, snap=b""):
    """Preserve the original singleton CONFIG-only API."""
    return _replay(policy, initial, wal, snap, False)


def replay_proposals(policy, initial, wal, snap=b""):
    """Actual whole-policy CONFIG/ISC gate; no external admission callback."""
    return _replay(policy, initial, wal, snap, True)


def retry_vote(machine, raw):
    vote = decode_flat(raw, 3)
    old = machine["votes"].get(key(vote))
    require(old is not None, "no historical vote")
    require(old["frame_hex"] == raw.hex(), "conflicting canonical vote bytes")
    require(old["vote_id"] == identifier("vote", raw), "cached vote ID")
    return {**old, "replay": True}


__all__ = ["replay", "replay_proposals", "retry_command", "retry_vote"]
