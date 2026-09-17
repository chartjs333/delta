"""Executable runner for 10-gene phenotype centroid workload."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from deltatorrent.plugins.phenotype_10gene.dataset import Synthetic10GeneCohortProvider
from deltatorrent.plugins.phenotype_10gene.model import Synthetic10GeneCentroidPlugin
from deltatorrent.plugins.workload import run_workload


def run_10gene_workload(
    scope: str = "STAGE_C_REAL_DRQ1",
    backend_commit: str = "670b58f6458fe84620f4f9f46401f855d04ae05d",
    repository: str = "chartjs333/delta",
    round_id: int = 1,
    wal_sequence: int = 12,
    produced_at: str | None = None,
    seed: int = 42,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Execute the 10-gene phenotype centroid workload via generic run_workload.

    Produces a real execution receipt bound to tabular-10gene-phenotype-v1 and
    synthetic-10gene-cohort-v1.
    """
    dataset_provider = Synthetic10GeneCohortProvider(seed=seed)
    model_plugin = Synthetic10GeneCentroidPlugin()

    receipt = run_workload(
        model_plugin=model_plugin,
        dataset_provider=dataset_provider,
        scope=scope,
        backend_commit=backend_commit,
        repository=repository,
        round_id=round_id,
        wal_sequence=wal_sequence,
        produced_at=produced_at,
    )

    if output_path is not None:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)
            f.write("\n")

    return receipt
