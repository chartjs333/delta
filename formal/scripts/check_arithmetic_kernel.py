#!/usr/bin/env python3
"""Check PO-A4 alone, including kernel-checked guard-removal counterexamples.

This scoped offline check needs only pinned Lean/Std. It does not replace the
mandatory Lake/mathlib build, PO-AB1, the formal gate or independent review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from check_lean_evidence import ALLOWED_AXIOMS, OBLIGATIONS, without_comments
from formal_artifacts import sha256_file, write_canonical_json

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "formal/proofs/DeltaReduce/ArithmeticKernel.lean"

MUTATIONS = (
    (
        "PRODUCT_GUARD_REMOVED",
        "if Fits lo hi acc ∧ Fits productLo productHi (coefficient * value) then",
        "if Fits lo hi acc then",
        "checkedAccumulate (-8) 7 (-8) 7 (-7) [(2, 7)] = some 7",
    ),
    (
        "PREFIX_GUARD_REMOVED",
        "if Fits lo hi acc ∧ Fits productLo productHi (coefficient * value) then",
        "if Fits productLo productHi (coefficient * value) then",
        "checkedAccumulate (-8) 7 (-8) 7 0 [(1, 7), (1, 7), (1, -7), (1, -7)] = some 0",
    ),
    (
        "CONVERSION_PRODUCT_GUARDS_REMOVED",
        "Fits lo hi p₁ ∧ Fits lo hi p₂ ∧ Fits lo hi d₁",
        "Fits lo hi d₁",
        "checkedConvert (-8) 7 (-8) 7 7 2 2 1 1 1 = some 7",
    ),
    (
        "OUTPUT_GUARD_REMOVED",
        "Fits outputLo outputHi result then some result else none",
        "True then some result else none",
        "checkedConvert (-128) 127 (-8) 7 8 1 1 1 1 1 = some 8",
    ),
    (
        "HALF_TIE_ROUNDED_DOWN",
        "if remainder < denominator - remainder then quotient else quotient + 1",
        "if remainder ≤ denominator - remainder then quotient else quotient + 1",
        "round 1 2 = 0 ∧ round (-1) 2 = -1",
    ),
)


def definitions(source: str) -> str:
    """Keep executable definitions for an independent, concrete witness theorem."""
    body = source.split("\nend DeltaReduce", 1)[0]
    chunks = re.split(r"(?m)(?=^(?:def|instance|theorem) )", body)
    return "".join(chunk for chunk in chunks if not chunk.startswith("theorem "))


def compile_lean(lean: Path, source: str, name: str, directory: Path) -> dict:
    path = directory / f"{name}.lean"
    path.write_text(source, encoding="utf-8", newline="\n")
    result = subprocess.run(
        [str(lean), str(path)],
        cwd=directory,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    output = result.stdout + result.stderr
    # Absolute temporary paths are diagnostic rather than semantic evidence.
    output = output.replace(str(directory).replace("\\", "/"), "<scratch>")
    output = output.replace(str(directory), "<scratch>")
    return {"exit_code": result.returncode, "source_sha256": sha256_file(path), "output": output}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--platform", choices=("windows", "linux"), required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    lean = args.lean.resolve(strict=True)
    lock = json.loads((ROOT / "formal/toolchain/lean.lock").read_text(encoding="utf-8"))
    locked = lock["lean_windows" if args.platform == "windows" else "lean"]
    archive_hash = sha256_file(args.archive)
    if archive_hash != locked["sha256"] or args.archive.stat().st_size != locked["bytes"]:
        raise ValueError("Lean archive differs from the pinned toolchain")
    executable_hash = sha256_file(lean)
    with zipfile.ZipFile(args.archive) as archive:
        suffix = "/bin/lean.exe" if args.platform == "windows" else "/bin/lean"
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
        if (
            len(matches) != 1
            or hashlib.sha256(archive.read(matches[0])).hexdigest() != executable_hash
        ):
            raise ValueError("Lean executable differs from the pinned archive")
    version = subprocess.run(
        [str(lean), "--version"], capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()
    if (
        locked["release"].removeprefix("v") not in version
        or locked["release_commit"][:12] not in version
    ):
        raise ValueError(f"Unexpected Lean version: {version}")
    source = SOURCE.read_text(encoding="utf-8")
    stripped = without_comments(source)
    if re.search(r"\b(?:sorry|admit|axiom)\b", stripped):
        raise ValueError("Proof placeholder or local axiom in source")
    names = [name for _, name in OBLIGATIONS["PO-A4"][1]]
    audit = source + "\n" + "\n".join(f"#print axioms DeltaReduce.{name}" for name in names)
    errors = []
    with tempfile.TemporaryDirectory(prefix="delta-arithmetic-kernel-") as temporary:
        directory = Path(temporary)
        checked = compile_lean(lean, audit, "KernelAudit", directory)
        if checked["exit_code"] != 0:
            errors.append("KERNEL_BUILD_FAILED")
        dependencies = {}
        for name, values in re.findall(
            r"'([^']+)' depends on axioms: \[([^\]]*)\]", checked["output"]
        ):
            dependencies[name] = sorted(x.strip() for x in values.split(",") if x.strip())
        for name in re.findall(r"'([^']+)' does not depend on any axioms", checked["output"]):
            dependencies[name] = []
        for name in names:
            axioms = dependencies.get(f"DeltaReduce.{name}")
            if axioms is None or not set(axioms) <= ALLOWED_AXIOMS:
                errors.append(f"INVALID_AXIOM_AUDIT:{name}")
        mutants = []
        for identifier, old, new, witness in MUTATIONS:
            if source.count(old) != 1:
                raise ValueError(f"Ambiguous mutation target: {identifier}")
            mutated = source.replace(old, new, 1)
            rejected = compile_lean(lean, mutated, identifier, directory)
            witness_source = definitions(mutated)
            witness_source += (
                f"\ntheorem concreteCounterexample : {witness} := by decide\n"
                "end DeltaReduce\n#print axioms DeltaReduce.concreteCounterexample\n"
            )
            counterexample = compile_lean(lean, witness_source, identifier + "_Witness", directory)
            passed = rejected["exit_code"] != 0 and counterexample["exit_code"] == 0
            if not passed:
                errors.append(f"MUTANT_NOT_DISCRIMINATED:{identifier}")
            mutants.append(
                {
                    "id": identifier,
                    "replacement": {"old": old, "new": new},
                    "counterexample_statement": witness,
                    "original_proofs_reject_mutant": rejected,
                    "concrete_counterexample": counterexample,
                    "status": "PASS" if passed else "FAIL",
                }
            )
    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if not errors else "FAIL",
        "scope": "PO-A4_STANDALONE_KERNEL_AND_GUARD_MUTANTS",
        "formal_go": False,
        "independent_review": False,
        "mandatory_project_build": "NOT_EXECUTED_BY_THIS_SCOPED_CHECK",
        "native_binding_obligation": "PO-AB1_OPEN",
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "toolchain": {
            "version": version,
            "archive_sha256": archive_hash,
            "executable_sha256": executable_hash,
            "lock_sha256": sha256_file(ROOT / "formal/toolchain/lean.lock"),
        },
        "kernel_check": checked,
        "axiom_dependencies": dependencies,
        "mutants": mutants,
        "errors": errors,
    }
    write_canonical_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "theorems": len(names),
                "mutants": len(mutants),
                "errors": errors,
            }
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
