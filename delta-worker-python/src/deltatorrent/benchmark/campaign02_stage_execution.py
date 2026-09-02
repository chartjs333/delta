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
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
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
    environment_id: str | None = None
    evidence_kind: str | None = None
    implementation_id: str | None = None
    runner_identity_id: str | None = None
    runner_role: str | None = None
    source_class: str | None = None
    verified_summary_ids: tuple[str, ...] = ()

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
        binding = (
            self.environment_id,
            self.evidence_kind,
            self.implementation_id,
            self.runner_identity_id,
            self.runner_role,
            self.source_class,
        )
        if any(item is not None for item in binding):
            if (
                not all(isinstance(item, str) and item for item in binding)
                or _CONTENT_ID.fullmatch(str(self.environment_id)) is None
                or _CONTENT_ID.fullmatch(str(self.implementation_id)) is None
                or _CONTENT_ID.fullmatch(str(self.runner_identity_id)) is None
                or not self.verified_summary_ids
                or any(_CONTENT_ID.fullmatch(item) is None for item in self.verified_summary_ids)
                or len(set(self.verified_summary_ids)) != len(self.verified_summary_ids)
            ):
                raise _fail("CAMPAIGN02_STAGE_PLAN_RUNNER_BINDING_INVALID")

    @classmethod
    def from_dict(cls, value: object) -> StagePlanEvidence:
        common_fields = {
            "decision",
            "evidence_ids",
            "plan_id",
            "runner_id",
            "schema_version",
            "source_commit",
            "source_tree",
            "type_name",
        }
        v2_fields = common_fields | {
            "environment_id",
            "evidence_kind",
            "formal_semantics_id",
            "implementation_id",
            "runner_identity_id",
            "runner_role",
            "source_class",
            "verified_summary_ids",
        }
        if (
            not isinstance(value, dict)
            or value.get("schema_version") not in {"1.0.0", "2.0.0"}
            or set(value)
            != (v2_fields if value.get("schema_version") == "2.0.0" else common_fields)
            or value["type_name"] != "CAMPAIGN02_STAGE_PLAN_EVIDENCE"
            or (
                value.get("schema_version") == "2.0.0"
                and value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            )
            or not isinstance(value["evidence_ids"], list)
            or any(not isinstance(item, str) for item in value["evidence_ids"])
            or (
                value.get("schema_version") == "2.0.0"
                and (
                    not isinstance(value["verified_summary_ids"], list)
                    or any(not isinstance(item, str) for item in value["verified_summary_ids"])
                )
            )
        ):
            raise _fail("CAMPAIGN02_STAGE_PLAN_EVIDENCE_FIELDS_INVALID")
        result = cls(
            plan_id=str(value["plan_id"]),
            runner_id=str(value["runner_id"]),
            source_commit=str(value["source_commit"]),
            source_tree=str(value["source_tree"]),
            evidence_ids=tuple(value["evidence_ids"]),
            decision=str(value["decision"]),
            environment_id=(
                str(value["environment_id"]) if value["schema_version"] == "2.0.0" else None
            ),
            evidence_kind=(
                str(value["evidence_kind"]) if value["schema_version"] == "2.0.0" else None
            ),
            implementation_id=(
                str(value["implementation_id"]) if value["schema_version"] == "2.0.0" else None
            ),
            runner_identity_id=(
                str(value["runner_identity_id"]) if value["schema_version"] == "2.0.0" else None
            ),
            runner_role=(str(value["runner_role"]) if value["schema_version"] == "2.0.0" else None),
            source_class=(
                str(value["source_class"]) if value["schema_version"] == "2.0.0" else None
            ),
            verified_summary_ids=(
                tuple(value["verified_summary_ids"]) if value["schema_version"] == "2.0.0" else ()
            ),
        )
        if result.document != value:
            raise _fail("CAMPAIGN02_STAGE_PLAN_EVIDENCE_DOCUMENT_MISMATCH")
        return result

    @property
    def document(self) -> dict[str, object]:
        document: dict[str, object] = {
            "decision": self.decision,
            "evidence_ids": list(self.evidence_ids),
            "plan_id": self.plan_id,
            "runner_id": self.runner_id,
            "schema_version": ("2.0.0" if self.runner_identity_id is not None else "1.0.0"),
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "type_name": "CAMPAIGN02_STAGE_PLAN_EVIDENCE",
        }
        if self.runner_identity_id is not None:
            document.update(
                {
                    "environment_id": self.environment_id,
                    "evidence_kind": self.evidence_kind,
                    "formal_semantics_id": FORMAL_SEMANTICS_ID,
                    "implementation_id": self.implementation_id,
                    "runner_identity_id": self.runner_identity_id,
                    "runner_role": self.runner_role,
                    "source_class": self.source_class,
                    "verified_summary_ids": list(self.verified_summary_ids),
                }
            )
        return document

    @property
    def content_id(self) -> str:
        domain = (
            b"deltareduce.010.campaign02-stage-plan-evidence.v2\0"
            if self.runner_identity_id is not None
            else b"deltareduce.010.campaign02-stage-plan-evidence.v1\0"
        )
        return sha256_content_id(domain + canonical_json_bytes(self.document))


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
    runner_environment_id: str
    runner_implementation_id: str
    runner_role: str
    runner_source_class: str
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
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_analyzer_id": self.gate_analyzer_id,
            "plan_catalog_id": self.plan_catalog_id,
            "plan_evidence_ids": list(self.plan_evidence_ids),
            "qualified_runtime_lineage_id": self.qualified_runtime_lineage_id,
            "required_plan_ids": list(self.required_plan_ids),
            "runner_id": self.runner_id,
            "runner_environment_id": self.runner_environment_id,
            "runner_implementation_id": self.runner_implementation_id,
            "runner_role": self.runner_role,
            "runner_source_class": self.runner_source_class,
            "schema_version": "2.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "stage_authorization_attestation_id": self.stage_authorization_attestation_id,
            "stage_execution_identities_id": self.stage_execution_identities_id,
            "type_name": "CAMPAIGN02_STAGE_GATE_RESULT",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-gate-result.v2\0"
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


