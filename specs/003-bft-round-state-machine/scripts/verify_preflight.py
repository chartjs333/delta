"""Verify feature-003 predecessors, formal binding and architecture before native source."""

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
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
DEFAULT_OUTPUT = FEATURE / "evidence" / "preflight.json"

EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_FORMAL_SOURCE = "1e6e0f6f70056161d95933e71494ec390c7c1151"
EXPECTED_FORMAL_REPORT_SHA256 = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"
EXPECTED_FEATURE001_MERGE = "7795d3209fb5e3093cc4450c4d49701137d4aab4"
EXPECTED_FEATURE001_PARENTS = [
    "9460e762a211bb5ca41798156dab8a0b8eb42c4c",
    "4dac7f4b12403d2ff8a2362d43d70f42a7b162c2",
]
EXPECTED_FEATURE002_MERGE = "a48d2af86fc7a976cb20b6be28058d22b09cec54"
EXPECTED_FEATURE002_PARENT = EXPECTED_FEATURE001_MERGE
EXPECTED_FEATURE002_HEAD = "63656dd69c6d61d73cc8f040e81fb43a94c0a593"
EXPECTED_FEATURE002_TREE = "75ed7a5f1b39ee8b0989744abe77af1be4d8a676"
EXPECTED_FEATURE002_IMPLEMENTATION = "30dccd27325b851438f1df6ca8409ebad21bb5e5"
EXPECTED_FEATURE002_EVIDENCE = {
    "specs/002-local-round-engine/evidence/exit-gate.md": (
        "2433bdb9776c04c8b09b61cf7948e034b05a6ae2c56618082dd9cce058c69e05"
    ),
    "specs/002-local-round-engine/evidence/final-compatibility.json": (
        "916d9b3e2fa21eaf67fe2642381c883a1441896990744d332771e0019ccaed11"
    ),
    "specs/002-local-round-engine/evidence/predecessor-gate.json": (
        "9edbc2454895498a7c0570b0011359b84be8ed12d2408206aa63a40ee22d52b5"
    ),
}

SOURCE_ARTIFACTS = (
    ".specify/memory/constitution.md",
    "docs/adr/0010-hybrid-runtime-boundary.md",
    "specs/ROADMAP.md",
    "specs/003-bft-round-state-machine/checklists/hybrid-runtime.md",
    "specs/003-bft-round-state-machine/checklists/requirements.md",
    "specs/003-bft-round-state-machine/formal-refinement.md",
    "specs/003-bft-round-state-machine/plan.md",
    "specs/003-bft-round-state-machine/runtime-profile.md",
    "specs/003-bft-round-state-machine/runtime-tasks.md",
    "specs/003-bft-round-state-machine/scripts/verify_preflight.py",
    "specs/003-bft-round-state-machine/spec.md",
    "specs/003-bft-round-state-machine/task-map.md",
    "specs/003-bft-round-state-machine/tasks.md",
)

LEGACY_IMPLEMENTATION_PATTERNS = {
    "LEGACY_PYTHON_PACKAGE_PATH": re.compile(r"src/deltatorrent/"),
    "LEGACY_PYTHON_REFERENCE_RUNTIME": re.compile(r"Python 3\.12 reference implementation"),
    "PRODUCTION_QUANTIZER_PATH": re.compile(r"quantize\.py"),
    "PROTOBUF_IMPLEMENTATION_PATH": re.compile(r"proto/deltareduce/"),
    "GRPC_IMPLEMENTATION_PATH": re.compile(r"adapters/grpc/|loopback gRPC adapter"),
}

PURE_CORE_PATTERNS = {
    "SOCKET_DEPENDENCY": re.compile(
        r"(?:#\s*include\s*[<\"](?:sys/socket|winsock|asio|boost/asio)|\bsocket\s*\()",
        re.IGNORECASE,
    ),
    "FILESYSTEM_DEPENDENCY": re.compile(r"#\s*include\s*<filesystem>|std::filesystem"),
    "WALL_CLOCK_DEPENDENCY": re.compile(r"system_clock|GetSystemTime|CLOCK_REALTIME"),
    "JVM_DEPENDENCY": re.compile(r"jni\.h|JNIEnv|JavaVM"),
    "PYTHON_DEPENDENCY": re.compile(r"Python\.h|pybind11|PyObject"),
    "NONDETERMINISTIC_RANDOM": re.compile(r"random_device"),
    "FAST_MATH": re.compile(r"(?:-ffast-math|/fp:fast)"),
}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes, derive_formal_semantics_id  # noqa: E402


