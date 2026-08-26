#!/usr/bin/env python3
"""Offline, fail-closed verification of the merged feature-000 Formal GO."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[3]
FEATURE_ROOT = ROOT / "specs" / "001-reproducible-training-baseline"
DEFAULT_REPORT = ROOT / "formal" / "reports" / "formal-verification-report.json"
DEFAULT_OUTPUT = FEATURE_ROOT / "evidence" / "formal-prerequisite.json"
EXPECTED_SEMANTICS_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_SOURCE_COMMIT = "1e6e0f6f70056161d95933e71494ec390c7c1151"
SEMANTICS_DOMAIN = "deltareduce.formal-semantics.v1"
REVIEW_SCOPE = {"COVERAGE", "LIVENESS", "MODEL", "PROOFS"}
TOOLCHAIN_IDS = {
    "TOOLCHAIN-CONTAINER",
    "TOOLCHAIN-JRE",
    "TOOLCHAIN-LEAN",
    "TOOLCHAIN-TLA",
}
MUTANT_IDS = {
    "MUT-CURRENT-WITHOUT-APPLYQC",
    "MUT-DUPLICATE-COMMITMENT",
    "MUT-EARLY-SEED",
    "MUT-INCOMPLETE-AGGREGATE",
    "MUT-MISSING-APC-PARENT",
    "MUT-MISSING-DURABLE-VOTE",
    "MUT-MISSING-SHARD-PARENT",
    "MUT-MUTABLE-ISC",
    "MUT-PARTIAL-PUBLICATION",
    "MUT-UNCHECKED-OVERFLOW",
}
EVIDENCE_IDS = {
    "EVIDENCE-CROSS-ARTIFACT",
    "EVIDENCE-LEAN",
    "EVIDENCE-MUTANTS",
    "EVIDENCE-REFINEMENT",
    "EVIDENCE-REPRODUCIBILITY",
    "EVIDENCE-REVIEW-1",
    "EVIDENCE-REVIEW-2",
    "EVIDENCE-SEMANTICS",
    "EVIDENCE-TLC",
    "EVIDENCE-TOOLCHAINS",
}
PROTECTED_BASELINE_ROLES = {
    "canonical_rational_rounding_decision",
    "constitution",
    "deltareduce_architecture_decision",
    "feature_plan",
    "feature_specification",
    "feature_tasks",
    "formal_gate_decision",
    "normative_failure_recovery_contract",
    "normative_parametric_proof_contract",
    "normative_refinement_contract",
    "stable_formal_id_registry",
}
REFINEMENT_OVERLAY_ROLES = {
    "authoritative_branch_topology",
    "execution_contract",
}
LOCK_PATHS = {
    "container": "formal/toolchain/container.lock",
    "dependencies": "formal/proofs/dependencies.lock.json",
    "lean": "formal/toolchain/lean.lock",
    "tla": "formal/toolchain/tla.lock",
}
HYBRID_DOCUMENTS = {
    "architecture": "docs/architecture/hybrid-runtime.md",
    "decision": "docs/adr/0010-hybrid-runtime-boundary.md",
    "runtime_map": "specs/HYBRID-RUNTIME-MAP.md",
    "source_provenance": "docs/source/hybrid-runtime-v1-amendment.md",
}


class PrerequisiteError(RuntimeError):
    """A stable, machine-readable prerequisite rejection."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def reject(code: str, detail: str = "") -> NoReturn:
    raise PrerequisiteError(code, detail)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            reject("JSON_DUPLICATE_KEY", key)
        result[key] = value
    return result


