#!/usr/bin/env python3
"""Standalone validator for canonical DeltaReduce action-labelled traces."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import (  # noqa: E402
    canonical_json_bytes,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    load_json_strict,
    validate_trace_document,
    write_canonical_json,
)


QUORUM = 3
FINALIZE_TO_VOTE = {
    "ACT-CONFIG-FINALIZE": "ACT-CONFIG-VOTE",
    "ACT-ISC-FINALIZE": "ACT-ISC-VOTE",
    "ACT-EC-FINALIZE": "ACT-EC-VOTE",
    "ACT-APC-FINALIZE": "ACT-APC-VOTE",
    "ACT-PARAM-FINALIZE": "ACT-PARAM-VOTE",
    "ACT-ROOT-FINALIZE": "ACT-ROOT-VOTE",
    "ACT-APPLY-FINALIZE": "ACT-APPLY-VOTE",
    "ACT-VIEW-FINALIZE": "ACT-VIEW-VOTE",
    "ACT-ABORT-FINALIZE": "ACT-ABORT-VOTE",
}
VOTE_ACTIONS = set(FINALIZE_TO_VOTE.values())
FAULT_PROGRESS_ACTIONS = {
    "ACT-ABORT-VOTE",
    "ACT-ABORT-FINALIZE",
    "ACT-CRASH",
    "ACT-RESTART",
    "ACT-JOURNAL-RECOVER",
    "ACT-MESSAGE-ENQUEUE",
    "ACT-MESSAGE-DELIVER",
    "ACT-MESSAGE-DROP",
    "ACT-MESSAGE-DUPLICATE",
    "ACT-MESSAGE-REPLAY",
    "ACT-PARTITION-ENABLE",
    "ACT-PARTITION-HEAL",
    "ACT-LOGICAL-TIME-ADVANCE",
}
UNSAFE_ARITHMETIC_CODES = {
    "ARITHMETIC_OVERFLOW",
    "ARITHMETIC_SATURATION",
    "ARITHMETIC_UNCHECKED",
}


class RefinementError(ValueError):
    """An implementation trace cannot refine the frozen formal transition relation."""

    def __init__(self, reason: str, detail: str):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


def fail(reason: str, detail: str) -> None:
    raise RefinementError(reason, detail)


def event_identity(event: dict[str, Any]) -> str:
    return event["result_hash"] or event["body_hash"] or event["next_state_root"]


def verify_quorum(
    event: dict[str, Any],
    votes: dict[tuple[str, str, str, str], set[str]],
) -> None:
    vote_action = FINALIZE_TO_VOTE[event["action_id"]]
    context = event["vote_context_id"]
    body = event["body_hash"]
    if context is None or body is None:
        fail("QC_CONTEXT_MISSING", event["action_id"])
    key = (vote_action, event["round_id"], context, body)
    if len(votes[key]) < QUORUM:
        fail(
            "QC_QUORUM_MISSING",
            f"{event['action_id']} has {len(votes[key])} unique matching votes",
        )


def check_trace(path: Path) -> dict[str, Any]:
    trace = load_json_strict(path)
    validate_trace_document(trace, ROOT)
    if path.read_bytes().removesuffix(b"\n") != canonical_json_bytes(trace):
        fail("NONCANONICAL_TRACE", str(path))

    expected_semantics = derive_formal_semantics_id(
        "1.0.0", discover_semantic_artifacts(ROOT)
    )
    if trace["formal_semantics_id"] != expected_semantics:
        fail("FORMAL_SEMANTICS_MISMATCH", trace["trace_id"])

    votes: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    durable_votes: dict[tuple[str, str], str] = {}
    commitments: dict[tuple[str, str], str] = {}
    isc_body_by_round: dict[str, str] = {}
    isc_members_by_result: dict[str, set[str]] = {}
    isc_results: set[str] = set()
    apc_results: set[str] = set()
    parameter_results_by_context: dict[str, list[str]] = defaultdict(list)
    aggregate_results: set[str] = set()
    apply_results: set[str] = set()
    certified_objects: set[str] = set()
    validator_recovery: dict[str, str] = defaultdict(lambda: "READY")
    hard_deadline_reached = False
    current_advanced = False
    valid_abort = False
    last_logical_time = -1

    for index, event in enumerate(trace["events"]):
        action = event["action_id"]
        actor = event["actor_id"]
        context = event["vote_context_id"]
        body = event["body_hash"]
        outcome = event["outcome"]
        accepted = outcome in {"ACCEPTED", "FINALIZED"}

        if event["logical_time"] < last_logical_time:
            fail("LOGICAL_TIME_REGRESSION", f"event {index}")
        last_logical_time = event["logical_time"]

        if hard_deadline_reached and accepted and action not in FAULT_PROGRESS_ACTIONS:
            fail("PROGRESS_AFTER_HARD_DEADLINE", action)
        if (
            action == "ACT-LOGICAL-TIME-ADVANCE"
            and event["error_code"] == "HARD_DEADLINE_REACHED"
        ):
            hard_deadline_reached = True

        if accepted and event["error_code"] in UNSAFE_ARITHMETIC_CODES:
            fail("UNCHECKED_ARITHMETIC_ACCEPTED", action)

        if action in VOTE_ACTIONS and accepted:
            if actor is None or context is None or body is None:
                fail("VOTE_CONTEXT_MISSING", f"event {index}")
            if validator_recovery[actor] == "RECOVERING":
                fail("VOTE_BEFORE_JOURNAL_RECOVERY", actor)
            durable_key = (actor, context)
            prior_body = durable_votes.get(durable_key)
            if prior_body is not None and prior_body != body:
                fail("CONFLICTING_DURABLE_VOTE", f"{actor}:{context}")
            durable_votes[durable_key] = body
            votes[(action, event["round_id"], context, body)].add(actor)

        if action in FINALIZE_TO_VOTE and accepted:
            if action == "ACT-ISC-FINALIZE":
                previous = isc_body_by_round.get(event["round_id"])
                if previous is not None and previous != body:
                    fail("ISC_MEMBERSHIP_MUTATION", event["round_id"])
            verify_quorum(event, votes)

        if action == "ACT-COMMIT" and accepted:
            if event["request_id"] is None or body is None:
                fail("COMMITMENT_CONTEXT_MISSING", f"event {index}")
            key = (event["round_id"], event["request_id"])
            previous = commitments.get(key)
            if previous is not None and previous != body:
                fail("COMMITMENT_REPLACEMENT", event["request_id"])
            commitments[key] = body

        if action == "ACT-ISC-FINALIZE" and accepted:
            isc_body_by_round[event["round_id"]] = body
            result = event_identity(event)
            members = set(event["artifact_refs"])
            isc_results.add(result)
            isc_members_by_result[result] = members
            certified_objects.add(result)

        if action == "ACT-SEED-GENERATE" and accepted:
            if not (set(event["parent_hashes"]) & isc_results):
                fail("SEED_WITHOUT_FINALIZED_ISC", f"event {index}")

        if action in {"ACT-EC-FINALIZE", "ACT-APC-FINALIZE"} and accepted:
            parent_iscs = set(event["parent_hashes"]) & isc_results
            if not parent_iscs:
                fail("EC_APC_WITHOUT_ISC_PARENT", action)
            permitted = set().union(
                *(isc_members_by_result[parent] for parent in parent_iscs)
            )
            if not set(event["artifact_refs"]) <= permitted:
                fail("EC_APC_NON_ISC_MEMBER", action)
            result = event_identity(event)
            certified_objects.add(result)
            if action == "ACT-APC-FINALIZE":
                apc_results.add(result)

        if action == "ACT-PARAM-FINALIZE" and accepted:
            if not (set(event["parent_hashes"]) & apc_results):
                fail("PARAMETER_QC_WRONG_PARENT", context or f"event-{index}")
            result = event_identity(event)
            parameter_results_by_context[context].append(result)
            certified_objects.add(result)

        if action == "ACT-ROOT-ASSEMBLE" and accepted:
            expected = {
                result
                for results in parameter_results_by_context.values()
                for result in results
            }
            exactly_one_per_key = all(
                len(results) == 1
                for results in parameter_results_by_context.values()
            )
            if not expected or set(event["artifact_refs"]) != expected:
                fail("AGGREGATE_INCOMPLETE_COVERAGE", f"event {index}")
            if not exactly_one_per_key:
                fail("AGGREGATE_DUPLICATE_COVERAGE", f"event {index}")

        if action == "ACT-ROOT-FINALIZE" and accepted:
            result = event_identity(event)
            aggregate_results.add(result)
            certified_objects.add(result)

        if action == "ACT-APPLY-FINALIZE" and accepted:
            if not (set(event["parent_hashes"]) & aggregate_results):
                fail("APPLY_QC_WRONG_PARENT", f"event {index}")
            result = event_identity(event)
            apply_results.add(result)
            certified_objects.add(result)

        if action == "ACT-CURRENT-ADVANCE" and accepted:
            if not (set(event["parent_hashes"]) & apply_results):
                fail("CURRENT_WITHOUT_APPLY_QC", f"event {index}")
            current_advanced = True

        if action == "ACT-PUBLISH" and accepted:
            if (
                event["error_code"] in {"LOCAL_PARTIAL_PUBLICATION", "PARTIAL_PUBLICATION"}
                or not event["artifact_refs"]
                or not set(event["artifact_refs"]) <= certified_objects
            ):
                fail("PARTIAL_OR_UNCERTIFIED_PUBLICATION", f"event {index}")

        if action == "ACT-CRASH" and actor is not None:
            validator_recovery[actor] = "CRASHED"
        elif action == "ACT-RESTART" and actor is not None:
            if validator_recovery[actor] != "CRASHED":
                fail("RESTART_WITHOUT_CRASH", actor)
            validator_recovery[actor] = "RECOVERING"
        elif action == "ACT-JOURNAL-RECOVER" and actor is not None:
            if validator_recovery[actor] != "RECOVERING":
                fail("JOURNAL_RECOVERY_OUT_OF_ORDER", actor)
            validator_recovery[actor] = "READY"

        if action == "ACT-ABORT-FINALIZE" and accepted:
            valid_abort = True

    if trace["terminal_outcome"] == "APPLIED" and not current_advanced:
        fail("APPLIED_WITHOUT_CURRENT_ADVANCE", trace["trace_id"])
    if trace["terminal_outcome"] == "ABORTED" and not valid_abort:
        fail("ABORTED_WITHOUT_ABORT_QC", trace["trace_id"])

    return {
        "trace_id": trace["trace_id"],
        "events": len(trace["events"]),
        "terminal_outcome": trace["terminal_outcome"],
        "status": "PASS",
    }


def check_all_fixtures() -> dict[str, Any]:
    legal_paths = sorted((ROOT / "formal" / "fixtures" / "traces" / "legal").glob("*.json"))
    illegal_paths = sorted((ROOT / "formal" / "fixtures" / "traces" / "illegal").glob("*.json"))
    if len(legal_paths) < 5:
        raise RuntimeError("at least five legal behavior fixtures are required")
    if len(illegal_paths) < 14:
        raise RuntimeError("all fourteen mandatory illegal fixtures are required")

    legal = [check_trace(path) for path in legal_paths]
    illegal: list[dict[str, Any]] = []
    for path in illegal_paths:
        try:
            check_trace(path)
        except RefinementError as error:
            illegal.append(
                {"fixture": path.name, "reason": error.reason, "status": "PASS"}
            )
        else:
            raise RuntimeError(f"illegal fixture unexpectedly refined: {path.name}")
    return {
        "schema_version": "1.0.0",
        "status": "PASS",
        "formal_semantics_id": derive_formal_semantics_id(
            "1.0.0", discover_semantic_artifacts(ROOT)
        ),
        "legal_fixture_count": len(legal),
        "illegal_fixture_count": len(illegal),
        "legal": legal,
        "illegal": illegal,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", nargs="?", type=Path)
    parser.add_argument("--all-fixtures", action="store_true")
    arguments = parser.parse_args()
    if arguments.all_fixtures:
        result = check_all_fixtures()
        write_canonical_json(
            ROOT / "formal" / "reports" / "refinement-evidence.json", result
        )
    elif arguments.trace is not None:
        result = check_trace(arguments.trace)
    else:
        parser.error("provide TRACE or --all-fixtures")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "status": "FAIL",
                    "error": f"{type(error).__name__}:{error}",
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        sys.exit(1)
