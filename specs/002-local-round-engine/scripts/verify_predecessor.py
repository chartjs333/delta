"""Verify the exact merged feature-001 predecessor before feature-002 code."""

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
DEFAULT_OUTPUT = FEATURE / "evidence" / "predecessor-gate.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_FORMAL_SOURCE = "1e6e0f6f70056161d95933e71494ec390c7c1151"
EXPECTED_FORMAL_REPORT_SHA256 = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"
EXPECTED_PREDECESSOR_HEAD = "4dac7f4b12403d2ff8a2362d43d70f42a7b162c2"
EXPECTED_MERGE_COMMIT = "7795d3209fb5e3093cc4450c4d49701137d4aab4"
EXPECTED_MERGE_FIRST_PARENT = "9460e762a211bb5ca41798156dab8a0b8eb42c4c"

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes, derive_formal_semantics_id  # noqa: E402


class GateError(RuntimeError):
    pass


def reject(code: str, detail: str = "") -> None:
    raise GateError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        reject("GIT_COMMAND_FAILED", completed.stderr.decode("utf-8", errors="replace").strip())
    return completed.stdout


def tracked_bytes(relative: str, revision: str = EXPECTED_PREDECESSOR_HEAD) -> bytes:
    if relative.startswith("/") or ".." in Path(relative).parts:
        reject("UNSAFE_TRACKED_PATH", relative)
    return git_bytes("show", f"{revision}:{relative}")


def load_tracked_json(relative: str, revision: str = EXPECTED_PREDECESSOR_HEAD) -> dict[str, Any]:
    raw = tracked_bytes(relative, revision)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("JSON_INVALID", f"{relative}:{exc}")
    require(isinstance(value, dict), "JSON_ROOT_INVALID", relative)
    return value


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def verify_merge() -> dict[str, object]:
    parents = git_bytes("show", "-s", "--format=%P", EXPECTED_MERGE_COMMIT).decode().split()
    require(
        parents == [EXPECTED_MERGE_FIRST_PARENT, EXPECTED_PREDECESSOR_HEAD],
        "PREDECESSOR_MERGE_PARENTS_INVALID",
    )
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_MERGE_COMMIT, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    require(ancestry.returncode == 0, "PREDECESSOR_MERGE_NOT_ANCESTOR")
    return {
        "first_parent": EXPECTED_MERGE_FIRST_PARENT,
        "merge_commit": EXPECTED_MERGE_COMMIT,
        "predecessor_head": EXPECTED_PREDECESSOR_HEAD,
    }


def verify_task_completion() -> dict[str, int]:
    counts: dict[str, int] = {}
    for relative, prefix in (
        ("specs/001-reproducible-training-baseline/tasks.md", "T"),
        ("specs/001-reproducible-training-baseline/runtime-tasks.md", "HR001-"),
    ):
        text = tracked_bytes(relative).decode("utf-8")
        unchecked = [line for line in text.splitlines() if re.match(r"^- \[ \] ", line)]
        require(not unchecked, "PREDECESSOR_TASK_INCOMPLETE", relative)
        if prefix == "T":
            identifiers = set(re.findall(r"\bT\d{3}\b", text))
            require({f"T{index:03d}" for index in range(36)} <= identifiers, "T_TASK_SET_INVALID")
        else:
            identifiers = set(re.findall(r"HR001-\d{3}", text))
            require(
                {f"HR001-{index:03d}" for index in range(1, 16)} <= identifiers,
                "HR_TASK_SET_INVALID",
            )
        counts[prefix] = len(identifiers)
    return counts


