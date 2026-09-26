"""Bounded observed command replay; votes and incomplete byte scans reject."""

from generate_native_state_vectors import decode_command, decode_state
from generate_native_transition_vectors import identifier, outputs
from native_admission_snapshot import require
from native_policy_wal import snapshot, wal_entries


def replay(initial, wal, snap=b"", clock=None):
    state = decode_state(initial)
    require(clock is None or (type(clock) is int and 0 <= clock < 2**64), "clock bound")
    tick, invalidated, requests = clock or 0, False, {}
    checkpoint = snapshot(snap) if snap else None
    matched = checkpoint is None or checkpoint["sequence"] == 0
    entries = wal_entries(wal)
    for entry in entries:
        require(entry["kind"] == 1, "mixed vote history not implemented")
        command = decode_command(entry["command"])
        require(clock is None or int(command["logical_tick"]) >= tick, "clock backwards")
        computed, state, _, _ = outputs(state, command)
        require(
            all(entry[k].hex() == computed[k + "_hex"] for k in ["state", "effects", "record"]),
            "computed journal output",
        )
        request = command["request_id"]
        require(request not in requests, "duplicate request")
        requests[request] = {
            **{k: computed[k] for k in ["state_hex", "effects_hex", "record_hex"]},
            **{k: computed[k] for k in ["next_id", "effects_id", "record_id"]},
            "sequence": entry["sequence"],
            "replay": False,
        }
        requests[request]["command_id"] = computed["command_id"]
        if clock is not None:
            tick, invalidated = int(command["logical_tick"]), True
        if checkpoint and checkpoint["sequence"] == entry["sequence"]:
            require(checkpoint["state"] == entry["state"], "snapshot state mismatch")
            matched = True
    require(matched, "snapshot position absent")
    require(not checkpoint or checkpoint["sequence"] <= len(entries), "snapshot ahead")
    return {
        "state_hex": entries[-1]["state"].hex() if entries else initial.hex(),
        "sequence": len(entries),
        "tick": tick,
        "invalidated": invalidated,
        "requests": requests,
    }


def retry(machine, raw):
    command = decode_command(raw)
    old = machine["requests"].get(command["request_id"])
    require(old is not None, "no historical request")
    require(old["command_id"] == identifier("command", raw), "request conflict")
    return {k: v for k, v in {**old, "replay": True}.items() if k != "command_id"}
