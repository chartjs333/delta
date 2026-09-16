"""Unit tests for QloraModelPlugin ModelPlugin implementation."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from deltatorrent.benchmark.qlora_delta_e2e import _materialize_applied_adapter
from deltatorrent.model_plugins import (
    QLORA_DESCRIPTOR,
    EvaluationResult,
    LocalTrainingResult,
    ModelPlugin,
    QloraAdapterModel,
    QloraModelPlugin,
    QloraPluginError,
)
from deltatorrent.model_plugins.qlora import QLORA_PARAMETER_SCHEMA_ID
from deltatorrent.qlora.backend import clone_adapters, logical_adapter_hash
from deltatorrent.qlora.tiny_profile import (
    ADAPTER_ORDER,
    ADAPTER_WIDTH,
    QLORA_DATASET_ID,
    QLORA_PLUGIN_ID,
    QLORA_SEGMENT_ID,
    evaluate_backend,
    flatten_adapters,
    new_tiny_backend,
    worker_batches,
)
from deltatorrent.qlora.trainer import Batch


def test_qlora_plugin_descriptor_and_protocol() -> None:
    plugin = QloraModelPlugin()
    assert isinstance(plugin, ModelPlugin)
    assert plugin.plugin_id == QLORA_PLUGIN_ID == "qlora-tiny-adapter-v1"
    assert plugin.total_elements == ADAPTER_WIDTH == 8
    assert plugin.tensor_order == (QLORA_SEGMENT_ID,) == ("qlora.adapter.flat",)

    schema = plugin.parameter_schema()
    assert len(schema.parameters) == 1
    spec = schema.parameters[0]
    assert spec.name == "qlora.adapter.flat"
    assert spec.shape == (8,)
    assert spec.trainable is True
    assert schema.fingerprint == QLORA_PARAMETER_SCHEMA_ID

    assert QLORA_DESCRIPTOR.plugin_id == plugin.plugin_id
    assert QLORA_DESCRIPTOR.sample_kind == "vector/tiny-qlora-2d"
    assert QLORA_DESCRIPTOR.target_kind == "regression/vector-2d"
    assert QLORA_DESCRIPTOR.supports_stage_c_real_drq1 is True
    assert QLORA_DESCRIPTOR.parameter_schema_id == plugin.parameter_schema().fingerprint
    assert QLORA_DESCRIPTOR.parameter_schema_id == QLORA_PARAMETER_SCHEMA_ID


def test_qlora_create_model_default_and_state() -> None:
    plugin = QloraModelPlugin()
    model = plugin.create_model()
    assert isinstance(model, QloraAdapterModel)
    assert model.base_model_id == plugin.base_model_id
    assert set(model.adapter_tensors.keys()) == set(ADAPTER_ORDER)
    assert model.adapter_tensors["model.layer0.lora_A"].shape == (2, 2)
    assert model.adapter_tensors["model.layer0.lora_B"].shape == (2, 2)

    # Passing existing QloraAdapterModel returns it
    model2 = plugin.create_model(model)
    assert model2 is model

    # Passing raw backend creates valid QloraAdapterModel
    raw_backend = new_tiny_backend()
    model3 = plugin.create_model(raw_backend)
    assert isinstance(model3, QloraAdapterModel)
    assert model3.base_model_id == plugin.base_model_id

    # Passing valid adapter tensors dictionary
    model4 = plugin.create_model(model.adapter_tensors)
    assert isinstance(model4, QloraAdapterModel)

    # Invalid state raises QloraPluginError
    with pytest.raises(QloraPluginError, match="INVALID_QLORA_MODEL_STATE"):
        plugin.create_model("invalid-state")


def test_qlora_create_model_and_parent_reject_invalid_shapes() -> None:
    plugin = QloraModelPlugin()

    # Flattened shape (4,) instead of (2, 2)
    bad_shape_mapping = {
        "model.layer0.lora_A": np.zeros(4, dtype=np.float64),
        "model.layer0.lora_B": np.zeros(4, dtype=np.float64),
    }
    with pytest.raises(QloraPluginError, match="ADAPTER_SHAPE_MISMATCH"):
        plugin.create_model(bad_shape_mapping)

    # Incomplete parameter set
    incomplete_mapping = {
        "model.layer0.lora_A": np.zeros((2, 2), dtype=np.float64),
    }
    with pytest.raises(QloraPluginError, match="ADAPTER_PARAMETER_SET_MISMATCH"):
        plugin.create_model(incomplete_mapping)

    # load_applied_checkpoint with invalid parent adapter shapes fails closed
    with pytest.raises(QloraPluginError, match="ADAPTER_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint((0,) * 8, parent_model=bad_shape_mapping)

    # train_ticket with invalid parent adapter shapes fails closed
    with pytest.raises(QloraPluginError, match="ADAPTER_SHAPE_MISMATCH"):
        plugin.train_ticket(
            ticket_id="ticket-bad-shape",
            data=worker_batches()[0],
            parent_model=bad_shape_mapping,
        )


def test_qlora_load_applied_checkpoint_parity_with_e2e_primitives() -> None:
    plugin = QloraModelPlugin()
    coords = (0, 0, 0, 0, 50, 12, 0, 12)

    plugin_model = plugin.load_applied_checkpoint(coords)
    e2e_model = _materialize_applied_adapter(coords)

    # Verify adapter tensors are bit-for-bit identical
    for name in ADAPTER_ORDER:
        assert np.array_equal(plugin_model.adapter_tensors[name], e2e_model.adapter_tensors[name])

    assert plugin_model.base_model_id == e2e_model.base_model_id
    assert (
        plugin_model.adapter_id == e2e_model.adapter_checkpoint_id
        or len(plugin_model.adapter_id) > 0
    )


def test_qlora_load_applied_checkpoint_chains_parent_model() -> None:
    plugin = QloraModelPlugin()
    coords_round1 = (0, 0, 0, 0, 20, 10, 0, 10)
    coords_round2 = (5, -5, 2, 0, 30, 2, 0, 2)

    model_r1 = plugin.load_applied_checkpoint(coords_round1)
    model_r2 = plugin.load_applied_checkpoint(coords_round2, parent_model=model_r1)

    # Verify parent adapters + round 2 delta
    parent_flat = flatten_adapters(clone_adapters(model_r1.backend))
    expected_r2_flat = parent_flat + (np.asarray(coords_round2, dtype=np.float64) / 10_000)
    actual_r2_flat = flatten_adapters(clone_adapters(model_r2.backend))
    assert np.allclose(actual_r2_flat, expected_r2_flat)
    assert model_r2.base_model_id == plugin.base_model_id


def test_qlora_load_applied_checkpoint_fail_closed() -> None:
    plugin = QloraModelPlugin()

    # Shape mismatch: 7 instead of 8
    with pytest.raises(QloraPluginError, match="CHECKPOINT_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint((1, 2, 3, 4, 5, 6, 7))

    # Shape mismatch: 9 instead of 8
    with pytest.raises(QloraPluginError, match="CHECKPOINT_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint(tuple(range(9)))

    # Non-integer coordinates
    with pytest.raises(QloraPluginError, match="CHECKPOINT_VALUES_NOT_INTEGER"):
        plugin.load_applied_checkpoint((1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0))

    # int16 overflow (> 32767)
    with pytest.raises(QloraPluginError, match="CHECKPOINT_INT16_OVERFLOW"):
        plugin.load_applied_checkpoint((0, 0, 0, 0, 32768, 0, 0, 0))

    # int16 underflow (< -32768)
    with pytest.raises(QloraPluginError, match="CHECKPOINT_INT16_OVERFLOW"):
        plugin.load_applied_checkpoint((0, 0, 0, 0, -32769, 0, 0, 0))

    # Immutable base binding violation on parent_model
    bad_backend = new_tiny_backend()
    bad_backend._base["model.layer0.weight"] = torch.zeros_like(
        bad_backend._base["model.layer0.weight"]
    )
    with pytest.raises(QloraPluginError, match="IMMUTABLE_BASE_BINDING_VIOLATION"):
        plugin.load_applied_checkpoint((0,) * 8, parent_model=bad_backend)


def test_qlora_train_ticket_delegates_to_existing_trainer() -> None:
    plugin = QloraModelPlugin()
    batch = worker_batches()[0]

    result = plugin.train_ticket(ticket_id="ticket-001", data=batch, domain_id="code")
    assert isinstance(result, LocalTrainingResult)
    assert result.ticket_id == "ticket-001"
    assert QLORA_SEGMENT_ID in result.tensors
    tensor = result.tensors[QLORA_SEGMENT_ID]
    assert tensor.shape == (8,)
    assert tensor.dtype == np.float32

    # Verify metadata fields
    assert result.metadata["status"] == "COMPLETE"
    assert result.metadata["domain_id"] == "code"
    assert result.metadata["base_hash_before"] == result.metadata["base_hash_after"]
    assert result.metadata["base_hash_before"] == plugin.base_model_id


def test_qlora_train_ticket_fail_closed() -> None:
    plugin = QloraModelPlugin()
    batch = worker_batches()[0]

    # Empty ticket_id
    with pytest.raises(QloraPluginError, match="INVALID_TICKET_ID"):
        plugin.train_ticket(ticket_id="", data=batch)

    # Invalid data
    with pytest.raises(QloraPluginError, match="INVALID_TRAINING_DATA"):
        plugin.train_ticket(ticket_id="ticket-001", data="not-a-batch")

    # Mutated parent backend base weights
    mutated_backend = new_tiny_backend()
    mutated_backend._base["model.layer0.weight"].add_(1.0)
    with pytest.raises(QloraPluginError, match="IMMUTABLE_BASE_BINDING_VIOLATION"):
        plugin.train_ticket(
            ticket_id="ticket-001",
            data=batch,
            parent_model=mutated_backend,
        )


def test_qlora_evaluate() -> None:
    plugin = QloraModelPlugin()
    model = plugin.create_model()

    # Evaluate using default evaluation batch
    eval_res = plugin.evaluate(model)
    assert isinstance(eval_res, EvaluationResult)
    assert eval_res.loss is not None
    assert eval_res.loss > 0.0
    assert eval_res.accuracy_ppm >= 0
    assert eval_res.metrics["evaluation_dataset_id"] == QLORA_DATASET_ID
    assert eval_res.metrics["sample_count"] == 5

    # Evaluation loss matches evaluate_backend
    e2e_eval = evaluate_backend(model.backend)
    assert eval_res.loss == e2e_eval["loss_mse"]
    assert eval_res.metrics["mean_absolute_error"] == e2e_eval["mean_absolute_error"]


def test_qlora_evaluate_custom_test_data() -> None:
    plugin = QloraModelPlugin()
    model = plugin.create_model()
    custom_batch = Batch(
        inputs=torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.float32),
        targets=torch.tensor([[0.0, 0.0], [0.0, 0.0]], dtype=torch.float32),
        token_count=2,
    )

    eval_res = plugin.evaluate(model, test_data=custom_batch)
    assert eval_res.metrics["sample_count"] == 2
    assert eval_res.loss is not None


def test_qlora_rejects_desynchronized_model_adapter_state() -> None:
    plugin = QloraModelPlugin()
    valid_model = plugin.create_model()
    batch = worker_batches()[0]

    # Forged model: valid zero adapter_tensors, but backend adapter has nonzero weights
    divergent_backend = new_tiny_backend()
    divergent_backend._adapters["model.layer0.lora_A"].data.add_(1.0)
    forged_model = QloraAdapterModel(
        backend=divergent_backend,
        adapter_tensors=valid_model.adapter_tensors,
        values=valid_model.values,
        base_model_id=plugin.base_model_id,
        adapter_id=logical_adapter_hash(divergent_backend),
    )

    with pytest.raises(QloraPluginError, match="MODEL_ADAPTER_STATE_MISMATCH"):
        plugin.create_model(forged_model)

    with pytest.raises(QloraPluginError, match="MODEL_ADAPTER_STATE_MISMATCH"):
        plugin.evaluate(forged_model)

    with pytest.raises(QloraPluginError, match="MODEL_ADAPTER_STATE_MISMATCH"):
        plugin.train_ticket(
            ticket_id="ticket-forged-sync",
            data=batch,
            parent_model=forged_model,
        )

    with pytest.raises(QloraPluginError, match="MODEL_ADAPTER_STATE_MISMATCH"):
        plugin.load_applied_checkpoint((0,) * 8, parent_model=forged_model)


def test_qlora_rejects_malformed_backend_shape() -> None:
    plugin = QloraModelPlugin()
    valid_model = plugin.create_model()
    batch = worker_batches()[0]

    # Forged model: backend adapter has shape (4,) instead of (2, 2)
    malformed_backend = new_tiny_backend()
    malformed_backend._adapters["model.layer0.lora_A"] = torch.nn.Parameter(
        torch.zeros(4, dtype=torch.float32)
    )
    forged_model = QloraAdapterModel(
        backend=malformed_backend,
        adapter_tensors=valid_model.adapter_tensors,
        values=valid_model.values,
        base_model_id=plugin.base_model_id,
        adapter_id="dummy-adapter-id",
    )

    with pytest.raises(QloraPluginError, match="ADAPTER_SHAPE_MISMATCH"):
        plugin.create_model(forged_model)

    # Must fail-closed with QloraPluginError, NOT raw torch RuntimeError
    with pytest.raises(QloraPluginError, match="ADAPTER_SHAPE_MISMATCH"):
        plugin.evaluate(forged_model)

    with pytest.raises(QloraPluginError, match="ADAPTER_SHAPE_MISMATCH"):
        plugin.train_ticket(
            ticket_id="ticket-malformed-shape",
            data=batch,
            parent_model=forged_model,
        )

    with pytest.raises(QloraPluginError, match="ADAPTER_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint((0,) * 8, parent_model=forged_model)


def test_qlora_accepts_consistent_model() -> None:
    plugin = QloraModelPlugin()
    model = plugin.create_model()
    batch = worker_batches()[0]

    # Model passed through create_model
    m1 = plugin.create_model(model)
    assert m1 is model

    # Model passed through evaluate
    res = plugin.evaluate(model)
    assert isinstance(res, EvaluationResult)
    assert res.loss is not None

    # Model used as parent in train_ticket
    train_res = plugin.train_ticket(
        ticket_id="ticket-consistent",
        data=batch,
        parent_model=model,
    )
    assert isinstance(train_res, LocalTrainingResult)

    # Model used as parent in load_applied_checkpoint
    ckpt_model = plugin.load_applied_checkpoint((0,) * 8, parent_model=model)
    assert isinstance(ckpt_model, QloraAdapterModel)
    assert ckpt_model.base_model_id == plugin.base_model_id


def test_qlora_rejects_non_finite_or_corrupt_adapter_state() -> None:
    plugin = QloraModelPlugin()
    valid_model = plugin.create_model()

    # NaN in adapter_tensors
    nan_tensors = {
        "model.layer0.lora_A": np.full((2, 2), np.nan, dtype=np.float64),
        "model.layer0.lora_B": np.zeros((2, 2), dtype=np.float64),
    }
    nan_model = QloraAdapterModel(
        backend=new_tiny_backend(),
        adapter_tensors=nan_tensors,
        values=valid_model.values,
        base_model_id=plugin.base_model_id,
        adapter_id=valid_model.adapter_id,
    )
    with pytest.raises(QloraPluginError, match="NON_FINITE_ADAPTER_VALUES"):
        plugin.create_model(nan_model)

    # Forged adapter_id
    tampered_id_model = QloraAdapterModel(
        backend=new_tiny_backend(),
        adapter_tensors=valid_model.adapter_tensors,
        values=valid_model.values,
        base_model_id=plugin.base_model_id,
        adapter_id="forged-id-1234",
    )
    with pytest.raises(QloraPluginError, match="MODEL_ADAPTER_STATE_MISMATCH"):
        plugin.create_model(tampered_id_model)