class PreflightError(RuntimeError):
    """A stable fail-closed preflight error."""


def reject(code: str, detail: str = "") -> None:
    raise PreflightError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        reject("GIT_COMMAND_FAILED", detail)
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def tracked_bytes(relative: str, revision: str) -> bytes:
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "UNSAFE_TRACKED_PATH", relative)
    return git_bytes("show", f"{revision}:{relative}")


def tracked_json(relative: str, revision: str) -> dict[str, Any]:
    try:
        document = json.loads(tracked_bytes(relative, revision).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("JSON_INVALID", f"{relative}:{exc}")
    require(isinstance(document, dict), "JSON_ROOT_INVALID", relative)
    return document


def require_ancestor(ancestor: str, descendant: str, code: str) -> None:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0, code)


def artifact_record(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}


def verify_feature001(source_commit: str) -> dict[str, Any]:
    parents = git_text("show", "-s", "--format=%P", EXPECTED_FEATURE001_MERGE).split()
    require(parents == EXPECTED_FEATURE001_PARENTS, "FEATURE001_MERGE_PARENTS_INVALID")
    require_ancestor(EXPECTED_FEATURE001_MERGE, source_commit, "FEATURE001_MERGE_NOT_ANCESTOR")

    gate_path = "specs/002-local-round-engine/evidence/predecessor-gate.json"
    gate_raw = tracked_bytes(gate_path, EXPECTED_FEATURE002_MERGE)
    require(
        sha256_bytes(gate_raw) == EXPECTED_FEATURE002_EVIDENCE[gate_path],
        "FEATURE001_GATE_HASH_MISMATCH",
    )
    gate = json.loads(gate_raw.decode("utf-8"))
    require(
        gate.get("status") == "PASS"
        and gate.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and gate.get("merged_predecessor", {}).get("merge_commit") == EXPECTED_FEATURE001_MERGE,
        "FEATURE001_GATE_INVALID",
    )
    evidence = gate.get("predecessor_evidence", {}).get("artifacts")
    require(isinstance(evidence, list) and len(evidence) == 4, "FEATURE001_EVIDENCE_INVALID")
    for record in evidence:
        require(isinstance(record, dict), "FEATURE001_EVIDENCE_RECORD_INVALID")
        path = record.get("path")
        digest = record.get("sha256")
        require(
            isinstance(path, str) and isinstance(digest, str), "FEATURE001_EVIDENCE_FIELDS_INVALID"
        )
        require(
            sha256_bytes(tracked_bytes(path, EXPECTED_FEATURE001_PARENTS[1])) == digest,
            "FEATURE001_EVIDENCE_HASH_MISMATCH",
            path,
        )
    return {
        "merge_commit": EXPECTED_FEATURE001_MERGE,
        "merge_parents": EXPECTED_FEATURE001_PARENTS,
        "evidence_artifacts": sorted(evidence, key=lambda item: item["path"]),
        "status": "PASS",
    }


