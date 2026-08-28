"""Validate implementation-derived feature-006 hierarchy and failure traces."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
DEFAULT_TRACES: Final = ROOT / "out" / "build" / "cpp20" / "hierarchy-traces"
GOLDEN: Final = ROOT / "delta-protocol" / "fixtures" / "006" / "cross-language" / "golden-v1.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
TOPOLOGY_ID: Final = "sha256:99b0c5ce4fe5c850e95750d39c8a9844148adc8b0f00353da02f2f1ad00da157"
PROOF_ID: Final = "sha256:cdad45d964352c7cd33e1588279ce4459fdb1c959661029fb56ee567b00c5245"
AGGREGATE_ID: Final = "sha256:f247578ef2b8e76b27274fc95f92fc50a1eb8586b4052952075a0fddfd4bdd29"
ILLEGAL: Final = {
    "illegal-artifact-loss.json": ("EXACT_ARTIFACT_REQUIRED", "BLOCKED"),
    "illegal-mixed-view.json": ("MIXED_VIEW_REJECTED", "BLOCKED"),
    "illegal-partial-coverage.json": ("REQUIRED_MATRIX_INCOMPLETE", "BLOCKED"),
    "illegal-quorum-loss.json": ("QC_QUORUM_MISSING", "BLOCKED"),
}
FORMAL_COUNTEREXAMPLES: Final = {
    "duplicate-aggregate.json": "AGGREGATE_DUPLICATE_COVERAGE",
    "incomplete-aggregate.json": "AGGREGATE_INCOMPLETE_REQUIRED_MATRIX",
    "restart-before-recovery.json": "VOTE_BEFORE_JOURNAL_RECOVERY",
    "unchecked-overflow.json": "UNCHECKED_ARITHMETIC_ACCEPTED",
    "view-without-qc.json": "QC_QUORUM_MISSING",
}


class ExecutionError(RuntimeError):
    """Stable fail-closed hierarchy execution error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ExecutionError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def content_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def formal_round_contract() -> dict[str, Any]:
    parameters = [
        "code/parameter-000",
        "code/parameter-001",
        "text/parameter-000",
        "text/parameter-001",
    ]
    assignments = [
        {
            "domain_id": parameter.split("/", 1)[0],
            "parameter_id": parameter,
            "shard_id": parameter.split("/", 1)[1],
            "vote_context_id": f"HIERARCHY-{parameter}:round-006-hierarchy",
        }
        for parameter in parameters
    ]
    schema = {"parameter_ids": parameters}
    plan = {"assignments": assignments}
    round_config = {
        "domain_ids": ["code", "text"],
        "parameter_schema_hash": content_id(schema),
        "shard_plan_hash": content_id(plan),
    }
    contract = {
        "round_id": "round-006-hierarchy",
        "round_config": {
            "body_hash": content_id(round_config),
            **round_config,
        },
        "parameter_schema": {"schema_hash": content_id(schema), **schema},
        "shard_plan": {"plan_hash": content_id(plan), **plan},
    }
    return {"contract_id": content_id(contract), **contract}


def formal_event(
    action: str,
    logical_time: int,
    state_root: str,
    *,
    artifacts: list[str] | None = None,
    body_hash: str | None = None,
    error_code: str | None = None,
    outcome: str = "ACCEPTED",
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "action_id": action,
        "actor_id": "c-eu-v1",
        "actor_role": "VALIDATOR",
        "artifact_refs": artifacts or [],
        "body_hash": body_hash,
        "durable_sequence": 2,
        "error_code": error_code,
        "height": 1,
        "logical_time": logical_time,
        "next_state_root": state_root,
        "outcome": outcome,
        "parent_hashes": [],
        "prior_state_root": state_root,
        "request_id": request_id,
        "result_hash": None,
        "round_id": "round-006-hierarchy",
        "schema_version": "1.0.0",
        "validator_epoch": "epoch-7",
        "view": 0,
        "vote_context_id": "HIERARCHY-INTERNAL:round-006-hierarchy",
    }


