from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "ingest.build_metadata"
DESCRIPTION = "Construct normalized metadata tables for ingested poems."
DEFAULT_OUTPUT = "outputs/runs/ingest_build_metadata.json"
DEFAULT_METADATA_CSV = "data/metadata/metadata_master.csv"
DEFAULT_METADATA_JSONL = "data/metadata/metadata_master.jsonl"
TEXT_EXTENSIONS = {".txt", ".md"}


def _safe_read_text(path: Path) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_header_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in text.splitlines()[:30]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key_norm = key.strip().lower().replace(" ", "_")
        if key_norm in {"title", "author", "year", "publication_year", "source", "source_repository"}:
            metadata[key_norm] = value.strip()
    return metadata


def _infer_from_filename(path: Path) -> dict[str, str]:
    # Heuristic for names like author_title_1912.txt
    stem = path.stem
    parts = re.split(r"[_-]+", stem)
    inferred: dict[str, str] = {}
    for token in reversed(parts):
        if token.isdigit() and len(token) == 4:
            inferred["publication_year"] = token
            break
    if len(parts) >= 2:
        inferred.setdefault("author", parts[0].replace(".", " ").strip())
        inferred.setdefault("title", " ".join(parts[1:]).strip())
    else:
        inferred.setdefault("title", stem)
    return inferred


def _record_for_file(path: Path, base_dir: Path, default_source: str) -> dict[str, str | int]:
    text = _safe_read_text(path)
    header = _extract_header_metadata(text)
    inferred = _infer_from_filename(path)
    content_hash = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()

    title = header.get("title") or inferred.get("title") or path.stem
    author = header.get("author") or inferred.get("author") or "Unknown"
    publication_year = header.get("publication_year") or header.get("year") or inferred.get("publication_year") or ""
    source_repository = header.get("source_repository") or header.get("source") or default_source

    return {
        "id": content_hash[:12],
        "title": str(title),
        "author": str(author),
        "publication_year": str(publication_year),
        "source_repository": str(source_repository),
        "relative_path": str(path.relative_to(base_dir)),
        "bytes": path.stat().st_size,
        "sha1": content_hash,
    }


def _write_metadata_csv(path: Path, records: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "title",
        "author",
        "publication_year",
        "source_repository",
        "relative_path",
        "bytes",
        "sha1",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def _write_metadata_jsonl(path: Path, records: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"), help="Directory containing raw source files.")
    parser.add_argument("--metadata-csv", type=Path, default=Path(DEFAULT_METADATA_CSV), help="Metadata CSV output file.")
    parser.add_argument("--metadata-jsonl", type=Path, default=Path(DEFAULT_METADATA_JSONL), help="Metadata JSONL output file.")
    parser.add_argument("--source", default="project_gutenberg", help="Default source_repository value.")
    args = parser.parse_args()

    records: list[dict[str, str | int]] = []
    if args.input_dir.exists():
        for path in sorted(args.input_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            records.append(_record_for_file(path, args.input_dir, args.source))

    required_fields = ["id", "author", "title", "publication_year", "source_repository"]
    missing_required = 0
    for record in records:
        for field in required_fields:
            if str(record.get(field, "")).strip() == "":
                missing_required += 1
                break

    if not args.dry_run:
        _write_metadata_csv(args.metadata_csv, records)
        _write_metadata_jsonl(args.metadata_jsonl, records)

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input_dir": str(args.input_dir),
            "required_fields": required_fields,
            "metadata_csv": str(args.metadata_csv),
            "metadata_jsonl": str(args.metadata_jsonl),
            "records": len(records),
            "missing_required_records": missing_required,
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
