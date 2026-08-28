"""Verify feature-004 predecessor, formal arithmetic and architecture before source."""

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
FEATURE = ROOT / "specs" / "004-compressed-delta-protocol"
DEFAULT_OUTPUT = FEATURE / "evidence" / "preflight.json"

EXPECTED_FEATURE003_MERGE = "53da4d3c0b236726566fb242fdcae84032b42679"
EXPECTED_FEATURE003_MERGE_PARENTS = (
    "a48d2af86fc7a976cb20b6be28058d22b09cec54",
    "f4f2101969d14709834ab6b6d60e88755d710334",
)
EXPECTED_FEATURE003_SOURCE = "189e5f155b787c2d1d391630fc599b67ea366bba"
EXPECTED_FEATURE003_OVERLAY = EXPECTED_FEATURE003_MERGE_PARENTS[1]
EXPECTED_FEATURE003_COMPAT_SHA256 = (
    "2cd392aafaba1ab70cc0a6919cae9580955c742f9f92296f54a570af29dca769"
)
EXPECTED_PROTOCOL_REGISTRY_SHA256 = (
    "bb037e00ea1a7eac1458c2ed1076b733dfbcc579fad25ed4ebd053c622a82af9"
)
EXPECTED_ABI_DESCRIPTOR_SHA256 = "3e19d745f2d702f0e77bd32f6c83fd50763237ecc505d735a0a68364f9a67f64"
EXPECTED_PREPARED_100_SHA256 = "91e5bd220c50d9dda5ed6d015243255f8219372d33e0be18b259bbe5338b7324"

EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_FORMAL_SOURCE = "1e6e0f6f70056161d95933e71494ec390c7c1151"
EXPECTED_FORMAL_REPORT_SHA256 = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"
EXPECTED_LEAN_REPORT_SHA256 = "4e79a87aa6524049f544cb235255af3aa38630ab8f2427455884d1618999e329"
EXPECTED_FIXEDPOINT_SHA256 = "6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736"

EXPECTED_EXIT_RESULT = {
    "effect_transcript_sha256": "11d4f62cba6b96eb17710e023c910ff67da69eebaf3896b275f551c443a3147d",
    "final_state_id": "sha256:c6fcf9131d0a481aee2918bf894dbebc62442dcb26be3c559630841f4d26f967",
    "runtime_count": 4,
    "status": "PASS",
    "ticket_count": 100,
    "wal_file_sha256": "cc08e6944772f16e460495963ae4bdd630abeb7afb7126e13b95a636e3c54f90",
    "wal_transcript_sha256": "9ddb1ff79eb2ef556e1310aa9cf057fadbe9dd50e952307473bbcd9775b72a06",
}

EXPECTED_ARITHMETIC_CONJUNCTS = {
    "PO-A1:product-bound": "DeltaReduce.signedProductBound",
    "PO-A2:flat-accumulator-bound": "DeltaReduce.flatAccumulatorBound",
    "PO-A3:numerator-accumulator-bound": "DeltaReduce.commonDenominatorNumeratorSafe",
    "PO-A3:positive-input-denominator": "DeltaReduce.reducedRationalDenominatorPositive",
    "PO-A3:canonical-reduced-input": "DeltaReduce.reducedRationalIsCoprime",
    "PO-A3:positive-common-denominator": "DeltaReduce.commonDenominatorPositive",
    "PO-A3:input-denominator-divides-common": "DeltaReduce.eachDenominatorDividesCommon",
    "PO-A3:round-below-half": "DeltaReduce.canonicalRoundBelowHalf",
    "PO-A3:round-at-or-above-half": "DeltaReduce.canonicalRoundAtOrAboveHalf",
    "PO-A3:round-half-tie-toward-positive": "DeltaReduce.canonicalRoundTieTowardPositive",
    "PO-A3:rounding-deterministic": "DeltaReduce.canonicalRoundDeterministic",
}

SOURCE_ARTIFACTS = (
    ".github/workflows/ci.yml",
    ".specify/memory/constitution.md",
    "Makefile",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "docs/adr/0010-hybrid-runtime-boundary.md",
    "specs/ROADMAP.md",
    "specs/004-compressed-delta-protocol/checklists/hybrid-runtime.md",
    "specs/004-compressed-delta-protocol/checklists/requirements.md",
    "specs/004-compressed-delta-protocol/formal-refinement.md",
    "specs/004-compressed-delta-protocol/plan.md",
    "specs/004-compressed-delta-protocol/runtime-profile.md",
    "specs/004-compressed-delta-protocol/runtime-tasks.md",
    "specs/004-compressed-delta-protocol/scripts/verify_preflight.py",
    "specs/004-compressed-delta-protocol/spec.md",
    "specs/004-compressed-delta-protocol/task-map.md",
    "specs/004-compressed-delta-protocol/tasks.md",
)

