"""Unit tests for model training examples and endpoints."""

from __future__ import annotations

from pathlib import Path

from model_examples import (
    get_execution_receipt,
    get_mnist_summary,
    get_qlora_qualification,
    run_causal_lm_step,
    run_qlora_live_step,
)


def test_mnist_summary_contents():
    summary = get_mnist_summary()
    assert summary["model_name"] == "MnistCentroidModel"
    assert summary["participant_count"] == 4
    assert len(summary["nodes"]) == 4
    assert summary["accuracy"]["centralized_percent"] == 82.05
    assert summary["accuracy"]["distributed_percent"] == 82.05
    assert summary["failure_simulation"]["status"] == "RECOVERED_AND_APPLIED"
    assert summary["failure_simulation"]["failed_node_id"] == "validator-04"
    assert summary["consensus_pipeline"]["aggregation_owner"] == "delta::robust::reduce_parameter_shard"
    assert len(summary["consensus_pipeline"]["stages"]) == 5
    assert "rounds" in summary
    assert len(summary["rounds"]) == 4
    assert summary["rounds"][2]["status"] == "CRASH_AND_RECOVERED"
    assert "chart_data" in summary
    assert summary["chart_data"]["failure_point_index"] == 2


def test_qlora_qualification_contents():
    qual = get_qlora_qualification()
    assert qual["status"] == "PASS"
    assert qual["badge"] == "RECORDED_RUN_8GB_QUALIFIED"
    assert qual["device"]["total_memory_gb"] <= 8.5
    assert qual["memory_profile"]["within_8gb_bound"] is True
    assert qual["architecture"]["base_parameters"] > 2_000_000_000
    assert qual["architecture"]["adapter_parameters"] > 12_000_000
    assert len(qual["training_performance"]["losses"]) == 8


def test_qlora_deltareduce_pipeline():
    result = run_qlora_live_step()
    assert result["status"] == "COMPLETE"
    assert result["badge"] == "CONSENSUS_APPLIED_4_WORKERS"
    assert result["participant_count"] == 4
    assert len(result["workers"]) == 4
    assert len(result["adapter_tensor_shape"]) > 0
    assert result["parameter_root"].startswith("sha256:")
    assert result["apply_digest"].startswith("sha256:")
    assert result["next_adapter_hash"].startswith("sha256:")
    assert "rounds" in result
    assert len(result["rounds"]) == 4
    assert "chart_data" in result
    assert len(result["chart_data"]["values"]) == 4

    # Verify cryptographic receipt
    receipt = result["receipt"]
    assert receipt["consensus_status"] == "APPLIED"
    assert len(receipt["stages"]) == 5
    assert receipt["stages"][1]["name"] == "PARAMETER_AGGREGATION"
    assert receipt["stages"][3]["name"] == "APPLY_CONSENSUS"
    assert get_execution_receipt(result["execution_id"]) is not None


def test_causal_lm_deltareduce_pipeline(tmp_path: Path):
    result = run_causal_lm_step(tmp_path)
    assert result["model_name"] == "TinyCausalLM"
    assert result["status"] == "COMPLETED"
    assert result["badge"] == "CONSENSUS_APPLIED_4_WORKERS"
    assert result["steps_count"] == 4
    assert result["initial_loss"] > 0
    assert result["final_loss"] > 0
    # True gradient descent loss reduction:
    assert result["final_loss"] < result["initial_loss"]
    assert result["loss_reduction"] > 0
    assert "rounds" in result
    assert len(result["rounds"]) == 5
    assert "chart_data" in result
    assert len(result["chart_data"]["values"]) == 6  # R0 plus 5 rounds
    assert result["total_tokens_processed"] > 0
    assert result["checkpoint_manifest"].startswith("sha256:")

    # Verify cryptographic receipt
    receipt = result["receipt"]
    assert receipt["consensus_status"] == "APPLIED"
    assert receipt["participant_count"] == 4
    assert len(receipt["workers"]) == 4
    assert receipt["parameter_root"].startswith("sha256:")
    assert receipt["apply_digest"].startswith("sha256:")
    assert (tmp_path / "receipts" / f"{result['execution_id']}.json").is_file()
