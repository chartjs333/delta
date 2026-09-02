"""Campaign 02 executable Stage C network/fault entrypoint."""

from __future__ import annotations

from collections.abc import Mapping

from deltatorrent.benchmark.campaign02_stage_execution import (
    StageGateFinalizer,
    StagePlanRunner,
    execute_stage,
)


def run_stage_c(
    *,
    definition: object,
    plan_catalog: object,
    authorization_proof: object,
    predecessor_gate_receipts: Mapping[str, bytes],
    runtime_lineage: object,
    stage_identities: object,
    plan_runner: StagePlanRunner,
    gate_finalizer: StageGateFinalizer,
) -> object:
    """Execute exactly the authorized 15-plan Stage C matrix after Stage A and B PASS."""
    return execute_stage(
        completed_stage="STAGE_C_EMULATED_WAN",
        runner_role="NETWORK_FAULT_RUNNER",
        definition=definition,  # type: ignore[arg-type]
        plan_catalog=plan_catalog,  # type: ignore[arg-type]
        authorization_proof=authorization_proof,  # type: ignore[arg-type]
        predecessor_gate_receipts=predecessor_gate_receipts,
        runtime_lineage=runtime_lineage,  # type: ignore[arg-type]
        stage_identities=stage_identities,  # type: ignore[arg-type]
        plan_runner=plan_runner,
        gate_finalizer=gate_finalizer,
    )