NATIVE_SOURCE_PREFIXES = (
    "delta-core-cpp/include/",
    "delta-core-cpp/src/",
    "delta-runtime-cpp/include/",
    "delta-runtime-cpp/src/",
    "delta-ffi/include/",
    "delta-ffi/src/",
)
NATIVE_SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}
FORBIDDEN_NATIVE_PATTERNS = {
    "FLOAT_CONSENSUS_TYPE": re.compile(r"\b(?:float|double)\b"),
    "FAST_MATH": re.compile(r"(?:-ffast-math|/fp:fast)"),
    "SATURATION_PATH": re.compile(r"\b(?:saturate|saturation|saturating)\b", re.IGNORECASE),
    "Q_TO_FLOAT_PATH": re.compile(r"q[_A-Za-z0-9]*\s*(?:to|as)[_A-Za-z0-9]*float", re.IGNORECASE),
}
FORBIDDEN_PLANNED_PATTERNS = {
    "LEGACY_PYTHON_FIXEDPOINT": re.compile(r"src/deltatorrent/fixedpoint/"),
    "LEGACY_PYTHON_SHARDS": re.compile(r"src/deltatorrent/shards/"),
    "LEGACY_PYTHON_REDUCE": re.compile(r"src/deltatorrent/reduce/"),
    "RESIDUAL_IMPLEMENTATION": re.compile(r"(?:residual\.py|Implement candidate/prior/current)"),
}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes, derive_formal_semantics_id  # noqa: E402


class PreflightError(RuntimeError):
    """Stable fail-closed feature-004 preflight error."""


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
        reject("GIT_COMMAND_FAILED", completed.stderr.decode(errors="replace").strip())
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    return git_bytes("show", f"{revision}:{path}")


def tracked_text(path: str, revision: str) -> str:
    return tracked_bytes(path, revision).decode("utf-8")


def tracked_json(path: str, revision: str) -> dict[str, Any]:
    try:
        value = json.loads(tracked_text(path, revision))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("JSON_INVALID", f"{path}:{exc}")
    require(isinstance(value, dict), "JSON_ROOT_INVALID", path)
    return value


def artifact(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}


def require_ancestor(ancestor: str, descendant: str, code: str) -> None:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0, code)


def discover_formal_artifacts(revision: str) -> list[dict[str, str]]:
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


