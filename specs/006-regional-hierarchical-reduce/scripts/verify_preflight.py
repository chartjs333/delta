"""Verify the exact feature-005, Formal and architecture boundary for feature 006."""

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
FEATURE = ROOT / "specs" / "006-regional-hierarchical-reduce"
OUTPUT = FEATURE / "evidence" / "preflight.json"

FEATURE005_MERGE = "1e884b4122898a8e0ff17254bc42414a8773830c"
FEATURE005_PARENTS = (
    "bd31efaa6d521bbfc3362ad9aac39455bd29a098",
    "be5d72305bfd883a5bd99607df6c2788014bfd0a",
)
FEATURE005_SOURCE = "01f200b193733a1b474ad755c5c0c739b3189a96"
FEATURE005_OVERLAY = FEATURE005_PARENTS[1]
FEATURE005_REPORT_SHA256 = "7f7f86ad5021107688277ab626b266a61c7e633eb5c401e44c7778b98733dad6"
FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FORMAL_SOURCE = "1e6e0f6f70056161d95933e71494ec390c7c1151"
FORMAL_REPORT_SHA256 = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"
LEAN_REPORT_SHA256 = "4e79a87aa6524049f544cb235255af3aa38630ab8f2427455884d1618999e329"

PROFILE_ID = "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"
SCALE_TABLE_ID = "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205"
SHARD_PLAN_ID = "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1"
CONFIG_ID = "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629"
PROOF_ID = "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076"
MANIFEST_ID = "sha256:d48ff2208becabd6b380503c2de6746dbbe4ec0c450fe67308a9a17d726fc254"
PIECE_PROFILE_ID = "sha256:de9ca7f1a4e2630f729227e34d51c0c03c565062cc9ba924e465a884acc7987d"
POLICY_REGISTRY_ID = "sha256:c0d1e26526a772498041c34a5c0c5735a4aec3d133e190635f01eb251203d64b"

PARTIAL_MEDIA_TYPES = {
    "application/vnd.deltareduce.parameter-partial;version=1",
    "application/vnd.deltareduce.regional-partial;version=1",
    "application/vnd.deltareduce.worker-q-shard;version=1",
}
THEOREM_CONJUNCTS = {
    "PO-A1": {"product-bound"},
    "PO-A2": {"flat-accumulator-bound"},
    "PO-A3": {
        "canonical-reduced-input",
        "input-denominator-divides-common",
        "numerator-accumulator-bound",
        "positive-common-denominator",
        "positive-input-denominator",
        "round-at-or-above-half",
        "round-below-half",
        "round-half-tie-toward-positive",
        "rounding-deterministic",
    },
    "PO-H1": {"exact-partition"},
    "PO-H2": {"hierarchy-equals-flat"},
}
SOURCE_ARTIFACTS = (
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
    "specs/006-regional-hierarchical-reduce/checklists/hybrid-runtime.md",
    "specs/006-regional-hierarchical-reduce/checklists/requirements.md",
    "specs/006-regional-hierarchical-reduce/formal-refinement.md",
    "specs/006-regional-hierarchical-reduce/plan.md",
    "specs/006-regional-hierarchical-reduce/runtime-profile.md",
    "specs/006-regional-hierarchical-reduce/runtime-tasks.md",
    "specs/006-regional-hierarchical-reduce/scripts/verify_preflight.py",
    "specs/006-regional-hierarchical-reduce/spec.md",
    "specs/006-regional-hierarchical-reduce/task-map.md",
    "specs/006-regional-hierarchical-reduce/tasks.md",
    "specs/006-regional-hierarchical-reduce/tests/test_verify_preflight.py",
)
PRODUCTION_PREFIXES = (
    "delta-core-cpp/",
    "delta-runtime-cpp/",
    "delta-ffi/",
    "delta-node-java/",
    "delta-worker-python/",
    "delta-protocol/",
)

