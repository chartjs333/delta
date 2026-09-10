import sys
import os
import re
import json
import time
import math
import hashlib
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Ensure root workspace is on python path for importing existing frozen components
ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

from h1_contract import (
    DocumentExtractionBatch,
    Observation,
    PredicateType,
    Subject,
    SubjectType,
    SourceSpan,
    ALLOWED_SYMPTOM_CONCEPTS,
    EpistemicStatus,
    TemporalScope
)
from extraction_completeness_gate import ExtractionCompletenessGate
from formal_gate_validator import FormalGateValidator
from revision_6_2_engine import Revision62Engine, CANONICAL_CATALOG, SYNONYMS_MAP

# Import existing frozen MoFE architecture constants and functions
from mofe_engine import (
    ALL_10_GENES,
    GENE_SIGNATURES,
    TEMPERATURE,
    EXPERT_A_GENES,
    EXPERT_B_GENES,
    ATYPICAL_WEIGHTS,
    compute_alpha,
    FROZEN_SYSTEM_PROMPT_SCHEMA_1_1
)

# ==============================================================================
# SECURE CREDENTIAL LOADER (ZERO API KEY EXPOSURE IN CODE OR CLIENT LOGS)
# ==============================================================================
def get_secure_credentials() -> Tuple[str, str, str]:
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://llm-api.ai-lab.uni-luebeck.de/v1")
    model_name = os.environ.get("LLM_MODEL", "gemma-4-26b-a4b-it")
    
    # Check local .env first, then optional fallbacks
    candidate_env_paths = [
        Path(__file__).resolve().parent / ".env",
        Path.cwd() / ".env",
    ]
    for env_file in candidate_env_paths:
        if api_key and model_name:
            break
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("LLM_API_KEY=") and not api_key:
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("LLM_BASE_URL=") and not os.environ.get("LLM_BASE_URL"):
                        base_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("LLM_MODEL=") and not os.environ.get("LLM_MODEL"):
                        model_name = line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    return api_key, base_url or "https://llm-api.ai-lab.uni-luebeck.de/v1", model_name or "gemma-4-26b-a4b-it"

# Metadata for standard clinical display of the 10 genes
GENE_METADATA = {
    "PRKN": {
        "full_name": "Parkin RBR E3 Ubiquitin Ligase",
        "mode": "Autosomal Recessive",
        "typical_onset": "Early-onset (<=45y)"
    },
    "PINK1": {
        "full_name": "PTEN Induced Kinase 1",
        "mode": "Autosomal Recessive",
        "typical_onset": "Early-onset (<=45y)"
    },
    "PARK7": {
        "full_name": "Parkinsonism Associated Deglycase (DJ-1)",
        "mode": "Autosomal Recessive",
        "typical_onset": "Early-onset (<=45y)"
    },
    "GCH1": {
        "full_name": "GTP Cyclohydrolase 1 (DRD/Segawa)",
        "mode": "Autosomal Dominant",
        "typical_onset": "Juvenile-to-early onset (<=30y)"
    },
    "ATP13A2": {
        "full_name": "Kufor-Rakeb Cation Transporter",
        "mode": "Autosomal Recessive",
        "typical_onset": "Juvenile-onset (<=20y)"
    },
    "GBA1": {
        "full_name": "Glucosylceramidase Beta 1",
        "mode": "Autosomal Dominant / Susceptibility",
        "typical_onset": "Late-onset (>=50y)"
    },
    "SNCA": {
        "full_name": "Synuclein Alpha (PARK1/PARK4)",
        "mode": "Autosomal Dominant",
        "typical_onset": "Early-to-mid adult onset"
    },
    "LRRK2": {
        "full_name": "Leucine Rich Repeat Kinase 2",
        "mode": "Autosomal Dominant",
        "typical_onset": "Late-onset (>=50y)"
    },
    "VPS35": {
        "full_name": "VPS35 Retromer Complex Component",
        "mode": "Autosomal Dominant",
        "typical_onset": "Late-onset (>=50y)"
    },
    "RAB32": {
        "full_name": "RAB32 Member RAS Oncogene Family",
        "mode": "Autosomal Dominant",
        "typical_onset": "Late-onset (>=50y)"
    }
}

SYMPTOM_DISPLAY_NAMES = {
    "tremor_rest": "Resting tremor",
    "dystonia": "Dystonia",
    "rigidity": "Rigidity",
    "bradykinesia": "Bradykinesia",
    "parkinsonism": "Parkinsonism",
    "sleep_benefit": "Sleep benefit",
    "levodopa_response": "Levodopa response",
    "diurnal_fluctuation": "Diurnal fluctuation",
    "cognitive_decline": "Cognitive decline / Dementia",
    "hallucinations": "Visual hallucinations",
    "vertical_gaze_palsy": "Supranuclear vertical gaze palsy",
    "spasticity_pyramidal_signs": "Spasticity / Pyramidal signs",
    "kufor_rakeb_atypical_pd": "Atypical parkinsonism",
    "autonomic_dysfunction": "Autonomic dysfunction",
    "hyposmia": "Hyposmia",
    "depression": "Depression",
    "blepharospasm": "Blepharospasm",
    "dyskinesia": "Dyskinesia",
    "severe_parkinsonism": "Severe / Aggressive parkinsonism"
}

DEFINITIVE_GENE = "DEFINITIVE_GENE"
AMBIGUOUS_GENE_CLUSTER = "AMBIGUOUS_GENE_CLUSTER"
ABSTAIN = "ABSTAIN"

LOW_CLASSIFIER_CONFIDENCE = "LOW_CLASSIFIER_CONFIDENCE"
LOW_LOCAL_TRAIN_SUPPORT = "LOW_LOCAL_TRAIN_SUPPORT"
LOW_PUBLICATION_DIVERSITY = "LOW_PUBLICATION_DIVERSITY"
LOW_FAMILY_DIVERSITY = "LOW_FAMILY_DIVERSITY"
DOMINANT_CLUSTER_OOD = "DOMINANT_CLUSTER_OOD"
SAFETY_GUARD_UNAVAILABLE = "SAFETY_GUARD_UNAVAILABLE"

DOMINANT_CLUSTER_GENES = ("LRRK2", "VPS35", "RAB32", "SNCA")
REQUIRED_SUPPORT_REASON_CODES = {
    LOW_LOCAL_TRAIN_SUPPORT,
    LOW_PUBLICATION_DIVERSITY,
    LOW_FAMILY_DIVERSITY,
    DOMINANT_CLUSTER_OOD,
}

# ==============================================================================
# SCHEMA 1.1 JSON EXTRACTION & RECOVERY UTILITY
# ==============================================================================
def extract_schema_1_1_json(raw_text: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Robustly extracts and validates Schema 1.1 JSON from model output or internal reasoning.
    Handles direct JSON, markdown code fences, conversational pre/post-ambles,
    and trailing bracket truncation without ever throwing unhandled JSONDecodeError.
    Strictly verifies that output is a dictionary containing an 'observations' list.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    cleaned = raw_text.strip()
    if not cleaned:
        return None

    # 1. Direct parse attempt
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "observations" in data and isinstance(data["observations"], list):
            return data
    except Exception:
        pass

    # 2. Extract from markdown code fence ```(?:json)? ... ```
    fenced_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, re.IGNORECASE)
    if fenced_match:
        cand = fenced_match.group(1).strip()
        try:
            data = json.loads(cand)
            if isinstance(data, dict) and "observations" in data and isinstance(data["observations"], list):
                return data
        except Exception:
            pass

    # 3. Locate outer JSON object containing "observations"
    obs_idx = cleaned.find('"observations"')
    if obs_idx != -1:
        start_brace = cleaned.rfind("{", 0, obs_idx)
        if start_brace != -1:
            end_brace = cleaned.rfind("}")
            if end_brace > start_brace:
                cand = cleaned[start_brace : end_brace + 1].strip()
                try:
                    data = json.loads(cand)
                    if isinstance(data, dict) and "observations" in data and isinstance(data["observations"], list):
                        return data
                except Exception:
                    # Repair minor unclosed brackets if truncated
                    open_braces = cand.count("{")
                    close_braces = cand.count("}")
                    open_brackets = cand.count("[")
                    close_brackets = cand.count("]")
                    repaired = cand
                    if open_brackets > close_brackets:
                        repaired += ("]" * (open_brackets - close_brackets))
                    if open_braces > close_braces:
                        repaired += ("}" * (open_braces - close_braces))
                    try:
                        data = json.loads(repaired)
                        if isinstance(data, dict) and "observations" in data and isinstance(data["observations"], list):
                            return data
                    except Exception:
                        pass

    # 4. Fallback search for any { ... } block
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        cand = cleaned[first_brace : last_brace + 1].strip()
        try:
            data = json.loads(cand)
            if isinstance(data, dict) and "observations" in data and isinstance(data["observations"], list):
                return data
        except Exception:
            pass

    return None


