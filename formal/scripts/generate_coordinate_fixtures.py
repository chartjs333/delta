"""Multicoordinate/domain fixtures and rehashed projection substitutions."""

import copy
from dataclasses import asdict, replace

from formal_artifacts import load_json_strict, write_canonical_json
from generate_native_trace_mutations import rehash_graph, replace_snapshot
from generate_trace_fixtures import (
    ILLEGAL,
    LEGAL,
    build_round_contract,
    cid,
    content_id,
    make_event,
    qc_events,
    trace,
    write_fixture,
)
from native_trace_witness import n


def matrix_contract(domains=3, lengths=(2, 3)):
    assignments = [
        {
            "parameter_id": f"d{d:02}-s{s:02}",
            "domain_id": f"d{d:02}",
            "shard_id": f"s{s:02}",
            "vote_context_id": f"PARAM:d{d:02}:s{s:02}:round-1",
        }
        for d in range(domains)
        for s in range(len(lengths))
    ]
    return build_round_contract(
        assignments, shard_lengths={f"s{s:02}": n for s, n in enumerate(lengths)}
    )


def rehash_contract(contract):
    schema = contract["parameter_schema"]
    schema["schema_hash"] = content_id({k: v for k, v in schema.items() if k != "schema_hash"})
    plan = contract["shard_plan"]
    plan["plan_hash"] = content_id({"assignments": plan["assignments"]})
    config = contract["round_config"]
    config["parameter_schema_hash"] = schema["schema_hash"]
    config["shard_plan_hash"] = plan["plan_hash"]
    config["body_hash"] = content_id({k: v for k, v in config.items() if k != "body_hash"})
    contract["contract_id"] = content_id({k: v for k, v in contract.items() if k != "contract_id"})


