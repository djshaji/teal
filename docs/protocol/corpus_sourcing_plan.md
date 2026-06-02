# Corpus Sourcing Plan

## Purpose
This document defines how the poetry corpus for 1850-1950 will be acquired, screened, logged, and balanced before downstream preprocessing and analysis.

## Collection Goals
- Build a diachronic English poetry corpus spanning 1850-1950.
- Preserve enough bibliographic metadata to support year-level and source-level aggregation.
- Avoid overreliance on a narrow canonical set of poets.
- Favor texts that preserve lineation and stanza boundaries.

## Priority Repositories

### Tier 1: Primary Acquisition Targets
Use these first because they offer the best balance of access, metadata quality, and text usability.

- HathiTrust Digital Library
  - Use for volume-level poetry collections and anthologies with stable bibliographic metadata.
  - Best for broad diachronic coverage and publication metadata.
- Project Gutenberg
  - Use for clean public-domain text when lineation is preserved.
  - Best for pilot data, script debugging, and baseline corpus seeding.
- Internet Archive
  - Use for scans and OCR when text is unavailable elsewhere.
  - Best for filling decade and author gaps.
- University-hosted text archives
  - Use when they provide curated editions with reliable dating and text structure.

### Tier 2: Secondary Gap-Filling Targets
Use these when Tier 1 leaves decade, venue, or author gaps.

- Periodical archives with poetry sections
- Specialized digital poetry collections
- Institutional repositories with public-domain verse volumes

### Tier 3: Manual or Restricted Targets
Reserve for targeted supplementation only.

- Access-restricted databases requiring manual retrieval
- Archives with unstable OCR and heavy paratext contamination
- Sites with unclear reuse conditions

## Inclusion Criteria
A text should be included when it satisfies most of the following:
- Publication year is known or can be reliably inferred.
- The text is in English.
- Poetic lineation is preserved or recoverable.
- Bibliographic metadata includes at least author, title, source, and year.
- Rights status allows research use and local storage for analysis.
- OCR quality is sufficient for correction without reconstructing the poem manually.

## Exclusion Rules
Exclude or quarantine texts when:
- Publication year is absent and cannot be inferred with confidence.
- The text is prose, mixed genre, or heavily editorialized.
- Line breaks are destroyed beyond practical recovery.
- OCR noise overwhelms the poem.
- The same poem appears in near-duplicate form without a clear versioning reason to retain both.

## Sampling Strategy

### Temporal Balancing
- Build acquisition targets by decade from the 1850s through the 1940s.
- Monitor counts by decade continuously during ingestion.
- Use targeted acquisition to fill thin decades before expanding already dense periods.

### Canonical Bias Control
- Separate acquisition into:
  - canonical authors
  - mid-tier anthologized authors
  - minor or periodical poets
- Do not allow the corpus to be dominated by a small cluster of highly anthologized writers.

### Venue Diversity
Track and balance by source type when possible:
- single-author collections
- anthologies
- periodicals
- collected editions

## Minimum Metadata Fields
Every candidate source entry in `data/metadata/sources.csv` should include:
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

## Acquisition Workflow
1. Register candidate texts in `data/metadata/sources.csv`.
2. Assign repository tier and acquisition priority.
3. Fetch or copy files into `data/raw/`.
4. Run metadata extraction with `scripts/ingest/build_metadata.py`.
5. Review decade coverage and missing metadata.
6. Run OCR cleanup and stanza segmentation.
7. Log exclusions, duplicates, and unresolved metadata problems.

## Quality Checks During Acquisition
- Year coverage by decade
- Source coverage by repository
- Canonical vs non-canonical balance
- Duplicate and near-duplicate detection
- OCR failure rate
- Missing metadata rate

## Reporting Outputs
The data workstream should eventually produce:
- source inventory report
- decade coverage report
- sampling bias report
- exclusion log
- metadata completeness summary

## Immediate Next Actions
- Populate `data/metadata/sources.csv` with an initial pilot set from Project Gutenberg and one scan-based repository.
- Establish target counts per decade.
- Add `rights_status` and `acquisition_status` fields to the source registry if not already present.
- Begin with texts that preserve line breaks for the first end-to-end validation run.
