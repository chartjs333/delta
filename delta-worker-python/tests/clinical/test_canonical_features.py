from __future__ import annotations

from deltatorrent.clinical.canonical_features import (
    canonical_features_for_column,
    canonicalize_inheritance,
    canonicalize_zygosity,
    map_column,
    map_column_for_gene,
    ontology_export,
    runtime_concept_to_canonical,
)


def test_diurnal_mapping() -> None:
    assert canonical_features_for_column("diurnal_fluctuations_sympt") == ("DIURNAL_FLUCTUATION",)
    assert runtime_concept_to_canonical("diurnal_fluctuation") == "DIURNAL_FLUCTUATION"


def test_levodopa_mapping() -> None:
    assert canonical_features_for_column("levodopa_response") == ("LEVODOPA_RESPONSE",)
    assert runtime_concept_to_canonical("levodopa_response") == "LEVODOPA_RESPONSE"


def test_autonomic_mapping() -> None:
    assert canonical_features_for_column("autonomic_sympt") == ("AUTONOMIC_DYSFUNCTION",)
    assert runtime_concept_to_canonical("autonomic_dysfunction") == "AUTONOMIC_DYSFUNCTION"


def test_hyposmia_mapping() -> None:
    assert canonical_features_for_column("olfaction_sympt") == ("HYPOSMIA",)
    assert runtime_concept_to_canonical("hyposmia") == "HYPOSMIA"


def test_family_history_mapping() -> None:
    assert map_column("family_history").role == "family_history"
    assert map_column("famhx").role == "family_history"
    assert map_column("comments_pat").role == "text_features"
    assert runtime_concept_to_canonical("familial_history") == "FAMILY_HISTORY"


def test_lrrk2_tremor_mapping_is_gene_specific_and_versioned() -> None:
    assert map_column("tremor_HP:0001337").role == "ignored"

    lrrk2_mapping = map_column_for_gene("LRRK2", "tremor_HP:0001337")
    assert lrrk2_mapping.role == "phenotype"
    assert lrrk2_mapping.targets == ("TREMOR_OTHER",)
    assert map_column_for_gene("GCH1", "tremor_HP:0001337").role == "ignored"

    source_mappings = ontology_export()["source_specific_column_mappings"]
    assert {
        "gene": "LRRK2",
        "mapping_version": "lrrk2-tremor-hp0001337-v1",
        "normalized_source_column": "tremor",
        "rationale": (
            "LRRK2 gold column tremor_HP:0001337 is a controlled patient-level "
            "clinical phenotype column with yes/no/-99 values; yes maps to "
            "non-rest-specific tremor evidence."
        ),
        "role": "phenotype",
        "targets": ["TREMOR_OTHER"],
    } in source_mappings


def test_zygosity_not_confused_with_inheritance() -> None:
    assert canonicalize_zygosity("heterozygous") == "heterozygous"
    assert canonicalize_inheritance("heterozygous") == "unknown"
    assert canonicalize_zygosity(("heterozygous", "heterozygous")) == "compound_heterozygous"