def verify_feature003(source_commit: str) -> dict[str, Any]:
    parents = tuple(git_text("show", "-s", "--format=%P", EXPECTED_FEATURE003_MERGE).split())
    require(parents == EXPECTED_FEATURE003_MERGE_PARENTS, "FEATURE003_MERGE_PARENTS_INVALID")
    require_ancestor(
        EXPECTED_FEATURE003_SOURCE, EXPECTED_FEATURE003_OVERLAY, "FEATURE003_SOURCE_CHAIN_INVALID"
    )
    require_ancestor(
        EXPECTED_FEATURE003_OVERLAY, EXPECTED_FEATURE003_MERGE, "FEATURE003_OVERLAY_CHAIN_INVALID"
    )
    require_ancestor(EXPECTED_FEATURE003_MERGE, source_commit, "FEATURE003_MERGE_NOT_ANCESTOR")

    compatibility_path = "specs/003-bft-round-state-machine/evidence/final-compatibility.json"
    compatibility_raw = tracked_bytes(compatibility_path, EXPECTED_FEATURE003_MERGE)
    require(
        sha256_bytes(compatibility_raw) == EXPECTED_FEATURE003_COMPAT_SHA256,
        "FEATURE003_COMPATIBILITY_HASH_MISMATCH",
    )
    compatibility = json.loads(compatibility_raw.decode("utf-8"))
    require(
        compatibility.get("status") == "PASS"
        and compatibility.get("classification") == "REFINEMENT_ONLY"
        and compatibility.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and compatibility.get("semantic_completeness_claimed") is False
        and compatibility.get("source", {}).get("commit") == EXPECTED_FEATURE003_SOURCE
        and compatibility.get("task_counts") == {"HR003": 24, "T": 53}
        and compatibility.get("native_exit") == EXPECTED_EXIT_RESULT,
        "FEATURE003_COMPATIBILITY_INVALID",
    )
    require(
        compatibility.get("new_formal_action_ids") == []
        and compatibility.get("new_failure_terminals") == []
        and compatibility.get("new_protocol_visible_durability_outcomes") == [],
        "FEATURE003_FORMAL_IMPACT_INVALID",
    )

    exit_gate = tracked_text(
        "specs/003-bft-round-state-machine/evidence/exit-gate.md",
        EXPECTED_FEATURE003_MERGE,
    )
    require(
        "**Decision**: PASS" in exit_gate
        and EXPECTED_FEATURE003_SOURCE in exit_gate
        and EXPECTED_FEATURE003_COMPAT_SHA256 in exit_gate,
        "FEATURE003_EXIT_GATE_INVALID",
    )
    for path, expected in (
        ("delta-protocol/registry.json", EXPECTED_PROTOCOL_REGISTRY_SHA256),
        ("delta-protocol/schemas/003/delta-abi-v1.json", EXPECTED_ABI_DESCRIPTOR_SHA256),
        (
            "delta-protocol/fixtures/003/cross-language/prepared-100-v1.json",
            EXPECTED_PREPARED_100_SHA256,
        ),
    ):
        require(
            sha256_bytes(tracked_bytes(path, EXPECTED_FEATURE003_MERGE)) == expected,
            "FEATURE003_ARTIFACT_HASH_MISMATCH",
            path,
        )

    tasks = tracked_text("specs/003-bft-round-state-machine/tasks.md", EXPECTED_FEATURE003_MERGE)
    runtime_tasks = tracked_text(
        "specs/003-bft-round-state-machine/runtime-tasks.md", EXPECTED_FEATURE003_MERGE
    )
    require(not re.findall(r"^- \[ \] ", tasks, re.MULTILINE), "FEATURE003_TASK_INCOMPLETE")
    require(
        not re.findall(r"^- \[ \] ", runtime_tasks, re.MULTILINE),
        "FEATURE003_RUNTIME_TASK_INCOMPLETE",
    )
    return {
        "artifacts": [
            artifact(compatibility_path, EXPECTED_FEATURE003_MERGE),
            artifact(
                "specs/003-bft-round-state-machine/evidence/exit-gate.md",
                EXPECTED_FEATURE003_MERGE,
            ),
            artifact("delta-protocol/registry.json", EXPECTED_FEATURE003_MERGE),
            artifact("delta-protocol/schemas/003/delta-abi-v1.json", EXPECTED_FEATURE003_MERGE),
            artifact(
                "delta-protocol/fixtures/003/cross-language/prepared-100-v1.json",
                EXPECTED_FEATURE003_MERGE,
            ),
        ],
        "evidence_overlay": EXPECTED_FEATURE003_OVERLAY,
        "final_source": EXPECTED_FEATURE003_SOURCE,
        "merge_commit": EXPECTED_FEATURE003_MERGE,
        "merge_parents": list(EXPECTED_FEATURE003_MERGE_PARENTS),
        "native_exit": EXPECTED_EXIT_RESULT,
        "status": "PASS",
    }


