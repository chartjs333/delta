"""Verify Campaign 02 Definition/attestation ordering before any execution authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.definition import BenchmarkDefinition  # noqa: E402
from deltatorrent.protocol.canonical import canonical_json_bytes  # noqa: E402

FORMAL_SEMANTICS_ID: Final = (
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
)
QUALIFIED_SOURCE: Final = "660710818a7a45708231ae03da78bac9bbc0abc9"
QUALIFIED_TREE: Final = "553f63928e13cf785798e8b1adfb53176e01629d"
REMEDIATION_MERGE: Final = "8e945ac9713de5898d3abdb10ad2474079a87260"

DEFINITION_PATH: Final = "configs/benchmark/campaign-02/definition-v1.json"
ATTESTATION_PATH: Final = "configs/benchmark/campaign-02/definition-attestation-v1.json"
METHODOLOGY_DIFF_PATH: Final = "reports/benchmark/campaigns/campaign-02/methodology-diff.json"
READINESS_PATH: Final = "reports/benchmark/campaigns/campaign-02/definition-readiness.json"
EXACT_EVIDENCE_PATH: Final = (
    "specs/010-wan-benchmark-and-quality/evidence/campaign-02-exact-source-qualification.json"
)
OUTPUT_PATH: Final = (
    ROOT / "specs/010-wan-benchmark-and-quality/evidence/"
    "campaign-02-definition-temporal-integrity.json"
)
OUTPUT_REPOSITORY_PATH: Final = (
    "specs/010-wan-benchmark-and-quality/evidence/campaign-02-definition-temporal-integrity.json"
)
VERIFIER_PATH: Final = (
    "specs/010-wan-benchmark-and-quality/scripts/verify_campaign02_definition_temporal.py"
)
POST_ATTESTATION_ALLOWED_EXACT: Final = {
    ".github/workflows/benchmark-campaign02-definition.yml",
    "reports/benchmark/campaigns/campaign-02/definition-readiness.json",
    "reports/benchmark/campaigns/campaign-02/methodology-diff.json",
    "specs/010-wan-benchmark-and-quality/campaign-02-tasks.md",
    OUTPUT_REPOSITORY_PATH,
    VERIFIER_PATH,
    "specs/010-wan-benchmark-and-quality/tests/test_campaign02_definition_temporal.py",
}
POST_ATTESTATION_ALLOWED_PREFIXES: Final = (
    "configs/benchmark/campaign-02/benchmark-review-validator-set-",
    "reports/benchmark/campaigns/campaign-02/definition-supersession-",
    "reports/benchmark/campaigns/campaign-02/definition-votes/",
)


class TemporalIntegrityError(RuntimeError):
    """Stable fail-closed temporal-integrity error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise TemporalIntegrityError(code)


def git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def tracked_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def tracked_json(commit: str, path: str) -> dict[str, object]:
    value = json.loads(tracked_bytes(commit, path))
    require(isinstance(value, dict), f"TRACKED_JSON_INVALID:{path}")
    return value


def object_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def tracked_id(commit: str, path: str) -> str:
    return "sha256:" + hashlib.sha256(tracked_bytes(commit, path)).hexdigest()


def first_commit(path: str, head: str) -> str:
    values = [
        value
        for value in git("log", "--diff-filter=A", "--format=%H", head, "--", path).splitlines()
        if value
    ]
    require(len(values) == 1, f"ARTIFACT_CREATION_COMMIT_NOT_EXACT:{path}")
    return values[0]


