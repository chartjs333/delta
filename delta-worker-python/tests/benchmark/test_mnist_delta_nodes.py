from __future__ import annotations

import base64
import hashlib
import inspect
import json
import struct
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

import numpy as np
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark import mnist_delta_nodes
from deltatorrent.benchmark.mnist_delta_nodes import (
    CONTENT_ID_TEXT_BYTES,
    DIGIT_COUNT,
    MODEL_MAGIC,
    NODE_COUNT,
    PIXELS_PER_DIGIT,
    STAGE_C_MNIST_EVENT_ID,
    STAGE_C_MNIST_SEGMENT_ID,
    VECTOR_WIDTH,
    MnistDeltaError,
    decode_applied_model,
    expected_central_model,
    run_stage_c_real_drq1_nodes,
    write_node_contribution,
    write_workload,
)


@dataclass(frozen=True, slots=True)
class _Summary:
    node_id: str
    counts: np.ndarray
    sums: np.ndarray
    summary_id: str


def _summaries() -> tuple[_Summary, ...]:
    ownership = ((0, 1, 2), (3, 4, 5), (6, 7), (8, 9))
    values: list[_Summary] = []
    for index, digits in enumerate(ownership, start=1):
        counts = np.zeros(DIGIT_COUNT, dtype=np.int64)
        sums = np.zeros((DIGIT_COUNT, PIXELS_PER_DIGIT), dtype=np.int64)
        for digit in digits:
            counts[digit] = 3
            sums[digit] = (digit + 1) * 3
        values.append(
            _Summary(
                node_id=f"demo-mnist-worker-{index:02d}",
                counts=counts,
                sums=sums,
                summary_id=f"sha256:{index:064x}",
            )
        )
    return tuple(values)


def _shard_ids() -> dict[str, str]:
    return {
        f"demo-mnist-worker-{index:02d}": f"sha256:{index + 100:064x}"
        for index in range(1, NODE_COUNT + 1)
    }


def _contributions(
    tmp_path: Path, summaries: tuple[_Summary, ...] | None = None
) -> tuple[mnist_delta_nodes.NodeContribution, ...]:
    selected = summaries or _summaries()
    return tuple(
        write_node_contribution(
            summary,
            _shard_ids()[summary.node_id],
            (tmp_path / f"worker-{index:02d}.bin").resolve(),
        )
        for index, summary in enumerate(selected, start=1)
    )


def _values(path: Path) -> np.ndarray:
    offset = 4 + 8 + CONTENT_ID_TEXT_BYTES * 2
    return np.frombuffer(path.read_bytes(), dtype=">i2", offset=offset).astype(np.int16)


@dataclass(frozen=True, slots=True)
class _FakeCausalEvidence:
    next_checkpoint_id: str
    current_pointer_after: str
    current_pointer_before: str
    missing_work_policy_result: str
    isc_ticket_set: tuple[str, ...]
    worker_count_before: int
    worker_count_lost: int


@dataclass(frozen=True, slots=True)
class _FakeTransition:
    event_id: str
    observed_outcome: str
    current_checkpoint_advanced: bool
    causal_evidence: _FakeCausalEvidence


@dataclass(frozen=True, slots=True)
class _FakeReceipt:
    plan_id: str
    fault_transitions: tuple[_FakeTransition, ...]
    native_fault_trace_id: str

    @property
    def raw_java_receipt_id(self) -> str:
        return "sha256:" + "d" * 64


class _FakeStageCBoundary:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def execute(self, **kwargs: object) -> _FakeReceipt:
        self.calls.append(kwargs)
        return _FakeReceipt(
            plan_id=str(kwargs["plan_id"]),
            fault_transitions=(
                _FakeTransition(
                    event_id=STAGE_C_MNIST_EVENT_ID,
                    observed_outcome="APPLIED",
                    current_checkpoint_advanced=True,
                    causal_evidence=_FakeCausalEvidence(
                        next_checkpoint_id="sha256:" + "b" * 64,
                        current_pointer_after="sha256:" + "b" * 64,
                        current_pointer_before="sha256:" + "a" * 64,
                        missing_work_policy_result="FULL_QUORUM_DELIVERED_EXACT_ISC",
                        isc_ticket_set=tuple(f"ticket-{index:03d}" for index in range(4)),
                        worker_count_before=4,
                        worker_count_lost=0,
                    ),
                ),
            ),
            native_fault_trace_id="sha256:" + "c" * 64,
        )


