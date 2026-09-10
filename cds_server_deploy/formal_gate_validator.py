import re
from typing import List, Dict, Any, Tuple, Optional
from h1_contract import (
    DocumentExtractionBatch,
    Observation,
    PredicateType,
    SubjectType,
    ALLOWED_SYMPTOM_CONCEPTS,
    EpistemicStatus,
    TemporalScope,
    TemporalRelationType,
    TemporalAnchor,
    TemporalRelation
)

# ==============================================================================
# CONCEPT GROUNDING DICTIONARY FOR SPAN CONTAINMENT
# ==============================================================================
CONCEPT_LEXICAL_GROUNDING = {
    "hallucinations": ["hallucin", "shadow", "visual", "seeing things"],
    "tremor_rest": ["tremor", "shaking", "pill-rolling"],
    "rigidity": ["rigidity", "stiff", "cogwheel", "lead-pipe"],
    "bradykinesia": ["bradykinesia", "slowness", "slow", "difficulty initiating", "movement speed"],
    "dystonia": ["dystonia", "dystonic", "posturing", "cramp", "foot dragging", "dragging", "turning of the foot", "inward turning", "inward posture", "posture of the"],
    "cognitive_decline": ["dementia", "cognitive", "memory", "intact", "impairment", "decline"],
    "autonomic_dysfunction": ["orthostatic", "hypotension", "dizziness", "autonomic", "light-headedness", "syncope"],
    "vertical_gaze_palsy": ["gaze", "restriction", "palsy", "vertical", "supranuclear"],
    "diurnal_fluctuation": ["worsening", "evening", "diurnal", "variation", "afternoon", "fluctuation"],
    "spasticity_pyramidal_signs": ["spasticity", "pyramidal", "hyperreflexia", "reflexes", "brisk"],
    "depression": ["depression", "depressed"],
    "parkinsonism": ["parkinsonism", "parkinson", "parkinsonian", "affected", "similar symptoms", "motor symptoms", "motor features", "motor impairment", "symptomatic"],
    "sleep_benefit": ["sleep", "rest"],
    "hyposmia": ["smell", "hyposmia", "olfactory", "loss of smell"],
    "levodopa_response": ["levodopa", "l-dopa", "dopa"]
}

# Negation indicators for polarity consistency check
NEGATION_CUES = ["denies", "no", "without", "never", "absence of", "no longer", "not", "neither"]

# ==============================================================================
# FORMAL VERIFICATION GATE: INVARIANT CHECKER & HALLUCINATION BARRIER (H1.1)
# ==============================================================================

class ValidationResult:
    def __init__(self, observation_id: str, is_valid: bool, errors: List[str], warnings: List[str]):
        self.observation_id = observation_id
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }

