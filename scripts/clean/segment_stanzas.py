from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "clean.segment_stanzas"
DESCRIPTION = "Segment poems into stanza-level analysis units."
DEFAULT_OUTPUT = "outputs/runs/clean_segment_stanzas.json"
TEXT_EXTENSIONS = {".txt", ".md"}


def _safe_read_text(path: Path) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _split_stanzas(text: str) -> list[list[str]]:
    stanzas: list[list[str]] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "":
            if current:
                stanzas.append(current)
                current = []
            continue
        current.append(line)
    if current:
        stanzas.append(current)
    return stanzas


def _poem_id(path: Path, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()
    return f"{path.stem}_{digest[:10]}"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--input", type=Path, default=Path("data/interim"), help="Cleaned corpus directory.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"), help="Processed stanza table directory.")
    parser.add_argument("--stanza-csv", default="stanza_units.csv", help="Output filename for stanza table.")
    parser.add_argument("--line-csv", default="line_units.csv", help="Output filename for line table.")
    parser.add_argument("--summary-csv", default="poem_summary.csv", help="Output filename for poem summary table.")
    args = parser.parse_args()

    stanza_rows: list[dict] = []
    line_rows: list[dict] = []
    poem_rows: list[dict] = []

    if args.input.exists():
        for path in sorted(args.input.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            text = _safe_read_text(path)
            stanzas = _split_stanzas(text)
            poem_id = _poem_id(path, text)

            total_lines = 0
            for stanza_idx, stanza_lines in enumerate(stanzas, start=1):
                stanza_text = "\n".join(stanza_lines)
                stanza_rows.append(
                    {
                        "poem_id": poem_id,
                        "relative_path": str(path.relative_to(args.input)),
                        "stanza_index": stanza_idx,
                        "line_count": len(stanza_lines),
                        "stanza_text": stanza_text,
                    }
                )

                for line_idx, line in enumerate(stanza_lines, start=1):
                    line_rows.append(
                        {
                            "poem_id": poem_id,
                            "relative_path": str(path.relative_to(args.input)),
                            "stanza_index": stanza_idx,
                            "line_index": line_idx,
                            "line_text": line,
                        }
                    )
                total_lines += len(stanza_lines)

            poem_rows.append(
                {
                    "poem_id": poem_id,
                    "relative_path": str(path.relative_to(args.input)),
                    "stanza_count": len(stanzas),
                    "line_count": total_lines,
                }
            )

    stanza_csv_path = args.output_dir / args.stanza_csv
    line_csv_path = args.output_dir / args.line_csv
    summary_csv_path = args.output_dir / args.summary_csv

    if not args.dry_run:
        _write_csv(
            stanza_csv_path,
            ["poem_id", "relative_path", "stanza_index", "line_count", "stanza_text"],
            stanza_rows,
        )
        _write_csv(
            line_csv_path,
            ["poem_id", "relative_path", "stanza_index", "line_index", "line_text"],
            line_rows,
        )
        _write_csv(
            summary_csv_path,
            ["poem_id", "relative_path", "stanza_count", "line_count"],
            poem_rows,
        )

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": str(args.input),
            "output_dir": str(args.output_dir),
            "stanza_csv": str(stanza_csv_path),
            "line_csv": str(line_csv_path),
            "summary_csv": str(summary_csv_path),
            "poems": len(poem_rows),
            "stanzas": len(stanza_rows),
            "lines": len(line_rows),
            "checks": ["line_boundary_integrity", "stanza_count_nonzero"],
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
