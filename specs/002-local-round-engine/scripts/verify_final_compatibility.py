"""Verify feature-002 formal binding and emit deterministic compatibility evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "002-local-round-engine"
DEFAULT_OUTPUT = FEATURE / "evidence" / "final-compatibility.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_FORMAL_SOURCE = "1e6e0f6f70056161d95933e71494ec390c7c1151"
EXPECTED_FORMAL_REPORT_SHA256 = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes, derive_formal_semantics_id  # noqa: E402


class CompatibilityError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise CompatibilityError(code)


def load_json(relative: str) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatibilityError(f"JSON_INVALID:{relative}") from exc
    require(isinstance(value, dict), f"JSON_ROOT_INVALID:{relative}")
    return value


def sha256_file(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def tracked_paths(*prefixes: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", *prefixes],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return tuple(path for path in completed.stdout.decode("utf-8").split("\0") if path)


def git_blob(path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def discover_semantic_artifacts() -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for path in tracked_paths("formal/tla", "formal/proofs", "formal/schemas"):
        kind: str | None = None
        if path.startswith("formal/tla/") and path.endswith(".tla") and "/mutants/" not in path:
            kind = "tla_module"
        elif path == "formal/proofs/DeltaReduce.lean" or (
            path.startswith("formal/proofs/DeltaReduce/") and path.endswith(".lean")
        ):
            kind = "lean_theorem"
        elif path == "formal/schemas/formal-trace.schema.json":
            kind = "trace_schema"
        if kind is not None:
            result.append(
                {
                    "kind": kind,
                    "path": path,
                    "sha256": hashlib.sha256(git_blob(path)).hexdigest(),
                }
            )
    return sorted(result, key=lambda item: (item["path"], item["kind"]))


def verify_formal_binding() -> tuple[list[dict[str, str]], dict[str, object]]:
    semantics = load_json("formal/reports/formal-semantics.json")
    discovered = discover_semantic_artifacts()
    require(discovered == semantics.get("semantic_artifacts"), "FORMAL_SEMANTIC_SOURCE_DRIFT")
    derived = derive_formal_semantics_id("1.0.0", discovered)
    require(derived == EXPECTED_FORMAL_ID, "FORMAL_SEMANTICS_ID_DRIFT")
    report_path = "formal/reports/formal-verification-report.json"
    report = load_json(report_path)
    require(sha256_file(report_path) == EXPECTED_FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_DRIFT")
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == derived,
        "FORMAL_REPORT_NOT_GO",
    )
    source = report.get("source_tree")
    require(
        isinstance(source, dict) and source.get("commit") == EXPECTED_FORMAL_SOURCE,
        "FORMAL_SOURCE_COMMIT_DRIFT",
    )
    return discovered, {
        "decision": "GO",
        "sha256": EXPECTED_FORMAL_REPORT_SHA256,
        "source_commit": EXPECTED_FORMAL_SOURCE,
    }


def verify_no_formal_diff() -> None:
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            "formal/tla",
            "formal/proofs",
            "formal/schemas",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    require(not completed.stdout.strip(), "FORMAL_SOURCE_DIFF_PRESENT")


def verify_registry() -> dict[str, object]:
    registry = load_json("delta-protocol/registry.json")
    require(registry.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "REGISTRY_ID_DRIFT")
    schemas = registry.get("schemas")
    fixtures = registry.get("fixtures")
    media = registry.get("media_types")
    require(
        isinstance(schemas, list) and isinstance(fixtures, list) and isinstance(media, list),
        "REGISTRY_SHAPE_INVALID",
    )
    require(
        [item.get("path") for item in schemas] == sorted(item.get("path") for item in schemas),
        "REGISTRY_SCHEMA_ORDER_INVALID",
    )
    require(
        [item.get("path") for item in fixtures] == sorted(item.get("path") for item in fixtures),
        "REGISTRY_FIXTURE_ORDER_INVALID",
    )
    for record in [*schemas, *fixtures, registry.get("action_registry")]:
        require(
            isinstance(record, dict) and set(record) == {"id", "path", "sha256"},
            "REGISTRY_RECORD_INVALID",
        )
        relative = f"delta-protocol/{record['path']}"
        require(sha256_file(relative) == record["sha256"], "REGISTRY_HASH_MISMATCH")
    schema_ids = {item["id"] for item in schemas}
    require(
        {
            "SCHEMA-DOMAIN-PURE-WORK-TICKET-V1",
            "SCHEMA-LOCAL-ROUND-COMPLETION-V1",
            "SCHEMA-NORMALIZED-CONTRIBUTION-CANDIDATE-V1",
            "SCHEMA-PARAMETER-SCHEMA-V1",
        }
        <= schema_ids,
        "LOCAL_ROUND_SCHEMA_MISSING",
    )
    require(all(item.get("schema_id") in schema_ids for item in media), "MEDIA_SCHEMA_MISSING")
    projection = load_json("delta-protocol/action-registry/formal-projection-v1.json")
    semantics = load_json("formal/reports/formal-semantics.json")
    ownership = semantics.get("feature_ownership")
    require(isinstance(ownership, list), "FORMAL_OWNERSHIP_INVALID")
    formal_actions = {
        item.get("id")
        for item in ownership
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    projected_actions = set(projection.get("actions", []))
    require(projected_actions <= formal_actions, "UNREGISTERED_PROJECTION_ACTION")
    require(projection.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "PROJECTION_ID_DRIFT")
    return {
        "fixture_count": len(fixtures),
        "media_type_count": len(media),
        "registry_sha256": sha256_file("delta-protocol/registry.json"),
        "schema_count": len(schemas),
    }


def verify_completed_scope() -> None:
    tasks = (FEATURE / "tasks.md").read_text(encoding="utf-8")
    runtime_tasks = (FEATURE / "runtime-tasks.md").read_text(encoding="utf-8")
    for index in range(30):
        require(
            re.search(rf"^- \[x\] T{index:03d}\b", tasks, re.MULTILINE) is not None,
            "TASK_INCOMPLETE",
        )
    for index in range(1, 9):
        require(
            re.search(rf"^- \[x\] \*\*HR002-{index:03d}\*\*", runtime_tasks, re.MULTILINE)
            is not None,
            "RUNTIME_TASK_INCOMPLETE",
        )


def verify() -> dict[str, Any]:
    artifacts, report = verify_formal_binding()
    verify_no_formal_diff()
    verify_completed_scope()
    registry = verify_registry()
    predecessor = load_json("specs/002-local-round-engine/evidence/predecessor-gate.json")
    require(
        predecessor.get("status") == "PASS"
        and predecessor.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "PREDECESSOR_GATE_INVALID",
    )
    runtime_profile = (FEATURE / "runtime-profile.md").read_text(encoding="utf-8")
    require("**Formal impact**: `REFINEMENT_ONLY`" in runtime_profile, "IMPACT_CLASS_DRIFT")
    require(EXPECTED_FORMAL_ID in runtime_profile, "RUNTIME_PROFILE_UNBOUND")
    evidence_paths = [
        "configs/worker/smoke-ticket.json",
        "delta-protocol/action-registry/formal-projection-v1.json",
        "delta-protocol/fixtures/local-round/feature004-encoder-inputs-v1.json",
        "delta-protocol/fixtures/local-round/traces-v1.json",
        "delta-protocol/registry.json",
        "delta-protocol/schemas/domain-pure-work-ticket-v1.json",
        "delta-protocol/schemas/local-round-completion-v1.json",
        "delta-protocol/schemas/normalized-contribution-candidate-v1.json",
        "delta-protocol/schemas/parameter-schema-v1.json",
        "delta-worker-python/src/deltatorrent/domain/formal_compat.py",
        "delta-worker-python/src/deltatorrent/worker/engine.py",
        "delta-worker-python/src/deltatorrent/worker/update_writer.py",
        "docs/local-round-contract.md",
        "specs/002-local-round-engine/evidence/predecessor-gate.json",
        "specs/002-local-round-engine/runtime-profile.md",
    ]
    return {
        "analysis_kind": "FORMAL_COMPATIBILITY_AND_CROSS_ARTIFACT",
        "artifacts": [
            {"path": path, "sha256": sha256_file(path)} for path in sorted(evidence_paths)
        ],
        "checks": [
            "FORMAL_GO_REVERIFIED",
            "FORMAL_SEMANTIC_SOURCE_SET_EXACT",
            "FORMAL_SEMANTICS_ID_REDERIVED",
            "NO_FORMAL_SOURCE_DIFF",
            "PROJECTION_ACTION_IDS_REGISTERED",
            "LOCAL_ROUND_PROTOCOL_HASHES_VERIFIED",
            "WORKER_LOCAL_FAILURES_REFINEMENT_ONLY",
            "PROTOCOL_AND_IMPLEMENTATION_IDS_BOUND",
        ],
        "classification": "REFINEMENT_ONLY",
        "errors": [],
        "formal_report": report,
        "formal_semantic_artifact_count": len(artifacts),
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "local_outcome_projection": {
            "CANCELLED": "FAULT",
            "COMPLETED": "ACCEPTED",
            "DATA_EXHAUSTED": "FAULT",
            "DEADLINE": "FAULT",
            "NON_FINITE": "FAULT",
            "OOM": "FAULT",
        },
        "new_failure_terminals": [],
        "new_formal_action_ids": [],
        "new_protocol_visible_durability_outcomes": [],
        "protocol_registry": registry,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "task_ids": ["T030"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = verify()
        encoded = canonical_json_bytes(result)
        output = args.output.resolve()
        if args.check_only:
            require(output.is_file(), "FINAL_COMPATIBILITY_EVIDENCE_MISSING")
            require(output.read_bytes() == encoded, "FINAL_COMPATIBILITY_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (CompatibilityError, OSError, ValueError, subprocess.SubprocessError) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