def verify_semantics() -> dict[str, object]:
    semantics = load_tracked_json("formal/reports/formal-semantics.json")
    artifacts = semantics.get("semantic_artifacts")
    require(isinstance(artifacts, list), "SEMANTIC_ARTIFACTS_INVALID")
    actual: list[dict[str, str]] = []
    for item in artifacts:
        require(
            isinstance(item, dict) and set(item) == {"kind", "path", "sha256"},
            "SEMANTIC_ARTIFACT_INVALID",
        )
        path = item["path"]
        require(isinstance(path, str), "SEMANTIC_PATH_INVALID")
        current = tracked_bytes(path, "HEAD")
        expected = tracked_bytes(path)
        require(current == expected, "FORMAL_SEMANTIC_SOURCE_DRIFT", path)
        actual.append(
            {
                "kind": str(item["kind"]),
                "path": path,
                "sha256": sha256(current),
            }
        )
    actual.sort(key=lambda item: (item["path"], item["kind"]))
    require(actual == artifacts, "SEMANTIC_MANIFEST_HASH_MISMATCH")
    derived = derive_formal_semantics_id("1.0.0", actual)
    require(derived == EXPECTED_FORMAL_ID, "FORMAL_SEMANTICS_ID_DRIFT")
    return {"artifact_count": len(actual), "derived_id": derived}


def verify_formal_report() -> dict[str, object]:
    relative = "formal/reports/formal-verification-report.json"
    raw = tracked_bytes(relative)
    require(sha256(raw) == EXPECTED_FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_MISMATCH")
    report = load_tracked_json(relative)
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "FORMAL_REPORT_NOT_COMPATIBLE_GO",
    )
    source = report.get("source_tree")
    require(
        isinstance(source, dict) and source.get("commit") == EXPECTED_FORMAL_SOURCE,
        "FORMAL_SOURCE_COMMIT_MISMATCH",
    )
    nodes = report.get("evidence_graph", {}).get("nodes", [])
    require(isinstance(nodes, list) and len(nodes) == 10, "FORMAL_EVIDENCE_GRAPH_INVALID")
    for node in nodes:
        require(isinstance(node, dict), "FORMAL_EVIDENCE_NODE_INVALID")
        path = node.get("path")
        digest = node.get("sha256")
        require(isinstance(path, str) and isinstance(digest, str), "EVIDENCE_NODE_FIELDS_INVALID")
        require(sha256(tracked_bytes(path)) == digest, "FORMAL_EVIDENCE_HASH_MISMATCH", path)
    reviews = report.get("review_attestations")
    require(isinstance(reviews, list) and len(reviews) == 2, "REVIEW_ATTESTATIONS_INVALID")
    reviewers = {item.get("reviewer_id") for item in reviews if isinstance(item, dict)}
    require(len(reviewers) == 2 and None not in reviewers, "REVIEWER_INDEPENDENCE_INVALID")
    return {
        "decision": "GO",
        "evidence_nodes": len(nodes),
        "reviewers": sorted(str(item) for item in reviewers),
        "sha256": EXPECTED_FORMAL_REPORT_SHA256,
        "source_commit": EXPECTED_FORMAL_SOURCE,
    }


def verify_predecessor_evidence() -> dict[str, object]:
    formal_prerequisite = load_tracked_json(
        "specs/001-reproducible-training-baseline/evidence/formal-prerequisite.json"
    )
    foundation = load_tracked_json(
        "specs/001-reproducible-training-baseline/evidence/foundation-gate.json"
    )
    compatibility = load_tracked_json(
        "specs/001-reproducible-training-baseline/evidence/final-compatibility.json"
    )
    exit_gate = tracked_bytes(
        "specs/001-reproducible-training-baseline/evidence/exit-gate.md"
    ).decode("utf-8")
    require(
        formal_prerequisite.get("status") == "PASS"
        and formal_prerequisite.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "FEATURE001_FORMAL_PREREQUISITE_INVALID",
    )
    require(
        foundation.get("status") == "PASS"
        and foundation.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and foundation.get("network_policy") == "PUBLIC_NETWORK_BLOCKED"
        and all(item.get("status") == "PASS" for item in foundation.get("commands", [])),
        "FEATURE001_FOUNDATION_INVALID",
    )
    require(
        compatibility.get("status") == "PASS"
        and compatibility.get("classification") == "REFINEMENT_ONLY"
        and compatibility.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and compatibility.get("formal_semantic_artifact_count") == 24
        and compatibility.get("new_formal_action_ids") == []
        and compatibility.get("new_failure_terminals") == []
        and compatibility.get("new_protocol_visible_durability_outcomes") == []
        and compatibility.get("semantic_completeness_claimed") is False,
        "FEATURE001_FINAL_COMPATIBILITY_INVALID",
    )
    require(
        "**Decision**: PASS" in exit_gate
        and "57 tests" in exit_gate
        and EXPECTED_FORMAL_ID in exit_gate,
        "FEATURE001_EXIT_GATE_INVALID",
    )
    paths = [
        "specs/001-reproducible-training-baseline/evidence/exit-gate.md",
        "specs/001-reproducible-training-baseline/evidence/final-compatibility.json",
        "specs/001-reproducible-training-baseline/evidence/formal-prerequisite.json",
        "specs/001-reproducible-training-baseline/evidence/foundation-gate.json",
    ]
    return {
        "artifacts": [
            {"path": path, "sha256": sha256(tracked_bytes(path))} for path in sorted(paths)
        ],
        "classification": "REFINEMENT_ONLY",
        "status": "PASS",
    }


