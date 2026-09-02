"""Qualify C2-034..C2-037 source without executing a benchmark stage."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
SCRIPTS: Final = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

import verify_campaign02_runner_remediation_source as legacy  # noqa: E402
from deltatorrent.benchmark.definition import BenchmarkDefinition  # noqa: E402
from deltatorrent.protocol.canonical import canonical_json_bytes  # noqa: E402

PREDECESSOR: Final = "c9a2da487eb6637200e45dbbd56d84b30704d38e"
SUPERSEDED_DEFINITION_ID: Final = (
    "sha256:3844edbdcfc402ca3fbd54f9a2e4dfab965a8a7280a6ccd3dad70611e88ee803"
)
_BASE_VERIFY_JUNIT: Final = legacy._LEGACY_VERIFY_JUNIT
IMMUTABLE_DEFINITION_PATHS: Final = (
    "configs/benchmark/campaign-02/definition-v3.json",
    "configs/benchmark/campaign-02/qualified-runtime-lineage-v3.json",
    "configs/benchmark/campaign-02/stage-execution-identities-v2.json",
    "reports/benchmark/campaigns/campaign-02/definition-readiness-v3.json",
    "reports/benchmark/campaigns/campaign-02/methodology-diff-v3.json",
    "reports/benchmark/campaigns/campaign-02/definition-construction-authorization-v3.json",
)
NEW_SOURCES: Final = (
    ".github/workflows/benchmark-campaign02-runner-provenance.yml",
    ".github/workflows/benchmark-campaign02-stage-a.yml",
    "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v1.json",
    "delta-protocol/schemas/010/campaign-02/benchmark-definition-v4.json",
    "delta-protocol/schemas/010/campaign-02/qualified-runtime-lineage-v4.json",
    "delta-protocol/schemas/010/campaign-02/stage-execution-identities-v3.json",
    "delta-protocol/schemas/010/campaign-02/stage-a-semantic-evidence-v1.json",
    "delta-protocol/schemas/010/campaign-02/stage-gate-receipt-v3.json",
    "delta-protocol/schemas/010/campaign-02/stage-gate-result-v2.json",
    "delta-protocol/schemas/010/campaign-02/stage-plan-evidence-v2.json",
    "delta-protocol/schemas/010/campaign-02/stage-workflow-gate-qc-v2.json",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_exactness.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_a_evidence.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
    "delta-worker-python/src/deltatorrent/benchmark/fault_profiles.py",
    "delta-worker-python/src/deltatorrent/benchmark/network_profiles.py",
    "reports/benchmark/campaigns/campaign-02/definition-supersession-executable-provenance.json",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_stage_a_control.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py",
    "specs/010-wan-benchmark-and-quality/scripts/verify_campaign02_runner_provenance_source.py",
)


class RunnerProvenanceQualificationError(RuntimeError):
    """Stable source-qualification error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RunnerProvenanceQualificationError(code)


def git(*arguments: str) -> str:
    process = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(process.returncode == 0, "CAMPAIGN02_RUNNER_PROVENANCE_GIT_FAILED")
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
        "CAMPAIGN02_RUNNER_PROVENANCE_PREDECESSOR_INVALID",
    )
    for path in IMMUTABLE_DEFINITION_PATHS:
        require(
            tracked_bytes(PREDECESSOR, path) == tracked_bytes(source_commit, path),
            f"CAMPAIGN02_DEFINITION_V3_MUTATED:{path}",
        )
    changed = sorted(git("diff", "--name-only", PREDECESSOR, source_commit).splitlines())
    require(
        all(path in changed for path in NEW_SOURCES),
        "CAMPAIGN02_RUNNER_PROVENANCE_SOURCE_INCOMPLETE",
    )
    return changed


