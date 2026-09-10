# ADR-0011: Hybrid NLP Semantic Boundary — Constrained SLM Extractor and Deterministic State Machine

**Status**: Accepted  
**Date**: 2026-09-06  
**Formal impact**: `REFINEMENT_ONLY` (Decoupled extraction and diagnostic gating under Constitution and ADR-0010)

---

## 1. Context

In Campaigns Blind-100 v1, v2, and v3, the symbolic NLP layer for clinical neurogenetics progressed through Revisions 6.0, 6.1, and 6.2.
* **Deterministic Core Strengths:** Molecular normalization (100%), canonical HGVS/transcript mapping (100%), multi-transcript alignment, intra- and inter-source conflict detection (99%), and document revision DAG evaluation achieved complete stability.
* **Empirical Natural Language Ceiling:** In Blind-100 v3 (realistic clinical narratives), failures clustered entirely around natural language discourse phenomena:
  1. Contrastive subject experiencer coordination (`proband's sister, not the proband, experienced hallucinations`);
  2. Subject-level negation coordination (`Neither patient nor spouse reports hallucinations...`);
  3. Positive semantic paraphrases of medical health (`cognition remains intact according to family`);
  4. Clinical descriptive idioms (`dragging of the left foot`, `intermittent foot posturing`, `before school age`);
  5. Unlinked discourse aggregates (`without linking identifiers to parental origin`).

Expanding rule-based regular expressions (Revision 6.3) creates diminishing returns and brittle lexical coupling. Conversely, allowing an unconstrained Large Language Model (LLM) to make clinical diagnoses or normalize variants introduces catastrophic hallucination risk, unverified biallelic claims, and loss of provenance.

---

## 2. Architectural Decision

We officially freeze the deterministic rule-based text parser at **Revision 6.2** and establish the **Hybrid Prototype H1 Architecture**.

The system is decomposed into a strict five-stage pipeline:

```text
[FREE TEXT CLINICAL NARRATIVE]
             │
             ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 1: Constrained Semantic Extractor (SLM)          │
│ • Emits atomic, typed Observation objects.             │
│ • Strictly forbidden from diagnostic/variant inference.│
└────────────────────────────┬───────────────────────────┘
                             │ (Typed Observation Batch)
                             ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2: Formal Verification Gate (Deterministic)      │
│ • Span ground-truth check: source_span ∈ text.         │
│ • Concept ontology containment; no invented entities.  │
│ • Rule: NO SOURCE SUPPORT → DROP / ABSTAIN.            │
└────────────────────────────┬───────────────────────────┘
                             │ (Validated Observations)
                             ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 3: Canonical Molecular Normalization             │
│ • Deterministic mapping: raw token → HGVS c. / p.      │
│ • Uses CANONICAL_CATALOG & SYNONYMS_MAP only.          │
└────────────────────────────┬───────────────────────────┘
                             │ (Canonical Molecular Records)
                             ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 4: Clinical State Machine & Audit DAG (Rev 6.2)  │
│ • Pedigree attribution (Proband vs Relatives).         │
│ • Document revision tree (Active vs Superseded).       │
│ • Phasing & Segregation (Cis / Trans / Unphased).      │
│ • Epistemic conflict detection & safety gate.          │
└────────────────────────────┬───────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [SAFETY CONFLICT / UNRESOLVED]     [UNAMBIGUOUS PHENOTYPE]
            │                                 │
            ▼                                 ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│ DIAGNOSTIC INFERENCE:     │     │ STAGE 5: Diagnostic Model │
│ BLOCKED / ABSTAIN         │     │ (Dual-Expert MoFE Rev 4/5)│
└───────────────────────────┘     └───────────────────────────┘
```

---

## 3. The Boundary Contract (Schema 1.0)

### 3.1 Observation Whitelist
Only the following predicates may cross from Stage 1 to Stage 2:
* `HAS_SYMPTOM`
* `HAS_NORMAL_FINDING`
* `HAS_VARIANT`
* `HAS_GENE_MENTION`
* `HAS_CLASSIFICATION_ASSERTION`
* `HAS_PARENTAL_ORIGIN`
* `HAS_ZYGOSITY`
* `HAS_PHASE_ASSERTION`
* `HAS_ONSET_AGE`
* `HAS_CURRENT_AGE`
* `HAS_TEMPORAL_ASSERTION`
* `DOCUMENT_SUPERSEDES`
* `DOCUMENT_CORRECTS`
* `DOCUMENT_QUOTES`
* `SOURCE_ASSERTS`
* `RELATION_UNRESOLVED`

