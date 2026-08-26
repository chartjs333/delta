"""Verify final feature-001 formal compatibility and write canonical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "001-reproducible-training-baseline"
DEFAULT_OUTPUT = FEATURE / "evidence" / "final-compatibility.json"
EXPECTED_SEMANTICS_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_SOURCE_COMMIT = "1e6e0f6f70056161d95933e71494ec390c7c1151"

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import (  # noqa: E402
    canonical_json_bytes,
    derive_formal_semantics_id,
)


class CompatibilityError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise CompatibilityError(code)


def load_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON_ROOT_INVALID:{relative}")
    return value


def sha256_file(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def discover_tracked_semantic_artifacts() -> list[dict[str, str]]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "formal/tla", "formal/proofs", "formal/schemas"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = completed.stdout.decode("utf-8").split("\0")
    entries: list[dict[str, str]] = []
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
        if kind is None:
            continue
        blob = subprocess.run(
            ["git", "show", f"HEAD:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        entries.append({"kind": kind, "path": path, "sha256": hashlib.sha256(blob).hexdigest()})
    return sorted(entries, key=lambda item: (item["path"], item["kind"]))


def verify() -> dict[str, Any]:
    semantics = load_json("formal/reports/formal-semantics.json")
    declared = semantics.get("semantic_artifacts")
    require(isinstance(declared, list), "SEMANTIC_ARTIFACTS_INVALID")
    discovered = discover_tracked_semantic_artifacts()
    require(discovered == declared, "FORMAL_SEMANTIC_SOURCE_DRIFT")
    derived = derive_formal_semantics_id("1.0.0", discovered)
    require(derived == EXPECTED_SEMANTICS_ID, "FORMAL_SEMANTICS_ID_DRIFT")
    require(semantics.get("formal_semantics_id") == derived, "SEMANTICS_REPORT_ID_MISMATCH")

    prerequisite = load_json(
        "specs/001-reproducible-training-baseline/evidence/formal-prerequisite.json"
    )
    foundation = load_json("specs/001-reproducible-training-baseline/evidence/foundation-gate.json")
    report = load_json("formal/reports/formal-verification-report.json")
    require(
        prerequisite.get("status") == "PASS" and prerequisite.get("formal_semantics_id") == derived,
        "FORMAL_PREREQUISITE_INVALID",
    )
    require(
        foundation.get("status") == "PASS" and foundation.get("formal_semantics_id") == derived,
        "FOUNDATION_GATE_INVALID",
    )
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == derived,
        "FORMAL_REPORT_INVALID",
    )
    source_tree = report.get("source_tree")
    require(
        isinstance(source_tree, dict)
        and source_tree.get("commit") == EXPECTED_SOURCE_COMMIT
        and source_tree.get("semantic_artifacts") == discovered,
        "FORMAL_REPORT_SOURCE_TREE_INVALID",
    )

    projection = load_json("delta-protocol/action-registry/formal-projection-v1.json")
    protocol_registry = load_json("delta-protocol/registry.json")
    ownership = semantics.get("feature_ownership")
    require(isinstance(ownership, list), "FORMAL_ACTION_OWNERSHIP_INVALID")
    formal_actions = {
        item.get("id")
        for item in ownership
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    projected_actions = set(projection.get("actions", []))
    require(projected_actions <= formal_actions, "UNREGISTERED_FORMAL_ACTION_ID")
    require(projection.get("formal_semantics_id") == derived, "PROJECTION_SEMANTICS_MISMATCH")
    require(
        protocol_registry.get("formal_semantics_id") == derived,
        "PROTOCOL_REGISTRY_SEMANTICS_MISMATCH",
    )

    runtime_profile = (FEATURE / "runtime-profile.md").read_text(encoding="utf-8")
    formal_compat = (
        ROOT / "delta-worker-python/src/deltatorrent/domain/formal_compat.py"
    ).read_text(encoding="utf-8")
    require("**Formal impact**: `REFINEMENT_ONLY`" in runtime_profile, "IMPACT_CLASS_INVALID")
    require(derived in runtime_profile and derived in formal_compat, "IMPLEMENTATION_UNBOUND")

    evidence_paths = [
        "delta-protocol/action-registry/formal-projection-v1.json",
        "delta-protocol/fixtures/formal/artifact-projection-v1.json",
        "delta-protocol/registry.json",
        "delta-worker-python/src/deltatorrent/domain/formal_compat.py",
        "docs/adr/0010-hybrid-runtime-boundary.md",
        "docs/architecture/hybrid-runtime.md",
        "docs/reproducibility.md",
        "specs/001-reproducible-training-baseline/evidence/formal-prerequisite.json",
        "specs/001-reproducible-training-baseline/evidence/foundation-gate.json",
        "specs/001-reproducible-training-baseline/runtime-profile.md",
        "specs/HYBRID-RUNTIME-MAP.md",
    ]
    return {
        "analysis_kind": "FORMAL_COMPATIBILITY_AND_CROSS_ARTIFACT",
        "artifacts": [
            {"path": path, "sha256": sha256_file(path)} for path in sorted(evidence_paths)
        ],
        "checks": [
            "FORMAL_GO_REVERIFIED",
            "FORMAL_SEMANTIC_SOURCE_SET_EXACT",
            "FORMAL_SEMANTICS_ID_REDERIVED",
            "PROJECTION_ACTION_IDS_REGISTERED",
            "RUNTIME_BOUNDARY_REFINEMENT_ONLY",
            "PROTOCOL_AND_IMPLEMENTATION_IDS_BOUND",
            "FOUNDATION_GATE_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "errors": [],
        "formal_report": {
            "decision": "GO",
            "sha256": sha256_file("formal/reports/formal-verification-report.json"),
            "source_commit": EXPECTED_SOURCE_COMMIT,
        },
        "formal_semantic_artifact_count": len(discovered),
        "formal_semantics_id": derived,
        "implementation_projection_action_ids": sorted(projected_actions),
        "new_failure_terminals": [],
        "new_formal_action_ids": [],
        "new_protocol_visible_durability_outcomes": [],
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "task_ids": ["T033", "T035"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = verify()
        encoded = canonical_json_bytes(result)
        output = args.output.resolve()
        if args.check_only:
            require(output.is_file(), "FINAL_COMPATIBILITY_EVIDENCE_MISSING")
            require(output.read_bytes() == encoded, "FINAL_COMPATIBILITY_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (CompatibilityError, OSError, ValueError, json.JSONDecodeError) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_SEMANTICS_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
