"""Runnable SDK tutorial: local CPU example, not a consensus or quality result."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from deltatorrent.data.base import DataPartition, DatasetDescriptor
from deltatorrent.data.registry import DatasetRegistry
from deltatorrent.domain.parameters import (
    FrozenOmissionPolicy,
    LogicalDType,
    ParameterSchema,
    ParameterSpec,
)
from deltatorrent.model_plugins.base import EvaluationResult, LocalTrainingResult, PluginDescriptor
from deltatorrent.model_plugins.registry import ModelPluginRegistry
from deltatorrent.model_plugins.runner import ModelPluginRunner

# --- DATASET ---
DATA = DatasetDescriptor(
    dataset_id="sdk-points-v1",
    display_name="SDK points",
    sample_kind="vector/sdk-1d",
    target_kind="class-id/0-1",
    deterministic=True,
    supports_offline_cache=True,
    description="Four training points and four separate evaluation points.",
)


class PointsProvider:
    dataset_id = DATA.dataset_id

    def descriptor(self):
        return DATA

    def materialize(self, cache_dir: Path, *, allow_download: bool):
        # The fixture is in this file; no network or cache write is needed.
        return {"dataset_id": self.dataset_id, "source": "embedded", "downloaded": False}

    def training_partition(self, partition_id: str):
        if partition_id != "train-0":
            raise ValueError("UNKNOWN_PARTITION")
        return DataPartition(
            partition_id=partition_id,
            samples=np.array([[-4], [-2], [2], [4]], dtype=np.float32),
            targets=np.array([0, 0, 1, 1], dtype=np.int64),
            metadata={"split": "train", "fixture_version": "1"},
        )

    def evaluation_data(self):
        return (
            np.array([[-5], [-1], [1], [5]], dtype=np.float32),
            np.array([0, 0, 1, 1], dtype=np.int64),
        )


# --- MODEL ---
SCHEMA = ParameterSchema(
    parameters=(ParameterSpec("centroids", (2,), LogicalDType.FLOAT32, True),),
    tied_aliases={},
    frozen_omission_policy=FrozenOmissionPolicy.INCLUDE_ALL,
)
MODEL = PluginDescriptor(
    plugin_id="sdk-centroid-v1",
    display_name="SDK nearest centroid",
    model_family="centroid",
    task_type="classification",
    sample_kind=DATA.sample_kind,
    target_kind=DATA.target_kind,
    deterministic=True,
    supports_stage_c_real_drq1=False,
    parameter_schema_id=SCHEMA.fingerprint,
)


def validated_data(data):
    samples, targets = (np.asarray(value) for value in data)
    if samples.ndim != 2 or samples.shape[1] != 1 or not len(samples):
        raise ValueError("SAMPLE_SHAPE_INVALID")
    if not np.issubdtype(samples.dtype, np.number) or np.iscomplexobj(samples):
        raise ValueError("SAMPLES_NOT_REAL")
    if not np.all(np.isfinite(samples)) or np.any(np.abs(samples) > 16):
        raise ValueError("SAMPLES_OUT_OF_RANGE")
    if targets.shape != (len(samples),) or not np.issubdtype(targets.dtype, np.integer):
        raise ValueError("TARGET_SHAPE_OR_DTYPE_INVALID")
    if not np.all(np.isin(targets, [0, 1])):
        raise ValueError("TARGETS_OUT_OF_RANGE")
    return samples.astype(np.float32), targets


class CentroidPlugin:
    plugin_id = MODEL.plugin_id
    tensor_order = ("centroids",)
    total_elements = 2

    def parameter_schema(self):
        return SCHEMA

    def create_model(self, state=None):
        if state is None:
            return np.zeros(2, dtype=np.float32)
        result = np.asarray(state)
        if result.shape != (2,) or not np.issubdtype(result.dtype, np.number):
            raise ValueError("MODEL_SHAPE_OR_DTYPE_INVALID")
        if np.iscomplexobj(result) or not np.all(np.isfinite(result)):
            raise ValueError("MODEL_NOT_FINITE_REAL")
        if np.any(np.abs(result) > 16):
            raise ValueError("MODEL_OUT_OF_RANGE")
        return result.astype(np.float32, copy=True)

    def train_ticket(self, *, ticket_id, data, parent_model=None, **kwargs):
        if not isinstance(ticket_id, str) or not ticket_id:
            raise ValueError("TICKET_ID_REQUIRED")
        # This tutorial computes fresh statistics; it does not support parent updates.
        if parent_model is not None or kwargs:
            raise ValueError("TUTORIAL_SUPPORTS_FRESH_STATISTICS_ONLY")
        samples, targets = validated_data(data)
        if set(targets.tolist()) != {0, 1}:
            raise ValueError("BOTH_CLASSES_REQUIRED")
        centroids = np.array(
            [samples[targets == label, 0].mean() for label in (0, 1)], dtype=np.float32
        )
        return LocalTrainingResult(
            ticket_id=ticket_id,
            tensors={"centroids": centroids},
            metadata={"sample_count": len(samples), "scope": "LOCAL_SDK_EXAMPLE"},
        )

    def load_applied_checkpoint(self, checkpoint_values, parent_model=None):
        # Tutorial codec: two integer coordinates at scale 1. No QC is asserted.
        values = np.asarray(checkpoint_values)
        if parent_model is not None or not np.issubdtype(values.dtype, np.integer):
            raise ValueError("INTEGER_COORDINATES_REQUIRED")
        return self.create_model(values)

    def evaluate(self, model, test_data):
        centroids = self.create_model(model)
        samples, targets = validated_data(test_data)
        distances = np.square(samples[:, 0, None] - centroids[None, :])
        predictions = distances.argmin(axis=1)
        correct = int(np.count_nonzero(predictions == targets))
        return EvaluationResult(
            accuracy_ppm=correct * 1_000_000 // len(targets),
            loss=None,
            metrics={"correct": correct, "total": len(targets)},
        )


# --- REGISTER AND RUN ---
def build_runner():
    models = ModelPluginRegistry()
    datasets = DatasetRegistry()
    models.register(MODEL, CentroidPlugin)
    datasets.register(DATA, PointsProvider)
    return ModelPluginRunner(
        plugin_id=MODEL.plugin_id,
        dataset_id=DATA.dataset_id,
        execution_scope="PLUGIN_BOUNDARY",
        model_registry=models,
        dataset_registry=datasets,
    )


def main():
    runner = build_runner()
    runner.materialize_dataset(allow_download=False)
    trained = runner.train_ticket(ticket_id="sdk-ticket-01", partition_id="train-0")
    model = runner.model_plugin.create_model(trained.tensors["centroids"])
    result = runner.evaluate(model)
    print(
        json.dumps(
            {
                "scope": "LOCAL_SDK_EXAMPLE",
                "centroids": model.tolist(),
                "accuracy_ppm": result.accuracy_ppm,
                "evaluated_samples": result.metrics["total"],
                "consensus_executed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
