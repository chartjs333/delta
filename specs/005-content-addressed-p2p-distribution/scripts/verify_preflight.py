"""Verify the exact feature-004, Formal and architecture boundary for feature 005."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "005-content-addressed-p2p-distribution"
OUTPUT = FEATURE / "evidence" / "preflight.json"

FEATURE004_MERGE = "bd31efaa6d521bbfc3362ad9aac39455bd29a098"
FEATURE004_PARENTS = (
    "53da4d3c0b236726566fb242fdcae84032b42679",
    "29fb4138499a348f90d6bbc44e77fe6d1914e25f",
)
FEATURE004_SOURCE = "22dd996b5d169763bfde49f32c1b1b18f2656493"
FEATURE004_OVERLAY = FEATURE004_PARENTS[1]
FEATURE004_REPORT_SHA256 = "9dbd9c7bda30d6ebe9b70f33a1a16d49a2b837b140d24f87becd433f05e3dccb"
FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FORMAL_SOURCE = "1e6e0f6f70056161d95933e71494ec390c7c1151"
FORMAL_REPORT_SHA256 = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"

PROFILE_ID = "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"
SCALE_TABLE_ID = "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205"
SHARD_PLAN_ID = "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1"
CONFIG_ID = "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629"
PROOF_ID = "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076"
COMMITMENT_ROOT = "sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d"

EXPECTED_ARTIFACT_HASHES = {
    "delta-protocol/fixtures/004/golden-hashes-v1.json": (
        "9bc8fff848b2c721b7d60ef8c6912243668fde23c92cb3231754573ff60c8980"
    ),
    "delta-protocol/registry.json": (
        "898553cc20183660ae0a8c5be2cc1b4cffb554a411736b75ceb465973871771f"
    ),
    "delta-protocol/schemas/003/delta-abi-v1.json": (
        "3e19d745f2d702f0e77bd32f6c83fd50763237ecc505d735a0a68364f9a67f64"
    ),
    "delta-protocol/schemas/004/registry-v1.json": (
        "7046f9430be23b06b18b977cc3e47648cdd3cdb859a741f6826aecbff92d05f5"
    ),
}

SOURCE_ARTIFACTS = (
    ".specify/memory/constitution.md",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "specs/ROADMAP.md",
    "specs/005-content-addressed-p2p-distribution/checklists/hybrid-runtime.md",
    "specs/005-content-addressed-p2p-distribution/checklists/requirements.md",
    "specs/005-content-addressed-p2p-distribution/formal-refinement.md",
    "specs/005-content-addressed-p2p-distribution/plan.md",
    "specs/005-content-addressed-p2p-distribution/runtime-profile.md",
    "specs/005-content-addressed-p2p-distribution/runtime-tasks.md",
    "specs/005-content-addressed-p2p-distribution/scripts/verify_preflight.py",
    "specs/005-content-addressed-p2p-distribution/spec.md",
    "specs/005-content-addressed-p2p-distribution/task-map.md",
    "specs/005-content-addressed-p2p-distribution/tasks.md",
    "specs/005-content-addressed-p2p-distribution/tests/test_verify_preflight.py",
)

PRODUCTION_PREFIXES = (
    "delta-protocol/schemas/005/",
    "delta-protocol/fixtures/005/",
    "delta-core-cpp/include/delta/distribution/",
    "delta-core-cpp/src/distribution/",
    "delta-ffi/src/distribution_abi.cpp",
    "delta-node-java/src/main/java/io/deltareduce/node/distribution/",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes, derive_formal_semantics_id  # noqa: E402


class PreflightError(RuntimeError):
    """Stable fail-closed feature-005 preflight error."""


def reject(code: str, detail: str = "") -> NoReturn:
    raise PreflightError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    return git_bytes("show", f"{revision}:{path}")


def tracked_text(path: str, revision: str) -> str:
    return tracked_bytes(path, revision).decode("utf-8")


def tracked_json(path: str, revision: str) -> dict[str, Any]:
    value = json.loads(tracked_text(path, revision))
    require(isinstance(value, dict), "JSON_ROOT_INVALID", path)
    return value


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


def formal_artifacts(revision: str) -> list[dict[str, str]]:
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
    result: list[dict[str, str]] = []
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
            result.append(
                {"kind": kind, "path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}
            )
    return sorted(result, key=lambda item: (item["path"], item["kind"]))


def validate_feature004_document(document: dict[str, Any]) -> None:
    require(document.get("status") == "PASS", "FEATURE004_STATUS_INVALID")
    require(document.get("classification") == "REFINEMENT_ONLY", "FEATURE004_CLASS_INVALID")
    require(document.get("semantic_completeness_claimed") is False, "FEATURE004_CLAIM_INVALID")
    source = document.get("source")
    formal = document.get("formal")
    identities = document.get("identities")
    require(isinstance(source, dict), "FEATURE004_SOURCE_INVALID")
    require(isinstance(formal, dict), "FEATURE004_FORMAL_INVALID")
    require(isinstance(identities, dict), "FEATURE004_IDENTITIES_INVALID")
    require(source.get("commit") == FEATURE004_SOURCE, "FEATURE004_SOURCE_DRIFT")
    require(
        formal
        == {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "FEATURE004_FORMAL_DRIFT",
    )
    require(
        identities
        == {
            "commitment_root": COMMITMENT_ROOT,
            "fixedpoint_config_id": CONFIG_ID,
            "profile_id": PROFILE_ID,
            "proof_instance_id": PROOF_ID,
        },
        "FEATURE004_IDENTITIES_DRIFT",
    )


def verify_feature004(source_commit: str) -> dict[str, Any]:
    parents = tuple(git_text("show", "-s", "--format=%P", FEATURE004_MERGE).split())
    require(parents == FEATURE004_PARENTS, "FEATURE004_MERGE_PARENTS_INVALID")
    require_ancestor(FEATURE004_SOURCE, FEATURE004_OVERLAY, "FEATURE004_SOURCE_CHAIN_INVALID")
    require_ancestor(FEATURE004_OVERLAY, FEATURE004_MERGE, "FEATURE004_OVERLAY_CHAIN_INVALID")
    require_ancestor(FEATURE004_MERGE, source_commit, "FEATURE004_MERGE_NOT_ANCESTOR")

    report_path = "specs/004-compressed-delta-protocol/evidence/final-compatibility.json"
    report_raw = tracked_bytes(report_path, FEATURE004_MERGE)
    require(
        sha256_bytes(report_raw) == FEATURE004_REPORT_SHA256,
        "FEATURE004_REPORT_HASH_DRIFT",
    )
    report = json.loads(report_raw.decode("utf-8"))
    require(isinstance(report, dict), "FEATURE004_REPORT_INVALID")
    validate_feature004_document(report)

    golden = tracked_json(
        "delta-protocol/fixtures/004/cross-language/golden-v1.json", FEATURE004_MERGE
    )
    require(golden.get("profile", {}).get("content_id") == PROFILE_ID, "PROFILE_ID_DRIFT")
    require(golden.get("scale_table", {}).get("content_id") == SCALE_TABLE_ID, "SCALE_ID_DRIFT")
    require(golden.get("shard_plan", {}).get("content_id") == SHARD_PLAN_ID, "SHARD_PLAN_ID_DRIFT")
    require(golden.get("fixedpoint_config", {}).get("content_id") == CONFIG_ID, "CONFIG_ID_DRIFT")
    require(golden.get("proof_instance", {}).get("content_id") == PROOF_ID, "PROOF_ID_DRIFT")
    require(
        golden.get("manifest", {}).get("value", {}).get("commitment_root") == COMMITMENT_ROOT,
        "COMMITMENT_ROOT_DRIFT",
    )

    for path, expected in EXPECTED_ARTIFACT_HASHES.items():
        require(
            sha256_bytes(tracked_bytes(path, FEATURE004_MERGE)) == expected,
            "FEATURE004_ARTIFACT_HASH_DRIFT",
            path,
        )
    for path in (
        "specs/004-compressed-delta-protocol/tasks.md",
        "specs/004-compressed-delta-protocol/runtime-tasks.md",
    ):
        require(
            not re.search(r"^- \[ \] ", tracked_text(path, FEATURE004_MERGE), re.MULTILINE),
            "FEATURE004_TASK_OPEN",
            path,
        )
    return {
        "artifacts": [artifact(report_path, FEATURE004_MERGE)]
        + [artifact(path, FEATURE004_MERGE) for path in sorted(EXPECTED_ARTIFACT_HASHES)],
        "evidence_overlay": FEATURE004_OVERLAY,
        "identities": {
            "commitment_root": COMMITMENT_ROOT,
            "fixedpoint_config_id": CONFIG_ID,
            "profile_id": PROFILE_ID,
            "proof_instance_id": PROOF_ID,
            "scale_table_id": SCALE_TABLE_ID,
            "shard_plan_id": SHARD_PLAN_ID,
        },
        "merge_commit": FEATURE004_MERGE,
        "merge_parents": list(FEATURE004_PARENTS),
        "report_sha256": FEATURE004_REPORT_SHA256,
        "source_commit": FEATURE004_SOURCE,
        "status": "PASS",
    }


def verify_formal(source_commit: str) -> dict[str, Any]:
    artifacts = formal_artifacts(source_commit)
    require(len(artifacts) == 24, "FORMAL_ARTIFACT_COUNT_INVALID")
    semantics = tracked_json("formal/reports/formal-semantics.json", source_commit)
    require(semantics.get("semantic_artifacts") == artifacts, "FORMAL_MANIFEST_DRIFT")
    require(derive_formal_semantics_id("1.0.0", artifacts) == FORMAL_ID, "FORMAL_ID_DRIFT")
    report_raw = tracked_bytes("formal/reports/formal-verification-report.json", source_commit)
    require(sha256_bytes(report_raw) == FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_DRIFT")
    report = json.loads(report_raw.decode("utf-8"))
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == FORMAL_ID
        and report.get("source_tree", {}).get("commit") == FORMAL_SOURCE,
        "FORMAL_REPORT_NOT_EXACT_GO",
    )
    reduce_apply = tracked_text("formal/tla/DeltaReduceReduceApply.tla", source_commit)
    availability = tracked_text("formal/tla/DeltaReduceAvailability.tla", source_commit)
    refinement = tracked_text("formal/tla/DeltaReduceRefinement.tla", source_commit)
    for marker in (
        "PublishCertifiedObject(object)",
        "PlaneSeparation ==",
        "CertifiedPublishOnly ==",
    ):
        require(marker in reduce_apply, "FORMAL_PUBLICATION_MARKER_MISSING", marker)
    for marker in (
        "RepairArtifact(source, target, content, shard)",
        "RepairPreservesCertifiedLineage ==",
    ):
        require(marker in availability, "FORMAL_REPAIR_MARKER_MISSING", marker)
    require('actionId = "ACT-PUBLISH"' in refinement, "FORMAL_PUBLISH_ACTION_UNBOUND")
    require('actionId = "ACT-ARTIFACT-REPAIR"' in refinement, "FORMAL_REPAIR_ACTION_UNBOUND")
    return {
        "artifact_count": len(artifacts),
        "formal_semantics_id": FORMAL_ID,
        "refined_actions": ["ACT-ARTIFACT-REPAIR", "ACT-PUBLISH"],
        "report_sha256": FORMAL_REPORT_SHA256,
        "source_commit": FORMAL_SOURCE,
        "status": "GO",
    }


def verify_architecture(source_commit: str) -> dict[str, Any]:
    changed = git_text("diff", "--name-only", FEATURE004_MERGE, source_commit).splitlines()
    findings = [
        {"id": "PRODUCTION_SOURCE_BEFORE_PREFLIGHT", "path": path}
        for path in changed
        if path.startswith(PRODUCTION_PREFIXES)
    ]
    docs = "\n".join(
        tracked_text(path, source_commit)
        for path in git_text(
            "ls-tree",
            "-r",
            "--name-only",
            source_commit,
            "--",
            "specs/005-content-addressed-p2p-distribution",
        ).splitlines()
        if path.endswith(".md")
    )
    forbidden = {
        "LEGACY_PYTHON_DISTRIBUTION": r"src/deltatorrent/distribution/",
        "LEGACY_PYTHON_STORAGE": r"src/deltatorrent/adapters/storage/",
        "FEATURE008_CERTIFICATE_TRANSPORT_CLAIM": (
            r"implements feature-008 consensus/certificate transport"
        ),
    }
    for identifier, pattern in forbidden.items():
        if re.search(pattern, docs, re.IGNORECASE):
            findings.append(
                {"id": identifier, "path": "specs/005-content-addressed-p2p-distribution"}
            )
    require("Native C++ validates" in docs, "NATIVE_POLICY_AUTHORITY_UNBOUND")
    require("Java cannot construct an allow decision" in docs, "JAVA_POLICY_SHORTCUT_UNBOUND")
    require("Worker q shards" in docs and "parameter partials" in docs, "MEDIA_DENYLIST_UNBOUND")
    require(not findings, "ARCHITECTURE_FINDINGS_PRESENT", json.dumps(findings, sort_keys=True))
    return {
        "changed_path_count": len(changed),
        "finding_count": 0,
        "findings": [],
        "production_source_count": 0,
        "rules": sorted(forbidden),
        "status": "PASS",
    }


def verify_formal_impact(source_commit: str) -> dict[str, Any]:
    diff = git_text(
        "diff",
        "--name-only",
        FEATURE004_MERGE,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not diff, "FORMAL_SOURCE_DIFF_PRESENT", diff)
    profile = tracked_text(
        "specs/005-content-addressed-p2p-distribution/runtime-profile.md", source_commit
    )
    plan = tracked_text("specs/005-content-addressed-p2p-distribution/plan.md", source_commit)
    refinement = tracked_text(
        "specs/005-content-addressed-p2p-distribution/formal-refinement.md", source_commit
    )
    require("**Formal impact**: `REFINEMENT_ONLY`" in profile, "FORMAL_CLASS_INVALID")
    require(FORMAL_ID in plan, "FORMAL_ID_UNBOUND")
    require("PublishCertifiedObject" in plan and "Repair" in refinement, "REFINEMENT_SCOPE_UNBOUND")
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
            "FEATURE004_MERGE_SOURCE_EVIDENCE_EXACT",
            "FEATURE004_TASKS_PROTOCOL_IDENTITIES_EXACT",
            "FORMAL_GO_AND_24_ARTIFACTS_REDERIVED",
            "PUBLISH_REPAIR_PLANE_SEPARATION_BOUND",
            "NO_FORMAL_SOURCE_DIFF",
            "ZERO_JAVA_POLICY_OR_LOCAL_PARTIAL_AUTHORITY_PATHS",
            "REFINEMENT_ONLY_CLASSIFICATION",
            "RECONCILED_SOURCE_TREE_BOUND",
        ],
        "errors": [],
        "feature004": verify_feature004(source_commit),
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
    except (PreflightError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(
            canonical_json_bytes(
                {
                    "error_code": str(exc),
                    "formal_semantics_id": FORMAL_ID,
                    "schema_version": "1.0.0",
                    "status": "FAIL",
                }
            ).decode("utf-8")
        )
        return 2
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
