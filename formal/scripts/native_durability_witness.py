"""Draft offline WAL projection; observations are not native/fsync attestations.

The receipt/effect encoding here is a versioned evidence projection, NOT the C
ABI or production WAL format. Whole-prefix observations require a trace starting
with an empty journal. Recovery authentication and physical crash cuts are open.
"""

from __future__ import annotations

import hashlib

from native_trace_witness import ACTIONS, n

EVENT_FIELDS = (
    "schema_version actor_id actor_role action_id round_id height view validator_epoch "
    "vote_context_id request_id prior_state_root next_state_root logical_time outcome "
    "error_code durable_sequence parent_hashes body_hash result_hash artifact_refs"
).split()
ENVELOPE_FIELDS = (
    "actor_id action_id round_id height validator_epoch vote_context_id parent_hashes body_hash"
).split()
PERSIST_STAGES = ["VALIDATED", "APPENDED", "DURABLE", "COMMITTED", "EXPOSED"]


def observation_id(value: dict) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            b"deltareduce.native-durability-observation.draft1\x00" + n.canonical(value)
        ).hexdigest()
    )


def journal_root(records: list[str]) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            b"deltareduce.vote-journal-projection.draft1\x00" + n.canonical(records)
        ).hexdigest()
    )


def envelope(event: dict) -> dict:
    return {field: event[field] for field in ENVELOPE_FIELDS}


def persisted_bytes(event: dict) -> tuple[str, str]:
    """Canonical diagnostic projection; actual native byte layout remains open."""
    effect = n.canonical({"projection_version": "draft1", "vote": envelope(event)})
    receipt = n.canonical(
        {
            "projection_version": "draft1",
            "vote": envelope(event),
            "sequence": event["durable_sequence"],
            "command_id": n.digest(event["arithmetic_witness"]["command_ascii"].encode("ascii")),
            "effect_id": n.digest(effect),
        }
    )
    return receipt.decode("ascii"), effect.decode("ascii")


