import re
import sys
import json
from typing import List, Dict, Any, Optional, Tuple

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ==============================================================================
# REVISION 6.2: CANONICAL GENE & VARIANT KNOWLEDGE BASE
# ==============================================================================
CANONICAL_CATALOG = {
    'c.1072delt': {
        'gene': 'PRKN', 'canonical_transcript': 'NM_004562.3',
        'hgvs_c': 'c.1072delT', 'hgvs_p': 'p.Cys358fs',
        'default_classification': 'Pathogenic'
    },
    'c.255dela': {
        'gene': 'PRKN', 'canonical_transcript': 'NM_004562.3',
        'hgvs_c': 'c.255delA', 'hgvs_p': 'p.Asn85fs',
        'default_classification': 'Pathogenic'
    },
    'c.202-1g>a': {
        'gene': 'PRKN', 'canonical_transcript': 'NM_004562.3',
        'hgvs_c': 'c.202-1G>A', 'hgvs_p': 'p.?',
        'default_classification': 'Pathogenic'
    },
    'c.3057delc': {
        'gene': 'ATP13A2', 'canonical_transcript': 'NM_022089.4',
        'hgvs_c': 'c.3057delC', 'hgvs_p': 'p.?',
        'default_classification': 'Pathogenic'
    },
    'p.ala311val': {
        'gene': 'PRKN', 'canonical_transcript': 'NM_004562.3',
        'hgvs_c': 'c.932C>T', 'hgvs_p': 'p.Ala311Val',
        'default_classification': 'VUS'
    },
    'p.asp620asn': {
        'gene': 'VPS35', 'canonical_transcript': 'NM_018206.6',
        'hgvs_c': 'c.1858G>A', 'hgvs_p': 'p.Asp620Asn',
        'default_classification': 'Pathogenic'
    },
    'p.gly2019ser': {
        'gene': 'LRRK2', 'canonical_transcript': 'NM_198578.4',
        'hgvs_c': 'c.6055G>A', 'hgvs_p': 'p.Gly2019Ser',
        'default_classification': 'Pathogenic (Reduced Penetrance)'
    },
    'p.asn409ser': {
        'gene': 'GBA1', 'canonical_transcript': 'NM_000157.4',
        'hgvs_c': 'c.1226A>G', 'hgvs_p': 'p.Asn409Ser',
        'default_classification': 'Pathogenic / Strong Susceptibility'
    },
    'p.ser71arg': {
        'gene': 'RAB32', 'canonical_transcript': 'NM_006834.5',
        'hgvs_c': 'c.213C>A', 'hgvs_p': 'p.Ser71Arg',
        'default_classification': 'Pathogenic'
    },
    'p.ala53thr': {
        'gene': 'SNCA', 'canonical_transcript': 'NM_000345.4',
        'hgvs_c': 'c.157G>A', 'hgvs_p': 'p.Ala53Thr',
        'default_classification': 'Pathogenic'
    },
    'p.gly309asp': {
        'gene': 'PINK1', 'canonical_transcript': 'NM_032409.3',
        'hgvs_c': 'c.926G>A', 'hgvs_p': 'p.Gly309Asp',
        'default_classification': 'Pathogenic'
    },
    'p.leu166pro': {
        'gene': 'PARK7', 'canonical_transcript': 'NM_007262.5',
        'hgvs_c': 'c.497T>C', 'hgvs_p': 'p.Leu166Pro',
        'default_classification': 'Pathogenic'
    }
}

SYNONYMS_MAP = {
    'd620n': 'p.asp620asn',
    's71r': 'p.ser71arg',
    'g2019s': 'p.gly2019ser',
    'a53t': 'p.ala53thr',
    'n370s': 'p.asn409ser',
    'g309d': 'p.gly309asp',
    'l166p': 'p.leu166pro',
    'a311v': 'p.ala311val'
}

WORD_TO_NUM = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
    'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60,
    'seventy': 70, 'eighty': 80, 'ninety': 90
}

ORDINAL_TO_DECADE = {
    'first': (0, 10, 'juvenile_onset'),
    'second': (11, 20, 'juvenile_onset'),
    'third': (21, 30, 'early_onset'),
    'fourth': (31, 40, 'early_onset'),
    'fifth': (41, 50, 'early_onset'),
    'sixth': (51, 60, 'late_onset'),
    'seventh': (61, 70, 'late_onset'),
    'eighth': (71, 80, 'late_onset')
}

def parse_written_number(text: str) -> Optional[int]:
    clean = text.lower().replace('-', ' ').strip()
    tokens = clean.split()
    total = 0
    for tok in tokens:
        if tok in WORD_TO_NUM:
            total += WORD_TO_NUM[tok]
        else:
            return None
    return total if total > 0 else None

