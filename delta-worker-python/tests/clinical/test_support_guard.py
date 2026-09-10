from __future__ import annotations

import pytest
from deltatorrent.clinical.classifier import ClinicalEncoder
from deltatorrent.clinical.gold_loader import ClinicalRecord
from deltatorrent.clinical.support_guard import (
    DOMINANT_CLUSTER_OOD,
    LOW_FAMILY_DIVERSITY,
    LOW_LOCAL_TRAIN_SUPPORT,
    LOW_PUBLICATION_DIVERSITY,
    LocalSupportStats,
    SupportGuardThresholds,
    canonical_support_matrix,
    should_downgrade_support_guard,
    support_guard_reasons,
)
from deltatorrent.clinical.uncertainty import (
    AMBIGUOUS_GENE_CLUSTER,
    DEFINITIVE_GENE,
)


def _record(gene: str, *, publication_id: str = "pmid1", family_id: str = "fam1") -> ClinicalRecord:
    return ClinicalRecord(
        record_id=f"{gene}:{publication_id}:{family_id}",
        gene=gene,
        publication_id=publication_id,
        family_id=family_id,
        individual_id="patient1",
        sex="unknown",
        aao_years=60.0,
        aao_group="LATE_ONSET",
        aao_missing=False,
        zygosity="heterozygous",
        inheritance="autosomal_dominant",
        family_history="positive",
        phenotype_features=("PARKINSONISM", "BRADYKINESIA", "TREMOR_REST"),
        pedigree_features=("AUTOSOMAL_DOMINANT_PEDIGREE",),
        feature_statuses=(),
        source_columns=(),
        publication_missing=False,
    )


def _stats() -> LocalSupportStats:
    return LocalSupportStats(
        k_neighbors=10,
        neighbor_similarity_floor=0.8,
        nearest_neighbor_similarity=0.7,
        effective_neighbor_count=1,
        gene_distribution={"SNCA": 1},
        gene_similarity_mass={"SNCA": 0.7},
        unique_publications=1,
        unique_families=1,
        local_publication_concentration=1.0,
        top_neighbors=[],
    )


def _thresholds() -> SupportGuardThresholds:
    return SupportGuardThresholds(
        k_neighbors=10,
        neighbor_similarity_floor=0.8,
        min_nearest_neighbor_similarity=0.75,
        min_effective_neighbor_count=3,
        min_top1_gene_neighbor_share=0.5,
        min_unique_publications=2,
        min_unique_families=2,
        max_publication_concentration=0.8,
    )


def test_canonical_support_matrix_does_not_encode_target_gene() -> None:
    lrrk2 = _record("LRRK2")
    snca = _record("SNCA")
    encoder = ClinicalEncoder.from_training_records((lrrk2, snca))

    matrix = canonical_support_matrix(encoder, (lrrk2, snca))

    assert matrix[0].tolist() == pytest.approx(matrix[1].tolist())


def test_support_guard_reasons_are_generic_data_quality_flags() -> None:
    reasons = support_guard_reasons(_stats(), _thresholds())

    assert reasons == (
        DOMINANT_CLUSTER_OOD,
        LOW_LOCAL_TRAIN_SUPPORT,
        LOW_PUBLICATION_DIVERSITY,
        LOW_FAMILY_DIVERSITY,
    )


def test_low_top1_neighbor_share_is_low_local_support() -> None:
    reasons = support_guard_reasons(
        LocalSupportStats(
            k_neighbors=10,
            neighbor_similarity_floor=0.8,
            nearest_neighbor_similarity=0.9,
            effective_neighbor_count=4,
            gene_distribution={"LRRK2": 3, "SNCA": 1},
            gene_similarity_mass={"LRRK2": 2.7, "SNCA": 0.8},
            unique_publications=3,
            unique_families=3,
            local_publication_concentration=0.5,
            top_neighbors=[],
        ),
        _thresholds(),
        top1_gene="SNCA",
    )

    assert reasons == (LOW_LOCAL_TRAIN_SUPPORT,)


def test_support_guard_can_only_downgrade_definitive_cluster_predictions() -> None:
    downgraded, reasons = should_downgrade_support_guard(
        current_status=DEFINITIVE_GENE,
        top1_gene="SNCA",
        stats=_stats(),
        thresholds=_thresholds(),
    )
    already_ambiguous, _ = should_downgrade_support_guard(
        current_status=AMBIGUOUS_GENE_CLUSTER,
        top1_gene="SNCA",
        stats=_stats(),
        thresholds=_thresholds(),
    )
    non_cluster, _ = should_downgrade_support_guard(
        current_status=DEFINITIVE_GENE,
        top1_gene="GBA1",
        stats=_stats(),
        thresholds=_thresholds(),
    )

    assert downgraded is True
    assert reasons
    assert already_ambiguous is False
    assert non_cluster is False
