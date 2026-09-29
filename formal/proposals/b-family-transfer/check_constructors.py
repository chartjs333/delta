"""Reproduce the R2 constructor/domain checkpoint; never issue a GO.

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
EVIDENCE = ROOT / "formal/proposals/evidence/b-family-constructors"
BASE = "4d67478f35450638799076edf89152efc34708a7"
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


def declared_names(text: str) -> list[str]:
    """Keep namespace qualification while sections only scope variables."""
    declaration = r"^(?:@\[[^\n]+\]\s*)?(?:structure|inductive|def|abbrev|theorem) ([\w.]+)"
    scopes: list[tuple[str, str]] = []
    names = []
    for line in text.splitlines():
        if start := re.fullmatch(r"(namespace|section)(?: (\S+))?", line):
            scopes.append((start[1], start[2] or ""))
        elif end := re.fullmatch(r"end(?: (\S+))?", line):
            require(bool(scopes), "AUDIT_UNMATCHED_END")
            _, name = scopes.pop()
            require(end[1] is None or end[1] == name, "AUDIT_SCOPE_MISMATCH")
        elif found := re.match(declaration, line):
            namespace = ".".join(name for kind, name in scopes if kind == "namespace")
            require(bool(namespace), "AUDIT_MISSING_NAMESPACE")
            names.append(f"{namespace}.{found[1]}")
    require(not scopes, "AUDIT_UNCLOSED_SCOPE")
    require(len(names) == len(re.findall(declaration, text, re.M)), "AUDIT_DROPPED_NAME")
    require(len(set(names)) == len(names), "AUDIT_DUPLICATE_NAME")
    return names


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
            "DeltaReduce.NativeRootParents",
            "DeltaReduce.PublicParentNames",
            "DeltaReduce.PublicDurablePrefix",
            "DeltaReduce.NativeVoteCache",
        ],
        dependencies=True,
    )
    sources = {
        "VectorShardRepresentation": ROOT / "formal/proposals/vector-shard-representation.lean",
        "SyncFamily": ROOT / "formal/proposals/b-feasibility/SyncFamily.lean",
        **{
            name: HERE / f"{name}.lean"
            for name in (
                "ShardFamily",
                "ManifestFamily",
                "NativeFamily",
                "StateFamily",
                "Checks",
                "FamilyInputs",
                "FamilyAuthority",
                "FamilyParameter",
                "FamilyApplyArithmetic",
                "FamilyGuards",
                "FamilyApply",
                "FamilyRoot",
                "FamilyRelation",
                "FamilyChecks",
            )
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
            declarations += declared_names(text)
    audit = BUILD / "Audit.lean"
    audit.write_text(
        "import FamilyChecks\nimport Checks\n"
        + "\n".join(f"#print axioms {name}" for name in declarations)
        + "\n",
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

    for name, source in sources.items():
        require(
            sha256_file(source) == sha256_file(BUILD / f"{name}.lean"), "SOURCE_CHANGED_DURING_RUN"
        )
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
    paths.update(
        ROOT / name
        for name in (
            "delta-core-cpp/src/apply/engine.cpp",
            "delta-core-cpp/src/certificates/contracts.cpp",
            "delta-core-cpp/src/arithmetic.cpp",
            "delta-runtime-cpp/src/certificate_runtime.cpp",
            "specs/000-formal-tla-spec/candidate-contract.md",
            "specs/000-formal-tla-spec/amendments/0001-arithmetic-input-binding.md",
            "formal/proposals/b-family-transfer/CONSTRUCTORS.md",
        )
    )
    source_hashes = [
        {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p)} for p in sorted(paths)
    ]
    result = {
        "scope": "R2_FROZEN_FULL_CONSTRUCTORS_NATIVE_DOMAINS_STATIC_SOURCE_RELATION",
        "status": "R2_1_CLOSED_R2_2_CLOSED_R2_3_OPEN",
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
            "Length-parametric direct original-source constructors and numeric implications "
            "within original native bounds; no draft layout/Q/name/pack/signed-denominator "
            "restriction. Full static source/configuration/alias correspondence remains R2.3; "
            "universal admission/refinement is NOT claimed."
        ),
        "boundary": (
            "Existing codec/hash/metadata/certificate/UnitSource abstractions remain. Full "
            "configuration/alias provenance and exact static state correspondence remain OPEN. "
            "The numeric original-optimizer graph is source-reviewed, not C++ "
            "execution/compiler verification."
        ),
        "residual": {
            "R2_1": {
                "status": "CLOSED",
                "closed": [
                    "original vector coordinate input selection and complete public field "
                    "construction",
                    "full PARAMETER/ROOT/APPLY leaves without later arithmetic prerequisites on "
                    "ROOT",
                    "length-parametric constructor existence over checked input authority",
                    "PARAMETER value computed from the same embedded public image and original "
                    "ordered native rows",
                    "PARAMETER gate and aggregate canonicality derived from checked authority, "
                    "primitive names and the existing leaf uniqueness condition",
                    "full APPLY executable gate from constructed components; next vector "
                    "tables retain canonical original shard keys",
                    "same embedded current cells and encoded next cells are joined by the "
                    "actual scalar mixture/optimizer at the original global coordinate",
                    "full authority canonicality and executable acceptance derived from "
                    "original atom/header/commitment loaders, primitive canonical metadata "
                    "and exact encoded-set uniqueness",
                    "exact block/corpus/family/authority source loading on the checked input "
                    "domain, composed directly with complete PARAMETER/APPLY body gates",
                    "OMIT_UNAVAILABLE full configured input completion with exact active-row "
                    "noninterference, without claiming unavailable bytes are zero",
                    "full original image construction and canonicality from primitive "
                    "namespaces and the same original numeric configuration",
                    "complete direct original PARAMETER/ROOT/APPLY construction avoiding "
                    "draft graph representability restrictions",
                ],
                "remaining": [],
            },
            "R2_2": {
                "status": "CLOSED",
                "closed": [
                    "INT64/INT128 checked typed-native arithmetic implies corresponding public "
                    "numeric guards",
                    "separate symmetric result bound includes the signed minimum",
                    "original uint64 optimizer denominators and exact rounding/operation graph",
                    "all numeric input guards derived from actual source input image",
                    "original final mixture LCM bound entails signed domain-weight "
                    "denominator and prefix checks, using the exact native LCM recurrence",
                    "direct original coefficient/APC/manifest source implies each numeric "
                    "PARAMETER guard without draft caps",
                    "original full uint64 common/optimizer denominator domain composes with "
                    "the full input and body constructors",
                    "same original policy selects the normalized immutable profile and "
                    "existing source-keyed quantum; all numeric input guards are derived",
                    "full original conversion/mixture/optimizer checks compose at the same "
                    "global shard offset and current/next cells",
                ],
                "remaining": [],
            },
            "R2_3": {
                "status": "OPEN_PARTIAL_COMPOSITION",
                "closed": [
                    "same-store frame/row equality derived; original arithmetic vote bytes and "
                    "sequences retained",
                    "ROOT primitive metadata and exact original certificate leaves compose with "
                    "family bodies",
                    "same decoded original policy, exact actor namespace and no alias inflation",
                    "generic signer membership/count and actual checked ISC quorum preserved",
                    "one direct executable source/profile/input/authority/body/vote projection "
                    "from original policy/state and canonical WAL/receipt bytes, without the "
                    "old draft Binding body adapter",
                    "original candidate and complete native snapshot/list retained; all "
                    "coordinate views share the original body ID, actor and sequence",
                    "exact arithmetic-input/APC member order and names; primitive actor, "
                    "height, epoch, config and current-parent namespaces checked together",
                    "observed nonempty current-pointer history supplies original model/optimizer "
                    "preimages through the existing reader; UNKNOWN is rejected",
                    "durable WAL-only arithmetic observation derives its receipt without "
                    "claiming response exposure; observed receipts must match exactly",
                    "complete mixed WAL scan and original positions retained, including "
                    "intervening commands; corrupt, torn and UNKNOWN observations reject",
                    "numeric current carrier no longer requires a fabricated prior APPLY; "
                    "canonical values bind to existing explicitly authenticated anchor hashes",
                    "direct original ROOT selector, finalized full ordered certificates and "
                    "family aggregate compose with existing AGGREGATE_ROOT/APC envelope",
                ],
                "remaining": [
                    "one authenticated configuration/alias/source relation across all existing "
                    "object kinds",
                    "entire static public/native state and certificate/vote collections with "
                    "exact coverage",
                    "complete all-actor original journal/static-state coverage, including "
                    "arbitrary initial current snapshots and existing non-arithmetic projections; "
                    "the direct arithmetic observation does not imply that complete relation",
                ],
            },
        },
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
        ROOT / "formal/proposals/evidence/b-family-constructors.json",
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