def verify_formal(source_commit: str) -> dict[str, Any]:
    artifacts = discover_formal_artifacts(source_commit)
    require(len(artifacts) == 24, "FORMAL_ARTIFACT_COUNT_INVALID")
    semantics = tracked_json("formal/reports/formal-semantics.json", source_commit)
    require(semantics.get("semantic_artifacts") == artifacts, "FORMAL_ARTIFACT_MANIFEST_DRIFT")
    require(
        derive_formal_semantics_id("1.0.0", artifacts) == EXPECTED_FORMAL_ID,
        "FORMAL_SEMANTICS_ID_DRIFT",
    )

    report_path = "formal/reports/formal-verification-report.json"
    report_raw = tracked_bytes(report_path, source_commit)
    require(sha256_bytes(report_raw) == EXPECTED_FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_DRIFT")
    report = json.loads(report_raw.decode("utf-8"))
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and report.get("source_tree", {}).get("commit") == EXPECTED_FORMAL_SOURCE,
        "FORMAL_REPORT_NOT_EXACT_GO",
    )
    theorem_checks = {
        item.get("id"): item
        for item in report.get("theorem_checks", [])
        if isinstance(item, dict) and item.get("id") in {"PO-A1", "PO-A2", "PO-A3"}
    }
    require(set(theorem_checks) == {"PO-A1", "PO-A2", "PO-A3"}, "ARITHMETIC_THEOREM_SET_INVALID")
    require(
        all(
            item.get("status") == "PASS" and item.get("verified")
            for item in theorem_checks.values()
        ),
        "ARITHMETIC_THEOREM_NOT_VERIFIED",
    )

    lean_path = "formal/reports/lean-proof-report.json"
    lean_raw = tracked_bytes(lean_path, source_commit)
    require(sha256_bytes(lean_raw) == EXPECTED_LEAN_REPORT_SHA256, "LEAN_REPORT_HASH_DRIFT")
    lean = json.loads(lean_raw.decode("utf-8"))
    require(lean.get("status") == "PASS" and lean.get("errors") == [], "LEAN_REPORT_INVALID")
    conjuncts = {
        item.get("id"): item
        for item in lean.get("normative_conjuncts", [])
        if isinstance(item, dict) and item.get("proof_obligation_id") in {"PO-A1", "PO-A2", "PO-A3"}
    }
    require(set(conjuncts) == set(EXPECTED_ARITHMETIC_CONJUNCTS), "ARITHMETIC_CONJUNCT_SET_INVALID")
    for identifier, theorem in EXPECTED_ARITHMETIC_CONJUNCTS.items():
        item = conjuncts[identifier]
        require(
            item.get("status") == "PASS"
            and item.get("theorem") == theorem
            and item.get("source") == "formal/proofs/DeltaReduce/FixedPoint.lean"
            and item.get("source_sha256") == EXPECTED_FIXEDPOINT_SHA256,
            "ARITHMETIC_CONJUNCT_INVALID",
            identifier,
        )
    require(
        sha256_bytes(tracked_bytes("formal/proofs/DeltaReduce/FixedPoint.lean", source_commit))
        == EXPECTED_FIXEDPOINT_SHA256,
        "FIXEDPOINT_SOURCE_HASH_DRIFT",
    )
    return {
        "artifact_count": len(artifacts),
        "arithmetic_conjuncts": [
            {"id": identifier, "theorem": EXPECTED_ARITHMETIC_CONJUNCTS[identifier]}
            for identifier in sorted(EXPECTED_ARITHMETIC_CONJUNCTS)
        ],
        "fixedpoint_source_sha256": EXPECTED_FIXEDPOINT_SHA256,
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "lean_report_sha256": EXPECTED_LEAN_REPORT_SHA256,
        "report_sha256": EXPECTED_FORMAL_REPORT_SHA256,
        "source_commit": EXPECTED_FORMAL_SOURCE,
        "status": "PASS",
    }


def source_paths(revision: str) -> list[str]:
    return git_text("ls-tree", "-r", "--name-only", revision).splitlines()


