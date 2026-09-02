"""Verify and execute the signed Campaign 02 Stage A authority bundle."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.arms import ArmSpec  # noqa: E402
from deltatorrent.benchmark.campaign02 import (  # noqa: E402
    CampaignExecutionPlan,
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.campaign02_binding import (  # noqa: E402
    Campaign02PlanCatalog,
    QualifiedRuntimeLineage,
    compile_campaign02_plan_catalog,
)
from deltatorrent.benchmark.campaign02_exactness import run_stage_a  # noqa: E402
from deltatorrent.benchmark.campaign02_execution_identities import (  # noqa: E402
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.campaign02_stage_execution import (  # noqa: E402
    StageExecutionSummary,
    StageGateFinalization,
    StagePlanEvidence,
    write_receipt_create_only,
)
from deltatorrent.benchmark.definition import BenchmarkDefinition  # noqa: E402
from deltatorrent.benchmark.governance import (  # noqa: E402
    BenchmarkReviewValidatorSet,
    SignedDefinitionVote,
)
from deltatorrent.benchmark.stage_authorization import (  # noqa: E402
    SignedStageAuthorizationVote,
    StageAuthorizationProof,
    StageAuthorizationValidatorSet,
)
from deltatorrent.protocol.canonical import (  # noqa: E402
    canonical_json_bytes,
    sha256_content_id,
)

BUNDLE_FIELDS: Final = {
    "arms",
    "definition",
    "definition_attestation",
    "definition_validator_set",
    "definition_votes",
    "runtime_lineage",
    "schema_version",
    "stage_authorization",
    "stage_authorization_attestation",
    "stage_authorization_validator_set",
    "stage_authorization_votes",
    "stage_execution_identities",
    "type_name",
}
STAGE_A_EVIDENCE_FILENAMES: Final = {
    "java-jdk25.log",
    "java-jdk26.log",
    "native-clang-cpp20.xml",
    "native-clang-cpp23.xml",
    "native-gcc-cpp20.xml",
    "native-gcc-cpp23.xml",
    "python-cross-component.xml",
}


class StageAControlError(ValueError):
    """Stable fail-closed Stage A workflow error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise StageAControlError(code)