class IdentityBearingStagePlanRunner(Protocol):
    identity_id: str
    role: str
    source_commit: str
    source_tree: str
    environment_id: str
    source_class: str
    implementation_id: str

    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence: ...


class IdentityBearingStageGateFinalizer(Protocol):
    identity_id: str
    role: str
    source_commit: str
    source_tree: str
    environment_id: str
    source_class: str
    implementation_id: str

    def finalize(self, summary: StageExecutionSummary) -> StageGateFinalization: ...


_BOUND_RUNNER_TOKEN: Final = object()
_BOUND_FINALIZER_TOKEN: Final = object()
_FORBIDDEN_PRIMARY_SOURCE_CLASSES: Final = frozenset(
    {"CALLER_SUPPLIED", "DRY", "FIXTURE", "NON_PRIMARY_FIXTURE", "SYNTHETIC"}
)


class VerifiedBoundStageRunner:
    """Opaque production wrapper returned only after recursive identity verification."""

    __slots__ = (
        "_runner",
        "environment_id",
        "identity_id",
        "implementation_id",
        "role",
        "source_class",
        "source_commit",
        "source_tree",
    )

    def __init__(
        self,
        token: object,
        runner: IdentityBearingStagePlanRunner,
    ) -> None:
        if token is not _BOUND_RUNNER_TOKEN:
            raise _fail("CAMPAIGN02_STAGE_RUNNER_DIRECT_CONSTRUCTION_FORBIDDEN")
        self._runner = runner
        self.identity_id = runner.identity_id
        self.role = runner.role
        self.source_commit = runner.source_commit
        self.source_tree = runner.source_tree
        self.environment_id = runner.environment_id
        self.source_class = runner.source_class
        self.implementation_id = runner.implementation_id

    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence:
        return self._runner.execute(plan)


class VerifiedBoundStageGateFinalizer:
    """Opaque gate-finalizer wrapper bound to the manifest's analyzer identity."""

    __slots__ = (
        "_finalizer",
        "environment_id",
        "identity_id",
        "implementation_id",
        "role",
        "source_class",
        "source_commit",
        "source_tree",
    )

    def __init__(
        self,
        token: object,
        finalizer: IdentityBearingStageGateFinalizer,
    ) -> None:
        if token is not _BOUND_FINALIZER_TOKEN:
            raise _fail("CAMPAIGN02_STAGE_FINALIZER_DIRECT_CONSTRUCTION_FORBIDDEN")
        self._finalizer = finalizer
        self.identity_id = finalizer.identity_id
        self.role = finalizer.role
        self.source_commit = finalizer.source_commit
        self.source_tree = finalizer.source_tree
        self.environment_id = finalizer.environment_id
        self.source_class = finalizer.source_class
        self.implementation_id = finalizer.implementation_id

    def finalize(self, summary: StageExecutionSummary) -> StageGateFinalization:
        return self._finalizer.finalize(summary)


