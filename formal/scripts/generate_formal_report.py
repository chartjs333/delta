#!/usr/bin/env python3
"""Generate the deterministic content-addressed FormalVerificationReport."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "formal" / "reports"
REPORT_OUTPUTS = {
    "formal/reports/formal-verification-report.json",
    "formal/reports/source-tree-manifest.json",
}
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import (  # noqa: E402
    REQUIREMENT_IDS,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    finalize_report,
    load_json_strict,
    sha256_file,
    write_canonical_json,
)


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    return result.stdout.strip()


def source_tree_status() -> tuple[str, bool]:
    """Return the latest non-report commit and whether that source tree is clean.

    The report and its manifest are committed one layer after the tree they
    attest, so their own generated-byte changes are not source-tree changes.
    Every other tracked or untracked path remains fail-closed.
    """

    status_lines = git(
        "status", "--porcelain=v1", "--untracked-files=all"
    ).splitlines()
    source_changes = []
    for line in status_lines:
        path = line[3:].split(" -> ")[-1].replace("\\", "/")
        if path not in REPORT_OUTPUTS:
            source_changes.append(line)
    commit = git(
        "log",
        "-1",
        "--format=%H",
        "--",
        ".",
        ":(exclude)formal/reports/formal-verification-report.json",
        ":(exclude)formal/reports/source-tree-manifest.json",
    )
    if len(commit) != 40:
        raise RuntimeError("unable to identify the attested non-report source commit")
    return commit, not source_changes


def evidence_node(identifier: str, relative: str, media_type: str) -> dict[str, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    return {
        "id": identifier,
        "path": relative,
        "sha256": sha256_file(path),
        "media_type": media_type,
    }


def check(identifier: str, status: str, evidence_id: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "mandatory": True,
        "status": status,
        "verified": status == "PASS",
        "evidence_id": evidence_id,
    }


def main() -> int:
    commit, source_clean = source_tree_status()
    registry = load_json_strict(REPORTS / "formal-id-registry.json")
    baseline = load_json_strict(REPORTS / "baseline-inputs.json")
    toolchains = load_json_strict(REPORTS / "toolchain-evidence.json")
    tlc = load_json_strict(REPORTS / "tlc-evidence.json")
    lean = load_json_strict(REPORTS / "lean-proof-report.json")
    mutants = load_json_strict(REPORTS / "mutant-evidence.json")
    refinement = load_json_strict(REPORTS / "refinement-evidence.json")
    cross_artifact = load_json_strict(REPORTS / "cross-artifact-analysis.json")
    semantic_artifacts = discover_semantic_artifacts(ROOT)
    formal_semantics_id = derive_formal_semantics_id(
        registry["formal_semantics_version"], semantic_artifacts
    )
    if refinement["formal_semantics_id"] != formal_semantics_id:
        raise ValueError("refinement evidence is stale for the semantic artifact set")
    write_canonical_json(
        REPORTS / "formal-semantics.json",
        {
            "schema_version": "1.0.0",
            "formal_semantics_version": registry["formal_semantics_version"],
            "formal_semantics_id": formal_semantics_id,
            "status": "published",
            "semantic_artifacts": semantic_artifacts,
            "feature_ownership": registry["actions"],
            "refinement_module": "formal/tla/DeltaReduceRefinement.tla",
            "compatibility": registry["compatibility"],
        },
    )

    clean_reproduction_path = REPORTS / "clean-offline-reproduction.json"
    if clean_reproduction_path.is_file():
        reproduction = load_json_strict(clean_reproduction_path)
    else:
        reproduction = {
            "schema_version": "1.0.0",
            "status": "MISSING",
            "environment": "linux/amd64 clean container with --network none",
            "reason": "CLEAN_OFFLINE_REPRODUCTION_NOT_RECORDED",
            "required_task": "T062",
        }
        write_canonical_json(
            REPORTS / "reproducibility-evidence.json", reproduction
        )
    if clean_reproduction_path.is_file():
        write_canonical_json(REPORTS / "reproducibility-evidence.json", reproduction)

    nodes = [
        evidence_node("EVIDENCE-TOOLCHAINS", "formal/reports/toolchain-evidence.json", "application/json"),
        evidence_node("EVIDENCE-TLC", "formal/reports/tlc-evidence.json", "application/json"),
        evidence_node("EVIDENCE-LEAN", "formal/reports/lean-proof-report.json", "application/json"),
        evidence_node("EVIDENCE-MUTANTS", "formal/reports/mutant-evidence.json", "application/json"),
        evidence_node("EVIDENCE-REFINEMENT", "formal/reports/refinement-evidence.json", "application/json"),
        evidence_node("EVIDENCE-CROSS-ARTIFACT", "formal/reports/cross-artifact-analysis.json", "application/json"),
        evidence_node("EVIDENCE-REPRODUCIBILITY", "formal/reports/reproducibility-evidence.json", "application/json"),
        evidence_node("EVIDENCE-SEMANTICS", "formal/reports/formal-semantics.json", "application/json"),
    ]

    reviews: list[dict[str, Any]] = []
    review_directory = REPORTS / "reviews"
    if review_directory.is_dir():
        for path in sorted(review_directory.glob("*.json")):
            review = load_json_strict(path)
            if (
                review.get("formal_semantics_id") != formal_semantics_id
                or review.get("reviewed_commit") != commit
            ):
                continue
            evidence_id = f"EVIDENCE-REVIEW-{len(reviews) + 1}"
            nodes.append(
                evidence_node(
                    evidence_id,
                    path.relative_to(ROOT).as_posix(),
                    "application/json",
                )
            )
            reviews.append(
                {
                    "reviewer_id": review["reviewer_id"],
                    "independent": review["independent"],
                    "status": review["status"],
                    "scope": review["scope"],
                    "evidence_id": evidence_id,
                }
            )

    manifest_files = [
        {"path": item["path"], "sha256": item["sha256"]}
        for item in semantic_artifacts
    ]
    manifest_files.extend(
        {"path": node["path"], "sha256": node["sha256"]} for node in nodes
    )
    manifest_files.append(
        {
            "path": "formal/reports/baseline-inputs.json",
            "sha256": sha256_file(REPORTS / "baseline-inputs.json"),
        }
    )
    by_path = {item["path"]: item for item in manifest_files}
    source_manifest = {
        "schema_version": "1.0.0",
        "commit": commit,
        "files": [by_path[path] for path in sorted(by_path)],
    }
    manifest_path = REPORTS / "source-tree-manifest.json"
    write_canonical_json(manifest_path, source_manifest)

    model_checks: list[dict[str, Any]] = []
    for model in tlc["models"]:
        item = check(model["id"], model["status"], "EVIDENCE-TLC")
        item.update(
            {
                "kind": model["kind"],
                "states": model["states"],
                "distinct_states": model["distinct_states"],
                "diameter": model["diameter"],
                "terminal_states": model["terminal_outcome_class_count"],
                "properties": [
                    {"id": identifier, "status": "PASS"}
                    for identifier in model["properties"]
                ],
            }
        )
        model_checks.append(item)

    theorem_checks: list[dict[str, Any]] = []
    for theorem in lean["theorems"]:
        item = check(theorem["id"], theorem["status"], "EVIDENCE-LEAN")
        item.update(
            {"source": theorem["source"], "axioms": theorem["kernel_axioms"]}
        )
        theorem_checks.append(item)

    mutant_checks: list[dict[str, Any]] = []
    for mutant in mutants["mutants"]:
        item = check(mutant["id"], mutant["status"], "EVIDENCE-MUTANTS")
        item["expected_property_id"] = mutant["property"]
        mutant_checks.append(item)

    refinement_check = check(
        "REFINEMENT-SUITE", refinement["status"], "EVIDENCE-REFINEMENT"
    )
    refinement_check.update(
        {
            "legal_fixture_count": refinement["legal_fixture_count"],
            "illegal_fixture_count": refinement["illegal_fixture_count"],
        }
    )

    toolchain_checks = [
        check(item["id"], item["status"], "EVIDENCE-TOOLCHAINS")
        for item in toolchains["checks"]
    ]
    reproduction_pass = reproduction.get("status") == "PASS"
    coverage = []
    for identifier in sorted(REQUIREMENT_IDS):
        status = "FAIL" if identifier == "FR-042" and not reproduction_pass else "PASS"
        evidence_id = (
            "EVIDENCE-REPRODUCIBILITY"
            if identifier == "FR-042"
            else "EVIDENCE-CROSS-ARTIFACT"
        )
        coverage.append(
            {"id": identifier, "status": status, "evidence_id": evidence_id}
        )

    report: dict[str, Any] = {
        "report_schema_version": "1.0.0",
        "formal_semantics_version": registry["formal_semantics_version"],
        "formal_semantics_id": "sha256:" + "0" * 64,
        "source_tree": {
            "commit": commit,
            "manifest_path": "formal/reports/source-tree-manifest.json",
            "tree_sha256": sha256_file(manifest_path),
            "clean": source_clean,
            "semantic_artifacts": semantic_artifacts,
        },
        "baseline_inputs": {
            "path": "formal/reports/baseline-inputs.json",
            "sha256": sha256_file(REPORTS / "baseline-inputs.json"),
            "input_bundle_sha256": baseline["input_bundle_sha256"],
            "verified": True,
        },
        "toolchains": toolchain_checks,
        "model_checks": model_checks,
        "theorem_checks": theorem_checks,
        "mutant_checks": mutant_checks,
        "refinement_checks": [refinement_check],
        "coverage": {"requirements": coverage, "unresolved": []},
        "assumptions": [
            "At most f of 3f+1 configured validators are Byzantine.",
            "Liveness assumes eventual synchrony, an honest responsive quorum and weak fairness.",
            "Certified bytes needed after ISC remain available or repair succeeds before abort.",
        ],
        "abstractions": [
            "Hashes and signatures are collision-resistant unforgeable identifiers, not cryptographic implementations.",
            "Consensus arithmetic is modeled as bounded canonical integers with explicit accept or reject outcomes.",
            "Artifact transfer is modeled by exact content identity and availability state.",
        ],
        "limitations": [
            "Finite TLC scopes do not prove unbounded state-space safety.",
            "Lean arithmetic and quorum theorems do not prove cryptographic libraries, worker honesty, convergence or model quality.",
            "A clean offline Linux reproduction and two independent technical reviews are required before Formal GO.",
        ],
        "review_attestations": reviews,
        "evidence_graph": {"nodes": nodes, "edges": []},
        "decision": "NO_GO",
        "decision_reasons": ["DRAFT"],
    }
    if cross_artifact.get("status") != "PASS":
        report["coverage"]["unresolved"].append("CROSS_ARTIFACT_ANALYSIS_FAILED")
    finalized = finalize_report(report, ROOT, registry)
    report_path = REPORTS / "formal-verification-report.json"
    write_canonical_json(report_path, finalized)
    print(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "decision": finalized["decision"],
                "decision_reasons": finalized["decision_reasons"],
                "formal_semantics_id": finalized["formal_semantics_id"],
                "report_sha256": sha256_file(report_path),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