def test_workload_contains_four_independent_negative_model_deltas(tmp_path: Path) -> None:
    summaries = _summaries()
    destination = tmp_path / "workload.bin"
    contributions, workload_id = write_workload(
        _contributions(tmp_path, summaries), "sha256:" + "a" * 64, destination
    )

    raw = destination.read_bytes()
    assert workload_id == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert raw[:8] == b"DMNIST2\0"
    assert struct.unpack_from(">IIII", raw, 8) == (2, 4, VECTOR_WIDTH, 4)
    assert len(raw) == 8 + 16 + CONTENT_ID_TEXT_BYTES + NODE_COUNT * (
        4 + 8 + CONTENT_ID_TEXT_BYTES * 2 + VECTOR_WIDTH * 2
    )
    assert [item.node_index for item in contributions] == [1, 2, 3, 4]
    for item, digits in zip(contributions, ((0, 1, 2), (3, 4, 5), (6, 7), (8, 9)), strict=True):
        values = _values(item.record_path)
        for digit in range(DIGIT_COUNT):
            start = digit * PIXELS_PER_DIGIT
            expected = -NODE_COUNT * (digit + 1) if digit in digits else 0
            assert np.all(values[start : start + PIXELS_PER_DIGIT] == expected)
            expected_presence = -NODE_COUNT if digit in digits else 0
            assert values[DIGIT_COUNT * PIXELS_PER_DIGIT + digit] == expected_presence


def test_stage_c_real_drq1_runner_stages_four_worker_shards(tmp_path: Path) -> None:
    boundary = _FakeStageCBoundary()
    contributions = _contributions(tmp_path / "workers")

    result = run_stage_c_real_drq1_nodes(
        Path(__file__).resolve().parents[3],
        tmp_path / "stagec",
        contributions,
        "sha256:" + "a" * 64,
        boundary=boundary,  # type: ignore[arg-type]
    )

    assert len(boundary.calls) == 1
    call = boundary.calls[0]
    worker_shards = cast(dict[str, bytes], call["worker_shards"])
    manifest = cast(dict[str, object], call["shards_manifest"])
    fault_profile = call["fault_profile"]
    assert sorted(worker_shards) == [f"ticket-{index:03d}" for index in range(4)]
    assert all(payload.startswith(b"DRQ1") for payload in worker_shards.values())
    assert manifest == {
        "element_count": VECTOR_WIDTH,
        "element_start": 0,
        "formal_semantics_id": mnist_delta_nodes.FORMAL_SEMANTICS_ID,
        "ordinal": 0,
        "parameter_schema_id": mnist_delta_nodes.STAGE_C_MNIST_PARAMETER_SCHEMA_ID,
        "profile_id": mnist_delta_nodes.STAGE_C_MNIST_ARITHMETIC_PROFILE_ID,
        "proof_instance_id": mnist_delta_nodes.STAGE_C_MNIST_PROOF_INSTANCE_ID,
        "round_config_id": mnist_delta_nodes.STAGE_C_MNIST_ROUND_CONFIG_ID,
        "scale_table_id": mnist_delta_nodes.STAGE_C_MNIST_SCALE_TABLE_ID,
        "segment_id": STAGE_C_MNIST_SEGMENT_ID,
        "segment_offset": 0,
        "shard_plan_id": mnist_delta_nodes.STAGE_C_MNIST_SHARD_PLAN_ID,
    }
    assert fault_profile.events[0].event_id == STAGE_C_MNIST_EVENT_ID
    assert result.final_checkpoint_id == result.evaluation_checkpoint_id
    assert result.ticket_ids == tuple(f"ticket-{index:03d}" for index in range(4))
    assert len(result.worker_shard_leaf_ids) == 4
    assert result.evidence["python_cross_node_aggregation_performed"] is False
    assert result.evidence["synthetic_contribution_fallback_allowed"] is False
    assert result.evidence["single_shard_scope"] is True
    loaded = json.loads(result.evidence_path.read_text(encoding="utf-8"))
    assert loaded == result.evidence


def test_local_quantization_uses_integer_half_toward_positive(tmp_path: Path) -> None:
    summary = _summaries()[0]
    sums = summary.sums.copy()
    counts = summary.counts.copy()
    counts[0] = 2
    sums[0] = 3
    changed = _Summary(summary.node_id, counts, sums, summary.summary_id)
    contribution = write_node_contribution(
        changed,
        _shard_ids()[summary.node_id],
        (tmp_path / "contribution.bin").resolve(),
    )
    assert np.all(_values(contribution.record_path)[:PIXELS_PER_DIGIT] == -2 * NODE_COUNT)


