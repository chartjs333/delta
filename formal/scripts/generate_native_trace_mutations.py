"""Mutate checked-in public fixtures after their native witness has been frozen."""

import copy
from pathlib import Path

from formal_artifacts import load_json_strict, write_canonical_json
from native_trace_witness import n, snapshot_id


def replace_snapshot(event: dict, bundle: dict, change) -> None:
    proof = event["arithmetic_witness"]
    snapshot = copy.deepcopy(bundle["snapshots"][proof["snapshot_id"]])
    change(snapshot)
    identity = snapshot_id(snapshot)
    bundle["snapshots"][identity] = snapshot
    proof["snapshot_id"] = identity


def rehash_graph(snapshot: dict, bundle: dict, kind: str, change) -> None:
    """Rehash every parent edge; retain the independently supplied current hash."""
    store = {key: value.encode("ascii") for key, value in bundle["artifacts"].items()}
    cache = {}

    def rewrite(ref):
        if ref["id"] in cache:
            return cache[ref["id"]]
        item = n.decode(store[ref["id"]])
        if item["kind"] == kind:
            change(item["payload"])

        def walk(value):
            if type(value) is dict:
                if set(value) == {"id", "kind", "length"}:
                    return rewrite(value)
                return {key: walk(child) for key, child in value.items()}
            if type(value) is list:
                return [walk(child) for child in value]
            return value

        result = n.put(store, item["kind"], walk(item["payload"]))
        cache[ref["id"]] = result
        return result

    snapshot["authority"] = rewrite(snapshot["authority"])
    snapshot["anchor"]["authority_id"] = snapshot["authority"]["id"]
    root = n.resolve(store, snapshot["authority"], "AUTHORITY")
    snapshot["projection_id"] = root["parents"]["apc"]["id"]
    bundle["artifacts"] = {key: value.decode("ascii") for key, value in store.items()}