class Campaign02StageGateFinalizer:
    """Source-bound finalizer that closes actual GitHub workflow and artifact provenance."""

    def __init__(
        self,
        *,
        stage_identities: StageExecutionIdentityManifest,
        finalized_at: datetime,
        workflow_repository: str,
        workflow_sha: str,
        dispatch_sha: str,
        workflow_ref: str,
        dispatch_ref: str,
        workflow_file_content_id: str,
        workflow_run_id: int,
        workflow_run_attempt: int,
        authority_artifact_digest: str,
        input_artifact_digests: Mapping[str, str],
        output_artifact_digests: Mapping[str, str],
    ) -> None:
        identity = stage_identities.identity("stage_gate_analyzer")
        self.identity_id = identity.content_id
        self.role = "STAGE_GATE_ANALYZER"
        self.source_commit = stage_identities.source_commit
        self.source_tree = stage_identities.source_tree
        self.environment_id = str(identity.value.get("environment_id", ""))
        self.source_class = "MEASURED_CONTROL_PLANE"
        self.implementation_id = str(identity.value.get("implementation_id", ""))
        self.finalized_at = finalized_at
        self.workflow_repository = workflow_repository
        self.workflow_sha = workflow_sha
        self.dispatch_sha = dispatch_sha
        self.workflow_ref = workflow_ref
        self.dispatch_ref = dispatch_ref
        self.workflow_file_content_id = workflow_file_content_id
        self.workflow_run_id = workflow_run_id
        self.workflow_run_attempt = workflow_run_attempt
        self.authority_artifact_digest = authority_artifact_digest
        self.input_artifact_digests = tuple(sorted(input_artifact_digests.items()))
        self.output_artifact_digests = tuple(sorted(output_artifact_digests.items()))
        self.document: dict[str, object] | None = None
        workflow_path = str(identity.value.get("workflow_path", ""))
        expected_ref = str(identity.value.get("workflow_default_ref", ""))
        expected_repository = str(identity.value.get("workflow_repository", ""))
        expected_workflow_ref = f"{expected_repository}/{workflow_path}@{expected_ref}"
        workflow_hashes = identity.value.get("workflow_hashes")
        expected_file_ids = (
            {
                item.get("content_id")
                for item in workflow_hashes
                if isinstance(item, dict) and item.get("path") == workflow_path
            }
            if isinstance(workflow_hashes, list)
            else set()
        )
        digest_values = (
            authority_artifact_digest,
            *(value for _name, value in self.input_artifact_digests),
            *(value for _name, value in self.output_artifact_digests),
        )
        if (
            finalized_at.tzinfo is None
            or workflow_repository != expected_repository
            or workflow_sha != self.source_commit
            or dispatch_sha != self.source_commit
            or workflow_ref != expected_workflow_ref
            or dispatch_ref != expected_ref
            or workflow_file_content_id not in expected_file_ids
            or workflow_run_id <= 0
            or workflow_run_attempt != 1
            or not self.input_artifact_digests
            or not self.output_artifact_digests
            or any(_CONTENT_ID.fullmatch(item) is None for item in digest_values)
        ):
            raise _fail("CAMPAIGN02_STAGE_WORKFLOW_PROVENANCE_INVALID")

    def finalize(self, summary: StageExecutionSummary) -> StageGateFinalization:
        if (
            summary.gate_analyzer_id != self.identity_id
            or summary.source_commit != self.workflow_sha
            or summary.runner_environment_id != self.environment_id
        ):
            raise _fail("CAMPAIGN02_STAGE_GATE_FINALIZER_SUMMARY_MISMATCH")
        self.document = {
            "authority_artifact_digest": self.authority_artifact_digest,
            "decision": "PASS",
            "dispatch_ref": self.dispatch_ref,
            "dispatch_sha": self.dispatch_sha,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_analyzer_id": summary.gate_analyzer_id,
            "gate_result_id": summary.content_id,
            "input_artifact_digests": dict(self.input_artifact_digests),
            "output_artifact_digests": dict(self.output_artifact_digests),
            "plan_evidence_ids": list(summary.plan_evidence_ids),
            "runner_id": summary.runner_id,
            "schema_version": "2.0.0",
            "source_commit": summary.source_commit,
            "source_tree": summary.source_tree,
            "type_name": "CAMPAIGN02_STAGE_WORKFLOW_GATE_QC",
            "workflow_file_content_id": self.workflow_file_content_id,
            "workflow_ref": self.workflow_ref,
            "workflow_repository": self.workflow_repository,
            "workflow_run_attempt": self.workflow_run_attempt,
            "workflow_run_id": self.workflow_run_id,
            "workflow_sha": self.workflow_sha,
        }
        return StageGateFinalization(
            gate_result_id=summary.content_id,
            gate_qc_id=sha256_content_id(
                b"deltareduce.010.campaign02-stage-workflow-gate-qc.v2\0"
                + canonical_json_bytes(self.document)
            ),
            finalized_at=self.finalized_at,
        )