def check_durability_trace(trace: dict, evidence) -> dict:
    journals: dict[str, list[str]] = {}
    saved: dict[tuple[str, str], dict] = {}
    recovery: dict[str, str] = {}
    counts = {"persisted": 0, "retried": 0, "conflicts": 0, "recovered": 0}
    for event in trace["events"]:
        action, actor, outcome = event["action_id"], event["actor_id"], event["outcome"]
        accepted = outcome in {"ACCEPTED", "FINALIZED"}
        journal = journals.setdefault(actor, [])
        before = list(journal)
        key = (actor, event["vote_context_id"])
        first = saved.get(key)
        arith = action in ACTIONS
        recovering = (
            action == "ACT-JOURNAL-RECOVER"
            and accepted
            and any(owner == actor for owner, _ in saved)
        )
        if arith or recovering:
            n.require(evidence is not None, "NATIVE_EVIDENCE_REQUIRED")
            observation = evidence.operations.get(event.get("durability_witness"))
            n.require(observation is not None, "DURABILITY_WITNESS_REQUIRED")
            n.shape(
                observation,
                "event snapshot_id command_ascii sequence_before sequence_after "
                "journal_before journal_after receipt_ascii effect_ascii stages",
            )
            n.require(
                n.canonical(observation["event"])
                == n.canonical({field: event[field] for field in EVENT_FIELDS}),
                "DURABILITY_EVENT_BINDING",
            )
            proof = event["arithmetic_witness"]
            n.require(
                observation["snapshot_id"] == (proof["snapshot_id"] if proof else None)
                and observation["command_ascii"] == (proof["command_ascii"] if proof else None),
                "DURABILITY_COMMAND_BINDING",
            )
            n.require(
                n.canonical(observation["sequence_before"]) == n.canonical(len(before))
                and observation["journal_before"] == journal_root(before),
                "DURABILITY_PRIOR_JOURNAL",
            )
            if arith:
                n.require(event["actor_role"] == "VALIDATOR", "NATIVE_EVENT_ROLE")
                n.require(
                    event["result_hash"] is None and event["artifact_refs"] == [],
                    "DURABILITY_UNPROJECTED_EFFECT",
                )
                n.require(proof is not None, "NATIVE_WITNESS_REQUIRED")
                raw = proof["command_ascii"]
                n.require(type(raw) is str and raw.isascii(), "NATIVE_COMMAND_ENCODING")
                command = n.shape(n.decode(raw.encode("ascii")), "action payload")
                n.require(command["action"] == action, "NATIVE_COMMAND_ACTION")
                n.require(
                    n.digest(n.canonical(command["payload"])) == event["body_hash"],
                    "DURABILITY_BODY_BINDING",
                )
                n.require(recovery.get(actor, "READY") == "READY", "DURABILITY_NOT_RECOVERED")
                if accepted:
                    n.require(first is None, "DURABILITY_DUPLICATE_APPEND")
                    n.require(observation["stages"] == PERSIST_STAGES, "DURABILITY_EXPOSE_ORDER")
                    receipt, effect = persisted_bytes(event)
                    n.require(
                        (observation["receipt_ascii"], observation["effect_ascii"])
                        == (receipt, effect),
                        "DURABILITY_PERSISTED_BYTES",
                    )
                    saved[key] = {
                        "command": raw,
                        "snapshot": proof["snapshot_id"],
                        "envelope": envelope(event),
                        "sequence": event["durable_sequence"],
                        "receipt": receipt,
                        "effect": effect,
                    }
                    counts["persisted"] += 1
                else:
                    n.require(first is not None, "DURABILITY_NO_PRIOR_RECORD")
                    n.require(
                        event["next_state_root"] == event["prior_state_root"],
                        "DURABILITY_NOT_STUTTER",
                    )
                    if raw == first["command"]:
                        n.require(
                            outcome == "NO_OP" and event["error_code"] is None,
                            "DURABILITY_RETRY_OUTCOME",
                        )
                        n.require(
                            observation["stages"] == ["LOOKUP", "EXPOSED"],
                            "DURABILITY_RETRY_STAGES",
                        )
                        n.require(
                            proof["snapshot_id"] == first["snapshot"]
                            and envelope(event) == first["envelope"]
                            and event["durable_sequence"] == first["sequence"],
                            "DURABILITY_RETRY_IDENTITY",
                        )
                        n.require(
                            (observation["receipt_ascii"], observation["effect_ascii"])
                            == (first["receipt"], first["effect"]),
                            "DURABILITY_RETRY_BYTES",
                        )
                        counts["retried"] += 1
                    else:
                        # Existing REJECTED + abstract stutter. No new error/status code.
                        n.require(outcome == "REJECTED", "DURABILITY_CONFLICT_OUTCOME")
                        n.require(
                            observation["stages"] == ["LOOKUP", "REJECTED"],
                            "DURABILITY_CONFLICT_STAGES",
                        )
                        n.require(
                            observation["receipt_ascii"] is None
                            and observation["effect_ascii"] is None
                            and event["durable_sequence"] == len(before),
                            "DURABILITY_CONFLICT_EFFECT",
                        )
                        counts["conflicts"] += 1
            else:
                n.require(
                    recovery.get(actor) == "RECOVERING"
                    and proof is None
                    and observation["stages"] == ["READ", "VERIFIED", "RECOVERED"]
                    and observation["receipt_ascii"] is None
                    and observation["effect_ascii"] is None
                    and event["durable_sequence"] == len(before),
                    "DURABILITY_RECOVERY_BINDING",
                )
                counts["recovered"] += 1
        if accepted and action.endswith("-VOTE"):
            n.require(event["durable_sequence"] == len(journal) + 1, "DURABILITY_SEQUENCE_EXACT")
            record_id = n.digest(n.canonical(envelope(event)))
            n.require(record_id not in journal, "DURABILITY_DUPLICATE_ENVELOPE")
            journal.append(record_id)
        if arith or recovering:
            n.require(
                n.canonical(observation["sequence_after"]) == n.canonical(len(journal))
                and observation["journal_after"] == journal_root(journal),
                "DURABILITY_JOURNAL_CHANGED",
            )
        if action == "ACT-CRASH" and (accepted or outcome == "FAULT"):
            recovery[actor] = "CRASHED"
        elif action == "ACT-RESTART" and accepted:
            recovery[actor] = "RECOVERING"
        elif action == "ACT-JOURNAL-RECOVER" and accepted:
            recovery[actor] = "READY"
    return counts
