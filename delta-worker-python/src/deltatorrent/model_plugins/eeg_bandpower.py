"""EEG Bandpower Centroid Classifier ModelPlugin implementation.

Encapsulates EEG bandpower nearest-centroid mathematics, parameter schema,
local sufficient statistics, applied-checkpoint decoding, and evaluation.
Generic Delta consensus and Stage C interact with this model exclusively
through the ModelPlugin protocol.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from deltatorrent.domain.parameters import (
    FrozenOmissionPolicy,
    LogicalDType,
    ParameterSchema,
    ParameterSpec,
)
from deltatorrent.model_plugins.base import EvaluationResult, LocalTrainingResult, ModelPlugin

CLASS_COUNT = 2  # 0: Rest / Relaxed, 1: Task / Motor Imagery
CHANNEL_COUNT = 4  # F3, F4, C3, C4
BAND_COUNT = 4  # delta, theta, alpha, beta
FEATURE_COUNT = CHANNEL_COUNT * BAND_COUNT  # 16
CENTROID_WEIGHT_ELEMENTS = CLASS_COUNT * FEATURE_COUNT  # 32
PRESENCE_ELEMENTS = CLASS_COUNT  # 2
TOTAL_ELEMENTS = CENTROID_WEIGHT_ELEMENTS + PRESENCE_ELEMENTS  # 34
SEGMENT_ID = "eeg.centroid"
PLUGIN_ID = "eeg-bandpower-centroid-v1"
SCALE_FACTOR = 10_000  # Fixed-point integer scale factor for relative powers in [0.0, 1.0]


class EegPluginError(ValueError):
    """Stable rejection for invalid EEG bandpower plugin operations."""


@dataclass(frozen=True, slots=True)
class EegBandpowerModel:
    """Decoded nearest-centroid model for EEG bandpower classification."""

    centroids: NDArray[np.float64]  # shape (2, 16): class feature means in [0.0, 1.0]
    presence: NDArray[np.int64]  # shape (2,): class presence indicators (1 if seen, else 0)
    values: NDArray[np.int16]  # shape (34,): canonical packed integer vector


def round_half_toward_positive(values: NDArray[np.int64], count: int) -> NDArray[np.int64]:
    """Calculate integer division rounding half toward positive.

    Guarantees exact parity with Delta consensus and Feature 008 integer arithmetic:
      sum=1, count=2  -> 1 (0.5 rounds up to 1)
      sum=3, count=2  -> 2
      sum=0, count=2  -> 0
      sum=2, count=2  -> 1
    """
    if count <= 0 or bool(np.any(values < 0)):
        raise EegPluginError("EEG_DELTA_LOCAL_SUM_INVALID")
    quotient, remainder = np.divmod(values, count)
    rounded = quotient + (remainder * 2 >= count)
    return np.ascontiguousarray(rounded, dtype=np.int64)


def scale_bandpower_features(samples: NDArray[np.float64]) -> NDArray[np.int64]:
    """Convert relative bandpower features to canonical nonnegative fixed-point integers.

    Values are encoded as floor(x * SCALE_FACTOR + 0.5), avoiding NumPy banker's rounding
    so the local model tensor follows the same half-toward-positive rule used by Delta.
    """
    if samples.ndim != 2 or samples.shape[1] != FEATURE_COUNT:
        raise EegPluginError("EEG_FEATURES_SHAPE_INVALID")
    if not np.all(np.isfinite(samples)):
        raise EegPluginError("EEG_FEATURES_NOT_FINITE")
    if bool(np.any(samples < 0.0)) or bool(np.any(samples > 1.0)):
        raise EegPluginError("EEG_FEATURES_OUT_OF_RANGE")
    scaled = np.floor(samples * SCALE_FACTOR + 0.5).astype(np.int64)
    if bool(np.any(scaled < 0)) or bool(np.any(scaled > SCALE_FACTOR)):
        raise EegPluginError("EEG_FEATURES_SCALE_OUT_OF_RANGE")
    return np.ascontiguousarray(scaled, dtype=np.int64)


def encode_eeg_centroid_values(
    scaled_sums: NDArray[np.int64],
    counts: NDArray[np.int64],
) -> NDArray[np.int16]:
    """Encode scaled sums and counts into canonical 34-element int16 vector.

    - First 32 elements: rounded class feature centroids (scaled by SCALE_FACTOR).
    - Last 2 elements: class presence indicators (1 if count > 0, else 0).
    """
    if scaled_sums.shape != (CLASS_COUNT, FEATURE_COUNT) or counts.shape != (CLASS_COUNT,):
        raise EegPluginError("EEG_MODEL_SHAPE_INVALID")
    if bool(np.any(scaled_sums < 0)) or bool(np.any(counts < 0)):
        raise EegPluginError("EEG_MODEL_NEGATIVE_VALUES")

    values = np.zeros(TOTAL_ELEMENTS, dtype=np.int16)
    for class_idx in range(CLASS_COUNT):
        count = int(counts[class_idx])
        row = scaled_sums[class_idx]
        start = class_idx * FEATURE_COUNT
        end = start + FEATURE_COUNT
        if count == 0:
            if bool(np.any(row != 0)):
                raise EegPluginError("EEG_DELTA_EMPTY_CLASS_HAS_SUM")
            continue
        rounded = round_half_toward_positive(row, count)
        if bool(np.any(rounded > SCALE_FACTOR)):
            raise EegPluginError("EEG_CENTROID_VALUE_EXCEEDS_SCALE")
        values[start:end] = rounded.astype(np.int16)
        values[CENTROID_WEIGHT_ELEMENTS + class_idx] = 1

    return values


def validate_eeg_labels(labels: NDArray[np.uint8], *, expected_size: int) -> None:
    """Validate binary EEG labels before arithmetic or metric indexing."""
    if labels.ndim != 1 or labels.shape[0] != expected_size:
        raise EegPluginError("EEG_LABELS_SHAPE_INVALID")
    if bool(np.any((labels != 0) & (labels != 1))):
        raise EegPluginError("EEG_LABELS_OUT_OF_RANGE")


def evaluate_eeg_centroids(
    centroids: NDArray[np.float64],
    presence: NDArray[np.int64],
    samples: NDArray[np.float64],
    labels: NDArray[np.uint8],
) -> EvaluationResult:
    """Evaluate nearest-centroid classifier on EEG bandpower features."""
    if samples.ndim != 2 or samples.shape[1] != FEATURE_COUNT:
        raise EegPluginError("EEG_TEST_FEATURES_SHAPE_INVALID")
    validate_eeg_labels(labels, expected_size=samples.shape[0])

    valid_classes = presence > 0
    if not bool(np.any(valid_classes)):
        raise EegPluginError("EEG_MODEL_HAS_NO_CLASSES")

    active_centroids = np.asarray(centroids, dtype=np.float64)
    centroid_norm = np.square(active_centroids).sum(axis=1)

    # Compute Euclidean distance to each centroid
    distances = (
        np.square(samples).sum(axis=1)[:, None]
        - 2.0 * samples @ active_centroids.T
        + centroid_norm[None, :]
    )
    distances[:, ~valid_classes] = math.inf
    predicted = distances.argmin(axis=1).astype(np.uint8)

    correct = int(np.count_nonzero(predicted == labels))
    total = int(labels.size)
    confusion = np.zeros((CLASS_COUNT, CLASS_COUNT), dtype=np.int64)
    np.add.at(confusion, (labels, predicted), 1)

    per_class: list[dict[str, int]] = []
    for cls_idx in range(CLASS_COUNT):
        mask = labels == cls_idx
        cls_total = int(np.count_nonzero(mask))
        cls_correct = int(np.count_nonzero(predicted[mask] == cls_idx))
        per_class.append(
            {
                "accuracy_ppm": (cls_correct * 1_000_000 // cls_total if cls_total > 0 else 0),
                "class_id": cls_idx,
                "correct": cls_correct,
                "total": cls_total,
            }
        )

    accuracy_ppm = correct * 1_000_000 // total if total > 0 else 0
    metrics: dict[str, object] = {
        "accuracy_ppm": accuracy_ppm,
        "confusion_matrix": [[int(val) for val in row] for row in confusion],
        "correct": correct,
        "per_class": per_class,
        "total": total,
    }
    return EvaluationResult(accuracy_ppm=accuracy_ppm, loss=None, metrics=metrics)


class EegBandpowerCentroidPlugin(ModelPlugin):
    """ModelPlugin implementation for EEG bandpower nearest-centroid classifier."""

    @property
    def plugin_id(self) -> str:
        return PLUGIN_ID

    def parameter_schema(self) -> ParameterSchema:
        return ParameterSchema(
            parameters=(
                ParameterSpec(
                    name=SEGMENT_ID,
                    shape=(TOTAL_ELEMENTS,),
                    logical_dtype=LogicalDType.FLOAT32,
                    trainable=True,
                ),
            ),
            tied_aliases={},
            frozen_omission_policy=FrozenOmissionPolicy.INCLUDE_ALL,
        )

    @property
    def tensor_order(self) -> tuple[str, ...]:
        return (SEGMENT_ID,)

    @property
    def total_elements(self) -> int:
        return TOTAL_ELEMENTS

    def create_model(self, state: Any | None = None) -> EegBandpowerModel:
        if state is None:
            values = np.zeros(TOTAL_ELEMENTS, dtype=np.int16)
            centroids = np.zeros((CLASS_COUNT, FEATURE_COUNT), dtype=np.float64)
            presence = np.zeros(CLASS_COUNT, dtype=np.int64)
            return EegBandpowerModel(centroids=centroids, presence=presence, values=values)
        if isinstance(state, EegBandpowerModel):
            return state
        if isinstance(state, (np.ndarray, list, tuple)):
            return self.load_applied_checkpoint(state)
        raise EegPluginError("INVALID_EEG_MODEL_STATE")

    def train_ticket(
        self,
        *,
        ticket_id: str,
        data: Any,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Compute canonical local contribution tensor and statistics for an EEG ticket."""
        if isinstance(data, (tuple, list)) and len(data) == 2:
            samples, labels = data
        elif hasattr(data, "samples") and hasattr(data, "targets"):
            samples, labels = data.samples, data.targets
        else:
            raise EegPluginError("INVALID_EEG_TRAINING_DATA")

        samples_arr = np.asarray(samples, dtype=np.float64)
        labels_arr = np.asarray(labels, dtype=np.uint8)

        if samples_arr.ndim != 2 or samples_arr.shape[1] != FEATURE_COUNT:
            raise EegPluginError("EEG_TRAIN_FEATURES_SHAPE_INVALID")
        validate_eeg_labels(labels_arr, expected_size=samples_arr.shape[0])

        counts = np.bincount(labels_arr, minlength=CLASS_COUNT).astype(np.int64)
        scaled_samples = scale_bandpower_features(samples_arr)

        sums_list: list[np.ndarray] = []
        for cls_idx in range(CLASS_COUNT):
            cls_mask = labels_arr == cls_idx
            if np.any(cls_mask):
                sums_list.append(scaled_samples[cls_mask].sum(axis=0, dtype=np.int64))
            else:
                sums_list.append(np.zeros(FEATURE_COUNT, dtype=np.int64))

        scaled_sums = np.stack(sums_list, axis=0)
        encoded_values = encode_eeg_centroid_values(scaled_sums, counts)

        metadata: dict[str, object] = {
            "class_counts": counts.tolist(),
            "contribution_type": "CANONICAL_LOCAL_CENTROID_TENSOR",
            "sample_count": int(labels_arr.size),
            "ticket_id": ticket_id,
        }
        return LocalTrainingResult(
            ticket_id=ticket_id,
            tensors={SEGMENT_ID: encoded_values.astype(np.float32)},
            metadata=metadata,
        )

    def load_applied_checkpoint(
        self,
        checkpoint_values: Sequence[int] | NDArray[Any],
        parent_model: Any | None = None,
    ) -> EegBandpowerModel:
        """Decode applied checkpoint coordinate vector into centroids and presence."""
        raw = np.asarray(checkpoint_values)
        if raw.size != TOTAL_ELEMENTS or (raw.ndim > 1 and raw.shape != (TOTAL_ELEMENTS,)):
            raise EegPluginError(
                f"CHECKPOINT_SHAPE_MISMATCH: expected {TOTAL_ELEMENTS}, got {raw.size}"
            )
        flat = raw.reshape(-1)
        if not np.issubdtype(flat.dtype, np.integer):
            raise EegPluginError("CHECKPOINT_VALUES_NOT_INTEGER")

        centroid_raw = flat[:CENTROID_WEIGHT_ELEMENTS].astype(np.int64)
        presence_values = flat[CENTROID_WEIGHT_ELEMENTS:].astype(np.int64)

        if bool(np.any(centroid_raw < 0)) or bool(np.any(centroid_raw > SCALE_FACTOR)):
            raise EegPluginError("CHECKPOINT_CENTROID_OUT_OF_RANGE")
        if bool(np.any((presence_values != 0) & (presence_values != 1))):
            raise EegPluginError("CHECKPOINT_PRESENCE_INVALID")

        values = flat.astype(np.int16)
        if not np.array_equal(values.astype(np.int64), flat.astype(np.int64)):
            raise EegPluginError("CHECKPOINT_INT16_OVERFLOW")

        centroids = (
            centroid_raw.reshape(CLASS_COUNT, FEATURE_COUNT).astype(np.float64) / SCALE_FACTOR
        )
        presence = np.ascontiguousarray(presence_values, dtype=np.int64)
        return EegBandpowerModel(centroids=centroids, presence=presence, values=values)

    def evaluate(self, model: Any, test_data: Any) -> EvaluationResult:
        if not isinstance(model, EegBandpowerModel):
            model = self.create_model(model)
        if isinstance(test_data, (tuple, list)) and len(test_data) == 2:
            samples, labels = test_data
        elif hasattr(test_data, "samples") and hasattr(test_data, "targets"):
            samples, labels = test_data.samples, test_data.targets
        else:
            raise EegPluginError("INVALID_EEG_TEST_DATA")

        return evaluate_eeg_centroids(
            model.centroids,
            model.presence,
            np.asarray(samples, dtype=np.float64),
            np.asarray(labels, dtype=np.uint8),
        )
