"""Emit the exact-source primary-executor CI qualification artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.definition import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    BenchmarkDefinition,
)
from deltatorrent.protocol.canonical import canonical_json_bytes  # noqa: E402

DEFINITION: Final = ROOT / "configs/benchmark/primary.yaml"
ATTESTATION: Final = ROOT / "configs/benchmark/primary-definition-attestation.json"
SUPERSESSION: Final = ROOT / "configs/benchmark/primary-definition-supersession.json"
FORMAL_REGRESSION: Final = (
    ROOT / "specs/010-wan-benchmark-and-quality/evidence/formal-regression.json"
)
PRODUCTION_ATTACKS: Final = (
    ROOT / "specs/010-wan-benchmark-and-quality/evidence/production-attacks.json"
)
ARCHITECTURE_GUARD: Final = (
    ROOT / "specs/010-wan-benchmark-and-quality/evidence/architecture-guard.json"
)
DEFAULT_OUTPUT: Final = (
    ROOT / "specs/010-wan-benchmark-and-quality/evidence/primary-executor-ci-qualification.json"
)
ALLOWED_DEFINITION_DIFFS: Final = frozenset({"sbom_id", "source_commit", "source_tree"})
SCIENTIFIC_FIELDS: Final = (
    "B",
    "H",
    "arm_ids",
    "base_model_id",
    "dataset_manifest_id",
    "decision_function",
    "domain_manifest_id",
    "evaluation_ids",
    "exclusions",
    "fault_profile_ids",
    "metric_definitions",
    "missing_run_policy",
    "model_mode",
    "network_profile_ids",
    "pi_d",
    "repetitions",
    "seeds",
    "ticket_plan_id",
    "tokenizer_id",
)
REQUIRED_CHECKS: Final = frozenset(
    {
        "architecture_guard",
        "cli_round_trip",
        "create_only_concurrency",
        "executor_negative_matrix",
        "formal_regression",
        "format",
        "mypy",
        "production_attacks",
        "pytest",
        "ruff",
    }
)
ALLOWED_OVERLAY_PATHS: Final = frozenset(
    {
        "configs/benchmark/primary-definition-attestation.json",
        "configs/benchmark/primary-definition-supersession.json",
        "configs/benchmark/primary.yaml",
        "configs/benchmark/sbom-v1.json",
        "reports/benchmark/phase-010-readiness.json",
        "specs/010-wan-benchmark-and-quality/evidence/architecture-guard.json",
        "specs/010-wan-benchmark-and-quality/scripts/verify_primary_executor_ci.py",
    }
)
ALLOWED_SKIPS: Final = frozenset(
    {
        "test_frozen_physical_profile_matches_designated_gpu",
        "test_complete_physical_ticket",
        "test_cuda_half_parameters_project_to_fp32_local_delta_reference",
    }
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def canonical_document(path: Path, *, allow_trailing_newline: bool = False) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    canonical = canonical_json_bytes(value)
    accepted = {canonical}
    if allow_trailing_newline:
        accepted.update({canonical + b"\n", canonical + b"\r\n"})
    require(isinstance(value, dict) and raw in accepted, f"NONCANONICAL:{path}")
    return value


def historical_document(commit: str, path: str) -> dict[str, object]:
    raw = subprocess.run(
        ("git", "show", f"{commit}:{path}"),
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    value = json.loads(raw)
    require(isinstance(value, dict) and canonical_json_bytes(value) == raw, f"NONCANONICAL:{path}")
    return value


def object_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def parse_skips(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    root = ET.parse(path).getroot()
    skipped: list[dict[str, str]] = []
    for case in root.iter("testcase"):
        skip = case.find("skipped")
        if skip is None:
            continue
        test_id = case.attrib.get("name", "")
        require(test_id in ALLOWED_SKIPS, f"UNAPPROVED_TEST_SKIP:{test_id}")
        skipped.append(
            {
                "reason": skip.attrib.get("message", "unspecified"),
                "test_id": f"{case.attrib.get('classname', '')}::{test_id}",
            }
        )
    return skipped


def verify_source_and_definition(head: str) -> tuple[BenchmarkDefinition, dict[str, object]]:
    definition_value = canonical_document(DEFINITION)
    definition = BenchmarkDefinition.from_dict(definition_value)
    attestation = canonical_document(ATTESTATION)
    supersession = canonical_document(SUPERSESSION)
    require(
        attestation.get("benchmark_definition_id") == definition.content_id, "ATTESTATION_DRIFT"
    )
    require(supersession.get("status") == "SUPERSEDED_BEFORE_PRIMARY_RESULTS", "STATUS_DRIFT")
    require(supersession.get("primary_results_exist") is False, "PRIMARY_RESULTS_ALREADY_EXIST")
    replacement = supersession.get("replacement")
    predecessor = supersession.get("predecessor")
    require(isinstance(replacement, dict) and isinstance(predecessor, dict), "SUPERSESSION_INVALID")
    require(
        replacement.get("benchmark_definition_id") == definition.content_id, "REPLACEMENT_DRIFT"
    )
    require(
        replacement.get("definition_attestation_id") == object_id(attestation),
        "REPLACEMENT_ATTESTATION_DRIFT",
    )
    predecessor_commit = predecessor.get("seal_commit")
    require(isinstance(predecessor_commit, str), "PREDECESSOR_COMMIT_INVALID")
    old_value = historical_document(predecessor_commit, "configs/benchmark/primary.yaml")
    old_attestation = historical_document(
        predecessor_commit, "configs/benchmark/primary-definition-attestation.json"
    )
    old_definition = BenchmarkDefinition.from_dict(old_value)
    require(
        predecessor.get("benchmark_definition_id") == old_definition.content_id,
        "PREDECESSOR_DEFINITION_DRIFT",
    )
    require(
        predecessor.get("definition_attestation_id") == object_id(old_attestation),
        "PREDECESSOR_ATTESTATION_DRIFT",
    )
    changed = {
        key
        for key in set(old_value) | set(definition_value)
        if old_value.get(key) != definition_value.get(key)
    }
    require(changed == ALLOWED_DEFINITION_DIFFS, f"DEFINITION_DIFF_FORBIDDEN:{sorted(changed)}")
    require(
        supersession.get("changed_fields") == sorted(ALLOWED_DEFINITION_DIFFS),
        "SUPERSESSION_CHANGED_FIELDS_DRIFT",
    )
    for field in SCIENTIFIC_FIELDS:
        require(
            old_value.get(field) == definition_value.get(field), f"SCIENTIFIC_FIELD_DRIFT:{field}"
        )
    source_commit = definition.source_commit
    require(
        git("rev-parse", f"{source_commit}^{{commit}}") == source_commit, "SOURCE_COMMIT_MISSING"
    )
    require(
        git("show", "-s", "--format=%T", source_commit) == definition.source_tree,
        "SOURCE_TREE_MISMATCH",
    )
    require(git("merge-base", "--is-ancestor", source_commit, head) == "", "SOURCE_NOT_ANCESTOR")
    source_file = "delta-worker-python/src/deltatorrent/benchmark/primary_executor.py"
    require(bool(git("show", f"{source_commit}:{source_file}")), "PRIMARY_EXECUTOR_SOURCE_MISSING")
    overlay_paths = set(git("diff", "--name-only", source_commit, head).splitlines())
    require(overlay_paths <= ALLOWED_OVERLAY_PATHS, f"NON_EVIDENCE_OVERLAY:{sorted(overlay_paths)}")
    return definition, supersession


def verify_regression_evidence() -> None:
    for path in (FORMAL_REGRESSION, PRODUCTION_ATTACKS, ARCHITECTURE_GUARD):
        document = canonical_document(path, allow_trailing_newline=True)
        require(document.get("status") == "PASS", f"REGRESSION_STATUS:{path.name}")
        require(document.get("classification") == "REGRESSION_ONLY", f"CLASSIFICATION:{path.name}")
        require(
            document.get("formal_semantics_id") == FORMAL_SEMANTICS_ID, f"FORMAL_ID:{path.name}"
        )
    require(
        not (ROOT / "reports/benchmark/primary/benchmark-result-qc.json").exists(),
        "BENCHMARK_RESULT_QC_FORBIDDEN",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--github-sha", default=os.environ.get("GITHUB_SHA", "HEAD"))
    parser.add_argument("--completed-check", action="append", default=[])
    parser.add_argument("--junitxml", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    head = git("rev-parse", arguments.github_sha)
    require(set(arguments.completed_check) == REQUIRED_CHECKS, "CI_CHECK_SET_INCOMPLETE")
    definition, supersession = verify_source_and_definition(head)
    verify_regression_evidence()
    report = {
        "benchmark_definition_id": definition.content_id,
        "checks": {name: "PASS" for name in sorted(REQUIRED_CHECKS)},
        "feature_010_decision": "NO_GO",
        "feature_011_blocked": True,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "hardware_skips": parse_skips(arguments.junitxml),
        "head_commit": head,
        "limitations": [
            "NO_PRIMARY_SCIENTIFIC_EXECUTION",
            "NO_PRIMARY_MULTI_HOST_WAN_EXECUTION",
            "NO_APPROVED_REAL_WAN_EXECUTION",
            "NO_BENCHMARK_RESULT_QC",
        ],
        "primary_execution_authorized": False,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source_commit": definition.source_commit,
        "source_tree": definition.source_tree,
        "status": "PASS",
        "supersession": supersession,
        "type_name": "PRIMARY_EXECUTOR_CI_QUALIFICATION",
        "workflow_run_id": arguments.workflow_run_id,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(canonical_json_bytes(report))
    print(canonical_json_bytes(report).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