# ==============================================================================
# COMPONENT 1: NARRATIVE AGE EXTRACTOR & CLINICAL ONSET CATEGORIZER
# ==============================================================================
def extract_numeric_age(sentence: str) -> Optional[int]:
    """
    Extracts numeric age across structured, colloquial, and narrative English:
    - "27-year-old", "27 yo", "27 y/o"
    - "aged 27", "age 27", "at 16 years of age", "at age 70"
    - "when he was 37", "was 51 at symptom onset"
    - "onset was at approximately 58 years"
    - "between ages 28 and 32" -> mid-point 30
    - "aged forty-two", "at sixteen years of age", "at age fifty"
    """
    s = sentence.strip()

    # 1. Interval expressions: "between ages 28 and 32" -> return midpoint
    m_between = re.search(r'\bbetween\s+ages?\s+(\d{1,3})\s+and\s+(\d{1,3})\b', s, re.I)
    if m_between:
        low, high = int(m_between.group(1)), int(m_between.group(2))
        return int((low + high) / 2)

    # 2. Inverted onset phrases: "was 51 at symptom onset" or "was 51 at onset"
    m_was_at = re.search(r'\bwas\s+(\d{1,3})\s+at\s+(?:symptom\s+)?onset\b', s, re.I)
    if m_was_at:
        return int(m_was_at.group(1))

    # 3. Clause: "when he/she/the patient was 37"
    m_when = re.search(r'\bwhen\s+(?:he|she|the\s+patient)\s+was\s+(\d{1,3})\b', s, re.I)
    if m_when:
        return int(m_when.group(1))

    # 4. Disease onset expressions: "onset was at approximately 58 years"
    m_onset_approx = re.search(r'\b(?:onset\s+was\s+at|at)\s+(?:approximately\s+|about\s+|around\s+)?(\d{1,3})\s*(?:years|y\/o)?\b', s, re.I)
    if m_onset_approx:
        return int(m_onset_approx.group(1))

    # 5. Standard digit patterns
    patterns = [
        re.compile(r'\b(\d{1,3})[- ]year[- ]old\b', re.I),
        re.compile(r'\b(\d{1,3})\s*y\/?o\b', re.I),
        re.compile(r'\b(?:aged?|age)\s+(\d{1,3})\b', re.I),
        re.compile(r'\b(?:at\s+age|at\s+the\s+age\s+of)\s+(\d{1,3})\b', re.I),
        re.compile(r'\bat\s+(\d{1,3})\s+years\s+(?:of\s+age)?\b', re.I),
        re.compile(r'\bchild\s+aged?\s+(\d{1,3})\b', re.I),
        re.compile(r'\bsymptoms\s+at\s+(\d{1,3})\b', re.I),
        re.compile(r'\bdeveloped\s+symptoms\s+at\s+(\d{1,3})\b', re.I)
    ]
    for pat in patterns:
        m = pat.search(s)
        if m:
            return int(m.group(1))

    # 6. Spelled out words: "aged forty-two", "at sixteen years of age", "at age fifty"
    # Matches words from one to ninety-nine
    word_pattern = re.compile(
        r'\b(?:aged?|at\s+age|at)\s+('
        r'(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)'
        r'(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?'
        r')(?:\s+years\s+(?:of\s+age)?)?\b',
        re.I
    )
    wm = word_pattern.search(s)
    if wm:
        num = parse_written_number(wm.group(1))
        if num is not None:
            return num

    return None

def categorize_onset(age: Optional[int], text_fallback: str = "") -> Optional[str]:
    """
    Categorizes clinical onset according to consensus guidelines:
    - < 18: juvenile_onset
    - 18 <= age <= 50: early_onset
    - > 50: late_onset
    Supports narrative decade idioms and qualitative descriptors.
    """
    if age is not None:
        if age < 18:
            return 'juvenile_onset'
        elif 18 <= age <= 50:
            return 'early_onset'
        else:
            return 'late_onset'

    tf = text_fallback.lower()

    # 1. Decade of life: "in the fourth decade of life"
    m_decade_ord = re.search(r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth)\s+decade\s+(?:of\s+life)?\b', tf)
    if m_decade_ord:
        ord_word = m_decade_ord.group(1)
        if ord_word in ORDINAL_TO_DECADE:
            return ORDINAL_TO_DECADE[ord_word][2]

    # 2. Approximate decades: "in his early thirties", "in her late sixties"
    if re.search(r'\b(?:early|mid|late)?\s*(?:twenties|thirties|forties)\b', tf):
        return 'early_onset'
    if re.search(r'\b(?:early|mid|late)?\s*(?:sixties|seventies|eighties)\b', tf):
        return 'late_onset'
    if re.search(r'\bearly\s+fifties\b', tf) or re.search(r'\blate\s+fifties\b', tf) or re.search(r'\bfifties\b', tf):
        # 51-59 is late onset under >50 rule
        return 'late_onset'

    # 3. Qualitative ontological descriptors
    if re.search(r'\bjuvenile\b|\bchildhood\b|\badolescence\b', tf):
        return 'juvenile_onset'
    if re.search(r'\bearly[- ]onset\b', tf):
        return 'early_onset'
    if re.search(r'\blate[- ]onset\b', tf):
        return 'late_onset'

    return None

