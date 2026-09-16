"""Unit tests for EegBandpowerCentroidPlugin ModelPlugin implementation."""

from __future__ import annotations

import numpy as np
import pytest
from deltatorrent.model_plugins import (
    EEG_BANDPOWER_DESCRIPTOR,
    EegBandpowerCentroidPlugin,
    EegBandpowerModel,
    EegPluginError,
    EvaluationResult,
    LocalTrainingResult,
    ModelPlugin,
)
from deltatorrent.model_plugins.eeg_bandpower import (
    FEATURE_COUNT,
    SCALE_FACTOR,
    TOTAL_ELEMENTS,
    round_half_toward_positive,
    scale_bandpower_features,
)


def test_eeg_plugin_descriptor_and_protocol() -> None:
    plugin = EegBandpowerCentroidPlugin()
    assert isinstance(plugin, ModelPlugin)
    assert plugin.plugin_id == "eeg-bandpower-centroid-v1"
    assert plugin.total_elements == TOTAL_ELEMENTS == 34
    assert plugin.tensor_order == ("eeg.centroid",)

    schema = plugin.parameter_schema()
    assert len(schema.parameters) == 1
    spec = schema.parameters[0]
    assert spec.name == "eeg.centroid"
    assert spec.shape == (34,)
    assert spec.trainable is True

    assert EEG_BANDPOWER_DESCRIPTOR.plugin_id == plugin.plugin_id
    assert EEG_BANDPOWER_DESCRIPTOR.sample_kind == "eeg/bandpower-4ch-4band"
    assert EEG_BANDPOWER_DESCRIPTOR.target_kind == "class-id/0-1"
    assert EEG_BANDPOWER_DESCRIPTOR.supports_stage_c_real_drq1 is False


def test_eeg_round_half_toward_positive_parity() -> None:
    # 0.5 rounds up to 1: sum=1, count=2 -> 1
    assert round_half_toward_positive(np.array([1], dtype=np.int64), 2)[0] == 1
    # 1.5 rounds up to 2: sum=3, count=2 -> 2
    assert round_half_toward_positive(np.array([3], dtype=np.int64), 2)[0] == 2
    # 0.0 -> 0
    assert round_half_toward_positive(np.array([0], dtype=np.int64), 2)[0] == 0
    # 1.0 -> 1
    assert round_half_toward_positive(np.array([2], dtype=np.int64), 2)[0] == 1

    with pytest.raises(EegPluginError, match="EEG_DELTA_LOCAL_SUM_INVALID"):
        round_half_toward_positive(np.array([1], dtype=np.int64), 0)

    with pytest.raises(EegPluginError, match="EEG_DELTA_LOCAL_SUM_INVALID"):
        round_half_toward_positive(np.array([-1], dtype=np.int64), 2)


def test_eeg_feature_scaling_avoids_bankers_rounding() -> None:
    samples = np.zeros((1, FEATURE_COUNT), dtype=np.float64)
    samples[0, 0] = 0.00005  # 0.5 after scale
    samples[0, 1] = 0.00025  # 2.5 after scale

    scaled = scale_bandpower_features(samples)

    assert np.rint(samples[0, 0] * SCALE_FACTOR) == 0.0
    assert scaled[0, 0] == 1
    assert scaled[0, 1] == 3


def test_eeg_plugin_rejects_invalid_feature_and_label_values() -> None:
    plugin = EegBandpowerCentroidPlugin()
    valid_samples = np.full((4, FEATURE_COUNT), 0.25, dtype=np.float64)

    bad_feature = valid_samples.copy()
    bad_feature[0, 0] = 1.1
    with pytest.raises(EegPluginError, match="EEG_FEATURES_OUT_OF_RANGE"):
        plugin.train_ticket(
            ticket_id="ticket-eeg-bad-feature",
            data=(bad_feature, np.array([0, 0, 1, 1], dtype=np.uint8)),
        )

    with pytest.raises(EegPluginError, match="EEG_LABELS_OUT_OF_RANGE"):
        plugin.train_ticket(
            ticket_id="ticket-eeg-bad-label",
            data=(valid_samples, np.array([0, 1, 2, 1], dtype=np.uint8)),
        )


def test_eeg_plugin_train_ticket() -> None:
    plugin = EegBandpowerCentroidPlugin()
    rng = np.random.Generator(np.random.PCG64(42))

    # Generate 10 samples of 16 bandpower features in [0.0, 1.0]
    samples = rng.uniform(0.0, 0.5, size=(10, FEATURE_COUNT))
    labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=np.uint8)

    res = plugin.train_ticket(ticket_id="ticket-eeg-001", data=(samples, labels))
    assert isinstance(res, LocalTrainingResult)
    assert res.ticket_id == "ticket-eeg-001"
    assert "eeg.centroid" in res.tensors
    tensor = res.tensors["eeg.centroid"]
    assert tensor.shape == (34,)
    assert res.metadata["sample_count"] == 10
    assert res.metadata["class_counts"] == [5, 5]

    # Both classes should be marked present
    assert tensor[32] == 1.0
    assert tensor[33] == 1.0


def test_eeg_plugin_checkpoint_decoding_and_evaluation() -> None:
    plugin = EegBandpowerCentroidPlugin()

    # Synthetic checkpoint with distinct class centroids
    # Class 0: all features 0.2 (scaled to 2000)
    # Class 1: all features 0.8 (scaled to 8000)
    checkpoint = np.zeros(TOTAL_ELEMENTS, dtype=np.int64)
    checkpoint[:16] = 2000
    checkpoint[16:32] = 8000
    checkpoint[32] = 1
    checkpoint[33] = 1

    model = plugin.load_applied_checkpoint(checkpoint)
    assert isinstance(model, EegBandpowerModel)
    assert model.centroids.shape == (2, 16)
    assert np.allclose(model.centroids[0], 0.2)
    assert np.allclose(model.centroids[1], 0.8)
    assert model.presence.tolist() == [1, 1]

    # Evaluate on test samples clearly separated
    test_samples = np.vstack(
        [
            np.full((5, 16), 0.22),  # close to class 0
            np.full((5, 16), 0.78),  # close to class 1
        ]
    )
    test_labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=np.uint8)

    eval_res = plugin.evaluate(model, (test_samples, test_labels))
    assert isinstance(eval_res, EvaluationResult)
    assert eval_res.accuracy_ppm == 1_000_000
    assert eval_res.metrics["correct"] == 10
    assert eval_res.metrics["total"] == 10


def test_eeg_plugin_checkpoint_validation_rejections() -> None:
    plugin = EegBandpowerCentroidPlugin()

    # Wrong shape
    with pytest.raises(EegPluginError, match="CHECKPOINT_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint(np.zeros(30, dtype=np.int64))

    # Float values
    with pytest.raises(EegPluginError, match="CHECKPOINT_VALUES_NOT_INTEGER"):
        plugin.load_applied_checkpoint(np.zeros(34, dtype=np.float64))

    # Centroid coordinate out of range (> SCALE_FACTOR 10000)
    bad_coord = np.zeros(34, dtype=np.int64)
    bad_coord[0] = SCALE_FACTOR + 1
    with pytest.raises(EegPluginError, match="CHECKPOINT_CENTROID_OUT_OF_RANGE"):
        plugin.load_applied_checkpoint(bad_coord)

    # Presence out of range
    bad_presence = np.zeros(34, dtype=np.int64)
    bad_presence[32] = 2
    with pytest.raises(EegPluginError, match="CHECKPOINT_PRESENCE_INVALID"):
        plugin.load_applied_checkpoint(bad_presence)
