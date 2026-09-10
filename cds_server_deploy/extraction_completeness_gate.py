import re
from typing import List, Dict, Any, Tuple
from h1_contract import (
    DocumentExtractionBatch,
    Observation,
    PredicateType
)

# ==============================================================================
# H1.1 EXTRACTION COMPLETENESS GATE
# Guards against silent omission / false negative empty batches
# Architecture: FREE TEXT -> SLM -> COMPLETENESS CHECK -> FORMAL GATE
# ==============================================================================

class ExtractionCompletenessGate:
    """
    Deterministic pre-gate auditor ensuring that explicit textual clinical anchors
    are not silently omitted by the semantic extractor.
    
    If text contains overt anchor tokens (HGVS mutations, known genes, explicit ages,
    classification terms) but the candidate batch fails to extract corresponding
    observations, the gate halts downstream processing with EXTRACTION_INCOMPLETE -> ABSTAIN.
    """
    KNOWN_GENES = {
        "PRKN", "PARK2", "LRRK2", "VPS35", "GBA", "GBA1",
        "SNCA", "PINK1", "DJ1", "ATP13A2", "GCH1"
    }

    CLASSIFICATION_WORDS = [
        r'\bpathogenic\b',
        r'\blikely\s+pathogenic\b',
        r'\bvus\b',
        r'\buncertain\s+significance\b',
        r'\blikely\s+benign\b',
        r'\bbenign\b'
    ]

    AGE_PATTERNS = [
        r'\b(?:at|by)\s+(?:age\s+)?(\d{1,2})\b',
        r'\baged\s+(\d{1,2})\b',
        r'\bage\s+(?:of\s+)?(\d{1,2})\b',
        r'\b(\d{1,2})\s+years?\s+(?:old|of\s+age)\b',
        r'\bonset\s+(?:at\s+)?(\d{1,2})\b',
        r'\bnow\s+(\d{1,2})\b'
    ]

    HGVS_PATTERNS = [
        r'\bc\.[0-9]+[a-zA-Z0-9_>+-]+\b',
        r'\bp\.[A-Z][a-z]{2}[0-9]+[A-Z][a-z]{2}\b',
        r'\b[A-Z][0-9]{2,4}[A-Z]\b',
        r'\bexon\s+[0-9]+(?:\s*(?:and|to|-)\s*[0-9]+)?\s+(?:deletion|duplication|del|dup|loss|deleted)\b'
    ]

    def audit_completeness(self, raw_text: str, batch: DocumentExtractionBatch) -> Tuple[bool, List[str]]:
        """
        Audits an incoming extraction batch against raw text anchors.
        Returns:
            is_complete (bool): True if all detected anchors are represented in batch.
            omissions (List[str]): List of missing anchor descriptions.
        """
        omissions = []
        text_lower = raw_text.lower()
        observations = batch.observations

        # 1. Total empty batch on non-empty substantive text
        if len(observations) == 0 and len(raw_text.strip()) > 10:
            # Check if text had any anchor
            has_any_anchor = (
                any(re.search(p, raw_text, re.IGNORECASE) for p in self.HGVS_PATTERNS) or
                any(re.search(rf'\b{g}\b', raw_text, re.IGNORECASE) for g in self.KNOWN_GENES) or
                any(re.search(p, text_lower) for p in self.CLASSIFICATION_WORDS) or
                any(re.search(p, text_lower) for p in self.AGE_PATTERNS)
            )
            if has_any_anchor:
                omissions.append(
                    "EXTRACTION_INCOMPLETE: Extractor returned 0 observations for clinical text containing actionable anchors"
                )
                return False, omissions

        # 2. HGVS Variant Anchor Check
        found_hgvs = []
        for p in self.HGVS_PATTERNS:
            matches = re.findall(p, raw_text, re.IGNORECASE)
            for m in matches:
                # Filter out obvious non-variant acronyms
                if m.upper() in self.KNOWN_GENES or m.upper() in ("VUS", "DNA", "RNA", "MDS", "MRI"):
                    continue
                found_hgvs.append(m)

        if found_hgvs:
            has_variant_obs = any(
                o.predicate in (PredicateType.HAS_VARIANT.value, PredicateType.AGGREGATE_CLASSIFICATION_ASSERTION.value)
                or (o.target and any(v.lower() in o.target.lower() for v in found_hgvs))
                for o in observations
            )
            if not has_variant_obs:
                omissions.append(
                    f"EXTRACTION_INCOMPLETE: Text contains variant anchor(s) {found_hgvs} but batch lacks HAS_VARIANT observation"
                )

        # 3. Known Gene Mention Anchor Check
        found_genes = [g for g in self.KNOWN_GENES if re.search(rf'\b{g}\b', raw_text, re.IGNORECASE)]
        if found_genes:
            has_gene_obs = any(
                o.predicate in (PredicateType.HAS_GENE_MENTION.value, PredicateType.HAS_VARIANT.value)
                or (o.value and str(o.value).upper() in found_genes)
                or (o.raw_variant and any(g in o.raw_variant.upper() for g in found_genes))
                for o in observations
            )
            if not has_gene_obs:
                omissions.append(
                    f"EXTRACTION_INCOMPLETE: Text mentions gene(s) {found_genes} but batch lacks gene/variant observation"
                )

        # 4. Explicit Age Anchor Check
        found_ages = []
        for p in self.AGE_PATTERNS:
            m = re.search(p, text_lower)
            if m:
                found_ages.append(m.group(1))

        if found_ages:
            has_age_obs = any(
                o.predicate in (PredicateType.HAS_ONSET_AGE.value, PredicateType.HAS_CURRENT_AGE.value)
                or (o.temporal_relation and o.temporal_relation.source_span)
                for o in observations
            )
            if not has_age_obs:
                omissions.append(
                    f"EXTRACTION_INCOMPLETE: Text contains explicit age '{found_ages[0]}' but batch lacks age observation"
                )

        # 5. Explicit Classification Word Check
        found_classes = [w for w in self.CLASSIFICATION_WORDS if re.search(w, text_lower)]
        if found_classes:
            has_class_obs = any(
                o.predicate in (PredicateType.HAS_CLASSIFICATION_ASSERTION.value, PredicateType.AGGREGATE_CLASSIFICATION_ASSERTION.value)
                or (o.value and any(re.search(c, str(o.value).lower()) for c in self.CLASSIFICATION_WORDS))
                or (o.raw_finding and any(re.search(c, str(o.raw_finding).lower()) for c in self.CLASSIFICATION_WORDS))
                for o in observations
            )
            if not has_class_obs:
                omissions.append(
                    "EXTRACTION_INCOMPLETE: Text contains classification descriptor but batch lacks classification assertion"
                )

        is_complete = (len(omissions) == 0)
        return is_complete, omissions
