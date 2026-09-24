"""Synthetic projected journal observations, never an execution attestation."""

from native_durability_witness import (
    ACTIONS,
    EVENT_FIELDS,
    PERSIST_STAGES,
    envelope,
    journal_root,
    n,
    observation_id,
    persisted_bytes,
)


def attach_durability(trace: dict, bundle: dict) -> None:
    bundle["schema_version"] = "1.2.0"
    bundle["operations"] = {}
    journals, saved = {}, {}
    for event in trace["events"]:
        event["durability_witness"] = None
        action, actor, outcome = event["action_id"], event["actor_id"], event["outcome"]
        accepted = outcome in {"ACCEPTED", "FINALIZED"}
        journal = journals.setdefault(actor, [])
        before = list(journal)
        first = saved.get((actor, event["vote_context_id"]))
        proof = event["arithmetic_witness"]
        receipt = effect = None
        stages = []
        if action in ACTIONS and proof:
            if accepted:
                receipt, effect = persisted_bytes(event)
                stages = PERSIST_STAGES[:]
                saved[(actor, event["vote_context_id"])] = (receipt, effect)
            elif outcome == "NO_OP" and first:
                receipt, effect = first
                stages = ["LOOKUP", "EXPOSED"]
            else:
                stages = ["LOOKUP", "REJECTED"]
        elif action == "ACT-JOURNAL-RECOVER" and accepted and any(a == actor for a, _ in saved):
            event["durable_sequence"] = len(before)
            stages = ["READ", "VERIFIED", "RECOVERED"]
        if accepted and action.endswith("-VOTE"):
            journal.append(n.digest(n.canonical(envelope(event))))
        if stages:
            observation = {
                "event": {field: event[field] for field in EVENT_FIELDS},
                "snapshot_id": proof["snapshot_id"] if proof else None,
                "command_ascii": proof["command_ascii"] if proof else None,
                "sequence_before": len(before),
                "sequence_after": len(journal),
                "journal_before": journal_root(before),
                "journal_after": journal_root(journal),
                "receipt_ascii": receipt,
                "effect_ascii": effect,
                "stages": stages,
            }
            identity = observation_id(observation)
            bundle["operations"][identity] = observation
            event["durability_witness"] = identity
