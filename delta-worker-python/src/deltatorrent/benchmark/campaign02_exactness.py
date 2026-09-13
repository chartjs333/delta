"""Campaign 02 executable Stage A entrypoint."""

from __future__ import annotations

from deltatorrent.benchmark.campaign02 import CampaignExecutionPlan
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.campaign02_stage_a_evidence import (
    StageASemanticEvidenceSummary,
)
from deltatorrent.benchmark.campaign02_stage_execution import (
    StagePlanEvidence,
    VerifiedBoundStageGateFinalizer,
    VerifiedBoundStageRunner,
    execute_stage,
)


class Campaign02ExactnessEvidenceRunner:
    """Replay only plan records backed by a semantically verified seven-lane matrix."""

    def __init__(
        self,
        *,
        evidence: tuple[StagePlanEvidence, ...],
        semantic_summary: StageASemanticEvidenceSummary,
        stage_identities: StageExecutionIdentityManifest,
    ) -> None:
        identity = stage_identities.identity("exactness_runner")
        self.identity_id = identity.content_id
        self.role = str(identity.value.get("role", ""))
        self.source_commit = stage_identities.source_commit
        self.source_tree = stage_identities.source_tree
        self.environment_id = str(identity.value.get("environment_id", ""))
        self.source_class = str(identity.value.get("source_class", ""))
        self.implementation_id = str(identity.value.get("implementation_id", ""))
        self._evidence = {item.plan_id: item for item in evidence}
        raw_ids = tuple(item.raw_digest for item in semantic_summary.artifacts)
        if (
            len(self._evidence) != len(evidence)
            or len(evidence) != 15
            or any(
                item.runner_identity_id != self.identity_id
                or item.runner_id != self.identity_id
                or item.runner_role != self.role
                or item.source_commit != self.source_commit
                or item.source_tree != self.source_tree
                or item.environment_id != self.environment_id
                or item.source_class != self.source_class
                or item.implementation_id != self.implementation_id
                or item.evidence_kind != "SEMANTIC_EXACTNESS_MATRIX"
                or item.evidence_ids != raw_ids
                or item.verified_summary_ids != (semantic_summary.content_id,)
                for item in evidence
            )
        ):
            raise ValueError("CAMPAIGN02_STAGE_A_EVIDENCE_BINDING_INVALID")

    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence:
        try:
            return self._evidence[plan.content_id]
        except KeyError as exc:
            raise ValueError("CAMPAIGN02_STAGE_A_EVIDENCE_MISSING") from exc


def run_stage_a(
    *,
    definition: object,
    plan_catalog: object,
    authorization_proof: object,
    runtime_lineage: object,
    stage_identities: object,
    plan_runner: VerifiedBoundStageRunner,
    gate_finalizer: VerifiedBoundStageGateFinalizer,
) -> object:
    """Execute exactly the authorized 15-plan Stage A matrix and emit its typed receipt."""
    return execute_stage(
        completed_stage="STAGE_A_EXACTNESS",
        runner_role="EXACTNESS_RUNNER",
        definition=definition,  # type: ignore[arg-type]
        plan_catalog=plan_catalog,  # type: ignore[arg-type]
        authorization_proof=authorization_proof,  # type: ignore[arg-type]
        predecessor_gate_receipts={},
        runtime_lineage=runtime_lineage,  # type: ignore[arg-type]
        stage_identities=stage_identities,  # type: ignore[arg-type]
        plan_runner=plan_runner,
        gate_finalizer=gate_finalizer,
    )
