# Chapter 2: The Victorian Baseline (1850-1890)

## Chapter Purpose
This chapter establishes the prosodic and affective baseline against which later rupture is measured. Its task is to demonstrate that mid-Victorian poetic production exhibits lower rhythmic variability, lower prosodic entropy, and a more stable relationship between form and affect than later periods.

## Core Claim To Test
Victorian poetry in the corpus should present relatively constrained stress organization and lower syncopation, producing a measurable low-entropy baseline prior to the transition into modernist fragmentation.

## Primary Evidence Inputs
- `data/processed/prosody_entropy_stanzas.csv`
- `data/processed/diachronic_series.csv`
- `data/processed/scansion_stanzas.csv`
- `data/processed/poem_summary.csv`

## Required Filters
Use publication years from 1850 through 1890 inclusive.

## Analyses To Report
### 1. Baseline Rhythmic Regularity
Report average stanza-level prosodic entropy, mean stress density, and latency behavior for the Victorian slice.

Questions to answer:
- How low is the Victorian average entropy relative to the rest of the corpus?
- Do inferred meters cluster around iambic regularity more often in this period?
- Are line-level syncopation rates comparatively constrained?

### 2. Stability of Formal Expectations
Describe how inferred meter and syllable counts behave within the Victorian corpus.

Questions to answer:
- Do stanza means show low dispersion?
- Are latency variance values concentrated in a narrow range?
- Does the baseline support the claim that regularity functioned as a technology of containment?

### 3. Baseline Figures and Tables
Planned figures:
- Time-slice or filtered version of `docs/figures/entropy_by_year.png`

Planned tables:
- Baseline summary table for Victorian rows from `data/processed/prosody_entropy_stanzas.csv`
- Distribution summary of inferred meter from `data/processed/scansion_stanzas.csv`

## Interpretation Targets
This chapter should not overclaim. Its function is to establish the benchmark against which later change becomes legible. The prose should move from descriptive statistics to literary-historical interpretation only after the baseline is clearly quantified.

## Writing Tasks Remaining
- Add direct citations from Victorian prosody scholarship.
- Insert one close-reading bridge paragraph showing how macro-level regularity complements canonical examples.
- Add a compact table comparing Victorian baseline metrics against whole-corpus averages.