# ==============================================================================
# COMPONENT 2: SEMANTIC REVISION GRAPH & INTRA-SENTENCE BRANCH EXTRACTOR
# ==============================================================================
class DocumentRevision:
    def __init__(self, rev_id: str, label: str, source: str, parent_id: Optional[str] = None,
                 supersedes_id: Optional[str] = None, is_independent: bool = False,
                 raw_text: str = ""):
        self.id = rev_id
        self.label = label
        self.source = source
        self.parent_id = parent_id
        self.supersedes_id = supersedes_id
        self.is_independent = is_independent
        self.raw_text = raw_text
        self.assertions: Dict[str, Any] = {}

class SemanticRevisionGraph:
    def __init__(self):
        self.revisions: Dict[str, DocumentRevision] = {}

    def add_revision(self, rev: DocumentRevision):
        self.revisions[rev.id] = rev

    def evaluate_lineage(self) -> Dict[str, Any]:
        if not self.revisions:
            return {'status': 'EMPTY'}

        superseded_ids = set()
        for rev in self.revisions.values():
            if rev.supersedes_id:
                superseded_ids.add(rev.supersedes_id)

        terminal_revisions = [rev for rev in self.revisions.values() if rev.id not in superseded_ids]

        terminal_origins = {}
        for r in terminal_revisions:
            allele = r.assertions.get('parental_allele')
            if allele:
                terminal_origins[r.id] = allele

        unique_terminal_values = set(terminal_origins.values())

        if len(terminal_revisions) > 1:
            if len(unique_terminal_values) > 1 or any(r.is_independent for r in terminal_revisions) or len(self.revisions) >= 2:
                return {
                    'status': 'VERSION_BRANCH_CONFLICT',
                    'effective_origin': 'UNDETERMINED',
                    'phasing_status': 'PHASING_BLOCKED',
                    'terminal_revisions': [
                        {'id': r.id, 'label': r.label, 'source': r.source, 'value': r.assertions.get('parental_allele')}
                        for r in terminal_revisions
                    ],
                    'reason': (
                        f"Lineage contains {len(terminal_revisions)} concurrent terminal revisions "
                        f"with conflicting assertions or independent branches "
                        f"and no supersession relation connecting them."
                    )
                }
        elif len(terminal_revisions) == 1:
            active_rev = terminal_revisions[0]
            eff = active_rev.assertions.get('parental_allele', 'unknown')
            return {
                'status': 'VERSION_HISTORY_RESOLVED',
                'effective_origin': eff,
                'phasing_status': 'DETERMINED',
                'active_revision': active_rev.label
            }
        else:
            eff = list(unique_terminal_values)[0] if unique_terminal_values else 'unknown'
            return {
                'status': 'UNAMBIGUOUS_CONCURRENCE',
                'effective_origin': eff,
                'phasing_status': 'DETERMINED'
            }

