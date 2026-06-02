# Chapter 4: The Modernist Fracture (1914-1950)

## Chapter Purpose
This chapter is the empirical center of the dissertation. It should demonstrate whether the post-1914 corpus exhibits the strongest levels of prosodic entropy, syncopation, and structural instability, and whether those features align with affective intensification.

## Core Claim To Test
The post-1914 period should show the clearest break in the corpus, with higher entropy and stronger co-variation between structural disruption and affective intensity than earlier periods.

## Primary Evidence Inputs
- `data/processed/prosody_entropy_stanzas.csv`
- `data/processed/diachronic_series.csv`
- `data/processed/cca_scores.csv`
- `data/processed/cca_loadings.csv`
- `data/processed/break_test_scan.csv`
- `data/processed/robustness_results.csv`

## Required Filters
Use publication years from 1914 through 1950 inclusive.

## Analyses To Report
### 1. Rupture Magnitude
Show whether post-1914 entropy and latency measures exceed earlier periods.

Questions to answer:
- How large is the increase relative to the Victorian baseline?
- Which specific prosodic features carry the largest change?
- Do the strongest increases cluster around wartime and immediate postwar years?

### 2. Structure and Affect
Interpret canonical correlation results.

Questions to answer:
- Which prosodic variables load most strongly in the first canonical component?
- Does the relationship support the claim that formal rupture and affective disturbance are linked?
- If proxy affect was used in exploratory runs, how should that limit interpretation until the final affect model is complete?

### 3. Breakpoint and Control Evidence
Integrate break-test and robustness outputs to show that the rupture is not a trivial artifact of aggregation.

Questions to answer:
- Is the strongest break near 1914?
- Do shuffled-time controls weaken or reinforce the substantive interpretation?
- Do high-syncopation subsets show stronger disruption than lower-syncopation subsets?

## Planned Figures and Tables
Planned figures:
- `docs/figures/entropy_by_year.png`
- `docs/figures/cca_loadings.png`
- `docs/figures/breakpoint_timeline.png`

Planned tables:
- Canonical loadings summary from `data/processed/cca_loadings.csv`
- Breakpoint ranking table from `data/processed/break_test_scan.csv`
- Robustness summary table from `data/processed/robustness_results.csv`

## Interpretation Targets
This chapter must move from measurement to argument. It should explain why these quantitative outputs support the thesis claim that modernist form was not merely stylistic innovation, but a measurable structural adaptation to historical trauma.

## Writing Tasks Remaining
- Replace any proxy-affect language with final affect-model results when available.
- Add a short interpretive bridge to canonical modernist poems used as illustrative cases.
- Tie the empirical results back to the dissertation's central theoretical vocabulary: rupture, latency, entropy, and affective reconfiguration.
