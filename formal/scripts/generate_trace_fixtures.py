#!/usr/bin/env python3
"""Generate canonical legal and mandatory-negative refinement fixtures."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import (  # noqa: E402
    canonical_json_bytes,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    load_json_strict,
    write_canonical_json,
)


LEGAL = ROOT / "formal" / "fixtures" / "traces" / "legal"
ILLEGAL = ROOT / "formal" / "fixtures" / "traces" / "illegal"
SEMANTICS_ID = derive_formal_semantics_id(
    "1.0.0", discover_semantic_artifacts(ROOT)
)


def cid(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def content_id(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


DEFAULT_ASSIGNMENTS = [
    {
        "parameter_id": "parameter-1",
        "domain_id": "d1",
        "shard_id": "s1",
        "vote_context_id": "NORMAL-PARAM-D1-S1:round-1",
    },
    {
        "parameter_id": "parameter-2",
        "domain_id": "d1",
        "shard_id": "s2",
        "vote_context_id": "NORMAL-PARAM-D1-S2:round-1",
    },
]


def build_round_contract(
    assignments: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    exact_assignments = assignments or DEFAULT_ASSIGNMENTS
    exact_assignments = sorted(
        exact_assignments,
        key=lambda item: (
            item["parameter_id"],
            item["domain_id"],
            item["shard_id"],
            item["vote_context_id"],
        ),
    )
    parameter_ids = sorted(item["parameter_id"] for item in exact_assignments)
    domain_ids = sorted({item["domain_id"] for item in exact_assignments})
    schema_payload = {"parameter_ids": parameter_ids}
    plan_payload = {"assignments": exact_assignments}
    parameter_schema = {
        "schema_hash": content_id(schema_payload),
        "parameter_ids": parameter_ids,
    }
    shard_plan = {
        "plan_hash": content_id(plan_payload),
        "assignments": exact_assignments,
    }
    config_payload = {
        "domain_ids": domain_ids,
        "parameter_schema_hash": parameter_schema["schema_hash"],
        "shard_plan_hash": shard_plan["plan_hash"],
    }
    round_config = {"body_hash": content_id(config_payload), **config_payload}
    contract_payload = {
        "round_id": "round-1",
        "round_config": round_config,
        "parameter_schema": parameter_schema,
        "shard_plan": shard_plan,
    }
    return {"contract_id": content_id(contract_payload), **contract_payload}


DEFAULT_ROUND_CONTRACT = build_round_contract()
ROUND_CONFIG_HASH = DEFAULT_ROUND_CONTRACT["round_config"]["body_hash"]


def make_event(
    action: str,
    *,
    actor: str | None = "validator-1",
    role: str | None = "VALIDATOR",
    body: str | None = None,
    result: str | None = None,
    context: str | None = None,
    parents: list[str] | None = None,
    artifacts: list[str] | None = None,
    request: str | None = None,
    outcome: str = "ACCEPTED",
    error: str | None = None,
    durable: int | None = None,
    view: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "action_id": action,
        "round_id": "round-1",
        "height": 1,
        "view": view,
        "validator_epoch": "epoch-1",
        "actor_id": actor,
        "actor_role": role,
        "request_id": request,
        "vote_context_id": context,
        "parent_hashes": parents or [],
        "body_hash": body,
        "result_hash": result,
        "prior_state_root": cid("pending-prior"),
        "next_state_root": cid("pending-next"),
        "durable_sequence": durable,
        "logical_time": 0,
        "outcome": outcome,
        "error_code": error,
        "artifact_refs": artifacts or [],
    }


def vote_events(action: str, body: str, context: str, *, view: int = 0) -> list[dict[str, Any]]:
    return [
        make_event(
            action,
            actor=f"validator-{number}",
            body=body,
            context=context,
            durable=number,
            view=view,
        )
        for number in (1, 2, 3)
    ]


def qc_events(
    vote_action: str,
    finalize_action: str,
    label: str,
    *,
    parents: list[str] | None = None,
    artifacts: list[str] | None = None,
    body_hash: str | None = None,
    vote_context: str | None = None,
    view: int = 0,
) -> tuple[list[dict[str, Any]], str, str]:
    body = body_hash or cid(label + "-body")
    result = cid(label + "-qc")
    context = vote_context or label.upper() + ":round-1"
    events = vote_events(vote_action, body, context, view=view)
    events.append(
        make_event(
            finalize_action,
            body=body,
            result=result,
            context=context,
            parents=parents,
            artifacts=artifacts,
            outcome="FINALIZED",
            view=view,
        )
    )
    return events, body, result


def trace(
    trace_id: str,
    events: list[dict[str, Any]],
    terminal: str = "IN_PROGRESS",
    round_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    initial = cid(trace_id + ":state:0")
    prior = initial
    for index, event in enumerate(events, start=1):
        next_root = cid(f"{trace_id}:state:{index}")
        event["prior_state_root"] = prior
        event["next_state_root"] = next_root
        event["logical_time"] = index - 1
        prior = next_root
    return {
        "schema_version": "1.0.0",
        "formal_semantics_id": SEMANTICS_ID,
        "trace_id": trace_id,
        "abstraction_version": "1.0.0",
        "round_contract": round_contract or DEFAULT_ROUND_CONTRACT,
        "initial_state_root": initial,
        "terminal_state_root": prior,
        "terminal_outcome": terminal,
        "events": events,
    }


def valid_isc(label: str = "isc") -> tuple[list[dict[str, Any]], str, list[str]]:
    members = [cid(label + "-ticket-1"), cid(label + "-ticket-2")]
    events, _body, result = qc_events(
        "ACT-ISC-VOTE", "ACT-ISC-FINALIZE", label, artifacts=members
    )
    return events, result, members


def valid_apc(label: str = "apc") -> tuple[list[dict[str, Any]], str]:
    isc_events, isc_result, members = valid_isc(label + "-isc")
    apc_events, _body, apc_result = qc_events(
        "ACT-APC-VOTE",
        "ACT-APC-FINALIZE",
        label,
        parents=[isc_result],
        artifacts=members,
    )
    return [*isc_events, *apc_events], apc_result


def write_fixture(directory: Path, name: str, document: dict[str, Any]) -> None:
    write_canonical_json(directory / f"{name}.json", document)


def generate_legal() -> None:
    events: list[dict[str, Any]] = [
        make_event("ACT-CONFIG-PROPOSE", body=ROUND_CONFIG_HASH, request="config-1")
    ]
    config_events, _config_body, _config_qc = qc_events(
        "ACT-CONFIG-VOTE",
        "ACT-CONFIG-FINALIZE",
        "normal-config",
        body_hash=ROUND_CONFIG_HASH,
    )
    events.extend(config_events)
    isc_events, isc_result, members = valid_isc("normal-isc")
    events.extend(isc_events)
    events.append(
        make_event(
            "ACT-SEED-GENERATE",
            body=cid("normal-seed"),
            result=cid("normal-seed-result"),
            parents=[isc_result],
        )
    )
    ec_events, _ec_body, ec_result = qc_events(
        "ACT-EC-VOTE",
        "ACT-EC-FINALIZE",
        "normal-ec",
        parents=[isc_result],
        artifacts=members,
    )
    events.extend(ec_events)
    apc_events, _apc_body, apc_result = qc_events(
        "ACT-APC-VOTE",
        "ACT-APC-FINALIZE",
        "normal-apc",
        parents=[isc_result, ec_result],
        artifacts=members,
    )
    events.extend(apc_events)
    parameter_results: list[str] = []
    for key in ("d1-s1", "d1-s2"):
        parameter_events, _parameter_body, parameter_result = qc_events(
            "ACT-PARAM-VOTE",
            "ACT-PARAM-FINALIZE",
            "normal-param-" + key,
            parents=[apc_result],
        )
        events.extend(parameter_events)
        parameter_results.append(parameter_result)
    root_body = cid("normal-root-body")
    events.append(
        make_event(
            "ACT-ROOT-ASSEMBLE",
            body=root_body,
            artifacts=parameter_results,
        )
    )
    root_events, _root_vote_body, root_result = qc_events(
        "ACT-ROOT-VOTE", "ACT-ROOT-FINALIZE", "normal-root"
    )
    events.extend(root_events)
    apply_events, _apply_body, apply_result = qc_events(
        "ACT-APPLY-VOTE",
        "ACT-APPLY-FINALIZE",
        "normal-apply",
        parents=[root_result],
    )
    events.extend(apply_events)
    events.append(
        make_event(
            "ACT-CURRENT-ADVANCE",
            body=cid("normal-current"),
            result=cid("normal-checkpoint"),
            parents=[apply_result],
            outcome="FINALIZED",
        )
    )
    write_fixture(
        LEGAL,
        "normal-apply",
        trace("TRACE-NORMAL-APPLY", events, "APPLIED"),
    )

    view_events = [
        make_event("ACT-TIMEOUT-SOFT", body=cid("timeout-observation"))
    ]
    view_qc, _view_body, _view_result = qc_events(
        "ACT-VIEW-VOTE", "ACT-VIEW-FINALIZE", "view-change", view=0
    )
    view_events.extend(view_qc)
    write_fixture(
        LEGAL,
        "view-change",
        trace("TRACE-VIEW-CHANGE", view_events),
    )

    artifact = cid("repair-artifact")
    repair_events = [
        make_event(
            "ACT-ARTIFACT-LOSE",
            actor="storage-1",
            role="STORAGE",
            body=artifact,
            artifacts=[artifact],
            outcome="FAULT",
            error="ARTIFACT_UNAVAILABLE",
        ),
        make_event(
            "ACT-ARTIFACT-REPAIR",
            actor="storage-2",
            role="STORAGE",
            body=artifact,
            result=artifact,
            artifacts=[artifact],
        ),
    ]
    write_fixture(LEGAL, "artifact-repair", trace("TRACE-ARTIFACT-REPAIR", repair_events))

    abort_events = [
        make_event(
            "ACT-LOGICAL-TIME-ADVANCE",
            actor=None,
            role="SYSTEM",
            error="HARD_DEADLINE_REACHED",
        )
    ]
    abort_qc, _abort_body, _abort_result = qc_events(
        "ACT-ABORT-VOTE", "ACT-ABORT-FINALIZE", "hard-abort"
    )
    abort_events.extend(abort_qc)
    write_fixture(
        LEGAL,
        "certified-abort",
        trace("TRACE-CERTIFIED-ABORT", abort_events, "ABORTED"),
    )

    root_qc, _root_body, root_result = qc_events(
        "ACT-ROOT-VOTE", "ACT-ROOT-FINALIZE", "recovery-root"
    )
    apply_qc, _apply_body, apply_result = qc_events(
        "ACT-APPLY-VOTE",
        "ACT-APPLY-FINALIZE",
        "recovery-apply",
        parents=[root_result],
    )
    recovery_events = [
        *root_qc,
        *apply_qc,
        make_event(
            "ACT-CRASH",
            actor="validator-1",
            error="CRASH_AFTER_APPLY_QC",
            outcome="FAULT",
        ),
        make_event("ACT-RESTART", actor="validator-1"),
        make_event("ACT-JOURNAL-RECOVER", actor="validator-1"),
        make_event(
            "ACT-CURRENT-ADVANCE",
            body=cid("recovery-current"),
            result=cid("recovery-checkpoint"),
            parents=[apply_result],
            outcome="FINALIZED",
        ),
        make_event(
            "ACT-CURRENT-ADVANCE",
            body=cid("recovery-current"),
            result=cid("recovery-checkpoint"),
            parents=[apply_result],
            outcome="NO_OP",
        ),
    ]
    write_fixture(
        LEGAL,
        "applyqc-pointer-recovery",
        trace("TRACE-APPLYQC-POINTER-RECOVERY", recovery_events, "APPLIED"),
    )

    for existing in LEGAL.glob("config-*.json"):
        document = load_json_strict(existing)
        document["formal_semantics_id"] = SEMANTICS_ID
        document["round_contract"] = DEFAULT_ROUND_CONTRACT
        for event in document["events"]:
            if event["action_id"].startswith("ACT-CONFIG-"):
                event["body_hash"] = ROUND_CONFIG_HASH
        write_canonical_json(existing, document)


def generate_illegal() -> None:
    vote_a = make_event(
        "ACT-CONFIG-VOTE", body=cid("vote-a"), context="CONFIG:1", durable=1
    )
    vote_b = make_event(
        "ACT-CONFIG-VOTE", body=cid("vote-b"), context="CONFIG:1", durable=2
    )
    write_fixture(
        ILLEGAL,
        "conflicting-durable-vote",
        trace("TRACE-ILLEGAL-CONFLICTING-DURABLE-VOTE", [vote_a, vote_b]),
    )

    commits = [
        make_event(
            "ACT-COMMIT",
            actor="worker-1",
            role="WORKER",
            request="ticket-1",
            body=cid("commit-a"),
        ),
        make_event(
            "ACT-COMMIT",
            actor="worker-2",
            role="WORKER",
            request="ticket-1",
            body=cid("commit-b"),
        ),
    ]
    write_fixture(
        ILLEGAL,
        "commitment-replacement",
        trace("TRACE-ILLEGAL-COMMITMENT-REPLACEMENT", commits),
    )

    write_fixture(
        ILLEGAL,
        "seed-without-isc",
        trace(
            "TRACE-ILLEGAL-SEED-WITHOUT-ISC",
            [make_event("ACT-SEED-GENERATE", body=cid("early-seed"))],
        ),
    )

    isc_events, _isc_result, _members = valid_isc("mutable-isc-a")
    second_body = cid("mutable-isc-b-body")
    isc_events.append(
        make_event(
            "ACT-ISC-FINALIZE",
            body=second_body,
            result=cid("mutable-isc-b-qc"),
            context="MUTABLE-ISC-B:round-1",
            outcome="FINALIZED",
        )
    )
    write_fixture(
        ILLEGAL,
        "mutable-isc",
        trace("TRACE-ILLEGAL-MUTABLE-ISC", isc_events),
    )

    for kind in ("ec", "apc"):
        base_events, isc_result, members = valid_isc("bad-member-" + kind)
        vote_action = "ACT-EC-VOTE" if kind == "ec" else "ACT-APC-VOTE"
        final_action = "ACT-EC-FINALIZE" if kind == "ec" else "ACT-APC-FINALIZE"
        bad_events, _body, _result = qc_events(
            vote_action,
            final_action,
            "bad-member-" + kind,
            parents=[isc_result],
            artifacts=[*members, cid("not-in-isc")],
        )
        write_fixture(
            ILLEGAL,
            kind + "-non-isc-member",
            trace(
                "TRACE-ILLEGAL-" + kind.upper() + "-NON-ISC-MEMBER",
                [*base_events, *bad_events],
            ),
        )

    wrong_parent_votes, body, result = qc_events(
        "ACT-PARAM-VOTE",
        "ACT-PARAM-FINALIZE",
        "wrong-parent-param",
        parents=[cid("wrong-apc")],
    )
    write_fixture(
        ILLEGAL,
        "parameter-wrong-parent",
        trace("TRACE-ILLEGAL-PARAMETER-WRONG-PARENT", wrong_parent_votes),
    )

    incomplete_preamble, incomplete_apc = valid_apc("incomplete-root")
    incomplete_parameter, _body, incomplete_result = qc_events(
        "ACT-PARAM-VOTE",
        "ACT-PARAM-FINALIZE",
        "normal-param-d1-s1",
        parents=[incomplete_apc],
    )
    write_fixture(
        ILLEGAL,
        "incomplete-aggregate",
        trace(
            "TRACE-ILLEGAL-INCOMPLETE-AGGREGATE",
            [
                *incomplete_preamble,
                *incomplete_parameter,
                make_event(
                    "ACT-ROOT-ASSEMBLE",
                    body=cid("incomplete-root"),
                    artifacts=[incomplete_result],
                ),
            ],
        ),
    )

    apc_preamble, apc_result = valid_apc("duplicate-root")
    duplicate_events: list[dict[str, Any]] = list(apc_preamble)
    duplicate_results: list[str] = []
    for suffix in ("a", "b"):
        param_events, _param_body, param_result = qc_events(
            "ACT-PARAM-VOTE",
            "ACT-PARAM-FINALIZE",
            "duplicate-key",
            parents=[apc_result],
        )
        if suffix == "b":
            param_events[-1]["result_hash"] = cid("duplicate-key-qc-b")
            param_result = cid("duplicate-key-qc-b")
        duplicate_events.extend(param_events)
        duplicate_results.append(param_result)
    duplicate_events.append(
        make_event(
            "ACT-ROOT-ASSEMBLE",
            body=cid("duplicate-root"),
            artifacts=duplicate_results,
        )
    )
    write_fixture(
        ILLEGAL,
        "duplicate-aggregate",
        trace(
            "TRACE-ILLEGAL-DUPLICATE-AGGREGATE",
            duplicate_events,
            round_contract=build_round_contract(
                [
                    {
                        "parameter_id": "parameter-1",
                        "domain_id": "d1",
                        "shard_id": "s1",
                        "vote_context_id": "DUPLICATE-KEY:round-1",
                    },
                    {
                        "parameter_id": "parameter-2",
                        "domain_id": "d1",
                        "shard_id": "s2",
                        "vote_context_id": "DUPLICATE-MISSING:round-1",
                    },
                ]
            ),
        ),
    )

    write_fixture(
        ILLEGAL,
        "unchecked-overflow",
        trace(
            "TRACE-ILLEGAL-UNCHECKED-OVERFLOW",
            [
                make_event(
                    "ACT-PARAM-PROPOSE",
                    body=cid("overflow-result"),
                    error="ARITHMETIC_UNCHECKED",
                )
            ],
        ),
    )
    write_fixture(
        ILLEGAL,
        "current-without-applyqc",
        trace(
            "TRACE-ILLEGAL-CURRENT-WITHOUT-APPLYQC",
            [
                make_event(
                    "ACT-CURRENT-ADVANCE",
                    body=cid("bad-current"),
                    result=cid("bad-checkpoint"),
                    parents=[cid("not-apply-qc")],
                    outcome="FINALIZED",
                )
            ],
            "APPLIED",
        ),
    )
    write_fixture(
        ILLEGAL,
        "partial-publication",
        trace(
            "TRACE-ILLEGAL-PARTIAL-PUBLICATION",
            [
                make_event(
                    "ACT-PUBLISH",
                    body=cid("worker-local-shard"),
                    artifacts=[cid("worker-local-shard")],
                    error="LOCAL_PARTIAL_PUBLICATION",
                )
            ],
        ),
    )
    restart_events = [
        make_event("ACT-CRASH", actor="validator-1", outcome="FAULT", error="CRASH_AFTER_PERSIST"),
        make_event("ACT-RESTART", actor="validator-1"),
        make_event(
            "ACT-CONFIG-VOTE",
            actor="validator-1",
            body=cid("restart-vote"),
            context="CONFIG:RESTART",
            durable=2,
        ),
    ]
    write_fixture(
        ILLEGAL,
        "restart-before-recovery",
        trace("TRACE-ILLEGAL-RESTART-BEFORE-RECOVERY", restart_events),
    )
    write_fixture(
        ILLEGAL,
        "view-without-qc",
        trace(
            "TRACE-ILLEGAL-VIEW-WITHOUT-QC",
            [
                make_event(
                    "ACT-VIEW-FINALIZE",
                    body=cid("view-no-qc"),
                    result=cid("view-no-qc-result"),
                    context="VIEW:NO-QC",
                    outcome="FINALIZED",
                )
            ],
        ),
    )
    write_fixture(
        ILLEGAL,
        "abort-without-qc",
        trace(
            "TRACE-ILLEGAL-ABORT-WITHOUT-QC",
            [],
            "ABORTED",
        ),
    )
    deadline_events = [
        make_event(
            "ACT-LOGICAL-TIME-ADVANCE",
            actor=None,
            role="SYSTEM",
            error="HARD_DEADLINE_REACHED",
        ),
        make_event("ACT-CONFIG-PROPOSE", body=cid("late-config")),
    ]
    write_fixture(
        ILLEGAL,
        "progress-after-hard-deadline",
        trace("TRACE-ILLEGAL-PROGRESS-AFTER-HARD-DEADLINE", deadline_events),
    )


def main() -> int:
    LEGAL.mkdir(parents=True, exist_ok=True)
    ILLEGAL.mkdir(parents=True, exist_ok=True)
    generate_legal()
    generate_illegal()
    print(
        f"generated semantics={SEMANTICS_ID} "
        f"legal={len(list(LEGAL.glob('*.json')))} "
        f"illegal={len(list(ILLEGAL.glob('*.json')))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
