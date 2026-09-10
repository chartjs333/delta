# Postmortem: Silent PRKN Tokenizer Contamination in Clinical Feature Pipeline

**Date:** 2026-09-05  
**Severity:** High (Clinical Differential Diagnosis Distortion)  
**Status:** Resolved & Permanently Guarded with Regression Test  
**Impacted Components:** `deploy_mixed_nodes_html.py`, `clinical_copilot_mixed_nodes.html`, upstream clinical entity extractor  
**Reported By:** External Clinical Reviewer  

---

## 1. Executive Summary

During clinical evaluation of the Federated 10-Gene Copilot (Version 2), review identified that `PRKN` was systematically injected as a top candidate across non-PRKN cases. Most notably, in a classic textbook juvenile Kufor-Rakeb presentation (`ATP13A2` mutation with vertical supranuclear gaze palsy, pyramidal spasticity, and dementia), the model prioritized `PRKN` at **56.4%** while relegating `ATP13A2` to **5.1%** (#5 rank).

Investigation of the token traces revealed that the extracted representation for non-PRKN cases contained `prkn` despite the original clinical prompt containing zero mentions of the PRKN gene or parkin protein.

---

## 2. Root Cause Analysis

### A. Substring Tokenizer Defect
In the JavaScript and Python prototype feature extractors, symptom and gene synonym mapping was performed via substring containment:

```javascript
// DEFECTIVE IMPLEMENTATION (Pre-Revision 2)
const SYNONYMS = {
    ...
    "prkn": "prkn",
    "parkin": "prkn", // <-- Intended for "parkin protein", but matched inside "parkinson" and "parkinsonism"!
    ...
};

for (const [phrase, tok] of Object.entries(SYNONYMS)) {
    if (lower.includes(phrase)) { // <-- "parkinsonism".includes("parkin") === true!
        tokens.push(tok);
    }
}
```

Because virtually every movement disorder query contains the words *"parkinson"* or *"parkinsonism"*, the substring check `"parkin"` unconditionally evaluated to `true`. Consequently, `prkn` was silently added to the extracted token list for **100% of Parkinson-related clinical notes**.

### B. Compounding Logit Bonus in Candidate Prioritization
The scoring pipeline included a heuristic bonus for candidate gene-specific tokens:

```javascript
for (const t of tokens) {
    if (geneSpecificTokens[g].includes(t)) bonus += 2.0;
}
```

Because `prkn` was falsely present in `tokens`, `PRKN` automatically received an unearned **+2.0 logit boost** in every single case. Coupled with `PRKN`'s larger sample representation in MDSGene (1,502 records vs 49 for `ATP13A2` and 84 for `RAB32`), this transformed `PRKN` into an artificial **attractor class**, suppressing true rare-disease candidates.

---

## 3. Corrective Actions

### A. Word-Boundary Regex with Negative Lookahead
The substring search was replaced with a strict word-boundary regular expression that explicitly forbids alphanumeric continuations:

```javascript
// CORRECTED IMPLEMENTATION
const REGEX_RULES = [
    // Matches "prkn" or standalone "parkin", but NOT "parkinson" or "parkinsonism"
    [/\b(?:prkn|parkin(?!\w))\b/i, "prkn", "gene"],
    [/\b(?:atp13a2)\b/i, "atp13a2", "gene"],
    [/\b(?:gba1|gba(?!\w))\b/i, "gba1", "gene"],
    ...
];
```

### B. Stratified Benchmark Architecture
To prevent conflation of different clinical tasks, evaluation was split into 3 strictly disjoint strata:
1. **Stratum 1 (Phenotype-Only)**: Symptoms + Age/Onset only (Strictly NO pedigree/inheritance, NO gene/variant names).
2. **Stratum 2 (Phenotype + Pedigree)**: Symptoms + Age/Onset + Inheritance (`hom`, `het`).
3. **Stratum 3 (Genotype-Aware)**: Symptoms + Age/Onset + Inheritance + Confirmed Gene/Variant.

### C. UI Semantic Decoupling
The output was restructured into 4 separate, non-overlapping cards:
1. *Extracted Patient Findings* (only tokens recognized in input);
2. *Candidate Gene Prioritization* (calibrated differential scores);
3. *Model-Associated Supporting Phenotypes* (symptoms only, no foreign variant names);
4. *Representative Variants from Candidate-Gene Corpus* (labeled explicitly as literature reference knowledge).

---

## 4. Regression Test Suite

A mandatory regression test was codified in `tests/test_tokenizer_contamination.py` and `d:\delta\test_3strata_benchmark.py`:

```python
def test_zero_prkn_contamination_in_non_prkn_cases():
    # Evaluates 18 non-PRKN challenge cases across 9 distinct genes
    for case in NON_PRKN_CASES:
        tokens = extract_features_for_stratum(case["text"], stratum=1)
        assert "prkn" not in tokens, f"PRKN contamination detected in case: {case['id']} ({case['gene']})"
```

**Verification Outcome:**
* Non-PRKN Contamination Rate: **`0/18 (0.0%)`**
* `ATP13A2` rank recovered from **#5 (5.1%)** $\rightarrow$ **#1 (97.8% calibrated score)** in classic Kufor-Rakeb presentation.

---

## 5. Lessons Learned for Clinical AI

1. **Explainable Token Traces are a Critical Safety Layer**:
   Without exposing raw extracted tokens in the UI and test suites, this bug would have remained disguised as "acceptable probabilistic error" (since `PRKN` is a legitimate Parkinson gene). The token trace immediately exposed the exact mechanistic failure.
2. **Never Use Substring Matching for Biomedical Acronyms**:
   Short gene symbols (`PARK`, `GBA`, `DJ1`, `PINK`, `PRKN`) frequently overlap with medical terminology (`parkinsonism`, `pink eye`, etc.). Word boundaries and semantic negative lookaheads are mandatory.
3. **Prioritization vs Calibration**:
   Raw softmax over unbalanced class logits must not be presented to clinicians as true "probabilities" without formal calibration (temperature scaling, reliability diagrams, Brier score, ECE).
