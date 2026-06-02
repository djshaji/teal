from __future__ import annotations

import csv
import random
from pathlib import Path

import numpy as np

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output
from scripts.stats.run_break_tests import _chow_statistic


STAGE = "stats.run_robustness"
DESCRIPTION = "Run robustness and sensitivity analyses."
DEFAULT_OUTPUT = "outputs/runs/stats_run_robustness.json"


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


def _to_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _corr(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    xm = _mean(x)
    ym = _mean(y)
    num = sum((a - xm) * (b - ym) for a, b in zip(x, y))
    den_x = sum((a - xm) ** 2 for a in x)
    den_y = sum((b - ym) ** 2 for b in y)
    if den_x <= 0 or den_y <= 0:
        return 0.0
    return num / ((den_x * den_y) ** 0.5)


def _period_label(year: int) -> str:
    if 1850 <= year <= 1890:
        return "victorian"
    if 1891 <= year <= 1913:
        return "transition"
    if 1914 <= year <= 1950:
        return "modernist"
    return "out_of_scope"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--input", type=Path, default=Path("data/processed"), help="Input analysis directory.")
    parser.add_argument(
        "--prosody",
        type=Path,
        default=Path("data/processed/prosody_entropy_stanzas.csv"),
        help="Prosody feature CSV (stanza level).",
    )
    parser.add_argument(
        "--series",
        type=Path,
        default=Path("data/processed/diachronic_series.csv"),
        help="Diachronic year series CSV.",
    )
    parser.add_argument("--target-year", type=int, default=1914, help="Reference break year for stability checks.")
    parser.add_argument("--shuffle-runs", type=int, default=200, help="Number of shuffled-time control runs.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for shuffling.")
    parser.add_argument(
        "--results-output",
        type=Path,
        default=Path("data/processed/robustness_results.csv"),
        help="Flat robustness results table.",
    )
    args = parser.parse_args()

    prosody_rows = _load_rows(args.prosody)
    series_rows = _load_rows(args.series)

    results_rows: list[dict[str, str | int | float]] = []

    # 1) Period-bin sensitivity: compare entropy means across historical segments.
    period_buckets: dict[str, list[float]] = {"victorian": [], "transition": [], "modernist": []}
    for row in prosody_rows:
        year = _to_int(row.get("year", ""), 0)
        label = _period_label(year)
        if label in period_buckets:
            period_buckets[label].append(_to_float(row.get("prosodic_entropy", "0")))

    vict_mean = _mean(period_buckets["victorian"])
    trans_mean = _mean(period_buckets["transition"])
    mod_mean = _mean(period_buckets["modernist"])
    results_rows.extend(
        [
            {
                "check": "period_bins",
                "metric": "mean_entropy_victorian",
                "value": round(vict_mean, 6),
                "n": len(period_buckets["victorian"]),
            },
            {
                "check": "period_bins",
                "metric": "mean_entropy_transition",
                "value": round(trans_mean, 6),
                "n": len(period_buckets["transition"]),
            },
            {
                "check": "period_bins",
                "metric": "mean_entropy_modernist",
                "value": round(mod_mean, 6),
                "n": len(period_buckets["modernist"]),
            },
            {
                "check": "period_bins",
                "metric": "delta_modernist_minus_victorian",
                "value": round(mod_mean - vict_mean, 6),
                "n": min(len(period_buckets["modernist"]), len(period_buckets["victorian"])),
            },
        ]
    )

    # 2) Form-subset proxy: low/high syncopation halves.
    valid_sync = [_to_float(row.get("syncopation_rate", "0")) for row in prosody_rows]
    if valid_sync:
        threshold = float(np.median(np.array(valid_sync, dtype=float)))
        low_entropy = [
            _to_float(row.get("prosodic_entropy", "0"))
            for row in prosody_rows
            if _to_float(row.get("syncopation_rate", "0")) <= threshold
        ]
        high_entropy = [
            _to_float(row.get("prosodic_entropy", "0"))
            for row in prosody_rows
            if _to_float(row.get("syncopation_rate", "0")) > threshold
        ]
        results_rows.extend(
            [
                {
                    "check": "form_subsets",
                    "metric": "syncopation_median_threshold",
                    "value": round(threshold, 6),
                    "n": len(valid_sync),
                },
                {
                    "check": "form_subsets",
                    "metric": "mean_entropy_low_syncopation",
                    "value": round(_mean(low_entropy), 6),
                    "n": len(low_entropy),
                },
                {
                    "check": "form_subsets",
                    "metric": "mean_entropy_high_syncopation",
                    "value": round(_mean(high_entropy), 6),
                    "n": len(high_entropy),
                },
            ]
        )

    # 3) Author-effects proxy: within-poem de-meaned correlation.
    by_poem: dict[str, list[dict[str, str]]] = {}
    for row in prosody_rows:
        by_poem.setdefault(str(row.get("poem_id", "")), []).append(row)

    residual_entropy: list[float] = []
    residual_sync: list[float] = []
    for poem_rows in by_poem.values():
        ent = [_to_float(r.get("prosodic_entropy", "0")) for r in poem_rows]
        sync = [_to_float(r.get("syncopation_rate", "0")) for r in poem_rows]
        ent_mean = _mean(ent)
        sync_mean = _mean(sync)
        residual_entropy.extend([v - ent_mean for v in ent])
        residual_sync.extend([v - sync_mean for v in sync])

    fe_corr = _corr(residual_entropy, residual_sync)
    results_rows.append(
        {
            "check": "author_effects_proxy",
            "metric": "within_poem_corr_entropy_syncopation",
            "value": round(fe_corr, 6),
            "n": len(residual_entropy),
        }
    )

    # 4) Time-label shuffle control on Chow F-stat at target year.
    series_sorted = sorted(
        [
            {
                "year": _to_int(row.get("year", ""), 0),
                "prosodic_entropy": _to_float(row.get("prosodic_entropy", "0")),
            }
            for row in series_rows
            if row.get("year", "") != ""
        ],
        key=lambda r: int(r["year"]),
    )

    observed_stat = 0.0
    shuffled_mean = 0.0
    shuffled_p95 = 0.0
    empirical_p = 1.0

    if len(series_sorted) >= 8:
        years = np.array([float(r["year"]) for r in series_sorted], dtype=float)
        entropy = np.array([float(r["prosodic_entropy"]) for r in series_sorted], dtype=float)
        split_idx = next((i for i, r in enumerate(series_sorted) if int(r["year"]) >= args.target_year), None)
        if split_idx is not None:
            observed_stat = _chow_statistic(years, entropy, split_idx)

            rng = random.Random(args.seed)
            shuffled_stats: list[float] = []
            entropy_list = list(entropy)
            for _ in range(max(1, args.shuffle_runs)):
                shuffled = entropy_list[:]
                rng.shuffle(shuffled)
                shuffled_stats.append(_chow_statistic(years, np.array(shuffled, dtype=float), split_idx))

            shuffled_mean = _mean(shuffled_stats)
            if shuffled_stats:
                sorted_stats = sorted(shuffled_stats)
                idx = min(len(sorted_stats) - 1, int(0.95 * (len(sorted_stats) - 1)))
                shuffled_p95 = sorted_stats[idx]
                ge_count = sum(1 for s in shuffled_stats if s >= observed_stat)
                empirical_p = ge_count / len(shuffled_stats)

    results_rows.extend(
        [
            {
                "check": "time_label_shuffle",
                "metric": "observed_chow_f",
                "value": round(observed_stat, 6),
                "n": len(series_sorted),
            },
            {
                "check": "time_label_shuffle",
                "metric": "shuffled_mean_chow_f",
                "value": round(shuffled_mean, 6),
                "n": args.shuffle_runs,
            },
            {
                "check": "time_label_shuffle",
                "metric": "shuffled_p95_chow_f",
                "value": round(shuffled_p95, 6),
                "n": args.shuffle_runs,
            },
            {
                "check": "time_label_shuffle",
                "metric": "empirical_p_value",
                "value": round(empirical_p, 6),
                "n": args.shuffle_runs,
            },
        ]
    )

    if not args.dry_run:
        _write_csv(args.results_output, ["check", "metric", "value", "n"], results_rows)

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": str(args.input),
            "prosody": str(args.prosody),
            "series": str(args.series),
            "target_year": args.target_year,
            "shuffle_runs": args.shuffle_runs,
            "results_output": str(args.results_output),
            "result_rows": len(results_rows),
            "checks": ["period_bins", "author_effects", "form_subsets", "time_label_shuffle"],
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
