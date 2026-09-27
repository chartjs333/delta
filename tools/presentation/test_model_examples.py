"""Unit tests for model training examples and endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from model_examples import (
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


def test_qlora_qualification_contents():
    qual = get_qlora_qualification()
    assert qual["status"] == "PASS"
    assert qual["badge"] == "RECORDED_RUN_8GB_QUALIFIED"
    assert qual["device"]["total_memory_gb"] <= 8.5
    assert qual["memory_profile"]["within_8gb_bound"] is True
    assert qual["architecture"]["base_parameters"] > 2_000_000_000
    assert qual["architecture"]["adapter_parameters"] > 12_000_000
    assert len(qual["training_performance"]["losses"]) == 8


def test_qlora_live_step():
    step = run_qlora_live_step()
    assert step["status"] == "COMPLETE"
    assert step["badge"] == "LIVE_STEP_MEASURED"
    assert step["worker_partition"] == "demo-qlora-worker-01"
    assert len(step["adapter_tensor_shape"]) > 0
    assert step["elapsed_ms"] >= 0


def test_causal_lm_step(tmp_path: Path):
    result = run_causal_lm_step(tmp_path)
    assert result["model_name"] == "TinyCausalLM"
    assert result["status"] == "COMPLETED"
    assert result["badge"] == "LIVE_RUN_MEASURED"
    assert result["steps_count"] == 4
    assert result["initial_loss"] > 0
    assert result["final_loss"] > 0
    assert result["total_tokens_processed"] == 64
    assert result["checkpoint_manifest"].startswith("sha256:")
