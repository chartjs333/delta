"""Synthetic 10-gene cohort DatasetProvider for phenotype classification."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from deltatorrent.data.base import (
    DataPartition,
    DatasetDescriptor,
    DatasetProvider,
    DatasetProviderError,
)

GENE_SYMBOLS: Final[tuple[str, ...]] = (
    "SNCA",
    "PRKN",
    "PINK1",
    "PARK7",
    "LRRK2",
    "ATP13A2",
    "GBA1",
    "VPS35",
    "FBXO7",
    "DNAJC6",
)

FEATURE_COUNT: Final[int] = 10
CLASS_COUNT: Final[int] = 2

DATASET_ID: Final[str] = "synthetic-10gene-cohort-v1"
SAMPLE_KIND: Final[str] = "tabular/genomic-10gene-vector"
TARGET_KIND: Final[str] = "class-id/0-1"

SYNTHETIC_10GENE_DESCRIPTOR: Final[DatasetDescriptor] = DatasetDescriptor(
    dataset_id=DATASET_ID,
    display_name="Synthetic 10-Gene Cohort Benchmark",
    sample_kind=SAMPLE_KIND,
    target_kind=TARGET_KIND,
    deterministic=True,
    supports_offline_cache=True,
    description=(
        "Deterministic synthetic cohort benchmark containing normalized "
        "10-gene expression vectors for binary phenotype classification."
    ),
    version="1.0.0",
)


class Phenotype10GeneDataError(DatasetProviderError):
    """Raised when 10-gene dataset data or partitions violate domain invariants."""


def validate_10gene_features_and_labels(
    features: object,
    labels: object | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.int64] | None]:
    """Strict shared validator for 10-gene tabular vectors and binary labels."""
    try:
        feat_arr = np.asarray(features, dtype=np.float64)
    except Exception as exc:
        raise Phenotype10GeneDataError("FEATURES_NOT_NUMERIC") from exc

    if feat_arr.ndim != 2 or feat_arr.shape[1] != FEATURE_COUNT:
        raise Phenotype10GeneDataError(
            f"FEATURES_SHAPE_INVALID: expected (N, {FEATURE_COUNT}), got {feat_arr.shape}"
        )

    if not bool(np.all(np.isfinite(feat_arr))):
        raise Phenotype10GeneDataError("FEATURES_NOT_FINITE")

    label_arr: NDArray[np.int64] | None = None
    if labels is not None:
        try:
            raw_labels = np.asarray(labels)
        except Exception as exc:
            raise Phenotype10GeneDataError("LABELS_NOT_NUMERIC") from exc

        if raw_labels.ndim != 1 or raw_labels.shape[0] != feat_arr.shape[0]:
            raise Phenotype10GeneDataError(
                f"LABELS_SHAPE_INVALID: expected ({feat_arr.shape[0]},), got {raw_labels.shape}"
            )

        if not np.issubdtype(raw_labels.dtype, np.number):
            raise Phenotype10GeneDataError("LABELS_NOT_NUMERIC")

        if not bool(np.all(np.isfinite(raw_labels))):
            raise Phenotype10GeneDataError("LABELS_NOT_FINITE")

        if not np.issubdtype(raw_labels.dtype, np.integer):
            raise Phenotype10GeneDataError("LABELS_MUST_BE_INTEGERS")

        unique = set(raw_labels.tolist())
        if not unique.issubset({0, 1}):
            raise Phenotype10GeneDataError(
                f"LABELS_OUT_OF_RANGE: expected strictly {{0, 1}}, got {unique}"
            )

        label_arr = raw_labels.astype(np.int64)

    return feat_arr, label_arr


@dataclass(frozen=True, slots=True)
class Synthetic10GeneCohortProvider(DatasetProvider):
    """Canonical DatasetProvider implementation for synthetic-10gene-cohort-v1."""

    num_samples: int = 200
    train_ratio: float = 0.8
    seed: int = 42

    def __post_init__(self) -> None:
        if self.num_samples < 20 or self.num_samples % 2 != 0:
            raise Phenotype10GeneDataError("NUM_SAMPLES_MUST_BE_EVEN_GE_20")
        if not (0.1 <= self.train_ratio <= 0.9):
            raise Phenotype10GeneDataError("TRAIN_RATIO_OUT_OF_RANGE")

    @property
    def dataset_id(self) -> str:
        return DATASET_ID

    def descriptor(self) -> DatasetDescriptor:
        return SYNTHETIC_10GENE_DESCRIPTOR

    def _generate_data(self) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
        """Generate balanced, deterministic synthetic expression cohorts."""
        rng = np.random.default_rng(self.seed)
        half_n = self.num_samples // 2

        # Class 0: Control cohort (mean -0.5, std 0.3)
        c0_features = rng.normal(loc=-0.5, scale=0.3, size=(half_n, FEATURE_COUNT))
        c0_labels = np.zeros(half_n, dtype=np.int64)

        # Class 1: Carrier / Phenotypic risk cohort (mean +0.5, std 0.3)
        c1_features = rng.normal(loc=0.5, scale=0.3, size=(half_n, FEATURE_COUNT))
        c1_labels = np.ones(half_n, dtype=np.int64)

        # Interleave to preserve balance
        features = np.empty((self.num_samples, FEATURE_COUNT), dtype=np.float64)
        labels = np.empty(self.num_samples, dtype=np.int64)
        features[0::2] = c0_features
        features[1::2] = c1_features
        labels[0::2] = c0_labels
        labels[1::2] = c1_labels

        validate_10gene_features_and_labels(features, labels)
        return features, labels

    def materialize(
        self,
        cache_dir: Path,
        *,
        allow_download: bool = True,
    ) -> Mapping[str, object]:
        """Materialize synthetic dataset cache fail-closed."""
        cache_dir.mkdir(parents=True, exist_ok=True)
        features, labels = self._generate_data()

        cache_file = cache_dir / "cohort_data.json"
        raw_bytes = features.astype("<f4").tobytes() + labels.astype("<i8").tobytes()
        content_hash = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"

        manifest = {
            "dataset_id": DATASET_ID,
            "sample_count": self.num_samples,
            "feature_count": FEATURE_COUNT,
            "class_count": CLASS_COUNT,
            "content_hash": content_hash,
            "deterministic": True,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, allow_nan=False)
            f.write("\n")

        return manifest

    def training_partition(self, partition_id: str) -> DataPartition:
        """Return the training data partition."""
        features, labels = self._generate_data()
        num_train = int(self.num_samples * self.train_ratio)
        if num_train % 2 != 0:
            num_train -= 1

        train_feat = features[:num_train]
        train_lbl = labels[:num_train]

        return DataPartition(
            partition_id=partition_id,
            samples=train_feat,
            targets=train_lbl,
            metadata={
                "dataset_id": DATASET_ID,
                "sample_count": num_train,
                "partition_id": partition_id,
                "sample_kind": SAMPLE_KIND,
                "target_kind": TARGET_KIND,
            },
        )

    def evaluation_data(self) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
        """Return the evaluation data split."""
        features, labels = self._generate_data()
        num_train = int(self.num_samples * self.train_ratio)
        if num_train % 2 != 0:
            num_train -= 1

        test_feat = features[num_train:]
        test_lbl = labels[num_train:]
        return test_feat, test_lbl