def is_ancestor(ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", ancestor, descendant),
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def campaign_paths(commit: str) -> list[str]:
    output = git(
        "ls-tree",
        "-r",
        "--name-only",
        commit,
        "--",
        "reports/benchmark/campaigns/campaign-02",
    )
    return sorted(value for value in output.splitlines() if value)


def prohibited_counts(paths: list[str]) -> dict[str, int]:
    prefix = "reports/benchmark/campaigns/campaign-02/"
    relative = [path.removeprefix(prefix).lower() for path in paths]
    return {
        "benchmark_result_qc": sum(
            name == "benchmark-result-qc.json" or name.startswith("result-qc/") for name in relative
        ),
        "execution_authorizations": sum(
            name == "execution-authorization.json" or name.startswith("authorizations/")
            for name in relative
        ),
        "primary_observations": sum(name.startswith("observations/") for name in relative),
        "real_wan_observations": sum(name.startswith("real-wan/") for name in relative),
        "scientific_observations": sum(name.startswith("stage-b/") for name in relative),
        "stage_a_receipts": sum(name.startswith("stage-a/") for name in relative),
        "stage_c_observations": sum(name.startswith("stage-c/") for name in relative),
    }


def allowed_post_attestation_path(path: str) -> bool:
    return path in POST_ATTESTATION_ALLOWED_EXACT or path.startswith(
        POST_ATTESTATION_ALLOWED_PREFIXES
    )


def post_attestation_commits(attestation_commit: str, actual_head: str) -> list[dict[str, object]]:
    commits = [
        value
        for value in git(
            "rev-list", "--reverse", f"{attestation_commit}..{actual_head}"
        ).splitlines()
        if value
    ]
    values: list[dict[str, object]] = []
    for commit in commits:
        paths = sorted(
            value
            for value in git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", commit
            ).splitlines()
            if value
        )
        require(bool(paths), f"POST_ATTESTATION_COMMIT_PATHS_EMPTY:{commit}")
        require(
            all(allowed_post_attestation_path(path) for path in paths),
            f"POST_ATTESTATION_PATH_FORBIDDEN:{commit}",
        )
        values.append(
            {
                "commit": commit,
                "paths": paths,
                "tree": git("show", "-s", "--format=%T", commit),
            }
        )
    return values


