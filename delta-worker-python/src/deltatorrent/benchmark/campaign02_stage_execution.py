"""Authority-gated Campaign 02 stage execution and typed receipt emission."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Protocol, cast

from deltatorrent.benchmark.campaign02 import (
    Campaign02PlanCatalogView,
    CampaignExecutionPlan,
    authorize_execution_class,
)
from deltatorrent.benchmark.campaign02_binding import (
    Campaign02PlanCatalog,
    QualifiedRuntimeLineage,
)
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.stage_authorization import (
    StageAuthorizationProof,
    StageGateReceipt,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")


class Campaign02StageExecutionError(ValueError):
    """Stable fail-closed stage executor rejection."""


def _fail(code: str) -> Campaign02StageExecutionError:
    return Campaign02StageExecutionError(code)


def _id(value: str, code: str) -> str:
    if _CONTENT_ID.fullmatch(value) is None:
        raise _fail(code)
    return value


@dataclass(frozen=True, slots=True)
class StagePlanEvidence:
    plan_id: str
    runner_id: str
    source_commit: str
    source_tree: str
    evidence_ids: tuple[str, ...]
    decision: str = "PASS"

    def __post_init__(self) -> None:
        if (
            self.decision != "PASS"
            or _CONTENT_ID.fullmatch(self.plan_id) is None
            or _CONTENT_ID.fullmatch(self.runner_id) is None
            or _COMMIT_ID.fullmatch(self.source_commit) is None
            or _COMMIT_ID.fullmatch(self.source_tree) is None
            or not self.evidence_ids
            or any(_CONTENT_ID.fullmatch(item) is None for item in self.evidence_ids)
            or len(set(self.evidence_ids)) != len(self.evidence_ids)
        ):
            raise _fail("CAMPAIGN02_STAGE_PLAN_EVIDENCE_INVALID")

    @classmethod
    def from_dict(cls, value: object) -> StagePlanEvidence:
        fields = {
            "decision",
            "evidence_ids",
            "plan_id",
            "runner_id",
            "schema_version",
            "source_commit",
            "source_tree",
            "type_name",
        }
        if (
            not isinstance(value, dict)
            or set(value) != fields
            or value["schema_version"] != "1.0.0"
            or value["type_name"] != "CAMPAIGN02_STAGE_PLAN_EVIDENCE"
            or not isinstance(value["evidence_ids"], list)
            or any(not isinstance(item, str) for item in value["evidence_ids"])
        ):
            raise _fail("CAMPAIGN02_STAGE_PLAN_EVIDENCE_FIELDS_INVALID")
        result = cls(
            plan_id=str(value["plan_id"]),
            runner_id=str(value["runner_id"]),
            source_commit=str(value["source_commit"]),
            source_tree=str(value["source_tree"]),
            evidence_ids=tuple(value["evidence_ids"]),
            decision=str(value["decision"]),
        )
        if result.document != value:
            raise _fail("CAMPAIGN02_STAGE_PLAN_EVIDENCE_DOCUMENT_MISMATCH")
        return result

    @property
    def document(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "evidence_ids": list(self.evidence_ids),
            "plan_id": self.plan_id,
            "runner_id": self.runner_id,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "type_name": "CAMPAIGN02_STAGE_PLAN_EVIDENCE",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-plan-evidence.v1\0"
            + canonical_json_bytes(self.document)
        )


@dataclass(frozen=True, slots=True)
class StageExecutionSummary:
    completed_stage: str
    benchmark_definition_id: str
    definition_attestation_id: str
    plan_catalog_id: str
    qualified_runtime_lineage_id: str
    stage_execution_identities_id: str
    gate_analyzer_id: str
    stage_authorization_attestation_id: str
    runner_id: str
    source_commit: str
    source_tree: str
    required_plan_ids: tuple[str, ...]
    accepted_plan_ids: tuple[str, ...]
    plan_evidence_ids: tuple[str, ...]

    @property
    def evidence_root(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-evidence-root.v1\0"
            + canonical_json_bytes(list(self.plan_evidence_ids))
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "accepted_plan_ids": list(self.accepted_plan_ids),
            "benchmark_definition_id": self.benchmark_definition_id,
            "completed_stage": self.completed_stage,
            "definition_attestation_id": self.definition_attestation_id,
            "evidence_root": self.evidence_root,
            "gate_analyzer_id": self.gate_analyzer_id,
            "plan_catalog_id": self.plan_catalog_id,
            "plan_evidence_ids": list(self.plan_evidence_ids),
            "qualified_runtime_lineage_id": self.qualified_runtime_lineage_id,
            "required_plan_ids": list(self.required_plan_ids),
            "runner_id": self.runner_id,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "stage_authorization_attestation_id": self.stage_authorization_attestation_id,
            "stage_execution_identities_id": self.stage_execution_identities_id,
            "type_name": "CAMPAIGN02_STAGE_GATE_RESULT",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-gate-result.v1\0"
            + canonical_json_bytes(self.document)
        )


@dataclass(frozen=True, slots=True)
class StageGateFinalization:
    gate_result_id: str
    gate_qc_id: str
    finalized_at: datetime
    decision: str = "PASS"

    def __post_init__(self) -> None:
        if (
            self.decision != "PASS"
            or _CONTENT_ID.fullmatch(self.gate_result_id) is None
            or _CONTENT_ID.fullmatch(self.gate_qc_id) is None
            or self.finalized_at.tzinfo is None
        ):
            raise _fail("CAMPAIGN02_STAGE_GATE_FINALIZATION_INVALID")


class StagePlanRunner(Protocol):
    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence: ...


class StageGateFinalizer(Protocol):
    def finalize(self, summary: StageExecutionSummary) -> StageGateFinalization: ...


def execute_stage(
    *,
    completed_stage: str,
    runner_role: str,
    definition: BenchmarkDefinition,
    plan_catalog: Campaign02PlanCatalog,
    authorization_proof: StageAuthorizationProof,
    predecessor_gate_receipts: Mapping[str, bytes],
    runtime_lineage: QualifiedRuntimeLineage,
    stage_identities: StageExecutionIdentityManifest,
    plan_runner: StagePlanRunner,
    gate_finalizer: StageGateFinalizer,
) -> StageGateReceipt:
    if completed_stage not in {"STAGE_A_EXACTNESS", "STAGE_C_EMULATED_WAN"}:
        raise _fail("CAMPAIGN02_EXECUTOR_STAGE_INVALID")
    if (
        definition.raw.get("schema_version") != "3.0.0"
        or definition.content_id != plan_catalog.definition_id
        or definition.qualified_runtime_lineage_id != runtime_lineage.content_id
        or definition.stage_execution_identities_id != stage_identities.content_id
        or runtime_lineage.stage_execution_identities_id != stage_identities.content_id
        or plan_catalog.runtime_lineage_id != runtime_lineage.content_id
        or plan_catalog.stage_execution_identities_id != stage_identities.content_id
        or plan_catalog.gate_analyzer_id != stage_identities.identity_id("stage_gate_analyzer")
        or definition.source_commit != runtime_lineage.source_commit
        or definition.source_tree != runtime_lineage.source_tree
        or stage_identities.source_commit != runtime_lineage.source_commit
        or stage_identities.source_tree != runtime_lineage.source_tree
    ):
        raise _fail("CAMPAIGN02_STAGE_EXECUTION_PACKAGE_MISMATCH")
    identity_name = {
        "STAGE_A_EXACTNESS": "exactness_runner",
        "STAGE_C_EMULATED_WAN": "network_fault_runner",
    }[completed_stage]
    runner_id = runtime_lineage.runner_id_for_stage(completed_stage)
    if runner_id != stage_identities.identity_id(identity_name):
        raise _fail("CAMPAIGN02_STAGE_EXECUTOR_IDENTITY_MISMATCH")
    required_plan_ids = plan_catalog.plan_ids_for_stage(completed_stage)
    plans = tuple(item for item in plan_catalog.plans if item.gate_stage == completed_stage)
    if (
        len(plans) != 15
        or len(required_plan_ids) != 15
        or tuple(item.content_id for item in plans) != required_plan_ids
        or any(item.runner_id != runner_id for item in plans)
    ):
        raise _fail("CAMPAIGN02_STAGE_EXACT_PLAN_SET_REQUIRED")
    verified = None
    evidence: list[StagePlanEvidence] = []
    for plan in plans:
        verified = authorize_execution_class(
            authorization_proof,
            plan,
            plan_catalog=cast(Campaign02PlanCatalogView, plan_catalog),
            predecessor_gate_receipts=predecessor_gate_receipts,
            runner_role=runner_role,
        )
        item = plan_runner.execute(plan)
        if (
            item.plan_id != plan.content_id
            or item.runner_id != runner_id
            or item.source_commit != plan.source_commit
            or item.source_tree != plan.source_tree
        ):
            raise _fail("CAMPAIGN02_STAGE_PLAN_EVIDENCE_BINDING_MISMATCH")
        evidence.append(item)
    if verified is None or len({item.content_id for item in evidence}) != 15:
        raise _fail("CAMPAIGN02_STAGE_EVIDENCE_SET_INCOMPLETE")
    summary = StageExecutionSummary(
        completed_stage=completed_stage,
        benchmark_definition_id=definition.content_id,
        definition_attestation_id=plan_catalog.attestation_id,
        plan_catalog_id=plan_catalog.content_id,
        qualified_runtime_lineage_id=runtime_lineage.content_id,
        stage_execution_identities_id=stage_identities.content_id,
        gate_analyzer_id=plan_catalog.gate_analyzer_id,
        stage_authorization_attestation_id=verified.content_id,
        runner_id=runner_id,
        source_commit=runtime_lineage.source_commit,
        source_tree=runtime_lineage.source_tree,
        required_plan_ids=required_plan_ids,
        accepted_plan_ids=tuple(item.plan_id for item in evidence),
        plan_evidence_ids=tuple(item.content_id for item in evidence),
    )
    finalization = gate_finalizer.finalize(summary)
    if (
        finalization.gate_result_id != summary.content_id
        or finalization.finalized_at < verified.authorization.issued_at
    ):
        raise _fail("CAMPAIGN02_STAGE_GATE_RESULT_MISMATCH")
    return StageGateReceipt(
        accepted_plan_ids=summary.accepted_plan_ids,
        benchmark_definition_id=summary.benchmark_definition_id,
        completed_stage=summary.completed_stage,
        definition_attestation_id=summary.definition_attestation_id,
        evidence_root=summary.evidence_root,
        finalized_at=finalization.finalized_at,
        gate_analyzer_id=summary.gate_analyzer_id,
        gate_qc_id=_id(finalization.gate_qc_id, "CAMPAIGN02_STAGE_GATE_QC_ID_INVALID"),
        gate_result_id=summary.content_id,
        plan_catalog_id=summary.plan_catalog_id,
        qualified_runtime_lineage_id=summary.qualified_runtime_lineage_id,
        required_plan_ids=summary.required_plan_ids,
        source_commit=summary.source_commit,
        source_tree=summary.source_tree,
        stage_authorization_attestation_id=summary.stage_authorization_attestation_id,
        decision="PASS",
        runner_id=summary.runner_id,
    )


def write_receipt_create_only(path: Path, receipt: StageGateReceipt) -> None:
    """Persist a canonical stage receipt without permitting overwrite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(receipt.canonical_bytes)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise _fail("CAMPAIGN02_STAGE_GATE_RECEIPT_ALREADY_EXISTS") from exc
