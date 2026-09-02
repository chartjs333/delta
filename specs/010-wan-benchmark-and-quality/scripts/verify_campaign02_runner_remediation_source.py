"""Qualify the C2-028..C2-032 runner-remediation source without execution authority."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
SCRIPTS: Final = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

import verify_campaign02_exact_source as legacy  # noqa: E402
from deltatorrent.benchmark.definition import BenchmarkDefinition  # noqa: E402
from deltatorrent.protocol.canonical import canonical_json_bytes  # noqa: E402

PREDECESSOR: Final = "9a4d0d8062ac432d7104284c75dc4b24773dadb0"
_LEGACY_VERIFY_JUNIT: Final = legacy.verify_junit
SUPERSEDED_DEFINITION_ID: Final = (
    "sha256:b263e77766599426dbf13574b05f2104ace1acf2d866e6ca5d9a3abef66f5dd5"
)
IMMUTABLE_AUDIT_PATHS: Final = (
    "configs/benchmark/campaign-02/definition-v2.json",
    "configs/benchmark/campaign-02/qualified-runtime-lineage-v2.json",
    "configs/benchmark/campaign-02/stage-execution-identities-v1.json",
    "reports/benchmark/campaigns/campaign-02/definition-readiness-v2.json",
    "reports/benchmark/campaigns/campaign-02/methodology-diff-v2.json",
    "reports/benchmark/campaigns/campaign-02/definition-construction-authorization-v2.json",
)
NEW_EXECUTION_SOURCES: Final = (
    ".github/workflows/benchmark-campaign02-runner-remediation.yml",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_exactness.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_stage_a_control.py",
    "specs/010-wan-benchmark-and-quality/scripts/verify_campaign02_runner_remediation_source.py",
    ".github/workflows/benchmark-campaign02-stage-a.yml",
)


class RunnerRemediationQualificationError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RunnerRemediationQualificationError(code)


def git(*arguments: str) -> str:
    process = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(process.returncode == 0, "CAMPAIGN02_RUNNER_REMEDIATION_GIT_FAILED")
    return process.stdout.strip()


def tracked_bytes(commit: str, path: str) -> bytes:
    process = subprocess.run(
        ("git", "show", f"{commit}:{path}"),
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, f"CAMPAIGN02_TRACKED_ARTIFACT_MISSING:{path}")
    return process.stdout


def verify_source_boundary(source_commit: str) -> list[str]:
    require(
        git("merge-base", PREDECESSOR, source_commit) == PREDECESSOR,
        "CAMPAIGN02_RUNNER_REMEDIATION_PREDECESSOR_INVALID",
    )
    for path in IMMUTABLE_AUDIT_PATHS:
        require(
            tracked_bytes(PREDECESSOR, path) == tracked_bytes(source_commit, path),
            f"CAMPAIGN02_SUPERSEDED_DEFINITION_MUTATED:{path}",
        )
    changed = sorted(git("diff", "--name-only", PREDECESSOR, source_commit).splitlines())
    require(
        all(path in changed for path in NEW_EXECUTION_SOURCES),
        "CAMPAIGN02_EXECUTABLE_REMEDIATION_SOURCE_INCOMPLETE",
    )
    forbidden = (
        re.compile(r"definition-attestation", re.IGNORECASE),
        re.compile(r"definition-votes", re.IGNORECASE),
        re.compile(r"stage-a-gate-receipt", re.IGNORECASE),
        re.compile(r"primary.*observation", re.IGNORECASE),
        re.compile(r"benchmark-result", re.IGNORECASE),
    )
    for path in changed:
        require(
            not any(pattern.search(path) for pattern in forbidden),
            f"CAMPAIGN02_PREMATURE_AUTHORITY_OR_RESULT:{path}",
        )
    return changed


def verify_governance() -> dict[str, object]:
    definition_value = json.loads(
        (ROOT / "configs/benchmark/campaign-02/definition-v2.json").read_bytes()
    )
    readiness = json.loads(
        (ROOT / "reports/benchmark/campaigns/campaign-02/definition-readiness-v2.json").read_bytes()
    )
    definition = BenchmarkDefinition.from_dict(definition_value)
    authorization = readiness.get("authorization")
    require(
        definition.content_id == SUPERSEDED_DEFINITION_ID
        and readiness.get("benchmark_definition_id") == SUPERSEDED_DEFINITION_ID
        and readiness.get("primary_observations_created") == 0
        and readiness.get("execution_authorization") == "ABSENT"
        and isinstance(authorization, dict)
        and authorization
        and all(value is False for value in authorization.values()),
        "CAMPAIGN02_SUPERSEDED_DEFINITION_GOVERNANCE_INVALID",
    )
    return {
        "independent_votes_present": 0,
        "primary_observations_created": 0,
        "status": "SUPERSEDED_BEFORE_ATTESTATION_PENDING_REPLACEMENT",
        "superseded_definition_id": SUPERSEDED_DEFINITION_ID,
    }


def verify_junit(path: Path) -> dict[str, object]:
    result = _LEGACY_VERIFY_JUNIT(path)
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise RunnerRemediationQualificationError("CAMPAIGN02_PORTABLE_JUNIT_INVALID") from exc
    cases = {
        case.attrib.get("name", "").split("[", 1)[0]
        for suite in ([root] if root.tag == "testsuite" else list(root.findall("testsuite")))
        for case in suite.iter("testcase")
    }
    required = {
        "test_authorization_verifier_cannot_be_presented_as_exactness_executor",
        "test_generated_catalog_uses_one_exact_stage_specific_runner",
        "test_generated_stage_b_reference_plan_runs_through_primary_scientific_runner",
        "test_multi_role_metadata_cannot_replace_a_stage_runner",
        "test_stage_a_rejects_incomplete_evidence_root_and_campaign01_bindings",
        "test_stage_a_requires_exact_15_plans_and_signed_authorization",
        "test_valid_campaign02_stage_a_dry_execution_emits_bound_v2_receipt",
        "test_valid_stage_c_dry_execution_requires_exact_stage_a_and_b_receipts",
    }
    require(required <= cases, "CAMPAIGN02_RUNNER_REGRESSION_CASES_MISSING")
    result["runner_remediation_required_cases"] = sorted(required)
    return result


def build(source_commit: str, portable_junit: Path, hardware_evidence: Path) -> dict[str, object]:
    legacy.PREDECESSOR = PREDECESSOR
    legacy.EXECUTION_BINDING_SOURCES = tuple(
        sorted({*legacy.EXECUTION_BINDING_SOURCES, *NEW_EXECUTION_SOURCES})
    )
    legacy.verify_source_boundary = verify_source_boundary
    legacy.verify_governance = verify_governance
    legacy.verify_junit = verify_junit
    report = legacy.build(source_commit, portable_junit, hardware_evidence)
    task_ids = report.get("task_ids")
    checks = report.get("checks")
    execution_binding = report.get("execution_binding")
    require(
        isinstance(task_ids, list)
        and isinstance(checks, list)
        and isinstance(execution_binding, dict),
        "CAMPAIGN02_RUNNER_REMEDIATION_REPORT_INVALID",
    )
    task_ids.extend(["C2-028", "C2-029", "C2-030", "C2-031", "C2-032"])
    checks.extend(
        [
            "STAGE_SPECIFIC_PLAN_RUNNER_BINDING_PASS",
            "PRIMARY_SCIENTIFIC_RUNNER_CATALOG_COMPATIBILITY_PASS",
            "CAMPAIGN02_STAGE_A_EXECUTOR_AND_WORKFLOW_PASS",
            "TYPED_STAGE_A_RECEIPT_EMISSION_PASS",
            "CAMPAIGN02_STAGE_C_EXECUTOR_PASS",
            "MULTI_ROLE_METADATA_NON_EXECUTABLE_PASS",
        ]
    )
    execution_binding.update(
        {
            "exactness_runner_entrypoint": (
                "deltatorrent.benchmark.campaign02_exactness.run_stage_a"
            ),
            "network_fault_runner_entrypoint": (
                "deltatorrent.benchmark.campaign02_network_fault.run_stage_c"
            ),
            "stage_a_plan_count": 15,
            "stage_c_plan_count": 15,
            "stage_specific_runner_binding": True,
            "typed_stage_a_receipt_schema": "2.0.0",
        }
    )
    report["qualification_generation"] = "C2_033_REPLACEMENT_SOURCE_PENDING_CI_RECEIPT"
    report["schema_version"] = "2.0.0"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--portable-junit", type=Path, required=True)
    parser.add_argument("--hardware-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = build(arguments.source_commit, arguments.portable_junit, arguments.hardware_evidence)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    require(not arguments.output.exists(), "CAMPAIGN02_QUALIFICATION_OUTPUT_EXISTS")
    arguments.output.write_bytes(canonical_json_bytes(report) + b"\n")
    print(
        canonical_json_bytes(
            {
                "primary_execution_authorized": False,
                "source_commit": arguments.source_commit,
                "source_tree": report["source"]["tree"],
                "status": "PASS",
            }
        ).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
