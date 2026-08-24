#!/usr/bin/env python3
"""Fail closed on missing PO theorems, proof holes and undeclared axioms."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROOFS = ROOT / "formal" / "proofs"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import sha256_file, write_canonical_json  # noqa: E402


THEOREMS = {
    "PO-Q1": ("DeltaReduce/Quorum.lean", "quorumIntersection"),
    "PO-Q2": ("DeltaReduce/Quorum.lean", "conflictingQCImpossible"),
    "PO-A1": ("DeltaReduce/FixedPoint.lean", "signedProductBound"),
    "PO-A2": ("DeltaReduce/FixedPoint.lean", "flatAccumulatorBound"),
    "PO-A3": ("DeltaReduce/FixedPoint.lean", "commonDenominatorNumeratorSafe"),
    "PO-H1": ("DeltaReduce/Hierarchy.lean", "exactDomainShardPartition"),
    "PO-H2": ("DeltaReduce/Hierarchy.lean", "hierarchicalEqualsFlat"),
    "PO-C1": ("DeltaReduce/Coverage.lean", "canonicalRootUnique"),
    "PO-AP1": ("DeltaReduce/Apply.lean", "applyVoteUniqueness"),
    "PO-AP2": ("DeltaReduce/Apply.lean", "advanceCurrentReplayIdempotent"),
    "PO-D1": ("DeltaReduce/Apply.lean", "domainMixturePreserved"),
    "PO-R1": ("DeltaReduce/Apply.lean", "abortPreservesCurrent"),
    "PO-R2": ("DeltaReduce/Apply.lean", "replayRecordIdempotent"),
}
ALLOWED_AXIOMS = {"propext", "Quot.sound", "Classical.choice"}


def without_comments(source: str) -> str:
    source = re.sub(r"/-.*?-/", "", source, flags=re.DOTALL)
    return re.sub(r"--.*$", "", source, flags=re.MULTILINE)


def main() -> int:
    errors: list[str] = []
    sources = [PROOFS / "DeltaReduce.lean", *sorted((PROOFS / "DeltaReduce").glob("*.lean"))]
    if not sources:
        errors.append("no Lean sources")

    for source in sources:
        stripped = without_comments(source.read_text(encoding="utf-8"))
        for token in ("sorry", "admit"):
            if re.search(rf"\b{token}\b", stripped):
                errors.append(f"{source.relative_to(ROOT)} contains {token}")
        if re.search(r"^\s*axiom\s+", stripped, flags=re.MULTILINE):
            errors.append(f"{source.relative_to(ROOT)} declares an axiom")

    theorem_records: list[dict[str, object]] = []
    for proof_id, (relative, theorem) in THEOREMS.items():
        source = PROOFS / relative
        text = without_comments(source.read_text(encoding="utf-8")) if source.is_file() else ""
        found = bool(re.search(rf"\btheorem\s+{re.escape(theorem)}\b", text))
        if not found:
            errors.append(f"{proof_id} theorem {theorem} is missing")
        theorem_records.append(
            {
                "id": proof_id,
                "source": f"formal/proofs/{relative}",
                "source_sha256": sha256_file(source) if source.is_file() else None,
                "theorem": f"DeltaReduce.{theorem}",
                "status": "PASS" if found else "FAIL",
            }
        )

    lake = os.environ.get("LAKE", "lake")
    if shutil.which(lake) is None and not Path(lake).is_file():
        errors.append(f"Lake executable not found: {lake}")
        output = ""
    else:
        result = subprocess.run(
            [lake, "env", "lean", "DeltaReduce/AxiomAudit.lean"],
            cwd=PROOFS,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0:
            errors.append(f"axiom audit failed with exit code {result.returncode}")

    axiom_dependencies: dict[str, list[str]] = {}
    for theorem, dependency_list in re.findall(
        r"'([^']+)' depends on axioms: \[([^\]]*)\]", output
    ):
        axiom_dependencies[theorem] = sorted(
            dependency.strip()
            for dependency in dependency_list.split(",")
            if dependency.strip()
        )
    for theorem in re.findall(r"'([^']+)' does not depend on any axioms", output):
        axiom_dependencies[theorem] = []

    reported_axioms = sorted(
        {
            dependency
            for dependencies in axiom_dependencies.values()
            for dependency in dependencies
        }
    )
    unknown_axioms = sorted(set(reported_axioms) - ALLOWED_AXIOMS)
    if unknown_axioms:
        errors.append(f"undeclared axioms: {unknown_axioms}")
    if "sorryAx" in output or "declaration uses 'sorry'" in output:
        errors.append("kernel audit reports a proof placeholder")
    for theorem_record in theorem_records:
        theorem = str(theorem_record["theorem"])
        if theorem not in axiom_dependencies:
            errors.append(f"axiom dependency result missing for {theorem}")
            theorem_record["status"] = "FAIL"
        theorem_record["kernel_axioms"] = axiom_dependencies.get(theorem, [])
    if "#print axioms" not in (
        PROOFS / "DeltaReduce" / "AxiomAudit.lean"
    ).read_text(encoding="utf-8"):
        errors.append("axiom audit commands are missing")

    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if not errors else "FAIL",
        "lean_toolchain": (PROOFS / "lean-toolchain").read_text(encoding="utf-8").strip(),
        "lake_manifest_sha256": sha256_file(PROOFS / "lake-manifest.json"),
        "dependency_lock_sha256": sha256_file(PROOFS / "dependencies.lock.json"),
        "allowed_kernel_axioms": sorted(ALLOWED_AXIOMS),
        "reported_kernel_axioms": reported_axioms,
        "theorems": theorem_records,
        "errors": errors,
    }
    write_canonical_json(ROOT / "formal" / "reports" / "lean-proof-report.json", report)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
