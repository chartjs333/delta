from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from deltatorrent.benchmark.campaign02_stage_c_runtime import _parse_receipt
from deltatorrent.benchmark.qlora_delta_e2e import (
    NODE_COUNT,
    QLORA_EVENT_ID,
    QLORA_QUANTUM_DENOMINATOR,
    QloraDeltaE2EError,
    _canonical_bytes,
    _fault_profile,
    _initial_adapter_arrays,
    _network_profiles,
    _run_central_baseline,
    _shards_manifest,
    _split_adapter_values,
    _stagec_values_hash,
    _worker_batches,
    _write_worker_contribution,
    run_qlora_delta_e2e,
    run_qlora_training_quality,
)
from deltatorrent.protocol.canonical import sha256_content_id

PROFILE_DOMAIN = b"deltareduce.010.stagec-java-transport-receipt.v1\0"


def _round_half_toward_positive(numerator: int, denominator: int) -> int:
    if numerator >= 0:
        quotient, remainder = divmod(numerator, denominator)
        return quotient + (1 if remainder >= denominator - remainder else 0)
    magnitude = -numerator
    quotient, remainder = divmod(magnitude, denominator)
    truncated = -quotient
    if remainder == 0 or remainder <= denominator - remainder:
        return truncated
    return truncated - 1


def _stage_values_from_workers(workers) -> tuple[int, ...]:
    stage_values: list[int] = []
    for coordinate in range(8):
        code = _round_half_toward_positive(
            workers[0].stage_c_q_values[coordinate] + workers[1].stage_c_q_values[coordinate],
            4,
        )
        text = _round_half_toward_positive(
            workers[2].stage_c_q_values[coordinate] + workers[3].stage_c_q_values[coordinate],
            4,
        )
        stage_values.append(-(code + text))
    return tuple(stage_values)


def _expected_round_values(tmp_path: Path, rounds: int) -> list[tuple[int, ...]]:
    parent = _initial_adapter_arrays()
    expected: list[tuple[int, ...]] = []
    for round_index in range(rounds):
        workers = tuple(
            _write_worker_contribution(
                index,
                batch,
                tmp_path / "expected" / f"round-{round_index:03d}",
                parent_adapters=parent,
                round_index=round_index,
            )
            for index, batch in enumerate(_worker_batches())
        )
        values = _stage_values_from_workers(workers)
        expected.append(values)
        parent_flat = np.concatenate(
            [parent[name].reshape(-1) for name in ("model.layer0.lora_A", "model.layer0.lora_B")]
        ) + (np.asarray(values, dtype=np.float64) / QLORA_QUANTUM_DENOMINATOR)
        parent = _split_adapter_values(parent_flat)
    return expected


def test_qlora_workers_emit_adapter_only_single_shard_drq1(tmp_path: Path) -> None:
    workers = tuple(
        _write_worker_contribution(index, batch, tmp_path)
        for index, batch in enumerate(_worker_batches())
    )

    assert len(workers) == NODE_COUNT
    assert {worker.domain_id for worker in workers} == {"code", "text"}
    for worker in workers:
        assert worker.training_result.status == "COMPLETE"
        assert worker.training_result.base_hash_before == worker.training_result.base_hash_after
        assert worker.produced.total_elements == 8
        assert len(worker.produced.shards) == 1
        assert worker.produced.commitment_root == worker.leaf_id
        assert worker.stage_c_q_values == tuple(-value for value in worker.worker_adapter_q_values)


def test_tiny_qlora_central_baseline_matches_stagec_integer_profile(tmp_path: Path) -> None:
    workers = tuple(
        _write_worker_contribution(index, batch, tmp_path)
        for index, batch in enumerate(_worker_batches())
    )
    _central, central_q_values, _metrics = _run_central_baseline()

    # REAL_DRQ1 identity adapter profile applies next_model = -(code + text).
    assert _stage_values_from_workers(workers) == central_q_values


