#!/usr/bin/env python3
"""Spec Kit style cross-artifact and final Constitution consistency audit."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "formal" / "reports"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import (  # noqa: E402
    REQUIREMENT_IDS,
    validate_contract_registry,
    load_json_strict,
    write_canonical_json,
)


def ids(pattern: str, path: Path) -> set[str]:
    return set(re.findall(pattern, path.read_text(encoding="utf-8")))


def main() -> int:
    errors: list[str] = []
    validate_contract_registry(ROOT)
    registry = load_json_strict(REPORTS / "formal-id-registry.json")
    manifest = load_json_strict(
        ROOT / "formal" / "tla" / "cfg" / "config-manifest.json"
    )

    spec_requirements = ids(
        r"\bFR-[0-9]{3}\b", ROOT / "specs" / "000-formal-tla-spec" / "spec.md"
    )
    if spec_requirements != REQUIREMENT_IDS:
        errors.append("spec requirement set differs from FR-001..FR-046")
    matrix_requirements = ids(
        r"\bFR-[0-9]{3}\b", REPORTS / "coverage-matrix.md"
    )
    if matrix_requirements != REQUIREMENT_IDS:
        errors.append("coverage matrix does not mention every formal requirement")

    task_ids = ids(
        r"\bT[0-9]{3}\b", ROOT / "specs" / "000-formal-tla-spec" / "tasks.md"
    )
    expected_tasks = {f"T{number:03d}" for number in range(67)}
    if task_ids != expected_tasks:
        errors.append("task set differs from T000..T066")

    registry_configs = {item["id"] for item in registry["configs"]}
    manifest_configs = {item["id"] for item in manifest["configs"]}
    if registry_configs != manifest_configs:
        errors.append("registry/config manifest ID mismatch")

    refinement = (
        ROOT / "formal" / "tla" / "DeltaReduceRefinement.tla"
    ).read_text(encoding="utf-8")
    registry_actions = {item["id"] for item in registry["actions"]}
    refinement_actions = set(re.findall(r'"(ACT-[A-Z0-9-]+)"', refinement))
    if registry_actions != refinement_actions:
        errors.append(
            "refinement action set mismatch: "
            f"missing={sorted(registry_actions - refinement_actions)} "
            f"extra={sorted(refinement_actions - registry_actions)}"
        )

    proof_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "formal" / "proofs" / "DeltaReduce").glob("*.lean"))
    )
    proof_names = {
        item["name"] for item in registry["proof_obligations"]
    }
    if len(proof_names) != 13:
        errors.append("proof registry does not contain thirteen obligations")
    lean_report = REPORTS / "lean-proof-report.json"
    if lean_report.is_file():
        proven = {item["id"] for item in load_json_strict(lean_report)["theorems"]}
        expected = {item["id"] for item in registry["proof_obligations"]}
        if proven != expected:
            errors.append("Lean evidence does not cover every proof obligation")
    elif "theorem " not in proof_sources:
        errors.append("Lean theorem sources are absent")

    legal = sorted((ROOT / "formal" / "fixtures" / "traces" / "legal").glob("*.json"))
    illegal = sorted((ROOT / "formal" / "fixtures" / "traces" / "illegal").glob("*.json"))
    if len(legal) < 5 or len(illegal) < 14:
        errors.append("refinement fixture cardinality is below the mandatory boundary")

    constitution = (
        ROOT / ".specify" / "memory" / "constitution.md"
    ).read_text(encoding="utf-8").lower()
    principle_terms = {
        "formal-first": ("formal", "tla+", "theorem"),
        "replicated-state": ("3f+1", "2f+1", "quorum"),
        "fixed-work": ("workticket", "immutable", "domain"),
        "integer-arithmetic": ("fixed-point", "overflow", "integer"),
        "certificate-lineage": ("certificate", "parent", "applyqc"),
        "failure-semantics": ("partition", "crash", "abort"),
        "atomic-apply": ("current", "applyqc", "atomic"),
        "plane-separation": ("distribution", "worker-local", "certified"),
    }
    constitution_results: list[dict[str, object]] = []
    for principle, terms in principle_terms.items():
        missing = [term for term in terms if term not in constitution]
        if missing:
            errors.append(f"constitution principle {principle} lacks {missing}")
        constitution_results.append(
            {
                "principle": principle,
                "status": "PASS" if not missing else "FAIL",
                "terms": list(terms),
            }
        )

    result = {
        "schema_version": "1.0.0",
        "status": "PASS" if not errors else "FAIL",
        "requirements": len(spec_requirements),
        "tasks": len(task_ids),
        "actions": len(registry_actions),
        "configs": len(registry_configs),
        "proof_obligations": len(registry["proof_obligations"]),
        "legal_fixtures": len(legal),
        "illegal_fixtures": len(illegal),
        "constitution": constitution_results,
        "errors": errors,
    }
    write_canonical_json(REPORTS / "cross-artifact-analysis.json", result)
    lines = [
        "# Final Constitution Check",
        "",
        f"Machine consistency result: **{result['status']}**.",
        "",
        "| Principle | Result | Evidence boundary |",
        "| --- | --- | --- |",
    ]
    for item in constitution_results:
        lines.append(
            f"| {item['principle']} | {item['status']} | "
            f"{', '.join(item['terms'])} |"
        )
    lines.extend(
        [
            "",
            "This check establishes cross-artifact consistency only. The final "
            "Formal GO additionally requires the executed TLC, Lean, mutant, "
            "refinement, offline reproduction and two independent review records.",
            "",
        ]
    )
    (REPORTS / "final-constitution-check.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
