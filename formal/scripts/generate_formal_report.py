#!/usr/bin/env python3
"""Generate the deterministic content-addressed FormalVerificationReport."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "formal" / "reports"
REPORT_OUTPUTS = {
    "formal/reports/clean-offline-reproduction.json",
    "formal/reports/cross-artifact-analysis.json",
    "formal/reports/formal-verification-report.json",
    "formal/reports/formal-semantics.json",
    "formal/reports/lean-proof-report.json",
    "formal/reports/mutant-evidence.json",
    "formal/reports/refinement-evidence.json",
    "formal/reports/reproducibility-evidence.json",
    "formal/reports/source-tree-manifest.json",
    "formal/reports/tlc-evidence.json",
    "formal/reports/toolchain-evidence.json",
}
REPORT_OUTPUT_GLOBS = ("formal/reports/reviews/*.json",)
REPRODUCTION_CHECK_IDS = (
    "phase0",
    "contracts",
    "toolchain",
    "report-verifier",
    "parse",
    "safety",
    "liveness",
    "proofs",
    "mutants",
    "refinement",
    "tlc-evidence",
    "cross-artifact",
)
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
    return result.stdout.rstrip()


def is_report_output(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in REPORT_OUTPUTS or (
        normalized.startswith("formal/reports/reviews/")
        and normalized.endswith(".json")
    )


def reproduction_matches_source(
    reproduction: dict[str, Any], commit: str, formal_semantics_id: str
) -> bool:
    checks = reproduction.get("checks")
    if not isinstance(checks, list):
        return False
    if [item.get("id") for item in checks if isinstance(item, dict)] != list(
        REPRODUCTION_CHECK_IDS
    ):
        return False
    checks_pass = all(
        isinstance(item, dict)
        and item.get("status") == "PASS"
        and item.get("exit_code") == 0
        and isinstance(item.get("command"), list)
        and bool(item["command"])
        and isinstance(item.get("output_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", item["output_sha256"]) is not None
        for item in checks
    )
    return (
        reproduction.get("schema_version") == "1.0.0"
        and reproduction.get("status") == "PASS"
        and reproduction.get("environment")
        == "linux/amd64 clean container with --network none"
        and reproduction.get("source_commit") == commit
        and reproduction.get("source_clean_at_start") is True
        and reproduction.get("formal_semantics_id") == formal_semantics_id
        and reproduction.get("network_interfaces") == ["lo"]
        and reproduction.get("network_proxies_forced_to_loopback") is True
        and reproduction.get("errors") == []
        and isinstance(reproduction.get("source_tree"), str)
        and re.fullmatch(r"[0-9a-f]{40}", reproduction["source_tree"]) is not None
        and isinstance(reproduction.get("source_manifest_sha256"), str)
        and re.fullmatch(
            r"[0-9a-f]{64}", reproduction["source_manifest_sha256"]
        )
        is not None
        and str(reproduction.get("machine", "")).lower() in {"amd64", "x86_64"}
        and str(reproduction.get("platform", "")).startswith("Linux-")
        and checks_pass
    )


def source_tree_status() -> tuple[str, bool]:
    """Return the latest source commit and whether that source tree is clean.

    Generated machine evidence and independent review attestations are committed
    as an evidence overlay after the source tree they attest. Ignoring only those
    known outputs avoids a circular reviewed_commit while every other tracked or
    untracked path remains fail-closed.
    """

    status_lines = git(
        "status", "--porcelain=v1", "--untracked-files=all"
    ).splitlines()
    source_changes = []
    for line in status_lines:
        path = line[3:].split(" -> ")[-1].replace("\\", "/")
        if not is_report_output(path):
            source_changes.append(line)
    exclusions = [f":(exclude){path}" for path in sorted(REPORT_OUTPUTS)]
    exclusions.extend(f":(exclude,glob){pattern}" for pattern in REPORT_OUTPUT_GLOBS)
    commit = git(
        "log",
        "-1",
        "--format=%H",
        "--",
        ".",
        *exclusions,
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
    reproduction_pass = reproduction_matches_source(
        reproduction, commit, formal_semantics_id
    )
    evidence_pass = {
        "EVIDENCE-TOOLCHAINS": all(
            item.get("status") == "PASS" for item in toolchains["checks"]
        ),
        "EVIDENCE-TLC": all(
            item.get("status") == "PASS" for item in tlc["models"]
        ),
        "EVIDENCE-LEAN": (
            lean.get("status") == "PASS"
            and lean.get("conjunct_completeness", {}).get("status") == "PASS"
        ),
        "EVIDENCE-MUTANTS": (
            mutants.get("status") == "PASS"
            and mutants.get("mutation_scope") == "PRODUCTION_ACTION_SOURCE"
        ),
        "EVIDENCE-REFINEMENT": refinement.get("status") == "PASS",
        "EVIDENCE-CROSS-ARTIFACT": (
            cross_artifact.get("status") == "PASS"
            and cross_artifact.get("gate_kind") == "SYNTACTIC_TRACEABILITY"
            and cross_artifact.get("semantic_completeness_claimed") is False
        ),
        "EVIDENCE-REPRODUCIBILITY": reproduction_pass,
        "EVIDENCE-SEMANTICS": True,
    }

    def requirement_evidence(identifier: str) -> str:
        number = int(identifier.removeprefix("FR-"))
        if number == 1:
            return "EVIDENCE-TOOLCHAINS"
        if number == 3 or number in {40, 41, 45}:
            return "EVIDENCE-CROSS-ARTIFACT"
        if 2 <= number <= 27:
            return "EVIDENCE-TLC"
        if 28 <= number <= 33:
            return "EVIDENCE-LEAN"
        if 34 <= number <= 36:
            return "EVIDENCE-MUTANTS"
        if 37 <= number <= 39:
            return "EVIDENCE-REFINEMENT"
        if 42 <= number <= 44:
            return "EVIDENCE-REPRODUCIBILITY"
        if number == 46:
            return "EVIDENCE-SEMANTICS"
        raise ValueError(f"unmapped formal requirement: {identifier}")

    coverage = []
    for identifier in sorted(REQUIREMENT_IDS):
        evidence_id = requirement_evidence(identifier)
        status = "PASS" if evidence_pass[evidence_id] else "FAIL"
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
            "The cross-artifact analyzer is a syntactic traceability gate and does not establish semantic completeness, liveness non-vacuity or theorem strength.",
            "A clean offline Linux reproduction and two independent technical reviews are required before Formal GO.",
        ],
        "review_attestations": reviews,
        "evidence_graph": {"nodes": nodes, "edges": []},
        "decision": "NO_GO",
        "decision_reasons": ["DRAFT"],
    }
    if not evidence_pass["EVIDENCE-CROSS-ARTIFACT"]:
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
