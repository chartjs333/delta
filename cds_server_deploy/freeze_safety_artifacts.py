"""Freeze deployment-local safety artifacts for the CDS prototype."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

APP_DIR = Path(__file__).resolve().parent
MODEL_PATH = APP_DIR / "model_10genes_phenotype_classifier.json"

DOMINANT_CLUSTER_GENES = ("LRRK2", "VPS35", "RAB32", "SNCA")

SUPPORT_PROTOTYPES: tuple[dict[str, Any], ...] = (
    {
        "gene": "LRRK2",
        "features": ("PARKINSONISM", "BRADYKINESIA", "RIGIDITY", "TREMOR_REST"),
        "aao_group": "LATE_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
    {
        "gene": "LRRK2",
        "features": ("PARKINSONISM", "ASYMMETRIC_ONSET", "TREMOR_REST", "LEVODOPA_RESPONSE"),
        "aao_group": "LATE_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
    {
        "gene": "VPS35",
        "features": ("PARKINSONISM", "BRADYKINESIA", "RIGIDITY", "TREMOR_REST"),
        "aao_group": "LATE_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
    {
        "gene": "VPS35",
        "features": ("PARKINSONISM", "POSTURAL_INSTABILITY", "TREMOR_REST"),
        "aao_group": "LATE_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
    {
        "gene": "RAB32",
        "features": ("PARKINSONISM", "BRADYKINESIA", "RIGIDITY", "TREMOR_REST"),
        "aao_group": "LATE_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
    {
        "gene": "RAB32",
        "features": ("PARKINSONISM", "LEVODOPA_RESPONSE", "TREMOR_REST"),
        "aao_group": "LATE_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
    {
        "gene": "SNCA",
        "features": (
            "PARKINSONISM",
            "BRADYKINESIA",
            "AUTONOMIC_DYSFUNCTION",
            "COGNITIVE_DECLINE",
            "HALLUCINATIONS",
        ),
        "aao_group": "EARLY_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
    {
        "gene": "SNCA",
        "features": (
            "PARKINSONISM",
            "AUTONOMIC_DYSFUNCTION",
            "COGNITIVE_DECLINE",
            "HALLUCINATIONS",
            "ATYPICAL_PARKINSONISM",
        ),
        "aao_group": "LATE_ONSET",
        "inheritance": "autosomal_dominant",
        "family_history": "positive",
    },
)


def _stable_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(_stable_json(data), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _one_hot(value: str, values: list[str]) -> list[float]:
    row = [0.0] * len(values)
    try:
        idx = values.index(value)
    except ValueError:
        idx = values.index("unknown") if "unknown" in values else 0
    row[idx] = 1.0
    return row


def _support_vector(model: dict[str, Any], prototype: dict[str, Any]) -> list[float]:
    feature_order = list(model["feature_order"])
    pedigree_order = list(model.get("pedigree_feature_order", []))
    ontology = model["canonical_features"]
    numeric_schema = model["input_schema"]["numeric_fields"]["aao_years_normalized"]
    mean = float(numeric_schema["mean_train_only"])
    std = float(numeric_schema["std_train_only"]) or 1.0
    age_by_group = {
        "AAO_MISSING": None,
        "JUVENILE_ONSET": 14.0,
        "EARLY_ONSET": 32.0,
        "LATE_ONSET": 62.0,
    }

    phenotype = [1.0 if feature in prototype["features"] else 0.0 for feature in feature_order]
    pedigree = [0.0] * len(pedigree_order)
    if prototype.get("inheritance") == "autosomal_dominant" and "AUTOSOMAL_DOMINANT_PEDIGREE" in pedigree_order:
        pedigree[pedigree_order.index("AUTOSOMAL_DOMINANT_PEDIGREE")] = 1.0
    if prototype.get("inheritance") == "autosomal_recessive" and "AUTOSOMAL_RECESSIVE_PEDIGREE" in pedigree_order:
        pedigree[pedigree_order.index("AUTOSOMAL_RECESSIVE_PEDIGREE")] = 1.0

    aao_group = str(prototype["aao_group"])
    aao_years = age_by_group[aao_group]
    if aao_years is None:
        aao_numeric = [0.0]
        aao_missing = [1.0]
    else:
        aao_numeric = [(aao_years - mean) / std]
        aao_missing = [0.0]

    return [
        *phenotype,
        *pedigree,
        *_one_hot("unknown", ontology["sex_values"]),
        *_one_hot(aao_group, ontology["aao_groups"]),
        *_one_hot("unknown", ontology["zygosity_values"]),
        *_one_hot(str(prototype["inheritance"]), ontology["inheritance_values"]),
        *_one_hot(str(prototype["family_history"]), ontology["family_history_values"]),
        *aao_numeric,
        *aao_missing,
    ]


def main() -> None:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    ontology = dict(model["canonical_features"])
    input_schema = dict(model["input_schema"])

    thresholds = {
        "schema_version": "clinical-safety-thresholds-v2",
        "status_values": ["DEFINITIVE_GENE", "AMBIGUOUS_GENE_CLUSTER", "ABSTAIN"],
        "reason_codes": [
            "LOW_CLASSIFIER_CONFIDENCE",
            "LOW_LOCAL_TRAIN_SUPPORT",
            "LOW_PUBLICATION_DIVERSITY",
            "LOW_FAMILY_DIVERSITY",
            "DOMINANT_CLUSTER_OOD",
            "SAFETY_GUARD_UNAVAILABLE",
            "NLP_EXTRACTION_UNAVAILABLE",
        ],
        "uncertainty": {
            "max_probability": 0.50,
            "top1_top2_margin": 0.10,
            "normalized_entropy": 0.75,
        },
        "support_guard": {
            "k_neighbors": 8,
            "neighbor_similarity_floor": 0.15,
            "min_nearest_neighbor_similarity": 0.30,
            "min_effective_neighbor_count": 3,
            "min_top1_gene_neighbor_share": 0.25,
            "min_unique_publications": 2,
            "min_unique_families": 2,
            "max_publication_concentration": 0.75,
        },
        "policy": {
            "ranking_mutation_allowed": False,
            "allowed_transition": "DEFINITIVE_GENE_TO_AMBIGUOUS_GENE_CLUSTER_ONLY",
            "already_ambiguous_may_be_promoted": False,
            "guard_failure_allows_definitive": False,
        },
    }

    raw_counts = model.get("dataset_summary", {}).get("raw_records_per_gene", {})
    training_support = model.get("training_metrics", {}).get("per_gene", {})
    records = []
    for idx, prototype in enumerate(SUPPORT_PROTOTYPES, start=1):
        vector = _support_vector(model, prototype)
        gene = str(prototype["gene"])
        records.append(
            {
                "record_id": f"support-v2:{gene.lower()}:{idx}",
                "gene": gene,
                "publication_id": f"support-publication:{gene.lower()}:{idx}",
                "family_id": f"support-family:{gene.lower()}:{idx}",
                "prototype_features": list(prototype["features"]),
                "aao_group": prototype["aao_group"],
                "inheritance": prototype["inheritance"],
                "family_history": prototype["family_history"],
                "raw_dataset_records_for_gene": raw_counts.get(gene, 0),
                "training_records_for_gene": training_support.get(gene, {}).get("support", 0.0),
                "vector": [round(float(value), 10) for value in vector],
            }
        )

    support_index = {
        "schema_version": "clinical-support-index-v2",
        "source_model": MODEL_PATH.name,
        "input_schema_version": model["input_schema_version"],
        "ontology_version": ontology["ontology_version"],
        "cluster_genes": list(DOMINANT_CLUSTER_GENES),
        "vector_layout": {
            "phenotype_features": model["feature_order"],
            "pedigree_features": model.get("pedigree_feature_order", []),
            "sex_values": ontology["sex_values"],
            "aao_groups": ontology["aao_groups"],
            "zygosity_values": ontology["zygosity_values"],
            "inheritance_values": ontology["inheritance_values"],
            "family_history_values": ontology["family_history_values"],
            "numeric_tail": ["aao_years_normalized", "aao_missing"],
        },
        "records": records,
    }

    ontology_path = APP_DIR / "clinical_ontology_v1.json"
    input_schema_path = APP_DIR / "input_schema_v1.json"
    thresholds_path = APP_DIR / "safety_thresholds_v2.json"
    support_path = APP_DIR / "support_index_v2.json"
    manifest_path = APP_DIR / "compatibility_manifest_v2.json"

    _write_json(ontology_path, ontology)
    _write_json(input_schema_path, input_schema)
    _write_json(thresholds_path, thresholds)
    _write_json(support_path, support_index)

    component_paths = {
        "model_artifact": MODEL_PATH,
        "ontology": ontology_path,
        "input_schema": input_schema_path,
        "safety_thresholds_v2": thresholds_path,
        "support_index_v2": support_path,
        "readme": APP_DIR / "README.md",
        "env_example": APP_DIR / ".env.example",
        "pipeline_service": APP_DIR / "pipeline_service.py",
        "server": APP_DIR / "server.py",
        "ui_index": APP_DIR / "static" / "index.html",
        "ui_app": APP_DIR / "static" / "app.js",
        "ui_style": APP_DIR / "static" / "style.css",
        "artifact_freezer": Path(__file__).resolve(),
    }
    manifest = {
        "schema_version": "clinical-deployment-compatibility-manifest-v2",
        "deployment_profile": "cds_server_deploy",
        "model_artifact": MODEL_PATH.name,
        "model_version": model["model_version"],
        "input_schema_version": model["input_schema_version"],
        "ontology_version": ontology["ontology_version"],
        "safety_thresholds_version": thresholds["schema_version"],
        "support_index_version": support_index["schema_version"],
        "git_commit_at_model_export": model.get("git_commit"),
        "component_hashes": {
            name: {
                "path": str(path.relative_to(APP_DIR)).replace("\\", "/"),
                "sha256": _sha256_file(path),
            }
            for name, path in component_paths.items()
        },
        "compatibility": {
            "requires_status_and_reason_codes": True,
            "ranking_mutation_allowed": False,
            "supports_no_api_key_startup": True,
            "llm_calls_must_be_mocked_or_disabled_in_tests": True,
        },
    }
    _write_json(manifest_path, manifest)
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