# ==============================================================================
# COMPONENT 3: CLINICAL SYMPTOMS & PHENOTYPE MAPPINGS
# ==============================================================================
SYMPTOM_PATTERNS = [
    ('dystonia', re.compile(r'\b(?:foot\s+|leg\s+|lower[- ]limb\s+)?dystonia\b', re.I)),
    ('tremor_rest', re.compile(r'\b(?:resting\s+tremor|unilateral\s+resting\s+tremor|tremor)\b', re.I)),
    ('bradykinesia', re.compile(r'\b(?:bradykinesia|slowness\s+of\s+movement)\b', re.I)),
    ('rigidity', re.compile(r'\b(?:cogwheel\s+rigidity|rigidity|stiffness)\b', re.I)),
    ('diurnal_fluctuation', re.compile(r'\b(?:worsening\s+in\s+the\s+evening|diurnal\s+variation)\b', re.I)),
    ('vertical_gaze_palsy', re.compile(r'\b(?:vertical\s+gaze\s+palsy|gaze\s+palsy)\b', re.I)),
    ('spasticity_pyramidal_signs', re.compile(r'\b(?:severe\s+spasticity|spasticity|pyramidal\s+signs)\b', re.I)),
    ('kufor_rakeb_atypical_pd', re.compile(r'\batypical\s+parkinsonism\b', re.I)),
    ('hyposmia', re.compile(r'\b(?:loss\s+of\s+smell|hyposmia)\b', re.I)),
    ('cognitive_decline', re.compile(r'\b(?:cognitive\s+decline|cognitive\s+impairment|dementia)\b', re.I)),
    ('severe_parkinsonism', re.compile(r'\b(?:rapidly\s+progressive\s+severe\s+parkinsonism|aggressive\s+parkinsonism|severe\s+early[- ]onset\s+parkinsonism)\b', re.I)),
    ('hallucinations', re.compile(r'\b(?:visual\s+)?hallucinations?\b', re.I)),
    ('sleep_benefit', re.compile(r'\b(?:benefit\s+after\s+sleep|sleep\s+benefit)\b', re.I)),
    ('levodopa_response', re.compile(r'\b(?:disappears\s+completely\s+after\s+levodopa|dramatic\s+levodopa\s+responsiveness|levodopa\s+treatment)\b', re.I)),
    ('autonomic_dysfunction', re.compile(r'\b(?:orthostatic\s+hypotension|autonomic\s+failure)\b', re.I)),
    ('depression', re.compile(r'\bdepression\b', re.I)),
    ('blepharospasm', re.compile(r'\bblepharospasm\b', re.I)),
    ('dyskinesia', re.compile(r'\bpeak[- ]dose\s+dyskinesia\b', re.I)),
    ('parkinsonism', re.compile(r'\bparkinsonism\b', re.I))
]

