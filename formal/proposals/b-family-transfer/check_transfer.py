"""Reproduce the bounded R2 representation checkpoint; never issue a GO.

Uses existing original byte-source loaders and fresh isolated Lean kernels.
Does not regenerate production models, schemas, witnesses or semantics metadata.
"""

# Existing repository checker imports are deliberately source-bound.
# ruff: noqa: E402
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "formal/build/b-family-transfer"
EVIDENCE = ROOT / "formal/proposals/evidence/b-family-transfer"
BASE = "e157e84c0e4091ec7654212085f8a5e2076a40b1"
DOD_SHA = "51b1a92b724f6021eb4a534e6f86c92905c8fecd6f55fb5173c7eaf253d8a2e6"
SEMANTICS = "sha256:b96d22536c196d778dc3643149d4180a44a14993ac6d50d89845967627d420ad"
sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import (
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    load_json_strict,
    sha256_file,
    write_canonical_json,
)
from generate_native_source_artifacts import generate


def require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def run() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    protected = [
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
        "formal/fixtures",
        "formal/reports",
        "delta-runtime-cpp",
        "delta-core-cpp",
        "delta-protocol",
        "specs/000-formal-tla-spec",
    ]
    diff = subprocess.run(
        ["git", "diff", "--exit-code", BASE, "--", *protected],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    require(diff.returncode == 0, "PROTECTED_SOURCE_CHANGE_STOP")
    dod = ROOT / "specs/000-formal-tla-spec/accepted-residual-20260928.md"
    require(sha256_file(dod) == DOD_SHA, "DOD_CHANGED_STOP")
    semantics = load_json_strict(ROOT / "formal/reports/formal-semantics.json")
    inventory = discover_semantic_artifacts(ROOT)
    require(inventory == semantics["semantic_artifacts"], "MANDATORY_INVENTORY_CHANGED_STOP")
    require(
        derive_formal_semantics_id(semantics["formal_semantics_version"], inventory) == SEMANTICS,
        "SEMANTICS_CHANGED_STOP",
    )
    original = generate()  # Calls the existing pinned canonical byte loaders, read-only.
    original_path = ROOT / "formal/proposals/native-source-artifact-vectors.json"
    require(original == load_json_strict(original_path), "ORIGINAL_SOURCE_REPRODUCTION")
    require([r["element_count"] for r in original["ordered_rows"]] == [4, 8, 8, 8, 8], "WIDTHS")
    require([r["element_start"] for r in original["ordered_rows"]] == [0, 4, 12, 20, 28], "OFFSETS")
    require(not original["cross_fixture_source_join"], "DO_NOT_INVENT_JOINED_CAPTURE")

    lake = os.environ.get("FAMILY_LAKE", "D:/formal-tools-20260920/lean/bin/lake.exe")
    env = {**os.environ, "LEAN_PATH": str(BUILD)}
    commands = []

    def check(name: str, args: list[str], dependencies: bool = False) -> str:
        command = [lake, *args]
        result = subprocess.run(
            command,
            cwd=ROOT / "formal/proofs",
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
            check=False,
        )
        output = result.stdout + result.stderr
        log = EVIDENCE / f"{name}.txt"
        log.write_text(output, encoding="utf-8", newline="\n")
        require(result.returncode == 0, f"LEAN:{name}")
        require(dependencies or "warning:" not in output, f"WARNING:{name}")
        require("sorryAx" not in output, f"SORRY:{name}")
        commands.append(
            {
                "command": command,
                "exit_code": result.returncode,
                "log": log.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(log),
            }
        )
        print(f"kernel checked: {name}", flush=True)
        return output

    check(
        "dependencies",
        [
            "build",
            "DeltaReduce.PublicApplyArithmetic",
            "DeltaReduce.NativeVectorArithmeticVectors",
            "DeltaReduce.NativeIscCertificate",
        ],
        dependencies=True,
    )
    sources = {
        "VectorShardRepresentation": ROOT / "formal/proposals/vector-shard-representation.lean",
        "SyncFamily": ROOT / "formal/proposals/b-feasibility/SyncFamily.lean",
        **{
            name: HERE / f"{name}.lean"
            for name in ("ShardFamily", "ManifestFamily", "NativeFamily", "StateFamily", "Checks")
        },
    }
    declarations = []
    for name, source in sources.items():
        target = BUILD / f"{name}.lean"
        shutil.copyfile(source, target)
        require(sha256_file(source) == sha256_file(target), "SOURCE_COPY")
        check(
            name,
            ["env", "lean", f"--root={BUILD}", "-o", str(BUILD / f"{name}.olean"), str(target)],
        )
        if source.parent == HERE:
            text = source.read_text(encoding="utf-8")
            require(not re.search(r"\b(?:sorry|admit|axiom|native_decide)\b", text), "PROOF_ESCAPE")
            namespace = re.search(r"^namespace (\S+)", text, re.M).group(1)
            names = re.findall(
                r"^(?:@\[[^\n]+\]\s*)?(?:structure|def|abbrev|theorem) (\w+)", text, re.M
            )
            declarations += [f"{namespace}.{name}" for name in names]
    audit = BUILD / "Audit.lean"
    audit.write_text(
        "import Checks\n" + "\n".join(f"#print axioms {name}" for name in declarations) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    output = check("axioms", ["env", "lean", str(audit)])
    audited = re.findall(
        r"'([^']+)' (?:does not depend on any axioms|depends on axioms: \[(.*?)\])", output, re.S
    )
    require({name for name, _ in audited} == set(declarations), "AUDIT_COVERAGE")
    for _, axioms in audited:
        require(
            set(axioms.replace("\n", "").replace(" ", "").split(","))
            <= {"", "propext", "Quot.sound", "Classical.choice"},
            "NONSTANDARD_AXIOM",
        )
    shutil.copyfile(audit, EVIDENCE / "Audit.lean")

    # Pin the complete local proof dependency closure, not only the new files.
    paths = set(sources.values()) | {Path(__file__).resolve(), dod, original_path}
    todo = list(sources.values())
    while todo:
        for module in re.findall(r"^import (\S+)", todo.pop().read_text(encoding="utf-8"), re.M):
            if module.startswith("DeltaReduce."):
                path = ROOT / "formal/proofs" / (module.replace(".", "/") + ".lean")
                if path not in paths:
                    paths.add(path)
                    todo.append(path)
    paths.update(ROOT / "formal/toolchain" / f"{name}.lock" for name in ("lean", "tla"))
    paths.update(ROOT / "formal/proofs" / name for name in ("lean-toolchain", "lake-manifest.json"))
    paths.update(
        ROOT / "formal/tla" / name
        for name in ("DeltaReduce.tla", "DeltaReduceArithmetic.tla", "DeltaReduceReduceApply.tla")
    )
    paths.update(
        ROOT / "formal/scripts" / name
        for name in (
            "formal_artifacts.py",
            "generate_native_source_artifacts.py",
            "native_source_artifacts.py",
        )
    )
    source_hashes = [
        {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p)} for p in sorted(paths)
    ]
    result = {
        "scope": "R2_GENERAL_FAMILY_REPRESENTATION_NOT_FULL_PUBLIC_REFINEMENT",
        "status": "REPRESENTATION_TRANSFER_PROVED_R2_OPEN",
        "basis_commit": BASE,
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "formal_semantics_id_unchanged": SEMANTICS,
        "dod_sha256": DOD_SHA,
        "production_init_next_changed": False,
        "certificate_semantics_changed": False,
        "wal_identity_changed": False,
        "r3_started": False,
        "formal_go": False,
        "original_manifest": original["manifest_id"],
        "widths": [4, 8, 8, 8, 8],
        "starts": [0, 4, 12, 20, 28],
        "original_sources_sha256": sha256_file(original_path),
        "original_joined_vector_vote_qc_wal_capture": False,
        "remaining_source_gaps": original["original008_unresolved"],
        "general_bounds": (
            "Every accepted manifest loader result; positive lengths, <=4096 shards, "
            "<=524288 cells per shard. NativeFrame/DerivedParameter/NativeApply theorems "
            "are length-parametric."
        ),
        "boundary": (
            "Existing codec/hash/metadata/certificate abstractions remain. Public input/body/"
            "configuration and admission equivalence are not inferred from native numeric success."
        ),
        "new_tlc_run": False,
        "complete_formal_gate_run": False,
        "commands": commands,
        "axiom_audited_declarations": declarations,
        "sources": source_hashes,
    }
    write_canonical_json(EVIDENCE / "checks.json", result)
    files = [
        {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p)}
        for p in sorted(EVIDENCE.iterdir())
        if p.is_file()
    ]
    write_canonical_json(
        ROOT / "formal/proposals/evidence/b-family-transfer.json",
        {
            "status": result["status"],
            "basis_commit": BASE,
            "sources": source_hashes,
            "evidence": files,
            "formal_go": False,
        },
    )
    print(json.dumps({"status": result["status"], "R2": "OPEN", "R3": "NOT_STARTED"}))


if __name__ == "__main__":
    run()