def generate(root: Path) -> None:
    original = load_json_strict(root / "legal/normal-apply.json")
    source = load_json_strict(root / "native/normal-apply.json")
    cases = []

    def case(name, reason, change, action="ACT-PARAM-VOTE"):
        document, bundle = copy.deepcopy(original), copy.deepcopy(source)
        event = next(e for e in document["events"] if e["action_id"] == action)
        change(document, bundle, event)
        document["trace_id"] = "TRACE-ILLEGAL-NATIVE-" + name.upper()
        filename = "native-" + name
        write_canonical_json(root / f"illegal/{filename}.json", document)
        write_canonical_json(root / f"native/{filename}.json", bundle)
        cases.append({"fixture": filename + ".json", "reason": reason})

    case(
        "missing-witness",
        "NATIVE_WITNESS_REQUIRED",
        lambda d, b, e: e.update(arithmetic_witness=None),
    )

    def reused_sequence(document, bundle, event):
        event["durable_sequence"] -= 1
        replace_snapshot(
            event, bundle, lambda s: s.update(durable_sequence=event["durable_sequence"])
        )

    case("sequence-reuse", "NATIVE_SEQUENCE_REUSE", reused_sequence)
    case("event-role", "NATIVE_EVENT_ROLE", lambda d, b, e: e.update(actor_role="WORKER"))
    case(
        "unknown-snapshot",
        "NATIVE_SNAPSHOT_MISSING",
        lambda d, b, e: e["arithmetic_witness"].update(snapshot_id="sha256:" + "0" * 64),
    )

    def missing_model(d, b, e):
        snap = b["snapshots"][e["arithmetic_witness"]["snapshot_id"]]
        authority = n.decode(b["artifacts"][snap["authority"]["id"]].encode())["payload"]
        del b["artifacts"][authority["model"]["id"]]

    case("missing-model", "ARTIFACT_MISSING", missing_model)

    def altered_snapshot(name, reason, fn):
        case(name, reason, lambda d, b, e: replace_snapshot(e, b, fn))

    altered_snapshot(
        "wrong-actor", "NATIVE_EVENT_BINDING", lambda s: s.update(actor_id="validator-4")
    )
    altered_snapshot(
        "wrong-state",
        "NATIVE_EVENT_BINDING",
        lambda s: s.update(prior_state_root="sha256:" + "0" * 64),
    )
    altered_snapshot(
        "wrong-sequence", "NATIVE_EVENT_BINDING", lambda s: s.update(durable_sequence=999)
    )
    altered_snapshot(
        "stale-current",
        "NATIVE_STALE_CURRENT",
        lambda s: s.update(current_checkpoint="later-parent"),
    )
    altered_snapshot(
        "not-recovered", "RECOVERY_REQUIRED", lambda s: s["anchor"].update(recovered=False)
    )
    altered_snapshot(
        "wrong-optimizer",
        "PARENT_OPTIMIZER",
        lambda s: s["anchor"].update(current_optimizer_hash="sha256:" + "0" * 64),
    )
    altered_snapshot(
        "wrong-projection",
        "NATIVE_CERTIFICATE_PROJECTION",
        lambda s: s.update(projection_id="sha256:" + "0" * 64),
    )
    altered_snapshot("wrong-role", "ROLE", lambda s: s["anchor"].update(role="APPLY"))

    for kind, reason in (("MODEL", "PARENT_MODEL"), ("OPTIMIZER", "PARENT_OPTIMIZER")):

        def mutate_graph(d, b, e, k=kind):
            replace_snapshot(
                e,
                b,
                lambda s: rehash_graph(
                    s, b, k, lambda p: p["values"].__setitem__(0, p["values"][0] + 1)
                ),
            )

        case("rehashed-" + kind.lower(), reason, mutate_graph)

    def result_change(document, bundle, event, field):
        context = event["vote_context_id"]
        for current in document["events"]:
            if current["vote_context_id"] != context:
                continue
            proof = current["arithmetic_witness"]
            if proof is not None:
                command = n.decode(proof["command_ascii"].encode("ascii"))
                command["payload"][field][0] += 1
                if field in {"next_model", "next_optimizer"}:
                    kind = field.removeprefix("next_")
                    command["payload"][field + "_hash"] = n.arithmetic.value_hash(
                        kind, tuple(command["payload"][field])
                    )
                proof["command_ascii"] = n.canonical(command).decode("ascii")
                identity = n.digest(n.canonical(command["payload"]))
            current["body_hash"] = identity

    case(
        "rehashed-parameter",
        "ARITHMETIC_RESULT_MISMATCH",
        lambda d, b, e: result_change(d, b, e, "numerators"),
    )
    for field in ("next_model", "next_optimizer"):
        case(
            "rehashed-" + field.replace("_", "-"),
            "ARITHMETIC_RESULT_MISMATCH",
            lambda d, b, e, f=field: result_change(d, b, e, f),
            "ACT-APPLY-VOTE",
        )

    def command_change(d, b, e, fn):
        proof = e["arithmetic_witness"]
        command = n.decode(proof["command_ascii"].encode("ascii"))
        fn(command)
        proof["command_ascii"] = n.canonical(command).decode("ascii")

    case(
        "command-action",
        "NATIVE_COMMAND_ACTION",
        lambda d, b, e: command_change(d, b, e, lambda c: c.update(action="ACT-APPLY-VOTE")),
    )
    case(
        "command-body",
        "NATIVE_COMMAND_BODY",
        lambda d, b, e: command_change(d, b, e, lambda c: c.update(payload=[])),
    )
    case(
        "noncanonical-command",
        "NONCANONICAL_BYTES",
        lambda d, b, e: e["arithmetic_witness"].update(
            command_ascii=" " + e["arithmetic_witness"]["command_ascii"]
        ),
    )
    write_canonical_json(root / "native/negative-expectations.json", cases)