def run_formal_checker(trace: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="delta-006-refinement-") as temporary:
        materialized = Path(temporary)
        archive_process = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "formal", "specs/000-formal-tla-spec"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        require(archive_process.returncode == 0, "FORMAL_ARCHIVE_FAILED")
        with tarfile.open(fileobj=io.BytesIO(archive_process.stdout), mode="r:") as archive:
            for member in archive.getmembers():
                target = (materialized / member.name).resolve()
                require(
                    target.is_relative_to(materialized.resolve()), "FORMAL_ARCHIVE_PATH_INVALID"
                )
            archive.extractall(materialized, filter="data")
        checker = materialized / "formal" / "scripts" / "check-refinement.py"
        path = materialized / "native-crash-recovery-projection.json"
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
    with tempfile.TemporaryDirectory(prefix="delta-006-counterexample-") as temporary:
        materialized = Path(temporary)
        archive_process = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "formal", "specs/000-formal-tla-spec"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        require(archive_process.returncode == 0, "FORMAL_ARCHIVE_FAILED")
        with tarfile.open(fileobj=io.BytesIO(archive_process.stdout), mode="r:") as archive:
            archive.extractall(materialized, filter="data")
        checker = materialized / "formal" / "scripts" / "check-refinement.py"
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


def verify_formal_projection(recovery: dict[str, Any]) -> dict[str, Any]:
    vote_ids = [
        str(event["vote_id"])
        for event in recovery["events"]
        if event.get("action") == "PERSIST_VOTE"
    ]
    require(len(vote_ids) == 2 and len(set(vote_ids)) == 2, "RECOVERY_VOTE_IDS_INVALID")
    state_root = content_id(
        {
            "formal_semantics_id": FORMAL_ID,
            "phase": "006-hierarchy-internal",
            "topology_id": TOPOLOGY_ID,
        }
    )
    trace = {
        "abstraction_version": "1.0.0",
        "events": [
            formal_event(
                "ACT-CRASH",
                0,
                state_root,
                error_code="CRASH_AFTER_DURABILITY",
                outcome="FAULT",
            ),
            formal_event("ACT-RESTART", 1, state_root),
            formal_event(
                "ACT-JOURNAL-RECOVER",
                2,
                state_root,
                artifacts=sorted(vote_ids),
                body_hash=vote_ids[0],
            ),
            formal_event(
                "ACT-MESSAGE-REPLAY",
                3,
                state_root,
                artifacts=[vote_ids[0]],
                body_hash=vote_ids[0],
                outcome="NO_OP",
                request_id="native-hierarchy-vote-replay",
            ),
        ],
        "formal_semantics_id": FORMAL_ID,
        "initial_state_root": state_root,
        "round_contract": formal_round_contract(),
        "schema_version": "1.0.0",
        "terminal_outcome": "IN_PROGRESS",
        "terminal_state_root": state_root,
        "trace_id": "TRACE-NATIVE-006-CRASH-RECOVERY-PROJECTION",
    }
    legal = run_formal_checker(trace)
    illegal = [
        run_formal_counterexample(name, expected_reason)
        for name, expected_reason in FORMAL_COUNTEREXAMPLES.items()
    ]
    return {
        "internal_hierarchy_actions": "STUTTER_UNTIL_FEATURE008_CERTIFICATE_TRANSITIONS",
        "legal": legal,
        "negative": illegal,
        "status": "PASS",
    }


def load_canonical(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode())
    require(isinstance(value, dict), "TRACE_ROOT_INVALID", path.name)
    require(raw == canonical_json_bytes(value) + b"\n", "TRACE_NOT_CANONICAL", path.name)
    require(value.get("formal_semantics_id") == FORMAL_ID, "TRACE_FORMAL_ID_INVALID", path.name)
    require(value.get("schema_version") == "1.0.0", "TRACE_SCHEMA_INVALID", path.name)
    return value


def keyed(
    items: list[dict[str, Any]], fields: tuple[str, ...]
) -> dict[tuple[str, ...], dict[str, Any]]:
    result: dict[tuple[str, ...], dict[str, Any]] = {}
    for item in items:
        value = item["value"]
        key = tuple(str(value[field]) for field in fields)
        require(key not in result, "GOLDEN_KEY_DUPLICATE", repr(key))
        result[key] = item
    return result


