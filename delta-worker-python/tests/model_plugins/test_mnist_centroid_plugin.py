"""Unit tests for the ModelPlugin contract and MnistCentroidPlugin implementation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from deltatorrent.benchmark.mnist_delta_nodes import _round_nonnegative_half_toward_positive
from deltatorrent.model_plugins import (
    EvaluationResult,
    LocalTrainingResult,
    MnistCentroidModel,
    MnistCentroidPlugin,
    ModelPlugin,
)
from deltatorrent.model_plugins.mnist_centroid import (
    CENTROID_WEIGHT_ELEMENTS,
    TOTAL_ELEMENTS,
    MnistPluginError,
    round_half_toward_positive,
)


def _synthetic_digits() -> tuple[np.ndarray, np.ndarray]:
    """Generate 20 distinct images across all 10 digits."""
    labels = np.repeat(np.arange(10, dtype=np.uint8), 2)
    images = np.zeros((20, 28, 28), dtype=np.uint8)
    for index, digit in enumerate(labels):
        images[index, digit * 2 : digit * 2 + 2, 5:25] = 200
    return images, labels


def test_mnist_plugin_adheres_to_model_plugin_protocol() -> None:
    plugin = MnistCentroidPlugin()
    assert isinstance(plugin, ModelPlugin)
    assert plugin.plugin_id == "mnist-centroid-v1"
    assert plugin.tensor_order == ("mnist.linear",)
    assert plugin.total_elements == TOTAL_ELEMENTS == 7850


def test_mnist_plugin_parameter_schema_is_canonical() -> None:
    plugin = MnistCentroidPlugin()
    schema = plugin.parameter_schema()
    assert len(schema.parameters) == 1
    param = schema.parameters[0]
    assert param.name == "mnist.linear"
    assert param.shape == (TOTAL_ELEMENTS,)
    assert param.trainable is True
    assert schema.fingerprint.startswith("sha256:")


def test_rounding_half_toward_positive_exact_delta_parity() -> None:
    """Prove exact integer half-toward-positive rounding parity with Delta consensus.

    Critical difference from banker's rounding (np.rint):
      sum=1, count=2:
        np.rint(0.5) = 0.0 (banker's rounding to nearest even)
        round_half_toward_positive = 1 (Delta consensus requirement)
    """
    # 1. Direct unit cases
    assert round_half_toward_positive(np.array([1], dtype=np.int64), 2)[0] == 1
    assert round_half_toward_positive(np.array([3], dtype=np.int64), 2)[0] == 2
    assert round_half_toward_positive(np.array([0], dtype=np.int64), 2)[0] == 0
    assert round_half_toward_positive(np.array([2], dtype=np.int64), 2)[0] == 1
    assert round_half_toward_positive(np.array([5], dtype=np.int64), 4)[0] == 1
    assert round_half_toward_positive(np.array([6], dtype=np.int64), 4)[0] == 2

    # Contrast explicitly with banker's rounding
    assert np.rint(1 / 2) == 0
    assert round_half_toward_positive(np.array([1], dtype=np.int64), 2)[0] == 1

    # 2. Mathematical equivalence against existing Delta reference helper across range
    test_sums = np.array([0, 1, 2, 3, 4, 5, 99, 100, 101, 255, 510, 1000], dtype=np.int64)
    for count in (1, 2, 3, 4, 5, 10, 17):
        expected = _round_nonnegative_half_toward_positive(test_sums, count)
        actual = round_half_toward_positive(test_sums, count)
        assert np.array_equal(actual, expected)


def test_mnist_plugin_train_ticket_produces_canonical_local_tensors() -> None:
    plugin = MnistCentroidPlugin()
    images, labels = _synthetic_digits()

    result = plugin.train_ticket(ticket_id="ticket-000", data=(images, labels))
    assert isinstance(result, LocalTrainingResult)
    assert result.ticket_id == "ticket-000"
    assert "mnist.linear" in result.tensors

    tensor = result.tensors["mnist.linear"]
    assert tensor.shape == (TOTAL_ELEMENTS,)
    assert tensor.dtype == np.float32

    # Class presence indicators (last 10 elements) should all be 1 since all 10 digits are present
    assert np.array_equal(tensor[7840:], np.ones(10, dtype=np.float32))
    assert result.metadata["sample_count"] == 20
    assert result.metadata["class_counts"] == [2] * 10
    assert result.metadata["contribution_type"] == "CANONICAL_LOCAL_CENTROID_TENSOR"


def test_mnist_plugin_load_applied_checkpoint_and_evaluate() -> None:
    plugin = MnistCentroidPlugin()
    images, labels = _synthetic_digits()

    train_res = plugin.train_ticket(ticket_id="ticket-000", data=(images, labels))
    tensor = train_res.tensors["mnist.linear"]

    # Emulate Stage C checkpoint: integer vector of 7850 coordinates
    checkpoint_vector = tensor.astype(np.int64)
    model = plugin.load_applied_checkpoint(checkpoint_vector)

    assert isinstance(model, MnistCentroidModel)
    assert model.centroids.shape == (10, 784)
    assert model.presence.shape == (10,)
    assert np.all(model.presence == 1)

    # Evaluate against the same synthetic images
    evaluation = plugin.evaluate(model, (images, labels))
    assert isinstance(evaluation, EvaluationResult)
    assert evaluation.accuracy_ppm == 1_000_000  # 100% accuracy on training centroids
    assert evaluation.metrics["correct"] == 20
    assert evaluation.metrics["total"] == 20
    assert len(evaluation.metrics["per_digit"]) == 10


def test_load_applied_checkpoint_fail_closed_validation() -> None:
    """Ensure load_applied_checkpoint rejects invalid values fail-closed."""
    plugin = MnistCentroidPlugin()

    # Valid template: 7840 coordinates in 0..255, 10 presence indicators in {0, 1}
    valid_coords = np.full(CENTROID_WEIGHT_ELEMENTS, 100, dtype=np.int64)
    valid_presence = np.ones(10, dtype=np.int64)
    valid = np.concatenate([valid_coords, valid_presence])
    assert isinstance(plugin.load_applied_checkpoint(valid), MnistCentroidModel)

    # 1. Centroid coordinate < 0
    neg_coords = valid.copy()
    neg_coords[42] = -1
    with pytest.raises(MnistPluginError, match="CHECKPOINT_CENTROID_OUT_OF_RANGE"):
        plugin.load_applied_checkpoint(neg_coords)

    # 2. Centroid coordinate > 255
    large_coords = valid.copy()
    large_coords[100] = 256
    with pytest.raises(MnistPluginError, match="CHECKPOINT_CENTROID_OUT_OF_RANGE"):
        plugin.load_applied_checkpoint(large_coords)

    # 3. Presence indicator not in {0, 1}
    bad_presence = valid.copy()
    bad_presence[CENTROID_WEIGHT_ELEMENTS + 3] = 2
    with pytest.raises(MnistPluginError, match="CHECKPOINT_PRESENCE_INVALID"):
        plugin.load_applied_checkpoint(bad_presence)

    bad_presence_neg = valid.copy()
    bad_presence_neg[CENTROID_WEIGHT_ELEMENTS + 5] = -1
    with pytest.raises(MnistPluginError, match="CHECKPOINT_PRESENCE_INVALID"):
        plugin.load_applied_checkpoint(bad_presence_neg)

    # 4. Wrong length
    with pytest.raises(MnistPluginError, match="CHECKPOINT_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint(valid[:100])
    with pytest.raises(MnistPluginError, match="CHECKPOINT_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint(np.append(valid, [1]))

    # 5. Non-integer values
    float_coords: Any = valid.astype(np.float64) + 0.5
    with pytest.raises(MnistPluginError, match="CHECKPOINT_VALUES_NOT_INTEGER"):
        plugin.load_applied_checkpoint(float_coords)


def test_mnist_plugin_rejects_invalid_inputs() -> None:
    plugin = MnistCentroidPlugin()
    images, labels = _synthetic_digits()

    with pytest.raises(MnistPluginError, match="INVALID_WORKER_TRAINING_DATA"):
        plugin.train_ticket(ticket_id="ticket-000", data="invalid")

    with pytest.raises(MnistPluginError, match="INVALID_TEST_DATA"):
        plugin.evaluate(plugin.create_model(), "invalid")

    # Ensure create_model and evaluate do not bypass fail-closed checkpoint validation
    invalid_overflow = np.full(TOTAL_ELEMENTS, 40000, dtype=np.int64)
    with pytest.raises(MnistPluginError, match="CHECKPOINT_CENTROID_OUT_OF_RANGE"):
        plugin.create_model(invalid_overflow)

    with pytest.raises(MnistPluginError, match="CHECKPOINT_CENTROID_OUT_OF_RANGE"):
        plugin.evaluate(invalid_overflow, (images, labels))

    invalid_presence = np.full(TOTAL_ELEMENTS, 100, dtype=np.int64)
    invalid_presence[CENTROID_WEIGHT_ELEMENTS + 1] = 2
    with pytest.raises(MnistPluginError, match="CHECKPOINT_PRESENCE_INVALID"):
        plugin.create_model(invalid_presence)

    with pytest.raises(MnistPluginError, match="CHECKPOINT_PRESENCE_INVALID"):
        plugin.evaluate(invalid_presence, (images, labels))

    # Valid array creates valid model
    valid = np.full(TOTAL_ELEMENTS, 100, dtype=np.int64)
    valid[CENTROID_WEIGHT_ELEMENTS:] = 1
    model = plugin.create_model(valid)
    assert isinstance(model, MnistCentroidModel)
    assert np.all(model.presence == 1)
