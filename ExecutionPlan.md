# Execution Plan: Diachronic Shifts in English Poetic Prosody (1850-1950)

## Purpose
This document converts the research proposal into an implementation roadmap with concrete deliverables for:
1. Writing tools and scripts
2. Performing the full analysis pipeline
3. Writing the thesis

## Project Outcomes
- A reproducible dual-track computational pipeline:
  - Rhythmic Track (prosodic parsing, latency, entropy)
  - Affective Track (stanza-level valence/arousal modeling)
- Diachronic statistical findings (correlation + structural break analysis)
- Thesis chapters with figures, tables, and methodological appendix
- Release-ready codebase with documentation and reproducibility scripts

## Recommended Repository Structure

```text
teal/
  data/
    raw/
    interim/
    processed/
    metadata/
  docs/
    protocol/
    thesis/
    figures/
    tables/
  notebooks/
  scripts/
    ingest/
    clean/
    prosody/
    affect/
    stats/
    viz/
    utils/
  src/
    teal/
      config/
      ingest/
      normalize/
      prosody/
      affect/
      stats/
      viz/
  tests/
    unit/
    integration/
  models/
    checkpoints/
  outputs/
    runs/
  environment/
  Makefile
  README.md
```

## Tooling Stack
- Language: Python 3.11+
- Environment: conda or venv + pip-tools/uv
- Data + NLP: pandas, polars (optional), numpy, spacy, transformers, datasets, sentencepiece
- Prosody: pronouncing / cmudict, custom scansion module, numba (optional)
- Statistics: scipy, statsmodels, scikit-learn, ruptures (Bai-Perron style alternatives)
- Visualization: matplotlib, seaborn, plotly (optional)
- Reproducibility: hydra or pydantic settings, DVC (optional), pre-commit, pytest
- Documentation: MkDocs or plain Markdown + thesis folder

## Workstreams

### A. Data Workstream
1. Source corpus from HathiTrust, Project Gutenberg, Internet Archive, Poetry Foundation where permitted, university textbases, and periodical archives.
  - Build a source priority list with three tiers:
    - Tier 1: public-domain, machine-readable collections with stable bibliographic metadata
    - Tier 2: OCR-derived scans with acceptable page-quality and recoverable lineation
    - Tier 3: restricted or manually intensive archives reserved for targeted gap-filling
  - Use stratified acquisition by decade (1850s through 1940s) to avoid overconcentration in canonical late-Victorian and high-Modernist peaks.
  - Track every candidate text in `data/metadata/sources.csv` with source URL, repository, rights status, year, author, title, and acquisition status.
  - Prioritize collections that preserve poetic lineation and publication-year metadata.
  - Maintain a gap log for underrepresented decades, regions, and publication venues.
2. Build metadata schema (author, year, publication venue, country, form tags).
3. Run OCR correction and normalization (orthography mapping policy).
4. Remove paratext and enforce stanza/line boundary integrity.
5. Export versioned datasets:
   - corpus_clean.parquet
   - stanza_units.parquet
   - metadata_master.csv

Acquisition protocol:
- See `docs/protocol/corpus_sourcing_plan.md` for repository priorities, inclusion criteria, exclusion rules, and sampling strategy.
- For manual acquisition runs, use `docs/protocol/manual_download_workflow.md` and `data/metadata/manual_download_urls.txt`.

Done criteria:
- >= 80% of planned corpus ingested with valid metadata
- Sampling bias report generated
- Data quality audit pass (defined checks below)

### B. Rhythmic Track Workstream
1. Implement grapheme-to-phoneme pipeline with OOV fallback.
2. Implement metrical grid inference per poem.
3. Compute per-line/per-stanza latency features:
   - delta_t
   - latency mean/variance
   - syncopation indices
4. Compute prosodic entropy per stanza and aggregate per text/year.
5. Validate against hand-scanned gold subset.

Done criteria:
- Parser runs end-to-end on full staged corpus
- Gold subset agreement threshold met (target metric pre-registered)
- Feature tables exported to processed layer

### C. Affective Track Workstream
1. Define stanza-level affect labels or proxy datasets for adaptation.
2. Build baseline model (lexicon + simple classifier) for comparison.
3. Fine-tune transformer model for valence/arousal outputs.
4. Evaluate with held-out set and error analysis by period.
5. Export affect vectors per stanza and text aggregates.

Done criteria:
- Baseline and final model benchmarked
- Error taxonomy documented (irony, inversion, archaic usage)
- Inference pipeline reproducible by command

### D. Synthesis + Statistical Inference Workstream
1. Join rhythmic and affective feature spaces on stanza/text/time keys.
2. Run canonical correlation analysis (CCA).
3. Run temporal structural break detection (Chow, Bai-Perron or robust alternatives).
4. Test robustness:
   - alternative period bins
   - author-fixed effects
   - form-specific subsets
5. Produce publication-quality plots and summary tables.

