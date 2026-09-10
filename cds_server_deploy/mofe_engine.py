# ==============================================================================
# FROZEN MOFE NEURAL & DUAL-EXPERT CLINICAL ENGINE (REVISION 4/5)
# Zero custom heuristics. Pure 10-gene phenotype differential.
# ==============================================================================
import json
import numpy as np

ALL_10_GENES = ["ATP13A2", "GCH1", "PRKN", "PINK1", "PARK7", "GBA1", "SNCA", "LRRK2", "VPS35", "RAB32"]

TEMPERATURE = 2.2

EXPERT_A_GENES = ["GBA1", "LRRK2", "PRKN", "PARK7"]
EXPERT_B_GENES = ["RAB32", "VPS35", "SNCA", "ATP13A2", "PINK1", "GCH1"]

ATYPICAL_WEIGHTS = {
    "vertical_gaze_palsy": 3.0,
    "diurnal_fluctuation": 3.0,
    "spasticity_pyramidal_signs": 2.5,
    "cognitive_decline": 2.0,
    "autonomic_dysfunction": 2.0,
    "dystonia": 1.8,
    "levodopa_response": 1.5,
}
W_MAX = 15.8

def compute_alpha(features):
    score = sum(ATYPICAL_WEIGHTS[f] for f in features if f in ATYPICAL_WEIGHTS)
    s_norm = score / W_MAX
    alpha = 0.20 + 0.65 * s_norm
    return float(np.clip(alpha, 0.15, 0.85))

GENE_SIGNATURES = {
    "ATP13A2": {
        "hallmarks": ["vertical_gaze_palsy", "spasticity_pyramidal_signs", "kufor_rakeb_atypical_pd", "juvenile_onset", "cognitive_decline"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["juvenile_onset"]
    },
    "GCH1": {
        "hallmarks": ["dystonia", "diurnal_fluctuation", "levodopa_response", "juvenile_onset"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["juvenile_onset", "early_onset"]
    },
    "PRKN": {
        "hallmarks": ["sleep_benefit", "dyskinesia", "tremor_rest", "early_onset", "dystonia"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["early_onset"]
    },
    "PINK1": {
        "hallmarks": ["early_onset", "depression", "tremor_rest", "sleep_benefit", "dystonia"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["early_onset"]
    },
    "PARK7": {
        "hallmarks": ["early_onset", "blepharospasm", "rigidity", "bradykinesia"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["early_onset"]
    },
    "GBA1": {
        "hallmarks": ["cognitive_decline", "hallucinations", "hyposmia", "late_onset", "depression"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    },
    "SNCA": {
        "hallmarks": ["cognitive_decline", "autonomic_dysfunction", "early_onset", "hallucinations", "severe_parkinsonism"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["early_onset", "late_onset"]
    },
    "LRRK2": {
        "hallmarks": ["tremor_rest", "late_onset", "bradykinesia", "rigidity"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    },
    "VPS35": {
        "hallmarks": ["tremor_rest", "late_onset", "bradykinesia", "rigidity"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    },
    "RAB32": {
        "hallmarks": ["tremor_rest", "late_onset", "bradykinesia", "rigidity"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    }
}

# Frozen Schema 1.1 System Prompt
FROZEN_SYSTEM_PROMPT_SCHEMA_1_1 = """You are a strictly constrained Clinical Semantic Extractor.
Your task is to extract atomic clinical and molecular observations from free clinical text into Schema 1.1 JSON.

STRICT CONSTRAINTS:
1. Extract ONLY observations literally supported by the input text.
2. DO NOT make clinical diagnoses or assign causal genes.
3. DO NOT normalize variants (keep the exact raw variant string from text, e.g. "c.1858G>A", "p.Asp620Asn", "c.255delA"). If both cDNA (e.g. "c.1858G>A") and protein (e.g. "p.Asp620Asn") changes appear, extract EACH as a separate atomic HAS_VARIANT observation.
4. For every observation, provide "source" with "text_span" containing the EXACT verbatim substring from the input text.
5. Approved concept whitelist for HAS_SYMPTOM:
   ['autonomic_dysfunction', 'blepharospasm', 'bradykinesia', 'cognitive_decline', 'depression', 'diurnal_fluctuation', 'dyskinesia', 'dystonia', 'hallucinations', 'hyposmia', 'kufor_rakeb_atypical_pd', 'levodopa_response', 'parkinsonism', 'rigidity', 'severe_parkinsonism', 'sleep_benefit', 'spasticity_pyramidal_signs', 'tremor_rest', 'vertical_gaze_palsy'].
   If a clinical finding does not exactly match a whitelist concept, output mapping_status="PROPOSED", raw_finding with the text phrase, and candidate_concept.
6. If an onset age is stated (e.g. "At age 44"), extract predicate="HAS_ONSET_AGE", value=44, temporal_scope="ONSET".
7. Unless explicit past cues (e.g. "years ago", "previously", "initially", "prior note") or onset cues appear, set temporal_scope="CURRENT".
8. If a symptom improved after sleep, extract concept="sleep_benefit".
9. For negations (e.g. "no cognitive symptoms"), set polarity="negative".
10. For relatives (e.g. "maternal aunt"), set subject={"type": "relative"}. For proband/patient, set subject={"type": "proband"}.
11. For document quotes or secondary reports, set epistemic_status="QUOTED" and source.asserted_by (e.g. "clinic_letter").
12. If multiple variant classifications are stated without linking to individual alleles, output AGGREGATE_CLASSIFICATION_ASSERTION with counts multiset, assignment_status="UNRESOLVED", and RELATION_UNRESOLVED.

OUTPUT FORMAT:
Return a single valid JSON object adhering to this structure:
{
  "schema_version": "1.1",
  "document_id": "doc_id",
  "observations": [
    {
      "id": "obs_001",
      "predicate": "HAS_SYMPTOM | HAS_NORMAL_FINDING | HAS_VARIANT | HAS_GENE_MENTION | HAS_CLASSIFICATION_ASSERTION | AGGREGATE_CLASSIFICATION_ASSERTION | HAS_PARENTAL_ORIGIN | HAS_ZYGOSITY | HAS_PHASE_ASSERTION | HAS_ONSET_AGE | HAS_CURRENT_AGE | RELATION_UNRESOLVED",
      "subject": {"type": "proband | father | mother | sister | brother | daughter | son | relative"},
      "concept": "canonical concept from whitelist or null",
      "raw_finding": "verbatim text phrase or null",
      "candidate_concept": "proposed candidate concept or null",
      "mapping_status": "CONFIRMED | PROPOSED",
      "raw_variant": "exact raw string from text or null",
      "polarity": "positive | negative",
      "temporal_scope": "CURRENT | HISTORICAL | RESOLVED | ONSET",
      "epistemic_status": "ASSERTED | REPORTED | SUSPECTED | POSSIBLE | UNCERTAIN | UNCONFIRMED | QUOTED | SUPERSEDED",
      "target": "target identifier if applicable or null",
      "value": "scalar value or dictionary of counts or null",
      "source": {
        "text_span": "exact verbatim substring from text",
        "start": 0,
        "end": 10,
        "asserted_by": "optional source or null"
      },
      "antecedent_span": null,
      "temporal_relation": null,
      "relation_object": null,
      "counts": null,
      "assignment_status": null
    }
  ]
}
"""
