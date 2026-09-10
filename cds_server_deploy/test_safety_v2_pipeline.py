import json
import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline_service import (
    AMBIGUOUS_GENE_CLUSTER,
    DEFINITIVE_GENE,
    DOMINANT_CLUSTER_GENES,
    DOMINANT_CLUSTER_OOD,
    LOW_FAMILY_DIVERSITY,
    LOW_LOCAL_TRAIN_SUPPORT,
    LOW_PUBLICATION_DIVERSITY,
    SAFETY_GUARD_UNAVAILABLE,
    ClinicalDecisionSupportPipeline,
)

SYMPTOM_PATTERNS = (
    ("parkinsonism", r"\bparkinsonism\b"),
    ("tremor_rest", r"\b(?:resting tremor|rest tremor|pill-rolling tremor)\b"),
    ("dystonia", r"\b(?:foot dystonia|lower limb dystonia|dystonia)\b"),
    ("sleep_benefit", r"\b(?:sleep benefit|benefit after sleep)\b"),
    ("diurnal_fluctuation", r"\b(?:diurnal fluctuation|worsening in the evening)\b"),
    (
        "levodopa_response",
        r"\b(?:levodopa response|relief with low-dose levodopa|dramatic levodopa response)\b",
    ),
    ("vertical_gaze_palsy", r"\b(?:supranuclear vertical gaze palsy|vertical gaze palsy)\b"),
    ("spasticity_pyramidal_signs", r"\b(?:spasticity|pyramidal signs)\b"),
    ("rigidity", r"\b(?:rigidity|cogwheel rigidity)\b"),
    ("bradykinesia", r"\bbradykinesia\b"),
    ("cognitive_decline", r"\b(?:cognitive decline|cognitive impairment)\b"),
    ("hallucinations", r"\b(?:visual hallucinations|hallucinations)\b"),
    ("hyposmia", r"\bhyposmia\b"),
    ("autonomic_dysfunction", r"\bautonomic\b"),
)


def _source(text: str, match: re.Match[str]) -> dict[str, Any]:
    return {
        "text_span": text[match.start() : match.end()],
        "start": match.start(),
        "end": match.end(),
    }


def _mock_schema_extraction(text: str) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []

    age_match = re.search(r"\b(\d{1,2})\s+years?\s+old\b", text, re.IGNORECASE)
    if age_match:
        observations.append(
            {
                "id": "obs_age",
                "predicate": "HAS_ONSET_AGE",
                "subject": {"type": "proband"},
                "value": int(age_match.group(1)),
                "source": _source(text, age_match),
            }
        )

    for concept, pattern in SYMPTOM_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        span_prefix = text[max(0, match.start() - 12) : match.start()].lower()
        observations.append(
            {
                "id": f"obs_{concept}",
                "predicate": "HAS_SYMPTOM",
                "subject": {"type": "proband"},
                "concept": concept,
                "polarity": "negative" if re.search(r"\bno\s+$", span_prefix) else "positive",
                "source": _source(text, match),
            }
        )

    for idx, match in enumerate(
        re.finditer(r"\b(?:c\.[0-9]+[A-Za-z0-9_>+-]+|p\.[A-Z][a-z]{2}[0-9]+[A-Z][a-z]{2})\b", text),
        start=1,
    ):
        observations.append(
            {
                "id": f"obs_variant_{idx}",
                "predicate": "HAS_VARIANT",
                "subject": {"type": "proband"},
                "raw_variant": match.group(0),
                "source": _source(text, match),
            }
        )

    gene_match = re.search(r"\b(PRKN|GCH1|ATP13A2|GBA1|VPS35|LRRK2|SNCA|PINK1|PARK7|RAB32)\b", text)
    if gene_match:
        observations.append(
            {
                "id": "obs_gene",
                "predicate": "HAS_GENE_MENTION",
                "subject": {"type": "proband"},
                "value": gene_match.group(1),
                "source": _source(text, gene_match),
            }
        )

    class_match = re.search(
        r"\b(Pathogenic|VUS|uncertain significance|benign)\b", text, re.IGNORECASE
    )
    if class_match:
        observations.append(
            {
                "id": "obs_classification",
                "predicate": "HAS_CLASSIFICATION_ASSERTION",
                "subject": {"type": "proband"},
                "value": class_match.group(1),
                "source": _source(text, class_match),
            }
        )

    return {
        "schema_version": "1.1",
        "document_id": "mock_demo_case",
        "observations": observations,
    }


def _feature(concept: str) -> dict[str, Any]:
    return {
        "id": f"manual_{concept}",
        "feature": concept,
        "concept": concept,
        "status": "Present",
        "subject": "Patient",
        "clinician_confirmed": True,
    }


def main() -> None:
    os.environ["LLM_API_KEY"] = ""
    os.environ["SKIP_VENV_BOOTSTRAP"] = "1"

    pipeline = ClinicalDecisionSupportPipeline()
    assert not pipeline.api_key
    assert pipeline.safety_artifacts_loaded, pipeline.safety_artifact_error

    thresholds = json.loads(
        (Path(__file__).resolve().parent / "safety_thresholds_v2.json").read_text()
    )
    required_reasons = {
        LOW_LOCAL_TRAIN_SUPPORT,
        LOW_PUBLICATION_DIVERSITY,
        LOW_FAMILY_DIVERSITY,
        DOMINANT_CLUSTER_OOD,
    }
    assert required_reasons.issubset(set(thresholds["reason_codes"]))

    examples = json.loads(
        (Path(__file__).resolve().parent / "examples.json").read_text(encoding="utf-8")
    )
    pipeline._call_nlp_model = _mock_schema_extraction  # type: ignore[method-assign]
    for example in examples:
        result = pipeline.analyze_case(example["text"])
        assert result["pipeline_status"] == "SUCCESS"
        assert result["status"] in {DEFINITIVE_GENE, AMBIGUOUS_GENE_CLUSTER}
        assert isinstance(result["reason_codes"], list)
        assert "classifier_safety" in result
        assert result["classifier_safety"]["status"] == result["status"]
        recalculated = pipeline.recalculate_case(json.loads(json.dumps(result)))
        assert recalculated["status"] in {DEFINITIVE_GENE, AMBIGUOUS_GENE_CLUSTER}
        assert isinstance(recalculated["reason_codes"], list)

    cluster_features = [
        _feature("parkinsonism"),
        _feature("bradykinesia"),
        _feature("autonomic_dysfunction"),
        _feature("cognitive_decline"),
        _feature("hallucinations"),
    ]
    ranking_before = pipeline.compute_phenotype_ranking(cluster_features, 46, "dominant familial")
    safety = pipeline.evaluate_classifier_safety(cluster_features, 46, "dominant familial")
    ranking_after = pipeline.compute_phenotype_ranking(cluster_features, 46, "dominant familial")
    assert ranking_before and ranking_after
    assert [row["gene"] for row in ranking_before] == [row["gene"] for row in ranking_after]
    assert [row["score_pct"] for row in ranking_before] == [
        row["score_pct"] for row in ranking_after
    ]
    assert safety["top_candidate"] in DOMINANT_CLUSTER_GENES

    pipeline.safety_artifacts_loaded = False
    failed_guard = pipeline.evaluate_classifier_safety(cluster_features, 46, "dominant familial")
    assert failed_guard["status"] == AMBIGUOUS_GENE_CLUSTER
    assert SAFETY_GUARD_UNAVAILABLE in failed_guard["reason_codes"]

    print("SAFETY_V2_DEPLOYMENT_SMOKE_OK")
    print(f"DEMO_CASES_CHECKED={len(examples)}")


if __name__ == "__main__":
    main()
