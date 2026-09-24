"""Draft offline WAL projection; observations are not native/fsync attestations.

The receipt/effect encoding here is a versioned evidence projection, NOT the C
ABI or production WAL format. Whole-prefix observations require a trace starting
with an empty journal. Recovery authentication and physical crash execution are open.
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
UNACKNOWLEDGED_STAGES = [
    ["VALIDATED", "APPENDED", "SURVIVED_UNACKNOWLEDGED"],
    ["VALIDATED", "APPENDED", "BARRIER_FAILED", "SURVIVED_UNACKNOWLEDGED"],
]
UNEXPOSED_STAGES = [PERSIST_STAGES[:3], PERSIST_STAGES[:4], *UNACKNOWLEDGED_STAGES]


def vote_exposed(event: dict, evidence) -> bool:
    """Quorum projection only; the complete observation is checked separately.

    Malformed/missing observations retain the legacy projection so their precise
    native validation error is not masked by a subsequent missing-quorum error.
    No trace can pass without that independent full validation.
    """
    if event["action_id"] not in ACTIONS or evidence is None:
        return True
    observation = evidence.operations.get(event.get("durability_witness"))
    return not isinstance(observation, dict) or observation.get("stages") not in UNEXPOSED_STAGES


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
    must_crash: set[str] = set()
    unacknowledged: set[str] = set()
    counts = {
        "persisted": 0,
        "retried": 0,
        "conflicts": 0,
        "recovered": 0,
        "persisted_unexposed": 0,
        "unacknowledged": 0,
    }
    for event in trace["events"]:
        action, actor, outcome = event["action_id"], event["actor_id"], event["outcome"]
        accepted = outcome in {"ACCEPTED", "FINALIZED"}
        if actor in must_crash:
            n.require(
                action == "ACT-CRASH" and (accepted or outcome == "FAULT"),
                "DURABILITY_CRASH_REQUIRED",
            )
            must_crash.remove(actor)
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
                    stages = observation["stages"]
                    unexposed = stages in UNEXPOSED_STAGES
                    n.require(stages == PERSIST_STAGES or unexposed, "DURABILITY_EXPOSE_ORDER")
                    receipt, effect = persisted_bytes(event)
                    n.require(
                        (observation["receipt_ascii"], observation["effect_ascii"])
                        == ((None, None) if unexposed else (receipt, effect)),
                        "DURABILITY_PERSISTED_BYTES",
                    )
                    if unexposed:
                        must_crash.add(actor)
                        counts["persisted_unexposed"] += 1
                    if stages in UNACKNOWLEDGED_STAGES:
                        unacknowledged.add(actor)
                        counts["unacknowledged"] += 1
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
                unacknowledged.discard(actor)
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
    # An unacknowledged write cannot establish record presence on its own. The
    # retrospective projection needs the subsequent verified complete prefix.
    n.require(not unacknowledged, "DURABILITY_UNACKNOWLEDGED_UNVERIFIED")
    return counts
