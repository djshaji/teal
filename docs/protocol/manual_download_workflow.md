# Manual Download Workflow

## Purpose
This workflow turns the source registry into a manual corpus acquisition queue for the data workstream.

## Input Registry
- Source queue: `data/metadata/sources.csv`
- Each row includes a URL you can open and download from manually.

## Step-by-Step Process
1. Open `data/metadata/sources.csv`.
2. Filter `acquisition_status=manual_queue`.
3. Sort by:
   - `priority` (high first)
   - `publication_year` (oldest to newest within priority)
4. Open each row's `url` in a browser.
5. Download the best available plain-text or OCR text file preserving line breaks.
6. Save into `data/raw/` using the row's `filename`.
7. Update the row:
   - `acquisition_status=downloaded`
   - add notes on edition/source quality.

## Status Values
- `manual_queue`: not downloaded yet
- `downloaded`: file acquired and saved in `data/raw/`
- `needs_review`: ambiguous metadata, rights, or poor OCR
- `excluded`: removed from corpus with reason in notes

## Filename Rules
- Keep names lowercase with underscores.
- Include year when known.
- Use `.txt` extension for corpus ingestion.

## Quality Checklist Per Download
- Publication year is visible and plausible.
- Author and title match row metadata.
- Poetic line breaks are preserved.
- Text is primarily poetry, not prose commentary.
- OCR noise is manageable for correction.

## After Each Download Batch
Run:
- `python scripts/ingest/build_metadata.py`
- `python scripts/ingest/report_source_coverage.py`

Then review:
- `data/metadata/metadata_master.csv`
- `data/metadata/source_coverage_by_decade.csv`
- `data/metadata/source_coverage_summary.md`

## Batch Target
- Minimum initial target: 2 downloaded texts per decade from the 1850s through 1940s.
- Stretch target for M2: 5 sources per decade with acceptable metadata completeness.
