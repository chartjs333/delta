from __future__ import annotations

import torch
from deltatorrent.clinical.classifier import ClinicalEncoder, clone_record_with_features, make_model
from deltatorrent.clinical.gold_loader import ClinicalRecord


def _record(
    record_id: str,
    gene: str,
    features: tuple[str, ...],
    *,
    aao_group: str = "EARLY_ONSET",
    aao_years: float | None = 35,
    inheritance: str = "unknown",
    family_history: str = "unknown",
    pedigree_features: tuple[str, ...] = (),
) -> ClinicalRecord:
    return ClinicalRecord(
        record_id=record_id,
        gene=gene,
        publication_id=f"pmid:{record_id}",
        family_id=f"family:{record_id}",
        individual_id=f"individual:{record_id}",
        sex="unknown",
        aao_years=aao_years,
        aao_group=aao_group,
        aao_missing=aao_years is None,
        zygosity="unknown",
        inheritance=inheritance,
        family_history=family_history,
        phenotype_features=features,
        pedigree_features=pedigree_features,
        feature_statuses=(),
        source_columns=(),
        publication_missing=False,
    )


def _logits(
    model: torch.nn.Module, encoder: ClinicalEncoder, records: tuple[ClinicalRecord, ...]
) -> torch.Tensor:
    encoded = encoder.encode_records(records)
    return model(
        encoded.phenotype,
        encoded.pedigree,
        encoded.sex,
        encoded.aao_group,
        encoded.zygosity,
        encoded.inheritance,
        encoded.family_history,
        encoded.aao_numeric,
        encoded.aao_missing,
    )


def test_park7_rab32_vps35_snca_challenge_profiles_encode_all_features() -> None:
    records = (
        _record(
            "park7",
            "PARK7",
            ("PARKINSONISM", "DYSTONIA", "BLEPHAROSPASM", "SPASTICITY_PYRAMIDAL_SIGNS"),
            aao_group="EARLY_ONSET",
            aao_years=28,
            inheritance="autosomal_recessive",
        ),
        _record(
            "rab32",
            "RAB32",
            ("PARKINSONISM", "BRADYKINESIA", "RIGIDITY", "TREMOR_REST"),
            aao_group="LATE_ONSET",
            aao_years=62,
            inheritance="autosomal_dominant",
            family_history="positive",
            pedigree_features=("AUTOSOMAL_DOMINANT_PEDIGREE",),
        ),
        _record(
            "vps35",
            "VPS35",
            ("PARKINSONISM", "BRADYKINESIA", "RIGIDITY", "TREMOR_REST"),
            aao_group="LATE_ONSET",
            aao_years=55,
            inheritance="autosomal_dominant",
            family_history="positive",
            pedigree_features=("AUTOSOMAL_DOMINANT_PEDIGREE",),
        ),
        _record(
            "snca",
            "SNCA",
            (
                "PARKINSONISM",
                "AUTONOMIC_DYSFUNCTION",
                "HYPOSMIA",
                "COGNITIVE_DECLINE",
                "HALLUCINATIONS",
            ),
            aao_group="EARLY_ONSET",
            aao_years=44,
            inheritance="autosomal_dominant",
            family_history="positive",
            pedigree_features=("AUTOSOMAL_DOMINANT_PEDIGREE",),
        ),
    )
    encoder = ClinicalEncoder.from_training_records(records)
    encoded = encoder.encode_records(records)
    expected_active = [4, 4, 4, 5]
    assert [int(row.sum().item()) for row in encoded.phenotype] == expected_active
    assert int(encoded.pedigree[1].sum().item()) == 1
    assert int(encoded.pedigree[2].sum().item()) == 1
    assert int(encoded.pedigree[3].sum().item()) == 1


def test_challenge_feature_ablations_change_logits() -> None:
    full_records = (
        _record("park7", "PARK7", ("PARKINSONISM", "DYSTONIA", "BLEPHAROSPASM")),
        _record("rab32", "RAB32", ("PARKINSONISM", "BRADYKINESIA", "TREMOR_REST")),
        _record("vps35", "VPS35", ("PARKINSONISM", "RIGIDITY", "TREMOR_REST")),
        _record("snca", "SNCA", ("PARKINSONISM", "AUTONOMIC_DYSFUNCTION", "COGNITIVE_DECLINE")),
    )
    ablated_records = (
        clone_record_with_features(full_records[0], ("PARKINSONISM", "DYSTONIA")),
        clone_record_with_features(full_records[1], ("PARKINSONISM", "BRADYKINESIA")),
        clone_record_with_features(full_records[2], ("PARKINSONISM", "RIGIDITY")),
        clone_record_with_features(full_records[3], ("PARKINSONISM", "COGNITIVE_DECLINE")),
    )
    encoder = ClinicalEncoder.from_training_records(full_records)
    model = make_model(encoder, seed=321, dropout=0.0)
    full_logits = _logits(model, encoder, full_records)
    ablated_logits = _logits(model, encoder, ablated_records)
    assert not torch.allclose(full_logits, ablated_logits)
    changed_rows = (full_logits - ablated_logits).abs().sum(dim=1)
    assert bool(torch.all(changed_rows > 0))