def build(verified_head: str) -> dict[str, object]:
    require(git("cat-file", "-t", verified_head) == "commit", "VERIFIED_HEAD_INVALID")
    definition_commit = first_commit(DEFINITION_PATH, verified_head)
    attestation_commit = first_commit(ATTESTATION_PATH, verified_head)
    verifier_commit = first_commit(VERIFIER_PATH, verified_head)
    require(definition_commit != attestation_commit, "DEFINITION_AND_ATTESTATION_NOT_SEPARATE")
    require(
        is_ancestor(REMEDIATION_MERGE, definition_commit),
        "DEFINITION_NOT_AFTER_REMEDIATION_MERGE",
    )
    require(
        is_ancestor(definition_commit, attestation_commit),
        "ATTESTATION_NOT_AFTER_DEFINITION",
    )
    require(
        is_ancestor(attestation_commit, verifier_commit),
        "VERIFIER_NOT_AFTER_ATTESTATION",
    )
    require(is_ancestor(verifier_commit, verified_head), "VERIFIER_NOT_IN_VERIFIED_HEAD")

    definition_value = tracked_json(verified_head, DEFINITION_PATH)
    definition = BenchmarkDefinition.from_dict(definition_value)
    attestation = tracked_json(verified_head, ATTESTATION_PATH)
    diff = tracked_json(verified_head, METHODOLOGY_DIFF_PATH)
    readiness = tracked_json(verified_head, READINESS_PATH)
    exact = tracked_json(verified_head, EXACT_EVIDENCE_PATH)
    require(
        attestation.get("benchmark_definition_id") == definition.content_id,
        "ATTESTATION_DEFINITION_MISMATCH",
    )
    require(
        readiness.get("definition_id") == definition.content_id
        and readiness.get("definition_attestation_id") == object_id(attestation)
        and readiness.get("methodology_diff_id") == object_id(diff),
        "READINESS_IDENTITY_MISMATCH",
    )
    require(
        readiness.get("definition_created_commit") == definition_commit,
        "READINESS_DEFINITION_COMMIT_MISMATCH",
    )
    require(
        definition.source_commit == QUALIFIED_SOURCE and definition.source_tree == QUALIFIED_TREE,
        "DEFINITION_QUALIFIED_SOURCE_MISMATCH",
    )
    authorization = readiness.get("authorization")
    require(isinstance(authorization, dict), "READINESS_AUTHORIZATION_MISSING")
    require(
        authorization
        == {
            "feature_011_authorized": False,
            "primary_execution_authorized": False,
            "real_wan_authorized": False,
            "result_qc_authorized": False,
            "stage_a_authorized": False,
            "stage_b_authorized": False,
            "stage_c_authorized": False,
        },
        "EXECUTION_AUTHORIZATION_NOT_FALSE",
    )
    require(
        readiness.get("c2_016_status") == "OPEN_REQUIRES_SEPARATE_GOVERNANCE_DECISION",
        "C2_016_NOT_OPEN",
    )
    execution_plan = readiness.get("execution_plan")
    require(
        isinstance(execution_plan, dict) and execution_plan.get("execution_allowed") is False,
        "EXECUTION_PLAN_ALREADY_ALLOWED",
    )
    require(
        exact.get("primary_scientific_execution_count") == 0
        and exact.get("scientific_observations_created") is False,
        "QUALIFICATION_ALREADY_CONTAINS_OBSERVATION",
    )

    counts = prohibited_counts(campaign_paths(verified_head))
    require(all(value == 0 for value in counts.values()), "PREAUTHORIZATION_ARTIFACT_PRESENT")
    return {
        "authorization": authorization,
        "benchmark_result_qc": "ABSENT",
        "c2_016_status": "OPEN_REQUIRES_SEPARATE_GOVERNANCE_DECISION",
        "checks": [
            "DEFINITION_CREATED_AFTER_REMEDIATION_MERGE_PASS",
            "DEFINITION_CREATED_BEFORE_ATTESTATION_PASS",
            "ATTESTATION_FINALIZED_BEFORE_EXECUTION_AUTHORIZATION_PASS",
            "NO_PRIMARY_OBSERVATION_BEFORE_ATTESTATION_PASS",
            "NO_STAGE_A_RECEIPT_BEFORE_ATTESTATION_PASS",
            "NO_SCIENTIFIC_OBSERVATION_PASS",
            "NO_REAL_WAN_OBSERVATION_PASS",
            "NO_BENCHMARK_RESULT_QC_PASS",
            "C2_016_REMAINS_OPEN_PASS",
        ],
        "definition_attestation_finalized_commit": attestation_commit,
        "definition_attestation_id": object_id(attestation),
        "definition_created_commit": definition_commit,
        "definition_id": definition.content_id,
        "execution_authorization": "ABSENT",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "methodology_diff_id": object_id(diff),
        "observation_counts": counts,
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "remediation_merge_commit": REMEDIATION_MERGE,
        "schema_version": "1.0.0",
        "status": "PASS_AWAITING_SEPARATE_C2_016_GOVERNANCE",
        "type_name": "CAMPAIGN02_DEFINITION_TEMPORAL_INTEGRITY",
        "verified_head": verified_head,
        "verifier_commit": verifier_commit,
        "verifier_source_id": tracked_id(verifier_commit, VERIFIER_PATH),
    }


def verify_checked_in_snapshot() -> dict[str, object]:
    require(OUTPUT_PATH.is_file(), "TEMPORAL_EVIDENCE_MISSING")
    raw = OUTPUT_PATH.read_bytes()
    current = json.loads(raw)
    require(isinstance(current, dict), "TEMPORAL_EVIDENCE_INVALID")
    require(raw == canonical_json_bytes(current) + b"\n", "TEMPORAL_EVIDENCE_NONCANONICAL")
    value = build(str(current.get("verified_head")))
    require(raw == canonical_json_bytes(value) + b"\n", "TEMPORAL_EVIDENCE_DRIFT")
    return value


