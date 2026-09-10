"""Shared canonical ontology for 10-gene parkinsonism phenotype classification.

The classifier, gold-file ingestion and runtime exports use this module as the
single source of truth for clinical feature IDs and non-leaking input roles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

GENES: tuple[str, ...] = (
    "GBA1",
    "LRRK2",
    "PRKN",
    "GCH1",
    "PINK1",
    "SNCA",
    "PARK7",
    "VPS35",
    "RAB32",
    "ATP13A2",
)

CANONICAL_PHENOTYPE_FEATURES: tuple[str, ...] = (
    "PARKINSONISM",
    "BRADYKINESIA",
    "RIGIDITY",
    "TREMOR_REST",
    "TREMOR_OTHER",
    "POSTURAL_INSTABILITY",
    "GAIT_DIFFICULTIES_FALLS",
    "ASYMMETRIC_ONSET",
    "DYSTONIA",
    "LOWER_LIMB_DYSTONIA",
    "UPPER_LIMB_DYSTONIA",
    "FACIAL_DYSTONIA",
    "BLEPHAROSPASM",
    "DIURNAL_FLUCTUATION",
    "SLEEP_BENEFIT",
    "LEVODOPA_RESPONSE",
    "MOTOR_FLUCTUATIONS",
    "DYSKINESIA",
    "HYPOSMIA",
    "COGNITIVE_DECLINE",
    "HALLUCINATIONS",
    "AUTONOMIC_DYSFUNCTION",
    "DEPRESSION",
    "ANXIETY",
    "SLEEP_DISORDER",
    "RBD",
    "ATYPICAL_PARKINSONISM",
    "VERTICAL_GAZE_PALSY",
    "SPASTICITY_PYRAMIDAL_SIGNS",
    "ATAXIA",
    "CEREBELLAR_SIGNS",
    "CHOREA",
    "MYOCLONUS",
    "SEIZURES",
    "DEVELOPMENTAL_DELAY",
    "INTELLECTUAL_DISABILITY",
    "DYSPHAGIA",
    "DYSARTHRIA",
    "HYPOPHONIA_OR_HYPOMIMIA",
    "GLUCOCEREBROSIDASE_SYSTEMIC_FEATURES",
)

PEDIGREE_FEATURES: tuple[str, ...] = (
    "AUTOSOMAL_DOMINANT_PEDIGREE",
    "AUTOSOMAL_RECESSIVE_PEDIGREE",
    "CONSANGUINITY",
    "MATERNAL_INHERITANCE",
    "PATERNAL_INHERITANCE",
)

SEX_VALUES: tuple[str, ...] = ("unknown", "female", "male", "other")
AAO_GROUPS: tuple[str, ...] = ("AAO_MISSING", "JUVENILE_ONSET", "EARLY_ONSET", "LATE_ONSET")
ZYGOSITY_VALUES: tuple[str, ...] = (
    "unknown",
    "heterozygous",
    "homozygous",
    "compound_heterozygous",
    "hemizygous",
)
INHERITANCE_VALUES: tuple[str, ...] = (
    "unknown",
    "autosomal_dominant",
    "autosomal_recessive",
    "x_linked",
    "mitochondrial",
    "de_novo",
)
FAMILY_HISTORY_VALUES: tuple[str, ...] = ("unknown", "positive", "negative")

ColumnRole = Literal[
    "phenotype",
    "pedigree",
    "family_history",
    "zygosity",
    "inheritance",
    "aao",
    "sex",
    "publication_id",
    "family_id",
    "individual_id",
    "variant",
    "text_features",
    "ignored",
]


@dataclass(frozen=True, slots=True)
class CanonicalColumnMapping:
    role: ColumnRole
    targets: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceSpecificColumnMapping:
    gene: str
    normalized_source_column: str
    role: ColumnRole
    targets: tuple[str, ...]
    mapping_version: str
    rationale: str


def normalize_column_name(header: object) -> str:
    """Normalize an Excel header without inferring a clinical concept."""

    text = str(header or "").strip().lower()
    text = text.split("_hp:", 1)[0]
    text = text.split(" hp:", 1)[0]
    text = text.replace("-", "_").replace("/", "_").replace("\\", "_")
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


_EXACT_COLUMNS: dict[str, CanonicalColumnMapping] = {
    "pmid": CanonicalColumnMapping("publication_id"),
    "publication_id": CanonicalColumnMapping("publication_id"),
    "family_id": CanonicalColumnMapping("family_id"),
    "individual_id": CanonicalColumnMapping("individual_id"),
    "patient_id": CanonicalColumnMapping("individual_id"),
    "sex": CanonicalColumnMapping("sex"),
    "aao": CanonicalColumnMapping("aao"),
    "aao_movement_disorder": CanonicalColumnMapping("aao"),
    "aao_any": CanonicalColumnMapping("aao"),
    "aao_classify": CanonicalColumnMapping("aao"),
    "mut1_de_novo": CanonicalColumnMapping("inheritance"),
    "mut1_genotype": CanonicalColumnMapping("zygosity"),
    "mut2_genotype": CanonicalColumnMapping("zygosity"),
    "mut3_genotype": CanonicalColumnMapping("zygosity"),
    "patient_genotype": CanonicalColumnMapping("zygosity"),
    "patients_genotype": CanonicalColumnMapping("zygosity"),
    "zygosity": CanonicalColumnMapping("zygosity"),
    "inheritance": CanonicalColumnMapping("inheritance"),
    "inheritance_pattern": CanonicalColumnMapping("inheritance"),
    "family_history": CanonicalColumnMapping("family_history"),
    "familial_history": CanonicalColumnMapping("family_history"),
    "family_history_sympt": CanonicalColumnMapping("family_history"),
    "famhx": CanonicalColumnMapping("family_history"),
    "consanguinity": CanonicalColumnMapping("pedigree", ("CONSANGUINITY",)),
    "autosomal_dominant_pedigree": CanonicalColumnMapping(
        "pedigree", ("AUTOSOMAL_DOMINANT_PEDIGREE",)
    ),
    "autosomal_recessive_pedigree": CanonicalColumnMapping(
        "pedigree", ("AUTOSOMAL_RECESSIVE_PEDIGREE",)
    ),
    "maternal_inheritance": CanonicalColumnMapping("pedigree", ("MATERNAL_INHERITANCE",)),
    "paternal_inheritance": CanonicalColumnMapping("pedigree", ("PATERNAL_INHERITANCE",)),
    "initial_sympt1": CanonicalColumnMapping("text_features"),
    "initial_sympt2": CanonicalColumnMapping("text_features"),
    "initial_sympt3": CanonicalColumnMapping("text_features"),
    "initial_symptom_for_output": CanonicalColumnMapping("text_features"),
    "other_sympt": CanonicalColumnMapping("text_features"),
    "various_symptoms": CanonicalColumnMapping("text_features"),
    "assoc_feat_sympt": CanonicalColumnMapping("text_features"),
    "body_distr_sympt": CanonicalColumnMapping("text_features"),
    "comments_pat": CanonicalColumnMapping("text_features"),
    "comments_patient": CanonicalColumnMapping("text_features"),
}

SOURCE_SPECIFIC_COLUMN_MAPPINGS: tuple[SourceSpecificColumnMapping, ...] = (
    SourceSpecificColumnMapping(
        gene="LRRK2",
        normalized_source_column="tremor",
        role="phenotype",
        targets=("TREMOR_OTHER",),
        mapping_version="lrrk2-tremor-hp0001337-v1",
        rationale=(
            "LRRK2 gold column tremor_HP:0001337 is a controlled patient-level "
            "clinical phenotype column with yes/no/-99 values; yes maps to "
            "non-rest-specific tremor evidence."
        ),
    ),
)

_SOURCE_SPECIFIC_COLUMNS: dict[tuple[str, str], CanonicalColumnMapping] = {
    (mapping.gene, mapping.normalized_source_column): CanonicalColumnMapping(
        mapping.role,
        mapping.targets,
    )
    for mapping in SOURCE_SPECIFIC_COLUMN_MAPPINGS
}

_VARIANT_COLUMN_RE = re.compile(
    r"^(?:mut\d+_(?:g|c|p|alias|alias_original|alias_copy|type|severity|rs_no)|"
    r"variant|variant_.*|.*_variant)$"
)

_COLUMN_PATTERNS: tuple[tuple[re.Pattern[str], CanonicalColumnMapping], ...] = (
    (
        re.compile(r"^(?:motor_sympt|parkinsonism_sympt)$"),
        CanonicalColumnMapping("phenotype", ("PARKINSONISM",)),
    ),
    (re.compile(r"^bradykinesia_sympt$"), CanonicalColumnMapping("phenotype", ("BRADYKINESIA",))),
    (re.compile(r"^rigidity_sympt$"), CanonicalColumnMapping("phenotype", ("RIGIDITY",))),
    (re.compile(r"^tremor_rest_sympt$"), CanonicalColumnMapping("phenotype", ("TREMOR_REST",))),
    (
        re.compile(r"^tremor_(?:action|postural|dystonic|other|unspecified)_sympt$"),
        CanonicalColumnMapping("phenotype", ("TREMOR_OTHER",)),
    ),
    (
        re.compile(r"^postural_instability_sympt$"),
        CanonicalColumnMapping("phenotype", ("POSTURAL_INSTABILITY",)),
    ),
    (
        re.compile(r"^gait_difficulties_falls_sympt$"),
        CanonicalColumnMapping("phenotype", ("GAIT_DIFFICULTIES_FALLS",)),
    ),
    (
        re.compile(r"^asymmetric_onset(?:_sympt)?$"),
        CanonicalColumnMapping("phenotype", ("ASYMMETRIC_ONSET",)),
    ),
    (
        re.compile(r"^dystonia_parkinsonism_sympt$"),
        CanonicalColumnMapping("phenotype", ("PARKINSONISM", "DYSTONIA")),
    ),
    (
        re.compile(r"^(?:dystonia_sympt|levodopa_induced_dystonia_sympt)$"),
        CanonicalColumnMapping("phenotype", ("DYSTONIA",)),
    ),
    (
        re.compile(r"^(?:lower_limb_dystonia_sympt|dyst_leg_sympt|dyst_foot_sympt)$"),
        CanonicalColumnMapping("phenotype", ("DYSTONIA", "LOWER_LIMB_DYSTONIA")),
    ),
    (
        re.compile(r"^(?:upper_limb_dystonia_sympt|dyst_arm_sympt|dyst_hand_sympt)$"),
        CanonicalColumnMapping("phenotype", ("DYSTONIA", "UPPER_LIMB_DYSTONIA")),
    ),
    (
        re.compile(r"^(?:dyst_upper_face_sympt|dyst_lower_face_sympt)$"),
        CanonicalColumnMapping("phenotype", ("DYSTONIA", "FACIAL_DYSTONIA")),
    ),
    (
        re.compile(r"^(?:segmental_multifocal_dystonia_sympt|body_distr_sympt)$"),
        CanonicalColumnMapping("phenotype", ("DYSTONIA",)),
    ),
    (
        re.compile(r"^diurnal_fluctuations?_sympt$|^diurnal_fluctuations?$"),
        CanonicalColumnMapping("phenotype", ("DIURNAL_FLUCTUATION",)),
    ),
    (
        re.compile(r"^sleep_benefit_sympt$|^sleep_benefit$"),
        CanonicalColumnMapping("phenotype", ("SLEEP_BENEFIT",)),
    ),
    (
        re.compile(r"^levodopa_response$|^l_dopa_response$"),
        CanonicalColumnMapping("phenotype", ("LEVODOPA_RESPONSE",)),
    ),
    (
        re.compile(r"^motor_fluctuations_sympt$"),
        CanonicalColumnMapping("phenotype", ("MOTOR_FLUCTUATIONS",)),
    ),
    (
        re.compile(r"^(?:dyskinesia_sympt|levodopa_induced_dyskinesia_sympt)$"),
        CanonicalColumnMapping("phenotype", ("DYSKINESIA",)),
    ),
    (
        re.compile(r"^(?:olfaction_sympt|abnormality_of_the_sense_of_smell|hyposmia_sympt)$"),
        CanonicalColumnMapping("phenotype", ("HYPOSMIA",)),
    ),
    (
        re.compile(r"^(?:cognitive_decline_sympt|dementia_sympt)$"),
        CanonicalColumnMapping("phenotype", ("COGNITIVE_DECLINE",)),
    ),
    (
        re.compile(r"^(?:hallucinations_sympt|psychotic_sympt)$"),
        CanonicalColumnMapping("phenotype", ("HALLUCINATIONS",)),
    ),
    (
        re.compile(r"^(?:autonomic_sympt|sexual_dysfunction|incontinence_sympt)$"),
        CanonicalColumnMapping("phenotype", ("AUTONOMIC_DYSFUNCTION",)),
    ),
    (re.compile(r"^depression_sympt$"), CanonicalColumnMapping("phenotype", ("DEPRESSION",))),
    (re.compile(r"^anxiety_sympt$"), CanonicalColumnMapping("phenotype", ("ANXIETY",))),
    (
        re.compile(r"^sleep_disorder_sympt$"),
        CanonicalColumnMapping("phenotype", ("SLEEP_DISORDER",)),
    ),
    (re.compile(r"^rbd_sympt$"), CanonicalColumnMapping("phenotype", ("RBD",))),
    (
        re.compile(r"^atypical_park_sympt$"),
        CanonicalColumnMapping("phenotype", ("ATYPICAL_PARKINSONISM",)),
    ),
    (
        re.compile(r"^(?:vertical_gaze_palsy_sympt|gaze_palsy_sympt)$"),
        CanonicalColumnMapping("phenotype", ("VERTICAL_GAZE_PALSY",)),
    ),
    (
        re.compile(
            r"^(?:saccadic_abnormalities_sympt|jerky_pursuit_sympt|oculogyric_spasms_sympt)$"
        ),
        CanonicalColumnMapping("phenotype", ("VERTICAL_GAZE_PALSY",)),
    ),
    (
        re.compile(r"^(?:spasticity_pyramidal_signs_sympt|hyperreflexia_sympt|babinski_sign)$"),
        CanonicalColumnMapping("phenotype", ("SPASTICITY_PYRAMIDAL_SIGNS",)),
    ),
    (
        re.compile(r"^(?:ataxia_dysdiadochokinesia_sympt|ataxia_sympt)$"),
        CanonicalColumnMapping("phenotype", ("ATAXIA",)),
    ),
    (re.compile(r"^cerebellar_signs$"), CanonicalColumnMapping("phenotype", ("CEREBELLAR_SIGNS",))),
    (re.compile(r"^chorea_sympt$"), CanonicalColumnMapping("phenotype", ("CHOREA",))),
    (
        re.compile(r"^(?:myoclonus_sympt|minimyoclonus_sympt)$"),
        CanonicalColumnMapping("phenotype", ("MYOCLONUS",)),
    ),
    (re.compile(r"^seizures_sympt$"), CanonicalColumnMapping("phenotype", ("SEIZURES",))),
    (
        re.compile(r"^(?:development_delay_sympt|dd_id_sympt)$"),
        CanonicalColumnMapping("phenotype", ("DEVELOPMENTAL_DELAY",)),
    ),
    (
        re.compile(
            r"^(?:intellectual_disability_sympt|intellectual_developmental_disorder_sympt)$"
        ),
        CanonicalColumnMapping("phenotype", ("INTELLECTUAL_DISABILITY",)),
    ),
    (re.compile(r"^dysphagia_sympt$"), CanonicalColumnMapping("phenotype", ("DYSPHAGIA",))),
    (
        re.compile(r"^dysarthria_anarthria_sympt$"),
        CanonicalColumnMapping("phenotype", ("DYSARTHRIA",)),
    ),
    (
        re.compile(r"^(?:hypomimia_sympt|monotonous_speech_sympt)$"),
        CanonicalColumnMapping("phenotype", ("HYPOPHONIA_OR_HYPOMIMIA",)),
    ),
    (
        re.compile(r"^(?:gd_hepatosplenomegaly_sympt|gd_blood_abnorm_sympt|gd_bone_abnorm_sympt)$"),
        CanonicalColumnMapping("phenotype", ("GLUCOCEREBROSIDASE_SYSTEMIC_FEATURES",)),
    ),
)

_TEXT_FEATURE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:parkinsonism|parkinsonian|parkinson's disease)\b", re.I), "PARKINSONISM"),
    (re.compile(r"\bbradykinesia\b|\bslowness\b", re.I), "BRADYKINESIA"),
    (re.compile(r"\brigidity\b|\bstiffness\b", re.I), "RIGIDITY"),
    (re.compile(r"\b(?:rest(?:ing)? tremor|pill[- ]rolling tremor)\b", re.I), "TREMOR_REST"),
    (re.compile(r"\btremor\b", re.I), "TREMOR_OTHER"),
    (re.compile(r"\bdystonia\b|\bdystonic\b", re.I), "DYSTONIA"),
    (re.compile(r"\b(?:leg|foot|lower limb).{0,30}\bdystonia\b", re.I), "LOWER_LIMB_DYSTONIA"),
    (re.compile(r"\bblepharospasm\b", re.I), "BLEPHAROSPASM"),
    (
        re.compile(r"\bautosomal dominant\b|\bdominant family history\b", re.I),
        "AUTOSOMAL_DOMINANT_PEDIGREE",
    ),
    (
        re.compile(r"\bautosomal recessive\b|\brecessive inheritance\b", re.I),
        "AUTOSOMAL_RECESSIVE_PEDIGREE",
    ),
    (re.compile(r"\bconsanguin", re.I), "CONSANGUINITY"),
    (re.compile(r"\bmaternal inheritance\b", re.I), "MATERNAL_INHERITANCE"),
    (re.compile(r"\bpaternal inheritance\b", re.I), "PATERNAL_INHERITANCE"),
    (
        re.compile(
            r"\bdiurnal (?:fluctuation|fluctuations|variation)\b|\bworsening in the evening\b", re.I
        ),
        "DIURNAL_FLUCTUATION",
    ),
    (re.compile(r"\bsleep benefit\b", re.I), "SLEEP_BENEFIT"),
    (re.compile(r"\blevodopa\b|\bl[- ]dopa\b", re.I), "LEVODOPA_RESPONSE"),
    (re.compile(r"\bdyskinesia\b", re.I), "DYSKINESIA"),
    (re.compile(r"\bhyposmia\b|\bloss of smell\b|\bolfactory\b", re.I), "HYPOSMIA"),
    (
        re.compile(r"\bcognitive decline\b|\bcognitive impairment\b|\bdementia\b", re.I),
        "COGNITIVE_DECLINE",
    ),
    (re.compile(r"\bhallucinations?\b|\bpsychosis\b", re.I), "HALLUCINATIONS"),
    (
        re.compile(r"\bautonomic\b|\northostatic\b|\burinary\b|\bincontinence\b", re.I),
        "AUTONOMIC_DYSFUNCTION",
    ),
    (re.compile(r"\bdepression\b|\bdepressive\b", re.I), "DEPRESSION"),
    (re.compile(r"\banxiety\b|\banxious\b", re.I), "ANXIETY"),
    (re.compile(r"\bREM sleep behavior disorder\b|\bRBD\b", re.I), "RBD"),
    (re.compile(r"\batypical parkinsonism\b|\bkufor[- ]rakeb\b", re.I), "ATYPICAL_PARKINSONISM"),
    (re.compile(r"\bvertical gaze palsy\b|\bgaze palsy\b", re.I), "VERTICAL_GAZE_PALSY"),
    (
        re.compile(r"\bpyramidal signs?\b|\bspasticity\b|\bhyperreflexia\b|\bbabinski\b", re.I),
        "SPASTICITY_PYRAMIDAL_SIGNS",
    ),
)

_POSITIVE_VALUES = {
    "1",
    "1.0",
    "yes",
    "y",
    "true",
    "present",
    "confirmed",
    "positive",
    "affected",
}
_NEGATIVE_VALUES = {"0", "0.0", "no", "n", "false", "absent", "negative", "unaffected"}
_UNKNOWN_VALUES = {
    "",
    "-99",
    "-99.0",
    "nan",
    "none",
    "not reported",
    "not_reported",
    "unknown",
    "clinically uncertain",
    "uncertain",
    "na",
    "n/a",
}

RUNTIME_HALLMARK_ALIASES: dict[str, str] = {
    "autonomic_dysfunction": "AUTONOMIC_DYSFUNCTION",
    "blepharospasm": "BLEPHAROSPASM",
    "bradykinesia": "BRADYKINESIA",
    "cognitive_decline": "COGNITIVE_DECLINE",
    "depression": "DEPRESSION",
    "diurnal_fluctuation": "DIURNAL_FLUCTUATION",
    "diurnal_fluctuations": "DIURNAL_FLUCTUATION",
    "dyskinesia": "DYSKINESIA",
    "dystonia": "DYSTONIA",
    "hallucinations": "HALLUCINATIONS",
    "hyposmia": "HYPOSMIA",
    "kufor_rakeb_atypical_pd": "ATYPICAL_PARKINSONISM",
    "levodopa_response": "LEVODOPA_RESPONSE",
    "parkinsonism": "PARKINSONISM",
    "rigidity": "RIGIDITY",
    "severe_parkinsonism": "ATYPICAL_PARKINSONISM",
    "sleep_benefit": "SLEEP_BENEFIT",
    "spasticity_pyramidal_signs": "SPASTICITY_PYRAMIDAL_SIGNS",
    "tremor_rest": "TREMOR_REST",
    "vertical_gaze_palsy": "VERTICAL_GAZE_PALSY",
    "familial_history": "FAMILY_HISTORY",
    "family_history": "FAMILY_HISTORY",
    "autosomal_dominant_pedigree": "AUTOSOMAL_DOMINANT_PEDIGREE",
    "autosomal_recessive_pedigree": "AUTOSOMAL_RECESSIVE_PEDIGREE",
    "consanguinity": "CONSANGUINITY",
}


def map_column(header: object) -> CanonicalColumnMapping:
    normalized = normalize_column_name(header)
    if normalized in _EXACT_COLUMNS:
        return _EXACT_COLUMNS[normalized]
    if _VARIANT_COLUMN_RE.match(normalized):
        return CanonicalColumnMapping("variant")
    for pattern, mapping in _COLUMN_PATTERNS:
        if pattern.match(normalized):
            return mapping
    return CanonicalColumnMapping("ignored")


def map_column_for_gene(gene: str, header: object) -> CanonicalColumnMapping:
    normalized = normalize_column_name(header)
    explicit = _SOURCE_SPECIFIC_COLUMNS.get((gene, normalized))
    if explicit is not None:
        return explicit
    return map_column(header)


def canonical_features_for_column(header: object) -> tuple[str, ...]:
    mapping = map_column(header)
    if mapping.role in {"phenotype", "pedigree"}:
        return mapping.targets
    return ()


def runtime_concept_to_canonical(concept: object) -> str | None:
    if not isinstance(concept, str):
        return None
    normalized = concept.strip()
    if normalized in CANONICAL_PHENOTYPE_FEATURES or normalized in PEDIGREE_FEATURES:
        return normalized
    return RUNTIME_HALLMARK_ALIASES.get(normalized.lower())


def classify_presence(value: object) -> Literal["positive", "negative", "unknown"]:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "positive" if value else "negative"
    if isinstance(value, int | float):
        if value == 1:
            return "positive"
        if value == 0:
            return "negative"
        if value == -99:
            return "unknown"
    text = str(value).strip().lower()
    if text in _POSITIVE_VALUES:
        return "positive"
    if text in _NEGATIVE_VALUES:
        return "negative"
    if text in _UNKNOWN_VALUES:
        return "unknown"
    return "unknown"


def canonicalize_text_features(text: object) -> tuple[str, ...]:
    if text is None:
        return ()
    raw = str(text).strip()
    if classify_presence(raw) != "unknown":
        return ()
    features: list[str] = []
    for pattern, feature in _TEXT_FEATURE_PATTERNS:
        if pattern.search(raw) and feature not in features:
            features.append(feature)
    return tuple(features)


def parse_aao_years(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float) and not isinstance(value, bool):
        numeric = float(value)
        return numeric if 0.0 < numeric <= 120.0 else None
    text = str(value).strip().lower()
    if text in _UNKNOWN_VALUES:
        return None
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", text)
    if not match:
        return None
    numeric = float(match.group(1))
    return numeric if 0.0 < numeric <= 120.0 else None


def aao_group_for_years(aao_years: float | None) -> str:
    if aao_years is None:
        return "AAO_MISSING"
    if aao_years <= 20:
        return "JUVENILE_ONSET"
    if aao_years < 45:
        return "EARLY_ONSET"
    return "LATE_ONSET"


def canonicalize_sex(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"f", "female", "woman"}:
        return "female"
    if text in {"m", "male", "man"}:
        return "male"
    if text in {"other", "nonbinary", "non_binary"}:
        return "other"
    return "unknown"


def canonicalize_zygosity(values: object | tuple[object, ...]) -> str:
    raw_values = values if isinstance(values, tuple) else (values,)
    texts = [str(v or "").strip().lower().replace("-", "_").replace(" ", "_") for v in raw_values]
    texts = [t for t in texts if t not in _UNKNOWN_VALUES]
    if not texts:
        return "unknown"
    joined = " ".join(texts)
    if "compound" in joined:
        return "compound_heterozygous"
    if "hemizyg" in joined:
        return "hemizygous"
    if "homozyg" in joined or re.search(r"\bhom\b", joined):
        return "homozygous"
    heterozygous_count = sum(
        1 for text in texts if "heterozyg" in text or re.search(r"\bhet\b", text)
    )
    if heterozygous_count >= 2:
        return "compound_heterozygous"
    if heterozygous_count == 1:
        return "heterozygous"
    return "unknown"


def canonicalize_inheritance(value: object) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if (
        text in _UNKNOWN_VALUES
        or "heterozyg" in text
        or "homozyg" in text
        or re.search(r"\bhet\b|\bhom\b", text)
    ):
        return "unknown"
    if "de_novo" in text or "denovo" in text:
        return "de_novo"
    if "dominant" in text or text == "ad":
        return "autosomal_dominant"
    if "recessive" in text or text == "ar":
        return "autosomal_recessive"
    if "x_link" in text or "xlinked" in text:
        return "x_linked"
    if "mitochondrial" in text or "maternal" in text:
        return "mitochondrial"
    return "unknown"


def canonicalize_family_history(value: object) -> str:
    status = classify_presence(value)
    if status == "positive":
        return "positive"
    if status == "negative":
        return "negative"
    text = str(value or "").strip().lower()
    if "sporadic" in text or "no family history" in text:
        return "negative"
    if (
        "family history" in text
        or "famhx" in text
        or "familial" in text
        or "affected relative" in text
        or "affected parent" in text
        or "dominant family" in text
    ):
        return "positive"
    return "unknown"


def ontology_export() -> dict[str, object]:
    return {
        "ontology_version": "10gene-parkinsonism-v1.1",
        "genes": list(GENES),
        "phenotype_features": list(CANONICAL_PHENOTYPE_FEATURES),
        "pedigree_features": list(PEDIGREE_FEATURES),
        "sex_values": list(SEX_VALUES),
        "aao_groups": list(AAO_GROUPS),
        "zygosity_values": list(ZYGOSITY_VALUES),
        "inheritance_values": list(INHERITANCE_VALUES),
        "family_history_values": list(FAMILY_HISTORY_VALUES),
        "source_specific_column_mappings": [
            {
                "gene": mapping.gene,
                "mapping_version": mapping.mapping_version,
                "normalized_source_column": mapping.normalized_source_column,
                "rationale": mapping.rationale,
                "role": mapping.role,
                "targets": list(mapping.targets),
            }
            for mapping in SOURCE_SPECIFIC_COLUMN_MAPPINGS
        ],
        "runtime_hallmark_aliases": dict(sorted(RUNTIME_HALLMARK_ALIASES.items())),
    }