def _receipt(plan_id: str, next_values: tuple[int, ...]) -> bytes:
    network_profiles = _network_profiles()
    fault_profile = _fault_profile()
    profile = network_profiles[0][1]
    profile_line = " ".join(
        (
            "PROFILE",
            profile.profile_id,
            "10",
            "10000",
            "10",
            "10000",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "10",
            "10000",
            "10000",
            "1000",
            "12000",
            "11000",
            "2000",
            "13000",
            "11000",
        )
    )
    profile_receipt = sha256_content_id(PROFILE_DOMAIN + profile_line.encode("ascii"))
    next_checkpoint = _stagec_values_hash(next_values)
    native_trace = b"1|ACT-QLORA|state|effect|APPLIED\n"
    fields = {
        "abort_qc_id": "NONE",
        "aggregate_root_qc_id": "sha256:" + "1" * 64,
        "aggregate_root_qc_tick": "122",
        "apply_qc_id": "sha256:" + "3" * 64,
        "apply_qc_tick": "132",
        "apply_quorum_threshold": "3",
        "apply_validator_set_id": "sha256:" + "4" * 64,
        "apply_work_item_id": "sha256:" + "2" * 64,
        "causal_transport_receipt_id": "sha256:" + "5" * 64,
        "certified_abort_tick": "0",
        "current_checkpoint_advanced": "true",
        "current_pointer_after": next_checkpoint,
        "current_pointer_before": "sha256:" + "c" * 64,
        "dropped_message_ids": "NONE",
        "event_id": QLORA_EVENT_ID,
        "failed_quorum_reason": "NONE",
        "gst_tick": "100",
        "hard_deadline_tick": "160",
        "isc_ticket_set": "ticket-000,ticket-001,ticket-002,ticket-003",
        "loss_fraction": "0/4",
        "lost_ticket_ids": "NONE",
        "lost_worker_ids": "NONE",
        "message_delivery_ticks": ",".join(
            [
                *(f"worker-ticket-{index:03d}:{100 + index}" for index in range(4)),
                *(f"aggregate-vote-{index}:{120 + index}" for index in range(3)),
                *(f"apply-vote-{index}:{130 + index}" for index in range(3)),
            ]
        ),
        "missing_work_policy_result": "FULL_QUORUM_DELIVERED_EXACT_ISC",
        "network_profile_id": "lan-control",
        "next_checkpoint_id": next_checkpoint,
        "next_model_value_count": str(len(next_values)),
        "next_model_values": ",".join(str(value) for value in next_values),
        "next_optimizer_state_id": "sha256:" + "f" * 64,
        "parent_checkpoint_id": "sha256:" + "c" * 64,
        "parent_optimizer_state_id": "sha256:" + "e" * 64,
        "partition_start_tick": "0",
        "per_domain_remaining_tickets": "code:2,text:2",
        "per_domain_required_tickets": "code:2,text:2",
        "pi_d_renormalized": "false",
        "quorum_capacity_after": "4",
        "quorum_capacity_before": "4",
        "quorum_formation_tick": "122",
        "schema_version": "1.0.0",
        "unavailable_ids": "NONE",
        "worker_count_before": "4",
        "worker_count_lost": "0",
    }
    causal = "".join(f"{key}={value}\n" for key, value in sorted(fields.items())).encode("ascii")
    fault = fault_profile.events[0]
    fault_line = " ".join(
        (
            "FAULT",
            fault.event_id,
            str(fault.at_step),
            fault.actor_class,
            fault.action,
            "APPLIED",
            "ACTUAL_RUNTIME_TRANSITION",
            sha256_content_id(native_trace),
            "sha256:" + "d" * 64,
            "sha256:" + "e" * 64,
            "sha256:" + "a" * 64,
            "19",
            "0",
            "0",
            "1",
            "1",
            native_trace.hex(),
            causal.hex(),
        )
    )
    return (
        "\n".join(
            [
                f"STAGEC_V1 {plan_id}",
                f"{profile_line} {profile_receipt}",
                fault_line,
                "END_STAGEC_V1",
            ]
        )
        + "\n"
    ).encode("ascii")


class FakeBoundary:
    def execute(self, **kwargs):
        assert kwargs["worker_shards"].keys() == {
            f"ticket-{index:03d}" for index in range(NODE_COUNT)
        }
        assert kwargs["shards_manifest"] == _shards_manifest()
        _central, central_q_values, _metrics = _run_central_baseline()
        return _parse_receipt(
            _receipt(kwargs["plan_id"], central_q_values),
            plan_id=kwargs["plan_id"],
            network_profiles=kwargs["network_profiles"],
            fault_profile=kwargs["fault_profile"],
        )


class FakeTrainingBoundary:
    def __init__(self, values_by_round: list[tuple[int, ...]]) -> None:
        self._values_by_round = list(values_by_round)
        self.calls = 0

    def execute(self, **kwargs):
        assert kwargs["worker_shards"].keys() == {
            f"ticket-{index:03d}" for index in range(NODE_COUNT)
        }
        assert kwargs["shards_manifest"] == _shards_manifest()
        values = self._values_by_round.pop(0)
        self.calls += 1
        return _parse_receipt(
            _receipt(kwargs["plan_id"], values),
            plan_id=kwargs["plan_id"],
            network_profiles=kwargs["network_profiles"],
            fault_profile=kwargs["fault_profile"],
        )


def test_qlora_delta_e2e_report_requires_real_drq1_evidence(tmp_path: Path) -> None:
    result = run_qlora_delta_e2e(
        Path(__file__).resolve().parents[3],
        tmp_path / "qlora-e2e",
        stage_c_boundary=FakeBoundary(),  # type: ignore[arg-type]
    )
    report = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert report["type_name"] == "QLORA_STAGEC_REAL_DRQ1_E2E_REPORT"
    assert report["execution_evidence"]["execution_mode"] == "REAL_DRQ1"
    assert report["execution_evidence"]["outcome"] == "APPLIED"
    assert report["execution_evidence"]["worker_count"] == 4
    assert report["execution_evidence"]["only_adapter_drq1_contributions"] is True
    assert report["execution_evidence"]["python_cross_worker_aggregation_performed"] is False
    assert report["execution_evidence"]["java_ml_arithmetic_performed"] is False
    assert report["execution_evidence"]["synthetic_fallback"] is False
    assert report["adapter_checkpoint_materialized"] is True
    assert report["comparison"]["centralized_and_distributed_q_values_byte_equal"] is True
    assert len(report["distributed"]["applied_adapter_values"]) == 8
    assert _canonical_bytes(result.report) + b"\n" == result.report_path.read_bytes()