### 3.2 Epistemic Status Enum
* `ASSERTED`: Direct factual assertion by author.
* `REPORTED`: Citation of external or patient report.
* `SUSPECTED`: Clinical hypothesis under consideration.
* `POSSIBLE`: Qualified possibility.
* `UNCERTAIN`: Explicit doubt or indeterminacy.
* `UNCONFIRMED`: Suspected but not verified by test.
* `QUOTED`: Quoting historical or secondary assertion.
* `SUPERSEDED`: Replaced by later amendment.
* `CONFLICTING`: Explicitly contradictory findings.

### 3.3 Temporal Scope Enum
* `CURRENT`: Currently present or actively evaluated.
* `HISTORICAL`: Past manifestation, antecedent event.
* `RESOLVED`: Previously present, now explicitly absent.
* `ONSET`: Manifestation present at initial disease onset.

### 3.4 Schema 1.1 Contract Refinements (H1.1)
Following Blind Semantic-100 v1 analysis, the boundary contract was refined to eliminate false rejections without weakening adversarial containment:
1. **Anaphoric Grounding:** Observations based on anaphora/ellipsis store both the local trigger span (`source_span`) and an explicit `antecedent_span`, validated against character offsets and verified for concept presence.
2. **Lexical vs Semantic Grounding Separation:** Qualitative discourse phrases (`became symptomatic`) require `raw_finding`, `candidate_concept`, and `mapping_status = "PROPOSED"`, preventing premature assignment of confirmed phenotype entities.
3. **Typed Temporal Relations:** Introduced structured `temporal_relation` object (`relation_type`: `BEFORE|AFTER|DURING|ONSET|RESOLVED|INTERVAL`, `anchor`: `motor_symptoms|diagnosis|visit|current_time`, `source_span`) replacing unbounded regex keywords.
4. **Experiencer Subject vs Relation Object Decoupling:** Molecular inheritance assertions keep `subject = "proband"` while declaring `relation_object = "mother"|"father"`, preventing false `SUBJECT_SPAN_MISMATCH` rejections on parental transmission phrases.
5. **Aggregated Classification Multisets:** Explicit `AGGREGATE_CLASSIFICATION_ASSERTION` with multiset `counts` (`{"pathogenic": 2, "vus": 1}`) and `assignment_status = "UNRESOLVED"`. Forbids auto-mapping counts to individual variant instances without formal relation links.

---

## 4. Invariants and Safety Constraints

1. **No Medical Inference by SLM:** The SLM cannot assert `diagnosis`, `causal_gene`, `compound_heterozygous_confirmed`, or `pathogenicity`.
2. **Raw vs Normalized Separation:** The SLM outputs only `raw_expression` (e.g. `"D620N"`). Normalization to `VPS35 p.Asp620Asn` is strictly executed by Stage 3.
3. **No Unanchored Entities (Containment Gate):** Every observation must contain `source_span` with exact `start` and `end` character offsets matching the input text. If `text[start:end] != source_span`, the observation is rejected.
4. **Confidence is Non-Decisional:** Confidence scores serve as audit metadata. Binary clinical gating is strictly based on discourse semantics, conflict state, and verification checks.
5. **Conflict Terminal Barrier:** Any unresolved safety-critical conflict (e.g., competing active report branches, unlinked biparental multiset mapping, gene-variant mismatch) sets `inference = BLOCKED`.

---

## 5. Implementation & Verification Audits

### 5.1 Historical Validation Audits
* **Milestone H1:** Prototype implementation of Schema 1.0, Formal Gate Validator, and 50 Semantic Extraction Benchmark Cases.
* **Milestone H1.1 (Contract Refinement):** Schema 1.1 implementation, eliminating false rejections on anaphoric grounding, temporal typing, and parental origin decoupling.

### 5.2 Blind Semantic-100 v2 Audit & Status Reclassification

An independent exam under Blind Semantic-100 v2 revealed the empirical limitations of template-matching extraction and uncovered 4 invariant escapes in the initial Formal Gate:

