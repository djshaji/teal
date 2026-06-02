# Data Protocol

## Scope
- Period: 1850-1950
- Languages: English
- Units: poem, stanza, line

## Source Registry
All acquisition candidates must be tracked in `data/metadata/sources.csv` before ingestion.

Minimum source-registry fields:
- source_id
- author
- title
- publication_year
- source_repository
- url
- filename
- rights_status
- acquisition_status
- notes

Recommended additional fields:
- country
- publication_venue
- form_label
- tier
- priority

## Required Metadata
- id
- author
- title
- publication_year
- source_repository
- form_label (if available)

## Acquisition Rules
- Prioritize Tier 1 repositories first (see `docs/protocol/corpus_sourcing_plan.md`).
- Balance sourcing across decades to avoid canon-heavy concentration.
- Log unresolved rights or access issues using `acquisition_status` and `notes`.
- Preserve provenance from source registry to metadata outputs.

## Quality Rules
- Preserve line breaks during ingestion.
- Remove paratext where detectable.
- Track OCR corrections in audit logs.
- Keep immutable snapshots under `data/interim` and `data/processed`.
- Maintain decade-level coverage and repository coverage summaries.
- Track duplicates and near-duplicates during corpus expansion.

## Data Quality Gates
- Metadata completeness >= 95% for required fields in `metadata_master.csv`.
- Source registry completeness >= 95% for minimum source-registry fields.
- At least one source represented in each targeted decade bin before full-model runs.
- OCR audit generated for each normalization run.

## Reproducibility
- Every script run should emit:
  - parameters
  - input/output paths
  - timestamp
  - script version or git commit hash

## Reporting Outputs
- `data/metadata/metadata_master.csv`
- `data/metadata/metadata_master.jsonl`
- `data/metadata/source_coverage_by_decade.csv`
- `data/metadata/source_coverage_by_repository.csv`
- `data/metadata/source_coverage_summary.md`
