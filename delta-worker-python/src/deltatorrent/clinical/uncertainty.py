"""Uncertainty and abstention utilities for phenotype classifier outputs."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

AMBIGUOUS_GENE_CLUSTER = "AMBIGUOUS_GENE_CLUSTER"
DEFINITIVE_GENE = "DEFINITIVE_GENE"
DOMINANT_CLUSTER_GENES: tuple[str, ...] = ("LRRK2", "VPS35", "RAB32", "SNCA")


@dataclass(frozen=True, slots=True)
class UncertaintyThresholds:
    max_probability: float
    top1_top2_margin: float
    entropy: float
    entropy_is_normalized: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _entropy(probabilities: tuple[float, ...]) -> float:
    return -sum(prob * math.log(max(prob, 1e-12)) for prob in probabilities if prob > 0.0)


def uncertainty_features(probabilities: tuple[float, ...]) -> dict[str, float]:
    """Return model-output uncertainty features from a probability vector."""

    if not probabilities:
        raise ValueError("PROBABILITIES_MUST_NOT_BE_EMPTY")
    total = sum(probabilities)
    if abs(total - 1.0) > 1e-4:
        raise ValueError(f"PROBABILITIES_MUST_SUM_TO_ONE: {total}")
    if any(prob < 0.0 for prob in probabilities):
        raise ValueError("PROBABILITIES_MUST_BE_NON_NEGATIVE")

    ordered = sorted(probabilities, reverse=True)
    max_probability = ordered[0]
    second_probability = ordered[1] if len(ordered) > 1 else 0.0
    entropy = _entropy(probabilities)
    normalized_entropy = entropy / math.log(len(probabilities)) if len(probabilities) > 1 else 0.0
    return {
        "max_probability": max_probability,
        "second_probability": second_probability,
        "top1_top2_margin": max_probability - second_probability,
        "entropy": entropy,
        "normalized_entropy": normalized_entropy,
    }


def ranked_cluster(
    genes: tuple[str, ...],
    probabilities: tuple[float, ...],
    *,
    cluster_genes: tuple[str, ...] = DOMINANT_CLUSTER_GENES,
) -> list[dict[str, float | str]]:
    """Return cluster genes ranked by absolute and cluster-conditional probability."""

    probability_by_gene = dict(zip(genes, probabilities, strict=True))
    cluster_total = sum(probability_by_gene.get(gene, 0.0) for gene in cluster_genes)
    rows: list[dict[str, float | str]] = []
    for gene in cluster_genes:
        probability = probability_by_gene.get(gene, 0.0)
        rows.append(
            {
                "gene": gene,
                "probability": probability,
                "cluster_conditional_probability": probability / cluster_total
                if cluster_total
                else 0.0,
            }
        )
    rows.sort(key=lambda row: float(row["probability"]), reverse=True)
    return rows


def decide_cluster_abstention(
    genes: tuple[str, ...],
    probabilities: tuple[float, ...],
    thresholds: UncertaintyThresholds,
    *,
    cluster_genes: tuple[str, ...] = DOMINANT_CLUSTER_GENES,
) -> dict[str, object]:
    """Return a definitive gene decision or cluster-level abstention."""

    if len(genes) != len(probabilities):
        raise ValueError("GENE_PROBABILITY_LENGTH_MISMATCH")
    if len(set(genes)) != len(genes):
        raise ValueError("GENES_MUST_BE_UNIQUE")
    missing = sorted(set(cluster_genes) - set(genes))
    if missing:
        raise ValueError(f"CLUSTER_GENES_MISSING_FROM_OUTPUT: {missing}")

    ranking: list[dict[str, float | str]] = [
        {"gene": gene, "probability": probability}
        for gene, probability in zip(genes, probabilities, strict=True)
    ]
    ranking.sort(key=lambda row: float(row["probability"]), reverse=True)
    features = uncertainty_features(probabilities)
    top1_gene = str(ranking[0]["gene"])
    cluster_candidate = top1_gene in set(cluster_genes)
    entropy_key = "normalized_entropy" if thresholds.entropy_is_normalized else "entropy"
    threshold_hits = {
        "max_probability_below_threshold": (
            features["max_probability"] <= thresholds.max_probability
        ),
        "top1_top2_margin_below_threshold": (
            features["top1_top2_margin"] <= thresholds.top1_top2_margin
        ),
        "entropy_above_threshold": features[entropy_key] >= thresholds.entropy,
    }
    ambiguous = cluster_candidate and any(threshold_hits.values())
    status = AMBIGUOUS_GENE_CLUSTER if ambiguous else DEFINITIVE_GENE
    return {
        "status": status,
        "top1_gene": top1_gene,
        "top1_probability": features["max_probability"],
        "top1_top2_margin": features["top1_top2_margin"],
        "entropy": features["entropy"],
        "normalized_entropy": features["normalized_entropy"],
        "thresholds": thresholds.to_dict(),
        "threshold_hits": threshold_hits,
        "cluster_candidate": cluster_candidate,
        "ranked_cluster": ranked_cluster(genes, probabilities, cluster_genes=cluster_genes)
        if ambiguous
        else [],
        "ranking": ranking,
    }