def verify_source_boundary() -> None:
    required = {
        ROOT / "delta-core-cpp/src/reduce/hierarchy.cpp": (
            "checked_multiply",
            "certificate.body_id == result.result_id",
            "global intake cannot mix regional committee views",
            "complete hierarchy cannot mix global committee views",
            "DELTA_HIERARCHY_MUTANT_AVERAGE_REGIONS",
            "DELTA_HIERARCHY_MUTANT_PARTIAL_GLOBAL",
        ),
        ROOT / "delta-ffi/src/hierarchy_abi.cpp": (
            "routing_projection_id(topology)",
            "delta_hierarchy_contract_validate_borrowed",
            "delta_hierarchy_contract_validate_copy",
        ),
        ROOT / "delta-node-java/src/main/java/io/deltareduce/node/hierarchy/HierarchyRouter.java": (
            "nativeValidation.routingProjectionId().equals(topology.routingProjectionId())",
            "routeCapacity",
            "maximumRetries",
            "hard deadline reached: deterministic routing abort",
        ),
    }
    for path, fragments in required.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            require(fragment in text, "SOURCE_BOUNDARY_INCOMPLETE", f"{path.name}:{fragment}")
    native = (ROOT / "delta-core-cpp/src/reduce/hierarchy.cpp").read_text(encoding="utf-8")
    require("float" not in native and "double" not in native, "AUTHORITATIVE_FLOAT_PATH_PRESENT")
    java = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(
            (ROOT / "delta-node-java/src/main/java/io/deltareduce/node/hierarchy").glob("*.java")
        )
    )
    for forbidden in ("buildQc", "createQc", "sumNumerator", "averageRegions"):
        require(forbidden not in java, "JAVA_MATH_QC_AUTHORITY_PRESENT", forbidden)


def verify_hierarchy(trace: dict[str, Any], golden: dict[str, Any]) -> dict[str, int]:
    require(trace.get("trace_id") == "TRACE-NATIVE-006-HIERARCHY-FLAT", "LEGAL_TRACE_ID_INVALID")
    require(trace.get("topology_id") == TOPOLOGY_ID, "TOPOLOGY_ID_INVALID")
    require(trace.get("hierarchy_proof_instance_id") == PROOF_ID, "PROOF_ID_INVALID")
    require(trace.get("aggregate_id") == AGGREGATE_ID, "AGGREGATE_ID_INVALID")
    require(trace.get("terminal_outcome") == "IN_PROGRESS", "PHASE_BOUNDARY_INVALID")
    require(trace.get("current_checkpoint_advanced") is False, "CURRENT_ADVANCED_BY_FEATURE006")
    events = trace.get("events")
    require(isinstance(events, list), "LEGAL_EVENTS_INVALID")
    regional_events = [
        event for event in events if event.get("action") == "REGIONAL_RESULT_FINALIZED"
    ]
    global_events = [
        event for event in events if event.get("action") == "GLOBAL_PARAMETER_RESULT_FINALIZED"
    ]
    assembly_events = [event for event in events if event.get("action") == "HIERARCHY_ASSEMBLED"]
    regional_results = keyed(
        golden["regional_shard_results"], ("domain_id", "region_id", "shard_id")
    )
    regional_qcs = keyed(golden["regional_shard_qcs"], ("domain_id", "region_id", "shard_id"))
    global_results = keyed(golden["global_parameter_results"], ("domain_id", "shard_id"))
    global_qcs = keyed(golden["global_parameter_qcs"], ("domain_id", "shard_id"))
    require(len(regional_events) == len(regional_results) == 12, "REGIONAL_MATRIX_INCOMPLETE")
    require(len(global_events) == len(global_results) == 4, "GLOBAL_MATRIX_INCOMPLETE")
    require(len(assembly_events) == 1, "ASSEMBLY_EVENT_INVALID")
    seen_regional: set[tuple[str, str, str]] = set()
    for event in regional_events:
        key = (event["domain_id"], event["region_id"], event["shard_id"])
        require(
            key not in seen_regional and key in regional_results, "REGIONAL_KEY_INVALID", repr(key)
        )
        seen_regional.add(key)
        require(
            event.get("body_id") == regional_results[key]["content_id"], "REGIONAL_BODY_ID_INVALID"
        )
        require(
            event.get("certificate_id") == regional_qcs[key]["content_id"],
            "REGIONAL_QC_ID_INVALID",
        )
        require(event.get("view") == 0, "REGIONAL_VIEW_INVALID")
    seen_global: set[tuple[str, str]] = set()
    for event in global_events:
        key = (event["domain_id"], event["shard_id"])
        require(key not in seen_global and key in global_results, "GLOBAL_KEY_INVALID", repr(key))
        seen_global.add(key)
        require(event.get("body_id") == global_results[key]["content_id"], "GLOBAL_BODY_ID_INVALID")
        require(
            event.get("certificate_id") == global_qcs[key]["content_id"], "GLOBAL_QC_ID_INVALID"
        )
        require(event.get("view") == 0, "GLOBAL_VIEW_INVALID")
    require(assembly_events[0].get("aggregate_id") == AGGREGATE_ID, "ASSEMBLY_ID_INVALID")
    flat = trace.get("flat_metrics")
    hierarchy = trace.get("hierarchy_metrics")
    require(isinstance(flat, dict) and isinstance(hierarchy, dict), "FAN_IN_METRICS_INVALID")
    require(flat.get("objects") == 22 and hierarchy.get("objects") == 12, "FAN_IN_OBJECTS_INVALID")
    require(
        isinstance(flat.get("payload_bytes"), int)
        and isinstance(hierarchy.get("payload_bytes"), int)
        and flat["payload_bytes"] > hierarchy["payload_bytes"] > 0,
        "FAN_IN_BYTES_INVALID",
    )
    return {
        "global_results": len(global_events),
        "regional_results": len(regional_events),
        "flat_objects": flat["objects"],
        "hierarchy_objects": hierarchy["objects"],
        "flat_payload_bytes": flat["payload_bytes"],
        "hierarchy_payload_bytes": hierarchy["payload_bytes"],
    }


