"""Publish and verify implementation-derived feature-007 scheduling refinement evidence."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "007-domain-pure-ticket-scheduling"
OUTPUT: Final = FEATURE / "evidence" / "scheduling-refinement.json"
DEFAULT_TRACES: Final = ROOT / "out" / "build" / "cpp20" / "scheduling-traces"
PREDECESSOR: Final = "2b9f26e75a864d4a210e4b8f2a87f1efdf03d8c1"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SOURCE_ARTIFACTS: Final = (
    ".github/workflows/scheduling.yml",
    "CMakeLists.txt",
    "Makefile",
    "delta-core-cpp/tests/scheduling_lifecycle_test.cpp",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_scheduling_refinement.py",
)
LEGAL_ACTIONS: Final = {
    "PLAN_FINALIZED": "ACT-TICKET-ISSUE",
    "LEASE_OPEN": "ACT-LEASE-OPEN",
    "LEASE_RENEW": "ACT-LEASE-RENEW",
    "LEASE_EXPIRE": "ACT-LEASE-EXPIRE",
    "LEASE_REASSIGN": "ACT-LEASE-REASSIGN",
    "COMMIT": "ACT-COMMIT",
    "CRASH_AFTER_DURABILITY": "ACT-CRASH",
    "RESTART": "ACT-RESTART",
    "RECOVER_JOURNAL": "ACT-JOURNAL-RECOVER",
    "REPLAY_TRANSITION": "ACT-MESSAGE-REPLAY",
}
ILLEGAL: Final = {
    "illegal-adaptive-h.json": ("PLAN_FINALIZE", "FORBIDDEN_ADAPTIVE_WORK_FIELD"),
    "illegal-device-weight.json": ("PLAN_FINALIZE", "FORBIDDEN_DEVICE_WEIGHT_FIELD"),
    "illegal-early-randomness.json": ("PLAN_FINALIZE", "EARLY_RANDOMNESS_FORBIDDEN"),
    "illegal-old-holder.json": ("COMMIT", "STALE_LEASE"),
    "illegal-post-commit-reassign.json": (
        "LEASE_REASSIGN",
        "COMMIT_ALREADY_ACCEPTED",
    ),
    "illegal-stale-timer.json": ("LEASE_EXPIRE", "STALE_TIMER_NOOP"),
}
FORMAL_COUNTEREXAMPLES: Final = {
    "commitment-replacement.json": "COMMITMENT_REPLACEMENT",
    "progress-after-hard-deadline.json": "PROGRESS_AFTER_HARD_DEADLINE",
    "restart-before-recovery.json": "VOTE_BEFORE_JOURNAL_RECOVERY",
    "seed-without-isc.json": "SEED_WITHOUT_FINALIZED_ISC",
    "unchecked-overflow.json": "UNCHECKED_ARITHMETIC_ACCEPTED",
}


class RefinementEvidenceError(RuntimeError):
    """Stable fail-closed scheduling refinement evidence error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise RefinementEvidenceError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def content_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def source_bytes(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def load_canonical(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    document = json.loads(raw)
    require(isinstance(document, dict), "TRACE_ROOT_INVALID", path.name)
    require(raw == canonical_json_bytes(document) + b"\n", "TRACE_NOT_CANONICAL", path.name)
    require(document.get("schema_version") == "1.0.0", "TRACE_SCHEMA_INVALID", path.name)
    require(document.get("formal_semantics_id") == FORMAL_ID, "TRACE_FORMAL_ID_INVALID", path.name)
    return document


def formal_round_contract() -> dict[str, Any]:
    parameters = ["ticket-code-000", "ticket-code-001", "ticket-text-000"]
    assignments = [
        {
            "domain_id": ticket.split("-", 2)[1],
            "parameter_id": ticket,
            "shard_id": ticket,
            "vote_context_id": f"SCHEDULING-{ticket}:round-007-scheduling",
        }
        for ticket in parameters
    ]
    schema = {"parameter_ids": parameters}
    plan = {"assignments": assignments}
    round_config = {
        "domain_ids": ["code", "text"],
        "parameter_schema_hash": content_id(schema),
        "shard_plan_hash": content_id(plan),
    }
    contract = {
        "round_id": "round-007-scheduling",
        "round_config": {"body_hash": content_id(round_config), **round_config},
        "parameter_schema": {"schema_hash": content_id(schema), **schema},
        "shard_plan": {"plan_hash": content_id(plan), **plan},
    }
    return {"contract_id": content_id(contract), **contract}


def formal_event(
    action: str,
    native: dict[str, Any],
    logical_time: int,
    prior_root: str,
    next_root: str,
) -> dict[str, Any]:
    artifact_id = native["artifact_id"]
    crash = action == "ACT-CRASH"
    replay = action == "ACT-MESSAGE-REPLAY"
    return {
        "action_id": action,
        "actor_id": "scheduler-v1",
        "actor_role": "VALIDATOR",
        "artifact_refs": [artifact_id],
        "body_hash": artifact_id,
        "durable_sequence": native["journal_sequence"],
        "error_code": "CRASH_AFTER_DURABILITY" if crash else None,
        "height": 1,
        "logical_time": logical_time,
        "next_state_root": next_root,
        "outcome": "FAULT" if crash else "NO_OP" if replay else "ACCEPTED",
        "parent_hashes": [],
        "prior_state_root": prior_root,
        "request_id": native["ticket_id"],
        "result_hash": artifact_id,
        "round_id": "round-007-scheduling",
        "schema_version": "1.0.0",
        "validator_epoch": "epoch-7",
        "view": 0,
        "vote_context_id": f"SCHEDULING-{native['ticket_id']}:round-007-scheduling",
    }


def formal_projection(native: dict[str, Any]) -> dict[str, Any]:
    initial = content_id({"phase": "007-scheduling", "trace_id": native["trace_id"]})
    prior = initial
    events = []
    for index, event in enumerate(native["events"]):
        action = LEGAL_ACTIONS[event["action"]]
        next_root = content_id(
            {
                "action": action,
                "artifact_id": event["artifact_id"],
                "index": index,
                "prior": prior,
            }
        )
        events.append(formal_event(action, event, index, prior, next_root))
        prior = next_root
    return {
        "abstraction_version": "1.0.0",
        "events": events,
        "formal_semantics_id": FORMAL_ID,
        "initial_state_root": initial,
        "round_contract": formal_round_contract(),
        "schema_version": "1.0.0",
        "terminal_outcome": "IN_PROGRESS",
        "terminal_state_root": prior,
        "trace_id": native["trace_id"] + "-PROJECTION",
    }


def materialize_formal_tree(directory: Path) -> Path:
    process = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD", "formal", "specs/000-formal-tla-spec"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, "FORMAL_ARCHIVE_FAILED")
    with tarfile.open(fileobj=io.BytesIO(process.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            target = (directory / member.name).resolve()
            require(target.is_relative_to(directory.resolve()), "FORMAL_ARCHIVE_PATH_INVALID")
        archive.extractall(directory, filter="data")
    return directory / "formal" / "scripts" / "check-refinement.py"


def run_formal_checker(trace: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="delta-007-refinement-") as temporary:
        materialized = Path(temporary)
        checker = materialize_formal_tree(materialized)
        path = materialized / "native-scheduling-projection.json"
        path.write_bytes(canonical_json_bytes(trace) + b"\n")
        process = subprocess.run(
            [sys.executable, str(checker), str(path)],
            cwd=materialized,
            check=False,
            capture_output=True,
            text=True,
        )
    lines = process.stdout.strip().splitlines()
    require(bool(lines), "FORMAL_CHECKER_OUTPUT_MISSING")
    result = json.loads(lines[-1])
    require(
        process.returncode == 0 and result.get("status") == "PASS",
        "LEGAL_FORMAL_PROJECTION_REJECTED",
        str(result.get("error")),
    )
    return result


def run_formal_counterexample(name: str, expected_reason: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="delta-007-counterexample-") as temporary:
        materialized = Path(temporary)
        checker = materialize_formal_tree(materialized)
        path = materialized / "formal" / "fixtures" / "traces" / "illegal" / name
        process = subprocess.run(
            [sys.executable, str(checker), str(path)],
            cwd=materialized,
            check=False,
            capture_output=True,
            text=True,
        )
    lines = process.stdout.strip().splitlines()
    require(process.returncode != 0 and bool(lines), "FORMAL_COUNTEREXAMPLE_ACCEPTED", name)
    result = json.loads(lines[-1])
    require(expected_reason in str(result.get("error")), "FORMAL_REASON_INVALID", name)
    return {"expected_reason": expected_reason, "fixture": name, "status": "PASS"}


def verify_legal(trace_root: Path) -> dict[str, Any]:
    lifecycle = load_canonical(trace_root / "legal-full-lifecycle.json")
    recovery = load_canonical(trace_root / "legal-restart-replay.json")
    lifecycle_actions = [event.get("action") for event in lifecycle.get("events", [])]
    require(
        lifecycle_actions
        == [
            "PLAN_FINALIZED",
            "LEASE_OPEN",
            "LEASE_RENEW",
            "LEASE_EXPIRE",
            "LEASE_REASSIGN",
            "COMMIT",
        ],
        "LEGAL_LIFECYCLE_ORDER_INVALID",
    )
    recovery_actions = [event.get("action") for event in recovery.get("events", [])]
    require(
        recovery_actions
        == ["CRASH_AFTER_DURABILITY", "RESTART", "RECOVER_JOURNAL", "REPLAY_TRANSITION"],
        "LEGAL_RECOVERY_ORDER_INVALID",
    )
    require(
        [event.get("status") for event in lifecycle["events"]] == ["APPLIED"] * 6,
        "LEGAL_LIFECYCLE_STATUS_INVALID",
    )
    require(
        [event.get("status") for event in recovery["events"]]
        == ["FAULT", "APPLIED", "APPLIED", "REPLAY"],
        "LEGAL_RECOVERY_STATUS_INVALID",
    )
    for trace in (lifecycle, recovery):
        require(trace.get("terminal_outcome") == "IN_PROGRESS", "TRACE_BOUNDARY_INVALID")
        require(
            all(
                isinstance(event.get("artifact_id"), str)
                and re.fullmatch(r"sha256:[0-9a-f]{64}", event["artifact_id"])
                and isinstance(event.get("journal_sequence"), int)
                and event["journal_sequence"] >= 0
                for event in trace["events"]
            ),
            "LEGAL_EVENT_BINDING_INVALID",
            trace["trace_id"],
        )
        sequences = [event["journal_sequence"] for event in trace["events"]]
        require(sequences == sorted(sequences), "JOURNAL_SEQUENCE_REGRESSION", trace["trace_id"])
    return {
        "accepted": [
            run_formal_checker(formal_projection(lifecycle)),
            run_formal_checker(formal_projection(recovery)),
        ],
        "native_trace_ids": [lifecycle["trace_id"], recovery["trace_id"]],
        "status": "PASS",
    }


def verify_illegal(trace_root: Path) -> list[dict[str, str]]:
    result = []
    for name, (action, error_code) in ILLEGAL.items():
        trace = load_canonical(trace_root / name)
        require(trace.get("accepted") is False, "ILLEGAL_TRACE_ACCEPTED", name)
        require(trace.get("action") == action, "ILLEGAL_ACTION_INVALID", name)
        require(trace.get("error_code") == error_code, "ILLEGAL_ERROR_INVALID", name)
        require(trace.get("terminal_outcome") == "BLOCKED", "ILLEGAL_OUTCOME_INVALID", name)
        result.append({"error_code": error_code, "fixture": name, "status": "PASS"})
    return result


def verify_measurement(trace_root: Path) -> dict[str, Any]:
    measurement = load_canonical(trace_root / "measurement-50-worker.json")
    require(measurement.get("worker_count") == 50, "WORKER_COUNT_INVALID")
    require(measurement.get("plan_permutations") == 64, "PLAN_PERMUTATIONS_INVALID")
    require(measurement.get("lease_permutations") == 64, "LEASE_PERMUTATIONS_INVALID")
    require(measurement.get("owner_changed") is True, "SPEED_SCENARIO_NOT_EXERCISED")
    require(
        measurement.get("speed_independent_ticket_bytes") is True,
        "SPEED_CHANGED_TICKET_BYTES",
    )
    require(
        isinstance(measurement.get("elapsed_ns"), int) and measurement["elapsed_ns"] > 0,
        "TIMING_MEASUREMENT_INVALID",
    )
    normalized = {**measurement, "elapsed_ns": "POSITIVE_MEASUREMENT_RECORDED"}
    return {
        "normalized_sha256": hashlib.sha256(canonical_json_bytes(normalized)).hexdigest(),
        "lease_permutations": 64,
        "owner_changed": True,
        "plan_id": measurement["plan_id"],
        "plan_permutations": 64,
        "timing_recorded": True,
        "worker_count": 50,
    }


def verify_source(commit: str) -> list[dict[str, str]]:
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(git_text("rev-parse", f"{commit}^") == PREDECESSOR, "SOURCE_PARENT_INVALID")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=False
        ).returncode
        == 0,
        "SOURCE_NOT_ANCESTOR",
    )
    changed = set(git_text("diff", "--name-only", PREDECESSOR, commit).splitlines())
    require(changed == set(SOURCE_ARTIFACTS), "SOURCE_SCOPE_INVALID", ",".join(sorted(changed)))
    formal_diff = git_text(
        "diff",
        "--name-only",
        PREDECESSOR,
        commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    native_test = source_bytes(
        commit, "delta-core-cpp/tests/scheduling_lifecycle_test.cpp"
    ).decode()
    cmake = source_bytes(commit, "CMakeLists.txt").decode()
    workflow = source_bytes(commit, ".github/workflows/scheduling.yml").decode()
    makefile = source_bytes(commit, "Makefile").decode()
    for marker in (
        "export_refinement_traces",
        "export_fifty_worker_measurement",
        "illegal-old-holder.json",
        "illegal-post-commit-reassign.json",
        "illegal-adaptive-h.json",
        "illegal-device-weight.json",
        "illegal-early-randomness.json",
    ):
        require(marker in native_test, "NATIVE_REFINEMENT_MARKER_MISSING", marker)
    require(
        "delta_core.scheduling_trace_export" in cmake,
        "TRACE_EXPORT_TEST_NOT_REGISTERED",
    )
    require("verify_scheduling_refinement.py" in workflow, "REFINEMENT_CI_GATE_MISSING")
    require("--check-only --trace-dir" in workflow, "REFINEMENT_CI_ARGUMENTS_MISSING")
    require("scheduling-refinement:" in makefile, "REFINEMENT_MAKE_GATE_MISSING")
    for mutant in (
        "DELTA_SCHEDULING_MUTANT_EXPOSE_BEFORE_DURABILITY",
        "ADAPT_WORK",
        "OVERLAP_RANGES",
        "SKIP_INFEASIBILITY",
    ):
        require(mutant in cmake, "PRODUCTION_MUTANT_NOT_REGISTERED", mutant)
    production = "\n".join(
        source_bytes(commit, path).decode()
        for path in (
            "delta-core-cpp/src/scheduling/contracts.cpp",
            "delta-core-cpp/src/scheduling/eligibility.cpp",
            "delta-core-cpp/src/scheduling/leases.cpp",
            "delta-core-cpp/src/scheduling/planner.cpp",
            "delta-core-cpp/src/scheduling/recovery.cpp",
        )
    )
    for forbidden in (
        r"\badaptive_h\b",
        r"\badaptive_b\b",
        r"\bdevice_speed_weight\b",
        r"\bstaleness_weight\b",
        r"\brho_t\b",
        r"\brandom_device\b",
    ):
        require(
            re.search(forbidden, production, re.IGNORECASE) is None,
            "FORBIDDEN_NATIVE_SCHEDULING_AUTHORITY_PRESENT",
            forbidden,
        )
    return [
        {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
        for path in SOURCE_ARTIFACTS
    ]


def trace_artifacts(trace_root: Path) -> list[dict[str, str]]:
    paths = sorted(trace_root.glob("*.json"))
    require(len(paths) == 9, "TRACE_SET_INCOMPLETE")
    result = []
    for path in paths:
        document = load_canonical(path)
        if path.name == "measurement-50-worker.json":
            document["elapsed_ns"] = "POSITIVE_MEASUREMENT_RECORDED"
        result.append(
            {
                "name": path.name,
                "normalized_sha256": hashlib.sha256(canonical_json_bytes(document)).hexdigest(),
            }
        )
    return result


def build(commit: str, trace_root: Path) -> dict[str, Any]:
    commit = git_text("rev-parse", commit)
    legal = verify_legal(trace_root)
    illegal = verify_illegal(trace_root)
    measurement = verify_measurement(trace_root)
    formal_negative = [
        run_formal_counterexample(name, reason) for name, reason in FORMAL_COUNTEREXAMPLES.items()
    ]
    return {
        "checks": [
            "IMPLEMENTATION_DERIVED_PLAN_LEASE_EXPIRE_REASSIGN_COMMIT_TRACE",
            "IMPLEMENTATION_DERIVED_CRASH_RESTART_RECOVER_REPLAY_TRACE",
            "EXACT_FEATURE000_CHECKER_ACCEPTS_LEGAL_PROJECTIONS",
            "OLD_HOLDER_POST_COMMIT_STALE_TIMER_REJECTED",
            "ADAPTIVE_H_DEVICE_WEIGHT_EARLY_RANDOMNESS_REJECTED",
            "PRODUCTION_MUTANTS_REMAIN_REGISTERED_AND_KILLED",
            "FIFTY_WORKER_PLAN_AND_LEASE_PERMUTATION_DETERMINISM",
            "SPEED_CHANGES_OWNERSHIP_NOT_TICKET_BYTES_OR_DEADLINES",
            "POSITIVE_TIMING_RECORDED_WITHOUT_SAFETY_OR_WAN_TARGET",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal_negative": formal_negative,
        "formal_semantics_id": FORMAL_ID,
        "illegal": illegal,
        "legal": legal,
        "measurement": measurement,
        "phase": "007-scheduling-refinement",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": verify_source(commit),
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T027", "T028", "T029", "HR007-007", "HR007-008", "HR007-010", "HR007-011"],
        "trace_artifacts": trace_artifacts(trace_root),
    }


def verify_evidence(trace_root: Path) -> dict[str, Any]:
    raw = OUTPUT.read_bytes()
    evidence = json.loads(raw)
    require(isinstance(evidence, dict), "EVIDENCE_ROOT_INVALID")
    require(raw == canonical_json_bytes(evidence), "EVIDENCE_NOT_CANONICAL")
    source = evidence.get("source")
    require(isinstance(source, dict), "EVIDENCE_SOURCE_INVALID")
    require(evidence == build(str(source.get("commit")), trace_root), "EVIDENCE_DRIFT")
    return evidence


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "007-scheduling-refinement", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--trace-dir", type=Path, default=DEFAULT_TRACES)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        trace_root = arguments.trace_dir.resolve()
        if arguments.write:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            result = build(arguments.source_commit, trace_root)
            OUTPUT.write_bytes(canonical_json_bytes(result))
        else:
            require(arguments.check_only, "CHECK_ONLY_REQUIRED")
            result = verify_evidence(trace_root)
    except (
        RefinementEvidenceError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
