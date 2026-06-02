from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        (row.get("author") or "").strip().lower(),
        (row.get("title") or "").strip().lower(),
        (row.get("publication_year") or "").strip(),
    )


def _repo_rank(source_repository: str) -> int:
    # Lower is better.
    ranks = {
        "project_gutenberg": 0,
        "internet_archive": 1,
        "hathitrust": 2,
        "periodical_archive": 3,
        "poetry_foundation": 4,
    }
    return ranks.get(source_repository, 99)


def _pick_preferred(existing: dict[str, str], candidate: dict[str, str]) -> dict[str, str]:
    e_rank = _repo_rank(existing.get("source_repository", ""))
    c_rank = _repo_rank(candidate.get("source_repository", ""))

    if c_rank < e_rank:
        return candidate
    if c_rank > e_rank:
        return existing

    e_tier = int((existing.get("tier") or "9").strip() or "9")
    c_tier = int((candidate.get("tier") or "9").strip() or "9")
    if c_tier < e_tier:
        return candidate
    return existing


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge two source registry CSV files with de-duplication.")
    parser.add_argument("--base", type=Path, default=Path("data/metadata/sources.csv"))
    parser.add_argument("--incoming", type=Path, default=Path("data/metadata/sources_tier1_seed_20.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/metadata/sources.csv"))
    args = parser.parse_args()

    base_rows = _load_csv(args.base)
    incoming_rows = _load_csv(args.incoming)

    if not base_rows and not incoming_rows:
        return

    fieldnames = list((base_rows[0] if base_rows else incoming_rows[0]).keys())
    merged: dict[tuple[str, str, str], dict[str, str]] = {}

    for row in base_rows:
        merged[_key(row)] = row

    for row in incoming_rows:
        k = _key(row)
        if k not in merged:
            merged[k] = row
        else:
            merged[k] = _pick_preferred(merged[k], row)

    rows_out = sorted(merged.values(), key=lambda r: ((r.get("publication_year") or "9999"), r.get("author") or ""))
    _write_csv(args.output, rows_out, fieldnames)


if __name__ == "__main__":
    main()