def verify_trace_dir(trace_root: Path) -> dict[str, Any]:
    verify_source_boundary()
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    hierarchy = verify_hierarchy(load_canonical(trace_root / "legal-hierarchy-flat.json"), golden)
    recovery = load_canonical(trace_root / "legal-crash-recovery.json")
    require(
        recovery.get("trace_id") == "TRACE-NATIVE-006-CRASH-RECOVERY", "RECOVERY_TRACE_ID_INVALID"
    )
    actions = [event.get("action") for event in recovery.get("events", [])]
    require(
        actions
        == ["PERSIST_VOTE", "PERSIST_VOTE", "CRASH", "RESTART", "RECOVER_JOURNAL", "REPLAY_VOTE"],
        "RECOVERY_ORDER_INVALID",
    )
    require(recovery["events"][4].get("vote_count") == 2, "RECOVERY_VOTE_COUNT_INVALID")
    require(recovery["events"][5].get("same_identity") is True, "RECOVERY_IDENTITY_INVALID")
    formal_projection = verify_formal_projection(recovery)
    illegal = []
    for name, (error_code, outcome) in ILLEGAL.items():
        trace = load_canonical(trace_root / name)
        require(trace.get("accepted") is False, "ILLEGAL_TRACE_ACCEPTED", name)
        require(trace.get("error_code") == error_code, "ILLEGAL_ERROR_INVALID", name)
        require(trace.get("terminal_outcome") == outcome, "ILLEGAL_OUTCOME_INVALID", name)
        illegal.append({"error_code": error_code, "fixture": name, "status": "PASS"})
    return {
        "checks": [
            "NATIVE_REGIONAL_GLOBAL_QC_MATRIX_EXACT",
            "HIERARCHY_EQUALS_FROZEN_FLAT_ORACLE_IDS",
            "COMPLETE_IMMUTABLE_DOMAIN_SHARD_MATRIX",
            "PERSIST_CRASH_RESTART_RECOVER_REPLAY_ORDER",
            "ARTIFACT_LOSS_MIXED_VIEW_PARTIAL_COVERAGE_QUORUM_LOSS_REJECTED",
            "FEATURE008_CURRENT_POINTER_BOUNDARY_PRESERVED",
            "CROSS_REGION_OBJECT_AND_PAYLOAD_BYTES_MEASURED",
            "EXACT_FEATURE000_REFINEMENT_CHECKER_ACCEPTS_RECOVERY_PROJECTION",
            "FORMAL_COVERAGE_QUORUM_OVERFLOW_RECOVERY_COUNTEREXAMPLES_REJECTED",
            "ZERO_NATIVE_FLOAT_AND_ZERO_JAVA_MATH_QC_AUTHORITY",
        ],
        "formal_projection": formal_projection,
        "formal_semantics_id": FORMAL_ID,
        "illegal": illegal,
        "legal_trace_count": 2,
        "metrics": hierarchy,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "task_ids": [
            "T015",
            "T016",
            "T017",
            "T018",
            "T019",
            "T020",
            "T021",
            "T022",
            "T023",
            "T024",
            "T025",
            "HR006-003",
            "HR006-004",
            "HR006-007",
            "HR006-008",
            "HR006-009",
            "HR006-011",
        ],
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "006-hierarchy-execution", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", type=Path, default=DEFAULT_TRACES)
    arguments = parser.parse_args()
    try:
        result = verify_trace_dir(arguments.trace_dir.resolve())
    except (ExecutionError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
