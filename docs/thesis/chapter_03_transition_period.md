# Chapter 3: The Tremors of Transition (1890-1914)

## Chapter Purpose
This chapter examines whether the years immediately preceding World War I show measurable prosodic destabilization before the full modernist break. It should determine whether the transition period is best described as gradual drift, early rupture, or a mixed regime.

## Core Claim To Test
The 1890-1914 interval should show rising entropy and syncopation relative to the Victorian baseline, but not yet the full rupture associated with the post-1914 period.

## Primary Evidence Inputs
- `data/processed/prosody_entropy_stanzas.csv`
- `data/processed/diachronic_series.csv`
- `data/processed/break_test_scan.csv`
- `data/processed/robustness_results.csv`

## Required Filters
Use publication years from 1890 through 1914, and compare them against the Victorian baseline and the later modernist period.

## Analyses To Report
### 1. Escalation Before Rupture
Measure whether entropy, latency variance, and syncopation rise in this intermediate period.

Questions to answer:
- Are there clear upward shifts relative to 1850-1890?
- Is the transition statistically smooth or jagged?
- Do the series suggest multiple local instabilities before the primary break?

### 2. Break-Test Contextualization
Use the breakpoint scan to evaluate whether pre-1914 years already show meaningful discontinuities.

Questions to answer:
- Does the scan suggest candidate breaks before 1914?
- Is 1914 still the strongest break year, or only the most visible one?
- How do shuffled-time controls affect confidence in the transition narrative?

### 3. Robustness Interpretation
Use `data/processed/robustness_results.csv` to show whether the transition pattern survives alternate binning and control checks.

## Planned Figures and Tables
Planned figures:
- Breakpoint scan from `docs/figures/breakpoint_timeline.png`
- A focused transition-period plot derived from `data/processed/diachronic_series.csv`

Planned tables:
- Transition vs Victorian mean comparison table
- Robustness summary table for pre-1914 results

## Interpretation Targets
This chapter should argue carefully for a pre-rupture tremor structure rather than forcing a simple binary between order and fracture. It should frame the transition period as analytically necessary for interpreting the larger shock.

## Writing Tasks Remaining
- Add literary-historical framing for industrialization and urbanization.
- Insert a paragraph clarifying whether the chapter supports punctuated equilibrium or escalating drift.
- Add direct references to the robustness controls used in the pipeline.
