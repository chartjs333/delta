"""Synthetic admission rejection and unknown/absent/blocked append projections."""

import copy

from formal_artifacts import load_json_strict, write_canonical_json
from generate_durability_fixtures import append
from generate_persistence_fixtures import (
    append_rebased,
    change_observation,
    retain_referenced_observations,
)
from generate_trace_fixtures import ILLEGAL, LEGAL, make_event
from native_durability_fixture import attach_durability
from native_durability_witness import EVENT_FIELDS, envelope, journal_root, n, observation_id
from native_trace_witness import snapshot_id


def observe(document, bundle, event, stages, *, unknown=False):
    prefix = []
    for previous in document["events"]:
        if previous is event:
            break
        if (
            previous["actor_id"] == event["actor_id"]
            and previous["action_id"].endswith("-VOTE")
            and previous["outcome"] in {"ACCEPTED", "FINALIZED"}
        ):
            prefix.append(n.digest(n.canonical(envelope(previous))))
    proof = event["arithmetic_witness"]
    value = {
        "event": {field: event[field] for field in EVENT_FIELDS},
        "snapshot_id": proof["snapshot_id"] if proof else None,
        "command_ascii": proof["command_ascii"] if proof else None,
        "sequence_before": len(prefix),
        "sequence_after": None if unknown else len(prefix),
        "journal_before": journal_root(prefix),
        "journal_after": None if unknown else journal_root(prefix),
        "receipt_ascii": None,
        "effect_ascii": None,
        "stages": stages,
    }
    identity = observation_id(value)
    bundle["operations"][identity] = value
    event["durability_witness"] = identity


def bind_attempt(document, bundle, event):
    append(document, event)
    # A rejected/interrupted invocation changes no replicated state.
    event["next_state_root"] = event["prior_state_root"]
    document["terminal_state_root"] = event["next_state_root"]
    proof = event["arithmetic_witness"]
    snapshot = copy.deepcopy(bundle["snapshots"][proof["snapshot_id"]])
    snapshot["prior_state_root"] = event["prior_state_root"]
    snapshot["anchor"]["logical_time"] = event["logical_time"]
    identity = snapshot_id(snapshot)
    bundle["snapshots"][identity] = snapshot
    proof["snapshot_id"] = identity