def verify_protocol_registry() -> dict[str, object]:
    registry = load_tracked_json("delta-protocol/registry.json")
    require(registry.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "REGISTRY_ID_MISMATCH")
    schemas = registry.get("schemas")
    media = registry.get("media_types")
    require(isinstance(schemas, list) and isinstance(media, list), "REGISTRY_SHAPE_INVALID")
    schema_ids: set[str] = set()
    for item in schemas:
        require(isinstance(item, dict), "REGISTRY_SCHEMA_INVALID")
        identifier = item.get("id")
        path = item.get("path")
        digest = item.get("sha256")
        require(
            isinstance(identifier, str) and isinstance(path, str) and isinstance(digest, str),
            "REGISTRY_SCHEMA_FIELDS_INVALID",
        )
        require(sha256(tracked_bytes(f"delta-protocol/{path}")) == digest, "SCHEMA_HASH_MISMATCH")
        schema_ids.add(identifier)
    require(
        all(isinstance(item, dict) and item.get("schema_id") in schema_ids for item in media),
        "REGISTRY_MEDIA_SCHEMA_INVALID",
    )
    action = registry.get("action_registry")
    require(isinstance(action, dict), "ACTION_REGISTRY_DESCRIPTOR_INVALID")
    action_path = action.get("path")
    require(isinstance(action_path, str), "ACTION_REGISTRY_PATH_INVALID")
    action_bytes = tracked_bytes(f"delta-protocol/{action_path}")
    require(sha256(action_bytes) == action.get("sha256"), "ACTION_REGISTRY_HASH_MISMATCH")
    action_registry = json.loads(action_bytes.decode("utf-8"))
    require(
        isinstance(action_registry, dict)
        and action_registry.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "ACTION_REGISTRY_SEMANTICS_MISMATCH",
    )
    return {
        "media_type_count": len(media),
        "registry_sha256": sha256(tracked_bytes("delta-protocol/registry.json")),
        "schema_count": len(schemas),
    }


def verify() -> dict[str, object]:
    return {
        "checks": [
            "FEATURE001_MERGE_EXACT",
            "FEATURE001_TASKS_COMPLETE",
            "FEATURE001_EXIT_EVIDENCE_PASS",
            "FORMAL_GO_EXACT",
            "FORMAL_SEMANTICS_REDERIVED",
            "PROTOCOL_REGISTRY_VERIFIED",
            "NO_FORMAL_SEMANTIC_DRIFT",
        ],
        "errors": [],
        "formal_impact": {
            "classification": "REFINEMENT_ONLY",
            "new_failure_terminals": [],
            "new_formal_action_ids": [],
            "new_protocol_visible_durability_outcomes": [],
        },
        "formal_report": verify_formal_report(),
        "formal_semantics": verify_semantics(),
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "merged_predecessor": verify_merge(),
        "predecessor_evidence": verify_predecessor_evidence(),
        "predecessor_tasks": verify_task_completion(),
        "protocol_registry": verify_protocol_registry(),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "task_ids": ["HR002-001", "T000"],
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
            require(output.is_file(), "PREDECESSOR_EVIDENCE_MISSING")
            require(output.read_bytes() == encoded, "PREDECESSOR_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
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
