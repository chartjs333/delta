"""Synthetic fixture producer. Its snapshots are not runtime attestations."""

from __future__ import annotations

from dataclasses import asdict, replace

from native_trace_witness import ACTIONS, n, snapshot_id


def attach_fixture_witnesses(trace: dict) -> dict:
    """Bind supplied trace events to deterministic fixture-only native snapshots."""
    store: dict[str, bytes] = {}
    snapshots = {}
    contract = trace["round_contract"]
    assignments = contract["shard_plan"]["assignments"]
    domains = contract["round_config"]["domain_ids"]
    shards = sorted({item["shard_id"] for item in assignments})
    schema = n.put(
        store,
        "SCHEMA",
        {
            "coordinates": [f"p{i:04}" for i in range(len(shards))],
            "shards": [{"id": shard, "offset": i, "length": 1} for i, shard in enumerate(shards)],
        },
    )
    profile = n.put(
        store,
        "PROFILE",
        {
            "accumulator_bits": 64,
            "apply_quantum": [1, 1],
            "domain_weights": [{"domain": d, "weight": [1, len(domains)]} for d in domains],
            "learning_rate": [1, 2],
            "momentum": [1, 2],
            "weight_decay": [0, 1],
            "rounding": "HALF_TOWARD_POSITIVE",
            "nesterov": True,
            "output_range": "FULL_SIGNED_INT64",
        },
    )
    model_values = [20 if i % 2 == 0 else -20 for i in range(len(shards))]
    optimizer_values = [2 if i % 2 == 0 else -2 for i in range(len(shards))]
    model = n.put(store, "MODEL", {"schema": schema, "quantum": [1, 1], "values": model_values})
    optimizer = n.put(
        store, "OPTIMIZER", {"schema": schema, "quantum": [1, 1], "values": optimizer_values}
    )
    tickets, plans, commitments = [], [], []
    by_key = {(a["domain_id"], a["shard_id"]): a for a in assignments}
    for di, domain in enumerate(domains):
        ticket = f"t{di:04}"
        tickets.append({"id": ticket, "domain": domain})
        leaves = []
        for si, shard in enumerate(shards):
            q = n.put(
                store,
                "Q_SHARD",
                {
                    "ticket": ticket,
                    "domain": domain,
                    "shard": shard,
                    "schema": schema,
                    "quantum": [1, 2],
                    "values": [1 if (di + si) % 2 == 0 else -1],
                },
            )
            leaves.append({"shard": shard, "q": q})
            plans.append(
                {
                    "domain": domain,
                    "shard": shard,
                    "context": by_key[(domain, shard)]["vote_context_id"],
                    "denominator": 1,
                    "quantum": [1, 2],
                    "contributions": [{"ticket": ticket, "weight": [1, 1], "q": q}],
                }
            )
        commitments.append({"ticket": ticket, "domain": domain, "leaves": leaves})
    plan = n.put(
        store,
        "PLAN",
        {"schema": schema, "profile": profile, "tickets": tickets, "assignments": plans},
    )
    members = [t["id"] for t in tickets]
    isc = n.put(store, "ISC_PROJECTION", {"members": members, "commitments": commitments})
    ec = n.put(store, "EC_PROJECTION", {"isc": isc, "eligible": members})
    apc = n.put(store, "APC_PROJECTION", {"ec": ec, "plan": plan})
    # Each event's native context is fixed before checking the command. A real
    # exporter must recover these values independently; this function is fixtures only.
    parent_certificates = {}
    rewritten = {}
    sequences = {}
    for event in trace["events"]:
        event.setdefault("arithmetic_witness", None)
        action = event["action_id"]
        if action.endswith("-VOTE") and event["outcome"] in {"ACCEPTED", "FINALIZED"}:
            actor = event["actor_id"]
            sequences[actor] = sequences.get(actor, 0) + 1
            event["durable_sequence"] = sequences[actor]
        if action == "ACT-APC-FINALIZE":
            parent_certificates["ACT-PARAM-VOTE"] = event["result_hash"]
        if action == "ACT-ROOT-FINALIZE":
            parent_certificates["ACT-APPLY-VOTE"] = event["result_hash"]
        if action in ACTIONS and event["outcome"] in {"ACCEPTED", "FINALIZED"}:
            match = next(
                (a for a in assignments if a["vote_context_id"] == event["vote_context_id"]), None
            )
            if action == "ACT-PARAM-VOTE" and match is None:
                continue  # Deliberately invalid legacy fixtures fail the graph check first.
            root = n.put(
                store,
                "AUTHORITY",
                {
                    "context": {
                        "round": event["round_id"],
                        "height": event["height"],
                        "view": event["view"],
                        "epoch": event["validator_epoch"],
                        "hard_deadline": 100000,
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
                n.arithmetic.value_hash("model", tuple(model_values)),
                n.arithmetic.value_hash("optimizer", tuple(optimizer_values)),
                event["round_id"],
                event["height"],
                event["view"],
                event["validator_epoch"],
                event["logical_time"],
                100000,
                "PARAMETER",
                True,
                "parent1",
            )
            witness = n.Witness(anchor, root, store)
            parameters = [witness.expected_parameter(*key) for key in witness.assignments]
            aggregate = n.put(
                store,
                "AGGREGATE_PROJECTION",
                {"authority_id": root["id"], "parameters": parameters},
            )
            if action == "ACT-APPLY-VOTE":
                anchor = replace(
                    anchor,
                    role="APPLY",
                    aggregate_id=aggregate["id"],
                    aggregate_length=aggregate["length"],
                )
                body = n.Witness(anchor, root, store).expected_apply(parameters)
                projection = aggregate["id"]
            else:
                body = witness.expected_parameter(match["domain_id"], match["shard_id"])
                projection = apc["id"]
            parent = parent_certificates.get(action, "sha256:" + "0" * 64)
            snapshot = {
                "actor_id": event["actor_id"],
                "action_id": action,
                "prior_state_root": event["prior_state_root"],
                "round_contract_id": contract["contract_id"],
                "vote_context_id": event["vote_context_id"],
                "durable_sequence": event["durable_sequence"],
                "current_checkpoint": "parent1",
                "parent_certificate": parent,
                "projection_id": projection,
                "anchor": asdict(anchor),
                "authority": root,
            }
            identity = snapshot_id(snapshot)
            snapshots[identity] = snapshot
            event["arithmetic_witness"] = {
                "snapshot_id": identity,
                "command_ascii": n.canonical({"action": action, "payload": body}).decode("ascii"),
            }
            event["body_hash"] = n.digest(n.canonical(body))
            event["parent_hashes"] = [parent]
            rewritten[(action, event["vote_context_id"])] = event["body_hash"]
        elif action in {"ACT-PARAM-FINALIZE", "ACT-APPLY-FINALIZE"}:
            event["body_hash"] = rewritten.get(
                (action.replace("FINALIZE", "VOTE"), event["vote_context_id"]), event["body_hash"]
            )
    return {
        "schema_version": "1.0.0",
        "snapshots": snapshots,
        "artifacts": {key: value.decode("ascii") for key, value in sorted(store.items())},
    }