def parse_json_strict(value: bytes, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("JSON_INVALID", f"{label}: {exc}")
    require(isinstance(parsed, dict), "JSON_ROOT_NOT_OBJECT", label)
    return parsed


def load_json_strict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        reject("REPORT_MISSING" if path == DEFAULT_REPORT else "JSON_FILE_MISSING", str(path))
    return parse_json_strict(path.read_bytes(), str(path))


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalized_text_sha256(value: bytes) -> str:
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        reject("BASELINE_INPUT_NOT_UTF8", str(exc))
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256_bytes(normalized.encode("utf-8"))


def safe_repo_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    require(
        "\\" not in relative and not pure.is_absolute() and ".." not in pure.parts,
        "UNSAFE_REPOSITORY_PATH",
        relative,
    )
    path = (root / Path(*pure.parts)).resolve()
    require(path.is_relative_to(root.resolve()), "UNSAFE_REPOSITORY_PATH", relative)
    return path


def git_bytes(root: Path, *args: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if check and completed.returncode != 0:
        reject(
            "GIT_COMMAND_FAILED",
            f"git {' '.join(args)}: {completed.stderr.decode('utf-8', errors='replace').strip()}",
        )
    return completed.stdout


def git_text(root: Path, *args: str, check: bool = True) -> str:
    return git_bytes(root, *args, check=check).decode("utf-8").strip()


def tracked_bytes(root: Path, relative: str, revision: str = "HEAD") -> bytes:
    safe_repo_path(root, relative)
    return git_bytes(root, "show", f"{revision}:{relative}")


def load_tracked_json(root: Path, relative: str, revision: str = "HEAD") -> dict[str, Any]:
    return parse_json_strict(tracked_bytes(root, relative, revision), f"{revision}:{relative}")


def sha256_tracked(root: Path, relative: str, revision: str = "HEAD") -> str:
    return sha256_bytes(tracked_bytes(root, relative, revision))


def git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def verify_merged_predecessor(root: Path, report_path: Path, source_commit: str) -> dict[str, str]:
    head = git_text(root, "rev-parse", "HEAD")
    origin_main = git_text(root, "rev-parse", "origin/main")
    require(git_is_ancestor(root, source_commit, head), "FORMAL_SOURCE_NOT_ANCESTOR")

    canonical_report = DEFAULT_REPORT.relative_to(root).as_posix()
    report_commit = git_text(root, "log", "-1", "--format=%H", "--", canonical_report)
    require(len(report_commit) == 40, "REPORT_COMMIT_NOT_FOUND")
    require(git_is_ancestor(root, report_commit, head), "GO_REPORT_NOT_ANCESTOR")

    merge_commit = ""
    merge_parent = ""
    for candidate in git_text(root, "rev-list", "--first-parent", "--merges", head).splitlines():
        parents = git_text(root, "show", "-s", "--format=%P", candidate).split()
        for parent in parents[1:]:
            if git_is_ancestor(root, report_commit, parent):
                merge_commit = candidate
                merge_parent = parent
                break
        if merge_commit:
            break
    require(bool(merge_commit), "FORMAL_GO_NOT_MERGED")
    require(git_is_ancestor(root, merge_commit, origin_main), "FORMAL_MERGE_NOT_ON_ORIGIN_MAIN")
    subject = git_text(root, "show", "-s", "--format=%s", merge_commit)
    require(subject.startswith("Merge pull request #1 "), "UNEXPECTED_FORMAL_MERGE", subject)
    require(report_path.resolve() == DEFAULT_REPORT.resolve(), "NONCANONICAL_REPORT_PATH")
    return {
        "feature_head": head,
        "merge_commit": merge_commit,
        "merged_report_parent": merge_parent,
        "origin_main": origin_main,
        "report_commit": report_commit,
    }


def verify_status_records(
    records: list[dict[str, Any]], expected_ids: set[str], category: str, evidence_ids: set[str]
) -> None:
    actual_ids = {record.get("id") for record in records}
    require(actual_ids == expected_ids, f"{category}_ID_SET_MISMATCH")
    require(len(records) == len(actual_ids), f"{category}_DUPLICATE_ID")
    for record in records:
        require(record.get("mandatory") is True, f"{category}_NOT_MANDATORY", str(record.get("id")))
        require(record.get("status") == "PASS", f"{category}_FAILED", str(record.get("id")))
        require(record.get("verified") is True, f"{category}_UNVERIFIED", str(record.get("id")))
        require(
            record.get("evidence_id") in evidence_ids,
            f"{category}_EVIDENCE_INVALID",
            str(record.get("id")),
        )


def verify_evidence_graph(report: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    graph = report.get("evidence_graph")
    require(isinstance(graph, dict), "EVIDENCE_GRAPH_MISSING")
    nodes = graph.get("nodes")
    require(isinstance(nodes, list), "EVIDENCE_NODES_MISSING")
    by_id: dict[str, dict[str, Any]] = {}
    loaded: dict[str, dict[str, Any]] = {}
    for node in nodes:
        identifier = node.get("id")
        require(isinstance(identifier, str) and identifier not in by_id, "EVIDENCE_ID_INVALID")
        by_id[identifier] = node
        require(
            node.get("media_type") == "application/json", "EVIDENCE_MEDIA_TYPE_INVALID", identifier
        )
        relative = str(node.get("path", ""))
        safe_repo_path(root, relative)
        value = tracked_bytes(root, relative)
        require(sha256_bytes(value) == node.get("sha256"), "EVIDENCE_HASH_MISMATCH", identifier)
        loaded[identifier] = parse_json_strict(value, f"HEAD:{relative}")
    require(set(by_id) == EVIDENCE_IDS, "EVIDENCE_ID_SET_MISMATCH")
    edges = graph.get("edges")
    require(isinstance(edges, list), "EVIDENCE_EDGES_INVALID")
    for edge in edges:
        require(edge.get("from") in by_id and edge.get("to") in by_id, "EVIDENCE_EDGE_INVALID")
    return loaded


def verify_source_and_semantics(report: dict[str, Any], root: Path) -> dict[str, Any]:
    source = report.get("source_tree")
    require(isinstance(source, dict), "SOURCE_TREE_MISSING")
    require(source.get("clean") is True, "SOURCE_TREE_NOT_CLEAN")
    require(source.get("commit") == EXPECTED_SOURCE_COMMIT, "SOURCE_COMMIT_MISMATCH")
    manifest_relative = str(source.get("manifest_path", ""))
    safe_repo_path(root, manifest_relative)
    require(
        sha256_tracked(root, manifest_relative) == source.get("tree_sha256"),
        "SOURCE_MANIFEST_HASH_MISMATCH",
    )
    manifest = load_tracked_json(root, manifest_relative)
    require(manifest.get("commit") == EXPECTED_SOURCE_COMMIT, "SOURCE_MANIFEST_COMMIT_MISMATCH")
    files = manifest.get("files")
    require(isinstance(files, list), "SOURCE_MANIFEST_FILES_INVALID")
    manifest_paths = [item.get("path") for item in files]
    require(manifest_paths == sorted(manifest_paths), "SOURCE_MANIFEST_NOT_SORTED")
    require(len(manifest_paths) == len(set(manifest_paths)), "SOURCE_MANIFEST_DUPLICATE_PATH")
    for item in files:
        relative = str(item.get("path", ""))
        safe_repo_path(root, relative)
        require(
            sha256_tracked(root, relative) == item.get("sha256"),
            "SOURCE_MANIFEST_FILE_HASH_MISMATCH",
            relative,
        )

    artifacts = source.get("semantic_artifacts")
    require(isinstance(artifacts, list) and artifacts, "SEMANTIC_ARTIFACTS_MISSING")
    ordered = sorted(artifacts, key=lambda item: (item["path"], item["kind"]))
    require(artifacts == ordered, "SEMANTIC_ARTIFACTS_NOT_SORTED")
    for artifact in artifacts:
        safe_repo_path(root, artifact["path"])
        require(
            sha256_tracked(root, artifact["path"]) == artifact["sha256"],
            "SEMANTIC_ARTIFACT_HASH_MISMATCH",
            artifact["path"],
        )
    payload = {
        "artifacts": ordered,
        "domain": SEMANTICS_DOMAIN,
        "formal_semantics_version": report.get("formal_semantics_version"),
    }
    derived = f"sha256:{sha256_bytes(canonical_json_bytes(payload))}"
    require(derived == EXPECTED_SEMANTICS_ID, "SEMANTICS_DERIVATION_MISMATCH")
    return {
        "artifact_count": len(artifacts),
        "derived_id": derived,
        "source_manifest_sha256": sha256_tracked(root, manifest_relative),
    }


def verify_baseline_inputs(report: dict[str, Any], root: Path) -> dict[str, Any]:
    declared = report.get("baseline_inputs")
    require(
        isinstance(declared, dict) and declared.get("verified") is True,
        "BASELINE_INPUTS_UNVERIFIED",
    )
    relative_path = str(declared.get("path", ""))
    path = safe_repo_path(root, relative_path)
    require(
        sha256_tracked(root, relative_path) == declared.get("sha256"),
        "BASELINE_INPUTS_HASH_MISMATCH",
    )
    baseline = load_tracked_json(root, relative_path)
    require(
        baseline.get("formal_semantics_id") == EXPECTED_SEMANTICS_ID, "BASELINE_SEMANTICS_MISMATCH"
    )
    require(
        baseline.get("input_bundle_sha256") == declared.get("input_bundle_sha256"),
        "BASELINE_BUNDLE_ID_MISMATCH",
    )
    inputs = baseline.get("inputs")
    require(isinstance(inputs, list) and inputs, "BASELINE_INPUTS_EMPTY")
    protected: list[dict[str, str]] = []
    overlay: list[dict[str, str]] = []
    bundle_records: list[str] = []
    roles = {item.get("role") for item in inputs}
    require(
        PROTECTED_BASELINE_ROLES | REFINEMENT_OVERLAY_ROLES == roles, "BASELINE_ROLE_SET_MISMATCH"
    )
    for item in inputs:
        relative = str(item.get("path", ""))
        declared_hash = str(item.get("sha256", ""))
        historical = tracked_bytes(root, relative, EXPECTED_SOURCE_COMMIT)
        require(
            normalized_text_sha256(historical) == declared_hash,
            "HISTORICAL_BASELINE_INPUT_MISMATCH",
            relative,
        )
        safe_repo_path(root, relative)
        current_value = tracked_bytes(root, relative)
        current_hash = normalized_text_sha256(current_value)
        role = str(item.get("role", ""))
        if role in PROTECTED_BASELINE_ROLES:
            require(current_hash == declared_hash, "PROTECTED_BASELINE_INPUT_CHANGED", relative)
            protected.append({"path": relative, "sha256": current_hash})
        else:
            current_text = current_value.decode("utf-8")
            require(EXPECTED_SEMANTICS_ID in current_text, "REFINEMENT_OVERLAY_UNBOUND", relative)
            overlay.append(
                {
                    "baseline_sha256": declared_hash,
                    "current_sha256": current_hash,
                    "path": relative,
                    "status": "ADDITIVE_REFINEMENT_OVERLAY",
                }
            )
        bundle_records.append(f"{relative}\t{declared_hash}\n")
    bundle = sha256_bytes("".join(sorted(bundle_records)).encode("utf-8"))
    require(bundle == baseline.get("input_bundle_sha256"), "BASELINE_BUNDLE_DERIVATION_MISMATCH")
    return {
        "input_bundle_sha256": bundle,
        "path": path.relative_to(root).as_posix(),
        "protected_current_inputs": sorted(protected, key=lambda item: item["path"]),
        "refinement_overlay_inputs": sorted(overlay, key=lambda item: item["path"]),
        "sha256": sha256_tracked(root, relative_path),
        "verified_historical_input_count": len(inputs),
    }


def verify_report_records(
    report: dict[str, Any], root: Path, loaded_evidence: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    registry = load_tracked_json(root, "formal/reports/formal-id-registry.json")
    evidence_ids = set(loaded_evidence)
    config_ids = {item["id"] for item in registry["configs"]}
    proof_ids = {item["id"] for item in registry["proof_obligations"]}
    verify_status_records(report.get("toolchains", []), TOOLCHAIN_IDS, "TOOLCHAIN", evidence_ids)
    verify_status_records(report.get("model_checks", []), config_ids, "MODEL", evidence_ids)
    verify_status_records(report.get("theorem_checks", []), proof_ids, "THEOREM", evidence_ids)
    verify_status_records(report.get("mutant_checks", []), MUTANT_IDS, "MUTANT", evidence_ids)
    verify_status_records(
        report.get("refinement_checks", []), {"REFINEMENT-SUITE"}, "REFINEMENT", evidence_ids
    )

    coverage = report.get("coverage")
    require(isinstance(coverage, dict) and coverage.get("unresolved") == [], "COVERAGE_UNRESOLVED")
    requirements = coverage.get("requirements")
    require(isinstance(requirements, list), "COVERAGE_RECORDS_MISSING")
    expected_requirements = {f"FR-{index:03d}" for index in range(1, 47)}
    actual_requirements = {item.get("id") for item in requirements}
    require(actual_requirements == expected_requirements, "COVERAGE_ID_SET_MISMATCH")
    require(len(requirements) == len(actual_requirements), "COVERAGE_DUPLICATE_ID")
    for item in requirements:
        require(item.get("status") == "PASS", "COVERAGE_FAILED", str(item.get("id")))
        require(item.get("evidence_id") in evidence_ids, "COVERAGE_EVIDENCE_INVALID")

    reviews = report.get("review_attestations")
    require(isinstance(reviews, list) and len(reviews) >= 2, "REVIEWS_INSUFFICIENT")
    reviewer_ids: set[str] = set()
    review_records: list[dict[str, str]] = []
    for review in reviews:
        evidence_id = review.get("evidence_id")
        payload = loaded_evidence.get(str(evidence_id))
        require(payload is not None, "REVIEW_EVIDENCE_MISSING")
        require(
            review.get("independent") is True and payload.get("independent") is True,
            "REVIEW_NOT_INDEPENDENT",
        )
        require(
            review.get("status") == "PASS" and payload.get("status") == "PASS", "REVIEW_NOT_PASS"
        )
        require(set(review.get("scope", [])) == REVIEW_SCOPE, "REVIEW_SCOPE_INVALID")
        require(set(payload.get("scope", [])) == REVIEW_SCOPE, "REVIEW_PAYLOAD_SCOPE_INVALID")
        require(payload.get("reviewed_commit") == EXPECTED_SOURCE_COMMIT, "REVIEW_SOURCE_MISMATCH")
        require(
            payload.get("formal_semantics_id") == EXPECTED_SEMANTICS_ID, "REVIEW_SEMANTICS_MISMATCH"
        )
        reviewer = str(review.get("reviewer_id", ""))
        require(reviewer == payload.get("reviewer_id") and reviewer, "REVIEWER_ID_MISMATCH")
        require(reviewer not in reviewer_ids, "REVIEWER_ID_DUPLICATE")
        reviewer_ids.add(reviewer)
        review_records.append({"evidence_id": str(evidence_id), "reviewer_id": reviewer})

    toolchain = loaded_evidence["EVIDENCE-TOOLCHAINS"]
    require(
        toolchain.get("status") == "PASS" and toolchain.get("errors") == [],
        "TOOLCHAIN_EVIDENCE_FAILED",
    )
    toolchain_checks = toolchain.get("checks")
    require(isinstance(toolchain_checks, list), "TOOLCHAIN_CHECKS_MISSING")
    require(
        {item.get("id") for item in toolchain_checks} == TOOLCHAIN_IDS,
        "TOOLCHAIN_EVIDENCE_ID_SET_MISMATCH",
    )
    require(
        all(item.get("status") == "PASS" for item in toolchain_checks), "TOOLCHAIN_CHECK_FAILED"
    )
    locks = toolchain.get("locks")
    require(isinstance(locks, dict), "TOOLCHAIN_LOCKS_MISSING")
    for identifier, relative in LOCK_PATHS.items():
        require(
            sha256_tracked(root, relative) == locks.get(identifier),
            "TOOLCHAIN_LOCK_HASH_MISMATCH",
            identifier,
        )

    reproduction = loaded_evidence["EVIDENCE-REPRODUCIBILITY"]
    require(
        reproduction.get("status") == "PASS" and reproduction.get("errors") == [],
        "REPRODUCTION_FAILED",
    )
    require(
        reproduction.get("formal_semantics_id") == EXPECTED_SEMANTICS_ID,
        "REPRODUCTION_SEMANTICS_MISMATCH",
    )
    checks = reproduction.get("checks")
    require(isinstance(checks, list) and len(checks) == 12, "REPRODUCTION_CHECK_COUNT_MISMATCH")
    require(all(item.get("status") == "PASS" for item in checks), "REPRODUCTION_CHECK_FAILED")

    semantics = loaded_evidence["EVIDENCE-SEMANTICS"]
    require(semantics.get("status") == "published", "SEMANTICS_EVIDENCE_UNPUBLISHED")
    require(
        semantics.get("formal_semantics_id") == EXPECTED_SEMANTICS_ID, "SEMANTICS_EVIDENCE_MISMATCH"
    )
    return {
        "coverage_requirements": len(requirements),
        "model_checks": len(config_ids),
        "mutant_checks": len(MUTANT_IDS),
        "refinement_checks": 1,
        "reviewers": sorted(review_records, key=lambda item: item["reviewer_id"]),
        "theorem_checks": len(proof_ids),
        "toolchains": len(TOOLCHAIN_IDS),
    }


def verify_hybrid_refinement(root: Path) -> dict[str, Any]:
    values = {
        identifier: tracked_bytes(root, relative).decode("utf-8")
        for identifier, relative in HYBRID_DOCUMENTS.items()
    }
    require(
        "**Formal impact**: `REFINEMENT_ONLY`" in values["decision"],
        "HYBRID_FORMAL_IMPACT_INVALID",
    )
    require(EXPECTED_SEMANTICS_ID in values["decision"], "HYBRID_DECISION_UNBOUND")
    require(
        all(
            marker in values["architecture"]
            for marker in ("C++ native runtime", "Java node", "Python/PyTorch worker")
        ),
        "HYBRID_ARCHITECTURE_INCOMPLETE",
    )
    require(
        "Not a protocol-semantic amendment by itself" in values["source_provenance"],
        "HYBRID_PROVENANCE_OVERCLAIM",
    )
    require(
        "Native/JVM production code starts in 003" in values["runtime_map"],
        "HYBRID_RUNTIME_BOUNDARY_INVALID",
    )
    return {
        "classification": "REFINEMENT_ONLY",
        "documents": [
            {
                "id": identifier,
                "path": relative,
                "sha256": sha256_tracked(root, relative),
            }
            for identifier, relative in sorted(HYBRID_DOCUMENTS.items())
        ],
        "new_formal_action_ids": [],
        "new_failure_terminals": [],
        "new_protocol_visible_durability_outcomes": [],
        "status": "PASS",
    }


def run_formal_report_verifier(root: Path, report_path: Path) -> dict[str, Any]:
    archive = git_bytes(root, "archive", "--format=tar", "HEAD")
    with tempfile.TemporaryDirectory(prefix="delta-formal-prerequisite-") as directory:
        snapshot = Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            bundle.extractall(snapshot, filter="data")
        snapshot_report = snapshot / "formal" / "reports" / "formal-verification-report.json"
        snapshot_report.write_bytes(report_path.read_bytes())
        command = [
            sys.executable,
            str(snapshot / "formal" / "scripts" / "verify_formal_report.py"),
            str(snapshot_report),
            "--require-go",
        ]
        completed = subprocess.run(
            command,
            cwd=snapshot,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    require(completed.returncode == 0, "FORMAL_REPORT_VERIFIER_FAILED", completed.stdout.strip())
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    require(bool(lines), "FORMAL_REPORT_VERIFIER_EMPTY")
    try:
        result = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        reject("FORMAL_REPORT_VERIFIER_INVALID_JSON", str(exc))
    require(
        result.get("status") == "PASS" and result.get("decision") == "GO",
        "FORMAL_REPORT_VERIFIER_REJECTED",
    )
    require(
        result.get("formal_semantics_id") == EXPECTED_SEMANTICS_ID,
        "FORMAL_REPORT_VERIFIER_SEMANTICS_MISMATCH",
    )
    return result


def verify(root: Path, report_path: Path) -> dict[str, Any]:
    report = load_json_strict(report_path)
    require(report.get("decision") == "GO", "REPORT_NOT_GO")
    require(report.get("decision_reasons") == [], "REPORT_HAS_DECISION_REASONS")
    require(report.get("formal_semantics_id") == EXPECTED_SEMANTICS_ID, "SEMANTICS_ID_MISMATCH")
    require(report.get("formal_semantics_version") == "1.0.0", "SEMANTICS_VERSION_MISMATCH")
    require(report_path.read_bytes() == canonical_json_bytes(report), "REPORT_NOT_CANONICAL")

    loaded_evidence = verify_evidence_graph(report, root)
    semantic_result = verify_source_and_semantics(report, root)
    baseline_result = verify_baseline_inputs(report, root)
    record_result = verify_report_records(report, root, loaded_evidence)
    formal_impact_result = verify_hybrid_refinement(root)
    merge_result = verify_merged_predecessor(root, report_path, EXPECTED_SOURCE_COMMIT)
    formal_verifier = run_formal_report_verifier(root, report_path)

    nodes = report["evidence_graph"]["nodes"]
    verifier_path = Path(__file__).resolve()
    return {
        "baseline_inputs": baseline_result,
        "errors": [],
        "evidence_graph": {
            "node_count": len(nodes),
            "nodes": sorted(
                [
                    {"id": node["id"], "path": node["path"], "sha256": node["sha256"]}
                    for node in nodes
                ],
                key=lambda item: item["id"],
            ),
        },
        "formal_impact": formal_impact_result,
        "formal_semantics": semantic_result,
        "formal_semantics_id": EXPECTED_SEMANTICS_ID,
        "merged_predecessor": merge_result,
        "report": {
            "decision": "GO",
            "decision_reasons": [],
            "path": report_path.relative_to(root).as_posix(),
            "sha256": sha256_bytes(report_path.read_bytes()),
            "source_commit": EXPECTED_SOURCE_COMMIT,
        },
        "schema_version": "1.0.0",
        "status": "PASS",
        "task_ids": ["HR001-001", "T000"],
        "verified_counts": record_result,
        "verifier": {
            "formal_report_verifier_sha256": formal_verifier["report_sha256"],
            "offline": True,
            "path": verifier_path.relative_to(root).as_posix(),
            "sha256": sha256_file(verifier_path),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = args.report.resolve()
    try:
        result = verify(ROOT, report_path)
    except (OSError, PrerequisiteError, subprocess.SubprocessError) as exc:
        if isinstance(exc, PrerequisiteError):
            code = exc.code
            detail = exc.detail
        else:
            code = type(exc).__name__.upper()
            detail = str(exc)
        failure = {
            "error_code": code,
            "errors": [detail] if detail else [],
            "formal_semantics_id": EXPECTED_SEMANTICS_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2

    encoded = canonical_json_bytes(result)
    if not args.check_only:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded)
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