def generate():
    contract = matrix_contract()
    base = load_json_strict(LEGAL / "normal-apply.json")["events"]
    end = next(i for i, e in enumerate(base) if e["action_id"] == "ACT-PARAM-VOTE")
    events = copy.deepcopy(base[:end])
    for event in events:
        if event["action_id"].startswith("ACT-CONFIG-"):
            event["body_hash"] = contract["round_config"]["body_hash"]
    apc = next(e["result_hash"] for e in events if e["action_id"] == "ACT-APC-FINALIZE")
    results = []
    for assignment in contract["shard_plan"]["assignments"]:
        part, _, result = qc_events(
            "ACT-PARAM-VOTE",
            "ACT-PARAM-FINALIZE",
            "matrix-" + assignment["parameter_id"],
            vote_context=assignment["vote_context_id"],
            parents=[apc],
        )
        events.extend(part)
        results.append(result)
    events.append(make_event("ACT-ROOT-ASSEMBLE", body=cid("matrix-root"), artifacts=results))
    part, _, root = qc_events("ACT-ROOT-VOTE", "ACT-ROOT-FINALIZE", "matrix-root")
    events.extend(part)
    part, _, apply = qc_events(
        "ACT-APPLY-VOTE", "ACT-APPLY-FINALIZE", "matrix-apply", parents=[root]
    )
    events.extend(part)
    events.append(
        make_event(
            "ACT-CURRENT-ADVANCE",
            body=cid("matrix-current"),
            result=cid("matrix-checkpoint"),
            parents=[apply],
            outcome="FINALIZED",
        )
    )
    write_fixture(
        LEGAL,
        "native-coordinate-matrix",
        trace("TRACE-NATIVE-COORDINATE-MATRIX", events, "APPLIED", contract),
    )
    original = load_json_strict(LEGAL / "native-coordinate-matrix.json")
    source = load_json_strict(LEGAL.parent / "native/native-coordinate-matrix.json")
    cases = load_json_strict(LEGAL.parent / "native/negative-expectations.json")

    def case(name, reason, mutate_contract=None, mutate_native=None):
        document, bundle = copy.deepcopy(original), copy.deepcopy(source)
        if mutate_contract:
            mutate_contract(document["round_contract"])
            rehash_contract(document["round_contract"])
            for event in document["events"]:
                if event["action_id"].startswith("ACT-CONFIG-"):
                    event["body_hash"] = document["round_contract"]["round_config"]["body_hash"]
                if event["arithmetic_witness"]:
                    replace_snapshot(
                        event,
                        bundle,
                        lambda s: s.update(
                            round_contract_id=document["round_contract"]["contract_id"]
                        ),
                    )
        if mutate_native:
            # Recompute every candidate and dependent aggregate as well as its
            # hashes: the graph is self-consistent, but disagrees with the frozen
            # public coordinate projection. Only the cross-boundary binding may
            # reject this case, not an incidental stale candidate/result hash.
            bodies = {}
            for event in document["events"]:
                proof = event["arithmetic_witness"]
                if proof is None:
                    key = (event["action_id"].replace("FINALIZE", "VOTE"), event["vote_context_id"])
                    if key in bodies:
                        event["body_hash"] = bodies[key]
                    continue

                def change(snapshot, event=event, proof=proof):
                    rehash_graph(snapshot, bundle, "SCHEMA", mutate_native)
                    store = {k: v.encode("ascii") for k, v in bundle["artifacts"].items()}
                    anchor = n.NativeAnchor(**snapshot["anchor"])
                    witness = n.Witness(anchor, snapshot["authority"], store)
                    if event["action_id"] == "ACT-APPLY-VOTE":
                        parameters = [
                            witness.expected_parameter(*key) for key in witness.assignments
                        ]
                        aggregate = n.put(
                            store,
                            "AGGREGATE_PROJECTION",
                            {"authority_id": snapshot["authority"]["id"], "parameters": parameters},
                        )
                        anchor = replace(
                            anchor,
                            aggregate_id=aggregate["id"],
                            aggregate_length=aggregate["length"],
                        )
                        snapshot["anchor"] = asdict(anchor)
                        snapshot["projection_id"] = aggregate["id"]
                        body = n.Witness(anchor, snapshot["authority"], store).expected_apply(
                            parameters
                        )
                    else:
                        prior = n.decode(proof["command_ascii"].encode("ascii"))["payload"]
                        body = witness.expected_parameter(prior["domain"], prior["shard"])
                    bundle["artifacts"] = {k: v.decode("ascii") for k, v in store.items()}
                    proof["command_ascii"] = n.canonical(
                        {"action": event["action_id"], "payload": body}
                    ).decode("ascii")
                    event["body_hash"] = n.digest(n.canonical(body))

                replace_snapshot(event, bundle, change)
                bodies[(event["action_id"], event["vote_context_id"])] = event["body_hash"]
        filename = "coordinate-" + name
        document["trace_id"] = "TRACE-ILLEGAL-" + filename.upper()
        write_canonical_json(ILLEGAL / (filename + ".json"), document)
        write_canonical_json(LEGAL.parent / "native" / (filename + ".json"), bundle)
        cases.append({"fixture": filename + ".json", "reason": reason})

    case("order", "COORDINATE_ORDER", lambda c: c["parameter_schema"]["coordinates"].reverse())
    case(
        "missing-range",
        "COORDINATE_RANGE_ORDER_OR_COVERAGE",
        lambda c: c["parameter_schema"]["ranges"].pop(),
    )
    case(
        "range-order",
        "COORDINATE_RANGE_ORDER_OR_COVERAGE",
        lambda c: c["parameter_schema"]["ranges"].reverse(),
    )
    case(
        "range-overrun",
        "COORDINATE_RANGE_BOUNDS",
        lambda c: c["parameter_schema"]["ranges"][1].update(length=4),
    )
    case(
        "domain-alias",
        "COORDINATE_SHARD_ALIAS",
        lambda c: c["parameter_schema"]["ranges"][2].update(offset=1),
    )

    def adjust_all(c, suffix, **changes):
        for item in c["parameter_schema"]["ranges"]:
            if item["parameter_id"].endswith(suffix):
                item.update(changes)

    case("overlap", "COORDINATE_EXACT_DOMAIN_COVERAGE", lambda c: adjust_all(c, "s01", offset=1))
    case("gap", "COORDINATE_EXACT_DOMAIN_COVERAGE", lambda c: adjust_all(c, "s00", length=1))
    case(
        "duplicate-domain-shard",
        "COORDINATE_DOMAIN_SHARD_DUPLICATE",
        lambda c: c["shard_plan"]["assignments"][1].update(shard_id="s00"),
    )
    case(
        "public-rename",
        "NATIVE_COORDINATE_SCHEMA_BINDING",
        lambda c: c["parameter_schema"]["coordinates"].__setitem__(0, "a0000"),
    )
    case(
        "native-rename",
        "NATIVE_COORDINATE_SCHEMA_BINDING",
        mutate_native=lambda p: p["coordinates"].__setitem__(0, "a0000"),
    )

    def swap_intervals(payload):
        payload["shards"][0]["offset"] = 3
        payload["shards"][1]["offset"] = 0

    case("native-offsets", "NATIVE_COORDINATE_SCHEMA_BINDING", mutate_native=swap_intervals)
    write_canonical_json(LEGAL.parent / "native/negative-expectations.json", cases)
