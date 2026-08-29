"""Verify the exact predecessor, Formal GO and authority boundary for feature 008."""

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
FEATURE: Final = ROOT / "specs" / "008-certificates-and-consensus"
OUTPUT: Final = FEATURE / "evidence" / "preflight.json"

FEATURE007_MERGE: Final = "2054f31ef0f6750645b924ef337a35d1737c619d"
FEATURE007_PARENTS: Final = (
    "827d3393acf347c9b45eabdb3d652bdc98bcfe75",
    "08a118c5d52a0a4f6658249cb65ea15e538904c2",
)
FEATURE007_SOURCE: Final = "781cdbd76d812bf66323a3d1d11ca93f4b9d8333"
FEATURE007_OVERLAY: Final = FEATURE007_PARENTS[1]
FEATURE007_REPORT_SHA256: Final = "2b45bf2dba25b15db624a02ee11e530a967961220e414ab04054428d44f59ef3"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FEATURE007_PLAN_ID: Final = (
    "sha256:e5dfb51a67b48809b78167156130e6cddbadcde73919ae6e6ae192db7b452a5f"
)

DEPENDENCY_REPORTS: Final = {
    "feature004": {
        "path": "specs/004-compressed-delta-protocol/evidence/final-compatibility.json",
        "sha256": "9dbd9c7bda30d6ebe9b70f33a1a16d49a2b837b140d24f87becd433f05e3dccb",
        "source": "22dd996b5d169763bfde49f32c1b1b18f2656493",
    },
    "feature005": {
        "path": "specs/005-content-addressed-p2p-distribution/evidence/final-compatibility.json",
        "sha256": "7f7f86ad5021107688277ab626b266a61c7e633eb5c401e44c7778b98733dad6",
        "source": "01f200b193733a1b474ad755c5c0c739b3189a96",
    },
    "feature006": {
        "path": "specs/006-regional-hierarchical-reduce/evidence/final-compatibility.json",
        "sha256": "d16f9cfc62efe95e902b301823c136c0530db68b1cfb48788c6a239ade123800",
        "source": "90cc7fac96675694bab15f4e1ae1e5c6e3f525be",
    },
}

REQUIRED_ACTION_IDS: Final = {
    "ACT-ABORT-FINALIZE",
    "ACT-ABORT-VOTE",
    "ACT-APC-FINALIZE",
    "ACT-APC-VOTE",
    "ACT-APPLY-COMPUTE",
    "ACT-APPLY-FINALIZE",
    "ACT-APPLY-VOTE",
    "ACT-ARTIFACT-CORRUPT",
    "ACT-ARTIFACT-LOSE",
    "ACT-ARTIFACT-REPAIR",
    "ACT-CRASH",
    "ACT-CURRENT-ADVANCE",
    "ACT-EC-FINALIZE",
    "ACT-EC-VOTE",
    "ACT-ISC-FINALIZE",
    "ACT-ISC-VOTE",
    "ACT-JOURNAL-RECOVER",
    "ACT-MESSAGE-DELIVER",
    "ACT-MESSAGE-DROP",
    "ACT-MESSAGE-DUPLICATE",
    "ACT-MESSAGE-ENQUEUE",
    "ACT-MESSAGE-REPLAY",
    "ACT-PARAM-FINALIZE",
    "ACT-PARAM-PROPOSE",
    "ACT-PARAM-VOTE",
    "ACT-RESTART",
    "ACT-ROOT-ASSEMBLE",
    "ACT-ROOT-FINALIZE",
    "ACT-ROOT-VOTE",
    "ACT-SEED-GENERATE",
}

SOURCE_ARTIFACTS: Final = (
    ".specify/memory/constitution.md",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "docs/adr/0010-hybrid-runtime-boundary.md",
    "specs/ROADMAP.md",
    "specs/000-formal-tla-spec/failure-semantics.md",
    "specs/000-formal-tla-spec/proof-obligations.md",
    "specs/000-formal-tla-spec/refinement-contract.md",
    "specs/004-compressed-delta-protocol/evidence/final-compatibility.json",
    "specs/005-content-addressed-p2p-distribution/evidence/final-compatibility.json",
    "specs/006-regional-hierarchical-reduce/evidence/final-compatibility.json",
    "specs/007-domain-pure-ticket-scheduling/evidence/final-compatibility.json",
    "specs/008-certificates-and-consensus/checklists/hybrid-runtime.md",
    "specs/008-certificates-and-consensus/checklists/requirements.md",
    "specs/008-certificates-and-consensus/formal-refinement.md",
    "specs/008-certificates-and-consensus/plan.md",
    "specs/008-certificates-and-consensus/runtime-profile.md",
    "specs/008-certificates-and-consensus/runtime-tasks.md",
    "specs/008-certificates-and-consensus/scripts/verify_preflight.py",
    "specs/008-certificates-and-consensus/spec.md",
    "specs/008-certificates-and-consensus/task-map.md",
    "specs/008-certificates-and-consensus/tasks.md",
    "specs/008-certificates-and-consensus/tests/test_verify_preflight.py",
)

