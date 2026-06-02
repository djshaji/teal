from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "ingest.report_source_coverage"
DESCRIPTION = "Summarize source registry coverage by decade and repository."
DEFAULT_OUTPUT = "outputs/runs/ingest_report_source_coverage.json"


def _load_sources(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _to_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _decade_label(year: int) -> str:
    if year <= 0:
        return "unknown"
    return f"{(year // 10) * 10}s"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary_md(
    path: Path,
    total_rows: int,
    decade_rows: list[dict[str, str | int]],
    repository_rows: list[dict[str, str | int]],
    missing_year: int,
    missing_url: int,
    pending_access: int,
    target_per_decade: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    under_target = [
        row for row in decade_rows if row["decade"] != "unknown" and int(row["source_count"]) < target_per_decade
    ]

    lines: list[str] = []
    lines.append("# Source Coverage Summary")
    lines.append("")
    lines.append(f"- Total source rows: {total_rows}")
    lines.append(f"- Missing/invalid publication year rows: {missing_year}")
    lines.append(f"- Missing URL rows: {missing_url}")
    lines.append(f"- Pending-access rows: {pending_access}")
    lines.append("")
    lines.append("## Coverage by Decade")
    for row in decade_rows:
        lines.append(f"- {row['decade']}: {row['source_count']}")
    lines.append("")
    lines.append("## Coverage by Repository")
    for row in repository_rows:
        lines.append(f"- {row['source_repository']}: {row['source_count']}")
    lines.append("")
    lines.append(f"## Decades Below Target ({target_per_decade} sources)")
    if under_target:
        for row in under_target:
            lines.append(f"- {row['decade']}: {row['source_count']}")
    else:
        lines.append("- None")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path("data/metadata/sources.csv"),
        help="Source registry CSV input.",
    )
    parser.add_argument(
        "--decade-output",
        type=Path,
        default=Path("data/metadata/source_coverage_by_decade.csv"),
        help="Decade coverage CSV output.",
    )
    parser.add_argument(
        "--repository-output",
        type=Path,
        default=Path("data/metadata/source_coverage_by_repository.csv"),
        help="Repository coverage CSV output.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("data/metadata/source_coverage_summary.md"),
        help="Markdown summary output.",
    )
    parser.add_argument(
        "--target-per-decade",
        type=int,
        default=5,
        help="Target source count per decade used for gap detection.",
    )
    args = parser.parse_args()

    rows = _load_sources(args.sources)

    decade_counter: Counter[str] = Counter()
    repo_counter: Counter[str] = Counter()
    missing_year = 0
    missing_url = 0
    pending_access = 0

    for row in rows:
        year = _to_int(str(row.get("publication_year", "")), 0)
        decade = _decade_label(year)
        decade_counter[decade] += 1

        repository = (row.get("source_repository") or "unknown").strip() or "unknown"
        repo_counter[repository] += 1

        if decade == "unknown":
            missing_year += 1
        if not (row.get("url") or "").strip():
            missing_url += 1

        status = (row.get("acquisition_status") or "").strip().lower()
        if status in {"pending_access", "queued", "planned", "manual_queue"}:
            pending_access += 1

    decade_rows: list[dict[str, str | int]] = [
        {"decade": decade, "source_count": count}
        for decade, count in sorted(decade_counter.items(), key=lambda kv: kv[0])
    ]
    repository_rows: list[dict[str, str | int]] = [
        {"source_repository": repo, "source_count": count}
        for repo, count in sorted(repo_counter.items(), key=lambda kv: kv[1], reverse=True)
    ]

    if not args.dry_run:
        _write_csv(args.decade_output, ["decade", "source_count"], decade_rows)
        _write_csv(args.repository_output, ["source_repository", "source_count"], repository_rows)
        _write_summary_md(
            args.summary_output,
            total_rows=len(rows),
            decade_rows=decade_rows,
            repository_rows=repository_rows,
            missing_year=missing_year,
            missing_url=missing_url,
            pending_access=pending_access,
            target_per_decade=args.target_per_decade,
        )

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "sources": str(args.sources),
            "total_rows": len(rows),
            "decade_output": str(args.decade_output),
            "repository_output": str(args.repository_output),
            "summary_output": str(args.summary_output),
            "missing_year_rows": missing_year,
            "missing_url_rows": missing_url,
            "pending_access_rows": pending_access,
            "target_per_decade": args.target_per_decade,
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