def _identity_binding(value: object, field: str, code: str) -> str:
    if not isinstance(value, dict):
        raise _fail(code)
    item = value.get(field)
    if not isinstance(item, str) or not item:
        raise _fail(code)
    return item


def verify_bound_stage_runner(
    runner: IdentityBearingStagePlanRunner,
    *,
    identity_name: str,
    stage_identities: StageExecutionIdentityManifest,
    source_root: Path,
) -> VerifiedBoundStageRunner:
    """Bind a concrete production runner to immutable manifest bytes before execution."""
    if stage_identities.schema_version != "3.0.0":
        raise _fail("CAMPAIGN02_STAGE_RUNNER_IDENTITY_VERSION_INVALID")
    identity = stage_identities.identity(identity_name)
    expected = {
        "identity_id": identity.content_id,
        "role": _identity_binding(identity.value, "role", "CAMPAIGN02_STAGE_RUNNER_ROLE_INVALID"),
        "source_commit": stage_identities.source_commit,
        "source_tree": stage_identities.source_tree,
        "environment_id": _identity_binding(
            identity.value, "environment_id", "CAMPAIGN02_STAGE_RUNNER_ENVIRONMENT_INVALID"
        ),
        "source_class": _identity_binding(
            identity.value, "source_class", "CAMPAIGN02_STAGE_RUNNER_SOURCE_CLASS_INVALID"
        ),
        "implementation_id": _identity_binding(
            identity.value, "implementation_id", "CAMPAIGN02_STAGE_RUNNER_IMPLEMENTATION_INVALID"
        ),
    }
    implementation_class = _identity_binding(
        identity.value,
        "implementation_class",
        "CAMPAIGN02_STAGE_RUNNER_IMPLEMENTATION_CLASS_INVALID",
    )
    actual_class = f"{runner.__class__.__module__}.{runner.__class__.__qualname__}"
    if (
        expected["source_class"] in _FORBIDDEN_PRIMARY_SOURCE_CLASSES
        or any(getattr(runner, name, None) != value for name, value in expected.items())
        or actual_class != implementation_class
    ):
        raise _fail("CAMPAIGN02_STAGE_RUNNER_OBJECT_BINDING_MISMATCH")
    stage_identities.verify_files(identity_name, source_root)
    return VerifiedBoundStageRunner(_BOUND_RUNNER_TOKEN, runner)


