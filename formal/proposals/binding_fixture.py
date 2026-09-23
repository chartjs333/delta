"""Deterministic public design fixture; no secrets or production certificates."""

from dataclasses import asdict, replace

import arithmetic_binding as a
import native_binding as n


def fixture() -> tuple[n.NativeAnchor, dict, dict[str, bytes]]:
    store = {}
    schema = n.put(
        store,
        "SCHEMA",
        {
            "coordinates": ["p0", "p1"],
            "shards": [
                {"id": "s0", "offset": 0, "length": 1},
                {"id": "s1", "offset": 1, "length": 1},
            ],
        },
    )
    profile = n.put(
        store,
        "PROFILE",
        {
            "accumulator_bits": 64,
            "apply_quantum": [1, 1],
            "domain_weights": [
                {"domain": "d0", "weight": [1, 2]},
                {"domain": "d1", "weight": [1, 2]},
            ],
            "learning_rate": [1, 2],
            "momentum": [1, 2],
            "weight_decay": [0, 1],
            "rounding": "HALF_TOWARD_POSITIVE",
            "nesterov": True,
            "output_range": "FULL_SIGNED_INT64",
        },
    )
    model = n.put(store, "MODEL", {"schema": schema, "quantum": [1, 1], "values": [20, -20]})
    optimizer = n.put(store, "OPTIMIZER", {"schema": schema, "quantum": [1, 1], "values": [2, -2]})
    tickets, assignments, commitments = [], [], []
    for domain, values in (("d0", [1, -1]), ("d1", [-1, 1])):
        ticket = "t" + domain[1:]
        tickets.append({"id": ticket, "domain": domain})
        leaves = []
        for index, value in enumerate(values):
            shard = "s" + str(index)
            q = n.put(
                store,
                "Q_SHARD",
                {
                    "ticket": ticket,
                    "domain": domain,
                    "shard": shard,
                    "schema": schema,
                    "quantum": [1, 2],
                    "values": [value],
                },
            )
            leaves.append({"shard": shard, "q": q})
            assignments.append(
                {
                    "domain": domain,
                    "shard": shard,
                    "context": domain + ":" + shard,
                    "denominator": 1,
                    "quantum": [1, 2],
                    "contributions": [{"ticket": ticket, "weight": [1, 1], "q": q}],
                }
            )
        commitments.append({"ticket": ticket, "domain": domain, "leaves": leaves})
    plan = n.put(
        store,
        "PLAN",
        {"schema": schema, "profile": profile, "tickets": tickets, "assignments": assignments},
    )
    isc = n.put(store, "ISC_PROJECTION", {"members": ["t0", "t1"], "commitments": commitments})
    ec = n.put(store, "EC_PROJECTION", {"isc": isc, "eligible": ["t0", "t1"]})
    apc = n.put(store, "APC_PROJECTION", {"ec": ec, "plan": plan})
    root = n.put(
        store,
        "AUTHORITY",
        {
            "context": {
                "round": "round1",
                "height": 1,
                "view": 0,
                "epoch": "epoch1",
                "hard_deadline": 10,
                "parent_checkpoint": "parent1",
            },
            "schema": schema,
            "profile": profile,
            "plan": plan,
            "model": model,
            "optimizer": optimizer,
            "parents": {"isc": isc, "ec": ec, "apc": apc},
        },
    )
    anchor = n.NativeAnchor(
        root["id"],
        a.value_hash("model", (20, -20)),
        a.value_hash("optimizer", (2, -2)),
        "round1",
        1,
        0,
        "epoch1",
        0,
        10,
        "PARAMETER",
        True,
        "parent1",
    )
    witness = n.Witness(anchor, root, store)
    aggregate = n.put(
        store,
        "AGGREGATE_PROJECTION",
        {
            "authority_id": root["id"],
            "parameters": [witness.expected_parameter(*key) for key in witness.assignments],
        },
    )
    anchor = replace(
        anchor, role="APPLY", aggregate_id=aggregate["id"], aggregate_length=aggregate["length"]
    )
    return anchor, root, store


def document() -> dict:
    anchor, root, store = fixture()
    witness = n.Witness(anchor, root, store)
    parameters = [witness.expected_parameter(*key) for key in witness.assignments]
    return {
        "status": "DRAFT_NOT_AUTHORITY",
        "formal_go": False,
        "anchor": asdict(anchor),
        "authority": root,
        "artifacts": {key: value.decode("ascii") for key, value in sorted(store.items())},
        "parameters": parameters,
        "apply": witness.expected_apply(parameters),
    }


if __name__ == "__main__":
    print(n.canonical(document()).decode())
