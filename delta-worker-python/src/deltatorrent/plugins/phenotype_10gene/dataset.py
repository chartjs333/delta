"""Synthetic 10-gene cohort dataset provider for phenotype classification."""

from __future__ import annotations

import hashlib

import torch

from deltatorrent.plugins.workload import DatasetProvider

GENE_SYMBOLS = (
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


class Synthetic10GeneCohortProvider(DatasetProvider):
    """Deterministic synthetic cohort dataset provider matching synthetic-10gene-cohort-v1."""

    def __init__(
        self,
        num_samples: int = 200,
        train_ratio: float = 0.8,
        seed: int = 42,
    ) -> None:
        if num_samples < 20 or num_samples % 2 != 0:
            raise ValueError("num_samples must be an even integer >= 20")
        if not (0.1 <= train_ratio <= 0.9):
            raise ValueError("train_ratio must be between 0.1 and 0.9")

        self._num_samples = num_samples
        self._train_ratio = train_ratio
        self._seed = seed

        # Generate deterministic cohorts
        generator = torch.Generator().manual_seed(seed)
        half_n = num_samples // 2

        # Class 0: Control cohort (mean -0.5, std 0.3)
        c0_features = torch.randn(half_n, 10, generator=generator) * 0.3 - 0.5
        c0_labels = torch.zeros(half_n, dtype=torch.int64)

        # Class 1: Carrier / Phenotypic risk cohort (mean +0.5, std 0.3)
        c1_features = torch.randn(half_n, 10, generator=generator) * 0.3 + 0.5
        c1_labels = torch.ones(half_n, dtype=torch.int64)

        # Interleave to preserve balance
        features = torch.empty(num_samples, 10, dtype=torch.float32)
        labels = torch.empty(num_samples, dtype=torch.int64)
        features[0::2] = c0_features
        features[1::2] = c1_features
        labels[0::2] = c0_labels
        labels[1::2] = c1_labels

        num_train = int(num_samples * train_ratio)
        # Ensure even split for training balance
        if num_train % 2 != 0:
            num_train -= 1

        self._train_features = features[:num_train].clone()
        self._train_labels = labels[:num_train].clone()
        self._test_features = features[num_train:].clone()
        self._test_labels = labels[num_train:].clone()

        # Compute canonical dataset digest from entire dataset bytes
        raw_bytes = (
            self._train_features.numpy().astype("<f4").tobytes()
            + self._train_labels.numpy().astype("<i8").tobytes()
            + self._test_features.numpy().astype("<f4").tobytes()
            + self._test_labels.numpy().astype("<i8").tobytes()
        )
        self._dataset_digest = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"

    @property
    def dataset_id(self) -> str:
        return "synthetic-10gene-cohort-v1"

    @property
    def sample_kind(self) -> str:
        return "tabular/genomic-10gene-vector"

    @property
    def target_kind(self) -> str:
        return "class-id/0-1"

    def load_train(self) -> tuple[torch.Tensor, torch.Tensor]:
        return self._train_features.clone(), self._train_labels.clone()

    def load_test(self) -> tuple[torch.Tensor, torch.Tensor]:
        return self._test_features.clone(), self._test_labels.clone()

    def dataset_digest(self) -> str:
        return self._dataset_digest

    def validate_sample(
        self,
        features: torch.Tensor,
        targets: torch.Tensor | None = None,
    ) -> None:
        """Strict domain validation for 10-gene tabular vectors."""
        if not isinstance(features, torch.Tensor):
            raise ValueError("Features must be a torch.Tensor")
        if features.ndim != 2 or features.shape[1] != 10:
            raise ValueError(f"Features must have shape (N, 10), got {tuple(features.shape)}")
        if targets is not None:
            if not isinstance(targets, torch.Tensor):
                raise ValueError("Targets must be a torch.Tensor")
            if targets.ndim != 1 or targets.shape[0] != features.shape[0]:
                raise ValueError(
                    f"Targets must have shape (N,) matching features N={features.shape[0]}, "
                    f"got {tuple(targets.shape)}"
                )
            unique = set(targets.tolist())
            if not unique.issubset({0, 1}):
                raise ValueError(f"Targets must be binary in {{0, 1}}, got {unique}")
