from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
from deltatorrent.benchmark.campaign02_demo_controllers import (
    generate_demo_controller_bundle,
)
from deltatorrent.benchmark.mnist_delta_nodes import (
    DIGIT_COUNT,
    NODE_COUNT,
    PIXELS_PER_DIGIT,
    VECTOR_WIDTH,
    run_delta_nodes,
)


@dataclass(frozen=True, slots=True)
class _Summary:
    node_id: str
    counts: np.ndarray
    sums: np.ndarray
    summary_id: str


def _node_local_summaries() -> tuple[_Summary, ...]:
    ownership = ((0, 1, 2), (3, 4, 5), (6, 7), (8, 9))
    summaries: list[_Summary] = []
    for node_index, digits in enumerate(ownership, start=1):
        counts = np.zeros(DIGIT_COUNT, dtype=np.int64)
        sums = np.zeros((DIGIT_COUNT, PIXELS_PER_DIGIT), dtype=np.int64)
        for digit in digits:
            counts[digit] = 3
            sums[digit] = (digit + 1) * 3
        summaries.append(
            _Summary(
                node_id=f"demo-mnist-worker-{node_index:02d}",
                counts=counts,
                sums=sums,
                summary_id=f"sha256:{node_index:064x}",
            )
        )
    return tuple(summaries)


@pytest.mark.skipif(
    os.environ.get("DELTA_MNIST_E2E") != "1",
    reason="requires the compiled native node and JDK 25 Netty relay",
)
def test_real_delta_path_reaches_applied_without_demo_aggregation(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    controllers = tmp_path / "controllers"
    generate_demo_controller_bundle(controllers)
    summaries = _node_local_summaries()
    shard_ids = {
        item.node_id: f"sha256:{index + 100:064x}" for index, item in enumerate(summaries, start=1)
    }

    result = run_delta_nodes(
        repository_root,
        tmp_path / "delta-execution",
        controllers,
        summaries,
        shard_ids,
        "sha256:" + "a" * 64,
    )

    expected = np.zeros(VECTOR_WIDTH, dtype=np.int16)
    for digit in range(DIGIT_COUNT):
        start = digit * PIXELS_PER_DIGIT
        expected[start : start + PIXELS_PER_DIGIT] = digit + 1
    expected[DIGIT_COUNT * PIXELS_PER_DIGIT :] = 1
    assert np.array_equal(result.applied_model.values, expected)

    trace = json.loads(result.execution_trace_path.read_text(encoding="utf-8"))
    assert trace["terminal_outcome"] == "APPLIED"
    assert trace["python_cross_node_aggregation_performed"] is False
    assert trace["aggregation_authority"] == "delta::robust::reduce_parameter_shard"
    assert [component["component"] for component in trace["components"]] == [
        "deltatorrent.benchmark.mnist_demo",
        "io.deltareduce.demo.MnistDeltaNettyRelay",
        "delta::runtime::CertificateVoteRuntime",
        "delta::certificates::ChainVerifier",
        "delta::robust::build_plan",
        "delta::robust::reduce_parameter_shard",
        "delta::apply::compute_candidate",
        "delta::runtime::CurrentPointerStore",
        "deltatorrent.benchmark.mnist_demo.evaluate_centroid_model",
    ]
    certificates = result.delta_execution["quorum_certificates"]
    assert [certificate["kind"] for certificate in certificates] == [
        "input_set",
        "eligibility",
        "aggregation_plan",
        "parameter_shard",
        "aggregate_root",
        "apply",
    ]
    assert all(certificate["signer_count"] == NODE_COUNT for certificate in certificates)
    assert all(certificate["threshold"] == 3 for certificate in certificates)
    assert result.failure_simulation["status"] == "RECOVERED_AND_APPLIED"
    assert result.failure_simulation["replay_observed"] is True
    assert result.failure_simulation["terminal_outcome"] == "APPLIED"

    evidence_value = os.environ.get("DELTA_MNIST_E2E_EVIDENCE_DIR")
    if evidence_value:
        evidence_dir = Path(evidence_value).resolve()
        evidence_dir.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(result.execution_trace_path, evidence_dir / "execution-trace.json")
        shutil.copyfile(result.execution_diagram_path, evidence_dir / "execution-path.mmd")
