# Chapter 1: Architecture and Methods

## Chapter Purpose
This chapter explains how the project converts a historical poetry corpus into reproducible evidence about diachronic changes in prosody and affect between 1850 and 1950. It should establish the technical validity of the corpus pipeline, justify the operational definitions of latency and entropy, and document the statistical procedures used to test for structural rupture.

## Core Argument
The methods stack treats poetry as a structured acoustic-semantic signal rather than as flattened lexical text. The pipeline therefore separates corpus construction, OCR correction, stanza segmentation, scansion, latency estimation, entropy estimation, affect modeling, and multivariate inference into distinct stages, each with explicit outputs and validation points.

## Pipeline Overview
### 1. Corpus Ingestion and Metadata
The project begins by registering source texts in `data/metadata/sources.csv` and collecting files into `data/raw/` through the ingestion layer.

Primary scripts:
- `scripts/ingest/fetch_sources.py`
- `scripts/ingest/build_metadata.py`

Primary outputs:
- `data/metadata/metadata_master.csv`
- `data/metadata/metadata_master.jsonl`

Key methodological point:
Metadata is treated as part of the analytical infrastructure, not as administrative overhead. Publication year, source repository, and poem identity are necessary to support diachronic aggregation and later break tests.

### 2. Normalization and Segmentation
The preprocessing layer corrects common OCR artifacts, removes likely page-number noise, normalizes typographic variation, and segments each poem into stanza and line units.

Primary scripts:
- `scripts/clean/ocr_correct.py`
- `scripts/clean/segment_stanzas.py`

Primary outputs:
- `data/interim/ocr_audit.csv`
- `data/processed/stanza_units.csv`
- `data/processed/line_units.csv`
- `data/processed/poem_summary.csv`

Key methodological point:
The unit of analysis must remain explicit throughout the thesis. The project moves between line-level, stanza-level, and year-level aggregation, and each inferential claim should identify the level at which evidence is computed.

### 3. Prosodic Feature Extraction
The prosodic engine estimates stress patterns, infers candidate meter, computes latency between observed and expected stress positions, and calculates prosodic entropy.

Primary scripts:
- `scripts/prosody/run_scansion.py`
- `scripts/prosody/compute_latency.py`
- `scripts/prosody/compute_entropy.py`

Primary outputs:
- `data/processed/scansion_lines.csv`
- `data/processed/scansion_stanzas.csv`
- `data/processed/latency_lines.csv`
- `data/processed/latency_stanzas.csv`
- `data/processed/prosody_entropy_stanzas.csv`
- `data/processed/diachronic_series.csv`

Operational definitions to formalize in final prose:
- Rhythmic latency: deviation between observed and expected stress onsets.
- Syncopation rate: proportion of stress-pattern mismatch relative to the inferred template.
- Prosodic entropy: Shannon-based uncertainty calculated from stress bits and stress transitions.

### 4. Affective Modeling
The affective track is designed to assign stanza-level valence and arousal values that can be aligned with prosodic features. The current codebase already reserves training and inference entry points, and later drafts of this chapter should replace proxy-language with the finalized model description once the affect stage is implemented end-to-end.

Reserved scripts:
- `scripts/affect/train_baseline.py`
- `scripts/affect/train_transformer.py`
- `scripts/affect/infer_affect.py`

Expected output:
- `data/processed/affect_features.csv`

Interim note for drafting:
Until the final affect model is complete, any exploratory correlation using proxy affect must be clearly labeled as bootstrap analysis rather than as the dissertation's definitive evidence.

### 5. Multivariate Statistics and Robustness
The inferential layer tests whether prosodic disruption and affective intensity co-vary and whether the temporal series exhibits a structural break around historically meaningful dates.

Primary scripts:
- `scripts/stats/run_cca.py`
- `scripts/stats/run_break_tests.py`
- `scripts/stats/run_robustness.py`

Primary outputs:
- `data/processed/cca_scores.csv`
- `data/processed/cca_loadings.csv`
- `data/processed/break_test_scan.csv`
- `data/processed/robustness_results.csv`

Statistical logic to explain:
- Canonical correlation analysis tests joint structure between prosodic and affective feature spaces.
- Chow-style breakpoint scanning identifies candidate rupture years in the diachronic series.
- Robustness checks compare historical bins, subset conditions, and shuffled-time controls.

## Validation and Quality Gates
This section should document the minimal evidentiary standard for each stage.

### Data Quality
- Metadata completeness for author, title, publication year, and repository.
- OCR audit review using `data/interim/ocr_audit.csv`.
- Manual sampling of stanza integrity after segmentation.

### Prosodic Quality
- Spot checks on stress-pattern plausibility.
- Comparison between inferred meter and known regular verse samples.
- Inspection of whether latency and entropy behave sensibly on regular versus irregular lines.

### Statistical Quality
- Minimum sample thresholds before running CCA.
- Explicit labeling of exploratory proxy-affect runs.
- Control analyses from `data/processed/robustness_results.csv`.

## Figures and Tables To Reference
Planned figures:
- `docs/figures/entropy_by_year.png`
- `docs/figures/cca_loadings.png`
- `docs/figures/breakpoint_timeline.png`

Planned tables:
- Metadata summary table from `data/metadata/metadata_master.csv`
- Stanza/line count summary from `data/processed/poem_summary.csv`
- Robustness summary table from `data/processed/robustness_results.csv`

## Writing Tasks Remaining
- Replace all provisional script-path references with prose in the final thesis draft while keeping the appendix reproducible.
- Add a short subsection justifying heuristic fallback scansion where dictionary coverage is incomplete.
- Add a subsection describing how the affect model is trained and validated once that stage is finalized.
- Add citations tying the statistical design back to computational literary studies and historical prosody research.
