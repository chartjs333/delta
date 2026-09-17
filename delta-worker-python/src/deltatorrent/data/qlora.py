"""DatasetProvider implementation for Tiny QLoRA 2D regression profiles.

Encapsulates deterministic 2D regression batches for QLoRA adapter training
and evaluation within the generic DatasetProvider protocol.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import numpy as np

from deltatorrent.data.base import (
    DataPartition,
    DatasetDescriptor,
    DatasetProvider,
    DatasetProviderError,
)
from deltatorrent.qlora.tiny_profile import (
    QLORA_DATASET_ID,
    evaluation_batch,
    worker_batches,
)

QLORA_DATASET_DESCRIPTOR: Final[DatasetDescriptor] = DatasetDescriptor(
    dataset_id=QLORA_DATASET_ID,
    display_name="Tiny QLoRA 2D Regression Dataset",
    sample_kind="vector/tiny-qlora-2d",
    target_kind="regression/vector-2d",
    deterministic=True,
    supports_offline_cache=False,
    description="Deterministic synthetic 2D regression dataset for QLoRA adapter training.",
    version="1.0.0",
)

DEMO_QLORA_PARTITIONS: Final[tuple[str, ...]] = (
    "demo-qlora-worker-01",
    "demo-qlora-worker-02",
    "demo-qlora-worker-03",
    "demo-qlora-worker-04",
)


class TinyQloraDatasetProvider(DatasetProvider):
    """DatasetProvider serving canonical 2D regression data for QLoRA adapter models."""

    def __init__(self) -> None:
        raw_batches = worker_batches()
        eval_batch = evaluation_batch()

        partitions: dict[str, DataPartition] = {}
        for idx, (p_name, batch) in enumerate(zip(DEMO_QLORA_PARTITIONS, raw_batches, strict=True)):
            samples = batch.inputs.detach().cpu().numpy().astype(np.float32)
            targets = batch.targets.detach().cpu().numpy().astype(np.float32)
            metadata = {
                "batch_index": idx,
                "dataset_id": QLORA_DATASET_ID,
                "partition_id": p_name,
                "sample_count": int(samples.shape[0]),
                "token_count": int(batch.token_count),
            }
            partition = DataPartition(
                partition_id=p_name,
                samples=samples,
                targets=targets,
                metadata=MappingProxyType(metadata),
            )
            partitions[p_name] = partition
            # Also register short alias and numeric alias
            partitions[f"worker-{idx + 1:02d}"] = partition
            partitions[str(idx)] = partition

        self._partitions: dict[str, DataPartition] = partitions
        self._eval_samples = eval_batch.inputs.detach().cpu().numpy().astype(np.float32)
        self._eval_targets = eval_batch.targets.detach().cpu().numpy().astype(np.float32)
        self._materialized: bool = True

    @property
    def dataset_id(self) -> str:
        return QLORA_DATASET_ID

    def descriptor(self) -> DatasetDescriptor:
        return QLORA_DATASET_DESCRIPTOR

    def materialize(
        self,
        cache_dir: Path | None = None,
        *,
        allow_download: bool = True,
    ) -> Mapping[str, Any]:
        """Return dataset materialization metadata."""
        return {
            "dataset_id": self.dataset_id,
            "partition_count": len(DEMO_QLORA_PARTITIONS),
            "sample_kind": QLORA_DATASET_DESCRIPTOR.sample_kind,
            "status": "materialized",
            "target_kind": QLORA_DATASET_DESCRIPTOR.target_kind,
            "total_sample_count": sum(
                len(self._partitions[p].samples) for p in DEMO_QLORA_PARTITIONS
            ),
        }

    def training_partition(self, partition_id: str) -> DataPartition:
        """Return the training data partition assigned to the specified worker."""
        if partition_id not in self._partitions:
            raise DatasetProviderError(
                f"UNKNOWN_PARTITION: '{partition_id}'. Available: {list(DEMO_QLORA_PARTITIONS)}"
            )
        return self._partitions[partition_id]

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Return the evaluation dataset as a (samples, targets) tuple."""
        return self._eval_samples.copy(), self._eval_targets.copy()


__all__ = [
    "DEMO_QLORA_PARTITIONS",
    "QLORA_DATASET_DESCRIPTOR",
    "TinyQloraDatasetProvider",
]
