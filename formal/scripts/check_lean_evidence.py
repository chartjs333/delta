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


OBLIGATIONS: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    "PO-Q1": ("DeltaReduce/Quorum.lean", (("intersection", "quorumIntersection"),)),
    "PO-Q2": (
        "DeltaReduce/Quorum.lean",
        (("conflicting-qc-impossibility", "conflictingQCImpossible"),),
    ),
    "PO-A1": ("DeltaReduce/FixedPoint.lean", (("product-bound", "signedProductBound"),)),
    "PO-A2": (
        "DeltaReduce/FixedPoint.lean",
        (("flat-accumulator-bound", "flatAccumulatorBound"),),
    ),
    "PO-A3": (
        "DeltaReduce/FixedPoint.lean",
        (
            ("numerator-accumulator-bound", "commonDenominatorNumeratorSafe"),
            ("positive-input-denominator", "reducedRationalDenominatorPositive"),
            ("canonical-reduced-input", "reducedRationalIsCoprime"),
            ("positive-common-denominator", "commonDenominatorPositive"),
            ("input-denominator-divides-common", "eachDenominatorDividesCommon"),
            ("round-below-half", "canonicalRoundBelowHalf"),
            ("round-at-or-above-half", "canonicalRoundAtOrAboveHalf"),
            ("round-half-tie-toward-positive", "canonicalRoundTieTowardPositive"),
            ("rounding-deterministic", "canonicalRoundDeterministic"),
        ),
    ),
    "PO-H1": ("DeltaReduce/Hierarchy.lean", (("exact-partition", "exactDomainShardPartition"),)),
    "PO-H2": ("DeltaReduce/Hierarchy.lean", (("hierarchy-equals-flat", "hierarchicalEqualsFlat"),)),
    "PO-C1": ("DeltaReduce/Coverage.lean", (("canonical-root-unique", "canonicalRootUnique"),)),
    "PO-AP1": ("DeltaReduce/Apply.lean", (("honest-vote-unique", "applyVoteUniqueness"),)),
    "PO-AP2": (
        "DeltaReduce/Apply.lean",
        (
            ("apply-qc-unique", "applyQCUniqueness"),
            ("current-unique-from-qc-intersection", "currentStateUniqueFromQCIntersection"),
            ("current-cas-accepted", "advanceCurrentAccepted"),
            ("current-replay-idempotent", "advanceCurrentReplayIdempotent"),
        ),
    ),
    "PO-D1": ("DeltaReduce/Apply.lean", (("domain-mixture-preserved", "domainMixturePreserved"),)),
    "PO-R1": ("DeltaReduce/Apply.lean", (("abort-preserves-current", "abortPreservesCurrent"),)),
    "PO-R2": (
        "DeltaReduce/Apply.lean",
        (
            ("durable-vote-journal-restored", "recoveryRestoresDurableVoteJournal"),
            ("certificates-restored", "recoveryRestoresCertificates"),
            ("current-checkpoint-restored", "recoveryRestoresCurrentCheckpoint"),
            ("full-observational-equivalence", "fullRecoveryObservationalEquivalence"),
            ("restart-recovery-idempotent", "restartRecoveryIdempotent"),
        ),
    ),
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
    conjunct_records: list[dict[str, object]] = []
    for proof_id, (relative, conjuncts) in OBLIGATIONS.items():
        source = PROOFS / relative
        text = without_comments(source.read_text(encoding="utf-8")) if source.is_file() else ""
        obligation_conjuncts: list[dict[str, object]] = []
        for conjunct_id, theorem in conjuncts:
            found = bool(re.search(rf"\btheorem\s+{re.escape(theorem)}\b", text))
            if not found:
                errors.append(
                    f"{proof_id} conjunct {conjunct_id} theorem {theorem} is missing"
                )
            record: dict[str, object] = {
                "id": f"{proof_id}:{conjunct_id}",
                "proof_obligation_id": proof_id,
                "conjunct": conjunct_id,
                "source": f"formal/proofs/{relative}",
                "source_sha256": sha256_file(source) if source.is_file() else None,
                "theorem": f"DeltaReduce.{theorem}",
                "status": "PASS" if found else "FAIL",
            }
            obligation_conjuncts.append(record)
            conjunct_records.append(record)
        theorem_records.append(
            {
                "id": proof_id,
                "source": f"formal/proofs/{relative}",
                "source_sha256": sha256_file(source) if source.is_file() else None,
                "theorem": obligation_conjuncts[0]["theorem"],
                "normative_conjuncts": obligation_conjuncts,
                "status": (
                    "PASS"
                    if all(item["status"] == "PASS" for item in obligation_conjuncts)
                    else "FAIL"
                ),
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
    for conjunct_record in conjunct_records:
        theorem = str(conjunct_record["theorem"])
        if theorem not in axiom_dependencies:
            errors.append(f"axiom dependency result missing for {theorem}")
            conjunct_record["status"] = "FAIL"
        conjunct_record["kernel_axioms"] = axiom_dependencies.get(theorem, [])
    for theorem_record in theorem_records:
        conjuncts = theorem_record["normative_conjuncts"]
        assert isinstance(conjuncts, list)
        theorem_record["status"] = (
            "PASS" if all(item["status"] == "PASS" for item in conjuncts) else "FAIL"
        )
        theorem_record["kernel_axioms"] = sorted(
            {
                axiom
                for item in conjuncts
                for axiom in item.get("kernel_axioms", [])
            }
        )
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
        "normative_conjuncts": conjunct_records,
        "conjunct_completeness": {
            "expected": len(conjunct_records),
            "verified": sum(item["status"] == "PASS" for item in conjunct_records),
            "status": (
                "PASS"
                if conjunct_records
                and all(item["status"] == "PASS" for item in conjunct_records)
                else "FAIL"
            ),
        },
        "errors": errors,
    }
    write_canonical_json(ROOT / "formal" / "reports" / "lean-proof-report.json", report)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