def verify_architecture(source_commit: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    changed = git_text("diff", "--name-only", EXPECTED_FEATURE003_MERGE, source_commit).splitlines()
    production_prefixes = (
        "delta-core-cpp/",
        "delta-runtime-cpp/",
        "delta-ffi/",
        "delta-node-java/src/",
        "delta-worker-python/src/",
        "delta-protocol/schemas/004/",
        "delta-protocol/fixtures/004/",
    )
    for path in changed:
        if path.startswith(production_prefixes):
            findings.append({"id": "PRODUCTION_SOURCE_BEFORE_PREFLIGHT", "path": path})

    spec_paths = [
        path
        for path in source_paths(source_commit)
        if path.startswith("specs/004-compressed-delta-protocol/") and path.endswith(".md")
    ]
    planned_text = "\n".join(tracked_text(path, source_commit) for path in spec_paths)
    for identifier, pattern in FORBIDDEN_PLANNED_PATTERNS.items():
        if pattern.search(planned_text):
            findings.append({"id": identifier, "path": "specs/004-compressed-delta-protocol"})

    native_sources = [
        path
        for path in source_paths(source_commit)
        if path.startswith(NATIVE_SOURCE_PREFIXES)
        and Path(path).suffix.lower() in NATIVE_SOURCE_SUFFIXES
    ]
    for path in native_sources:
        text = tracked_text(path, source_commit)
        for identifier, pattern in FORBIDDEN_NATIVE_PATTERNS.items():
            if pattern.search(text):
                findings.append({"id": identifier, "path": path})

    python_paths = [
        path
        for path in source_paths(source_commit)
        if re.search(
            r"^delta-worker-python/src/deltatorrent/(?:fixedpoint|shards|reduce|residual)(?:/|\.)",
            path,
        )
    ]
    findings.extend(
        {"id": "PYTHON_CONSENSUS_AUTHORITY_PATH", "path": path} for path in python_paths
    )
    require(not findings, "ARCHITECTURE_FINDINGS_PRESENT", json.dumps(findings, sort_keys=True))
    return {
        "changed_path_count": len(changed),
        "finding_count": 0,
        "findings": [],
        "native_source_count": len(native_sources),
        "planned_spec_count": len(spec_paths),
        "python_consensus_path_count": 0,
        "rules": sorted([*FORBIDDEN_NATIVE_PATTERNS, *FORBIDDEN_PLANNED_PATTERNS]),
        "status": "PASS",
    }


def verify_formal_impact(source_commit: str) -> dict[str, Any]:
    diff = git_text(
        "diff",
        "--name-only",
        EXPECTED_FEATURE003_MERGE,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not diff, "FORMAL_SOURCE_DIFF_PRESENT", diff)
    profile = tracked_text("specs/004-compressed-delta-protocol/runtime-profile.md", source_commit)
    plan = tracked_text("specs/004-compressed-delta-protocol/plan.md", source_commit)
    refinement = tracked_text(
        "specs/004-compressed-delta-protocol/formal-refinement.md", source_commit
    )
    require("**Formal impact**: `REFINEMENT_ONLY`" in profile, "FORMAL_IMPACT_CLASS_INVALID")
    require(EXPECTED_FORMAL_ID in profile and EXPECTED_FORMAL_ID in plan, "FORMAL_ID_UNBOUND")
    require(
        "PO-A3 is not evidence for worker ties-to-even quantization" in plan
        and "PO-A3 does not prove the worker encoder's ties-to-even" in refinement,
        "PO_A3_BOUNDARY_UNCLEAR",
    )
    return {
        "classification": "REFINEMENT_ONLY",
        "new_failure_terminals": [],
        "new_formal_action_ids": [],
        "new_protocol_visible_durability_outcomes": [],
        "po_a3_worker_ties_even_claimed": False,
        "status": "PASS",
    }


def verify_source(source_commit: str) -> dict[str, Any]:
    require_ancestor(source_commit, "HEAD", "PREFLIGHT_SOURCE_NOT_ANCESTOR")
    constitution = tracked_text(".specify/memory/constitution.md", source_commit)
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_INVALID")
    return {
        "artifacts": [artifact(path, source_commit) for path in SOURCE_ARTIFACTS],
        "commit": source_commit,
        "constitution_version": "2.1.0",
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }


def verify(source_commit: str) -> dict[str, Any]:
    return {
        "architecture": verify_architecture(source_commit),
        "checks": [
            "FEATURE003_MERGE_SOURCE_EVIDENCE_EXACT",
            "FEATURE003_TASKS_AND_NATIVE_EXIT_EXACT",
            "FORMAL_GO_AND_24_ARTIFACTS_REDERIVED",
            "PO_A1_A2_A3_CONJUNCTS_EXACT",
            "PO_A3_WORKER_ROUNDING_BOUNDARY_EXPLICIT",
            "NO_FORMAL_SOURCE_DIFF",
            "ZERO_FLOAT_DYNAMIC_SCALE_SATURATION_LEGACY_RESIDUAL_PATHS",
            "REFINEMENT_ONLY_CLASSIFICATION",
            "RECONCILED_SOURCE_TREE_BOUND",
        ],
        "errors": [],
        "feature003": verify_feature003(source_commit),
        "formal": verify_formal(source_commit),
        "formal_impact": verify_formal_impact(source_commit),
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": verify_source(source_commit),
        "status": "PASS",
        "task_ids": ["T000", "T001", "T002", "T003", "T004"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def source_for_run(output: Path, check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(output.is_file(), "PREFLIGHT_EVIDENCE_MISSING")
    try:
        document = json.loads(output.read_text(encoding="utf-8"))
        source = document["source"]["commit"]
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
        source_commit = source_for_run(output, args.check_only)
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