def test_expected_central_model_is_independent_positive_reference() -> None:
    sums = np.zeros((DIGIT_COUNT, PIXELS_PER_DIGIT), dtype=np.int64)
    counts = np.full(DIGIT_COUNT, 2, dtype=np.int64)
    for digit in range(DIGIT_COUNT):
        sums[digit] = 2 * (digit + 1)
    values = expected_central_model(sums, counts)
    assert np.array_equal(
        values[: DIGIT_COUNT * PIXELS_PER_DIGIT].reshape(DIGIT_COUNT, PIXELS_PER_DIGIT)[:, 0],
        np.arange(1, 11, dtype=np.int16),
    )
    assert np.all(values[DIGIT_COUNT * PIXELS_PER_DIGIT :] == 1)


def test_applied_model_decoder_binds_exact_native_bytes(tmp_path: Path) -> None:
    values = np.zeros(VECTOR_WIDTH, dtype=np.int16)
    values[: DIGIT_COUNT * PIXELS_PER_DIGIT] = 7
    values[DIGIT_COUNT * PIXELS_PER_DIGIT :] = 1
    raw = MODEL_MAGIC + struct.pack(">I", VECTOR_WIDTH) + values.astype(">i2").tobytes()
    path = tmp_path / "applied-model.bin"
    path.write_bytes(raw)

    model = decode_applied_model(path)

    assert model.raw_bytes == raw
    assert model.centroids.shape == (DIGIT_COUNT, PIXELS_PER_DIGIT)
    assert np.all(model.centroids == 7)
    assert np.all(model.presence == 1)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda raw: raw[:-1],
        lambda raw: b"NOTMODEL" + raw[8:],
        lambda raw: raw[:8] + struct.pack(">I", VECTOR_WIDTH - 1) + raw[12:],
    ),
)
def test_applied_model_decoder_rejects_mutated_native_bytes(
    tmp_path: Path, mutation: Callable[[bytes], bytes]
) -> None:
    values = np.zeros(VECTOR_WIDTH, dtype=np.int16)
    raw = MODEL_MAGIC + struct.pack(">I", VECTOR_WIDTH) + values.astype(">i2").tobytes()
    path = tmp_path / "applied-model.bin"
    path.write_bytes(mutation(raw))
    with pytest.raises(MnistDeltaError, match=r"APPLIED_MODEL|APPLIED_MODEL_WIDTH"):
        decode_applied_model(path)


def test_missing_node_is_rejected_before_any_native_execution(tmp_path: Path) -> None:
    contributions = _contributions(tmp_path)
    with pytest.raises(MnistDeltaError, match="NODE_COUNT_INVALID"):
        write_workload(
            contributions[:3],
            "sha256:" + "a" * 64,
            tmp_path / "workload.bin",
        )


def test_demo_integration_module_defines_no_cross_node_aggregate_function() -> None:
    source = inspect.getsource(mnist_delta_nodes)
    assert "aggregate_summaries" not in source
    assert "Python fallback" not in source
    assert "delta::robust::reduce_parameter_shard" in source


def _relay_signers() -> tuple[tuple[str, Ed25519PrivateKey], ...]:
    values = []
    for _index in range(NODE_COUNT):
        key = Ed25519PrivateKey.generate()
        public = key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        values.append((base64.b64encode(public).decode("ascii"), key))
    return tuple(values)


def test_relay_preflight_rejects_duplicate_source_before_java(tmp_path: Path) -> None:
    source = (tmp_path / "source.bin").resolve()
    source.write_bytes(b"one")
    entries = (
        mnist_delta_nodes._RelayEntry(source, PurePosixPath("a.bin"), 0),
        mnist_delta_nodes._RelayEntry(source, PurePosixPath("b.bin"), 1),
    )
    toolchain = mnist_delta_nodes.DeltaToolchain(source, source, str(source))
    with pytest.raises(MnistDeltaError, match="SOURCE_DUPLICATE"):
        mnist_delta_nodes._run_relay(
            toolchain,
            _relay_signers(),
            entries,
            (tmp_path / "output").resolve(),
            (tmp_path / "evidence").resolve(),
            "duplicate-source",
        )


def test_action_only_forged_transport_trace_is_rejected(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    actions = (
        "SOURCE_VERIFIED",
        "NETTY_TRANSMITTED",
        "NETTY_RECEIVED",
        "ATOMIC_WRITE_VERIFIED",
    )
    trace.write_text(
        "".join(f'{{"action":"{action}"}}\n' for action in actions),
        encoding="utf-8",
    )
    expected = (
        {
            "content_id": "sha256:" + "a" * 64,
            "destination": "payload.bin",
            "size_bytes": 3,
        },
    )
    with pytest.raises(MnistDeltaError, match="TRACE_INVALID"):
        mnist_delta_nodes._validate_relay_trace(trace, expected, 123)