Done criteria:
- Primary hypothesis tests complete
- Sensitivity analyses complete
- Results package generated in outputs/runs/<timestamp>/

### E. Thesis Writing Workstream
1. Freeze chapter templates and required figure/table inventory.
2. Draft methods chapter alongside implementation (not after).
3. Draft empirical chapters in sequence by analysis readiness.
4. Run final consistency pass (claims, citations, reproducibility links).
5. Produce submission package.

Done criteria:
- Full thesis draft complete
- Internal review comments resolved
- Submission-ready PDF + appendix + code release note

## Milestone Plan (12-Month Model)

### M1 (Month 1): Project Bootstrap
- Initialize repository structure, environment, CI, lint/test tooling
- Write data protocol and annotation policy
- Milestone output: technical design doc + reproducibility checklist

### M2 (Months 2-3): Corpus Build
- Ingest corpus, metadata enrichment, OCR cleanup, stanza segmentation
- Milestone output: v1 cleaned corpus + quality audit report

### M3 (Months 4-5): Prosodic Engine v1
- Implement and validate scansion + latency/entropy extraction
- Milestone output: rhythmic feature tables + validation report

### M4 (Months 6-7): Affective Engine v1
- Build baseline + fine-tuned model, run evaluation and error analysis
- Milestone output: affect feature tables + model card

### M5 (Months 8-9): Integration and Statistical Testing
- CCA, break tests, robustness checks, core figures
- Milestone output: analysis report with all primary findings

### M6 (Months 10-11): Thesis Drafting
- Chapter-by-chapter drafting with frozen figures/tables
- Milestone output: full thesis draft for supervisor review

### M7 (Month 12): Finalization and Release
- Revisions, appendices, reproducibility package, defense prep
- Milestone output: submission package + code/data release

## Script and Command Plan

### Initial script map
- scripts/ingest/fetch_sources.py
- scripts/ingest/build_metadata.py
- scripts/clean/ocr_correct.py
- scripts/clean/segment_stanzas.py
- scripts/prosody/run_scansion.py
- scripts/prosody/compute_latency.py
- scripts/prosody/compute_entropy.py
- scripts/affect/train_baseline.py
- scripts/affect/train_transformer.py
- scripts/affect/infer_affect.py
- scripts/stats/run_cca.py
- scripts/stats/run_break_tests.py
- scripts/stats/run_robustness.py
- scripts/viz/build_figures.py

### Reproducible command interface
Use a Makefile or task runner:
- make ingest
- make clean
- make prosody
- make affect-train
- make affect-infer
- make stats
- make viz
- make thesis-report

Each command should:
- read from config files only
- write immutable timestamped outputs
- emit a run manifest (versions, params, input hashes)

## Data Quality Gates
- Metadata completeness >= 95% for required fields (author, year, source)
- OCR residual error estimate below pre-defined threshold
- Stanza boundary integrity checks pass on sampled validation set
- Duplicate and near-duplicate text detection report generated
- Corpus period distribution report (by decade and source)

## Evaluation Plan

### Rhythmic Track
- Gold subset inter-annotator benchmark
- Agreement metrics on stress patterns and inferred meter
- Stability checks across orthography normalization variants

### Affective Track
- Valence/arousal regression metrics (or ordinal metrics if discretized)
- Temporal drift analysis by decade
- Error clusters: irony, war lexicon, archaic semantics

### Joint Model
- Canonical correlation strength and significance
- Breakpoint confidence intervals
- Counterfactual checks (randomized time labels, shuffled controls)

## Thesis Production Plan

### Chapter sequence
1. Architecture and Methods
2. Victorian Baseline (1850-1890)
3. Transition Period (1890-1914)
4. Modernist Fracture (1914-1950)
5. Conclusion and Open Humanities Infrastructure

### Writing cadence
- Weekly output target: 1200-1800 polished words
- Biweekly figure freeze cycle
- Monthly supervisor memo: completed analyses, open risks, next tasks

## Risk Register and Mitigations
- Risk: uneven corpus quality by decade
  - Mitigation: stratified sampling + quality-weighted analyses
- Risk: scansion errors on OOV vocabulary
  - Mitigation: fallback G2P + manual audits on high-impact samples
- Risk: affect model overfits modern language patterns
  - Mitigation: domain adaptation + period-aware validation splits
- Risk: timeline slip due to model iteration loops
  - Mitigation: milestone gates with baseline-first policy

## Definition of Done (Global)
- End-to-end pipeline can be run from raw data to final figures by scripted commands
- All key claims in thesis trace to reproducible outputs
- Statistical tests and robustness checks documented
- Thesis manuscript complete with bibliography, appendices, and methods transparency

## Immediate Next 14 Days
1. Create repository directories and base config files.
2. Set up environment and CI (lint/test hooks).
3. Implement ingest + metadata scripts with one source connector.
4. Draft data protocol and annotation policy.
5. Build minimal prosody prototype on a small pilot corpus.
6. Start Chapter 1 methods draft in parallel with implementation notes.
