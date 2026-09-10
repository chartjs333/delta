import re

# Regression fixtures intentionally keep long clinical phrases intact.
# ruff: noqa: E501

# Regression Suite: Word-Boundary Clinical Tokenizer vs Substring Leakage
REGEX_RULES = [
    (
        r"\b(?:supranuclear vertical gaze palsy|supranuclear gaze palsy|vertical gaze palsy|gaze palsy)\b",
        "vertical_gaze_palsy",
    ),
    (
        r"\b(?:pyramidal signs|spasticity|extensor plantar|spastic paraplegia|hyperreflexia)\b",
        "spasticity_pyramidal_signs",
    ),
    (
        r"\b(?:cognitive decline|cognitive impairment|dementia|executive dysfunction)\b",
        "cognitive_decline",
    ),
    (
        r"\b(?:diurnal fluctuation|diurnal variation|worsening in the evening|worsening in evening)\b",
        "diurnal_fluctuation",
    ),
    (r"\b(?:sleep benefit)\b", "sleep_benefit"),
    (r"\b(?:levodopa[- ]induced dyskinesia|peak[- ]dose dyskinesia|dyskinesia)\b", "dyskinesia"),
    (r"\b(?:hyposmia|loss of smell|profound hyposmia)\b", "hyposmia"),
    (r"\b(?:hallucinations|visual hallucinations)\b", "hallucinations"),
    (r"\b(?:resting tremor|rest tremor|pill[- ]rolling tremor|tremor)\b", "tremor_rest"),
    (r"\b(?:bradykinesia|slowness of movement|slowness)\b", "bradykinesia"),
    (r"\b(?:rigidity|cogwheel rigidity|stiffness)\b", "rigidity"),
    (r"\b(?:dystonia|limb dystonia|focal dystonia)\b", "dystonia"),
    (r"\b(?:blepharospasm)\b", "blepharospasm"),
    (r"\b(?:atypical parkinsonism|kufor[- ]rakeb)\b", "kufor_rakeb_atypical_pd"),
    # Strict Gene Names (Must never match inside 'parkinson' or 'parkinsonism')
    (r"\b(?:atp13a2)\b", "atp13a2"),
    (r"\b(?:gch1)\b", "gch1"),
    (r"\b(?:prkn|parkin(?!\w))\b", "prkn"),
    (r"\b(?:pink1)\b", "pink1"),
    (r"\b(?:park7|dj-?1)\b", "park7"),
    (r"\b(?:lrrk2)\b", "lrrk2"),
    (r"\b(?:gba1|gba(?!\w))\b", "gba1"),
    (r"\b(?:snca)\b", "snca"),
    (r"\b(?:vps35)\b", "vps35"),
    (r"\b(?:rab32)\b", "rab32"),
]


def extract_tokens(text: str):
    lower = text.lower()
    extracted = []
    for pattern, tok in REGEX_RULES:
        if re.search(pattern, lower, re.I):
            if tok not in extracted:
                extracted.append(tok)
    return extracted


NON_PRKN_CHALLENGE_TEXTS = [
    (
        "ATP13A2",
        "Juvenile patient, 16 years old, atypical parkinsonism with severe spasticity, vertical gaze palsy, dementia.",
    ),
    (
        "ATP13A2",
        "Young adult female, rigid-akinetic parkinsonism, extensive pyramidal signs, spastic paraplegia, early dementia.",
    ),
    (
        "GCH1",
        "Child, 7 years old female, lower limb dystonia with marked diurnal fluctuation, levodopa response.",
    ),
    (
        "GCH1",
        "Young girl, 9yo, focal limb dystonia, marked diurnal variation, dramatic complete relief with low dose levodopa.",
    ),
    (
        "PINK1",
        "Young adult, 35 years old female, early-onset parkinsonism, psychiatric disturbance with severe depression and anxiety.",
    ),
    (
        "PINK1",
        "Male, 38 years old, early-onset bradykinesia, rigidity, postural instability, autosomal recessive, sleep benefit.",
    ),
    (
        "PARK7",
        "Male, 30 years old, early-onset atypical parkinsonism, focal dystonia, brisk reflexes, blepharospasm.",
    ),
    (
        "PARK7",
        "Female, 33 years old, early-onset rigid-akinetic syndrome, blepharospasm, autosomal recessive.",
    ),
    (
        "LRRK2",
        "Male, 65 years old, late-onset unilateral resting tremor, cogwheel rigidity, bradykinesia, autosomal dominant.",
    ),
    (
        "LRRK2",
        "Female, 68 years old, classic late-onset asymmetric resting tremor, bradykinesia, levodopa response.",
    ),
    (
        "GBA1",
        "Male, 58 years old, parkinsonism with profound hyposmia, early visual hallucinations, cognitive decline.",
    ),
    (
        "GBA1",
        "Female, 62 years old, late-onset parkinsonism, early executive dysfunction, dementia, severe loss of smell.",
    ),
    (
        "SNCA",
        "Male, 46 years old, early-onset severe aggressive parkinsonism, prominent early dementia, hallucinations.",
    ),
    (
        "SNCA",
        "Female, 44 years old, rapidly progressive parkinsonism, early autonomic failure, severe cognitive decline.",
    ),
    (
        "VPS35",
        "Male, 54 years old, familial late-onset parkinsonism, prominent resting tremor, preserved cognition.",
    ),
    (
        "VPS35",
        "Female, 57 years old, classic Parkinson's disease, unilateral pill-rolling tremor, cogwheel rigidity.",
    ),
    (
        "RAB32",
        "Male, 62 years old, autosomal dominant late-onset Parkinson's disease, resting tremor, bradykinesia.",
    ),
    (
        "RAB32",
        "Female, 64 years old, typical late-onset levodopa-responsive tremor-predominant parkinsonism, normal cognition.",
    ),
]


def test_zero_prkn_contamination_in_non_prkn_challenge_texts():
    """Regression test ensuring that 'parkin' never matches inside 'parkinson' or 'parkinsonism'."""
    for _expected_gene, text in NON_PRKN_CHALLENGE_TEXTS:
        tokens = extract_tokens(text)
        assert "prkn" not in tokens, (
            f"REGRESSION DETECTED: 'prkn' was incorrectly extracted from non-PRKN text: '{text}'. "
            f"Extracted tokens: {tokens}"
        )


def test_explicit_prkn_extraction():
    """Verifies that actual PRKN mentions and isolated 'parkin' are correctly extracted."""
    assert "prkn" in extract_tokens("Confirmed PRKN mutation in patient with early onset tremor.")
    assert "prkn" in extract_tokens("Biallelic parkin gene deletion confirmed by MLPA.")
    assert "prkn" not in extract_tokens(
        "Atypical parkinsonism with vertical supranuclear gaze palsy."
    )