ALLOWED_PREFLIGHT_PATHS = {".github/workflows/ci.yml", "Makefile", "specs/ROADMAP.md"}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes, derive_formal_semantics_id  # noqa: E402


class PreflightError(RuntimeError):
    """Stable fail-closed feature-006 preflight error."""


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


def validate_feature005_document(document: dict[str, Any]) -> None:
    require(document.get("status") == "PASS", "FEATURE005_STATUS_INVALID")
    require(document.get("classification") == "REFINEMENT_ONLY", "FEATURE005_CLASS_INVALID")
    require(document.get("semantic_completeness_claimed") is False, "FEATURE005_CLAIM_INVALID")
    source = document.get("source")
    formal = document.get("formal")
    identities = document.get("identities")
    phase = document.get("phase_evidence")
    require(isinstance(source, dict), "FEATURE005_SOURCE_INVALID")
    require(isinstance(formal, dict), "FEATURE005_FORMAL_INVALID")
    require(isinstance(identities, dict), "FEATURE005_IDENTITIES_INVALID")
    require(isinstance(phase, dict), "FEATURE005_PHASE_EVIDENCE_INVALID")
    require(source.get("commit") == FEATURE005_SOURCE, "FEATURE005_SOURCE_DRIFT")
    require(
        formal
        == {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "FEATURE005_FORMAL_DRIFT",
    )
    require(
        identities
        == {
            "manifest_id": MANIFEST_ID,
            "piece_profile_id": PIECE_PROFILE_ID,
            "policy_registry_id": POLICY_REGISTRY_ID,
        },
        "FEATURE005_IDENTITIES_DRIFT",
    )
    require(
        phase.get("source", {}).get("commit") == FEATURE005_SOURCE, "FEATURE005_PHASE_SOURCE_DRIFT"
    )
    require(phase.get("status") == "PASS", "FEATURE005_PHASE_STATUS_INVALID")


def verify_report_manifest(document: dict[str, Any], revision: str) -> int:
    entries = document.get("source", {}).get("artifacts", [])
    require(isinstance(entries, list) and entries, "FEATURE005_SOURCE_ARTIFACTS_INVALID")
    for entry in entries:
        require(isinstance(entry, dict), "FEATURE005_SOURCE_ARTIFACT_INVALID")
        path, expected = entry.get("path"), entry.get("sha256")
        require(
            isinstance(path, str) and isinstance(expected, str),
            "FEATURE005_SOURCE_ARTIFACT_INVALID",
        )
        require(
            sha256_bytes(tracked_bytes(path, revision)) == expected,
            "FEATURE005_SOURCE_ARTIFACT_DRIFT",
            path,
        )
    return len(entries)


def verify_feature005(source_commit: str) -> dict[str, Any]:
    parents = tuple(git_text("show", "-s", "--format=%P", FEATURE005_MERGE).split())
    require(parents == FEATURE005_PARENTS, "FEATURE005_MERGE_PARENTS_INVALID")
    require_ancestor(FEATURE005_SOURCE, FEATURE005_OVERLAY, "FEATURE005_SOURCE_CHAIN_INVALID")
    require_ancestor(FEATURE005_OVERLAY, FEATURE005_MERGE, "FEATURE005_OVERLAY_CHAIN_INVALID")
    require_ancestor(FEATURE005_MERGE, source_commit, "FEATURE005_MERGE_NOT_ANCESTOR")
    report_path = "specs/005-content-addressed-p2p-distribution/evidence/final-compatibility.json"
    report_raw = tracked_bytes(report_path, FEATURE005_MERGE)
    require(sha256_bytes(report_raw) == FEATURE005_REPORT_SHA256, "FEATURE005_REPORT_HASH_DRIFT")
    report = json.loads(report_raw.decode("utf-8"))
    require(isinstance(report, dict), "FEATURE005_REPORT_INVALID")
    validate_feature005_document(report)
    source_artifact_count = verify_report_manifest(report, FEATURE005_SOURCE)
    for entry in report.get("evidence_artifacts", []):
        path, expected = entry.get("path"), entry.get("sha256")
        require(
            isinstance(path, str) and isinstance(expected, str),
            "FEATURE005_EVIDENCE_ARTIFACT_INVALID",
        )
        require(
            sha256_bytes(tracked_bytes(path, FEATURE005_MERGE)) == expected,
            "FEATURE005_EVIDENCE_ARTIFACT_DRIFT",
            path,
        )
    golden = tracked_json(
        "delta-protocol/fixtures/005/cross-language/golden-v1.json", FEATURE005_MERGE
    )
    require(golden.get("manifest", {}).get("content_id") == MANIFEST_ID, "MANIFEST_ID_DRIFT")
    require(
        golden.get("piece_profile", {}).get("content_id") == PIECE_PROFILE_ID,
        "PIECE_PROFILE_ID_DRIFT",
    )
    policy = golden.get("policy_registry", {})
    require(policy.get("content_id") == POLICY_REGISTRY_ID, "POLICY_REGISTRY_ID_DRIFT")
    forbidden = set(policy.get("value", {}).get("forbidden_media_types", []))
    require(PARTIAL_MEDIA_TYPES <= forbidden, "PARTIAL_MEDIA_DENYLIST_DRIFT")
    for path in (
        "specs/005-content-addressed-p2p-distribution/tasks.md",
        "specs/005-content-addressed-p2p-distribution/runtime-tasks.md",
    ):
        require(
            not re.search(r"^- \[ \] ", tracked_text(path, FEATURE005_MERGE), re.MULTILINE),
            "FEATURE005_TASK_OPEN",
            path,
        )
    return {
        "evidence_overlay": FEATURE005_OVERLAY,
        "identities": {
            "manifest_id": MANIFEST_ID,
            "piece_profile_id": PIECE_PROFILE_ID,
            "policy_registry_id": POLICY_REGISTRY_ID,
        },
        "merge_commit": FEATURE005_MERGE,
        "merge_parents": list(FEATURE005_PARENTS),
        "partial_media_types": sorted(PARTIAL_MEDIA_TYPES),
        "report": artifact(report_path, FEATURE005_MERGE),
        "report_sha256": FEATURE005_REPORT_SHA256,
        "source_artifact_count": source_artifact_count,
        "source_commit": FEATURE005_SOURCE,
        "status": "PASS",
    }


def verify_feature004_arithmetic(source_commit: str) -> dict[str, Any]:
    golden = tracked_json(
        "delta-protocol/fixtures/004/cross-language/golden-v1.json", source_commit
    )
    exact = {
        "fixedpoint_config_id": golden.get("fixedpoint_config", {}).get("content_id"),
        "profile_id": golden.get("profile", {}).get("content_id"),
        "proof_instance_id": golden.get("proof_instance", {}).get("content_id"),
        "scale_table_id": golden.get("scale_table", {}).get("content_id"),
        "shard_plan_id": golden.get("shard_plan", {}).get("content_id"),
    }
    expected = {
        "fixedpoint_config_id": CONFIG_ID,
        "profile_id": PROFILE_ID,
        "proof_instance_id": PROOF_ID,
        "scale_table_id": SCALE_TABLE_ID,
        "shard_plan_id": SHARD_PLAN_ID,
    }
    require(exact == expected, "FEATURE004_ARITHMETIC_IDENTITIES_DRIFT")
    return {"identities": exact, "status": "PASS"}


def validate_required_theorems(
    formal_report: dict[str, Any], lean_report: dict[str, Any]
) -> list[dict[str, Any]]:
    formal_checks = {item.get("id"): item for item in formal_report.get("theorem_checks", [])}
    lean_checks = {item.get("id"): item for item in lean_report.get("theorems", [])}
    result: list[dict[str, Any]] = []
    for theorem_id, expected_conjuncts in THEOREM_CONJUNCTS.items():
        formal = formal_checks.get(theorem_id, {})
        lean = lean_checks.get(theorem_id, {})
        require(
            formal.get("mandatory") is True
            and formal.get("verified") is True
            and formal.get("status") == "PASS",
            "FORMAL_THEOREM_CHECK_INVALID",
            theorem_id,
        )
        conjuncts = lean.get("normative_conjuncts", [])
        actual = {item.get("conjunct") for item in conjuncts if isinstance(item, dict)}
        require(lean.get("status") == "PASS", "LEAN_THEOREM_INVALID", theorem_id)
        require(actual == expected_conjuncts, "LEAN_CONJUNCT_COVERAGE_DRIFT", theorem_id)
        require(
            all(item.get("status") == "PASS" for item in conjuncts),
            "LEAN_CONJUNCT_NOT_PASS",
            theorem_id,
        )
        source, source_hash = lean.get("source"), lean.get("source_sha256")
        require(
            isinstance(source, str) and isinstance(source_hash, str),
            "LEAN_SOURCE_INVALID",
            theorem_id,
        )
        require(
            sha256_bytes(tracked_bytes(source, FORMAL_SOURCE)) == source_hash,
            "LEAN_SOURCE_HASH_DRIFT",
            theorem_id,
        )
        require(
            all(
                item.get("proof_obligation_id") == theorem_id
                and item.get("source") == source
                and item.get("source_sha256") == source_hash
                for item in conjuncts
            ),
            "LEAN_CONJUNCT_EVIDENCE_INVALID",
            theorem_id,
        )
        result.append(
            {"conjuncts": sorted(actual), "id": theorem_id, "source": source, "status": "PASS"}
        )
    return result


def verify_formal(source_commit: str) -> dict[str, Any]:
    artifacts = formal_artifacts(source_commit)
    require(len(artifacts) == 24, "FORMAL_ARTIFACT_COUNT_INVALID")
    semantics = tracked_json("formal/reports/formal-semantics.json", source_commit)
    require(semantics.get("semantic_artifacts") == artifacts, "FORMAL_MANIFEST_DRIFT")
    require(derive_formal_semantics_id("1.0.0", artifacts) == FORMAL_ID, "FORMAL_ID_DRIFT")
    report_raw = tracked_bytes("formal/reports/formal-verification-report.json", source_commit)
    require(sha256_bytes(report_raw) == FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_DRIFT")
    report = json.loads(report_raw.decode("utf-8"))
    require(isinstance(report, dict), "FORMAL_REPORT_INVALID")
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == FORMAL_ID
        and report.get("source_tree", {}).get("commit") == FORMAL_SOURCE,
        "FORMAL_REPORT_NOT_EXACT_GO",
    )
    lean_raw = tracked_bytes("formal/reports/lean-proof-report.json", source_commit)
    require(sha256_bytes(lean_raw) == LEAN_REPORT_SHA256, "LEAN_REPORT_HASH_DRIFT")
    lean = json.loads(lean_raw.decode("utf-8"))
    require(isinstance(lean, dict), "LEAN_REPORT_INVALID")
    require(lean.get("status") == "PASS", "LEAN_REPORT_NOT_PASS")
    return {
        "artifact_count": len(artifacts),
        "formal_semantics_id": FORMAL_ID,
        "lean_report_sha256": LEAN_REPORT_SHA256,
        "report_sha256": FORMAL_REPORT_SHA256,
        "source_commit": FORMAL_SOURCE,
        "status": "GO",
        "theorem_checks": validate_required_theorems(report, lean),
    }


def verify_architecture(source_commit: str) -> dict[str, Any]:
    changed = git_text("diff", "--name-only", FEATURE005_MERGE, source_commit).splitlines()
    production = [path for path in changed if path.startswith(PRODUCTION_PREFIXES)]
    require(not production, "PRODUCTION_SOURCE_BEFORE_PREFLIGHT", json.dumps(production))
    unexpected = [
        path
        for path in changed
        if not path.startswith("specs/006-regional-hierarchical-reduce/")
        and path not in ALLOWED_PREFLIGHT_PATHS
    ]
    require(not unexpected, "UNEXPECTED_PREFLIGHT_PATH", json.dumps(unexpected))
    paths = (
        "specs/006-regional-hierarchical-reduce/formal-refinement.md",
        "specs/006-regional-hierarchical-reduce/plan.md",
        "specs/006-regional-hierarchical-reduce/runtime-profile.md",
        "specs/006-regional-hierarchical-reduce/spec.md",
    )
    combined = "\n".join(tracked_text(path, source_commit) for path in paths)
    require("src/deltatorrent/" not in combined, "LEGACY_PYTHON_AUTHORITY_PATH")
    require("authoritative C++" in combined, "NATIVE_HIERARCHY_AUTHORITY_UNBOUND")
    require(
        "Java cannot:" in combined and "average regional outputs" in combined,
        "JAVA_MATH_SHORTCUT_UNBOUND",
    )
    require("average-of-averages" in combined, "AVERAGE_OF_AVERAGES_RULE_UNBOUND")
    require("post-freeze" in combined or "Post-ISC" in combined, "POST_FREEZE_RULE_UNBOUND")
    require("never enter P2P publication" in combined, "PARTIAL_PUBLICATION_RULE_UNBOUND")
    require(
        "no central or average-of-available-regions fallback" in combined,
        "CENTRAL_FALLBACK_RULE_UNBOUND",
    )
    return {
        "changed_path_count": len(changed),
        "finding_count": 0,
        "findings": [],
        "production_source_count": 0,
        "status": "PASS",
        "zero_authority_paths": [
            "authoritative_float_reduce",
            "average_of_averages",
            "central_fallback",
            "partial_object_publication",
            "post_freeze_exclusion",
        ],
    }


def verify_formal_impact(source_commit: str) -> dict[str, Any]:
    diff = git_text(
        "diff",
        "--name-only",
        FEATURE005_MERGE,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not diff, "FORMAL_SOURCE_DIFF_PRESENT", diff)
    profile = tracked_text(
        "specs/006-regional-hierarchical-reduce/runtime-profile.md", source_commit
    )
    refinement = tracked_text(
        "specs/006-regional-hierarchical-reduce/formal-refinement.md", source_commit
    )
    plan = tracked_text("specs/006-regional-hierarchical-reduce/plan.md", source_commit)
    require("**Formal impact**: `REFINEMENT_ONLY`" in profile, "FORMAL_CLASS_INVALID")
    require(FORMAL_ID in plan, "FORMAL_ID_UNBOUND")
    for theorem_id in THEOREM_CONJUNCTS:
        require(
            theorem_id in refinement or theorem_id in plan,
            "THEOREM_PRECONDITION_UNBOUND",
            theorem_id,
        )
    require("Feature-008 boundary" in refinement, "FEATURE008_BOUNDARY_UNBOUND")
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
            "FEATURE005_MERGE_SOURCE_EVIDENCE_EXACT",
            "FEATURE005_TASKS_AND_SOURCE_MANIFEST_EXACT",
            "FEATURE004_ARITHMETIC_IDENTITIES_EXACT",
            "FORMAL_GO_AND_24_ARTIFACTS_REDERIVED",
            "PO_H1_H2_AND_PO_A1_A3_CONJUNCTS_EXACT",
            "PARTIAL_MEDIA_TYPES_DENIED",
            "NO_FORMAL_SOURCE_DIFF",
            "ZERO_FLOAT_AVERAGING_CENTRAL_MUTATION_PUBLICATION_PATHS",
            "REFINEMENT_ONLY_CLASSIFICATION",
            "PREFLIGHT_SOURCE_TREE_BOUND",
        ],
        "errors": [],
        "feature004_arithmetic": verify_feature004_arithmetic(source_commit),
        "feature005": verify_feature005(source_commit),
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
            not git_text("status", "--porcelain", "--untracked-files=all"), "SOURCE_TREE_NOT_CLEAN"
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
