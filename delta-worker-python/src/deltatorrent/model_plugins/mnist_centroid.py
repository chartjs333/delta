"""MNIST Centroid Classifier ModelPlugin implementation.

Encapsulates all MNIST-specific centroid mathematics, parameter schema, local sufficient
statistics (sums and class counts), applied-checkpoint decoding, and evaluation.
Generic Delta consensus, sharding policy, quantization, and worker runtimes interact with this
model exclusively through the ModelPlugin protocol.
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

DIGIT_COUNT = 10
PIXELS_PER_DIGIT = 28 * 28  # 784
CENTROID_WEIGHT_ELEMENTS = DIGIT_COUNT * PIXELS_PER_DIGIT  # 7840
PRESENCE_ELEMENTS = DIGIT_COUNT  # 10
TOTAL_ELEMENTS = CENTROID_WEIGHT_ELEMENTS + PRESENCE_ELEMENTS  # 7850
SEGMENT_ID = "mnist.linear"
PLUGIN_ID = "mnist-centroid-v1"


class MnistPluginError(ValueError):
    """Stable rejection for invalid MNIST centroid plugin operations."""


@dataclass(frozen=True, slots=True)
class MnistCentroidModel:
    """Decoded nearest-centroid model from checkpoint or sufficient statistics."""

    centroids: NDArray[np.int64]  # shape (10, 784): class pixel coordinate sums / means
    presence: NDArray[np.int64]  # shape (10,): class presence indicators (counts > 0)
    values: NDArray[np.int16]  # shape (7850,): canonical packed integer vector


def compute_mnist_summary(
    images: NDArray[np.uint8], labels: NDArray[np.uint8]
) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Calculate exact integer class sufficient statistics for the centroid model."""
    if images.ndim != 3 or images.shape[1:] != (28, 28) or labels.shape != (images.shape[0],):
        raise MnistPluginError("MNIST_SUMMARY_ARRAY_SHAPE_INVALID")
    flat = images.reshape(images.shape[0], 28 * 28)
    counts = np.bincount(labels, minlength=10).astype(np.int64)
    sums = np.stack(
        [flat[labels == digit].sum(axis=0, dtype=np.int64) for digit in range(10)],
        axis=0,
    )
    return np.asarray(sums, dtype=np.int64), counts


def round_half_toward_positive(values: NDArray[np.int64], count: int) -> NDArray[np.int64]:
    """Calculate integer division rounding half toward positive.

    Equivalent to quotient + (remainder * 2 >= count).
    Guarantees exact parity with Delta consensus and Feature 008 integer arithmetic:
      sum=1, count=2  -> 1 (0.5 rounds up to 1, unlike banker's rounding np.rint to 0)
      sum=3, count=2  -> 2
      sum=0, count=2  -> 0
      sum=2, count=2  -> 1
    """
    if count <= 0 or bool(np.any(values < 0)):
        raise MnistPluginError("MNIST_DELTA_LOCAL_SUM_INVALID")
    quotient, remainder = np.divmod(values, count)
    rounded = quotient + (remainder * 2 >= count)
    return np.ascontiguousarray(rounded, dtype=np.int64)


def encode_centroid_values(sums: NDArray[np.int64], counts: NDArray[np.int64]) -> NDArray[np.int16]:
    """Encode sums and counts into canonical 7850-element int16 vector.

    - First 7840 elements: rounded class pixel centroids (half-toward-positive).
    - Last 10 elements: class presence indicators (1 if count > 0, else 0).
    """
    if sums.shape != (DIGIT_COUNT, PIXELS_PER_DIGIT) or counts.shape != (DIGIT_COUNT,):
        raise MnistPluginError("MNIST_MODEL_SHAPE_INVALID")
    if bool(np.any(sums < 0)) or bool(np.any(counts < 0)):
        raise MnistPluginError("MNIST_MODEL_NEGATIVE_VALUES")
    values = np.zeros(TOTAL_ELEMENTS, dtype=np.int16)
    for digit in range(DIGIT_COUNT):
        count = int(counts[digit])
        row = sums[digit]
        start = digit * PIXELS_PER_DIGIT
        end = start + PIXELS_PER_DIGIT
        if count == 0:
            if bool(np.any(row != 0)):
                raise MnistPluginError("MNIST_DELTA_EMPTY_CLASS_HAS_SUM")
            continue
        rounded = round_half_toward_positive(row, count)
        if bool(np.any(rounded > 255)):
            raise MnistPluginError("MNIST_CENTROID_OUT_OF_RANGE")
        values[start:end] = rounded.astype(np.int16)
        values[CENTROID_WEIGHT_ELEMENTS + digit] = np.int16(1)
    return values