```text
H1.1 Blind Semantic-100 v2

Semantic extraction:       FAIL (1.2%)
Formal containment:        FAIL (73.3%)
Unsafe escapes:            4

Root cause:
• template-matching extractor
• incomplete formal invariants

Previous Regression-150:
RECLASSIFIED AS DEVELOPMENT/REGRESSION VALIDATION,
NOT GENERALIZATION EVIDENCE

Decision:
Replace template extractor with genuine semantic inference.
Strengthen Formal Gate before next blind campaign.
```

### 5.3 Architectural Countermeasures Implemented

1. **Formal Gate Hardening (4 Core Invariants):**
   * **Universal Provenance Grounding:** Every claimed `asserted_by` must have direct lexical grounding in the source text.
   * **Universal Subject Leakage:** Verifies attribution leakage for any subject pair $A \to B$ ($A \ne B$).
   * **Complete Phasing Invariants:**
     - `CIS` + opposite parental origins (`maternal` + `paternal`) $\to$ `CROSS_OBS_PHASING_CONFLICT`.
     - `TRANS` + same parental origin (`maternal` + `maternal` or `paternal` + `paternal`) $\to$ `CROSS_OBS_PHASING_CONFLICT`.
   * **Generalized Cardinality Invariant:** Textual variant count $N_{\text{text}} > N_{\text{extracted}}$ flags `CARDINALITY_INCONSISTENCY` / `INCOMPLETE_EXTRACTION` for any $N$.
   * **Verification:** Hardened gate achieved **15 / 15 (100.0%)** containment and **0 unsafe escapes** on the dedicated adversarial attack suite (`test_adversarial_gate_15.py`).

2. **Extraction Completeness Gate (`extraction_completeness_gate.py`):**
   * Prevents empty or partial batches from passing as safe successes.
   * Deterministically audits presence of textual anchors (HGVS tokens, known gene symbols, explicit ages, classification terms).
   * Missing anchors trigger `EXTRACTION_INCOMPLETE` $\to$ `ABSTAIN`.

3. **Provider-Independent Semantic Extractor Interface (`semantic_extractor_interface.py`):**
   * Establishes `SemanticExtractor(ABC)` decoupled from specific LLM vendors.
   * Implements strict Schema 1.1 JSON prompting (`LLMSemanticExtractor`) and dependency-based parsing (`GeneralizedRuleSemanticExtractor`).
   * Eliminates verbatim sentence comparisons (`if "exact phrase" in text`).

### 5.4 Milestone H1.2: Real Semantic Model Integration & Smoke Benchmark
To guarantee genuine semantic inference without hidden regex fallbacks, Milestone H1.2 established:
* `H12SemanticModelPipeline`: End-to-end orchestration connecting actual model inference $\to$ Schema 1.1 JSON parsing $\to$ Extraction Completeness Gate $\to$ Formal Verification Gate.
* **Strict Zero-Fallback Policy:** If the model returns invalid JSON or fails Schema 1.1 constraints, the case fails with `EXTRACTION_FAILURE` $\to$ `ABSTAIN`. No silent fallback to heuristic regex or string templates is permitted.
* **Comprehensive Audit Trail:** Every transaction records `extractor_type`, `model_id`, `schema_version`, `raw_model_output`, `parsed_observations`, `completeness_result`, and `formal_gate_result` in `h1_2_smoke_audit_log.json`.
* **15 Smoke Cases Validated:** 15/15 cases passed end-to-end through the complete pipeline with 0 unsafe escapes.

### 5.5 Freezing Protocol for H1 Blind Semantic-100 v3
Before commencing the true blind campaign, all 5 pipeline layers are simultaneously frozen:
1. **Model identity:** Frozen (`model_id`, inference temperature $T=0.0$).
2. **System Prompt:** Frozen (exact `SYSTEM_PROMPT_SCHEMA_1_1` instructions).
3. **Contract Schema:** Frozen (Schema 1.1 enums and dataclasses).
4. **Extraction Completeness Gate:** Frozen (`extraction_completeness_gate.py`).
5. **Formal Verification Gate:** Frozen (`formal_gate_validator.py`).

No prompt tweaks or gate adjustments are permitted once the Blind-100 v3 test suite begins execution. Generalization will be measured on raw, unseen clinical texts.



