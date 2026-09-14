from __future__ import annotations

import base64
import hashlib
import inspect
import struct
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

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
    VECTOR_WIDTH,
    MnistDeltaError,
    contribution_from_summary,
    decode_applied_model,
    expected_central_model,
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


def test_workload_contains_four_independent_negative_model_deltas(tmp_path: Path) -> None:
    summaries = _summaries()
    destination = tmp_path / "workload.bin"
    contributions, workload_id = write_workload(
        summaries,
        _shard_ids(),
        "sha256:" + "a" * 64,
        destination,
    )

    raw = destination.read_bytes()
    assert workload_id == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert raw[:8] == b"DMNIST1\0"
    assert struct.unpack_from(">IIII", raw, 8) == (1, 4, VECTOR_WIDTH, 4)
    assert len(raw) == 8 + 16 + CONTENT_ID_TEXT_BYTES + NODE_COUNT * (
        4 + 8 + CONTENT_ID_TEXT_BYTES + VECTOR_WIDTH * 2
    )
    assert [item.node_index for item in contributions] == [1, 2, 3, 4]
    for item, digits in zip(contributions, ((0, 1, 2), (3, 4, 5), (6, 7), (8, 9)), strict=True):
        for digit in range(DIGIT_COUNT):
            start = digit * PIXELS_PER_DIGIT
            expected = -NODE_COUNT * (digit + 1) if digit in digits else 0
            assert np.all(item.values[start : start + PIXELS_PER_DIGIT] == expected)
            expected_presence = -NODE_COUNT if digit in digits else 0
            assert item.values[DIGIT_COUNT * PIXELS_PER_DIGIT + digit] == expected_presence


def test_local_quantization_uses_integer_half_toward_positive() -> None:
    summary = _summaries()[0]
    sums = summary.sums.copy()
    counts = summary.counts.copy()
    counts[0] = 2
    sums[0] = 3
    changed = _Summary(summary.node_id, counts, sums, summary.summary_id)
    contribution = contribution_from_summary(changed, _shard_ids()[summary.node_id])
    assert np.all(contribution.values[:PIXELS_PER_DIGIT] == -2 * NODE_COUNT)


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
    with pytest.raises(MnistDeltaError, match="NODE_COUNT_INVALID"):
        write_workload(
            _summaries()[:3],
            _shard_ids(),
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