def evaluate_mnist_centroids(
    centroids: NDArray[np.int64],
    presence: NDArray[np.int64],
    images: NDArray[np.uint8],
    labels: NDArray[np.uint8],
) -> EvaluationResult:
    """Measure nearest-centroid predictions against test images and labels."""
    if centroids.shape != (10, 28 * 28) or presence.shape != (10,):
        raise MnistPluginError("MNIST_MODEL_SHAPE_INVALID")
    if images.ndim != 3 or images.shape[1:] != (28, 28) or labels.shape != (images.shape[0],):
        raise MnistPluginError("MNIST_TEST_ARRAY_SHAPE_INVALID")
    valid_classes = presence > 0
    if not bool(np.any(valid_classes)):
        raise MnistPluginError("MNIST_MODEL_HAS_NO_CLASSES")

    active_centroids = np.asarray(centroids, dtype=np.float64)
    centroid_norm = np.square(active_centroids).sum(axis=1)
    predictions: list[NDArray[np.uint8]] = []
    flat_images = images.reshape(images.shape[0], 28 * 28)
    for start in range(0, flat_images.shape[0], 512):
        batch = flat_images[start : start + 512].astype(np.float64)
        distances = (
            np.square(batch).sum(axis=1)[:, None]
            - 2.0 * batch @ active_centroids.T
            + centroid_norm[None, :]
        )
        distances[:, ~valid_classes] = math.inf
        predictions.append(distances.argmin(axis=1).astype(np.uint8))
    predicted = np.concatenate(predictions)
    correct = int(np.count_nonzero(predicted == labels))
    total = int(labels.size)
    confusion = np.zeros((10, 10), dtype=np.int64)
    np.add.at(confusion, (labels, predicted), 1)

    per_digit: list[dict[str, int]] = []
    for digit in range(10):
        mask = labels == digit
        digit_total = int(np.count_nonzero(mask))
        digit_correct = int(np.count_nonzero(predicted[mask] == digit))
        per_digit.append(
            {
                "accuracy_ppm": digit_correct * 1_000_000 // digit_total if digit_total > 0 else 0,
                "correct": digit_correct,
                "digit": digit,
                "total": digit_total,
            }
        )

    accuracy_ppm = correct * 1_000_000 // total if total > 0 else 0
    metrics: dict[str, object] = {
        "accuracy_ppm": accuracy_ppm,
        "confusion_matrix": [[int(val) for val in row] for row in confusion],
        "correct": correct,
        "per_digit": per_digit,
        "predictions": predicted,
        "total": total,
    }
    return EvaluationResult(accuracy_ppm=accuracy_ppm, loss=None, metrics=metrics)


