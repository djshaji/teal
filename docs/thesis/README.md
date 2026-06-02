# Thesis Draft Workspace

Draft chapters in this directory and keep figure/table references aligned with `docs/figures` and `docs/tables`.

The chapter files in this folder are now scaffolded against the current pipeline outputs so writing can proceed in parallel with analysis.

## Current Drafting Workflow
1. Run the pipeline stages that generate the chapter's evidence.
2. Update the corresponding chapter file with observed results, interpretation, and citations.
3. Freeze figure references only after the associated CSV outputs are stable.
4. Move implementation detail that is too low-level for the main text into appendices or a reproducibility note.

## Suggested chapter files
- `chapter_01_methods.md`
- `chapter_02_victorian_baseline.md`
- `chapter_03_transition_period.md`
- `chapter_04_modernist_fracture.md`
- `chapter_05_conclusion.md`

## Evidence Map
- Chapter 1 should draw mainly from pipeline design, quality controls, and methodological outputs.
- Chapter 2 should use baseline-era slices from `data/processed/prosody_entropy_stanzas.csv` and `data/processed/diachronic_series.csv`.
- Chapter 3 should focus on pre-1914 drift and any intermediate break behavior.
- Chapter 4 should center on rupture evidence from CCA, break tests, and robustness outputs.
- Chapter 5 should synthesize findings and describe infrastructure release, reproducibility, and future extensions.
