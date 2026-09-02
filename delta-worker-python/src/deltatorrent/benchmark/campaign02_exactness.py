"""Campaign 02 executable Stage A entrypoint."""

from __future__ import annotations

from deltatorrent.benchmark.campaign02_stage_execution import (
    StageGateFinalizer,
    StagePlanRunner,
    execute_stage,
)


def run_stage_a(
    *,
    definition: object,
    plan_catalog: object,
    authorization_proof: object,
    runtime_lineage: object,
    stage_identities: object,
    plan_runner: StagePlanRunner,
    gate_finalizer: StageGateFinalizer,
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