PRODUCTION_PREFIXES: Final = (
    "delta-core-cpp/",
    "delta-runtime-cpp/",
    "delta-ffi/",
    "delta-node-java/",
    "delta-worker-python/",
    "delta-protocol/",
)
ALLOWED_PREFLIGHT_PATHS: Final = {"specs/ROADMAP.md"}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class PreflightError(RuntimeError):
    """Stable fail-closed feature-008 preflight error."""


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


def verify_manifest(entries: object, revision: str, code: str) -> int:
    require(isinstance(entries, list) and entries, code)
    for entry in entries:
        require(isinstance(entry, dict), code)
        path, expected = entry.get("path"), entry.get("sha256")
        require(isinstance(path, str) and isinstance(expected, str), code)
        require(sha256_bytes(tracked_bytes(path, revision)) == expected, code, path)
    return len(entries)


def validate_feature007_document(document: dict[str, Any]) -> None:
    require(document.get("status") == "PASS", "FEATURE007_STATUS_INVALID")
    require(document.get("classification") == "REFINEMENT_ONLY", "FEATURE007_CLASS_INVALID")
    require(document.get("semantic_completeness_claimed") is False, "FEATURE007_CLAIM_INVALID")
    require(
        document.get("formal")
        == {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "FEATURE007_FORMAL_DRIFT",
    )
    source = document.get("source")
    require(isinstance(source, dict), "FEATURE007_SOURCE_INVALID")
    require(source.get("commit") == FEATURE007_SOURCE, "FEATURE007_SOURCE_DRIFT")
    refinement = document.get("refinement")
    ci = document.get("scheduling_ci")
    require(
        isinstance(refinement, dict) and refinement.get("status") == "PASS",
        "FEATURE007_REFINEMENT_INVALID",
    )
    require(isinstance(ci, dict) and ci.get("status") == "PASS", "FEATURE007_CI_INVALID")
    require(
        ci.get("source")
        == {"commit": source.get("commit"), "tree": source.get("tree")},
        "FEATURE007_CI_SOURCE_DRIFT",
    )


def verify_feature007(source_commit: str) -> dict[str, Any]:
    parents = tuple(git_text("show", "-s", "--format=%P", FEATURE007_MERGE).split())
    require(parents == FEATURE007_PARENTS, "FEATURE007_MERGE_PARENTS_INVALID")
    require_ancestor(FEATURE007_SOURCE, FEATURE007_OVERLAY, "FEATURE007_SOURCE_CHAIN_INVALID")
    require_ancestor(FEATURE007_OVERLAY, FEATURE007_MERGE, "FEATURE007_OVERLAY_CHAIN_INVALID")
    require_ancestor(FEATURE007_MERGE, source_commit, "FEATURE007_MERGE_NOT_ANCESTOR")

    report_path = "specs/007-domain-pure-ticket-scheduling/evidence/final-compatibility.json"
    report_raw = tracked_bytes(report_path, FEATURE007_MERGE)
    require(sha256_bytes(report_raw) == FEATURE007_REPORT_SHA256, "FEATURE007_REPORT_HASH_DRIFT")
    document = json.loads(report_raw.decode())
    require(isinstance(document, dict), "FEATURE007_REPORT_INVALID")
    validate_feature007_document(document)
    source_count = verify_manifest(
        document.get("source", {}).get("artifacts"),
        FEATURE007_SOURCE,
        "FEATURE007_SOURCE_MANIFEST_DRIFT",
    )
    evidence_count = verify_manifest(
        document.get("evidence_artifacts"),
        FEATURE007_MERGE,
        "FEATURE007_EVIDENCE_MANIFEST_DRIFT",
    )
    for path in (
        "specs/007-domain-pure-ticket-scheduling/tasks.md",
        "specs/007-domain-pure-ticket-scheduling/runtime-tasks.md",
    ):
        require(
            not re.search(r"^- \[ \] ", tracked_text(path, FEATURE007_MERGE), re.MULTILINE),
            "FEATURE007_TASK_OPEN",
            path,
        )
    return {
        "evidence_artifact_count": evidence_count,
        "evidence_overlay": FEATURE007_OVERLAY,
        "merge_commit": FEATURE007_MERGE,
        "merge_parents": list(FEATURE007_PARENTS),
        "report": artifact(report_path, FEATURE007_MERGE),
        "report_sha256": FEATURE007_REPORT_SHA256,
        "source_artifact_count": source_count,
        "source_commit": FEATURE007_SOURCE,
        "status": "PASS",
    }


def verify_dependency_reports() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, expected in DEPENDENCY_REPORTS.items():
        path = expected["path"]
        raw = tracked_bytes(path, FEATURE007_MERGE)
        require(sha256_bytes(raw) == expected["sha256"], "DEPENDENCY_REPORT_HASH_DRIFT", name)
        document = json.loads(raw.decode())
        require(isinstance(document, dict), "DEPENDENCY_REPORT_INVALID", name)
        require(document.get("status") == "PASS", "DEPENDENCY_REPORT_NOT_PASS", name)
        require(document.get("classification") == "REFINEMENT_ONLY", "DEPENDENCY_CLASS_DRIFT", name)
        require(
            document.get("semantic_completeness_claimed") is False,
            "DEPENDENCY_CLAIM_DRIFT",
            name,
        )
        require(
            document.get("source", {}).get("commit") == expected["source"],
            "DEPENDENCY_SOURCE_DRIFT",
            name,
        )
        require(document.get("formal", {}).get("status") == "GO", "DEPENDENCY_FORMAL_NOT_GO", name)
        require(
            document.get("formal", {}).get("formal_semantics_id") == FORMAL_ID,
            "DEPENDENCY_FORMAL_ID_DRIFT",
            name,
        )
        result[name] = {
            "report": {"path": path, "sha256": expected["sha256"]},
            "source_commit": expected["source"],
            "status": "PASS",
        }
    return result


def verify_ticket_and_lease_identity() -> dict[str, Any]:
    path = "delta-protocol/fixtures/007/cross-language/golden-v1.json"
    document = json.loads(tracked_bytes(path, FEATURE007_SOURCE).decode())
    require(isinstance(document, dict), "FEATURE007_FIXTURE_INVALID")
    plan = document.get("plan")
    leases = document.get("ticket_leases")
    require(isinstance(plan, dict), "FEATURE007_PLAN_INVALID")
    require(plan.get("content_id") == FEATURE007_PLAN_ID, "FEATURE007_PLAN_ID_DRIFT")
    require(isinstance(leases, list) and leases, "FEATURE007_LEASES_INVALID")
    lease_ids: list[str] = []
    for lease in leases:
        require(isinstance(lease, dict), "FEATURE007_LEASE_INVALID")
        require(lease.get("value", {}).get("plan_id") == FEATURE007_PLAN_ID, "LEASE_PLAN_DRIFT")
        lease_id = lease.get("content_id")
        require(isinstance(lease_id, str), "FEATURE007_LEASE_ID_INVALID")
        lease_ids.append(lease_id)
    return {
        "fixture": artifact(path, FEATURE007_SOURCE),
        "lease_ids": lease_ids,
        "plan_id": FEATURE007_PLAN_ID,
        "status": "PASS",
    }


def load_feature007_preflight() -> Any:
    path = ROOT / "specs/007-domain-pure-ticket-scheduling/scripts/verify_preflight.py"
    spec = importlib.util.spec_from_file_location("feature007_preflight_dependency", path)
    require(spec is not None and spec.loader is not None, "FORMAL_HELPER_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_formal(source_commit: str) -> dict[str, Any]:
    result = load_feature007_preflight().verify_formal(source_commit)
    require(result.get("status") == "GO", "FORMAL_NOT_GO")
    refinement = tracked_text("formal/tla/DeltaReduceRefinement.tla", source_commit)
    missing = sorted(action for action in REQUIRED_ACTION_IDS if f'"{action}"' not in refinement)
    require(not missing, "FORMAL_ACTION_MISSING", ",".join(missing))
    failure = tracked_text("specs/000-formal-tla-spec/failure-semantics.md", source_commit)
    for marker in (
        "Every vote that can contribute to RoundConfigQC, ISC, EC, APC, ParameterShardQC",
        "Seed proposal bound to wrong/no ISC",
        "Aggregate assembly mixed view",
        "Crash after ApplyQC before current-pointer CAS",
        "complete production lifecycle and reach `APPLIED`",
    ):
        require(marker in failure, "FORMAL_FAILURE_RULE_MISSING", marker)
    proofs = tracked_text("specs/000-formal-tla-spec/proof-obligations.md", source_commit)
    for marker in ("PO-A3", "PO-C1", "PO-AP1", "PO-AP2", "PO-D1", "PO-R2"):
        require(marker in proofs, "FORMAL_PROOF_OBLIGATION_MISSING", marker)
    return {**result, "required_action_ids": sorted(REQUIRED_ACTION_IDS)}


def verify_architecture(source_commit: str) -> dict[str, Any]:
    changed = git_text("diff", "--name-only", FEATURE007_MERGE, source_commit).splitlines()
    production = [path for path in changed if path.startswith(PRODUCTION_PREFIXES)]
    require(not production, "PRODUCTION_SOURCE_BEFORE_PREFLIGHT", json.dumps(production))
    unexpected = [
        path
        for path in changed
        if not path.startswith("specs/008-certificates-and-consensus/")
        and path not in ALLOWED_PREFLIGHT_PATHS
    ]
    require(not unexpected, "UNEXPECTED_PREFLIGHT_PATH", json.dumps(unexpected))
    paths = (
        "specs/008-certificates-and-consensus/formal-refinement.md",
        "specs/008-certificates-and-consensus/plan.md",
        "specs/008-certificates-and-consensus/runtime-profile.md",
        "specs/008-certificates-and-consensus/spec.md",
        "specs/008-certificates-and-consensus/task-map.md",
        "specs/008-certificates-and-consensus/tasks.md",
    )
    combined = "\n".join(tracked_text(path, source_commit) for path in paths)
    for legacy in (
        "src/deltatorrent/certificates",
        "src/deltatorrent/robust",
        "src/deltatorrent/apply",
        "proto/deltareduce/certificates",
    ):
        require(legacy not in combined, "LEGACY_AUTHORITY_PATH", legacy)
    for marker in (
        "C++ alone",
        "Java",
        "Python",
        "pre-ISC randomness",
        "floating robust/apply",
        "immutable required domain\u00d7shard",
        "ApplyQC",
    ):
        require(marker in combined, "AUTHORITY_RULE_UNBOUND", marker)
    return {
        "changed_path_count": len(changed),
        "finding_count": 0,
        "findings": [],
        "production_source_count": 0,
        "status": "PASS",
        "zero_authority_paths": [
            "device_derived_consensus_weight",
            "floating_robust_or_apply",
            "java_certificate_or_apply_decision",
            "pre_isc_randomness",
            "python_validator_authority",
            "single_signer_current",
            "tolerance_based_assembly",
        ],
    }


def verify_formal_impact(source_commit: str) -> dict[str, Any]:
    diff = git_text(
        "diff",
        "--name-only",
        FEATURE007_MERGE,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not diff, "FORMAL_SOURCE_DIFF_PRESENT", diff)
    refinement = tracked_text(
        "specs/008-certificates-and-consensus/formal-refinement.md", source_commit
    )
    profile = tracked_text("specs/008-certificates-and-consensus/runtime-profile.md", source_commit)
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
            "FEATURE007_MERGE_SOURCE_EVIDENCE_EXACT",
            "FEATURE004_005_006_REPORT_IDENTITIES_BOUND",
            "FEATURE007_TICKET_PLAN_AND_LEASE_IDENTITIES_BOUND",
            "FORMAL_GO_AND_FULL_CHAIN_ACTIONS_REDERIVED",
            "FAILURE_RECOVERY_AND_PROOF_PRECONDITIONS_BOUND",
            "NO_FORMAL_SOURCE_DIFF",
            "ZERO_FORBIDDEN_AUTHORITY_PATHS",
            "REFINEMENT_ONLY_CLASSIFICATION",
            "PREFLIGHT_SOURCE_TREE_BOUND",
        ],
        "dependency_reports": verify_dependency_reports(),
        "errors": [],
        "feature007": verify_feature007(source_commit),
        "formal": verify_formal(source_commit),
        "formal_impact": verify_formal_impact(source_commit),
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": verify_source(source_commit),
        "status": "PASS",
        "task_ids": [f"T{index:03d}" for index in range(6)],
        "ticket_and_lease_identity": verify_ticket_and_lease_identity(),
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