class FormalGateValidator:
    """
    Formal Verification Gate (H1.1) that filters, validates, and gates incoming observations
    from the Constrained SLM Semantic Extractor before they can touch the Revision 6.2 core.
    Enforces the iron rule: NO SOURCE SUPPORT -> DROP / ABSTAIN.
    """
    def __init__(self, raw_text: str):
        self.raw_text = raw_text

    def validate_observation(self, obs: Observation) -> ValidationResult:
        errors = []
        warnings = []

        # 1. Subject validation
        valid_subjects = {s.value for s in SubjectType}
        if not obs.subject or obs.subject.type not in valid_subjects:
            errors.append(f"Invalid or missing subject type: {obs.subject.type if obs.subject else 'None'}")

        # 2. Predicate validation
        valid_predicates = {p.value for p in PredicateType}
        if not obs.predicate or obs.predicate not in valid_predicates:
            errors.append(f"Invalid predicate: {obs.predicate}")

        # 3. Source Span & Ground-Truth Containment Check (Hallucination Barrier)
        span_text = ""
        if not obs.source or not obs.source.text_span:
            errors.append("NO_SOURCE_SUPPORT: Missing source span metadata")
        else:
            span_text = obs.source.text_span
            start = obs.source.start
            end = obs.source.end

            # Verify exact span offset matching
            if 0 <= start < end <= len(self.raw_text):
                actual_text_slice = self.raw_text[start:end]
                if actual_text_slice.strip() != span_text.strip():
                    errors.append(
                        f"SPAN_OFFSET_MISMATCH: Offset [{start}:{end}] yields '{actual_text_slice}' "
                        f"but claimed '{span_text}'"
                    )
            else:
                # If offsets out of range, check if span_text exists anywhere in raw_text
                if span_text not in self.raw_text:
                    errors.append(f"SPAN_HALLUCINATION: Claimed span '{span_text}' does not exist in input text")
                else:
                    warnings.append(f"Offset bounds [{start}:{end}] out of range, but substring found in text")

        # 4. Concept Grounding Check: Ensure concept is semantically anchored in source span or antecedent span
        if obs.predicate == PredicateType.HAS_SYMPTOM.value and span_text:
            # A. Whitelist check
            if obs.mapping_status == "CONFIRMED":
                if not obs.concept or obs.concept not in ALLOWED_SYMPTOM_CONCEPTS:
                    errors.append(f"ILLEGAL_CONCEPT: Concept '{obs.concept}' is not in approved ontology whitelist")
                else:
                    c_cues = CONCEPT_LEXICAL_GROUNDING.get(obs.concept, [obs.concept])
                    span_lower = span_text.lower()

                    # H1.1 Refinement 1: Anaphoric Grounding via explicit antecedent_span
                    if obs.resolution_method in ("anaphora_resolution", "anaphoric_grounding") or obs.antecedent_span:
                        if not obs.antecedent_span:
                            errors.append("MISSING_ANTECEDENT_SPAN: Observation uses anaphora but lacks antecedent_span")
                        else:
                            ant_txt = obs.antecedent_span.text_span
                            ant_s = obs.antecedent_span.start
                            ant_e = obs.antecedent_span.end
                            if 0 <= ant_s < ant_e <= len(self.raw_text) and self.raw_text[ant_s:ant_e].strip() == ant_txt.strip():
                                if not any(cue in ant_txt.lower() for cue in c_cues):
                                    errors.append(f"ANTECEDENT_CONCEPT_UNGROUNDED: Concept '{obs.concept}' not grounded in antecedent span '{ant_txt}'")
                            else:
                                if ant_txt.lower() not in self.raw_text.lower():
                                    errors.append(f"ANTECEDENT_SPAN_HALLUCINATION: Antecedent span '{ant_txt}' not found in source text")
                                else:
                                    if not any(cue in ant_txt.lower() for cue in c_cues):
                                        errors.append(f"ANTECEDENT_CONCEPT_UNGROUNDED: Concept '{obs.concept}' not grounded in antecedent span '{ant_txt}'")
                    elif obs.resolution_method == "ellipsis_recovery":
                        # In ellipsis recovery, concept grounding draws from the antecedent clause in text
                        if not any(cue in self.raw_text.lower() for cue in c_cues):
                            errors.append(
                                f"SPAN_CONCEPT_UNGROUNDED: Concept '{obs.concept}' has zero lexical support in document"
                            )
                    else:
                        if not any(cue in span_lower for cue in c_cues):
                            errors.append(
                                f"SPAN_CONCEPT_UNGROUNDED: Concept '{obs.concept}' has zero lexical support in span '{span_text}'"
                            )
            elif obs.mapping_status == "PROPOSED":
                # H1.1 Refinement 2: Qualitative/Candidate concepts allowed as PROPOSED
                if not obs.candidate_concept or obs.candidate_concept not in ALLOWED_SYMPTOM_CONCEPTS:
                    errors.append(f"ILLEGAL_CANDIDATE: Proposed candidate '{obs.candidate_concept}' is not in approved ontology")
                warnings.append(f"PROPOSED_MAPPING: Raw finding '{obs.raw_finding}' pending deterministic approval")

        # 5. Polarity Consistency Check
        if obs.polarity not in ("positive", "negative"):
            errors.append(f"Invalid polarity: {obs.polarity}")
        elif span_text and obs.predicate in (PredicateType.HAS_SYMPTOM.value, PredicateType.HAS_NORMAL_FINDING.value):
            span_lower = span_text.lower()
            # If epistemic status is UNCONFIRMED/SUSPECTED/UNCERTAIN, doubt cues like "never confirmed" are epistemic, not polarity inversions
            is_epistemic_qualifier = obs.epistemic_status in (
                EpistemicStatus.UNCONFIRMED.value,
                EpistemicStatus.SUSPECTED.value,
                EpistemicStatus.UNCERTAIN.value,
                EpistemicStatus.POSSIBLE.value
            ) or ("suspected but never confirmed" in span_lower)

            # Contrastive negation cue: "not the proband" negates proband, not the sister!
            has_contrastive_not = bool(re.search(r'\bnot\s+(?:the\s+)?(proband|patient|sister|brother|father|mother)\b', span_lower))
            is_negated_subject = False
            if has_contrastive_not:
                neg_target = re.search(r'\bnot\s+(?:the\s+)?([a-z]+)\b', span_lower)
                if neg_target and obs.subject.type == neg_target.group(1):
                    is_negated_subject = True

            has_neg_cue = any(re.search(rf'\b{cue}\b', span_lower) for cue in NEGATION_CUES)
            if has_contrastive_not and not is_negated_subject:
                has_neg_cue = False

            if has_neg_cue and obs.polarity == "positive" and not is_epistemic_qualifier:
                # Special exemption: "not only ... but also"
                if not re.search(r'\bnot\s+only\b', span_lower):
                    errors.append(
                        f"POLARITY_INVERSION: Source span '{span_text}' contains explicit negation cue but polarity asserted positive"
                    )

        # 6. Subject-Span and Relation Grounding Check
        # H1.1 Refinement 4: Distinguish experiencer subject from relation object (e.g. parental origin)
        if span_text and obs.subject:
            span_lower = span_text.lower()
            claimed_subj = obs.subject.type
            relatives = ["father", "mother", "sister", "brother", "daughter", "son", "grandmother", "grandfather", "aunt"]
            found_relatives = [r for r in relatives if re.search(rf'\b{r}\b', span_lower)]

            is_parental_origin_rel = (
                obs.predicate == PredicateType.HAS_PARENTAL_ORIGIN.value or
                (obs.relation_object and obs.relation_object in found_relatives) or
                (claimed_subj == "proband" and any(cue in span_lower for cue in ["inherited from", "came from", "variant is maternal", "variant is paternal", "maternal", "paternal"]))
            )

            if found_relatives and not is_parental_origin_rel:
                # Multi-clause relation check: e.g. "The sister has hallucinations; the proband has tremor."
                if ";" in span_text or " while " in span_lower or " whereas " in span_lower:
                    clauses = re.split(r'[;]|\s+while\s+|\s+whereas\s+', span_lower)
                    for cl in clauses:
                        if obs.concept and any(cue in cl for cue in CONCEPT_LEXICAL_GROUNDING.get(obs.concept, [obs.concept])):
                            cl_relatives = [r for r in relatives if re.search(rf'\b{r}\b', cl)]
                            if cl_relatives and claimed_subj not in cl_relatives:
                                errors.append(
                                    f"RELATION_GROUNDING_MISMATCH: Concept '{obs.concept}' is in clause governed by relative '{cl_relatives[0]}', not claimed subject '{claimed_subj}'"
                                )
                else:
                    if claimed_subj == "proband" and not re.search(r'\bproband\b|\bpatient\b', span_lower):
                        errors.append(
                            f"SUBJECT_SPAN_MISMATCH: Claimed subject '{claimed_subj}' contradicts span grounded in relative(s): {found_relatives}"
                        )
                    elif claimed_subj not in found_relatives and claimed_subj != "proband":
                        errors.append(
                            f"SUBJECT_SPAN_MISMATCH: Claimed subject '{claimed_subj}' does not match span relative '{found_relatives[0]}'"
                        )

        # 7. Temporal Scope & Typed Temporal Relation Grounding Check
        # H1.1 Refinement 3: Support typed TemporalRelation objects
        if obs.temporal_relation:
            valid_rel_types = {t.value for t in TemporalRelationType}
            if obs.temporal_relation.relation_type not in valid_rel_types:
                errors.append(f"INVALID_TEMPORAL_RELATION_TYPE: Unknown relation type '{obs.temporal_relation.relation_type}'")
            if obs.temporal_relation.source_span:
                tr_span = obs.temporal_relation.source_span.text_span
                if tr_span.lower() not in self.raw_text.lower():
                    errors.append(f"UNSUPPORTED_TEMPORAL_RELATION: Temporal relation span '{tr_span}' not found in source text")
        elif obs.temporal_scope in (TemporalScope.HISTORICAL.value, TemporalScope.RESOLVED.value, TemporalScope.ONSET.value):
            text_lower = self.raw_text.lower()
            temp_cues = {
                TemporalScope.HISTORICAL.value: [
                    "previously", "past", "history", "years ago", "earlier", "prior",
                    "initially", "before", "had ", "later", "subsequently", "followed by",
                    "during", "developed", "preceded", "was present", "early", "early in",
                    "historical", "obsolete"
                ],
                TemporalScope.RESOLVED.value: ["resolved", "no longer", "disappeared", "cleared"],
                TemporalScope.ONSET.value: [
                    "onset", "at onset", "began", "started", "presenting", "first noticed",
                    "initial", "first symptom", "first complaint", "first neurological",
                    "first became", "from the outset", "first"
                ]
            }
            cues = temp_cues.get(obs.temporal_scope, [])
            if not any(cue in text_lower for cue in cues):
                errors.append(
                    f"UNSUPPORTED_TEMPORAL_SCOPE: Temporal scope '{obs.temporal_scope}' has no temporal cue support in source text"
                )

        # 8. Source / Asserted_By Grounding Check (Universal Provenance Grounding)
        if obs.source and obs.source.asserted_by:
            ab = obs.source.asserted_by.lower().strip()
            text_lower = self.raw_text.lower()
            prov_cues = {
                "laboratory_report": ["lab", "laboratory", "report", "testing", "panel", "exome", "sequencing"],
                "laboratory": ["lab", "laboratory", "report", "testing"],
                "outside_laboratory": ["outside lab", "outside laboratory", "external lab", "reference lab"],
                "previous_report": ["previous report", "older report", "prior report", "earlier report", "old report"],
                "amended_report": ["amended", "addendum", "revised", "correction"],
                "clinic_note": ["clinic", "hospital", "chart", "letter", "note"],
                "clinician": ["neurologist", "physician", "doctor", "clinician"],
                "neurologist": ["neurologist", "physician", "doctor", "clinician"],
                "clinvar": ["clinvar"],
                "database": ["database", "gnomad", "db", "omim"],
                "patient": ["patient", "proband"],
                "family": ["family", "mother", "father", "sister", "brother", "wife", "spouse"]
            }
            tokens = [t for t in re.split(r'[-_\s]+', ab) if len(t) > 2]
            cues = prov_cues.get(ab, tokens)
            is_grounded = any(cue in text_lower for cue in cues) or any(t in text_lower for t in tokens)
            if not is_grounded:
                errors.append(f"UNSUPPORTED_SOURCE_ASSERTION: Claimed asserted_by '{obs.source.asserted_by}' has no lexical cue in text")

        # 9. Zygosity Grounding Check
        if obs.predicate == PredicateType.HAS_ZYGOSITY.value:
            val = str(obs.value).lower()
            text_lower = self.raw_text.lower()
            if val in ("heterozygous", "homozygous"):
                if val not in text_lower:
                    errors.append(f"UNSUPPORTED_ZYGOSITY: Zygosity '{obs.value}' not found in source text")

        # 10. Molecular Hallucination Check for HAS_VARIANT
        if obs.predicate == PredicateType.HAS_VARIANT.value:
            if not obs.raw_variant and not obs.raw_finding:
                errors.append("HAS_VARIANT requires non-empty raw_variant or raw_finding")
            elif obs.raw_variant:
                clean_var = obs.raw_variant.strip()
                if clean_var.lower() not in self.raw_text.lower():
                    errors.append(f"MOLECULAR_HALLUCINATION: raw_variant '{clean_var}' not found in source text")
                elif span_text and clean_var.lower() not in span_text.lower():
                    warnings.append(f"raw_variant '{clean_var}' in text but not within claimed span '{span_text}'")

        # 11. Classification Assertion & Aggregate Multiset Grounding Check
        # H1.1 Refinement 5: Support AGGREGATE_CLASSIFICATION_ASSERTION with multiset counts
        if obs.predicate in (PredicateType.HAS_CLASSIFICATION_ASSERTION.value, PredicateType.AGGREGATE_CLASSIFICATION_ASSERTION.value):
            allowed_classes = {
                "pathogenic", "likely pathogenic", "vus", "likely benign", "benign",
                "uncertain", "unclassified", "none", "pending", "unknown"
            }
            if isinstance(obs.value, dict) or obs.counts or obs.predicate == PredicateType.AGGREGATE_CLASSIFICATION_ASSERTION.value:
                counts_dict = obs.counts or (obs.value if isinstance(obs.value, dict) else {})
                if not counts_dict:
                    errors.append("AGGREGATE_CLASSIFICATION_EMPTY: Aggregate classification multiset is empty")
                else:
                    text_lower = self.raw_text.lower()
                    for cls_label in counts_dict.keys():
                        cls_clean = str(cls_label).lower().strip()
                        if not any(ac in cls_clean for ac in allowed_classes):
                            errors.append(f"ILLEGAL_CLASSIFICATION: Unknown classification label '{cls_clean}' in aggregate multiset")
                        else:
                            val_cues = [cls_clean]
                            if cls_clean == "vus": val_cues.extend(["vus", "uncertain significance"])
                            if cls_clean == "pathogenic": val_cues.extend(["pathogenic", "mutation"])
                            if not any(cue in text_lower for cue in val_cues):
                                errors.append(f"UNSUPPORTED_CLASSIFICATION: Multiset class '{cls_clean}' has no lexical support in source text")
                    if obs.assignment_status not in ("UNRESOLVED", "RESOLVED") and obs.predicate == PredicateType.AGGREGATE_CLASSIFICATION_ASSERTION.value:
                        warnings.append("AGGREGATE_CLASSIFICATION_STATUS: assignment_status should be explicitly UNRESOLVED or RESOLVED")
            else:
                val = str(obs.value).lower().strip()
                if not any(ac in val for ac in allowed_classes):
                    errors.append(f"ILLEGAL_CLASSIFICATION: Unknown classification value '{obs.value}'")
                else:
                    text_lower = self.raw_text.lower()
                    val_cues = [val]
                    if val == "vus": val_cues.extend(["vus", "uncertain significance"])
                    if val == "pathogenic": val_cues.extend(["pathogenic", "mutation"])
                    if val in ("unclassified", "none", "unknown", "pending"):
                        val_cues.extend(["no classification", "not classified", "unclassified", "not yet assigned", "pending", "awaiting", "review"])
                    if not any(cue in text_lower for cue in val_cues):
                        errors.append(
                            f"UNSUPPORTED_CLASSIFICATION: Claimed classification '{obs.value}' has no lexical support in source text"
                        )

        # 12. Parental Origin Grounding Check
        if obs.predicate == PredicateType.HAS_PARENTAL_ORIGIN.value:
            val = str(obs.value).lower().strip()
            text_lower = self.raw_text.lower()
            if val == "maternal" and not any(w in text_lower for w in ["mother", "maternal"]):
                errors.append(f"UNSUPPORTED_PARENTAL_ORIGIN: Value '{obs.value}' not supported by source text")
            elif val == "paternal" and not any(w in text_lower for w in ["father", "paternal"]):
                errors.append(f"UNSUPPORTED_PARENTAL_ORIGIN: Value '{obs.value}' not supported by source text")

        # 13. Epistemic Status & Coreference Ambiguity Validation
        valid_epistemic = {e.value for e in EpistemicStatus}
        if obs.epistemic_status not in valid_epistemic:
            errors.append(f"Invalid epistemic status: {obs.epistemic_status}")

        # Check overconfident ambiguous coreference
        if obs.resolution_method == "overconfident_coreference" or (
            obs.target and "it" in span_text.lower().split() and "two" in self.raw_text.lower() and obs.confidence > 0.95 and obs.predicate != PredicateType.RELATION_UNRESOLVED.value
        ):
            errors.append("AMBIGUOUS_COREFERENCE_UNRESOLVED: Pronoun antecedent is ambiguous across multiple candidates; requires RELATION_UNRESOLVED")

        is_valid = (len(errors) == 0)
        return ValidationResult(obs.id, is_valid, errors, warnings)

    def validate_cross_observation_consistency(self, observations: List[Observation]) -> List[str]:
        """
        Cross-Observation Consistency Check:
        Verifies that the entire set of observations in a document batch is mutually coherent.
        Traps joint/compound errors where individual observations pass per-obs span check,
        but together form a contradictory or corrupt clinical interpretation.
        """
        inconsistencies = []

        # 1. Contradictory polarities for the exact same subject, concept, and temporal scope
        concept_states: Dict[Tuple[str, str, str], List[Observation]] = {}
        for o in observations:
            if o.predicate == PredicateType.HAS_SYMPTOM.value and o.concept:
                key = (o.subject.type, o.concept, o.temporal_scope)
                concept_states.setdefault(key, []).append(o)

        for (subj, concept, temp), obs_list in concept_states.items():
            asserted_polarities = {
                o.polarity for o in obs_list
                if o.epistemic_status == EpistemicStatus.ASSERTED.value
            }
            if len(asserted_polarities) > 1:
                inconsistencies.append(
                    f"CROSS_OBS_CONTRADICTORY_POLARITY: Subject '{subj}' has simultaneous positive and negative '{temp}' status for concept '{concept}'"
                )

        # 2. Subject leakage: Universal check for ANY Subject A -> Subject B (A != B)
        ENTITY_CUES = {
            "proband": ["proband", "patient"],
            "father": ["father"],
            "mother": ["mother"],
            "sister": ["sister"],
            "brother": ["brother"],
            "daughter": ["daughter"],
            "son": ["son"],
            "grandmother": ["grandmother"],
            "grandfather": ["grandfather"],
            "spouse": ["spouse", "wife", "husband"],
            "relative": ["relative", "relatives"]
        }

        for o in observations:
            if o.source and o.source.text_span:
                span_low = o.source.text_span.lower()
                claimed_subj = o.subject.type
                # Exemption for molecular parental origin where proband is subject and mother/father is relation object
                if o.predicate == PredicateType.HAS_PARENTAL_ORIGIN.value:
                    continue
                if o.relation_object and claimed_subj == "proband" and any(cue in span_low for cue in ["inherited from", "maternal", "paternal", "came from"]):
                    continue

                # Identify entities explicitly anchored in this span
                mentioned_entities = set()
                for ent, cues in ENTITY_CUES.items():
                    if any(re.search(rf'\b{re.escape(cue)}\b', span_low) for cue in cues):
                        mentioned_entities.add(ent)

                other_entities = mentioned_entities - {claimed_subj}
                has_claimed_cue = any(re.search(rf'\b{re.escape(cue)}\b', span_low) for cue in ENTITY_CUES.get(claimed_subj, [claimed_subj]))

                if other_entities and not has_claimed_cue:
                    anchor_ent = list(other_entities)[0]
                    inconsistencies.append(
                        f"CROSS_OBS_SUBJECT_LEAKAGE: Subject '{claimed_subj}' was attributed '{o.concept or o.predicate}' using span '{o.source.text_span}' anchored to '{anchor_ent}'"
                    )

        # 3. Phasing vs Parental Origin contradiction
        # CIS requires same parent (cannot have maternal + paternal)
        # TRANS requires opposite parents (cannot have maternal + maternal or paternal + paternal)
        has_cis = any(o.predicate == PredicateType.HAS_PHASE_ASSERTION.value and str(o.value).lower() == "cis" for o in observations)
        has_trans = any(o.predicate == PredicateType.HAS_PHASE_ASSERTION.value and str(o.value).lower() == "trans" for o in observations)
        origins = [
            str(o.value).lower() for o in observations
            if o.predicate == PredicateType.HAS_PARENTAL_ORIGIN.value
        ]
        origins_set = set(origins)

        if has_cis:
            if "maternal" in origins_set and "paternal" in origins_set:
                inconsistencies.append(
                    "CROSS_OBS_PHASING_CONFLICT: Batch asserts CIS phasing but variants originate from opposite parents (maternal + paternal)"
                )
        if has_trans:
            if len(origins) >= 2 and len(origins_set) == 1 and ("maternal" in origins_set or "paternal" in origins_set):
                inconsistencies.append(
                    f"CROSS_OBS_PHASING_CONFLICT: Batch asserts TRANS phasing but variants originate from the same parent ({list(origins_set)[0]})"
                )

        # 4. Molecular variant cardinality check (False deduplication / variant loss detection)
        # Generalized for any N_text > N_extracted
        AA_MAP = {
            'Ala': 'A', 'Arg': 'R', 'Asn': 'N', 'Asp': 'D', 'Cys': 'C',
            'Gln': 'Q', 'Glu': 'E', 'Gly': 'G', 'His': 'H', 'Ile': 'I',
            'Leu': 'L', 'Lys': 'K', 'Met': 'M', 'Phe': 'F', 'Pro': 'P',
            'Ser': 'S', 'Thr': 'T', 'Trp': 'W', 'Tyr': 'Y', 'Val': 'V'
        }
        def norm_hgvs(v: str) -> str:
            m = re.match(r'^p\.([A-Z][a-z]{2})([0-9]+)([A-Z][a-z]{2})$', v)
            if m:
                a1, pos, a2 = m.groups()
                if a1 in AA_MAP and a2 in AA_MAP:
                    return f"{AA_MAP[a1]}{pos}{AA_MAP[a2]}".lower()
            return v.lower()

        hgvs_matches = re.findall(r'\b(?:c\.[0-9]+[a-zA-Z0-9_>+-]+|p\.[A-Z][a-z]{2}[0-9]+[A-Z][a-z]{2}|[A-Z][0-9]+[A-Z])\b', self.raw_text)
        exon_matches = re.findall(r'\b(?:exon\s+[0-9]+(?:\s*(?:and|to|-)\s*[0-9]+)?(?:\s+(?:deletion|duplication|del|dup|loss|deleted))?|(?:deletion|duplication|loss)\s+of\s+exon[s]?\s+[0-9]+)\b', self.raw_text, re.IGNORECASE)
        distinct_variants = set(norm_hgvs(m) for m in hgvs_matches) | set(m.lower() for m in exon_matches)
        variant_obs = [o for o in observations if o.predicate == PredicateType.HAS_VARIANT.value]
        variant_targets = {
            norm_hgvs(o.target) for o in observations
            if o.target and norm_hgvs(o.target) in distinct_variants
        }
        n_extracted = len(variant_obs) + len(variant_targets - {norm_hgvs(o.raw_variant) for o in variant_obs if o.raw_variant})
        n_text_variants = len(distinct_variants)

        has_aggregate = any(o.predicate in (PredicateType.AGGREGATE_CLASSIFICATION_ASSERTION.value, PredicateType.HAS_PHASE_ASSERTION.value) for o in observations)

        if n_text_variants >= 2 and n_text_variants > n_extracted and not has_aggregate:
            inconsistencies.append(
                f"CARDINALITY_INCONSISTENCY: Source text mentions {n_text_variants} distinct variants {distinct_variants} but batch contains only {n_extracted} variant observation(s)"
            )

        return inconsistencies

    def filter_batch(self, batch: DocumentExtractionBatch) -> Tuple[List[Observation], List[ValidationResult]]:
        """
        Processes an incoming extraction batch, applies the Formal Verification Gate,
        and returns (validated_observations, audit_results).
        Dropped observations are never forwarded to the clinical state machine.
        """
        validated = []
        audit_results = []

        for obs in batch.observations:
            res = self.validate_observation(obs)
            audit_results.append(res)
            if res.is_valid:
                validated.append(obs)

        # Apply Cross-Observation Consistency Check on candidate batch
        self.cross_inconsistencies = self.validate_cross_observation_consistency(batch.observations)
        if self.cross_inconsistencies:
            for inc in self.cross_inconsistencies:
                audit_results.append(ValidationResult("batch_cross_consistency", False, [inc], []))
            # If fatal contradictory cross-observation state occurs, block corrupted observations
            if any("CROSS_OBS_CONTRADICTORY_POLARITY" in inc or "CROSS_OBS_SUBJECT_LEAKAGE" in inc or "CARDINALITY_INCONSISTENCY" in inc or "INCOMPLETE_EXTRACTION" in inc or "CROSS_OBS_PHASING_CONFLICT" in inc for inc in self.cross_inconsistencies):
                validated = []

        return validated, audit_results
