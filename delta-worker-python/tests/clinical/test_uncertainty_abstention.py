from __future__ import annotations

import pytest
from deltatorrent.clinical.uncertainty import (
    AMBIGUOUS_GENE_CLUSTER,
    DEFINITIVE_GENE,
    UncertaintyThresholds,
    decide_cluster_abstention,
    uncertainty_features,
)


def test_uncertainty_features_include_probability_margin_and_entropy() -> None:
    features = uncertainty_features((0.55, 0.35, 0.05, 0.05))

    assert features["max_probability"] == pytest.approx(0.55)
    assert features["top1_top2_margin"] == pytest.approx(0.20)
    assert 0.0 < features["normalized_entropy"] < 1.0


def test_cluster_abstention_returns_ranked_cluster_for_ambiguous_case() -> None:
    decision = decide_cluster_abstention(
        ("LRRK2", "VPS35", "RAB32", "SNCA"),
        (0.42, 0.39, 0.10, 0.09),
        UncertaintyThresholds(
            max_probability=0.50,
            top1_top2_margin=0.10,
            entropy=0.50,
        ),
    )

    assert decision["status"] == AMBIGUOUS_GENE_CLUSTER
    assert decision["top1_gene"] == "LRRK2"
    assert [row["gene"] for row in decision["ranked_cluster"]] == [
        "LRRK2",
        "VPS35",
        "RAB32",
        "SNCA",
    ]


def test_cluster_abstention_keeps_definitive_non_cluster_or_confident_case() -> None:
    non_cluster = decide_cluster_abstention(
        ("GBA1", "LRRK2", "VPS35", "SNCA"),
        (0.42, 0.39, 0.10, 0.09),
        UncertaintyThresholds(
            max_probability=0.50,
            top1_top2_margin=0.10,
            entropy=0.50,
        ),
        cluster_genes=("LRRK2", "VPS35", "SNCA"),
    )
    confident_cluster = decide_cluster_abstention(
        ("LRRK2", "VPS35", "RAB32", "SNCA"),
        (0.91, 0.04, 0.03, 0.02),
        UncertaintyThresholds(
            max_probability=0.50,
            top1_top2_margin=0.10,
            entropy=0.50,
        ),
    )

    assert non_cluster["status"] == DEFINITIVE_GENE
    assert confident_cluster["status"] == DEFINITIVE_GENE
    assert confident_cluster["ranked_cluster"] == []
