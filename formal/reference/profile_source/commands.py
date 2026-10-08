"""Original summary-command producer inside the complete source composition.

Reconstructs pinned N transition.cpp and command cache semantics, using the
independently selected generation's exact DRC1 bytes. It never rewrites legacy
bytes or turns a coarse command into certificate/whole-snapshot authorization.
The outer fold must still join policy admission, source occurrence and barrier.
"""

from dataclasses import dataclass, replace

from formal.reference.isc_crypto.codec import _require, _uint, content_id
from formal.reference.isc_w1.codec import decode_request_source
from formal.reference.profile_source import capsule_binding as wire
from formal.reference.profile_source import journals

PIN = "60c692f6e391f839829dfc64e93380db54cd507b"
U64_MAX = 2**64 - 1


def identifier(kind, raw):
    return content_id("deltareduce:003:" + kind + ":v1", raw)


def apply_fields(state, command):
    """Exactly the seven original coarse commands, including original no-op CONFIG."""
    _require(command["round_id"] == state["round_id"], "round_mismatch")
    _require(command["height"] == state["height"], "height_mismatch")
    kind, phase = command["command_kind"], state["phase"]
    result = dict(state)
    if kind != "ADVANCE_VIEW":
        _require(command["view"] == state["view"], "view_mismatch")
    if kind == "FINALIZE_ROUND_CONFIG":
        _require(phase == "TICKETING_OPEN", "illegal_phase")
        return result
    _require(phase not in ("AGGREGATED", "ABORTED"), "terminal_state")
    if kind == "ADVANCE_VIEW":
        _require(
            int(state["view"]) < U64_MAX and int(command["view"]) == int(state["view"]) + 1,
            "view_mismatch",
        )
        result["view"] = command["view"]
    elif kind == "ACCEPT_COMMITMENT":
        _require(phase in ("TICKETING_OPEN", "COMMITTED"), "illegal_phase")
        _require(state["committed_ticket_count"] < state["ticket_count"], "ticket_limit_reached")
        result["committed_ticket_count"] += 1
        result["phase"] = "COMMITTED"
    elif kind == "ACCEPT_AVAILABILITY":
        _require(phase in ("COMMITTED", "AVAILABLE"), "illegal_phase")
        _require(
            state["available_ticket_count"] < state["committed_ticket_count"],
            "availability_limit_reached",
        )
        result["available_ticket_count"] += 1
        result["phase"] = "AVAILABLE"
    elif kind == "FINALIZE_INPUT_FREEZE":
        _require(phase == "AVAILABLE", "illegal_phase")
        _require(state["available_ticket_count"] > 0, "input_set_empty")
        result["phase"] = "ELIGIBLE"
    elif kind == "FINALIZE_AGGREGATE":
        _require(phase == "ELIGIBLE", "illegal_phase")
        result["phase"], result["state_root"] = "AGGREGATED", command["body_hash"]
    elif kind == "CERTIFY_ABORT":
        result["phase"] = "ABORTED"
    else:
        _require(False, "unsupported_command")
    _require(int(state["durable_sequence"]) < U64_MAX, "durable_sequence_overflow")
    result["durable_sequence"] = str(int(state["durable_sequence"]) + 1)
    return result


@dataclass(frozen=True)
class Output:
    original_state: bytes
    original_command: bytes
    next_state: bytes
    effects: bytes
    record: bytes
    command_id: str
    next_id: str
    effects_id: str
    record_id: str


def execute(sigma, original_state, original_command):
    state = wire.read_state(original_state, sigma)
    command = wire.read_command(original_command, sigma)
    next_fields = apply_fields(state, command)
    following = wire.envelope(5, next_fields)
    wire.read_state(following, sigma)
    prior_id = identifier("round-state", original_state)
    command_id = identifier("command", original_command)
    next_id = identifier("round-state", following)
    effects = wire.envelope(
        7,
        {
            "effects": [
                {
                    "body_hash": next_id,
                    "effect_id": "effect:" + command["request_id"] + ":01:persist",
                    "kind": "PERSIST_STATE",
                    "target_id": command["actor_id"],
                },
                {
                    "body_hash": command["body_hash"],
                    "effect_id": "effect:" + command["request_id"] + ":02:publish",
                    "kind": "PUBLISH_CERTIFICATE",
                    "target_id": "validators",
                },
            ],
            "formal_semantics_id": sigma,
            "next_state_root": next_id,
            "prior_state_root": prior_id,
            "request_id": command["request_id"],
            "round_id": command["round_id"],
            "schema_version": "1.0.0",
            "type_name": "EFFECT_BATCH",
        },
    )
    effects_id = identifier("effect-batch", effects)
    record = wire.envelope(
        8,
        {
            "command_id": command_id,
            "effect_batch_id": effects_id,
            "formal_semantics_id": sigma,
            "next_state_root": next_id,
            "prior_state_root": prior_id,
            "record_kind": "TRANSITION",
            "round_id": command["round_id"],
            "schema_version": "1.0.0",
            "sequence": next_fields["durable_sequence"],
            "type_name": "WAL_RECORD",
        },
    )
    return Output(
        original_state,
        original_command,
        following,
        effects,
        record,
        command_id,
        next_id,
        effects_id,
        identifier("wal-record", record),
    )