def load_canonical(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StageAControlError("CAMPAIGN02_STAGE_A_JSON_INVALID") from exc
    require(
        isinstance(value, dict)
        and raw in {canonical_json_bytes(value), canonical_json_bytes(value) + b"\n"},
        "CAMPAIGN02_STAGE_A_JSON_NONCANONICAL",
    )
    return value


def git(source_root: Path, *arguments: str) -> str:
    process = subprocess.run(
        ("git", "-C", str(source_root), *arguments),
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(process.returncode == 0, "CAMPAIGN02_STAGE_A_GIT_FAILED")
    return process.stdout.strip()


@dataclass(frozen=True, slots=True)
class AuthorityBundle:
    definition: BenchmarkDefinition
    catalog: Campaign02PlanCatalog
    runtime_lineage: QualifiedRuntimeLineage
    stage_identities: StageExecutionIdentityManifest
    stage_authorization_proof: StageAuthorizationProof

    @classmethod
    def load(cls, path: Path) -> AuthorityBundle:
        value = load_canonical(path)
        require(
            set(value) == BUNDLE_FIELDS
            and value["schema_version"] == "1.0.0"
            and value["type_name"] == "CAMPAIGN02_STAGE_A_AUTHORITY_BUNDLE",
            "CAMPAIGN02_STAGE_A_BUNDLE_FIELDS_INVALID",
        )
        definition = BenchmarkDefinition.from_dict(value["definition"])
        definition_validator_set = BenchmarkReviewValidatorSet.from_dict(
            value["definition_validator_set"]
        )
        raw_definition_votes = value["definition_votes"]
        raw_arms = value["arms"]
        require(
            isinstance(raw_definition_votes, list)
            and isinstance(raw_arms, list)
            and len(raw_arms) == 5,
            "CAMPAIGN02_STAGE_A_BUNDLE_COLLECTION_INVALID",
        )
        definition_votes = tuple(
            SignedDefinitionVote.from_dict(item) for item in raw_definition_votes
        )
        arms = tuple(ArmSpec.from_wrapper(item) for item in raw_arms)
        runtime_lineage = QualifiedRuntimeLineage.from_dict(value["runtime_lineage"])
        stage_identities = StageExecutionIdentityManifest.from_dict(
            value["stage_execution_identities"]
        )
        workload = load_workload_contract(ROOT / "configs/benchmark/campaign-02/workload-v2.json")
        domain_manifest = load_domain_manifest(
            ROOT / "configs/benchmark/campaign-02/domain-manifest-v1.json"
        )
        ticket_plan = load_ticket_plan(
            ROOT / "configs/benchmark/campaign-02/ticket-plan-v1.json",
            workload,
            domain_manifest,
        )
        catalog = compile_campaign02_plan_catalog(
            definition=definition,
            attestation_document=_dict(
                value["definition_attestation"],
                "CAMPAIGN02_STAGE_A_DEFINITION_ATTESTATION_INVALID",
            ),
            validator_set=definition_validator_set,
            votes=definition_votes,
            workload=workload,
            domain_manifest=domain_manifest,
            ticket_plan=ticket_plan,
            arms=arms,
            runtime_lineage=runtime_lineage,
            stage_identities=stage_identities,
        )
        stage_validator_set = StageAuthorizationValidatorSet.from_dict(
            value["stage_authorization_validator_set"]
        )
        raw_stage_votes = value["stage_authorization_votes"]
        require(isinstance(raw_stage_votes, list), "CAMPAIGN02_STAGE_A_VOTES_INVALID")
        proof = StageAuthorizationProof(
            authorization_document=_dict(
                value["stage_authorization"],
                "CAMPAIGN02_STAGE_A_AUTHORIZATION_INVALID",
            ),
            attestation_document=_dict(
                value["stage_authorization_attestation"],
                "CAMPAIGN02_STAGE_A_AUTHORIZATION_ATTESTATION_INVALID",
            ),
            validator_set=stage_validator_set,
            votes=tuple(SignedStageAuthorizationVote.from_dict(item) for item in raw_stage_votes),
        )
        return cls(definition, catalog, runtime_lineage, stage_identities, proof)

    def verify_source(self, source_root: Path) -> None:
        require(
            git(source_root, "rev-parse", "HEAD") == self.runtime_lineage.source_commit,
            "CAMPAIGN02_STAGE_A_SOURCE_COMMIT_MISMATCH",
        )
        require(
            git(source_root, "show", "-s", "--format=%T", "HEAD")
            == self.runtime_lineage.source_tree,
            "CAMPAIGN02_STAGE_A_SOURCE_TREE_MISMATCH",
        )
        require(not git(source_root, "status", "--porcelain"), "CAMPAIGN02_STAGE_A_SOURCE_DIRTY")


def _dict(value: object, code: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise StageAControlError(code)
    return value


class EvidenceReplayRunner:
    def __init__(self, evidence: tuple[StagePlanEvidence, ...]) -> None:
        self._evidence = {item.plan_id: item for item in evidence}
        require(len(self._evidence) == len(evidence), "CAMPAIGN02_STAGE_A_EVIDENCE_DUPLICATE")

    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence:
        try:
            return self._evidence[plan.content_id]
        except KeyError as exc:
            raise StageAControlError("CAMPAIGN02_STAGE_A_EVIDENCE_MISSING") from exc


class WorkflowGateFinalizer:
    def __init__(self, workflow_run_id: int, workflow_head: str, finalized_at: datetime) -> None:
        require(workflow_run_id > 0, "CAMPAIGN02_STAGE_A_WORKFLOW_RUN_INVALID")
        self.workflow_run_id = workflow_run_id
        self.workflow_head = workflow_head
        self.finalized_at = finalized_at
        self.document: dict[str, object] | None = None

    def finalize(self, summary: StageExecutionSummary) -> StageGateFinalization:
        require(
            self.workflow_head == summary.source_commit,
            "CAMPAIGN02_STAGE_A_WORKFLOW_HEAD_MISMATCH",
        )
        self.document = {
            "decision": "PASS",
            "gate_result_id": summary.content_id,
            "gate_analyzer_id": summary.gate_analyzer_id,
            "plan_evidence_ids": list(summary.plan_evidence_ids),
            "runner_id": summary.runner_id,
            "schema_version": "1.0.0",
            "source_commit": summary.source_commit,
            "source_tree": summary.source_tree,
            "type_name": "CAMPAIGN02_STAGE_A_WORKFLOW_GATE_QC",
            "workflow_head": self.workflow_head,
            "workflow_run_id": self.workflow_run_id,
        }
        return StageGateFinalization(
            gate_result_id=summary.content_id,
            gate_qc_id=sha256_content_id(
                b"deltareduce.010.campaign02-stage-a-workflow-gate-qc.v1\0"
                + canonical_json_bytes(self.document)
            ),
            finalized_at=self.finalized_at,
        )


def write_create_only(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(canonical_json_bytes(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise StageAControlError("CAMPAIGN02_STAGE_A_OUTPUT_EXISTS") from exc


def verify_bundle(arguments: argparse.Namespace) -> dict[str, object]:
    bundle = AuthorityBundle.load(arguments.bundle)
    bundle.verify_source(arguments.source_root)
    plan_ids = list(bundle.catalog.plan_ids_for_stage("STAGE_A_EXACTNESS"))
    require(len(plan_ids) == 15, "CAMPAIGN02_STAGE_A_PLAN_SET_INVALID")
    return {
        "benchmark_definition_id": bundle.definition.content_id,
        "matrix": [
            {"ordinal": ordinal, "plan_id": plan_id} for ordinal, plan_id in enumerate(plan_ids)
        ],
        "plan_ids": plan_ids,
        "qualified_source_commit": bundle.runtime_lineage.source_commit,
        "qualified_source_tree": bundle.runtime_lineage.source_tree,
        "status": "PASS",
    }


def emit_plan_evidence(arguments: argparse.Namespace) -> dict[str, object]:
    bundle = AuthorityBundle.load(arguments.bundle)
    bundle.verify_source(arguments.source_root)
    plans = tuple(
        item
        for item in bundle.catalog.plans
        if item.gate_stage == "STAGE_A_EXACTNESS" and item.content_id == arguments.plan_id
    )
    require(len(plans) == 1, "CAMPAIGN02_STAGE_A_PLAN_NOT_FOUND")
    plan = plans[0]
    from deltatorrent.benchmark.campaign02 import authorize_execution_class

    authorize_execution_class(
        bundle.stage_authorization_proof,
        plan,
        plan_catalog=bundle.catalog,  # type: ignore[arg-type]
        predecessor_gate_receipts={},
        runner_role="EXACTNESS_RUNNER",
    )
    evidence_files = tuple(
        sorted(
            {
                *arguments.evidence_file,
                *(
                    path
                    for directory in arguments.evidence_dir
                    for path in directory.rglob("*")
                    if path.is_file()
                ),
            }
        )
    )
    require(
        all(path.is_file() for path in evidence_files)
        and {path.name for path in evidence_files} == STAGE_A_EVIDENCE_FILENAMES
        and len(evidence_files) == len(STAGE_A_EVIDENCE_FILENAMES),
        "CAMPAIGN02_STAGE_A_EXACTNESS_MATRIX_INCOMPLETE",
    )
    evidence = StagePlanEvidence(
        plan_id=plan.content_id,
        runner_id=plan.runner_id,
        source_commit=plan.source_commit,
        source_tree=plan.source_tree,
        evidence_ids=tuple(sha256_content_id(path.read_bytes()) for path in evidence_files),
    )
    write_create_only(arguments.output, evidence.document)
    return {"evidence_id": evidence.content_id, "plan_id": plan.content_id, "status": "PASS"}


def finalize(arguments: argparse.Namespace) -> dict[str, object]:
    bundle = AuthorityBundle.load(arguments.bundle)
    bundle.verify_source(arguments.source_root)
    paths = tuple(sorted(arguments.evidence_dir.rglob("*.json")))
    evidence = tuple(StagePlanEvidence.from_dict(load_canonical(path)) for path in paths)
    require(len(evidence) == 15, "CAMPAIGN02_STAGE_A_EVIDENCE_SET_INCOMPLETE")
    finalized_at = datetime.fromisoformat(arguments.finalized_at.replace("Z", "+00:00"))
    finalizer = WorkflowGateFinalizer(
        arguments.workflow_run_id, arguments.workflow_head, finalized_at
    )
    receipt = run_stage_a(
        definition=bundle.definition,
        plan_catalog=bundle.catalog,
        authorization_proof=bundle.stage_authorization_proof,
        runtime_lineage=bundle.runtime_lineage,
        stage_identities=bundle.stage_identities,
        plan_runner=EvidenceReplayRunner(evidence),
        gate_finalizer=finalizer,
    )
    require(finalizer.document is not None, "CAMPAIGN02_STAGE_A_GATE_QC_MISSING")
    write_create_only(arguments.output_gate_qc, finalizer.document)
    write_receipt_create_only(arguments.output_receipt, receipt)
    return {
        "receipt_id": receipt.content_id,
        "required_plan_count": len(receipt.required_plan_ids),
        "runner_id": receipt.runner_id,
        "status": "PASS",
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--bundle", type=Path, required=True)
    common.add_argument("--source-root", type=Path, required=True)
    commands.add_parser("verify-bundle", parents=[common])
    emit = commands.add_parser("emit-plan-evidence", parents=[common])
    emit.add_argument("--plan-id", required=True)
    emit.add_argument("--evidence-file", action="append", type=Path, default=[])
    emit.add_argument("--evidence-dir", action="append", type=Path, default=[])
    emit.add_argument("--output", type=Path, required=True)
    close = commands.add_parser("finalize", parents=[common])
    close.add_argument("--evidence-dir", type=Path, required=True)
    close.add_argument("--workflow-run-id", type=int, required=True)
    close.add_argument("--workflow-head", required=True)
    close.add_argument("--finalized-at", required=True)
    close.add_argument("--output-gate-qc", type=Path, required=True)
    close.add_argument("--output-receipt", type=Path, required=True)
    return result


def main() -> int:
    arguments = parser().parse_args()
    handlers = {
        "verify-bundle": verify_bundle,
        "emit-plan-evidence": emit_plan_evidence,
        "finalize": finalize,
    }
    value = handlers[arguments.command](arguments)
    print(canonical_json_bytes(value).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