def generate():
    native = LEGAL.parent / "native"
    base = load_json_strict(LEGAL / "normal-apply.json")
    source = load_json_strict(native / "normal-apply.json")
    for kind, action in (("parameter", "ACT-PARAM-VOTE"), ("apply", "ACT-APPLY-VOTE")):
        index = next(i for i, e in enumerate(base["events"]) if e["action_id"] == action)
        for mode in (
            "rejected",
            "append-absent",
            "barrier-absent",
            "torn",
            "ambiguous",
            "incomplete",
        ):
            document, bundle = copy.deepcopy(base), copy.deepcopy(source)
            name = f"uncertain-{kind}-{mode}"
            document["trace_id"] = "TRACE-" + name.upper()
            document["events"] = document["events"][:index]
            document["terminal_state_root"] = document["events"][-1]["next_state_root"]
            document["terminal_outcome"] = "IN_PROGRESS"
            first = copy.deepcopy(base["events"][index])
            tip = first["durable_sequence"] - 1
            first["outcome"] = "REJECTED" if mode == "rejected" else "FAULT"
            first["durable_sequence"] = tip if mode == "rejected" else None
            first["error_code"] = None  # Diagnostic stages introduce no protocol error code.
            if mode == "rejected":
                proof = first["arithmetic_witness"]
                command = n.decode(proof["command_ascii"].encode("ascii"))
                command["payload"]["numerators" if kind == "parameter" else "next_model"][0] += 1
                proof["command_ascii"] = n.canonical(command).decode("ascii")
                first["body_hash"] = n.digest(n.canonical(command["payload"]))
            bind_attempt(document, bundle, first)
            scan = None
            if mode not in {"rejected", "incomplete"}:
                for event in (
                    make_event("ACT-CRASH", actor=first["actor_id"], outcome="FAULT"),
                    make_event("ACT-RESTART", actor=first["actor_id"]),
                ):
                    append(document, event)
                blocked = mode in {"torn", "ambiguous"}
                scan = make_event(
                    "ACT-JOURNAL-RECOVER",
                    actor=first["actor_id"],
                    outcome="BLOCKED" if blocked else "ACCEPTED",
                )
                append(document, scan)
                scan["durable_sequence"] = None if blocked else tip
                if blocked:
                    scan["next_state_root"] = scan["prior_state_root"]
                    document["terminal_state_root"] = scan["next_state_root"]
            if mode in {"rejected", "append-absent", "barrier-absent"}:
                for event in base["events"][index : index + 4]:
                    append_rebased(document, bundle, event)
            attach_durability(document, bundle)
            stages = ["VALIDATING", "REJECTED"] if mode == "rejected" else ["VALIDATED", "APPENDED"]
            if mode == "barrier-absent":
                stages.append("BARRIER_FAILED")
            if mode != "rejected":
                stages.append("UNKNOWN")
            observe(document, bundle, first, stages, unknown=mode != "rejected")
            if scan:
                middle = {"torn": "CORRUPT", "ambiguous": "AMBIGUOUS"}.get(mode, "VERIFIED_ABSENT")
                observe(
                    document,
                    bundle,
                    scan,
                    ["READ", middle, "BLOCKED" if blocked else "RECOVERED"],
                    unknown=blocked,
                )
            retain_referenced_observations(document, bundle)
            write_canonical_json(LEGAL / (name + ".json"), document)
            write_canonical_json(native / (name + ".json"), bundle)

    cases = load_json_strict(native / "negative-expectations.json")

    def case(name, source, reason, mutate):
        document = load_json_strict(LEGAL / ("uncertain-parameter-" + source + ".json"))
        bundle = load_json_strict(native / ("uncertain-parameter-" + source + ".json"))
        first = next(e for e in document["events"] if e["action_id"] == "ACT-PARAM-VOTE")
        mutate(document, bundle, first)
        filename = "uncertain-" + name + ".json"
        document["trace_id"] = "TRACE-ILLEGAL-" + name.upper()
        document["terminal_state_root"] = document["events"][-1]["next_state_root"]
        retain_referenced_observations(document, bundle)
        write_canonical_json(ILLEGAL / filename, document)
        write_canonical_json(native / filename, bundle)
        cases.append({"fixture": filename, "reason": reason})

    def valid_rejection(document, bundle, first):
        command = next(
            e
            for e in document["events"]
            if e["action_id"] == "ACT-PARAM-VOTE" and e["outcome"] == "ACCEPTED"
        )
        first["arithmetic_witness"]["command_ascii"] = command["arithmetic_witness"][
            "command_ascii"
        ]
        first["body_hash"] = command["body_hash"]
        change_observation(
            bundle, first, command_ascii=first["arithmetic_witness"]["command_ascii"]
        )

    case("valid-command-rejected", "rejected", "NATIVE_REJECTION_NOT_JUSTIFIED", valid_rejection)

    def invalid_anchor(document, bundle, first):
        proof = first["arithmetic_witness"]
        snapshot = copy.deepcopy(bundle["snapshots"][proof["snapshot_id"]])
        snapshot["anchor"]["recovered"] = False
        identity = snapshot_id(snapshot)
        bundle["snapshots"][identity] = snapshot
        proof["snapshot_id"] = identity
        change_observation(bundle, first, snapshot_id=identity)

    case("invalid-anchor-rejection", "rejected", "RECOVERY_REQUIRED", invalid_anchor)

    def rejection_state(document, bundle, first):
        document["events"] = document["events"][: document["events"].index(first) + 1]
        first["next_state_root"] = n.digest(b"invalid rejection state change")
        change_observation(bundle, first)

    case(
        "rejection-changes-state",
        "rejected",
        "DURABILITY_ADMISSION_REJECTION_OUTPUT",
        rejection_state,
    )
    for field in ("receipt_ascii", "effect_ascii"):
        case(
            "rejection-" + field,
            "rejected",
            "DURABILITY_ADMISSION_REJECTION_OUTPUT",
            lambda d, b, e, field=field: change_observation(b, e, **{field: "{}"}),
        )
    case(
        "rejection-append",
        "rejected",
        "DURABILITY_JOURNAL_CHANGED",
        lambda d, b, e: change_observation(b, e, sequence_after=e["durable_sequence"] + 1),
    )
    case(
        "unknown-claims-prefix",
        "incomplete",
        "DURABILITY_UNKNOWN_ASSERTS_JOURNAL",
        lambda d, b, e: change_observation(b, e, sequence_after=4, journal_after=journal_root([])),
    )
    case(
        "unknown-exposes",
        "incomplete",
        "DURABILITY_UNKNOWN_OUTPUT",
        lambda d, b, e: change_observation(b, e, effect_ascii="{}"),
    )

    def known_event_sequence(document, bundle, first):
        first["durable_sequence"] = 4
        change_observation(bundle, first)

    case("unknown-event-sequence", "incomplete", "DURABILITY_UNKNOWN_OUTPUT", known_event_sequence)

    def scan_change(document, bundle, first, **changes):
        scan = next(e for e in document["events"] if e["action_id"] == "ACT-JOURNAL-RECOVER")
        change_observation(bundle, scan, **changes)

    case(
        "ordinary-recovery",
        "append-absent",
        "DURABILITY_ABSENCE_NOT_VERIFIED",
        lambda d, b, e: scan_change(d, b, e, stages=["READ", "VERIFIED", "RECOVERED"]),
    )
    case(
        "absent-truncates-prefix",
        "append-absent",
        "DURABILITY_JOURNAL_CHANGED",
        lambda d, b, e: scan_change(d, b, e, sequence_after=0),
    )
    case(
        "blocked-claims-prefix",
        "torn",
        "DURABILITY_UNKNOWN_ASSERTS_JOURNAL",
        lambda d, b, e: scan_change(d, b, e, sequence_after=4, journal_after=journal_root([])),
    )

    def promote_blocked(document, bundle, first):
        scan = copy.deepcopy(document["events"][-1])
        scan["outcome"] = "ACCEPTED"
        scan["durable_sequence"] = 4
        append(document, scan)
        observe(document, bundle, scan, ["READ", "VERIFIED_ABSENT", "RECOVERED"])

    case("blocked-becomes-ready", "torn", "DURABILITY_BLOCKED_SCAN_UNRESOLVED", promote_blocked)

    def early_retry(document, bundle, first):
        event = copy.deepcopy(first)
        event["outcome"] = "NO_OP"
        event["durable_sequence"] = 5
        append(document, event)
        observe(document, bundle, event, ["LOOKUP", "EXPOSED"])

    case("retry-before-crash", "incomplete", "DURABILITY_CRASH_REQUIRED", early_retry)

    def absent_replay(document, bundle, first):
        admitted = next(
            e
            for e in document["events"]
            if e["action_id"] == "ACT-PARAM-VOTE" and e["outcome"] == "ACCEPTED"
        )
        document["events"] = document["events"][: document["events"].index(admitted) + 1]
        admitted["outcome"] = "NO_OP"
        admitted["next_state_root"] = admitted["prior_state_root"]
        change_observation(bundle, admitted, stages=["LOOKUP", "EXPOSED"])

    case(
        "absent-replay-without-record", "append-absent", "DURABILITY_NO_PRIOR_RECORD", absent_replay
    )
    write_canonical_json(native / "negative-expectations.json", cases)