def _verify_completed_tasks(revision: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for path, expression, expected in (
        ("specs/002-local-round-engine/tasks.md", r"\bT\d{3}\b", 32),
        ("specs/002-local-round-engine/runtime-tasks.md", r"HR002-\d{3}", 9),
    ):
        text = tracked_bytes(path, revision).decode("utf-8")
        require(
            not re.findall(r"^- \[ \] ", text, re.MULTILINE), "FEATURE002_TASK_INCOMPLETE", path
        )
        identifiers = sorted(set(re.findall(expression, text)))
        require(len(identifiers) == expected, "FEATURE002_TASK_SET_INVALID", path)
        result["T" if expression.startswith(r"\bT") else "HR002"] = len(identifiers)
    return result


def verify_feature002(source_commit: str) -> dict[str, Any]:
    parents = git_text("show", "-s", "--format=%P", EXPECTED_FEATURE002_MERGE).split()
    require(parents == [EXPECTED_FEATURE002_PARENT], "FEATURE002_SQUASH_PARENT_INVALID")
    merge_tree = git_text("rev-parse", f"{EXPECTED_FEATURE002_MERGE}^{{tree}}")
    # A squash-merged PR head is not part of main's ancestry and GitHub's checkout
    # does not promise to fetch deleted feature refs.  The immutable merge tree and
    # content-addressed exit evidence are the offline-verifiable acceptance boundary.
    require(merge_tree == EXPECTED_FEATURE002_TREE, "FEATURE002_MERGED_TREE_INVALID")
    require_ancestor(EXPECTED_FEATURE002_MERGE, source_commit, "FEATURE002_MERGE_NOT_ANCESTOR")

    artifacts = []
    for path, expected in sorted(EXPECTED_FEATURE002_EVIDENCE.items()):
        record = artifact_record(path, EXPECTED_FEATURE002_MERGE)
        require(record["sha256"] == expected, "FEATURE002_EVIDENCE_HASH_MISMATCH", path)
        artifacts.append(record)

    predecessor = tracked_json(
        "specs/002-local-round-engine/evidence/predecessor-gate.json",
        EXPECTED_FEATURE002_MERGE,
    )
    compatibility = tracked_json(
        "specs/002-local-round-engine/evidence/final-compatibility.json",
        EXPECTED_FEATURE002_MERGE,
    )
    exit_gate = tracked_bytes(
        "specs/002-local-round-engine/evidence/exit-gate.md", EXPECTED_FEATURE002_MERGE
    ).decode("utf-8")
    require(predecessor.get("status") == "PASS", "FEATURE002_PREDECESSOR_INVALID")
    require(
        compatibility.get("status") == "PASS"
        and compatibility.get("classification") == "REFINEMENT_ONLY"
        and compatibility.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and compatibility.get("formal_semantic_artifact_count") == 24
        and compatibility.get("new_formal_action_ids") == []
        and compatibility.get("new_failure_terminals") == []
        and compatibility.get("new_protocol_visible_durability_outcomes") == [],
        "FEATURE002_COMPATIBILITY_INVALID",
    )
    require(
        "**Decision**: PASS" in exit_gate
        and EXPECTED_FEATURE002_IMPLEMENTATION in exit_gate
        and EXPECTED_FORMAL_ID in exit_gate,
        "FEATURE002_EXIT_GATE_INVALID",
    )
    return {
        "accepted_branch_head": EXPECTED_FEATURE002_HEAD,
        "evidence_artifacts": artifacts,
        "implementation_source_commit": EXPECTED_FEATURE002_IMPLEMENTATION,
        "merge_commit": EXPECTED_FEATURE002_MERGE,
        "merge_parent": EXPECTED_FEATURE002_PARENT,
        "merged_tree": EXPECTED_FEATURE002_TREE,
        "status": "PASS",
        "task_counts": _verify_completed_tasks(EXPECTED_FEATURE002_MERGE),
    }


def discover_semantic_artifacts(revision: str) -> list[dict[str, str]]:
    paths = git_text(
        "ls-tree",
        "-r",
        "--name-only",
        revision,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    ).splitlines()
    artifacts: list[dict[str, str]] = []
    for path in paths:
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
            artifacts.append(
                {"kind": kind, "path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}
            )
    return sorted(artifacts, key=lambda item: (item["path"], item["kind"]))


def verify_formal(source_commit: str) -> dict[str, Any]:
    artifacts = discover_semantic_artifacts(source_commit)
    require(len(artifacts) == 24, "FORMAL_ARTIFACT_COUNT_INVALID")
    semantics = tracked_json("formal/reports/formal-semantics.json", source_commit)
    require(semantics.get("semantic_artifacts") == artifacts, "FORMAL_ARTIFACT_MANIFEST_DRIFT")
    derived = derive_formal_semantics_id("1.0.0", artifacts)
    require(derived == EXPECTED_FORMAL_ID, "FORMAL_SEMANTICS_ID_DRIFT")

    report_path = "formal/reports/formal-verification-report.json"
    report_raw = tracked_bytes(report_path, source_commit)
    require(
        sha256_bytes(report_raw) == EXPECTED_FORMAL_REPORT_SHA256,
        "FORMAL_REPORT_HASH_MISMATCH",
    )
    report = json.loads(report_raw.decode("utf-8"))
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == derived
        and report.get("source_tree", {}).get("commit") == EXPECTED_FORMAL_SOURCE,
        "FORMAL_REPORT_NOT_EXACT_GO",
    )
    nodes = report.get("evidence_graph", {}).get("nodes")
    require(isinstance(nodes, list) and len(nodes) == 10, "FORMAL_EVIDENCE_GRAPH_INVALID")
    for node in nodes:
        require(isinstance(node, dict), "FORMAL_EVIDENCE_NODE_INVALID")
        path = node.get("path")
        digest = node.get("sha256")
        require(isinstance(path, str) and isinstance(digest, str), "FORMAL_EVIDENCE_FIELDS_INVALID")
        require(
            sha256_bytes(tracked_bytes(path, source_commit)) == digest,
            "FORMAL_EVIDENCE_HASH_MISMATCH",
            path,
        )
    reviews = report.get("review_attestations")
    reviewers = {
        item.get("reviewer_id")
        for item in reviews or []
        if isinstance(item, dict) and item.get("status") == "PASS" and item.get("independent")
    }
    require(len(reviewers) == 2 and None not in reviewers, "FORMAL_REVIEW_INDEPENDENCE_INVALID")
    return {
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "decision": "GO",
        "evidence_node_count": len(nodes),
        "formal_semantics_id": derived,
        "report_sha256": EXPECTED_FORMAL_REPORT_SHA256,
        "reviewers": sorted(reviewers),
        "source_commit": EXPECTED_FORMAL_SOURCE,
    }


def _source_paths(revision: str) -> list[str]:
    raw = git_bytes("ls-tree", "-r", "-z", "--name-only", revision)
    return [path for path in raw.decode("utf-8").split("\0") if path]


def verify_architecture(source_commit: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    planned_paths = [
        path for path in SOURCE_ARTIFACTS if path.startswith("specs/003-") and path.endswith(".md")
    ]
    planned_text = "\n".join(
        tracked_bytes(path, source_commit).decode("utf-8") for path in planned_paths
    )
    for identifier, pattern in LEGACY_IMPLEMENTATION_PATTERNS.items():
        match = pattern.search(planned_text)
        if match:
            findings.append({"id": identifier, "path": "specs/003-bft-round-state-machine"})

    required_fragments = (
        "delta-core-cpp",
        "delta-runtime-cpp",
        "delta-ffi",
        "delta-node-java",
        "C++20",
        "JDK 25 FFM",
        "REFINEMENT_ONLY",
        EXPECTED_FORMAL_ID,
    )
    for fragment in required_fragments:
        if fragment not in planned_text:
            findings.append({"id": "REQUIRED_NATIVE_BOUNDARY_MISSING", "path": fragment})

    paths = _source_paths(source_commit)
    core_sources = [
        path
        for path in paths
        if path.startswith("delta-core-cpp/")
        and Path(path).suffix.lower() in {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}
    ]
    for path in core_sources:
        text = tracked_bytes(path, source_commit).decode("utf-8", errors="replace")
        for identifier, pattern in PURE_CORE_PATTERNS.items():
            if pattern.search(text):
                findings.append({"id": identifier, "path": path})

    python_validator_paths = [
        path
        for path in paths
        if path.startswith("delta-worker-python/src/")
        and re.search(r"(?:^|/)(?:validator|consensus|bft)(?:[_.-]|/)", path, re.IGNORECASE)
    ]
    for path in python_validator_paths:
        findings.append({"id": "PYTHON_VALIDATOR_STATE_PATH", "path": path})

    java_sources = [
        path for path in paths if path.startswith("delta-node-java/") and path.endswith(".java")
    ]
    for path in java_sources:
        text = tracked_bytes(path, source_commit).decode("utf-8", errors="replace")
        if re.search(r"\b(?:changeView|hardAbort|finalizeQC|applyQC)\s*\(", text):
            findings.append({"id": "JAVA_TRANSITION_DECISION", "path": path})

    require(not findings, "ARCHITECTURE_FINDINGS_PRESENT", json.dumps(findings, sort_keys=True))
    return {
        "finding_count": 0,
        "findings": [],
        "java_source_count": len(java_sources),
        "planned_artifact_count": len(planned_paths),
        "pure_core_source_count": len(core_sources),
        "python_validator_path_count": len(python_validator_paths),
        "rules": sorted([*LEGACY_IMPLEMENTATION_PATTERNS, *PURE_CORE_PATTERNS]),
        "status": "PASS",
    }


def verify_formal_impact(source_commit: str) -> dict[str, Any]:
    adr_path = "docs/adr/0010-hybrid-runtime-boundary.md"
    text = tracked_bytes(adr_path, source_commit).decode("utf-8")
    require("**Status**: Accepted" in text, "ADR0010_NOT_ACCEPTED")
    require(
        f"**Formal impact**: `REFINEMENT_ONLY` against formal semantics `{EXPECTED_FORMAL_ID}`"
        in text,
        "ADR0010_FORMAL_BINDING_INVALID",
    )
    require(
        "This ADR does not add a formal action" in text
        and "work stops and feature 000 is amended" in text,
        "ADR0010_STOP_RULE_INVALID",
    )
    return {
        "adr": artifact_record(adr_path, source_commit),
        "classification": "REFINEMENT_ONLY",
        "new_failure_terminals": [],
        "new_formal_action_ids": [],
        "new_protocol_visible_durability_outcomes": [],
        "status": "PASS",
    }


def verify_source_contract(source_commit: str) -> dict[str, Any]:
    require_ancestor(source_commit, "HEAD", "PREFLIGHT_SOURCE_NOT_ANCESTOR")
    artifacts = [artifact_record(path, source_commit) for path in SOURCE_ARTIFACTS]
    constitution = tracked_bytes(".specify/memory/constitution.md", source_commit).decode("utf-8")
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_INVALID")
    return {
        "artifacts": artifacts,
        "commit": source_commit,
        "constitution_version": "2.1.0",
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }


def verify(source_commit: str) -> dict[str, Any]:
    return {
        "architecture": verify_architecture(source_commit),
        "checks": [
            "FEATURE001_MERGE_AND_EVIDENCE_EXACT",
            "FEATURE002_SQUASH_TREE_AND_EVIDENCE_EXACT",
            "PREDECESSOR_TASKS_COMPLETE",
            "FORMAL_GO_EXACT",
            "FORMAL_SEMANTIC_ARTIFACTS_REDERIVED",
            "ADR0010_REFINEMENT_ONLY",
            "ZERO_ARCHITECTURE_FINDINGS",
            "SOURCE_TREE_BOUND",
        ],
        "errors": [],
        "feature001": verify_feature001(source_commit),
        "feature002": verify_feature002(source_commit),
        "formal": verify_formal(source_commit),
        "formal_impact": verify_formal_impact(source_commit),
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source_tree": verify_source_contract(source_commit),
        "status": "PASS",
        "task_ids": ["T000", "T001", "T002", "T003", "HR003-001", "HR003-002", "HR003-003"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def _source_for_check(output: Path, check_only: bool) -> str:
    if not check_only:
        dirty = git_text("status", "--porcelain", "--untracked-files=all")
        require(not dirty, "SOURCE_TREE_NOT_CLEAN")
        return git_text("rev-parse", "HEAD")
    require(output.is_file(), "PREFLIGHT_EVIDENCE_MISSING")
    try:
        existing = json.loads(output.read_text(encoding="utf-8"))
        source = existing["source_tree"]["commit"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        reject("PREFLIGHT_EVIDENCE_INVALID", str(exc))
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "PREFLIGHT_SOURCE_INVALID",
    )
    return source


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    try:
        source_commit = _source_for_check(output, args.check_only)
        result = verify(source_commit)
        encoded = canonical_json_bytes(result)
        if args.check_only:
            require(output.read_bytes() == encoded, "PREFLIGHT_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (PreflightError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
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
