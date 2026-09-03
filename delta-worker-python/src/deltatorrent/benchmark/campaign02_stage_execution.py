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
from deltatorrent.benchmark.campaign02_bootstrap import (
    BootstrapRuntimeProvenance,
    VerifiedBootstrapMapping,
    WorkflowRegistrationReceipt,
    verify_bootstrap_runtime,
    verify_registration_receipt,
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
    bootstrap_mapping_id: str

    def finalize(self, summary: StageExecutionSummary) -> StageGateFinalization: ...


_BOUND_RUNNER_TOKEN: Final = object()
_BOUND_FINALIZER_TOKEN: Final = object()
_FORBIDDEN_PRIMARY_SOURCE_CLASSES: Final = frozenset(
    {"CALLER_SUPPLIED", "DRY", "FIXTURE", "NON_PRIMARY_FIXTURE", "SIMULATED_ONLY", "SYNTHETIC"}
)


class VerifiedBoundStageRunner:
    """Opaque production wrapper returned only after recursive identity verification."""

    __slots__ = (
        "_runner",
        "environment_id",
        "identity_id",
        "image_id",
        "implementation_id",
        "java_executable_id",
        "native_executable_id",
        "netty_artifact_ids",
        "role",
        "source_class",
        "source_commit",
        "source_tree",
        "transport_harness_id",
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
        self.image_id = getattr(runner, "image_id", None)
        self.java_executable_id = getattr(runner, "java_executable_id", None)
        self.native_executable_id = getattr(runner, "native_executable_id", None)
        self.transport_harness_id = getattr(runner, "transport_harness_id", None)
        self.netty_artifact_ids = tuple(getattr(runner, "netty_artifact_ids", ()))

    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence:
        return self._runner.execute(plan)


class VerifiedBoundStageGateFinalizer:
    """Opaque gate-finalizer wrapper bound to the manifest's analyzer identity."""

    __slots__ = (
        "_finalizer",
        "bootstrap_mapping_id",
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
        self.bootstrap_mapping_id = getattr(finalizer, "bootstrap_mapping_id", None)
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
    """Source-bound finalizer for mapped bootstrap, checkout and artifact provenance."""

    @dataclass(frozen=True, slots=True)
    class Artifact:
        name: str
        artifact_id: int
        digest: str
        content_digest: str
        workflow_run_id: int
        workflow_run_attempt: int
        origin_class: str

        def __post_init__(self) -> None:
            if (
                not self.name
                or isinstance(self.artifact_id, bool)
                or not isinstance(self.artifact_id, int)
                or self.artifact_id <= 0
                or _CONTENT_ID.fullmatch(self.digest) is None
                or _CONTENT_ID.fullmatch(self.content_digest) is None
                or self.workflow_run_id <= 0
                or self.workflow_run_attempt <= 0
                or self.origin_class
                not in {"AUTHORITY_RUN", "BOOTSTRAP_REGISTRATION_RUN", "CURRENT_STAGE_RUN"}
            ):
                raise _fail("CAMPAIGN02_STAGE_WORKFLOW_ARTIFACT_INVALID")

    def __init__(
        self,
        *,
        stage_identities: StageExecutionIdentityManifest,
        finalized_at: datetime,
        bootstrap_mapping: VerifiedBootstrapMapping,
        registration_receipt: WorkflowRegistrationReceipt,
        provenance: BootstrapRuntimeProvenance,
        authority_artifact: Artifact,
        input_artifacts: tuple[Artifact, ...],
        output_artifacts: tuple[Artifact, ...],
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
        self.bootstrap_mapping = bootstrap_mapping
        self.bootstrap_mapping_id = bootstrap_mapping.mapping.content_id
        self.registration_receipt = registration_receipt
        self.provenance = provenance
        self.authority_artifact = authority_artifact
        self.input_artifacts = tuple(sorted(input_artifacts, key=lambda item: item.name))
        self.output_artifacts = tuple(sorted(output_artifacts, key=lambda item: item.name))
        self.document: dict[str, object] | None = None
        workflow_hashes = identity.value.get("workflow_hashes")
        source_workflow_ids = (
            {
                item.get("content_id")
                for item in workflow_hashes
                if isinstance(item, dict)
                and item.get("path") == bootstrap_mapping.mapping.source_stage_a_workflow_path
            }
            if isinstance(workflow_hashes, list)
            else set()
        )
        verify_bootstrap_runtime(bootstrap_mapping, provenance)
        verify_registration_receipt(bootstrap_mapping, registration_receipt)
        artifacts = (*self.input_artifacts, *self.output_artifacts)
        artifact_coordinates: dict[int, tuple[str, int, int, str]] = {}
        artifact_coordinate_conflict = False
        for item in artifacts:
            coordinate = (
                item.digest,
                item.workflow_run_id,
                item.workflow_run_attempt,
                item.origin_class,
            )
            previous = artifact_coordinates.setdefault(item.artifact_id, coordinate)
            artifact_coordinate_conflict |= previous != coordinate
        if (
            stage_identities.schema_version != "4.0.0"
            or finalized_at.tzinfo is None
            or bootstrap_mapping.mapping.qualified_source_commit != self.source_commit
            or bootstrap_mapping.mapping.qualified_source_tree != self.source_tree
            or bootstrap_mapping.mapping.source_stage_a_workflow_content_id
            not in source_workflow_ids
            or provenance.workflow_id != registration_receipt.workflow_id
            or not self.input_artifacts
            or not self.output_artifacts
            or authority_artifact not in self.input_artifacts
            or authority_artifact.origin_class != "AUTHORITY_RUN"
            or sum(item.origin_class == "AUTHORITY_RUN" for item in self.input_artifacts) != 1
            or not any(
                item.origin_class == "BOOTSTRAP_REGISTRATION_RUN" for item in self.input_artifacts
            )
            or not any(item.origin_class == "CURRENT_STAGE_RUN" for item in self.input_artifacts)
            or any(item.origin_class != "CURRENT_STAGE_RUN" for item in self.output_artifacts)
            or len({item.name for item in artifacts}) != len(artifacts)
            or artifact_coordinate_conflict
            or any(
                item.workflow_run_id != provenance.run_id
                or item.workflow_run_attempt != provenance.run_attempt
                for item in artifacts
                if item.origin_class == "CURRENT_STAGE_RUN"
            )
        ):
            raise _fail("CAMPAIGN02_STAGE_WORKFLOW_PROVENANCE_INVALID")

    def finalize(self, summary: StageExecutionSummary) -> StageGateFinalization:
        if (
            summary.gate_analyzer_id != self.identity_id
            or summary.source_commit != self.bootstrap_mapping.mapping.qualified_source_commit
            or summary.source_tree != self.bootstrap_mapping.mapping.qualified_source_tree
            or summary.runner_environment_id != self.environment_id
        ):
            raise _fail("CAMPAIGN02_STAGE_GATE_FINALIZER_SUMMARY_MISMATCH")
        self.document = {
            "authority_artifact_digest": self.authority_artifact.digest,
            "authority_artifact_content_digest": self.authority_artifact.content_digest,
            "authority_artifact_id": self.authority_artifact.artifact_id,
            "bootstrap_mapping_attestation_id": self.bootstrap_mapping.content_id,
            "bootstrap_mapping_id": self.bootstrap_mapping.mapping.content_id,
            "decision": "PASS",
            "dispatch_ref": self.provenance.dispatch_ref,
            "event_name": self.provenance.event_name,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_analyzer_id": summary.gate_analyzer_id,
            "gate_result_id": summary.content_id,
            "github_sha": self.provenance.github_sha,
            "input_artifact_digests": {item.name: item.digest for item in self.input_artifacts},
            "input_artifact_content_digests": {
                item.name: item.content_digest for item in self.input_artifacts
            },
            "input_artifact_ids": {item.name: item.artifact_id for item in self.input_artifacts},
            "input_artifact_origins": {
                item.name: item.origin_class for item in self.input_artifacts
            },
            "input_artifact_run_attempts": {
                item.name: item.workflow_run_attempt for item in self.input_artifacts
            },
            "input_artifact_run_ids": {
                item.name: item.workflow_run_id for item in self.input_artifacts
            },
            "output_artifact_digests": {item.name: item.digest for item in self.output_artifacts},
            "output_artifact_content_digests": {
                item.name: item.content_digest for item in self.output_artifacts
            },
            "output_artifact_ids": {item.name: item.artifact_id for item in self.output_artifacts},
            "output_artifact_origins": {
                item.name: item.origin_class for item in self.output_artifacts
            },
            "output_artifact_run_attempts": {
                item.name: item.workflow_run_attempt for item in self.output_artifacts
            },
            "output_artifact_run_ids": {
                item.name: item.workflow_run_id for item in self.output_artifacts
            },
            "plan_evidence_ids": list(summary.plan_evidence_ids),
            "qualified_source_commit": self.bootstrap_mapping.mapping.qualified_source_commit,
            "qualified_source_tree": self.bootstrap_mapping.mapping.qualified_source_tree,
            "registration_receipt_id": self.registration_receipt.content_id,
            "repository": self.provenance.repository,
            "runner_id": summary.runner_id,
            "run_attempt": self.provenance.run_attempt,
            "run_id": self.provenance.run_id,
            "schema_version": "3.0.0",
            "source_commit": summary.source_commit,
            "source_stage_a_workflow_content_id": (
                self.bootstrap_mapping.mapping.source_stage_a_workflow_content_id
            ),
            "source_tree": summary.source_tree,
            "type_name": "CAMPAIGN02_STAGE_WORKFLOW_GATE_QC",
            "workflow_blob_id": self.provenance.workflow_blob_id,
            "workflow_content_id": self.provenance.workflow_content_id,
            "workflow_id": self.provenance.workflow_id,
            "workflow_path": self.provenance.workflow_path,
            "workflow_ref": self.provenance.workflow_ref,
            "workflow_sha": self.provenance.workflow_sha,
        }
        return StageGateFinalization(
            gate_result_id=summary.content_id,
            gate_qc_id=sha256_content_id(
                b"deltareduce.010.campaign02-stage-workflow-gate-qc.v3\0"
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


def _identity_string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return ()
    return tuple(value)


def verify_bound_stage_runner(
    runner: IdentityBearingStagePlanRunner,
    *,
    identity_name: str,
    stage_identities: StageExecutionIdentityManifest,
    source_root: Path,
) -> VerifiedBoundStageRunner:
    """Bind a concrete production runner to immutable manifest bytes before execution."""
    if stage_identities.schema_version not in {"3.0.0", "4.0.0"}:
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
    measured_boundary_mismatch = False
    if identity_name == "network_fault_runner" and stage_identities.schema_version == "4.0.0":
        measured_boundary_mismatch = any(
            getattr(runner, field, None) != identity.value.get(field)
            for field in (
                "image_id",
                "java_executable_id",
                "native_executable_id",
                "transport_harness_id",
            )
        ) or tuple(getattr(runner, "netty_artifact_ids", ())) != _identity_string_list(
            identity.value.get("netty_artifact_ids")
        )
    if (
        expected["source_class"] in _FORBIDDEN_PRIMARY_SOURCE_CLASSES
        or any(getattr(runner, name, None) != value for name, value in expected.items())
        or actual_class != implementation_class
        or measured_boundary_mismatch
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
        definition.raw.get("schema_version") not in {"4.0.0", "5.0.0"}
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
        or (
            definition.raw.get("schema_version") == "5.0.0"
            and definition.bootstrap_mapping_id != gate_finalizer.bootstrap_mapping_id
        )
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
    stage_c_boundary_mismatch = False
    if completed_stage == "STAGE_C_EMULATED_WAN":
        network_identity = stage_identities.identity("network_fault_runner").value
        stage_c_boundary_mismatch = (
            definition.raw.get("schema_version") != "5.0.0"
            or stage_identities.schema_version != "4.0.0"
            or runtime_lineage.schema_version != "5.0.0"
            or runtime_lineage.image_id != network_identity.get("image_id")
            or runtime_lineage.java_executable_id != network_identity.get("java_executable_id")
            or runtime_lineage.native_executable_id != network_identity.get("native_executable_id")
            or runtime_lineage.transport_harness_id != network_identity.get("transport_harness_id")
            or runtime_lineage.netty_artifact_ids
            != _identity_string_list(network_identity.get("netty_artifact_ids"))
            or plan_runner.image_id != runtime_lineage.image_id
            or plan_runner.java_executable_id != runtime_lineage.java_executable_id
            or plan_runner.native_executable_id != runtime_lineage.native_executable_id
            or plan_runner.transport_harness_id != runtime_lineage.transport_harness_id
            or plan_runner.netty_artifact_ids != runtime_lineage.netty_artifact_ids
            or any(
                item.image_id != runtime_lineage.image_id
                or item.java_executable_id != runtime_lineage.java_executable_id
                or item.native_executable_id != runtime_lineage.native_executable_id
                or item.transport_harness_id != runtime_lineage.transport_harness_id
                or item.netty_artifact_ids != runtime_lineage.netty_artifact_ids
                for item in plans
            )
        )
    if (
        len(plans) != 15
        or len(required_plan_ids) != 15
        or tuple(item.content_id for item in plans) != required_plan_ids
        or any(item.runner_id != runner_id for item in plans)
        or stage_c_boundary_mismatch
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
