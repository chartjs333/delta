"""Synthetic 10-Gene Phenotype Centroid ModelPlugin implementation."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray

from deltatorrent.data.phenotype_10gene import (
    CLASS_COUNT,
    FEATURE_COUNT,
    validate_10gene_features_and_labels,
)
from deltatorrent.domain.parameters import (
    FrozenOmissionPolicy,
    LogicalDType,
    ParameterSchema,
    ParameterSpec,
)
from deltatorrent.model_plugins.base import (
    EvaluationResult,
    LocalTrainingResult,
    ModelPlugin,
    PluginDescriptor,
)
from deltatorrent.plugins.contract import (
    DeltaPlugin,
    abstain_response,
    plugin_incompatible_response,
)

PLUGIN_ID: Final[str] = "tabular-10gene-phenotype-v1"
SEGMENT_ID: Final[str] = "phenotype.centroid"

CENTROID_WEIGHT_ELEMENTS: Final[int] = CLASS_COUNT * FEATURE_COUNT  # 20
PRESENCE_ELEMENTS: Final[int] = CLASS_COUNT  # 2
TOTAL_ELEMENTS: Final[int] = CENTROID_WEIGHT_ELEMENTS + PRESENCE_ELEMENTS  # 22
SCALE_FACTOR: Final[int] = 10_000

PHENOTYPE_10GENE_DESCRIPTOR: Final[PluginDescriptor] = PluginDescriptor(
    plugin_id=PLUGIN_ID,
    display_name="Synthetic 10-Gene Phenotype Centroid",
    model_family="centroid",
    task_type="phenotype_classification",
    sample_kind="tabular/genomic-10gene-vector",
    target_kind="class-id/0-1",
    deterministic=True,
    supports_stage_c_real_drq1=True,
    parameter_schema_id=None,
)


class PhenotypePluginError(ValueError):
    """Stable rejection for invalid phenotype centroid plugin operations."""


@dataclass(frozen=True, slots=True)
class Phenotype10GeneModel:
    """Decoded nearest-centroid model for 10-gene phenotype classification."""

    centroids: NDArray[np.float64]  # shape (2, 10): class feature centroids
    presence: NDArray[np.int64]  # shape (2,): class presence indicators (1 if observed, else 0)
    values: NDArray[np.int16]  # shape (22,): canonical packed integer vector


def round_half_toward_positive(values: NDArray[np.int64], count: int) -> NDArray[np.int64]:
    """Calculate integer division rounding half toward positive."""
    if count <= 0:
        raise PhenotypePluginError("COUNT_MUST_BE_POSITIVE")
    quotient, remainder = np.divmod(values, count)
    rounded = quotient + (remainder * 2 >= count)
    return np.ascontiguousarray(rounded, dtype=np.int64)


def scale_10gene_features(samples: NDArray[np.float64]) -> NDArray[np.int64]:
    """Convert continuous features to canonical fixed-point integers."""
    if not bool(np.all(np.isfinite(samples))):
        raise PhenotypePluginError("FEATURES_NOT_FINITE")
    scaled = np.floor(samples * SCALE_FACTOR + 0.5).astype(np.int64)
    return np.ascontiguousarray(scaled, dtype=np.int64)


def encode_10gene_centroid_values(
    scaled_sums: NDArray[np.int64],
    counts: NDArray[np.int64],
) -> NDArray[np.int16]:
    """Encode scaled sums and counts into canonical 22-element int16 vector."""
    if scaled_sums.shape != (CLASS_COUNT, FEATURE_COUNT) or counts.shape != (CLASS_COUNT,):
        raise PhenotypePluginError("ENCODE_SHAPE_INVALID")

    values = np.zeros(TOTAL_ELEMENTS, dtype=np.int16)
    for cls_idx in range(CLASS_COUNT):
        count = int(counts[cls_idx])
        row = scaled_sums[cls_idx]
        start = cls_idx * FEATURE_COUNT
        end = start + FEATURE_COUNT
        if count == 0:
            continue
        rounded = round_half_toward_positive(row, count)
        values[start:end] = rounded.astype(np.int16)
        values[CENTROID_WEIGHT_ELEMENTS + cls_idx] = 1

    return values


def evaluate_10gene_centroids(
    centroids: NDArray[np.float64],
    presence: NDArray[np.int64],
    samples: NDArray[np.float64],
    labels: NDArray[np.int64],
) -> EvaluationResult:
    """Evaluate nearest-centroid classifier on 10-gene features."""
    validate_10gene_features_and_labels(samples, labels)

    valid_classes = presence > 0
    if not bool(np.any(valid_classes)):
        raise PhenotypePluginError("MODEL_HAS_NO_CLASSES")

    active_centroids = np.asarray(centroids, dtype=np.float64)
    centroid_norm = np.square(active_centroids).sum(axis=1)

    # Compute Euclidean distance squared to each centroid
    distances = (
        np.square(samples).sum(axis=1)[:, None]
        - 2.0 * samples @ active_centroids.T
        + centroid_norm[None, :]
    )
    distances[:, ~valid_classes] = math.inf
    predicted = distances.argmin(axis=1).astype(np.int64)

    correct = int(np.count_nonzero(predicted == labels))
    total = int(labels.size)
    confusion = np.zeros((CLASS_COUNT, CLASS_COUNT), dtype=np.int64)
    np.add.at(confusion, (labels, predicted), 1)

    accuracy_ppm = correct * 1_000_000 // total if total > 0 else 0
    metrics: dict[str, object] = {
        "accuracy_ppm": accuracy_ppm,
        "confusion_matrix": [[int(val) for val in row] for row in confusion],
        "correct": correct,
        "total": total,
    }
    return EvaluationResult(
        accuracy_ppm=accuracy_ppm,
        loss=None,
        metrics=metrics,
    )


class Synthetic10GeneCentroidPlugin(ModelPlugin, DeltaPlugin):
    """Nearest centroid classifier for 10-gene tabular phenotype vectors.

    Conforms to both ModelPlugin and DeltaPlugin structural protocols.
    """

    def __init__(self) -> None:
        self._schema = ParameterSchema(
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
        self._current_model: Phenotype10GeneModel | None = None

    @property
    def plugin_id(self) -> str:
        return PLUGIN_ID

    def parameter_schema(self) -> ParameterSchema:
        return self._schema

    @property
    def tensor_order(self) -> tuple[str, ...]:
        return (SEGMENT_ID,)

    @property
    def total_elements(self) -> int:
        return TOTAL_ELEMENTS

    def create_model(self, state: Any | None = None) -> Phenotype10GeneModel:
        """Create a model instance from optional checkpoint values or zeros."""
        if state is None:
            centroids = np.zeros((CLASS_COUNT, FEATURE_COUNT), dtype=np.float64)
            presence = np.zeros(CLASS_COUNT, dtype=np.int64)
            values = np.zeros(TOTAL_ELEMENTS, dtype=np.int16)
            model = Phenotype10GeneModel(centroids=centroids, presence=presence, values=values)
            self._current_model = model
            return model
        if isinstance(state, Phenotype10GeneModel):
            self._current_model = state
            return state
        return self.load_applied_checkpoint(state)

    def train_ticket(
        self,
        *,
        ticket_id: str,
        data: Any,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        """Train a ticket on 10-gene partition data."""
        if not ticket_id or not isinstance(ticket_id, str):
            raise PhenotypePluginError("INVALID_TICKET_ID")
        if not isinstance(data, (tuple, list)) or len(data) != 2:
            raise PhenotypePluginError("INVALID_TICKET_DATA_TUPLE")

        samples, labels = data
        samples_arr, labels_arr = validate_10gene_features_and_labels(samples, labels)
        assert labels_arr is not None

        counts = np.bincount(labels_arr, minlength=CLASS_COUNT).astype(np.int64)
        scaled_samples = scale_10gene_features(samples_arr)

        sums_list: list[NDArray[np.int64]] = []
        for cls_idx in range(CLASS_COUNT):
            cls_mask = labels_arr == cls_idx
            if np.any(cls_mask):
                sums_list.append(scaled_samples[cls_mask].sum(axis=0, dtype=np.int64))
            else:
                sums_list.append(np.zeros(FEATURE_COUNT, dtype=np.int64))

        scaled_sums = np.stack(sums_list, axis=0)
        encoded_values = encode_10gene_centroid_values(scaled_sums, counts)

        # Update local model state
        self._current_model = self.load_applied_checkpoint(encoded_values)

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
    ) -> Phenotype10GeneModel:
        """Decode checkpoint vector into centroids and presence."""
        raw = np.asarray(checkpoint_values)
        if raw.size != TOTAL_ELEMENTS or (raw.ndim > 1 and raw.shape != (TOTAL_ELEMENTS,)):
            raise PhenotypePluginError(
                f"CHECKPOINT_SHAPE_MISMATCH: expected {TOTAL_ELEMENTS}, got {raw.size}"
            )
        flat = raw.reshape(-1)
        if not np.issubdtype(flat.dtype, np.integer):
            raise PhenotypePluginError("CHECKPOINT_VALUES_NOT_INTEGER")

        centroid_raw = flat[:CENTROID_WEIGHT_ELEMENTS].astype(np.int64)
        presence_values = flat[CENTROID_WEIGHT_ELEMENTS:].astype(np.int64)

        if bool(np.any((presence_values != 0) & (presence_values != 1))):
            raise PhenotypePluginError("CHECKPOINT_PRESENCE_INVALID")

        values = flat.astype(np.int16)
        if not np.array_equal(values.astype(np.int64), flat.astype(np.int64)):
            raise PhenotypePluginError("CHECKPOINT_INT16_OVERFLOW")

        centroids = (
            centroid_raw.reshape(CLASS_COUNT, FEATURE_COUNT).astype(np.float64) / SCALE_FACTOR
        )
        presence = np.ascontiguousarray(presence_values, dtype=np.int64)
        model = Phenotype10GeneModel(centroids=centroids, presence=presence, values=values)
        self._current_model = model
        return model

    def evaluate(self, model: Any, test_data: Any) -> EvaluationResult:
        """Evaluate model against 10-gene test data."""
        if isinstance(model, Synthetic10GeneCentroidPlugin):
            if model._current_model is not None:
                model = model._current_model
            else:
                model = self.create_model()
        elif not isinstance(model, Phenotype10GeneModel):
            model = self.create_model(model)
        if isinstance(test_data, (tuple, list)) and len(test_data) == 2:
            samples, labels = test_data
        elif hasattr(test_data, "samples") and hasattr(test_data, "targets"):
            samples, labels = test_data.samples, test_data.targets
        else:
            raise PhenotypePluginError("INVALID_TEST_DATA")

        samples_arr, labels_arr = validate_10gene_features_and_labels(samples, labels)
        assert labels_arr is not None

        return evaluate_10gene_centroids(
            model.centroids,
            model.presence,
            samples_arr,
            labels_arr,
        )

    # --- DeltaPlugin Protocol Implementation ---

    def canonical_model_digest(self) -> str:
        """Return deterministic SHA-256 of canonical int16 parameter values."""
        if self._current_model is None or not np.any(self._current_model.presence > 0):
            raise RuntimeError("MODEL_NOT_TRAINED")
        raw_bytes = self._current_model.values.astype("<i2").tobytes()
        return f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"

    def metadata(self) -> dict[str, Any]:
        """Return plugin manifest conforming to DeltaPlugin protocol."""
        try:
            model_hash = self.canonical_model_digest()[7:]
        except RuntimeError:
            model_hash = "0" * 64

        return {
            "plugin_id": PLUGIN_ID,
            "version": "1.0.0",
            "entrypoint": (
                "deltatorrent.model_plugins.phenotype_10gene:Synthetic10GeneCentroidPlugin"
            ),
            "contract": {
                "class": "DeltaPlugin",
                "methods": ["metadata", "health", "analyze"],
            },
            "compatible_delta_engines": [
                {
                    "repository": "chartjs333/delta",
                    "commit": "670b58f6458fe84620f4f9f46401f855d04ae05d",
                    "compatibility": "pinned",
                }
            ],
            "capabilities": [
                "tabular/genomic-10gene-vector",
                "class-id/0-1",
                "stage_c_real_drq1",
            ],
            "failure_policy": {"mode": "fail-closed"},
            "artifact_identity": {
                "components": [
                    {
                        "name": "centroid_parameters",
                        "path": "centroids.bin",
                        "sha256": model_hash,
                        "size_bytes": TOTAL_ELEMENTS * 2,
                    }
                ]
            },
        }

    def health(self) -> dict[str, Any]:
        """Return readiness status."""
        trained = self._current_model is not None and bool(np.any(self._current_model.presence > 0))
        return {
            "status": "READY" if trained else "UNINITIALIZED",
            "trained": trained,
            "model_digest": self.canonical_model_digest() if trained else None,
        }

    def analyze(self, request: dict[str, Any]) -> dict[str, Any]:
        """Inference endpoint conforming strictly to DeltaPlugin protocol."""
        if not isinstance(request, Mapping):
            return plugin_incompatible_response(["INVALID_REQUEST_PAYLOAD"])

        if self._current_model is None or not bool(np.any(self._current_model.presence > 0)):
            return abstain_response(["MODEL_NOT_TRAINED"])

        sample = request.get("sample")
        if not isinstance(sample, (list, tuple)) or len(sample) != FEATURE_COUNT:
            return plugin_incompatible_response(["INVALID_SAMPLE_DIMENSIONS"])

        # Finite numeric validation (Reviewer 1 High Finding)
        try:
            sample_arr = np.asarray(sample, dtype=np.float64)
        except Exception:
            return plugin_incompatible_response(["INVALID_NUMERIC_VALUES"])

        if not bool(np.all(np.isfinite(sample_arr))):
            return plugin_incompatible_response(["INVALID_NUMERIC_VALUES"])

        centroids = self._current_model.centroids
        presence = self._current_model.presence

        # Distances to each centroid
        d0 = float(np.linalg.norm(sample_arr - centroids[0])) if presence[0] > 0 else math.inf
        d1 = float(np.linalg.norm(sample_arr - centroids[1])) if presence[1] > 0 else math.inf

        pred_class = 0 if d0 <= d1 else 1
        denom = math.exp(-d0) + math.exp(-d1)
        score = math.exp(-d0 if pred_class == 0 else -d1) / denom if denom > 0 else 0.5

        return {
            "ranking": [
                {
                    "class_id": pred_class,
                    "score": round(score, 4),
                    "label": "CARRIER" if pred_class == 1 else "CONTROL",
                }
            ],
            "status": "ANALYZED",
            "reason_codes": ["CENTROID_MATCH"],
            "artifact_identity": {
                "model_digest": self.canonical_model_digest(),
            },
            "evidence": {
                "distance_c0": round(d0, 4),
                "distance_c1": round(d1, 4),
            },
        }
