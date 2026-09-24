"""Synthetic persisted-but-unexposed public/native projections, not disk runs."""

import copy

from formal_artifacts import load_json_strict, write_canonical_json
from generate_durability_fixtures import append, retry
from generate_trace_fixtures import ILLEGAL, LEGAL, make_event
from native_durability_fixture import attach_durability
from native_durability_witness import EVENT_FIELDS, UNEXPOSED_STAGES, observation_id
from native_trace_witness import snapshot_id

CUTS = ("durable", "committed", "append-survived", "barrier-failed-survived")


def change_observation(bundle, event, **changes):
    value = copy.deepcopy(bundle["operations"][event["durability_witness"]])
    value.update(changes)
    value["event"] = {field: event[field] for field in EVENT_FIELDS}
    identity = observation_id(value)
    bundle["operations"][identity] = value
    event["durability_witness"] = identity


def retain_referenced_observations(document, bundle):
    referenced = {e["durability_witness"] for e in document["events"] if e["durability_witness"]}
    bundle["operations"] = {key: bundle["operations"][key] for key in sorted(referenced)}


def append_rebased(document, bundle, event):
    """Rebase synthetic later events; actual witnesses must come from native."""
    event = copy.deepcopy(event)
    append(document, event)
    proof = event["arithmetic_witness"]
    if proof and event["outcome"] in {"ACCEPTED", "FINALIZED"}:
        snapshot = copy.deepcopy(bundle["snapshots"][proof["snapshot_id"]])
        snapshot["prior_state_root"] = event["prior_state_root"]
        snapshot["anchor"]["logical_time"] = event["logical_time"]
        identity = snapshot_id(snapshot)
        bundle["snapshots"][identity] = snapshot
        proof["snapshot_id"] = identity


def generate():
    native = LEGAL.parent / "native"
    base = load_json_strict(LEGAL / "normal-apply.json")
    source_bundle = load_json_strict(native / "normal-apply.json")
    for kind, action in (("parameter", "ACT-PARAM-VOTE"), ("apply", "ACT-APPLY-VOTE")):
        index = next(i for i, e in enumerate(base["events"]) if e["action_id"] == action)
        for label, stages in zip(CUTS, UNEXPOSED_STAGES, strict=True):
            document, bundle = copy.deepcopy(base), copy.deepcopy(source_bundle)
            name = f"cut-{kind}-{label}"
            document["trace_id"] = "TRACE-" + name.upper()
            document["events"] = document["events"][: index + 1]
            document["terminal_outcome"] = "IN_PROGRESS"
            first = document["events"][-1]
            document["terminal_state_root"] = first["next_state_root"]
            for event in (
                make_event(
                    "ACT-CRASH",
                    actor=first["actor_id"],
                    outcome="FAULT",
                    error="CRASH_AFTER_PERSIST",
                ),
                make_event("ACT-RESTART", actor=first["actor_id"]),
                make_event("ACT-JOURNAL-RECOVER", actor=first["actor_id"]),
                retry(first),
            ):
                append(document, event)
            # The other two original votes plus the exact QC complete this key.
            # The recovered retry must supply the missing third exposed vote.
            for event in base["events"][index + 1 : index + 4]:
                append_rebased(document, bundle, event)
            attach_durability(document, bundle)
            change_observation(bundle, first, stages=stages, receipt_ascii=None, effect_ascii=None)
            retain_referenced_observations(document, bundle)
            write_canonical_json(LEGAL / (name + ".json"), document)
            write_canonical_json(native / (name + ".json"), bundle)

    cases = load_json_strict(native / "negative-expectations.json")

    def case(name, reason, change, source="cut-parameter-durable"):
        document = load_json_strict(LEGAL / (source + ".json"))
        bundle = load_json_strict(native / (source + ".json"))
        first = next(e for e in document["events"] if e["action_id"] == "ACT-PARAM-VOTE")
        change(document, bundle, first)
        document["trace_id"] = "TRACE-ILLEGAL-CUT-" + name.upper()
        document["terminal_state_root"] = document["events"][-1]["next_state_root"]
        filename = "cut-" + name + ".json"
        retain_referenced_observations(document, bundle)
        write_canonical_json(ILLEGAL / filename, document)
        write_canonical_json(native / filename, bundle)
        cases.append({"fixture": filename, "reason": reason})

    case(
        "early-receipt",
        "DURABILITY_PERSISTED_BYTES",
        lambda d, b, e: change_observation(b, e, receipt_ascii="{}"),
    )
    case(
        "early-effect",
        "DURABILITY_PERSISTED_BYTES",
        lambda d, b, e: change_observation(b, e, effect_ascii="{}"),
    )
    case(
        "no-durable-record",
        "DURABILITY_EXPOSE_ORDER",
        lambda d, b, e: change_observation(b, e, stages=["VALIDATED", "APPENDED"]),
    )
    case(
        "expose-without-commit",
        "DURABILITY_EXPOSE_ORDER",
        lambda d, b, e: change_observation(
            b, e, stages=["VALIDATED", "APPENDED", "DURABLE", "EXPOSED"]
        ),
    )

    def without_exposure(document, bundle, first):
        document["events"] = [e for e in document["events"] if e["outcome"] != "NO_OP"]

    case("qc-before-exposure", "QC_QUORUM_MISSING", without_exposure)

    def before_crash(document, bundle, first):
        event = retry(first)
        event["prior_state_root"] = event["next_state_root"] = first["next_state_root"]
        event["logical_time"] = first["logical_time"]
        document["events"].insert(document["events"].index(first) + 1, event)
        attach_durability(document, bundle)
        change_observation(
            bundle, first, stages=UNEXPOSED_STAGES[0], receipt_ascii=None, effect_ascii=None
        )

    case("retry-before-crash", "DURABILITY_CRASH_REQUIRED", before_crash)

    def unverified(document, bundle, first):
        index = next(i for i, e in enumerate(document["events"]) if e["action_id"] == "ACT-CRASH")
        document["events"] = document["events"][: index + 1]

    case(
        "unacknowledged-unverified",
        "DURABILITY_UNACKNOWLEDGED_UNVERIFIED",
        unverified,
        "cut-parameter-barrier-failed-survived",
    )

    def recover_change(document, bundle, first):
        event = next(e for e in document["events"] if e["action_id"] == "ACT-JOURNAL-RECOVER")
        change_observation(bundle, event, sequence_after=0)

    case("recovery-truncates-unexposed", "DURABILITY_JOURNAL_CHANGED", recover_change)

    def retry_change(document, bundle, first):
        event = next(e for e in document["events"] if e["outcome"] == "NO_OP")
        change_observation(bundle, event, receipt_ascii="{}")

    case("replay-rewrites-receipt", "DURABILITY_RETRY_BYTES", retry_change)
    write_canonical_json(native / "negative-expectations.json", cases)