@dataclass(frozen=True)
class Cached:
    request: str
    physical_slot: int
    output: Output


@dataclass(frozen=True)
class Machine:
    state: bytes
    tick: int | None
    invalidated: bool = False
    requests: tuple[Cached, ...] = ()


def initial(sigma, original_state, tick):
    wire.read_state(original_state, sigma)
    if tick is not None:
        _uint(tick, 8)
    return Machine(original_state, tick)


def persisted(sigma, machine, frame):
    """Check every original kind-1 output, not just its hashes or next-state shape.

    The enclosing mixed scan derives physical slot continuity; the state's
    coarse sequence and inner record are deliberately not equated to this slot.
    This fold checks retained bytes, without performing production recovery.
    """
    _require(frame.kind == 1, "summary command kind required")
    command = wire.read_command(frame.sections[0], sigma)
    _require(
        all(row.request != command["request_id"] for row in machine.requests),
        "durable journal contains duplicate original request",
    )
    tick = int(command["logical_tick"])
    _require(machine.tick is None or machine.tick <= tick, "command time moved backwards")
    computed = execute(sigma, machine.state, frame.sections[0])
    _require(
        frame.sections[1:] == (computed.next_state, computed.effects, computed.record),
        "whole original command output differs",
    )
    cached = Cached(command["request_id"], frame.sequence, computed)
    return replace(
        machine,
        state=computed.next_state,
        tick=tick if machine.tick is not None else None,
        invalidated=machine.invalidated or machine.tick is not None,
        requests=(*machine.requests, cached),
    )


def retry(sigma, machine, original_command):
    command = wire.read_command(original_command, sigma)
    selected = tuple(row for row in machine.requests if row.request == command["request_id"])
    _require(len(selected) == 1, "one existing original request required")
    # The original ID check is retained, with exact original bytes available for
    # the profile join. Equality is not a new hash-collision-resistance premise.
    _require(
        selected[0].output.command_id == identifier("command", original_command),
        "request_conflict",
    )
    return selected[0]


@dataclass(frozen=True)
class Prefix:
    journal: journals.Journal
    initial: Machine
    # One derived coarse state after every original physical record. Keeping
    # these positions is necessary even when the record has no coarse change.
    states: tuple[Machine, ...]
    # Exact original kind-2/3 records still require their own producer checks.
    # They are NOT silently admitted as state-machine stuttering transitions.
    pending_protocol: tuple[journals.Position, ...]

    def before(self, slot):
        _require(type(slot) is int and 1 <= slot <= len(self.states), "original physical slot")
        return self.initial if slot == 1 else self.states[slot - 2]

    @property
    def cut(self):
        n = self.journal.cut_slot
        return self.initial if n == 0 else self.states[n - 1]

    @property
    def target(self):
        return self.initial if not self.states else self.states[-1]


def prefix(sigma, initial_state, tick, original_wal, *, cut_slot, required_prefix):
    """Derive the coarse predecessor at every source position from original bytes.

    Scope is one conjunct of the full mixed fold: it does not authenticate the
    initial state, make a kind-2 vote legal or establish W1 policy/finality. Those
    outstanding records are returned exactly, rather than removed or certified.
    """
    journal = journals.inspect(original_wal, cut_slot=cut_slot, required_prefix=required_prefix)
    start = initial(sigma, initial_state, tick)
    state, states, pending = start, [], []
    for position in journal.positions:
        frame = position.decoded
        if frame.kind == 1:
            state = persisted(sigma, state, frame)
        elif frame.kind == 3:
            source = decode_request_source(frame.sections[0])
            _require(
                source.prior_state_bytes == state.state,
                "W1 prior coarse state is not derived from original command prefix",
            )
            pending.append(position)
        else:
            _require(frame.kind == 2, "unsupported original journal kind")
            pending.append(position)
        states.append(state)
    return Prefix(journal, start, tuple(states), tuple(pending))
