"""Canonical synthetic persist/retry/recovery projections and adversarial cases."""

import copy

from formal_artifacts import load_json_strict, write_canonical_json
from generate_trace_fixtures import ILLEGAL, LEGAL, cid, make_event
from native_durability_fixture import attach_durability
from native_durability_witness import EVENT_FIELDS, n, observation_id


def append(document, event):
    event["prior_state_root"] = document["terminal_state_root"]
    event["next_state_root"] = (
        event["prior_state_root"]
        if event["outcome"] in {"NO_OP", "REJECTED"}
        else cid(f"{document['trace_id']}:{len(document['events'])}")
    )
    event["logical_time"] = document["events"][-1]["logical_time"] + 1
    document["terminal_state_root"] = event["next_state_root"]
    document["events"].append(event)


def retry(event, conflict=False):
    event = copy.deepcopy(event)
    event["outcome"] = "REJECTED" if conflict else "NO_OP"
    event["error_code"] = None
    event["request_id"] = "transport-retry-id"
    if conflict:
        proof = event["arithmetic_witness"]
        body = n.decode(proof["command_ascii"].encode("ascii"))
        body["payload"]["conflicting_extension"] = 1
        proof["command_ascii"] = n.canonical(body).decode("ascii")
        event["body_hash"] = n.digest(n.canonical(body["payload"]))
    return event


