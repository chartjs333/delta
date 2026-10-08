"""Synthetic successor coarse commands; no production history or sigma assignment."""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import capsule_binding as wire
from formal.reference.profile_source import commands
from formal.reference.profile_source.configuration_vectors import value_term
from formal.reference.profile_source.isc_vectors import bs


def generate():
    sigma = "sha256:" + "9" * 64
    state = {
        "available_ticket_count": 0,
        "committed_ticket_count": 0,
        "config_id": "sha256:" + "1" * 64,
        "durable_sequence": "4",
        "formal_semantics_id": sigma,
        "height": "7",
        "parent_checkpoint_id": "sha256:" + "2" * 64,
        "phase": "TICKETING_OPEN",
        "round_id": "original-round",
        "schema_version": "1.0.0",
        "state_root": "sha256:" + "3" * 64,
        "ticket_count": 3,
        "type_name": "ROUND_STATE",
        "view": "2",
    }
    command = {
        "actor_id": "a",
        "body_hash": "sha256:" + "4" * 64,
        "command_kind": "FINALIZE_ROUND_CONFIG",
        "formal_semantics_id": sigma,
        "height": "7",
        "logical_tick": "23",
        "request_id": "original-request",
        "round_id": state["round_id"],
        "schema_version": "1.0.0",
        "type_name": "COMMAND",
        "view": "2",
    }
    cases = []
    for kind, phase, committed, available in (
        ("FINALIZE_ROUND_CONFIG", "TICKETING_OPEN", 0, 0),
        ("ADVANCE_VIEW", "TICKETING_OPEN", 0, 0),
        ("ACCEPT_COMMITMENT", "TICKETING_OPEN", 0, 0),
        ("ACCEPT_AVAILABILITY", "COMMITTED", 1, 0),
        ("FINALIZE_INPUT_FREEZE", "AVAILABLE", 1, 1),
        ("FINALIZE_AGGREGATE", "ELIGIBLE", 1, 1),
        ("CERTIFY_ABORT", "ELIGIBLE", 1, 1),
    ):
        s, c = deepcopy(state), deepcopy(command)
        s.update(phase=phase, committed_ticket_count=committed, available_ticket_count=available)
        c["command_kind"] = kind
        if kind == "ADVANCE_VIEW":
            c["view"] = "3"
        cases.append((kind, s, c, False))
    for name, sm, cm in (
        ("wrong_view", {}, {"view": "3", "command_kind": "ACCEPT_COMMITMENT"}),
        ("overflow", {"durable_sequence": str(2**64 - 1)}, {"command_kind": "CERTIFY_ABORT"}),
        ("terminal", {"phase": "ABORTED"}, {"command_kind": "ADVANCE_VIEW", "view": "3"}),
        ("unknown", {}, {"command_kind": "UNKNOWN_ORIGINAL"}),
        ("different_generation", {}, {"formal_semantics_id": "sha256:" + "8" * 64}),
    ):
        cases.append((name, {**state, **sm}, {**command, **cm}, False))
    cases.append(("trailing_command_byte", state, command, True))
    lines = [
        "import ProfileCommands",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace CommandVectors",
    ]
    originals = []
    for i, (name, s, c, trailing) in enumerate(cases):
        sr, cr = wire.envelope(5, s), wire.envelope(6, c)
        if trailing:
            cr += b"\0"
        try:
            output = commands.execute(sigma, sr, cr)
            result = output.next_state
        except CodecError:
            result = None
        lines += [
            f"def s{i} : DeltaReduce.NativePolicyCodec.Value := {value_term(s)}",
            f"def c{i} : DeltaReduce.NativePolicyCodec.Value := {value_term(c)}",
            f"def sr{i} : Bytes := {bs(sr)}",
            f"def cr{i} : Bytes := {bs(cr)}",
        ]
        if result is None:
            lines += [
                f"example : (Commands.derive s{i} c{i} sr{i} cr{i}).isNone = true "
                ":= by decide +kernel"
            ]
        else:
            lines += [
                f"example : (Commands.derive s{i} c{i} sr{i} cr{i}).map (·.nextBytes) =",
                f"  some {bs(result)} := by decide +kernel",
            ]
            if i == 3:
                # One full command envelope join plus the general theorems;
                # all seven state rules are independently checked above.
                table = {}
                for kind, raw in (
                    ("round-state", sr),
                    ("command", cr),
                    ("round-state", output.next_state),
                    ("effect-batch", output.effects),
                    ("wal-record", output.record),
                ):
                    preimage = ("deltareduce:003:" + kind + ":v1").encode() + b"\0" + raw
                    table[preimage] = sha256(preimage).digest()
                lines += [
                    "def hash (raw : Bytes) : Bytes :=",
                    *(
                        f"  if raw = {bs(raw)} then {bs(digest)} else"
                        for raw, digest in table.items()
                    ),
                    "  []",
                    f"def entry : DeltaReduce.NativeWalBytes.Entry := ⟨23,1,cr{i},",
                    f"  {bs(result)}, {bs(output.effects)}, {bs(output.record)}⟩",
                    f"example : (Commands.execute hash s{i} c{i} sr{i} cr{i}).map",
                    "  (fun x => (x.edge.nextBytes,x.effects,x.record)) =",
                    "  some (entry.state,entry.effects,entry.record) := by decide +kernel",
                    f"example : (Commands.checkStored hash s{i} c{i} sr{i} entry).isSome = true",
                    "  := by decide +kernel",
                    f"example : (Commands.checkStored hash s{i} c{i} sr{i}",
                    "  {entry with effects := entry.effects ++ [0]}).isNone = true "
                    ":= by decide +kernel",
                ]
        originals.append(
            {
                "name": name,
                "state": sr.hex(),
                "command": cr.hex(),
                "next": None if result is None else result.hex(),
            }
        )
        if result is not None:
            originals[-1].update(effects=output.effects.hex(), record=output.record.hex())
            if i == 3:
                originals[-1]["sha256_preimages"] = {
                    raw.hex(): digest.hex() for raw, digest in table.items()
                }
    return "\n".join([*lines, "end CommandVectors"]) + "\n", originals
