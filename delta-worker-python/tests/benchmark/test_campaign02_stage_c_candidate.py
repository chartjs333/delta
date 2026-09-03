from __future__ import annotations

import subprocess
from pathlib import Path

from deltatorrent.benchmark.campaign02_stage_c_candidate import build_candidate_catalog
from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredStageCRuntimeBoundary,
    RuntimeArtifact,
)
from deltatorrent.protocol.canonical import sha256_content_id

ROOT = Path(__file__).resolve().parents[3]


def _artifact(relative: str) -> RuntimeArtifact:
    path = ROOT / relative
    return RuntimeArtifact(path, sha256_content_id(path.read_bytes()))


def test_candidate_compiles_exact_stage_c_catalog_without_execution_authority(
    tmp_path: Path,
) -> None:
    boundary = MeasuredStageCRuntimeBoundary(
        image_id=sha256_content_id(b"candidate-image"),
        java_executable=_artifact("pyproject.toml"),
        native_executable=_artifact("CMakeLists.txt"),
        transport_harness=_artifact("uv.lock"),
        netty_artifacts=(_artifact("README.md"),),
        os_interface_counter_root=tmp_path,
        working_root=tmp_path / "unused",
    )
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    source_tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
    ).strip()
    candidate = build_candidate_catalog(
        source_root=ROOT,
        source_commit=source_commit,
        source_tree=source_tree,
        boundary=boundary,
    )
    plans = tuple(
        plan for plan in candidate.catalog.plans if plan.gate_stage == "STAGE_C_EMULATED_WAN"
    )

    assert len(plans) == len({plan.content_id for plan in plans}) == 15
    assert candidate.stage_identities.schema_version == "4.0.0"
    assert candidate.runtime_lineage.schema_version == "5.0.0"
    assert all(
        plan.runner_id == candidate.runtime_lineage.network_fault_runner_id for plan in plans
    )
    assert all(plan.execution_authorization_id is None for plan in plans)
    assert len(candidate.compiler_signature_ids) == 3
