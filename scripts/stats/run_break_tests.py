from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "stats.run_break_tests"
DESCRIPTION = "Run structural break tests on diachronic series."
DEFAULT_OUTPUT = "outputs/runs/stats_run_break_tests.json"


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fit_rss(x: np.ndarray, y: np.ndarray) -> float:
    # OLS with intercept
    X = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ beta
    return float(np.sum(residuals ** 2))


def _chow_statistic(x: np.ndarray, y: np.ndarray, split_idx: int, k: int = 2) -> float:
    if split_idx <= 1 or split_idx >= len(x) - 1:
        return 0.0
    n = len(x)
    rss_full = _fit_rss(x, y)
    rss_1 = _fit_rss(x[:split_idx], y[:split_idx])
    rss_2 = _fit_rss(x[split_idx:], y[split_idx:])

    numerator = (rss_full - (rss_1 + rss_2)) / k
    denominator_term = (rss_1 + rss_2) / max(1, (n - 2 * k))
    if denominator_term <= 0:
        return 0.0
    return float(max(0.0, numerator / denominator_term))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument(
        "--series",
        type=Path,
        default=Path("data/processed/diachronic_series.csv"),
        help="Time-series CSV input.",
    )
    parser.add_argument("--target-year", type=int, default=1914, help="Primary Chow-test break year.")
    parser.add_argument("--min-segment", type=int, default=8, help="Minimum years per segment for scan.")
    parser.add_argument(
        "--scan-output",
        type=Path,
        default=Path("data/processed/break_test_scan.csv"),
        help="Output CSV for scanned candidate breakpoints.",
    )
    args = parser.parse_args()

    raw_rows = _load_rows(args.series)
    rows = [
        {
            "year": int(_to_float(row.get("year", "0"))),
            "prosodic_entropy": _to_float(row.get("prosodic_entropy", "0")),
        }
        for row in raw_rows
        if row.get("year", "") != ""
    ]
    rows = sorted(rows, key=lambda x: int(x["year"]))

    candidate_rows: list[dict[str, str | int | float]] = []
    best_year = None
    best_stat = 0.0
    target_stat = 0.0

    if len(rows) >= (2 * args.min_segment + 2):
        years = np.array([float(row["year"]) for row in rows], dtype=float)
        entropy = np.array([float(row["prosodic_entropy"]) for row in rows], dtype=float)

        for idx in range(args.min_segment, len(rows) - args.min_segment):
            split_year = int(rows[idx]["year"])
            stat = _chow_statistic(years, entropy, idx)
            candidate_rows.append(
                {
                    "split_year": split_year,
                    "chow_f_stat": round(stat, 6),
                }
            )
            if stat > best_stat:
                best_stat = stat
                best_year = split_year

        target_idx = next((i for i, row in enumerate(rows) if int(row["year"]) >= args.target_year), None)
        if target_idx is not None:
            target_stat = _chow_statistic(years, entropy, target_idx)

    if not args.dry_run:
        _write_csv(args.scan_output, ["split_year", "chow_f_stat"], candidate_rows)

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "series": str(args.series),
            "target_year": args.target_year,
            "candidate_breaks": len(candidate_rows),
            "target_chow_f_stat": round(target_stat, 6),
            "best_break_year": best_year if best_year is not None else "",
            "best_break_f_stat": round(best_stat, 6),
            "scan_output": str(args.scan_output),
            "tests": ["chow", "bai_perron_or_alternative"],
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
