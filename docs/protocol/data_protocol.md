# Data Protocol

## Scope
- Period: 1850-1950
- Languages: English
- Units: poem, stanza, line

## Required Metadata
- id
- author
- title
- publication_year
- source_repository
- form_label (if available)

## Quality Rules
- Preserve line breaks during ingestion.
- Remove paratext where detectable.
- Track OCR corrections in audit logs.
- Keep immutable snapshots under `data/interim` and `data/processed`.

## Reproducibility
- Every script run should emit:
  - parameters
  - input/output paths
  - timestamp
  - script version or git commit hash