def verify_governance() -> dict[str, object]:
    definition = BenchmarkDefinition.from_dict(
        json.loads((ROOT / "configs/benchmark/campaign-02/definition-v3.json").read_bytes())
    )
    supersession = json.loads(
        (
            ROOT / "reports/benchmark/campaigns/campaign-02/"
            "definition-supersession-executable-provenance.json"
        ).read_bytes()
    )
    require(
        definition.content_id == SUPERSEDED_DEFINITION_ID
        and supersession.get("superseded_definition_id") == SUPERSEDED_DEFINITION_ID
        and supersession.get("status") == "SUPERSEDED_BEFORE_ATTESTATION"
        and supersession.get("votes") == 0
        and supersession.get("attestation") == "ABSENT"
        and supersession.get("observations") == 0
        and supersession.get("replacement_definition_id") is None,
        "CAMPAIGN02_DEFINITION_V3_SUPERSESSION_INVALID",
    )
    return {
        "definition_attestation": "ABSENT",
        "independent_votes_present": 0,
        "primary_observations_created": 0,
        "status": "SUPERSEDED_BEFORE_ATTESTATION_PENDING_DEFINITION_V4",
        "superseded_definition_id": SUPERSEDED_DEFINITION_ID,
    }


def verify_junit(path: Path) -> dict[str, object]:
    result = _BASE_VERIFY_JUNIT(path)
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise RunnerProvenanceQualificationError(
            "CAMPAIGN02_RUNNER_PROVENANCE_JUNIT_INVALID"
        ) from exc
    cases = {
        case.attrib.get("name", "").split("[", 1)[0]
        for suite in ([root] if root.tag == "testsuite" else list(root.findall("testsuite")))
        for case in suite.iter("testcase")
    }
    required = {
        "test_concrete_stage_c_runner_executes_all_15_plans_and_profiles",
        "test_stage_a_admission_test_api_cannot_emit_a_gate_receipt",
        "test_stage_a_rejects_caller_supplied_dry_runner_before_execution",
        "test_stage_a_semantic_verifier_rejects_same_named_fabricated_artifacts",
        "test_stage_a_workflow_finalizer_binds_to_exact_analyzer_bytes",
        "test_stage_a_workflow_provenance_rejects_wrong_github_context",
        "test_stage_c_admission_requires_exact_stage_a_and_b_receipts_without_execution",
    }
    require(required <= cases, "CAMPAIGN02_RUNNER_PROVENANCE_CASES_MISSING")
    result["runner_provenance_required_cases"] = sorted(required)
    return result


def build(source_commit: str, portable_junit: Path, hardware_evidence: Path) -> dict[str, object]:
    legacy.PREDECESSOR = PREDECESSOR
    legacy.IMMUTABLE_AUDIT_PATHS = tuple(
        sorted({*legacy.IMMUTABLE_AUDIT_PATHS, *IMMUTABLE_DEFINITION_PATHS})
    )
    legacy.NEW_EXECUTION_SOURCES = tuple(sorted({*legacy.NEW_EXECUTION_SOURCES, *NEW_SOURCES}))
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
        "CAMPAIGN02_RUNNER_PROVENANCE_REPORT_INVALID",
    )
    task_ids.extend(["C2-034", "C2-035", "C2-036", "C2-037"])
    checks.extend(
        [
            "IDENTITY_BEARING_PRODUCTION_RUNNER_PASS",
            "CALLER_SUPPLIED_DRY_FIXTURE_SYNTHETIC_FAIL_CLOSED_PASS",
            "CONCRETE_STAGE_C_15_PLAN_PROFILE_EXECUTION_PASS",
            "STAGE_A_SEMANTIC_EVIDENCE_CONTENT_VERIFICATION_PASS",
            "ACTUAL_GITHUB_WORKFLOW_PROVENANCE_CLOSURE_PASS",
            "DEFINITION_V3_SUPERSEDED_BEFORE_ATTESTATION_PASS",
        ]
    )
    execution_binding.update(
        {
            "production_receipt_schema": "3.0.0",
            "runner_object_identity_verified_before_first_plan": True,
            "stage_a_semantic_artifact_count": 7,
            "stage_c_concrete_plan_count": 15,
            "workflow_sha_from_github_context": True,
        }
    )
    report["qualification_generation"] = "C2_034_C2_037_SOURCE_PENDING_TERMINAL_CI_RECEIPT"
    report["schema_version"] = "3.0.0"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--portable-junit", type=Path, required=True)
    parser.add_argument("--hardware-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = build(arguments.source_commit, arguments.portable_junit, arguments.hardware_evidence)
    require(not arguments.output.exists(), "CAMPAIGN02_QUALIFICATION_OUTPUT_EXISTS")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
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