def test_qlora_training_quality_chains_applied_adapter_checkpoints(
    tmp_path: Path,
) -> None:
    rounds = 3
    fake_boundary = FakeTrainingBoundary(_expected_round_values(tmp_path, rounds))
    result = run_qlora_training_quality(
        Path(__file__).resolve().parents[3],
        tmp_path / "training-quality",
        rounds=rounds,
        stage_c_boundary=fake_boundary,  # type: ignore[arg-type]
    )
    report = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert fake_boundary.calls == rounds
    assert report["type_name"] == ("QLORA_STAGEC_REAL_DRQ1_MULTI_ROUND_TRAINING_QUALITY_REPORT")
    assert report["execution_evidence"]["round_count"] == rounds
    assert report["execution_evidence"]["all_rounds_applied"] is True
    assert report["execution_evidence"]["checkpoint_chain_continuous"] is True
    assert report["execution_evidence"]["python_cross_worker_aggregation_performed"] is False
    assert report["execution_evidence"]["java_ml_arithmetic_performed"] is False
    assert report["execution_evidence"]["synthetic_fallback"] is False
    assert report["training_quality"]["distributed_loss_improved"] is True
    assert (
        report["training_quality"]["distributed_final_loss_mse"]
        < report["training_quality"]["distributed_initial_loss_mse"]
    )
    checkpoint_chain = report["checkpoint_chain"]
    assert len(checkpoint_chain) == rounds + 1
    for round_index, round_report in enumerate(report["rounds"]):
        assert round_report["round_index"] == round_index
        assert round_report["parent_adapter_id"] == checkpoint_chain[round_index]
        assert round_report["applied_adapter_id"] == checkpoint_chain[round_index + 1]
        assert set(round_report["worker_parent_adapter_ids"]) == {checkpoint_chain[round_index]}
        assert round_report["adapter_checkpoint_materialized"] is True
        assert round_report["stage_c_model_values_hash_verified"] is True
    assert report["centralized"]["same_training_budget"] is True
    assert report["centralized"]["baseline_used_for_execution"] is False
    trajectory = report["trajectory"]
    summary = trajectory["summary"]
    assert summary["tolerances"] == {
        "max_checkpoint_l2": 0.01,
        "max_loss_delta": 0.001,
        "min_cosine_similarity": 0.999,
    }
    assert summary["trajectory_within_tolerance"] is True
    assert summary["max_loss_delta"] <= summary["tolerances"]["max_loss_delta"]
    assert summary["max_checkpoint_distance"] <= summary["tolerances"]["max_checkpoint_l2"]
    assert len(trajectory["rounds"]) == rounds
    for round_index, trajectory_round in enumerate(trajectory["rounds"]):
        assert trajectory_round["round"] == round_index + 1
        assert trajectory_round["distributed_checkpoint_id"] == checkpoint_chain[round_index + 1]
        assert isinstance(trajectory_round["loss_delta"], float)
        assert trajectory_round["max_abs_adapter_q_diff"] >= 0
        assert trajectory_round["l2_adapter_checkpoint_distance"] >= 0.0
        assert trajectory_round["cosine_similarity_from_m0"] >= 0.999
    assert _canonical_bytes(result.report) + b"\n" == result.report_path.read_bytes()


def test_qlora_delta_e2e_fails_closed_without_boundary_env(tmp_path: Path, monkeypatch) -> None:
    for name in (
        "DELTA_STAGEC_JAVA",
        "DELTA_MNIST_JAVA",
        "DELTA_STAGEC_NATIVE_SIDECAR",
        "DELTA_STAGEC_TRANSPORT_HARNESS",
        "DELTA_STAGEC_NETTY_CLASSPATH",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(QloraDeltaE2EError, match="QLORA_STAGEC_RUNTIME_BOUNDARY_MISSING"):
        run_qlora_delta_e2e(Path(__file__).resolve().parents[3], tmp_path / "missing")


def test_qlora_training_quality_fails_closed_without_boundary_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    for name in (
        "DELTA_STAGEC_JAVA",
        "DELTA_MNIST_JAVA",
        "DELTA_STAGEC_NATIVE_SIDECAR",
        "DELTA_STAGEC_TRANSPORT_HARNESS",
        "DELTA_STAGEC_NETTY_CLASSPATH",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(QloraDeltaE2EError, match="QLORA_STAGEC_RUNTIME_BOUNDARY_MISSING"):
        run_qlora_training_quality(Path(__file__).resolve().parents[3], tmp_path / "missing")