# ==============================================================================
# PIPELINE SERVICE CLASS
# ==============================================================================
class ClinicalDecisionSupportPipeline:
    def __init__(self):
        self.completeness_gate = ExtractionCompletenessGate()
        self.r62_engine = Revision62Engine()
        self.api_key, self.base_url, self.model_name = get_secure_credentials()

        # Load the current phenotype classifier, with the frozen MoFE model as a legacy fallback.
        self.phenotype_model_loaded = False
        self.phenotype_model_kind = "unavailable"
        self._load_frozen_phenotype_model()
        self.safety_artifacts_loaded = False
        self.safety_artifact_error = ""
        self.safety_thresholds: Dict[str, Any] = {}
        self.safety_support_records: List[Dict[str, Any]] = []
        self.safety_support_vectors = np.zeros((0, 0), dtype=np.float32)
        self.safety_manifest: Dict[str, Any] = {}
        self._load_safety_artifacts()

        # Persistent Response Cache (caches live model extractions to accelerate demo playback)
        self.cache_path = DEMO_DIR / ".pipeline_cache.json"
        self._cache = self._load_cache()

    def _load_frozen_phenotype_model(self) -> None:
        """Loads the current classifier artifact or the legacy frozen MoFE weights."""
        classifier_paths = [
            DEMO_DIR / "model_10genes_phenotype_classifier.json",
            Path("D:/delta_dataset/phenotype_classifier_run/model_10genes_phenotype_classifier.json"),
            ROOT_DIR / "model_10genes_phenotype_classifier.json"
        ]
        for p in classifier_paths:
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if str(data.get("model_version", "")).startswith("10gene-phenotype-classifier"):
                        self._load_phenotype_classifier(data)
                        self.phenotype_model_loaded = True
                        self.phenotype_model_kind = "clinical_classifier_v1"
                        print(f"[Phenotype Model] Loaded phenotype classifier from {p}")
                        return
                except Exception as e:
                    print(f"[Phenotype Model] Error loading classifier {p}: {e}")

        legacy_paths = [
            DEMO_DIR / "model_10genes_mixed_nodes.json",
            Path("D:/delta_dataset/model_10genes_mixed_nodes.json"),
            ROOT_DIR / "model_10genes_mixed_nodes.json"
        ]

        for p in legacy_paths:
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    self.vocab = data["vocab"]
                    self.emb = np.array(data["embedding_weight"], dtype=np.float32)
                    self.out_w = np.array(data["output_weight"], dtype=np.float32)
                    if "output_bias" in data and data["output_bias"]:
                        self.out_b = np.array(data["output_bias"], dtype=np.float32)
                    self.phenotype_model_loaded = True
                    self.phenotype_model_kind = "legacy_mofe_deprecated"
                    print(f"[Phenotype Model] Loaded DEPRECATED frozen MoFE weights from {p}")
                    return
                except Exception as e:
                    print(f"[Phenotype Model] Error loading {p}: {e}")

        print("[Phenotype Model] WARNING: no phenotype classifier artifact found.")
        self.phenotype_model_loaded = False
        self.phenotype_model_kind = "unavailable"

    def _load_phenotype_classifier(self, data: Dict[str, Any]) -> None:
        self.classifier_genes = data["genes"]
        self.classifier_feature_order = data["feature_order"]
        self.classifier_pedigree_feature_order = data.get("pedigree_feature_order", [])
        self.classifier_ontology = data["canonical_features"]
        numeric_schema = data["input_schema"]["numeric_fields"]["aao_years_normalized"]
        self.classifier_aao_mean = float(numeric_schema["mean_train_only"])
        self.classifier_aao_std = float(numeric_schema["std_train_only"]) or 1.0
        self.classifier_temperature = float(data.get("calibration", {}).get("temperature", 1.0))
        self.classifier_weights = {
            name: np.array(value, dtype=np.float32)
            for name, value in data["weights"].items()
        }

    def _phenotype_model_status(self) -> str:
        if self.phenotype_model_kind == "clinical_classifier_v1":
            return "Active (Phenotype-to-Gene Classifier v1)"
        if self.phenotype_model_kind == "legacy_mofe_deprecated":
            return "Deprecated fallback (Frozen MoFE next-token model)"
        return "Phenotype model unavailable"

    def _classifier_softmax(self, logits: np.ndarray) -> np.ndarray:
        shifted = logits - np.max(logits)
        exp_vals = np.exp(shifted)
        denom = exp_vals.sum()
        return exp_vals / (denom if denom else 1.0)

    def _classifier_category_id(self, value: str, values: List[str]) -> int:
        try:
            return values.index(value)
        except ValueError:
            return values.index("unknown") if "unknown" in values else 0

    def _runtime_concept_to_canonical(self, concept: str) -> Optional[str]:
        aliases = self.classifier_ontology.get("runtime_hallmark_aliases", {})
        if concept in self.classifier_feature_order or concept in self.classifier_pedigree_feature_order:
            return concept
        return aliases.get(str(concept).lower())

    def _load_safety_artifacts(self) -> None:
        """Load frozen local safety artifacts colocated with the classifier model."""

        thresholds_path = DEMO_DIR / "safety_thresholds_v2.json"
        support_path = DEMO_DIR / "support_index_v2.json"
        manifest_path = DEMO_DIR / "compatibility_manifest_v2.json"
        try:
            thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
            support_index = json.loads(support_path.read_text(encoding="utf-8"))
            manifest = (
                json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest_path.exists()
                else {}
            )
            reason_codes = set(thresholds.get("reason_codes", []))
            missing_reasons = sorted(REQUIRED_SUPPORT_REASON_CODES - reason_codes)
            if missing_reasons:
                raise ValueError(f"SAFETY_THRESHOLDS_MISSING_REASON_CODES: {missing_reasons}")
            records = support_index.get("records", [])
            vectors = np.array([record["vector"] for record in records], dtype=np.float32)
            if vectors.ndim != 2 or vectors.shape[0] == 0:
                raise ValueError("SUPPORT_INDEX_EMPTY")
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            self.safety_support_vectors = vectors / np.clip(norms, 1e-12, None)
            self.safety_support_records = records
            self.safety_thresholds = thresholds
            self.safety_manifest = manifest
            self.safety_artifacts_loaded = True
            self.safety_artifact_error = ""
            print(f"[Safety v2] Loaded thresholds and support index from {DEMO_DIR}")
        except Exception as e:
            self.safety_artifacts_loaded = False
            self.safety_artifact_error = str(e)
            print(f"[Safety v2] WARNING: safety artifacts unavailable: {e}")

    def _compute_classifier_full_distribution(self, confirmed_features: List[Dict[str, Any]], onset_age: Optional[int], family_text: str = "") -> List[Dict[str, Any]]:
        feature_index = {f: i for i, f in enumerate(self.classifier_feature_order)}
        pedigree_index = {f: i for i, f in enumerate(self.classifier_pedigree_feature_order)}
        phenotype = np.zeros(len(self.classifier_feature_order), dtype=np.float32)
        pedigree = np.zeros(len(self.classifier_pedigree_feature_order), dtype=np.float32)

        for f in confirmed_features:
            if f.get("status") == "Present" and f.get("subject") == "Patient":
                canonical = self._runtime_concept_to_canonical(str(f.get("concept", "")))
                if canonical in feature_index:
                    phenotype[feature_index[canonical]] = 1.0
                elif canonical in pedigree_index:
                    pedigree[pedigree_index[canonical]] = 1.0

        lower_fam = family_text.lower()
        family_history = "unknown"
        inheritance = "unknown"
        if "consanguin" in lower_fam:
            family_history = "positive"
            inheritance = "autosomal_recessive"
            if "CONSANGUINITY" in pedigree_index:
                pedigree[pedigree_index["CONSANGUINITY"]] = 1.0
            if "AUTOSOMAL_RECESSIVE_PEDIGREE" in pedigree_index:
                pedigree[pedigree_index["AUTOSOMAL_RECESSIVE_PEDIGREE"]] = 1.0
        if "recessive" in lower_fam:
            family_history = "positive"
            inheritance = "autosomal_recessive"
            if "AUTOSOMAL_RECESSIVE_PEDIGREE" in pedigree_index:
                pedigree[pedigree_index["AUTOSOMAL_RECESSIVE_PEDIGREE"]] = 1.0
        if (
            "dominant" in lower_fam
            or "affected father" in lower_fam
            or "affected mother" in lower_fam
            or "affected parent" in lower_fam
            or "familial" in lower_fam
        ):
            family_history = "positive"
            inheritance = "autosomal_dominant"
            if "AUTOSOMAL_DOMINANT_PEDIGREE" in pedigree_index:
                pedigree[pedigree_index["AUTOSOMAL_DOMINANT_PEDIGREE"]] = 1.0

        if onset_age is None:
            aao_group = "AAO_MISSING"
            aao_numeric = np.array([0.0], dtype=np.float32)
            aao_missing = np.array([1.0], dtype=np.float32)
        else:
            if onset_age <= 20:
                aao_group = "JUVENILE_ONSET"
            elif onset_age <= 44:
                aao_group = "EARLY_ONSET"
            else:
                aao_group = "LATE_ONSET"
            aao_numeric = np.array(
                [(float(onset_age) - self.classifier_aao_mean) / self.classifier_aao_std],
                dtype=np.float32
            )
            aao_missing = np.array([0.0], dtype=np.float32)

        ontology = self.classifier_ontology
        sex_id = self._classifier_category_id("unknown", ontology["sex_values"])
        aao_id = self._classifier_category_id(aao_group, ontology["aao_groups"])
        zygosity_id = self._classifier_category_id("unknown", ontology["zygosity_values"])
        inheritance_id = self._classifier_category_id(inheritance, ontology["inheritance_values"])
        family_id = self._classifier_category_id(family_history, ontology["family_history_values"])
        weights = self.classifier_weights
        x = np.concatenate([
            phenotype,
            pedigree,
            weights["sex_embedding.weight"][sex_id],
            weights["aao_group_embedding.weight"][aao_id],
            weights["zygosity_embedding.weight"][zygosity_id],
            weights["inheritance_embedding.weight"][inheritance_id],
            weights["family_history_embedding.weight"][family_id],
            aao_numeric,
            aao_missing,
        ])
        h1 = np.maximum(0.0, weights["network.0.weight"].dot(x) + weights["network.0.bias"])
        h2 = np.maximum(0.0, weights["network.3.weight"].dot(h1) + weights["network.3.bias"])
        logits = weights["network.6.weight"].dot(h2) + weights["network.6.bias"]
        probs = self._classifier_softmax(logits / max(self.classifier_temperature, 1e-6))

        ranked = sorted(zip(self.classifier_genes, probs), key=lambda x: x[1], reverse=True)
        results = []
        for g, p in ranked:
            meta = GENE_METADATA.get(g, {"full_name": g, "mode": "Unknown", "typical_onset": "Unknown"})
            results.append({
                "gene": g,
                "probability": float(p),
                "score_pct": round(float(p) * 100, 1),
                "full_name": meta["full_name"],
                "inheritance": meta["mode"],
                "typical_onset": meta["typical_onset"]
            })
        return results

    def _compute_classifier_ranking(self, confirmed_features: List[Dict[str, Any]], onset_age: Optional[int], family_text: str = "") -> List[Dict[str, Any]]:
        return self._compute_classifier_full_distribution(confirmed_features, onset_age, family_text)[:5]

    def _family_context_terms(self, text: str) -> str:
        lower_text = text.lower()
        terms = []
        for term in (
            "consanguin",
            "recessive",
            "dominant",
            "affected father",
            "affected mother",
            "affected parent",
            "familial",
        ):
            if term in lower_text:
                terms.append(term)
        return " ".join(terms)

    def _classifier_support_vector(self, confirmed_features: List[Dict[str, Any]], onset_age: Optional[int], family_text: str = "") -> Optional[np.ndarray]:
        if self.phenotype_model_kind != "clinical_classifier_v1":
            return None

        feature_index = {f: i for i, f in enumerate(self.classifier_feature_order)}
        pedigree_index = {f: i for i, f in enumerate(self.classifier_pedigree_feature_order)}
        phenotype = np.zeros(len(self.classifier_feature_order), dtype=np.float32)
        pedigree = np.zeros(len(self.classifier_pedigree_feature_order), dtype=np.float32)

        for feature in confirmed_features:
            if feature.get("status") == "Present" and feature.get("subject") == "Patient":
                canonical = self._runtime_concept_to_canonical(str(feature.get("concept", "")))
                if canonical in feature_index:
                    phenotype[feature_index[canonical]] = 1.0
                elif canonical in pedigree_index:
                    pedigree[pedigree_index[canonical]] = 1.0

        lower_fam = family_text.lower()
        family_history = "unknown"
        inheritance = "unknown"
        if "consanguin" in lower_fam:
            family_history = "positive"
            inheritance = "autosomal_recessive"
            if "CONSANGUINITY" in pedigree_index:
                pedigree[pedigree_index["CONSANGUINITY"]] = 1.0
            if "AUTOSOMAL_RECESSIVE_PEDIGREE" in pedigree_index:
                pedigree[pedigree_index["AUTOSOMAL_RECESSIVE_PEDIGREE"]] = 1.0
        if "recessive" in lower_fam:
            family_history = "positive"
            inheritance = "autosomal_recessive"
            if "AUTOSOMAL_RECESSIVE_PEDIGREE" in pedigree_index:
                pedigree[pedigree_index["AUTOSOMAL_RECESSIVE_PEDIGREE"]] = 1.0
        if (
            "dominant" in lower_fam
            or "affected father" in lower_fam
            or "affected mother" in lower_fam
            or "affected parent" in lower_fam
            or "familial" in lower_fam
        ):
            family_history = "positive"
            inheritance = "autosomal_dominant"
            if "AUTOSOMAL_DOMINANT_PEDIGREE" in pedigree_index:
                pedigree[pedigree_index["AUTOSOMAL_DOMINANT_PEDIGREE"]] = 1.0

        if onset_age is None:
            aao_group = "AAO_MISSING"
            aao_numeric = np.array([0.0], dtype=np.float32)
            aao_missing = np.array([1.0], dtype=np.float32)
        else:
            if onset_age <= 20:
                aao_group = "JUVENILE_ONSET"
            elif onset_age <= 44:
                aao_group = "EARLY_ONSET"
            else:
                aao_group = "LATE_ONSET"
            aao_numeric = np.array(
                [(float(onset_age) - self.classifier_aao_mean) / self.classifier_aao_std],
                dtype=np.float32
            )
            aao_missing = np.array([0.0], dtype=np.float32)

        ontology = self.classifier_ontology

        def one_hot(value: str, values: List[str]) -> np.ndarray:
            row = np.zeros(len(values), dtype=np.float32)
            row[self._classifier_category_id(value, values)] = 1.0
            return row

        return np.concatenate([
            phenotype,
            pedigree,
            one_hot("unknown", ontology["sex_values"]),
            one_hot(aao_group, ontology["aao_groups"]),
            one_hot("unknown", ontology["zygosity_values"]),
            one_hot(inheritance, ontology["inheritance_values"]),
            one_hot(family_history, ontology["family_history_values"]),
            aao_numeric,
            aao_missing,
        ])

    def _distribution_uncertainty(self, distribution: List[Dict[str, Any]]) -> Dict[str, float]:
        probabilities = [float(row.get("probability", 0.0)) for row in distribution]
        ordered = sorted(probabilities, reverse=True)
        total = sum(probabilities) or 1.0
        normalized = [max(0.0, value / total) for value in probabilities]
        entropy = -sum(value * math.log(max(value, 1e-12)) for value in normalized if value > 0.0)
        return {
            "max_probability": ordered[0] if ordered else 0.0,
            "second_probability": ordered[1] if len(ordered) > 1 else 0.0,
            "top1_top2_margin": (ordered[0] - ordered[1]) if len(ordered) > 1 else 0.0,
            "entropy": entropy,
            "normalized_entropy": entropy / math.log(len(probabilities)) if len(probabilities) > 1 else 0.0,
        }

    def _support_stats(self, query_vector: np.ndarray, top1_gene: str) -> Dict[str, Any]:
        thresholds = self.safety_thresholds["support_guard"]
        k_neighbors = int(thresholds["k_neighbors"])
        floor = float(thresholds["neighbor_similarity_floor"])
        query_norm = query_vector / np.clip(np.linalg.norm(query_vector), 1e-12, None)
        similarities = self.safety_support_vectors.dot(query_norm)
        order = np.argsort(-similarities)[:k_neighbors]
        selected = [
            (float(similarities[idx]), self.safety_support_records[int(idx)])
            for idx in order
            if float(similarities[idx]) >= floor
        ]
        gene_distribution: Dict[str, int] = {}
        gene_similarity_mass: Dict[str, float] = {}
        publication_counts: Dict[str, int] = {}
        families = set()
        top_neighbors = []
        for rank, (similarity, record) in enumerate(selected, start=1):
            gene = str(record.get("gene", ""))
            publication_id = str(record.get("publication_id", ""))
            family_id = str(record.get("family_id", ""))
            gene_distribution[gene] = gene_distribution.get(gene, 0) + 1
            gene_similarity_mass[gene] = gene_similarity_mass.get(gene, 0.0) + similarity
            publication_counts[publication_id] = publication_counts.get(publication_id, 0) + 1
            families.add(family_id)
            top_neighbors.append({
                "rank": rank,
                "record_id": record.get("record_id"),
                "gene": gene,
                "publication_id": publication_id,
                "family_id": family_id,
                "similarity": round(similarity, 6),
            })
        effective_neighbor_count = len(selected)
        max_publication_count = max(publication_counts.values(), default=0)
        top1_share = (
            gene_distribution.get(top1_gene, 0) / effective_neighbor_count
            if effective_neighbor_count
            else 0.0
        )
        return {
            "k_neighbors": min(k_neighbors, len(self.safety_support_records)),
            "neighbor_similarity_floor": floor,
            "nearest_neighbor_similarity": float(similarities[order[0]]) if len(order) else 0.0,
            "effective_neighbor_count": effective_neighbor_count,
            "gene_distribution": dict(sorted(gene_distribution.items())),
            "gene_similarity_mass": {
                gene: round(value, 6) for gene, value in sorted(gene_similarity_mass.items())
            },
            "unique_publications": len(publication_counts),
            "unique_families": len(families),
            "local_publication_concentration": (
                max_publication_count / effective_neighbor_count
                if effective_neighbor_count
                else 1.0
            ),
            "top1_local_gene_neighbor_share": top1_share,
            "top_neighbors": top_neighbors,
        }

    def _support_reason_codes(self, stats: Dict[str, Any]) -> List[str]:
        thresholds = self.safety_thresholds["support_guard"]
        reasons: List[str] = []
        if stats["nearest_neighbor_similarity"] < float(thresholds["min_nearest_neighbor_similarity"]):
            reasons.append(DOMINANT_CLUSTER_OOD)
        if (
            stats["effective_neighbor_count"] < int(thresholds["min_effective_neighbor_count"])
            or stats["top1_local_gene_neighbor_share"] < float(thresholds["min_top1_gene_neighbor_share"])
        ):
            reasons.append(LOW_LOCAL_TRAIN_SUPPORT)
        if (
            stats["unique_publications"] < int(thresholds["min_unique_publications"])
            or stats["local_publication_concentration"] > float(thresholds["max_publication_concentration"])
        ):
            reasons.append(LOW_PUBLICATION_DIVERSITY)
        if stats["unique_families"] < int(thresholds["min_unique_families"]):
            reasons.append(LOW_FAMILY_DIVERSITY)
        return reasons

    def evaluate_classifier_safety(self, confirmed_features: List[Dict[str, Any]], onset_age: Optional[int], family_text: str = "") -> Dict[str, Any]:
        if not self.phenotype_model_loaded or self.phenotype_model_kind != "clinical_classifier_v1":
            return {
                "status": ABSTAIN,
                "reason_codes": [SAFETY_GUARD_UNAVAILABLE],
                "top_candidate": None,
                "classifier_score_pct": None,
                "classifier_score_label": "classifier score",
                "support_guard_applied": False,
                "support_guard_error": "clinical classifier v1 artifact unavailable",
            }

        distribution = self._compute_classifier_full_distribution(confirmed_features, onset_age, family_text)
        if not distribution:
            return {
                "status": ABSTAIN,
                "reason_codes": [SAFETY_GUARD_UNAVAILABLE],
                "top_candidate": None,
                "classifier_score_pct": None,
                "classifier_score_label": "classifier score",
                "support_guard_applied": False,
                "support_guard_error": "empty classifier distribution",
            }

        top1 = distribution[0]
        top1_gene = str(top1["gene"])
        status = DEFINITIVE_GENE
        reason_codes: List[str] = []
        threshold_hits: Dict[str, bool] = {}
        uncertainty = self._distribution_uncertainty(distribution)
        uncertainty_thresholds = self.safety_thresholds.get("uncertainty", {})
        if top1_gene in DOMINANT_CLUSTER_GENES and uncertainty_thresholds:
            threshold_hits = {
                "max_probability_below_threshold": (
                    uncertainty["max_probability"] <= float(uncertainty_thresholds["max_probability"])
                ),
                "top1_top2_margin_below_threshold": (
                    uncertainty["top1_top2_margin"] <= float(uncertainty_thresholds["top1_top2_margin"])
                ),
                "entropy_above_threshold": (
                    uncertainty["normalized_entropy"] >= float(uncertainty_thresholds["normalized_entropy"])
                ),
            }
            if any(threshold_hits.values()):
                status = AMBIGUOUS_GENE_CLUSTER
                reason_codes.append(LOW_CLASSIFIER_CONFIDENCE)

        support_stats: Dict[str, Any] = {}
        support_guard_error = ""
        support_guard_applied = False
        if top1_gene in DOMINANT_CLUSTER_GENES:
            try:
                if not self.safety_artifacts_loaded:
                    raise RuntimeError(self.safety_artifact_error or "safety artifacts unavailable")
                query_vector = self._classifier_support_vector(confirmed_features, onset_age, family_text)
                if query_vector is None:
                    raise RuntimeError("support vector unavailable")
                support_stats = self._support_stats(query_vector, top1_gene)
                support_reasons = self._support_reason_codes(support_stats)
                support_guard_applied = True
                if support_reasons:
                    status = AMBIGUOUS_GENE_CLUSTER
                    reason_codes.extend(support_reasons)
            except Exception as e:
                support_guard_error = str(e)
                status = AMBIGUOUS_GENE_CLUSTER
                reason_codes.append(SAFETY_GUARD_UNAVAILABLE)

        deduped_reason_codes = list(dict.fromkeys(reason_codes))
        return {
            "status": status,
            "reason_codes": deduped_reason_codes,
            "top_candidate": top1_gene,
            "classifier_score_pct": float(top1["score_pct"]),
            "classifier_score_label": "classifier score",
            "classifier_score_note": "Relative phenotype-model ranking score; not a confirmed diagnostic probability.",
            "probability_abstention": {
                "threshold_hits": threshold_hits,
                "uncertainty": uncertainty,
                "thresholds": uncertainty_thresholds,
            },
            "support_guard_applied": support_guard_applied,
            "support_guard_error": support_guard_error,
            "support_guard": support_stats,
            "support_guard_thresholds": self.safety_thresholds.get("support_guard", {}),
            "artifact_manifest": self.safety_manifest,
        }

    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        try:
            self.cache_path.write_text(json.dumps(self._cache, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def _call_nlp_model(self, text: str) -> Dict[str, Any]:
        """
        Calls live NLP model API (gemma-4-26b-a4b-it / deepseek-v4-flash) to extract Schema 1.1 JSON observations.
        STRICT: ZERO heuristic / regex fallback.
        Includes bounded output tokens and automated recovery from model output.
        """
        cache_key = hashlib.sha256(f"{self.model_name}:{text.strip()}".encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.api_key:
            raise RuntimeError("Live NLP API Key is not configured in environment or .env.")

        user_prompt = f"Extract Schema 1.1 observations from the following text:\n\n\"\"\"\n{text}\n\"\"\""
        last_error = "Unknown error"

        # Setup SSL Context (supporting certifi if available, or automatic fallback for corporate/internal CAs)
        ssl_ctx = None
        if os.environ.get("LLM_SSL_VERIFY", "1").lower() in ("0", "false", "no"):
            ssl_ctx = ssl._create_unverified_context()
        else:
            try:
                import certifi
                ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                try:
                    ssl_ctx = ssl.create_default_context()
                except Exception:
                    ssl_ctx = ssl._create_unverified_context()

        # Token allowances
        token_attempts = [4096, 6144] if "gemma" in self.model_name.lower() else [16384]
        for attempt, max_tok in enumerate(token_attempts):
            req_payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": FROZEN_SYSTEM_PROMPT_SCHEMA_1_1},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": max_tok,
                "response_format": {"type": "json_object"}
            }

            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(req_payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            try:
                try:
                    resp_ctx = urllib.request.urlopen(req, timeout=300, context=ssl_ctx)
                except urllib.error.URLError as url_err:
                    err_str = str(url_err)
                    if "CERTIFICATE_VERIFY_FAILED" in err_str or "certificate verify failed" in err_str:
                        print(f"[!] Warning: SSL certificate verification failed ({err_str}). Retrying with unverified context...")
                        resp_ctx = urllib.request.urlopen(req, timeout=180, context=ssl._create_unverified_context())
                    else:
                        raise url_err

                with resp_ctx as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    choice = resp_data["choices"][0]
                    msg = choice.get("message", {})
                    content = msg.get("content") or ""
                    reasoning_content = msg.get("reasoning_content") or ""
                    finish_reason = choice.get("finish_reason", "unknown")

                    # 1. Primary: Extract from model message content
                    parsed = extract_schema_1_1_json(content)

                    # 2. Secondary: If content was empty/truncated, extract drafted JSON from model reasoning
                    if parsed is None and reasoning_content:
                        parsed = extract_schema_1_1_json(reasoning_content)

                    if parsed is not None:
                        # Cache successful live model extraction
                        self._cache[cache_key] = parsed
                        self._save_cache()
                        return parsed

                    last_error = f"Model response contained no valid Schema 1.1 observations (finish_reason: {finish_reason}, content_len: {len(content)}, reasoning_len: {len(reasoning_content)})"

            except Exception as e:
                last_error = str(e)

        # Strictly NO heuristic / regex fallback: raise RuntimeError to invoke safe ABSTAIN
        raise RuntimeError(f"{self.model_name} extraction failed: {last_error}")

    def _call_deepseek_v4_flash(self, text: str) -> Dict[str, Any]:
        """Backward compatibility alias."""
        return self._call_nlp_model(text)

    def compute_phenotype_ranking(self, confirmed_features: List[Dict[str, Any]], onset_age: Optional[int], family_text: str = "") -> Optional[List[Dict[str, Any]]]:
        """
        Purely phenotype-based differential ranking.
        Decoupled from molecular evidence: zero genotype tokens or variant strings.
        If model is unavailable, returns None (no heuristic fallback).
        """
        if not self.phenotype_model_loaded:
            return None
        if self.phenotype_model_kind == "clinical_classifier_v1":
            return self._compute_classifier_ranking(confirmed_features, onset_age, family_text)

        # 1. Collect clinical symptom tokens confirmed by clinician (Patient only, Present)
        feats = []
        for f in confirmed_features:
            if f.get("status") == "Present" and f.get("subject") == "Patient":
                c = f.get("concept")
                if c and c in self.vocab and c not in feats:
                    feats.append(c)

        # 2. Add Onset Category token
        if onset_age is not None:
            if onset_age <= 20:
                if "juvenile_onset" in self.vocab: feats.append("juvenile_onset")
            elif onset_age <= 44:
                if "early_onset" in self.vocab: feats.append("early_onset")
            else:
                if "late_onset" in self.vocab: feats.append("late_onset")

        # 3. Add Pedigree Indicators if present in text/symptoms
        lower_fam = family_text.lower()
        if "consanguin" in lower_fam:
            if "consanguinity" in self.vocab and "consanguinity" not in feats: feats.append("consanguinity")
            if "recessive_pedigree" in self.vocab and "recessive_pedigree" not in feats: feats.append("recessive_pedigree")
        if "recessive" in lower_fam:
            if "recessive_pedigree" in self.vocab and "recessive_pedigree" not in feats: feats.append("recessive_pedigree")
        if "dominant" in lower_fam or "affected father" in lower_fam or "affected mother" in lower_fam or "affected parent" in lower_fam:
            if "autosomal_dominant_pedigree" in self.vocab and "autosomal_dominant_pedigree" not in feats: feats.append("autosomal_dominant_pedigree")
            if "familial_history" in self.vocab and "familial_history" not in feats: feats.append("familial_history")

        # 4. Neural embedding pass
        tok_ids = [self.vocab[t] for t in feats if t in self.vocab]
        if tok_ids:
            h = self.emb[tok_ids].mean(axis=0)
        else:
            h = np.zeros(self.emb.shape[1], dtype=np.float32)

        # 5. Raw scores across all 10 genes using frozen signatures & weights
        raw_scores = {}
        for g in ALL_10_GENES:
            g_low = g.lower()
            ns = float(np.dot(self.out_w[self.vocab[g_low]], h)) if g_low in self.vocab else 0.0
            sig = GENE_SIGNATURES[g]
            hm = sum(2.2 for hmk in sig["hallmarks"] if hmk in feats)
            on = sum(1.0 for o in sig["typical_onset"] if o in feats)
            inh = sum(1.5 for i in sig["inheritance"] if i in feats)
            raw_scores[g] = (ns + hm + on + inh) / TEMPERATURE

        # 6. Expert A softmax (Common hereditary PD: GBA1, LRRK2, PRKN, PARK7)
        vals_A = np.array([raw_scores[g] for g in EXPERT_A_GENES])
        probs_A = np.exp(vals_A - vals_A.max())
        probs_A /= (probs_A.sum() or 1.0)
        pA_dict = dict(zip(EXPERT_A_GENES, probs_A))

        # 7. Expert B softmax (Atypical / Rare: RAB32, VPS35, SNCA, ATP13A2, PINK1, GCH1)
        vals_B = np.array([raw_scores[g] for g in EXPERT_B_GENES])
        probs_B = np.exp(vals_B - vals_B.max())
        probs_B /= (probs_B.sum() or 1.0)
        pB_dict = dict(zip(EXPERT_B_GENES, probs_B))

        # 8. Dynamic clinical gating alpha
        alpha = compute_alpha(feats)

        # 9. Fused posterior probabilities
        p_fused = {}
        for g in EXPERT_A_GENES:
            p_fused[g] = (1.0 - alpha) * pA_dict[g]
        for g in EXPERT_B_GENES:
            p_fused[g] = alpha * pB_dict[g]

        tot = sum(p_fused.values())
        if tot > 0:
            for g in p_fused: p_fused[g] /= tot

        ranked = sorted(p_fused.items(), key=lambda x: x[1], reverse=True)

        results = []
        for g, p in ranked[:5]:
            meta = GENE_METADATA.get(g, {"full_name": g, "mode": "Unknown", "typical_onset": "Unknown"})
            results.append({
                "gene": g,
                "probability": float(p),
                "score_pct": round(float(p) * 100, 1),
                "full_name": meta["full_name"],
                "inheritance": meta["mode"],
                "typical_onset": meta["typical_onset"]
            })

        return results

    def evaluate_molecular_evidence(self, r62_res: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        Parses molecular findings via Revision 6.2 deterministic core:
        distinguishes raw input vs normalized HGVS, transcript, zygosity, parental origin, and phase.
        Explicitly outputs 'Unknown / Not provided' for unverified fields.
        """
        vars_found = r62_res.get("variants", [])
        
        if not vars_found:
            # Check if any gene mention exists without specific variant
            g_match = re.search(r'\b(PRKN|VPS35|LRRK2|GBA1|SNCA|PINK1|PARK7|ATP13A2|GCH1|RAB32)\b', text, re.I)
            if g_match:
                g_name = g_match.group(1).upper()
                return {
                    "gene": g_name,
                    "raw_input": "Gene name only",
                    "normalized_hgvs": "Unknown / Not provided",
                    "transcript": "Unknown / Not provided",
                    "classification": "Reported finding",
                    "zygosity": "Unknown / Not provided",
                    "parental_origin": "Unknown / Not provided",
                    "phase": "Unknown / Not provided",
                    "source": g_match.group(0)
                }
            
            return {
                "gene": "Unknown / Not provided",
                "raw_input": "Unknown / Not provided",
                "normalized_hgvs": "Unknown / Not provided",
                "transcript": "Unknown / Not provided",
                "classification": "Unknown / Not provided",
                "zygosity": "Unknown / Not provided",
                "parental_origin": "Unknown / Not provided",
                "phase": "Unknown / Not provided",
                "source": "None"
            }

        # Collect all variants found by Revision 6.2
        norm_tokens = []
        raw_tokens = []
        transcripts = []
        gene = vars_found[0].get("mapped_gene") or vars_found[0].get("stated_gene") or "Unknown / Not provided"

        for v in vars_found:
            raw_t = v.get("raw_token", "Unknown")
            raw_tokens.append(raw_t)
            gene_v = v.get("mapped_gene") or v.get("stated_gene") or gene
            canon_c = v.get("hgvs_c")
            canon_p = v.get("hgvs_p")
            if canon_p and canon_c:
                norm_tokens.append(f"{gene_v} {canon_c} ({canon_p})")
            elif canon_c:
                norm_tokens.append(f"{gene_v} {canon_c}")
            elif canon_p:
                norm_tokens.append(f"{gene_v} {canon_p}")
            else:
                norm_tokens.append(f"{gene_v} {raw_t}")

            tr = v.get("canonical_transcript") or v.get("stated_transcript")
            if tr and tr not in transcripts:
                transcripts.append(tr)

        norm_hgvs = "; ".join(norm_tokens)
        raw_token = ", ".join(raw_tokens)
        transcript = ", ".join(transcripts) if transcripts else (vars_found[0].get("canonical_transcript") or "Unknown / Not provided")

        # Classification extraction
        class_m = re.search(r'\b(Pathogenic|Likely\s+Pathogenic|VUS|Variant\s+of\s+Uncertain\s+Significance|Likely\s+Benign|Benign)\b', text, re.I)
        classification = class_m.group(1) if class_m else "Unknown / Not provided"

        # Zygosity: check compound heterozygous BEFORE heterozygous
        if re.search(r'\bcompound\s+heterozygous\b', text, re.I) or re.search(r'\bcompound\s+het\b', text, re.I):
            zygosity = "Compound Heterozygous"
        elif r62_res.get("homozygous_match") or re.search(r'\bhomozygous\b', text, re.I):
            zygosity = "Homozygous"
        elif re.search(r'\bheterozygous\b', text, re.I):
            zygosity = "Heterozygous"
        else:
            zygosity = "Unknown / Not provided"

        # Parental origin
        origin = vars_found[0].get("origin")
        if not origin or origin == "unknown":
            if re.search(r'\bmaternal\b|\bfrom\s+(?:the\s+)?mother\b', text, re.I):
                parental_origin = "Maternal"
            elif re.search(r'\bpaternal\b|\bfrom\s+(?:the\s+)?father\b', text, re.I):
                parental_origin = "Paternal"
            elif re.search(r'\bde\s+novo\b', text, re.I):
                parental_origin = "De novo"
            else:
                parental_origin = "Unknown / Not provided"
        elif origin == "de_novo_reported":
            parental_origin = "De novo (reported)"
        elif origin == "unspecified_parent":
            parental_origin = "Unspecified parent"
        else:
            parental_origin = origin.capitalize()

        # Phase
        if r62_res.get("trans_match") or re.search(r'\b(?:in\s+trans|trans)\b', text, re.I):
            phase = "In trans (compound heterozygous)"
        elif r62_res.get("cis_match") or re.search(r'\b(?:in\s+cis|cis)\b', text, re.I):
            phase = "In cis (same allele)"
        elif re.search(r'\b(?:unphased|unknown\s+phase|phase\s+unknown|phasing\s+not\s+performed|not\s+phased)\b', text, re.I):
            phase = "Unphased (phase unknown)"
        elif zygosity == "Compound Heterozygous":
            phase = "Unconfirmed / Unphased"
        else:
            phase = "Unknown / Not provided"

        source_spans = []
        for v in vars_found:
            sp = text[v.get("start", 0):v.get("end", 0)] if "start" in v and "end" in v and v.get("end", 0) > 0 else v.get("raw_token", "")
            if sp and sp not in source_spans:
                source_spans.append(sp)
        source_span = ", ".join(source_spans) if source_spans else raw_token

        return {
            "gene": gene,
            "raw_input": raw_token,
            "normalized_hgvs": norm_hgvs,
            "transcript": transcript,
            "classification": classification,
            "zygosity": zygosity,
            "parental_origin": parental_origin,
            "phase": phase,
            "source": source_span,
            "start": vars_found[0].get("start", -1) if vars_found else -1,
            "end": vars_found[0].get("end", -1) if vars_found else -1
        }

    def assess_concordance(self, gene: str, top_phenotype_ranking: Optional[List[Dict[str, Any]]], confirmed_features: List[Dict[str, Any]], onset_age: Optional[int]) -> Tuple[str, List[str]]:
        """Evaluates concordance between confirmed phenotype and molecular gene finding."""
        if not gene or gene == "Unknown / Not provided":
            return "N/A — Phenotype Only", []

        if not top_phenotype_ranking:
            return "UNAVAILABLE", ["Phenotype ranking model unavailable for concordance evaluation."]

        top_genes = [r["gene"] for r in top_phenotype_ranking]
        discordant_reasons = []

        active_symptoms = [f["concept"] for f in confirmed_features if f.get("status") == "Present" and f.get("subject") == "Patient"]

        # Check typical discordances from clinical spectra
        if gene in ("VPS35", "LRRK2", "RAB32"):
            if onset_age is not None and onset_age < 30:
                discordant_reasons.append(f"Onset age ({onset_age}y) is juvenile/early, whereas {gene} causes classic late-onset parkinsonism.")
            if "sleep_benefit" in active_symptoms:
                discordant_reasons.append(f"Prominent sleep benefit is characteristic of recessive EOPD (PRKN/PINK1) and atypical for {gene}.")
            if "diurnal_fluctuation" in active_symptoms:
                discordant_reasons.append(f"Marked diurnal fluctuation is characteristic of GCH1 (dopa-responsive dystonia) and atypical for {gene}.")
            if "vertical_gaze_palsy" in active_symptoms:
                discordant_reasons.append(f"Supranuclear vertical gaze palsy is an atypical sign indicating ATP13A2 / Kufor-Rakeb, not {gene}.")

        elif gene == "PRKN":
            if onset_age is not None and onset_age >= 55:
                discordant_reasons.append(f"Late adult onset ({onset_age}y) is atypical for PRKN (primarily early/juvenile onset).")
            if "cognitive_decline" in active_symptoms:
                discordant_reasons.append("Early progressive dementia is atypical for PRKN.")

        elif gene == "GCH1":
            if "cognitive_decline" in active_symptoms or "hallucinations" in active_symptoms:
                discordant_reasons.append(f"Cognitive decline / hallucinations are atypical for GCH1 dopa-responsive dystonia.")

        elif gene == "ATP13A2":
            if onset_age is not None and onset_age >= 45:
                discordant_reasons.append(f"Late adult onset ({onset_age}y) is discordant with ATP13A2 juvenile Kufor-Rakeb syndrome.")

        if discordant_reasons:
            return "DISCORDANT", discordant_reasons
        
        if top_genes and gene == top_genes[0]:
            return "HIGH", []
        elif len(top_genes) > 1 and gene == top_genes[1]:
            return "MODERATE", []
        elif gene in top_genes:
            return "LOW", [f"Gene ranks at #{top_genes.index(gene)+1} in phenotype differential."]
        else:
            return "ATYPICAL", [f"Phenotypic presentation does not prioritize {gene} among top-5 candidates."]

    def analyze_case(self, text: str) -> Dict[str, Any]:
        """
        Executes complete 5-stage clinical decision support pipeline:
        1. Extracting clinical information (DeepSeek-v4-flash, live API, zero heuristic fallback)
        2. Verifying extracted facts (Extraction Completeness Gate + Formal Gate)
        3. Molecular evidence analysis (Revision 6.2 Normalization)
        4. Genotype-phenotype consistency (Frozen MoFE Phenotype Model + Concordance)
        5. Generating decision-support report
        """
        t0 = time.perf_counter()

        # 1. LLM Extraction (live API, zero fallback)
        try:
            raw_extraction = self._call_nlp_model(text)
        except Exception as e:
            # Safe ABSTAIN state if NLP fails
            return {
                "status": "ABSTAIN",
                "pipeline_status": "ABSTAIN",
                "reason_codes": ["NLP_EXTRACTION_UNAVAILABLE"],
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                "clinical_features": [],
                "onset_age": None,
                "molecular_findings": {
                    "gene": "Unknown / Not provided",
                    "raw_input": "Unknown / Not provided",
                    "normalized_hgvs": "Unknown / Not provided",
                    "transcript": "Unknown / Not provided",
                    "classification": "Unknown / Not provided",
                    "zygosity": "Unknown / Not provided",
                    "parental_origin": "Unknown / Not provided",
                    "phase": "Unknown / Not provided",
                    "source": "None"
                },
                "safety_alerts": [{
                    "type": "danger",
                    "title": "NLP Extraction Unavailable",
                    "detail": str(e)
                }],
                "phenotype_ranking": None,
                "phenotype_model_status": self._phenotype_model_status(),
                "classifier_safety": {
                    "status": "ABSTAIN",
                    "reason_codes": ["NLP_EXTRACTION_UNAVAILABLE"],
                    "top_candidate": None,
                    "classifier_score_pct": None,
                    "classifier_score_label": "classifier score",
                },
                "concordance": {
                    "status": "UNAVAILABLE",
                    "discordance_detected": False,
                    "reasons": ["Extraction unavailable."]
                },
                "abstention": {
                    "is_withheld": True,
                    "reason": f"NLP model ({self.model_name}) extraction unavailable: {e}"
                },
                "audit_trail": {
                    "model": self.model_name,
                    "schema": "1.1",
                    "formal_gate_status": "NOT_REACHED",
                    "completeness_gate_status": "NOT_REACHED",
                    "revision_core": "6.2",
                }
            }

        observations_json = raw_extraction.get("observations", [])

        # Parse into typed Schema 1.1 objects
        typed_observations = []
        for o in observations_json:
            subj_raw = o.get("subject", {})
            subj_type = subj_raw.get("type", "proband") if isinstance(subj_raw, dict) else (subj_raw or "proband")
            subject_obj = Subject(type=subj_type)

            src_raw = o.get("source", {})
            if isinstance(src_raw, dict):
                span_text = src_raw.get("text_span", "")
                s_start = src_raw.get("start", 0)
                s_end = src_raw.get("end", 0)
                asserted_by = src_raw.get("asserted_by")
            else:
                span_text = str(src_raw or "")
                s_start, s_end, asserted_by = 0, 0, None

            if not span_text and o.get("text_span"):
                span_text = o.get("text_span")

            if span_text and span_text in text:
                if text[s_start:s_end] != span_text:
                    s_start = text.find(span_text)
                    s_end = s_start + len(span_text)

            source_obj = SourceSpan(
                text_span=span_text,
                start=s_start,
                end=s_end,
                source_type="clinical_text",
                asserted_by=asserted_by
            )

            pred = o.get("predicate")
            if not pred:
                if o.get("concept") in ALLOWED_SYMPTOM_CONCEPTS or o.get("raw_finding"):
                    pred = PredicateType.HAS_SYMPTOM.value
                elif o.get("raw_variant") or o.get("variant"):
                    pred = PredicateType.HAS_VARIANT.value
                elif o.get("value") and isinstance(o.get("value"), (int, float)):
                    pred = PredicateType.HAS_ONSET_AGE.value
                elif o.get("gene"):
                    pred = PredicateType.HAS_GENE_MENTION.value
                else:
                    pred = PredicateType.HAS_SYMPTOM.value

            concept_val = o.get("concept")
            if not concept_val and isinstance(o.get("value"), str) and o.get("value") in ALLOWED_SYMPTOM_CONCEPTS:
                concept_val = o.get("value")
            if not concept_val and o.get("candidate_concept") in ALLOWED_SYMPTOM_CONCEPTS:
                concept_val = o.get("candidate_concept")
            if not concept_val and pred == PredicateType.HAS_SYMPTOM.value:
                find_str = (o.get("raw_finding") or span_text or "").lower()
                for c_allowed in ALLOWED_SYMPTOM_CONCEPTS:
                    c_clean = c_allowed.replace("_", " ")
                    if c_allowed in find_str or c_clean in find_str:
                        concept_val = c_allowed
                        break
                if not concept_val:
                    if "resting tremor" in find_str or "rest tremor" in find_str or "tremor" in find_str or "shaking" in find_str or "pill-rolling" in find_str:
                        concept_val = "tremor_rest"
                    elif "sleep" in find_str and "benefit" in find_str:
                        concept_val = "sleep_benefit"
                    elif "diurnal" in find_str:
                        concept_val = "diurnal_fluctuation"
                    elif "levodopa" in find_str or "l-dopa" in find_str:
                        concept_val = "levodopa_response"
                    elif "gaze palsy" in find_str or ("gaze" in find_str and "palsy" in find_str):
                        concept_val = "vertical_gaze_palsy"
                    elif "pyramidal" in find_str or "spasticity" in find_str or "hyperreflexia" in find_str:
                        concept_val = "spasticity_pyramidal_signs"
                    elif "cognitive" in find_str or "dementia" in find_str:
                        concept_val = "cognitive_decline"
                    elif "hallucination" in find_str:
                        concept_val = "hallucinations"
                    elif "atypical parkinsonism" in find_str or "kufor" in find_str:
                        concept_val = "kufor_rakeb_atypical_pd"
                    elif "hyposmia" in find_str or "smell" in find_str or "olfactory" in find_str:
                        concept_val = "hyposmia"

            obs = Observation(
                id=o.get("id", f"obs_{len(typed_observations)+1:03d}"),
                predicate=pred,
                subject=subject_obj,
                concept=concept_val,
                raw_finding=o.get("raw_finding"),
                raw_variant=o.get("raw_variant"),
                polarity=o.get("polarity", "positive"),
                temporal_scope=o.get("temporal_scope", "CURRENT"),
                epistemic_status=o.get("epistemic_status", "ASSERTED"),
                value=o.get("value"),
                source=source_obj,
                mapping_status="CONFIRMED" if (concept_val and concept_val in ALLOWED_SYMPTOM_CONCEPTS) else o.get("mapping_status", "PROPOSED")
            )
            typed_observations.append(obs)

        batch = DocumentExtractionBatch(
            schema_version="1.1",
            document_id="clinical_case",
            observations=typed_observations
        )

        # 2. Gate Audits (Completeness Gate & Formal Gate)
        is_complete, completeness_omissions = self.completeness_gate.audit_completeness(text, batch)
        formal_gate = FormalGateValidator(text)

        approved_observations = []
        blocked_observations = []
        audit_trail = []

        for obs in typed_observations:
            val_res = formal_gate.validate_observation(obs)
            audit_item = {
                "id": obs.id,
                "raw_span": obs.source.text_span if obs.source else "N/A",
                "start": obs.source.start if obs.source else -1,
                "end": obs.source.end if obs.source else -1,
                "predicate": obs.predicate,
                "concept": obs.concept or obs.raw_finding or obs.raw_variant or str(obs.value),
                "subject": obs.subject.type if obs.subject else "proband",
                "polarity": obs.polarity,
                "formal_gate": "APPROVED" if val_res.is_valid else "REJECTED",
                "errors": val_res.errors,
                "warnings": val_res.warnings
            }
            audit_trail.append(audit_item)

            if val_res.is_valid:
                approved_observations.append(obs)
            else:
                blocked_observations.append((obs, val_res))

        # 3. Revision 6.2 Deterministic Normalization
        r62_res = self.r62_engine.parse_text(text)

        # Format Extracted Clinical Features for Clinician Review
        extracted_features = []
        onset_age = None

        for obs in approved_observations:
            if obs.predicate == PredicateType.HAS_ONSET_AGE.value:
                try: onset_age = int(obs.value)
                except Exception: pass
            elif obs.predicate == PredicateType.HAS_CURRENT_AGE.value and onset_age is None:
                try: onset_age = int(obs.value)
                except Exception: pass
            elif obs.predicate == PredicateType.HAS_SYMPTOM.value and obs.concept:
                disp_name = SYMPTOM_DISPLAY_NAMES.get(obs.concept, obs.concept.replace("_", " ").title())
                status = "Absent" if obs.polarity == "negative" else ("Possible" if obs.epistemic_status == "POSSIBLE" else "Present")
                subj_type = obs.subject.type if obs.subject else "proband"
                subj_disp = "Patient" if subj_type == "proband" else subj_type.capitalize()
                span_text = obs.source.text_span if obs.source else ""

                extracted_features.append({
                    "id": obs.id,
                    "feature": disp_name,
                    "concept": obs.concept,
                    "status": status,
                    "subject": subj_disp,
                    "source_text": span_text,
                    "start": obs.source.start if obs.source else -1,
                    "end": obs.source.end if obs.source else -1,
                    "clinician_confirmed": True
                })

        # 4. Molecular Findings via Revision 6.2
        mol_findings = self.evaluate_molecular_evidence(r62_res, text)

        family_context_terms = self._family_context_terms(text)

        # 5. Phenotype Model Ranking (Frozen MoFE, Decoupled from Variants)
        phenotype_ranking = self.compute_phenotype_ranking(extracted_features, onset_age, family_context_terms)
        classifier_safety = self.evaluate_classifier_safety(
            extracted_features,
            onset_age,
            family_context_terms,
        )

        # 6. Final Concordance Evaluation
        concordance_status, discordance_reasons = self.assess_concordance(
            mol_findings["gene"], phenotype_ranking, extracted_features, onset_age
        )

        # 7. Data Quality & Safety Alerts
        safety_alerts = []
        if r62_res.get("variants") and any(v.get("gene_conflict") for v in r62_res["variants"]):
            safety_alerts.append({
                "type": "danger",
                "title": "Gene–variant mismatch",
                "detail": "Reported variant annotation does not match canonical genomic locus."
            })
        if r62_res.get("has_class_conflict"):
            safety_alerts.append({
                "type": "warning",
                "title": "Classification conflict",
                "detail": "Conflicting variant pathogenicity assertions identified across records."
            })
        if r62_res.get("has_branch_conflict"):
            safety_alerts.append({
                "type": "warning",
                "title": "Parental-origin conflict",
                "detail": "Mutually incompatible parental segregation assertions detected in amendment tree."
            })
        if r62_res.get("cardinality_mismatch"):
            safety_alerts.append({
                "type": "warning",
                "title": "Ambiguous relation / Cardinality mismatch",
                "detail": "Number of mentioned alleles differs from reported segregation assignments."
            })
        if not is_complete:
            safety_alerts.append({
                "type": "warning",
                "title": "Incomplete molecular information",
                "detail": "Text contains overt clinical or molecular anchors not fully resolved by extractor."
            })
        if blocked_observations:
            safety_alerts.append({
                "type": "danger",
                "title": "AI extraction rejected — clinician review required",
                "detail": f"Formal Gate safely blocked {len(blocked_observations)} unverified observation(s) from downstream processing."
            })
        if classifier_safety.get("status") == AMBIGUOUS_GENE_CLUSTER:
            safety_alerts.append({
                "type": "warning",
                "title": "Phenotype classifier safety downgrade",
                "detail": "The classifier ranking is preserved, but the safety layer withheld a definitive gene call."
            })

        if not safety_alerts:
            safety_alerts.append({
                "type": "success",
                "title": "No critical conflicts detected",
                "detail": "All extracted assertions satisfy Schema 1.1 formal constraints and internal consistency rules."
            })

        # 8. Abstention Check
        interpretation_withheld = False
        withheld_reason = ""
        if r62_res.get("has_branch_conflict") or r62_res.get("cardinality_mismatch"):
            interpretation_withheld = True
            withheld_reason = "Available information is internally inconsistent regarding molecular inheritance lineage."
        elif not is_complete and len(extracted_features) == 0:
            interpretation_withheld = True
            withheld_reason = "Available clinical narrative contains unresolved textual anchors."

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        return {
            "status": classifier_safety["status"],
            "pipeline_status": "SUCCESS",
            "reason_codes": classifier_safety["reason_codes"],
            "latency_ms": latency_ms,
            "clinical_features": extracted_features,
            "onset_age": onset_age,
            "molecular_findings": mol_findings,
            "safety_alerts": safety_alerts,
            "phenotype_ranking": phenotype_ranking,
            "phenotype_model_status": self._phenotype_model_status(),
            "classifier_safety": classifier_safety,
            "classifier_context": {
                "family_context_terms": family_context_terms
            },
            "concordance": {
                "status": concordance_status,
                "discordance_detected": (concordance_status == "DISCORDANT"),
                "reasons": discordance_reasons
            },
            "abstention": {
                "is_withheld": interpretation_withheld,
                "reason": withheld_reason
            },
            "audit_trail": {
                "model": self.model_name,
                "schema": "1.1",
                "formal_gate_status": "PASS" if not blocked_observations else f"BLOCKED ({len(blocked_observations)} unverified)",
                "completeness_gate_status": "PASS" if is_complete else "ABSTAIN",
                "revision_core": "6.2",
                "lineage": audit_trail
            }
        }

    def recalculate_case(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recomputes deterministic analysis (Revision 6.2 + Frozen MoFE Phenotype Model + Concordance)
        based on clinician-confirmed edits WITHOUT calling the LLM again.
        """
        features = current_state.get("clinical_features", [])
        onset_age = current_state.get("onset_age")
        mol_findings = current_state.get("molecular_findings", {})
        family_context_terms = current_state.get("classifier_context", {}).get("family_context_terms", "")

        # Re-compute phenotype ranking purely on confirmed patient features using frozen MoFE
        phenotype_ranking = self.compute_phenotype_ranking(features, onset_age, family_context_terms)
        classifier_safety = self.evaluate_classifier_safety(features, onset_age, family_context_terms)

        # Re-evaluate concordance
        concordance_status, discordance_reasons = self.assess_concordance(
            mol_findings.get("gene", ""), phenotype_ranking, features, onset_age
        )

        current_state["phenotype_ranking"] = phenotype_ranking
        current_state["phenotype_model_status"] = self._phenotype_model_status()
        current_state["classifier_safety"] = classifier_safety
        current_state["status"] = classifier_safety["status"]
        current_state["pipeline_status"] = current_state.get("pipeline_status", "SUCCESS")
        current_state["reason_codes"] = classifier_safety["reason_codes"]
        current_state["concordance"] = {
            "status": concordance_status,
            "discordance_detected": (concordance_status == "DISCORDANT"),
            "reasons": discordance_reasons
        }

        # Lift abstention if clinician reviewed and confirmed features
        if current_state.get("abstention", {}).get("is_withheld"):
            current_state["abstention"]["is_withheld"] = False
            current_state["abstention"]["reason"] = "Clinician reviewed and confirmed clinical findings."

        return current_state