class MnistCentroidPlugin(ModelPlugin):
    """ModelPlugin implementation for the MNIST nearest-centroid classifier."""

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

    def create_model(self, state: Any | None = None) -> MnistCentroidModel:
        if state is None:
            values = np.zeros(TOTAL_ELEMENTS, dtype=np.int16)
            centroids = np.zeros((DIGIT_COUNT, PIXELS_PER_DIGIT), dtype=np.int64)
            presence = np.zeros(DIGIT_COUNT, dtype=np.int64)
            return MnistCentroidModel(centroids=centroids, presence=presence, values=values)
        if isinstance(state, MnistCentroidModel):
            return state
        if isinstance(state, (tuple, list)) and len(state) == 2:
            sums, counts = state
            values = encode_centroid_values(np.asarray(sums), np.asarray(counts))
            centroids = (
                values[:CENTROID_WEIGHT_ELEMENTS]
                .reshape(DIGIT_COUNT, PIXELS_PER_DIGIT)
                .astype(np.int64)
            )
            presence = values[CENTROID_WEIGHT_ELEMENTS:].astype(np.int64)
            return MnistCentroidModel(centroids=centroids, presence=presence, values=values)
        if isinstance(state, (np.ndarray, list, tuple)):
            return self.load_applied_checkpoint(state)
        raise MnistPluginError("INVALID_MNIST_MODEL_STATE")

    def train_ticket(
        self,
        *,
        ticket_id: str,
        data: Any,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Compute canonical local contribution tensor and sufficient statistics for a ticket."""
        if isinstance(data, (tuple, list)) and len(data) == 2:
            images, labels = data
        elif hasattr(data, "train_images") and hasattr(data, "train_labels"):
            images, labels = data.train_images, data.train_labels
        elif hasattr(data, "images") and hasattr(data, "labels"):
            images, labels = data.images, data.labels
        else:
            raise MnistPluginError("INVALID_WORKER_TRAINING_DATA")

        sums, counts = compute_mnist_summary(np.asarray(images), np.asarray(labels))
        encoded_values = encode_centroid_values(sums, counts)

        metadata: dict[str, object] = {
            "class_counts": counts.tolist(),
            "contribution_type": "CANONICAL_LOCAL_CENTROID_TENSOR",
            "sample_count": int(labels.size),
            "ticket_id": ticket_id,
            "sufficient_statistics": {
                "sums_shape": list(sums.shape),
                "counts": counts.tolist(),
            },
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
    ) -> MnistCentroidModel:
        """Decode applied checkpoint coordinate vector into centroids and class presence.

        Enforces strict fail-closed validation:
        - Exact length == 7850
        - Centroid coordinates strictly in 0..255
        - Class presence indicators strictly 0 or 1
        - Values fit in signed 16-bit integers without wrapping
        """
        raw = np.asarray(checkpoint_values)
        if raw.size != TOTAL_ELEMENTS or (raw.ndim > 1 and raw.shape != (TOTAL_ELEMENTS,)):
            raise MnistPluginError(
                f"CHECKPOINT_SHAPE_MISMATCH: expected {TOTAL_ELEMENTS}, got {raw.size}"
            )
        flat = raw.reshape(-1)
        if not np.issubdtype(flat.dtype, np.integer):
            raise MnistPluginError("CHECKPOINT_VALUES_NOT_INTEGER")
        centroid_values = flat[:CENTROID_WEIGHT_ELEMENTS].astype(np.int64)
        presence_values = flat[CENTROID_WEIGHT_ELEMENTS:].astype(np.int64)
        if bool(np.any(centroid_values < 0)) or bool(np.any(centroid_values > 255)):
            raise MnistPluginError("CHECKPOINT_CENTROID_OUT_OF_RANGE")
        if bool(np.any((presence_values != 0) & (presence_values != 1))):
            raise MnistPluginError("CHECKPOINT_PRESENCE_INVALID")
        values = flat.astype(np.int16)
        if not np.array_equal(values.astype(np.int64), flat.astype(np.int64)):
            raise MnistPluginError("CHECKPOINT_INT16_OVERFLOW")
        centroids = np.ascontiguousarray(
            centroid_values.reshape(DIGIT_COUNT, PIXELS_PER_DIGIT), dtype=np.int64
        )
        presence = np.ascontiguousarray(presence_values, dtype=np.int64)
        return MnistCentroidModel(centroids=centroids, presence=presence, values=values)

    def evaluate(self, model: Any, test_data: Any) -> EvaluationResult:
        if not isinstance(model, MnistCentroidModel):
            model = self.create_model(model)
        if isinstance(test_data, (tuple, list)) and len(test_data) == 2:
            images, labels = test_data
        elif hasattr(test_data, "test_images") and hasattr(test_data, "test_labels"):
            images, labels = test_data.test_images, test_data.test_labels
        else:
            raise MnistPluginError("INVALID_TEST_DATA")
        return evaluate_mnist_centroids(
            model.centroids,
            model.presence,
            np.asarray(images, dtype=np.uint8),
            np.asarray(labels, dtype=np.uint8),
        )
