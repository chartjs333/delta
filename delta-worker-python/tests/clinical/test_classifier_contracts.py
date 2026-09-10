from __future__ import annotations

import pytest
import torch
from deltatorrent.clinical.classifier import ClinicalEncoder, make_model, ranking_for_record
from deltatorrent.clinical.gold_loader import ClinicalRecord
from deltatorrent.clinical.split import publication_disjoint_split


def _record(
    record_id: str,
    gene: str,
    publication_id: str,
    features: tuple[str, ...],
    *,
    aao_years: float | None = 30,
    zygosity: str = "unknown",
    inheritance: str = "unknown",
    family_history: str = "unknown",
) -> ClinicalRecord:
    aao_group = "AAO_MISSING"
    if aao_years is not None:
        if aao_years <= 20:
            aao_group = "JUVENILE_ONSET"
        elif aao_years < 45:
            aao_group = "EARLY_ONSET"
        else:
            aao_group = "LATE_ONSET"
    return ClinicalRecord(
        record_id=record_id,
        gene=gene,
        publication_id=publication_id,
        family_id=f"family:{publication_id}",
        individual_id=f"individual:{record_id}",
        sex="unknown",
        aao_years=aao_years,
        aao_group=aao_group,
        aao_missing=aao_years is None,
        zygosity=zygosity,
        inheritance=inheritance,
        family_history=family_history,
        phenotype_features=features,
        pedigree_features=(),
        feature_statuses=(),
        source_columns=(),
        publication_missing=False,
    )


def test_publication_split_isolation() -> None:
    records = tuple(
        _record(f"r{i}", "GCH1" if i % 2 == 0 else "SNCA", f"pmid:{i // 2}", ("DYSTONIA",))
        for i in range(12)
    )
    split = publication_disjoint_split(records, seed=7)
    publication_to_split: dict[str, str] = {}
    for split_name in ("train", "validation", "calibration", "test"):
        for record in split.records_for(split_name):
            previous = publication_to_split.setdefault(record.publication_id, split_name)
            assert previous == split_name


def test_no_symptom_truncation() -> None:
    features = (
        "PARKINSONISM",
        "BRADYKINESIA",
        "RIGIDITY",
        "TREMOR_REST",
        "DYSTONIA",
        "DIURNAL_FLUCTUATION",
        "LEVODOPA_RESPONSE",
        "SLEEP_BENEFIT",
    )
    train = (_record("r1", "GCH1", "pmid:1", features),)
    encoder = ClinicalEncoder.from_training_records(train)
    encoded = encoder.encode_records(train)
    active_count = int(encoded.phenotype[0].sum().item())
    assert active_count == len(features)


def test_no_gene_diagnosis_or_variant_input_terms() -> None:
    record = _record(
        "r1",
        "GCH1",
        "pmid:1",
        ("DYSTONIA", "DIURNAL_FLUCTUATION", "LEVODOPA_RESPONSE"),
        zygosity="heterozygous",
        inheritance="autosomal_dominant",
        family_history="positive",
    )
    encoder = ClinicalEncoder.from_training_records((record,))
    joined_terms = " ".join(encoder.model_input_terms(record)).lower()
    forbidden_terms = ("gch1", "target gene", "diagnosis", "variant", "p.asp", "c.")
    for term in forbidden_terms:
        assert term not in joined_terms


def test_no_test_vocab_leakage_in_train_artifacts() -> None:
    train = (_record("train", "GCH1", "pmid:train", ("DYSTONIA",), aao_years=10),)
    test_only = _record(
        "test",
        "SNCA",
        "pmid:test",
        ("AUTONOMIC_DYSFUNCTION",),
        aao_years=90,
    )
    encoder = ClinicalEncoder.from_training_records(train)
    assert encoder.train_feature_counts == {"DYSTONIA": 1}
    assert encoder.aao_mean == 10
    encoded_test = encoder.encode_records((test_only,))
    assert int(encoded_test.phenotype[0].sum().item()) == 1


def test_prediction_depends_on_phenotype_features() -> None:
    base = _record("base", "GCH1", "pmid:1", ("DYSTONIA",), aao_years=12)
    changed = _record(
        "changed",
        "GCH1",
        "pmid:1",
        ("DYSTONIA", "DIURNAL_FLUCTUATION", "LEVODOPA_RESPONSE", "SLEEP_BENEFIT"),
        aao_years=12,
    )
    encoder = ClinicalEncoder.from_training_records((base, changed))
    model = make_model(encoder, seed=123, dropout=0.0)
    encoded = encoder.encode_records((base, changed))
    logits = model(
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
    assert not torch.allclose(logits[0], logits[1])


def test_diagnosis_gene_variant_absent_from_input_schema() -> None:
    record = _record("r1", "ATP13A2", "pmid:1", ("VERTICAL_GAZE_PALSY",), aao_years=14)
    encoder = ClinicalEncoder.from_training_records((record,))
    schema = str(encoder.input_schema()).lower()
    assert "forbidden_input_roles" in schema
    assert "target_gene" in schema
    assert "diagnosis" in schema
    assert "variant_gene" in schema
    assert "mut1" not in schema
    with pytest.raises(KeyError):
        _ = encoder.train_feature_counts["ATP13A2"]


def test_label_gene_subset_creates_real_four_way_head() -> None:
    label_genes = ("LRRK2", "VPS35", "RAB32", "SNCA")
    records = (
        _record("lrrk2", "LRRK2", "pmid:1", ("PARKINSONISM",)),
        _record("vps35", "VPS35", "pmid:2", ("PARKINSONISM", "POSTURAL_INSTABILITY")),
        _record("rab32", "RAB32", "pmid:3", ("PARKINSONISM", "DYSKINESIA")),
        _record("snca", "SNCA", "pmid:4", ("PARKINSONISM", "AUTONOMIC_DYSFUNCTION")),
    )
    encoder = ClinicalEncoder.from_training_records(records, label_genes=label_genes)
    encoded = encoder.encode_records(records)
    model = make_model(encoder, seed=123, dropout=0.0)
    logits = model(
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

    assert encoded.labels.tolist() == [0, 1, 2, 3]
    assert tuple(logits.shape) == (4, 4)
    ranking = ranking_for_record(model, encoder, records[0])
    assert len(ranking) == len(label_genes)
    assert {row["gene"] for row in ranking} == set(label_genes)


def test_label_gene_subset_rejects_outside_record() -> None:
    encoder = ClinicalEncoder.from_training_records(
        (_record("lrrk2", "LRRK2", "pmid:1", ("PARKINSONISM",)),),
        label_genes=("LRRK2", "VPS35"),
    )

    with pytest.raises(ValueError, match="RECORD_GENE_OUTSIDE_LABEL_SET"):
        encoder.encode_records((_record("snca", "SNCA", "pmid:2", ("PARKINSONISM",)),))
