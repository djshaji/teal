from __future__ import annotations

import csv
import re
from pathlib import Path

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "clean.ocr_correct"
DESCRIPTION = "Apply OCR correction and normalization policies."
DEFAULT_OUTPUT = "outputs/runs/clean_ocr_correct.json"
TEXT_EXTENSIONS = {".txt", ".md"}

# Conservative normalization defaults to avoid semantic drift.
DEFAULT_REPLACEMENTS: dict[str, str] = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "—": "-",
    "–": "-",
    "’": "'",
    "“": '"',
    "”": '"',
    "\t": " ",
}


def _safe_read_text(path: Path) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _strip_paratext_lines(text: str) -> tuple[str, int]:
    kept_lines: list[str] = []
    removed = 0
    for line in text.splitlines():
        normalized = line.strip()
        # Remove likely OCR/page artifacts while keeping poetic lines.
        if normalized.isdigit() and len(normalized) <= 4:
            removed += 1
            continue
        if re.match(r"^page\s+\d+$", normalized, flags=re.IGNORECASE):
            removed += 1
            continue
        if re.match(r"^\[?\d+\]?$", normalized):
            removed += 1
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines) + ("\n" if text.endswith("\n") else ""), removed


def _apply_replacements(text: str, replacements: dict[str, str]) -> tuple[str, list[dict[str, str | int]]]:
    current = text
    audit_rows: list[dict[str, str | int]] = []
    for src, dst in replacements.items():
        count = current.count(src)
        if count == 0:
            continue
        current = current.replace(src, dst)
        audit_rows.append({"original": src, "replacement": dst, "count": count})

    # Collapse repeated spaces but preserve line boundaries.
    collapsed_lines = [re.sub(r" {2,}", " ", ln).rstrip() for ln in current.splitlines()]
    current = "\n".join(collapsed_lines) + ("\n" if current.endswith("\n") else "")
    return current, audit_rows


def _write_audit_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["relative_path", "original", "replacement", "count", "paratext_lines_removed"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--input", type=Path, default=Path("data/raw"), help="Input corpus directory.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim"), help="Cleaned intermediate directory.")
    parser.add_argument(
        "--audit-csv",
        type=Path,
        default=Path("data/interim/ocr_audit.csv"),
        help="Audit CSV for replacement counts.",
    )
    parser.add_argument(
        "--disable-paratext-strip",
        action="store_true",
        help="Disable removal of likely page-number artifacts.",
    )
    args = parser.parse_args()

    processed_files = 0
    total_replacements = 0
    total_paratext_removed = 0
    audit_rows: list[dict[str, str | int]] = []

    if args.input.exists():
        for path in sorted(args.input.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            relative = path.relative_to(args.input)
            destination = args.output_dir / relative

            text = _safe_read_text(path)
            paratext_removed = 0
            if not args.disable_paratext_strip:
                text, paratext_removed = _strip_paratext_lines(text)

            corrected, replacements = _apply_replacements(text, DEFAULT_REPLACEMENTS)

            if not args.dry_run:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(corrected, encoding="utf-8")

            if replacements:
                for replacement in replacements:
                    audit_rows.append(
                        {
                            "relative_path": str(relative),
                            "original": str(replacement["original"]),
                            "replacement": str(replacement["replacement"]),
                            "count": int(replacement["count"]),
                            "paratext_lines_removed": paratext_removed,
                        }
                    )
                    total_replacements += int(replacement["count"])
            elif paratext_removed > 0:
                audit_rows.append(
                    {
                        "relative_path": str(relative),
                        "original": "<paratext>",
                        "replacement": "<removed>",
                        "count": 0,
                        "paratext_lines_removed": paratext_removed,
                    }
                )

            total_paratext_removed += paratext_removed
            processed_files += 1

    if not args.dry_run:
        _write_audit_csv(args.audit_csv, audit_rows)

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": str(args.input),
            "output_dir": str(args.output_dir),
            "audit_csv": str(args.audit_csv),
            "files_processed": processed_files,
            "replacement_count": total_replacements,
            "paratext_lines_removed": total_paratext_removed,
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
