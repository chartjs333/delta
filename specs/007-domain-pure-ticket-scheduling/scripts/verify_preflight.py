"""Verify the exact feature-006, Formal and runtime-authority boundary for feature 007."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "007-domain-pure-ticket-scheduling"
OUTPUT: Final = FEATURE / "evidence" / "preflight.json"

FEATURE006_MERGE: Final = "827d3393acf347c9b45eabdb3d652bdc98bcfe75"
FEATURE006_PARENTS: Final = (
    "1e884b4122898a8e0ff17254bc42414a8773830c",
    "b487ea81851cfd5b4769579392798841cb18afc0",
)
FEATURE006_SOURCE: Final = "90cc7fac96675694bab15f4e1ae1e5c6e3f525be"
FEATURE006_OVERLAY: Final = FEATURE006_PARENTS[1]
FEATURE006_REPORT_SHA256: Final = "d16f9cfc62efe95e902b301823c136c0530db68b1cfb48788c6a239ade123800"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
REQUIRED_ACTION_IDS: Final = {
    "ACT-ABORT-FINALIZE",
    "ACT-ABORT-VOTE",
    "ACT-COMMIT",
    "ACT-JOURNAL-RECOVER",
    "ACT-LEASE-EXPIRE",
    "ACT-LEASE-OPEN",
    "ACT-LEASE-REASSIGN",
    "ACT-LEASE-RENEW",
    "ACT-RESTART",
    "ACT-TICKET-ISSUE",
}
SOURCE_ARTIFACTS: Final = (
    ".github/workflows/ci.yml",
    ".specify/memory/constitution.md",
    "Makefile",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "docs/adr/0010-hybrid-runtime-boundary.md",
    "specs/HYBRID-RUNTIME-MAP.md",
    "specs/ROADMAP.md",
    "specs/000-formal-tla-spec/failure-semantics.md",
    "specs/000-formal-tla-spec/proof-obligations.md",
    "specs/000-formal-tla-spec/refinement-contract.md",
    "specs/006-regional-hierarchical-reduce/evidence/final-compatibility.json",
    "specs/007-domain-pure-ticket-scheduling/checklists/hybrid-runtime.md",
    "specs/007-domain-pure-ticket-scheduling/checklists/requirements.md",
    "specs/007-domain-pure-ticket-scheduling/formal-refinement.md",
    "specs/007-domain-pure-ticket-scheduling/plan.md",
    "specs/007-domain-pure-ticket-scheduling/runtime-profile.md",
    "specs/007-domain-pure-ticket-scheduling/runtime-tasks.md",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_preflight.py",
    "specs/007-domain-pure-ticket-scheduling/spec.md",
    "specs/007-domain-pure-ticket-scheduling/task-map.md",
    "specs/007-domain-pure-ticket-scheduling/tasks.md",
    "specs/007-domain-pure-ticket-scheduling/tests/test_verify_preflight.py",
)
PRODUCTION_PREFIXES: Final = (
    "delta-core-cpp/",
    "delta-runtime-cpp/",
    "delta-ffi/",
    "delta-node-java/",
    "delta-worker-python/",
    "delta-protocol/",
)
ALLOWED_PREFLIGHT_PATHS: Final = {".github/workflows/ci.yml", "Makefile", "specs/ROADMAP.md"}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class PreflightError(RuntimeError):
    """Stable fail-closed feature-007 preflight error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PreflightError(f"{code}:{detail}" if detail else code)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    return git_bytes("show", f"{revision}:{path}")


def tracked_text(path: str, revision: str) -> str:
    return tracked_bytes(path, revision).decode()


def artifact(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}


def require_ancestor(ancestor: str, descendant: str, code: str) -> None:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, code)