def verify_bound_stage_gate_finalizer(
    finalizer: IdentityBearingStageGateFinalizer,
    *,
    stage_identities: StageExecutionIdentityManifest,
    source_root: Path,
) -> VerifiedBoundStageGateFinalizer:
    identity = stage_identities.identity("stage_gate_analyzer")
    expected = {
        "identity_id": identity.content_id,
        "role": "STAGE_GATE_ANALYZER",
        "source_commit": stage_identities.source_commit,
        "source_tree": stage_identities.source_tree,
        "environment_id": _identity_binding(
            identity.value, "environment_id", "CAMPAIGN02_STAGE_FINALIZER_ENVIRONMENT_INVALID"
        ),
        "source_class": "MEASURED_CONTROL_PLANE",
        "implementation_id": _identity_binding(
            identity.value, "implementation_id", "CAMPAIGN02_STAGE_FINALIZER_IMPLEMENTATION_INVALID"
        ),
    }
    implementation_class = _identity_binding(
        identity.value,
        "implementation_class",
        "CAMPAIGN02_STAGE_FINALIZER_IMPLEMENTATION_CLASS_INVALID",
    )
    actual_class = f"{finalizer.__class__.__module__}.{finalizer.__class__.__qualname__}"
    if (
        any(getattr(finalizer, name, None) != value for name, value in expected.items())
        or actual_class != implementation_class
    ):
        raise _fail("CAMPAIGN02_STAGE_FINALIZER_OBJECT_BINDING_MISMATCH")
    stage_identities.verify_files("stage_gate_analyzer", source_root)
    return VerifiedBoundStageGateFinalizer(_BOUND_FINALIZER_TOKEN, finalizer)


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
    plan_runner: VerifiedBoundStageRunner,
    gate_finalizer: VerifiedBoundStageGateFinalizer,
) -> StageGateReceipt:
    if completed_stage not in {"STAGE_A_EXACTNESS", "STAGE_C_EMULATED_WAN"}:
        raise _fail("CAMPAIGN02_EXECUTOR_STAGE_INVALID")
    if (
        definition.raw.get("schema_version") != "4.0.0"
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
    expected_evidence_kind = {
        "STAGE_A_EXACTNESS": "SEMANTIC_EXACTNESS_MATRIX",
        "STAGE_C_EMULATED_WAN": "NETWORK_FAULT_EXECUTION",
    }[completed_stage]
    if (
        not isinstance(plan_runner, VerifiedBoundStageRunner)
        or not isinstance(gate_finalizer, VerifiedBoundStageGateFinalizer)
        or runner_id != stage_identities.identity_id(identity_name)
        or plan_runner.identity_id != runner_id
        or plan_runner.role != runner_role
        or plan_runner.source_commit != runtime_lineage.source_commit
        or plan_runner.source_tree != runtime_lineage.source_tree
        or plan_runner.environment_id != runtime_lineage.environment_id
        or gate_finalizer.identity_id != stage_identities.identity_id("stage_gate_analyzer")
        or gate_finalizer.source_commit != runtime_lineage.source_commit
        or gate_finalizer.source_tree != runtime_lineage.source_tree
        or gate_finalizer.environment_id != runtime_lineage.environment_id
    ):
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
            or item.runner_identity_id != plan_runner.identity_id
            or item.runner_role != plan_runner.role
            or item.environment_id != plan_runner.environment_id
            or item.source_class != plan_runner.source_class
            or item.implementation_id != plan_runner.implementation_id
            or item.evidence_kind != expected_evidence_kind
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
        runner_environment_id=plan_runner.environment_id,
        runner_implementation_id=plan_runner.implementation_id,
        runner_role=plan_runner.role,
        runner_source_class=plan_runner.source_class,
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
        runner_environment_id=summary.runner_environment_id,
        runner_implementation_id=summary.runner_implementation_id,
        runner_role=summary.runner_role,
        runner_source_class=summary.runner_source_class,
    )


@dataclass(frozen=True, slots=True)
class NonPrimaryStageAdmissionResult:
    """Test-only authorization result that cannot serialize as a gate receipt."""

    completed_stage: str
    accepted_plan_ids: tuple[str, ...]
    stage_authorization_attestation_id: str


def validate_stage_admission_for_test(
    *,
    completed_stage: str,
    runner_role: str,
    plan_catalog: Campaign02PlanCatalog,
    authorization_proof: StageAuthorizationProof,
    predecessor_gate_receipts: Mapping[str, bytes],
) -> NonPrimaryStageAdmissionResult:
    """Exercise signed admission without executing plans or producing receipt bytes."""
    plans = tuple(item for item in plan_catalog.plans if item.gate_stage == completed_stage)
    if len(plans) != 15:
        raise _fail("CAMPAIGN02_STAGE_EXACT_PLAN_SET_REQUIRED")
    verified = None
    for plan in plans:
        verified = authorize_execution_class(
            authorization_proof,
            plan,
            plan_catalog=cast(Campaign02PlanCatalogView, plan_catalog),
            predecessor_gate_receipts=predecessor_gate_receipts,
            runner_role=runner_role,
        )
    if verified is None:
        raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_PROOF_REQUIRED")
    return NonPrimaryStageAdmissionResult(
        completed_stage=completed_stage,
        accepted_plan_ids=tuple(item.content_id for item in plans),
        stage_authorization_attestation_id=verified.content_id,
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