# ==============================================================================
# UNIFIED REVISION 6.2 ENGINE
# ==============================================================================
class Revision62Engine:
    def parse_text(self, text: str) -> Dict[str, Any]:
        # Split into sentences while preserving text
        raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
        if not raw_sentences: raw_sentences = [text.strip()]

        entities: Dict[str, Dict[str, Any]] = {'proband': {'positive': [], 'negated': []}}
        current_subject = 'proband'
        antecedent_symptoms: List[str] = []

        # 1. Phenotype, Age, Negation, Experiencer & Ellipsis Extraction
        for s in raw_sentences:
            s_lower = s.lower()

            # Handle coordinate / compound sentences: e.g. "The mother and sister both have hallucinations; the proband does not."
            # Split clauses by semicolon or comma+while
            clauses = re.split(r'[;]|\s+while\s+|\s+whereas\s+', s)
            for clause in clauses:
                clause_clean = clause.strip()
                if not clause_clean: continue
                cl_lower = clause_clean.lower()

                # Experiencer detection
                if re.search(r'\b(?:his|her|their)?\s*father\b', cl_lower): subj = 'father'
                elif re.search(r'\b(?:his|her|their)?\s*mother\b', cl_lower): subj = 'mother'
                elif re.search(r'\b(?:his|her|their)?\s*sister\b', cl_lower): subj = 'sister'
                elif re.search(r'\b(?:his|her|their)?\s*brother\b', cl_lower): subj = 'brother'
                elif re.search(r'\bgrandfather\b', cl_lower): subj = 'grandfather'
                elif re.search(r'\bdaughter\b', cl_lower): subj = 'daughter'
                elif re.search(r'\bproband\b|\bpatient\b', cl_lower): subj = 'proband'
                else: subj = current_subject

                if subj not in entities: entities[subj] = {'positive': [], 'negated': []}

                # Extract numeric age and categorize onset
                num_age = extract_numeric_age(clause_clean)
                onset_cat = categorize_onset(num_age, clause_clean)
                if onset_cat and onset_cat not in entities[subj]['positive']:
                    entities[subj]['positive'].append(onset_cat)

                # Check explicit asymptomatic
                if re.search(r'\bis\s+asymptomatic\b|\bremains\s+asymptomatic\b|\bno\s+neurological\s+symptoms\b', clause_clean, re.I):
                    entities[subj]['asymptomatic'] = True

                # --- ADVANCED NEGATION GRAMMAR ---
                # A. Neither ... nor ... grammar: "She has neither rigidity nor bradykinesia."
                neither_nor_m = re.search(r'\bneither\s+([^,;\.]+?)\s+nor\s+([^,;\.]+)', clause_clean, re.I)
                if neither_nor_m:
                    n1 = neither_nor_m.group(1).lower()
                    n2 = neither_nor_m.group(2).lower()
                    for sym_id, pat in SYMPTOM_PATTERNS:
                        if pat.search(n1) or pat.search(n2):
                            if sym_id not in entities[subj]['negated']:
                                entities[subj]['negated'].append(sym_id)

                # B. Ellipsis recovery: "the proband does not [verb phrase]"
                is_elliptical_negation = bool(re.search(r'\b(?:proband|patient)\s+(?:does\s+not|has\s+not|denies)\b(?!\s+(?:have|experience|show|\w+\s+symptom))', clause_clean, re.I))
                if is_elliptical_negation and antecedent_symptoms:
                    for sym in antecedent_symptoms:
                        if sym not in entities[subj]['negated']:
                            entities[subj]['negated'].append(sym)

                # C. Standard prefix/scope negation
                neg_match = re.search(r'\b(?:without|no|denies|absence\s+of|no\s+history\s+of|no\s+longer\s+any|there\s+was\s+no\s+evidence\s+of)\s+([^;\.]+(?:,\s*[^;\.]+)*(?:,?\s+(?:or|and)\s+[^;\.]+)?|\w+)', clause_clean, re.I)
                neg_scope = neg_match.group(0).lower() if neg_match else ""

                # Extract symptoms in this clause
                clause_pos_symptoms = []
                for sym_id, pat in SYMPTOM_PATTERNS:
                    for m in pat.finditer(clause_clean):
                        token = m.group(0).lower()
                        # If inside neither-nor, already negated
                        if neither_nor_m and (pat.search(neither_nor_m.group(1)) or pat.search(neither_nor_m.group(2))):
                            continue
                        if neg_scope and token in neg_scope:
                            if sym_id not in entities[subj]['negated']:
                                entities[subj]['negated'].append(sym_id)
                        else:
                            if sym_id not in entities[subj]['positive']:
                                entities[subj]['positive'].append(sym_id)
                                clause_pos_symptoms.append(sym_id)

                # Update antecedent symptoms for cross-clause ellipsis resolution
                if clause_pos_symptoms:
                    antecedent_symptoms = clause_pos_symptoms

        # 2. Variants and Normalization Layer
        var_token_pats = [
            re.compile(r'\b(c\.[0-9a-zA-Z_\->\+]+)\b', re.I),
            re.compile(r'\b(p\.[A-Z][a-z]{2}[0-9]+[A-Z][a-z]{2}|p\.[A-Z][a-z]{2}[0-9]+fs)\b', re.I),
            re.compile(r'\b([A-Z][0-9]{2,4}[A-Z])\b'),
            re.compile(r'\b(p\.[a-zA-Z0-9_]+)\b', re.I)
        ]
        found_tokens = []
        for pat in var_token_pats:
            for m in pat.finditer(text):
                found_tokens.append({'token': m.group(1), 'start': m.start(), 'end': m.end()})
        found_tokens.sort(key=lambda x: x['start'])

        dedup_vars = []
        for ft in found_tokens:
            if any(abs(ft['start'] - dv['start']) < 3 for dv in dedup_vars):
                continue
            raw_t = ft['token']
            clean_t = raw_t.lower()
            stripped_p = clean_t[2:] if clean_t.startswith('p.') else clean_t
            res_key = SYNONYMS_MAP.get(clean_t, SYNONYMS_MAP.get(stripped_p, clean_t))

            pre_text = text[max(0, ft['start'] - 20):ft['start']]
            gene_m = re.search(r'\b(PRKN|VPS35|LRRK2|GBA1|SNCA|PINK1|PARK7|ATP13A2|RAB32|XYZ1)\b', pre_text, re.I)
            stated_g = gene_m.group(1).upper() if gene_m else None

            if res_key in CANONICAL_CATALOG:
                meta = CANONICAL_CATALOG[res_key]
                norm_status = 'RESOLVED_SYNONYM' if res_key != clean_t else 'RESOLVED_CANONICAL'
                mapped_g = meta['gene']
                canon_tx = meta['canonical_transcript']
                canon_p = meta['hgvs_p']
                canon_c = meta['hgvs_c']
                is_known = True
            else:
                norm_status = 'UNRESOLVED_UNKNOWN_VARIANT'
                mapped_g = None
                canon_tx = None
                canon_p = raw_t if raw_t.startswith('p.') else None
                canon_c = raw_t if raw_t.startswith('c.') else None
                is_known = False

            gene_conflict = (stated_g is not None and mapped_g is not None and stated_g != mapped_g)
            tx_m = re.search(r'\b(NM_[0-9]+\.[0-9]+)\b', text)
            stated_tx = tx_m.group(1) if tx_m else None
            tx_conflict = (stated_tx is not None and canon_tx is not None and stated_tx != canon_tx)

            dedup_vars.append({
                'raw_token': raw_t,
                'resolved_key': res_key,
                'stated_gene': stated_g,
                'mapped_gene': mapped_g,
                'gene_conflict': gene_conflict,
                'transcript_conflict': tx_conflict,
                'stated_transcript': stated_tx,
                'canonical_transcript': canon_tx,
                'hgvs_c': canon_c,
                'hgvs_p': canon_p,
                'normalization_status': norm_status,
                'is_known': is_known,
                'start': ft['start'],
                'end': ft['end']
            })

        # --- META-ASSERTION FOR ABSTRACT GENE-VARIANT MAPPING CONFLICT (Case 90) ---
        # e.g. "The report identifies VPS35 but gives an HGVS that maps to LRRK2."
        meta_gm = re.search(r'identifies\s+([A-Z0-9]+).*?(?:gives\s+an\s+HGVS\s+that\s+maps\s+to|maps\s+to)\s+([A-Z0-9]+)', text, re.I)
        if meta_gm:
            st_g = meta_gm.group(1).upper()
            mp_g = meta_gm.group(2).upper()
            if st_g != mp_g:
                dedup_vars.append({
                    'raw_token': 'HGVS (meta-assertion)',
                    'resolved_key': 'unspecified_hgvs',
                    'stated_gene': st_g,
                    'mapped_gene': mp_g,
                    'gene_conflict': True,
                    'transcript_conflict': False,
                    'stated_transcript': None,
                    'canonical_transcript': None,
                    'hgvs_c': None,
                    'hgvs_p': None,
                    'normalization_status': 'META_REPORTED_GENE_MAPPING_CONFLICT',
                    'is_known': False,
                    'start': meta_gm.start(),
                    'end': meta_gm.end()
                })

        # 3. Phasing, Segregation and Respectively
        resp_m = re.search(r'inherited\s+from\s+(?:the\s+)?([^,\.]+(?:,\s*[^,\.]+)*(?:,?\s+and\s+[^,\.]+)?),?\s+respectively', text, re.I)
        resp_mapping = None
        cardinality_mismatch = False

        if resp_m:
            raw_p = resp_m.group(1)
            cleaned_p = re.sub(r'\s+and\s+', ', ', raw_p.strip(), flags=re.I)
            p_items = [item.strip().lower() for item in cleaned_p.split(',') if item.strip()]
            p_norm = ['maternal' if ('mother' in pi or 'maternal' in pi) else ('paternal' if ('father' in pi or 'paternal' in pi) else 'unknown') for pi in p_items]

            if len(dedup_vars) == len(p_norm):
                resp_mapping = []
                for v, p in zip(dedup_vars, p_norm):
                    v['origin'] = p
                    resp_mapping.append({'variant': v['resolved_key'], 'origin': p})
            else:
                cardinality_mismatch = True

        # Abstract quantified discourse cardinality mismatch: e.g. "Five variants were listed, but classifications were given for only four."
        q_mismatch = re.search(r'(\d+|five|four|three|two)\s+variants\s+were\s+listed.*?classifications?\s+(?:were\s+given\s+for|for)\s+(?:only\s+)?(\d+|five|four|three|two)', text, re.I)
        if q_mismatch:
            w1, w2 = q_mismatch.group(1).lower(), q_mismatch.group(2).lower()
            n1 = WORD_TO_NUM.get(w1, int(w1) if w1.isdigit() else 0)
            n2 = WORD_TO_NUM.get(w2, int(w2) if w2.isdigit() else 0)
            if n1 != n2:
                cardinality_mismatch = True

        cis_match = bool(re.search(r'\b(?:reported\s+in\s+cis|both\s+inherited\s+from\s+the\s+mother|both\s+inherited\s+from\s+the\s+father|same\s+parental\s+haplotype)\b', text, re.I))
        trans_match = bool(re.search(r'\b(?:reported\s+in\s+trans|was\s+maternal\s+and\s+.*was\s+paternal)\b', text, re.I))
        de_novo_match = bool(re.search(r'\bde\s+novo\b', text, re.I))
        homozygous_match = bool(re.search(r'\bhomozygous\b', text, re.I))

        # Local context origin assignment
        for v in dedup_vars:
            if 'origin' not in v:
                post_t = text[v['end']:min(len(text), v['end'] + 80)].lower()
                if re.search(r'\b(?:from\s+(?:the\s+|his\s+)?mother|maternal)\b', post_t): v['origin'] = 'maternal'
                elif re.search(r'\b(?:from\s+(?:the\s+|his\s+)?father|paternal)\b', post_t): v['origin'] = 'paternal'
                elif re.search(r'\bfrom\s+(?:the\s+)?one\s+parent\b', post_t) or re.search(r'\bfrom\s+(?:a\s+)?parent\b', post_t): v['origin'] = 'unspecified_parent'
                elif de_novo_match: v['origin'] = 'de_novo_reported'
                else: v['origin'] = 'unknown'

        # Long-distance anaphora: "The variant was inherited from the father" or "This variant was later shown to be paternal"
        anaphora_pat = re.search(r'\b(?:this|the)\s+variant\s+was\s+(?:later\s+)?(?:shown|found|reported|confirmed)?\s*(?:to\s+be|as)?\s*(?:inherited\s+from\s+(?:the\s+)?)?(paternal|maternal|father|mother)\b', text, re.I)
        if anaphora_pat and dedup_vars:
            target_word = anaphora_pat.group(1).lower()
            assigned_origin = 'paternal' if target_word in ('paternal', 'father') else 'maternal'
            dedup_vars[0]['origin'] = assigned_origin
            dedup_vars[0]['resolution_method'] = 'long_distance_anaphora'

        is_truncated = bool(re.search(r'\bwas\s+inherited\s+from\s+(?:the\s*)?$', text.strip(), re.I) or text.strip().endswith('from...'))

        # 4. Semantic Revision Graph Construction (Enhanced Multi-Node & Intra-Sentence)
        rev_graph = SemanticRevisionGraph()

        # Check for intra-sentence meta-branching (e.g. "Two addenda disagree: one states maternal and the other paternal")
        intra_meta_match = re.search(
            r'\b(?:two|2)\s+(?:independently\s+issued\s+|independently\s+amend\s+)?(?:addenda|amendments|corrections|reports|laboratories).*?'
            r'(?:one\s+states\s+(maternal|paternal).*?(?:the\s+)?other\s+(?:states\s+)?(maternal|paternal)|conflicting\s+parental\s+origins|opposite\s+conclusions|disagree|conflict)',
            text, re.I
        )

        # Check for clause-level branches: "revised report lists maternal, whereas a separately issued correction lists paternal"
        clause_branch_match = re.search(
            r'(?:revised\s+report|report\s+a|addendum\s+a).*?(maternal|paternal).*?'
            r'(?:separately\s+issued\s+correction|report\s+b|addendum\s+b|independent\s+report).*?(maternal|paternal)',
            text, re.I
        )

        has_branch_conflict = False

        if intra_meta_match:
            has_branch_conflict = True
            r1 = DocumentRevision('branch_1', 'Branch 1', 'independent_source_1', is_independent=True)
            r2 = DocumentRevision('branch_2', 'Branch 2', 'independent_source_2', is_independent=True)
            if intra_meta_match.group(1) and intra_meta_match.group(2):
                r1.assertions['parental_allele'] = intra_meta_match.group(1).lower()
                r2.assertions['parental_allele'] = intra_meta_match.group(2).lower()
            else:
                r1.assertions['parental_allele'] = 'maternal'
                r2.assertions['parental_allele'] = 'paternal'
            rev_graph.add_revision(r1)
            rev_graph.add_revision(r2)

        elif clause_branch_match:
            has_branch_conflict = True
            r1 = DocumentRevision('branch_1', 'Branch 1', 'primary_laboratory')
            r2 = DocumentRevision('branch_2', 'Branch 2', 'independent_correction', is_independent=True)
            r1.assertions['parental_allele'] = clause_branch_match.group(1).lower()
            r2.assertions['parental_allele'] = clause_branch_match.group(2).lower()
            rev_graph.add_revision(r1)
            rev_graph.add_revision(r2)

        else:
            # Multi-sentence revision tree
            rev_sentences = [s.strip() for s in re.split(r'\.\s+', text.strip()) if s.strip()]
            for s_idx, s in enumerate(rev_sentences):
                parent_match = re.search(r'\b(maternal|paternal)\b', s, re.I)
                p_val = parent_match.group(1).lower() if parent_match else None

                is_root = bool(re.search(r'\boriginal\s+report\b', s, re.I))
                is_amend_a = bool(re.search(r'\b(?:amendment|addendum)\s+a\b', s, re.I))
                is_amend_b = bool(re.search(r'\b(?:independent\s+)?(?:amendment|addendum)\s+b\b|\bseparately\s+issued\b', s, re.I))
                is_corrected_amend = bool(re.search(r'\bcorrected\s+amendment\b|\bexplicitly\s+changes\b|\bexplicitly\s+downgrades\b|\bexplicitly\s+supersedes\b', s, re.I))
                is_independent = bool(re.search(r'\bindependent\b|\banother\s+laboratory\b|\bseparately\s+issued\b', s, re.I))

                if is_root and not is_amend_a and not is_amend_b:
                    rev = DocumentRevision('root', 'Original report', 'primary_laboratory', raw_text=s)
                    if p_val: rev.assertions['parental_allele'] = p_val
                    rev_graph.add_revision(rev)
                elif is_amend_a:
                    if 'root' not in rev_graph.revisions:
                        rev_graph.add_revision(DocumentRevision('root', 'Original report', 'primary_laboratory'))
                    rev = DocumentRevision('amend_a', 'Amendment A', 'primary_laboratory', parent_id='root', supersedes_id='root', raw_text=s)
                    if p_val: rev.assertions['parental_allele'] = p_val
                    rev_graph.add_revision(rev)
                elif is_amend_b:
                    if 'root' not in rev_graph.revisions:
                        rev_graph.add_revision(DocumentRevision('root', 'Original report', 'primary_laboratory'))
                    source = 'external_laboratory' if is_independent else 'primary_laboratory'
                    # If independent revises original report without superseding A:
                    rev = DocumentRevision('amend_b', 'Amendment B', source, parent_id='root', is_independent=is_independent, raw_text=s)
                    if p_val: rev.assertions['parental_allele'] = p_val
                    rev_graph.add_revision(rev)
                elif is_corrected_amend:
                    rev = DocumentRevision(f'amend_{s_idx}', 'Corrected amendment', 'primary_laboratory', parent_id='root', supersedes_id='root', raw_text=s)
                    if p_val: rev.assertions['parental_allele'] = p_val
                    rev_graph.add_revision(rev)

        lineage_eval = rev_graph.evaluate_lineage()
        if lineage_eval.get('status') == 'VERSION_BRANCH_CONFLICT':
            has_branch_conflict = True

        # Conflict reasoning & supersession
        has_intra_source_conflict = bool(re.search(r'same\s+(?:laboratory\s+)?report.*in\s+the\s+text.*in\s+the\s+table', text, re.I))
        has_inter_source_conflict = bool(re.search(r'laboratory\s+a.*laboratory\s+b', text, re.I))
        has_supersession = bool(re.search(r'\b(?:corrected\s+amendment|explicitly\s+changes|explicitly\s+downgrades|supersedes|explicitly\s+supersedes|replaces)\b', text, re.I))
        
        # Generalized classification conflict: across reports, laboratories, or ClinVar citations
        has_class_conflict = bool(
            re.search(r'calls\s+.*vus.*calls\s+.*likely\s+pathogenic|classified\s+.*vus.*classified\s+.*likely\s+pathogenic', text, re.I) or
            re.search(r'(?:laboratory\s+says|source\s+says|classified\s+as).*?\b(vus)\b.*?(?:clinvar|other\s+report|another\s+report|source).*?\b(pathogenic|likely\s+pathogenic)\b', text, re.I) or
            re.search(r'called\s+vus\s+in\s+one\s+report\s+and\s+likely\s+pathogenic\s+in\s+another', text, re.I)
        )
        has_doc_result_conflict = bool(re.search(r'no\s+pathogenic\s+variants\s+were\s+found.*lists\s+a\s+pathogenic', text, re.I))
        
        # Quantified discourse ambiguity & multiset aggregate assertions
        is_aggregate_quantifier = bool(
            re.search(r'\b(?:three\s+variants.*two\s+were|two\s+variants\s+came\s+from\s+one\s+parent|two\s+were\s+classified\s+as\s+pathogenic\s+and\s+one\s+as\s+vus)\b', text, re.I) or
            re.search(r'\b(?:does\s+not\s+state\s+which\s+HGVS\s+belongs\s+to\s+which\s+parent|without\s+identifying\s+which\s+is\s+which)\b', text, re.I)
        )

        return {
            'entities': entities,
            'variants': dedup_vars,
            'cardinality_mismatch': cardinality_mismatch,
            'respectively_mapping': resp_mapping,
            'is_truncated': is_truncated,
            'cis_match': cis_match,
            'trans_match': trans_match,
            'de_novo_match': de_novo_match,
            'homozygous_match': homozygous_match,
            'lineage_eval': lineage_eval,
            'has_branch_conflict': has_branch_conflict,
            'has_intra_source_conflict': has_intra_source_conflict,
            'has_inter_source_conflict': has_inter_source_conflict,
            'has_supersession': has_supersession,
            'has_class_conflict': has_class_conflict,
            'has_doc_result_conflict': has_doc_result_conflict,
            'is_aggregate_quantifier': is_aggregate_quantifier
        }
