import json
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

# ==============================================================================
# HYBRID PROTOTYPE H1.1: OBSERVATION CONTRACT (SCHEMA 1.1)
# ==============================================================================

class EpistemicStatus(str, Enum):
    ASSERTED = "ASSERTED"
    REPORTED = "REPORTED"
    SUSPECTED = "SUSPECTED"
    POSSIBLE = "POSSIBLE"
    UNCERTAIN = "UNCERTAIN"
    UNCONFIRMED = "UNCONFIRMED"
    QUOTED = "QUOTED"
    SUPERSEDED = "SUPERSEDED"
    CONFLICTING = "CONFLICTING"

class TemporalScope(str, Enum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    RESOLVED = "RESOLVED"
    ONSET = "ONSET"

class TemporalRelationType(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    DURING = "DURING"
    ONSET = "ONSET"
    RESOLVED = "RESOLVED"
    INTERVAL = "INTERVAL"

class TemporalAnchor(str, Enum):
    MOTOR_SYMPTOMS = "motor_symptoms"
    DIAGNOSIS = "diagnosis"
    VISIT = "visit"
    CURRENT_TIME = "current_time"
    ADOLESCENCE = "adolescence"
    UNIVERSITY = "university"
    FIRST_SYMPTOM = "first_symptom"
    CUSTOM = "custom"

class SubjectType(str, Enum):
    PROBAND = "proband"
    FATHER = "father"
    MOTHER = "mother"
    SISTER = "sister"
    BROTHER = "brother"
    GRANDFATHER = "grandfather"
    GRANDMOTHER = "grandmother"
    SON = "son"
    DAUGHTER = "daughter"
    AUNT = "aunt"
    COUSIN = "cousin"
    RELATIVE = "relative"

class PredicateType(str, Enum):
    HAS_SYMPTOM = "HAS_SYMPTOM"
    HAS_NORMAL_FINDING = "HAS_NORMAL_FINDING"
    HAS_VARIANT = "HAS_VARIANT"
    HAS_GENE_MENTION = "HAS_GENE_MENTION"
    HAS_CLASSIFICATION_ASSERTION = "HAS_CLASSIFICATION_ASSERTION"
    AGGREGATE_CLASSIFICATION_ASSERTION = "AGGREGATE_CLASSIFICATION_ASSERTION"
    HAS_PARENTAL_ORIGIN = "HAS_PARENTAL_ORIGIN"
    HAS_ZYGOSITY = "HAS_ZYGOSITY"
    HAS_PHASE_ASSERTION = "HAS_PHASE_ASSERTION"
    HAS_ONSET_AGE = "HAS_ONSET_AGE"
    HAS_CURRENT_AGE = "HAS_CURRENT_AGE"
    HAS_TEMPORAL_ASSERTION = "HAS_TEMPORAL_ASSERTION"
    DOCUMENT_SUPERSEDES = "DOCUMENT_SUPERSEDES"
    DOCUMENT_CORRECTS = "DOCUMENT_CORRECTS"
    DOCUMENT_QUOTES = "DOCUMENT_QUOTES"
    SOURCE_ASSERTS = "SOURCE_ASSERTS"
    RELATION_UNRESOLVED = "RELATION_UNRESOLVED"

# Canonical Symptom Concept Ontology Whitelist
ALLOWED_SYMPTOM_CONCEPTS = {
    "dystonia",
    "tremor_rest",
    "bradykinesia",
    "rigidity",
    "diurnal_fluctuation",
    "vertical_gaze_palsy",
    "spasticity_pyramidal_signs",
    "kufor_rakeb_atypical_pd",
    "hyposmia",
    "cognitive_decline",
    "severe_parkinsonism",
    "hallucinations",
    "sleep_benefit",
    "levodopa_response",
    "autonomic_dysfunction",
    "depression",
    "blepharospasm",
    "dyskinesia",
    "parkinsonism"
}

@dataclass
class SourceSpan:
    text_span: str
    start: int
    end: int
    source_type: str = "clinical_text"
    asserted_by: Optional[str] = None

@dataclass
class Subject:
    type: str
    id: str = "subject_default"

@dataclass
class TemporalRelation:
    relation_type: str  # TemporalRelationType
    anchor: str         # TemporalAnchor | str
    source_span: Optional[SourceSpan] = None

@dataclass
class Observation:
    id: str
    predicate: str
    subject: Subject
    concept: Optional[str] = None
    raw_finding: Optional[str] = None
    candidate_concept: Optional[str] = None
    mapping_status: str = "CONFIRMED"  # CONFIRMED | PROPOSED
    raw_variant: Optional[str] = None
    polarity: str = "positive"  # positive | negative
    temporal_scope: str = TemporalScope.CURRENT.value
    epistemic_status: str = EpistemicStatus.ASSERTED.value
    target: Optional[str] = None
    value: Optional[Any] = None
    source: Optional[SourceSpan] = None
    antecedent_span: Optional[SourceSpan] = None  # Anaphoric grounding
    temporal_relation: Optional[TemporalRelation] = None  # Typed temporal relation
    relation_object: Optional[str] = None  # Experiencer vs Relation object distinction (e.g. mother/father)
    counts: Optional[Dict[str, int]] = None  # For aggregate multiset classifications
    assignment_status: Optional[str] = None  # UNRESOLVED | RESOLVED
    confidence: float = 1.0
    resolution_method: str = "direct_mention"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DocumentExtractionBatch:
    schema_version: str = "1.1"
    document_id: str = "doc_default"
    raw_text: str = ""
    observations: List[Observation] = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentExtractionBatch":
        obs_list = []
        for o in data.get("observations", []):
            subj_data = o.get("subject", {"type": "proband"})
            subj = Subject(type=subj_data.get("type", "proband"), id=subj_data.get("id", "subject_default"))
            src_data = o.get("source")
            src = SourceSpan(
                text_span=src_data.get("text_span", ""),
                start=src_data.get("start", 0),
                end=src_data.get("end", 0),
                source_type=src_data.get("source_type", "clinical_text"),
                asserted_by=src_data.get("asserted_by")
            ) if src_data else None

            ant_data = o.get("antecedent_span")
            ant_src = SourceSpan(
                text_span=ant_data.get("text_span", ""),
                start=ant_data.get("start", 0),
                end=ant_data.get("end", 0),
                source_type=ant_data.get("source_type", "clinical_text"),
                asserted_by=ant_data.get("asserted_by")
            ) if ant_data else None

            tr_data = o.get("temporal_relation")
            tr = None
            if tr_data:
                tr_src_data = tr_data.get("source_span")
                tr_src = SourceSpan(
                    text_span=tr_src_data.get("text_span", ""),
                    start=tr_src_data.get("start", 0),
                    end=tr_src_data.get("end", 0)
                ) if tr_src_data else None
                tr = TemporalRelation(
                    relation_type=tr_data.get("relation_type", "BEFORE"),
                    anchor=tr_data.get("anchor", "motor_symptoms"),
                    source_span=tr_src
                )

            obs = Observation(
                id=o.get("id", "obs"),
                predicate=o.get("predicate", ""),
                subject=subj,
                concept=o.get("concept"),
                raw_finding=o.get("raw_finding"),
                candidate_concept=o.get("candidate_concept"),
                mapping_status=o.get("mapping_status", "CONFIRMED"),
                raw_variant=o.get("raw_variant"),
                polarity=o.get("polarity", "positive"),
                temporal_scope=o.get("temporal_scope", TemporalScope.CURRENT.value),
                epistemic_status=o.get("epistemic_status", EpistemicStatus.ASSERTED.value),
                target=o.get("target"),
                value=o.get("value"),
                source=src,
                antecedent_span=ant_src,
                temporal_relation=tr,
                relation_object=o.get("relation_object"),
                counts=o.get("counts"),
                assignment_status=o.get("assignment_status"),
                confidence=o.get("confidence", 1.0),
                resolution_method=o.get("resolution_method", "direct_mention")
            )
            obs_list.append(obs)

        return cls(
            schema_version=data.get("schema_version", "1.1"),
            document_id=data.get("document_id", "doc_default"),
            raw_text=data.get("raw_text", ""),
            observations=obs_list
        )
