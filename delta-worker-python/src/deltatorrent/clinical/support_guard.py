"""Local-support OOD guard for dominant-cluster phenotype predictions."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

import torch
from torch import Tensor
from torch.nn import functional as F

from deltatorrent.clinical.canonical_features import (
    AAO_GROUPS,
    FAMILY_HISTORY_VALUES,
    INHERITANCE_VALUES,
    SEX_VALUES,
    ZYGOSITY_VALUES,
)
from deltatorrent.clinical.classifier import ClinicalEncoder
from deltatorrent.clinical.gold_loader import ClinicalRecord
from deltatorrent.clinical.uncertainty import (
    AMBIGUOUS_GENE_CLUSTER,
    DEFINITIVE_GENE,
    DOMINANT_CLUSTER_GENES,
)

LOW_LOCAL_TRAIN_SUPPORT = "LOW_LOCAL_TRAIN_SUPPORT"
LOW_PUBLICATION_DIVERSITY = "LOW_PUBLICATION_DIVERSITY"
LOW_FAMILY_DIVERSITY = "LOW_FAMILY_DIVERSITY"
DOMINANT_CLUSTER_OOD = "DOMINANT_CLUSTER_OOD"

SUPPORT_GUARD_REASONS: tuple[str, ...] = (
    LOW_LOCAL_TRAIN_SUPPORT,
    LOW_PUBLICATION_DIVERSITY,
    LOW_FAMILY_DIVERSITY,
    DOMINANT_CLUSTER_OOD,
)


@dataclass(frozen=True, slots=True)
class SupportGuardThresholds:
    k_neighbors: int
    neighbor_similarity_floor: float
    min_nearest_neighbor_similarity: float
    min_effective_neighbor_count: int
    min_top1_gene_neighbor_share: float
    min_unique_publications: int
    min_unique_families: int
    max_publication_concentration: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NeighborWindow:
    similarities: tuple[float, ...]
    indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class LocalSupportStats:
    k_neighbors: int
    neighbor_similarity_floor: float
    nearest_neighbor_similarity: float
    effective_neighbor_count: int
    gene_distribution: dict[str, int]
    gene_similarity_mass: dict[str, float]
    unique_publications: int
    unique_families: int
    local_publication_concentration: float
    top_neighbors: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def canonical_support_matrix(
    encoder: ClinicalEncoder,
    records: tuple[ClinicalRecord, ...],
) -> Tensor:
    """Encode records into the same non-leaking canonical feature families."""

    data = encoder.encode_records(records)
    return torch.cat(
        [
            data.phenotype,
            data.pedigree,
            F.one_hot(data.sex, num_classes=len(SEX_VALUES)).float(),
            F.one_hot(data.aao_group, num_classes=len(AAO_GROUPS)).float(),
            F.one_hot(data.zygosity, num_classes=len(ZYGOSITY_VALUES)).float(),
            F.one_hot(data.inheritance, num_classes=len(INHERITANCE_VALUES)).float(),
            F.one_hot(
                data.family_history,
                num_classes=len(FAMILY_HISTORY_VALUES),
            ).float(),
            data.aao_numeric,
            data.aao_missing,
        ],
        dim=1,
    )


def _normalize_rows(matrix: Tensor) -> Tensor:
    norms = torch.linalg.vector_norm(matrix, ord=2, dim=1, keepdim=True)
    return matrix / torch.clamp(norms, min=1e-12)


@dataclass(frozen=True, slots=True)
class DominantClusterSupportIndex:
    records: tuple[ClinicalRecord, ...]
    vectors: Tensor
    cluster_genes: tuple[str, ...] = DOMINANT_CLUSTER_GENES

    @classmethod
    def from_records(
        cls,
        encoder: ClinicalEncoder,
        records: tuple[ClinicalRecord, ...],
        *,
        cluster_genes: tuple[str, ...] = DOMINANT_CLUSTER_GENES,
    ) -> DominantClusterSupportIndex:
        cluster_records = tuple(record for record in records if record.gene in cluster_genes)
        if not cluster_records:
            raise ValueError("DOMINANT_CLUSTER_TRAIN_SUPPORT_EMPTY")
        return cls(
            records=cluster_records,
            vectors=_normalize_rows(canonical_support_matrix(encoder, cluster_records)),
            cluster_genes=cluster_genes,
        )

    def topk_windows(
        self,
        encoder: ClinicalEncoder,
        records: tuple[ClinicalRecord, ...],
        *,
        max_k: int,
        batch_size: int = 512,
    ) -> list[NeighborWindow]:
        if max_k <= 0:
            raise ValueError("MAX_K_MUST_BE_POSITIVE")
        k = min(max_k, len(self.records))
        if not records:
            return []

        query_vectors = _normalize_rows(canonical_support_matrix(encoder, records))
        windows: list[NeighborWindow] = []
        for start in range(0, int(query_vectors.shape[0]), batch_size):
            batch = query_vectors[start : start + batch_size]
            similarities = torch.matmul(batch, self.vectors.T)
            values, indices = torch.topk(similarities, k=k, dim=1, largest=True, sorted=True)
            for row_values, row_indices in zip(values, indices, strict=True):
                windows.append(
                    NeighborWindow(
                        similarities=tuple(float(value) for value in row_values.tolist()),
                        indices=tuple(int(index) for index in row_indices.tolist()),
                    )
                )
        return windows

    def summarize_window(
        self,
        window: NeighborWindow,
        *,
        k_neighbors: int,
        neighbor_similarity_floor: float,
        top_neighbor_limit: int = 10,
    ) -> LocalSupportStats:
        if k_neighbors <= 0:
            raise ValueError("K_NEIGHBORS_MUST_BE_POSITIVE")
        k = min(k_neighbors, len(window.indices))
        selected = [
            (similarity, index)
            for similarity, index in zip(
                window.similarities[:k],
                window.indices[:k],
                strict=True,
            )
            if similarity >= neighbor_similarity_floor
        ]
        gene_counts: Counter[str] = Counter()
        gene_mass: defaultdict[str, float] = defaultdict(float)
        publication_counts: Counter[str] = Counter()
        families: set[str] = set()
        top_neighbors: list[dict[str, object]] = []
        for rank, (similarity, index) in enumerate(selected, start=1):
            record = self.records[index]
            gene_counts[record.gene] += 1
            gene_mass[record.gene] += similarity
            publication_counts[record.publication_id] += 1
            families.add(record.family_id)
            if rank <= top_neighbor_limit:
                top_neighbors.append(
                    {
                        "rank": rank,
                        "record_id": record.record_id,
                        "gene": record.gene,
                        "publication_id": record.publication_id,
                        "family_id": record.family_id,
                        "similarity": similarity,
                    }
                )
        effective_neighbor_count = len(selected)
        max_publication_count = max(publication_counts.values(), default=0)
        return LocalSupportStats(
            k_neighbors=k,
            neighbor_similarity_floor=neighbor_similarity_floor,
            nearest_neighbor_similarity=window.similarities[0] if window.similarities else 0.0,
            effective_neighbor_count=effective_neighbor_count,
            gene_distribution=dict(sorted(gene_counts.items())),
            gene_similarity_mass={
                gene: float(value) for gene, value in sorted(gene_mass.items())
            },
            unique_publications=len(publication_counts),
            unique_families=len(families),
            local_publication_concentration=(
                max_publication_count / effective_neighbor_count
                if effective_neighbor_count
                else 1.0
            ),
            top_neighbors=top_neighbors,
        )


def support_guard_reasons(
    stats: LocalSupportStats,
    thresholds: SupportGuardThresholds,
    *,
    top1_gene: str | None = None,
) -> tuple[str, ...]:
    """Return generic local-support reasons for downgrading a definitive call."""

    reasons: list[str] = []
    if stats.nearest_neighbor_similarity < thresholds.min_nearest_neighbor_similarity:
        reasons.append(DOMINANT_CLUSTER_OOD)
    top1_gene_neighbor_share = 1.0
    if top1_gene is not None:
        top1_gene_neighbor_share = (
            stats.gene_distribution.get(top1_gene, 0) / stats.effective_neighbor_count
            if stats.effective_neighbor_count
            else 0.0
        )
    if (
        stats.effective_neighbor_count < thresholds.min_effective_neighbor_count
        or top1_gene_neighbor_share < thresholds.min_top1_gene_neighbor_share
    ):
        reasons.append(LOW_LOCAL_TRAIN_SUPPORT)
    if (
        stats.unique_publications < thresholds.min_unique_publications
        or stats.local_publication_concentration
        > thresholds.max_publication_concentration
    ):
        reasons.append(LOW_PUBLICATION_DIVERSITY)
    if stats.unique_families < thresholds.min_unique_families:
        reasons.append(LOW_FAMILY_DIVERSITY)
    return tuple(reasons)


def should_downgrade_support_guard(
    *,
    current_status: str,
    top1_gene: str,
    stats: LocalSupportStats,
    thresholds: SupportGuardThresholds,
    cluster_genes: tuple[str, ...] = DOMINANT_CLUSTER_GENES,
) -> tuple[bool, tuple[str, ...]]:
    """Decide whether the support guard may downgrade a cluster prediction."""

    if current_status != DEFINITIVE_GENE:
        return False, ()
    if top1_gene not in cluster_genes:
        return False, ()
    reasons = support_guard_reasons(stats, thresholds, top1_gene=top1_gene)
    return bool(reasons), reasons


def support_guard_status(
    *,
    current_status: str,
    top1_gene: str,
    stats: LocalSupportStats,
    thresholds: SupportGuardThresholds,
    cluster_genes: tuple[str, ...] = DOMINANT_CLUSTER_GENES,
) -> dict[str, object]:
    downgraded, reasons = should_downgrade_support_guard(
        current_status=current_status,
        top1_gene=top1_gene,
        stats=stats,
        thresholds=thresholds,
        cluster_genes=cluster_genes,
    )
    return {
        "status": AMBIGUOUS_GENE_CLUSTER if downgraded else current_status,
        "support_guard_downgraded": downgraded,
        "support_guard_reasons": list(reasons),
        "top1_local_gene_neighbor_share": (
            stats.gene_distribution.get(top1_gene, 0) / stats.effective_neighbor_count
            if stats.effective_neighbor_count
            else 0.0
        ),
        "local_support": stats.to_dict(),
        "support_guard_thresholds": thresholds.to_dict(),
    }