def generate():
    native = LEGAL.parent / "native"
    base = load_json_strict(LEGAL / "normal-apply.json")
    bundle = load_json_strict(native / "normal-apply.json")
    parameter_index = next(
        i for i, e in enumerate(base["events"]) if e["action_id"] == "ACT-PARAM-VOTE"
    )
    parameter = base["events"][parameter_index]
    apply = next(e for e in base["events"] if e["action_id"] == "ACT-APPLY-VOTE")
    for after_current in (False, True):
        document = copy.deepcopy(base)
        name = "durability-after-current" if after_current else "durability-retry-recovery"
        document["trace_id"] = "TRACE-" + name.upper()
        if not after_current:
            document["events"] = document["events"][: parameter_index + 1]
            document["terminal_outcome"] = "IN_PROGRESS"
            document["terminal_state_root"] = document["events"][-1]["next_state_root"]
        originals = [parameter, apply] if after_current else [parameter]
        for original in originals:
            append(document, retry(original))
        append(document, make_event("ACT-CRASH", outcome="FAULT", error="CRASH_AFTER_PERSIST"))
        append(document, make_event("ACT-RESTART"))
        append(document, make_event("ACT-JOURNAL-RECOVER"))
        for original in originals:
            append(document, retry(original))
        conflict = retry(parameter, conflict=True)
        conflict["durable_sequence"] = (
            apply["durable_sequence"] if after_current else parameter["durable_sequence"]
        )
        append(document, conflict)
        # A conflict must not poison the old record, even after current advanced.
        append(document, retry(originals[-1]))
        pack = copy.deepcopy(bundle)
        attach_durability(document, pack)
        write_canonical_json(LEGAL / (name + ".json"), document)
        write_canonical_json(native / (name + ".json"), pack)

    base = load_json_strict(LEGAL / "durability-after-current.json")
    pack = load_json_strict(native / "durability-after-current.json")
    first_index = parameter_index
    retry_index = len(base["events"]) - 1
    conflict_index = retry_index - 1
    recover_index = next(
        i for i, e in enumerate(base["events"]) if e["action_id"] == "ACT-JOURNAL-RECOVER"
    )
    cases = load_json_strict(native / "negative-expectations.json")

    def case(name, index, reason, change):
        document, bundle = copy.deepcopy(base), copy.deepcopy(pack)
        event = document["events"][index]
        observation = copy.deepcopy(bundle["operations"][event["durability_witness"]])
        change(event, observation)
        observation["event"] = {field: event[field] for field in EVENT_FIELDS}
        identity = observation_id(observation)
        bundle["operations"][identity] = observation
        event["durability_witness"] = identity
        document["terminal_state_root"] = document["events"][-1]["next_state_root"]
        filename = "durability-" + name + ".json"
        document["trace_id"] = "TRACE-ILLEGAL-" + name.upper()
        write_canonical_json(ILLEGAL / filename, document)
        write_canonical_json(native / filename, bundle)
        cases.append({"fixture": filename, "reason": reason})

    case(
        "prior-sequence",
        first_index,
        "DURABILITY_PRIOR_JOURNAL",
        lambda e, o: o.update(sequence_before=0),
    )
    case(
        "prior-prefix",
        first_index,
        "DURABILITY_PRIOR_JOURNAL",
        lambda e, o: o.update(journal_before=cid("other")),
    )
    case(
        "expose-before-barrier",
        first_index,
        "DURABILITY_EXPOSE_ORDER",
        lambda e, o: o.update(stages=["VALIDATED", "APPENDED", "EXPOSED", "DURABLE", "COMMITTED"]),
    )
    case(
        "missing-barrier",
        first_index,
        "DURABILITY_EXPOSE_ORDER",
        lambda e, o: o["stages"].remove("DURABLE"),
    )
    case(
        "first-receipt",
        first_index,
        "DURABILITY_PERSISTED_BYTES",
        lambda e, o: o.update(receipt_ascii="{}"),
    )
    case(
        "first-effect",
        first_index,
        "DURABILITY_PERSISTED_BYTES",
        lambda e, o: o.update(effect_ascii="{}"),
    )
    case(
        "next-sequence",
        first_index,
        "DURABILITY_JOURNAL_CHANGED",
        lambda e, o: o.update(sequence_after=999),
    )
    case(
        "next-prefix",
        first_index,
        "DURABILITY_JOURNAL_CHANGED",
        lambda e, o: o.update(journal_after=cid("other")),
    )
    case(
        "retry-receipt",
        retry_index,
        "DURABILITY_RETRY_BYTES",
        lambda e, o: o.update(receipt_ascii="{}"),
    )
    case(
        "retry-effect",
        retry_index,
        "DURABILITY_RETRY_BYTES",
        lambda e, o: o.update(effect_ascii="{}"),
    )
    case(
        "retry-sequence",
        retry_index,
        "DURABILITY_RETRY_IDENTITY",
        lambda e, o: e.update(durable_sequence=999),
    )
    case(
        "retry-append",
        retry_index,
        "DURABILITY_JOURNAL_CHANGED",
        lambda e, o: o.update(sequence_after=999),
    )
    case(
        "retry-state-change",
        retry_index,
        "DURABILITY_NOT_STUTTER",
        lambda e, o: e.update(next_state_root=cid("mutated-state")),
    )
    case(
        "retry-unknown-context",
        retry_index,
        "DURABILITY_NO_PRIOR_RECORD",
        lambda e, o: e.update(vote_context_id="unknown"),
    )
    case(
        "retry-early-expose",
        retry_index,
        "DURABILITY_RETRY_STAGES",
        lambda e, o: o.update(stages=["EXPOSED", "LOOKUP"]),
    )
    case(
        "recovery-prefix",
        recover_index,
        "DURABILITY_PRIOR_JOURNAL",
        lambda e, o: o.update(journal_before=cid("lost-wal")),
    )
    case(
        "recovery-truncation",
        recover_index,
        "DURABILITY_JOURNAL_CHANGED",
        lambda e, o: o.update(sequence_after=0),
    )
    case(
        "recovery-unverified",
        recover_index,
        "DURABILITY_RECOVERY_BINDING",
        lambda e, o: o.update(stages=["READ", "RECOVERED"]),
    )
    case(
        "recovery-rejected",
        recover_index,
        "DURABILITY_NOT_RECOVERED",
        lambda e, o: e.update(outcome="REJECTED"),
    )
    case(
        "conflict-receipt",
        conflict_index,
        "DURABILITY_CONFLICT_EFFECT",
        lambda e, o: o.update(receipt_ascii="{}"),
    )
    case(
        "conflict-effect",
        conflict_index,
        "DURABILITY_CONFLICT_EFFECT",
        lambda e, o: o.update(effect_ascii="{}"),
    )
    case(
        "conflict-append",
        conflict_index,
        "DURABILITY_JOURNAL_CHANGED",
        lambda e, o: o.update(journal_after=cid("appended-conflict")),
    )
    case(
        "conflict-noop",
        conflict_index,
        "DURABILITY_CONFLICT_OUTCOME",
        lambda e, o: e.update(outcome="NO_OP"),
    )
    case(
        "conflict-stage",
        conflict_index,
        "DURABILITY_CONFLICT_STAGES",
        lambda e, o: o.update(stages=["LOOKUP", "APPENDED", "REJECTED"]),
    )

    def noncanonical(event, observation):
        event["arithmetic_witness"]["command_ascii"] += " "
        observation["command_ascii"] = event["arithmetic_witness"]["command_ascii"]

    case("retry-noncanonical", retry_index, "NONCANONICAL_BYTES", noncanonical)
    write_canonical_json(native / "negative-expectations.json", cases)


if __name__ == "__main__":
    generate()