def validate_feature006_document(document: dict[str, Any]) -> None:
    require(document.get("status") == "PASS", "FEATURE006_STATUS_INVALID")
    require(document.get("classification") == "REFINEMENT_ONLY", "FEATURE006_CLASS_INVALID")
    require(document.get("semantic_completeness_claimed") is False, "FEATURE006_CLAIM_INVALID")
    require(
        document.get("formal")
        == {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "FEATURE006_FORMAL_DRIFT",
    )
    source = document.get("source")
    native = document.get("native_hierarchy")
    ci = document.get("hierarchy_ci")
    require(isinstance(source, dict), "FEATURE006_SOURCE_INVALID")
    require(isinstance(native, dict), "FEATURE006_NATIVE_INVALID")
    require(isinstance(ci, dict), "FEATURE006_CI_INVALID")
    require(source.get("commit") == FEATURE006_SOURCE, "FEATURE006_SOURCE_DRIFT")
    require(native.get("status") == "PASS", "FEATURE006_NATIVE_STATUS_INVALID")
    require(ci.get("status") == "PASS", "FEATURE006_CI_STATUS_INVALID")
    require(native.get("source") == source, "FEATURE006_NATIVE_SOURCE_DRIFT")
    require(
        ci.get("source") == {"commit": source.get("commit"), "tree": source.get("tree")},
        "FEATURE006_CI_SOURCE_DRIFT",
    )


def verify_manifest(entries: object, revision: str, code: str) -> int:
    require(isinstance(entries, list) and entries, code)
    for entry in entries:
        require(isinstance(entry, dict), code)
        path, expected = entry.get("path"), entry.get("sha256")
        require(isinstance(path, str) and isinstance(expected, str), code)
        require(sha256_bytes(tracked_bytes(path, revision)) == expected, code, path)
    return len(entries)


def verify_feature006(source_commit: str) -> dict[str, Any]:
    parents = tuple(git_text("show", "-s", "--format=%P", FEATURE006_MERGE).split())
    require(parents == FEATURE006_PARENTS, "FEATURE006_MERGE_PARENTS_INVALID")
    require_ancestor(FEATURE006_SOURCE, FEATURE006_OVERLAY, "FEATURE006_SOURCE_CHAIN_INVALID")
    require_ancestor(FEATURE006_OVERLAY, FEATURE006_MERGE, "FEATURE006_OVERLAY_CHAIN_INVALID")
    require_ancestor(FEATURE006_MERGE, source_commit, "FEATURE006_MERGE_NOT_ANCESTOR")
    report_path = "specs/006-regional-hierarchical-reduce/evidence/final-compatibility.json"
    report_raw = tracked_bytes(report_path, FEATURE006_MERGE)
    require(sha256_bytes(report_raw) == FEATURE006_REPORT_SHA256, "FEATURE006_REPORT_HASH_DRIFT")
    document = json.loads(report_raw.decode())
    require(isinstance(document, dict), "FEATURE006_REPORT_INVALID")
    validate_feature006_document(document)
    source_count = verify_manifest(
        document.get("source", {}).get("artifacts"),
        FEATURE006_SOURCE,
        "FEATURE006_SOURCE_MANIFEST_DRIFT",
    )
    evidence_count = verify_manifest(
        document.get("evidence_artifacts"),
        FEATURE006_MERGE,
        "FEATURE006_EVIDENCE_MANIFEST_DRIFT",
    )
    for path in (
        "specs/006-regional-hierarchical-reduce/tasks.md",
        "specs/006-regional-hierarchical-reduce/runtime-tasks.md",
    ):
        require(
            not re.search(r"^- \[ \] ", tracked_text(path, FEATURE006_MERGE), re.MULTILINE),
            "FEATURE006_TASK_OPEN",
            path,
        )
    return {
        "evidence_artifact_count": evidence_count,
        "evidence_overlay": FEATURE006_OVERLAY,
        "merge_commit": FEATURE006_MERGE,
        "merge_parents": list(FEATURE006_PARENTS),
        "report": artifact(report_path, FEATURE006_MERGE),
        "report_sha256": FEATURE006_REPORT_SHA256,
        "source_artifact_count": source_count,
        "source_commit": FEATURE006_SOURCE,
        "status": "PASS",
    }


def load_feature006_preflight() -> Any:
    path = ROOT / "specs/006-regional-hierarchical-reduce/scripts/verify_preflight.py"
    spec = importlib.util.spec_from_file_location("feature006_preflight_dependency", path)
    require(spec is not None and spec.loader is not None, "FORMAL_HELPER_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_formal(source_commit: str) -> dict[str, Any]:
    result = load_feature006_preflight().verify_formal(source_commit)
    require(result.get("status") == "GO", "FORMAL_NOT_GO")
    refinement = tracked_text("formal/tla/DeltaReduceRefinement.tla", source_commit)
    missing = sorted(action for action in REQUIRED_ACTION_IDS if f'"{action}"' not in refinement)
    require(not missing, "FORMAL_ACTION_MISSING", ",".join(missing))
    failure = tracked_text("specs/000-formal-tla-spec/failure-semantics.md", source_commit)
    for marker in (
        "Ticket lease expires before commitment",
        "Old/new lease holders race",
        "replay/verify durable vote and transition journal",
    ):
        require(marker in failure, "FORMAL_FAILURE_RULE_MISSING", marker)
    return {**result, "required_action_ids": sorted(REQUIRED_ACTION_IDS)}


def verify_architecture(source_commit: str) -> dict[str, Any]:
    changed = git_text("diff", "--name-only", FEATURE006_MERGE, source_commit).splitlines()
    production = [path for path in changed if path.startswith(PRODUCTION_PREFIXES)]
    require(not production, "PRODUCTION_SOURCE_BEFORE_PREFLIGHT", json.dumps(production))
    unexpected = [
        path
        for path in changed
        if not path.startswith("specs/007-domain-pure-ticket-scheduling/")
        and path not in ALLOWED_PREFLIGHT_PATHS
    ]
    require(not unexpected, "UNEXPECTED_PREFLIGHT_PATH", json.dumps(unexpected))
    paths = (
        "specs/007-domain-pure-ticket-scheduling/formal-refinement.md",
        "specs/007-domain-pure-ticket-scheduling/plan.md",
        "specs/007-domain-pure-ticket-scheduling/runtime-profile.md",
        "specs/007-domain-pure-ticket-scheduling/spec.md",
        "specs/007-domain-pure-ticket-scheduling/task-map.md",
        "specs/007-domain-pure-ticket-scheduling/tasks.md",
    )
    combined = "\n".join(tracked_text(path, source_commit) for path in paths)
    require("src/deltatorrent/scheduling" not in combined, "LEGACY_PYTHON_AUTHORITY_PATH")
    for marker in (
        "C++ alone",
        "Java",
        "Python",
        "adaptive-H",
        "device-weight",
        "opaque timer",
        "pre-ISC randomness",
        "commitment versus expiry",
    ):
        require(marker in combined, "AUTHORITY_RULE_UNBOUND", marker)
    return {
        "changed_path_count": len(changed),
        "finding_count": 0,
        "findings": [],
        "production_source_count": 0,
        "status": "PASS",
        "zero_authority_paths": [
            "adaptive_fixed_work",
            "device_derived_math",
            "java_scheduling_decision",
            "pre_isc_random_scheduling",
            "python_scheduling_authority",
            "stale_weighting",
        ],
    }


def verify_formal_impact(source_commit: str) -> dict[str, Any]:
    diff = git_text(
        "diff",
        "--name-only",
        FEATURE006_MERGE,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not diff, "FORMAL_SOURCE_DIFF_PRESENT", diff)
    refinement = tracked_text(
        "specs/007-domain-pure-ticket-scheduling/formal-refinement.md", source_commit
    )
    profile = tracked_text(
        "specs/007-domain-pure-ticket-scheduling/runtime-profile.md", source_commit
    )
    require("**Classification**: `REFINEMENT_ONLY`" in refinement, "FORMAL_CLASS_INVALID")
    require("**Formal impact**: `REFINEMENT_ONLY`" in profile, "RUNTIME_FORMAL_CLASS_INVALID")
    require(FORMAL_ID in refinement, "FORMAL_ID_UNBOUND")
    return {
        "classification": "REFINEMENT_ONLY",
        "new_failure_terminals": [],
        "new_formal_action_ids": [],
        "new_protocol_visible_durability_outcomes": [],
        "status": "PASS",
    }


def verify_source(source_commit: str) -> dict[str, Any]:
    require_ancestor(source_commit, "HEAD", "PREFLIGHT_SOURCE_NOT_ANCESTOR")
    require(
        "**Version**: 2.1.0" in tracked_text(".specify/memory/constitution.md", source_commit),
        "CONSTITUTION_VERSION_INVALID",
    )
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
            "FEATURE006_MERGE_SOURCE_EVIDENCE_EXACT",
            "FEATURE006_TASKS_AND_MANIFESTS_EXACT",
            "FORMAL_GO_AND_24_ARTIFACTS_REDERIVED",
            "TICKET_LEASE_RECOVERY_ACTIONS_EXIST",
            "NO_FORMAL_SOURCE_DIFF",
            "ZERO_ADAPTIVE_STALE_DEVICE_RANDOM_AUTHORITY_PATHS",
            "REFINEMENT_ONLY_CLASSIFICATION",
            "PREFLIGHT_SOURCE_TREE_BOUND",
        ],
        "errors": [],
        "feature006": verify_feature006(source_commit),
        "formal": verify_formal(source_commit),
        "formal_impact": verify_formal_impact(source_commit),
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": verify_source(source_commit),
        "status": "PASS",
        "task_ids": ["T000", "T001", "T002", "T003", "T004"],
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "PREFLIGHT_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "PREFLIGHT_SOURCE_INVALID",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        result = verify(source_for_run(arguments.check_only))
        encoded = canonical_json_bytes(result)
        if arguments.check_only:
            require(OUTPUT.read_bytes() == encoded, "PREFLIGHT_EVIDENCE_STALE")
        else:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(encoded)
    except (
        PreflightError,
        RuntimeError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(
            canonical_json_bytes(
                {
                    "error_code": str(error),
                    "formal_semantics_id": FORMAL_ID,
                    "schema_version": "1.0.0",
                    "status": "FAIL",
                }
            ).decode()
        )
        return 2
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