def build_terminal_receipt(actual_head: str, workflow_run_id: str) -> dict[str, object]:
    require(git("cat-file", "-t", actual_head) == "commit", "ACTUAL_HEAD_INVALID")
    require(git("rev-parse", "HEAD") == actual_head, "ACTUAL_HEAD_NOT_CHECKED_OUT")
    require(bool(workflow_run_id.strip()), "WORKFLOW_RUN_ID_REQUIRED")
    snapshot = tracked_json(actual_head, OUTPUT_REPOSITORY_PATH)
    snapshot_raw = tracked_bytes(actual_head, OUTPUT_REPOSITORY_PATH)
    require(
        snapshot_raw == canonical_json_bytes(snapshot) + b"\n",
        "TEMPORAL_SNAPSHOT_NONCANONICAL",
    )
    snapshot_head = str(snapshot.get("verified_head"))
    expected_snapshot = build(snapshot_head)
    require(
        snapshot_raw == canonical_json_bytes(expected_snapshot) + b"\n",
        "TEMPORAL_SNAPSHOT_DRIFT",
    )
    require(is_ancestor(snapshot_head, actual_head), "SNAPSHOT_NOT_IN_ACTUAL_HEAD")
    attestation_commit = first_commit(ATTESTATION_PATH, actual_head)
    require(
        attestation_commit == snapshot.get("definition_attestation_finalized_commit")
        and is_ancestor(attestation_commit, actual_head),
        "ATTESTATION_NOT_IN_ACTUAL_HEAD",
    )
    commits = post_attestation_commits(attestation_commit, actual_head)
    counts = prohibited_counts(campaign_paths(actual_head))
    require(all(value == 0 for value in counts.values()), "TERMINAL_HEAD_ARTIFACT_PRESENT")
    authorization = snapshot.get("authorization")
    require(
        isinstance(authorization, dict)
        and authorization
        and all(value is False for value in authorization.values()),
        "TERMINAL_HEAD_AUTHORIZATION_INVALID",
    )
    return {
        "actual_head": actual_head,
        "actual_tree": git("show", "-s", "--format=%T", actual_head),
        "allowed_post_attestation_commits": commits,
        "attestation_commit": attestation_commit,
        "authorization": authorization,
        "benchmark_result_qc": "ABSENT",
        "checks": [
            "EXPLICIT_ACTUAL_TERMINAL_HEAD_PASS",
            "CHECKED_IN_TEMPORAL_SNAPSHOT_REPRODUCED_PASS",
            "ATTESTATION_ANCESTOR_OF_TERMINAL_HEAD_PASS",
            "POST_ATTESTATION_PATH_ALLOWLIST_PASS",
            "NO_TERMINAL_HEAD_EXECUTION_ARTIFACT_PASS",
            "NO_TERMINAL_HEAD_AUTHORIZATION_PASS",
        ],
        "definition_attestation_id": snapshot["definition_attestation_id"],
        "definition_id": snapshot["definition_id"],
        "execution_authorization": "ABSENT",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "primary_execution_authorized": False,
        "prohibited_artifact_counts": counts,
        "schema_version": "1.0.0",
        "snapshot_id": tracked_id(actual_head, OUTPUT_REPOSITORY_PATH),
        "snapshot_verified_head": snapshot_head,
        "status": "PASS_TERMINAL_HEAD_NO_EXECUTION",
        "terminal_head_verifier_id": tracked_id(actual_head, VERIFIER_PATH),
        "type_name": "CAMPAIGN02_DEFINITION_TERMINAL_HEAD_RECEIPT",
        "workflow_run_id": workflow_run_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verified-head")
    parser.add_argument("--terminal-receipt-output", type=Path)
    parser.add_argument("--workflow-run-id")
    arguments = parser.parse_args()
    if arguments.terminal_receipt_output is not None:
        require(isinstance(arguments.verified_head, str), "VERIFIED_HEAD_REQUIRED")
        require(isinstance(arguments.workflow_run_id, str), "WORKFLOW_RUN_ID_REQUIRED")
        value = build_terminal_receipt(arguments.verified_head, arguments.workflow_run_id)
        arguments.terminal_receipt_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.terminal_receipt_output.write_bytes(canonical_json_bytes(value) + b"\n")
    elif arguments.write:
        require(isinstance(arguments.verified_head, str), "VERIFIED_HEAD_REQUIRED")
        value = build(arguments.verified_head)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_bytes(canonical_json_bytes(value) + b"\n")
    else:
        value = verify_checked_in_snapshot()
    print(
        json.dumps(
            {
                "c2_016_status": value.get("c2_016_status", "NOT_AUTHORIZED"),
                "definition_id": value["definition_id"],
                "primary_execution_authorized": False,
                "status": value["status"],
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
