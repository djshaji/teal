from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "viz.build_figures"
DESCRIPTION = "Generate publication-ready figures and tables."
DEFAULT_OUTPUT = "outputs/runs/viz_build_figures.json"


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


def _save_entropy_plot(rows: list[dict[str, str]], output_path: Path) -> bool:
    if not rows:
        return False
    years = [_to_int(r.get("year", "0")) for r in rows]
    entropy = [_to_float(r.get("prosodic_entropy", "0")) for r in rows]

    pairs = sorted(zip(years, entropy), key=lambda t: t[0])
    years_sorted = [p[0] for p in pairs]
    entropy_sorted = [p[1] for p in pairs]

    plt.figure(figsize=(9, 4.8))
    plt.plot(years_sorted, entropy_sorted, linewidth=2)
    plt.title("Prosodic Entropy by Year")
    plt.xlabel("Year")
    plt.ylabel("Entropy")
    plt.grid(alpha=0.3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return True


def _save_cca_loadings_plot(rows: list[dict[str, str]], output_path: Path) -> bool:
    if not rows:
        return False
    features = [str(r.get("feature", "")) for r in rows]
    weights = [_to_float(r.get("weight", "0")) for r in rows]
    sets = [str(r.get("set", "")) for r in rows]

    colors = ["#1f77b4" if s == "prosody" else "#ff7f0e" for s in sets]

    plt.figure(figsize=(10, 5.2))
    positions = list(range(len(features)))
    plt.bar(positions, weights, color=colors)
    plt.axhline(0.0, color="black", linewidth=1)
    plt.xticks(positions, features, rotation=35, ha="right")
    plt.ylabel("Canonical Weight")
    plt.title("CCA Loadings (Component 1)")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return True


def _save_breakpoint_plot(rows: list[dict[str, str]], output_path: Path) -> bool:
    if not rows:
        return False

    split_years = [_to_int(r.get("split_year", "0")) for r in rows]
    chow_stats = [_to_float(r.get("chow_f_stat", "0")) for r in rows]
    pairs = sorted(zip(split_years, chow_stats), key=lambda t: t[0])
    split_sorted = [p[0] for p in pairs]
    stat_sorted = [p[1] for p in pairs]

    max_idx = max(range(len(stat_sorted)), key=lambda i: stat_sorted[i]) if stat_sorted else 0
    best_year = split_sorted[max_idx] if split_sorted else None

    plt.figure(figsize=(9, 4.8))
    plt.plot(split_sorted, stat_sorted, linewidth=2)
    if best_year is not None:
        plt.axvline(best_year, linestyle="--", linewidth=1.5, color="#d62728", label=f"Best break: {best_year}")
        plt.legend()
    plt.title("Structural Break Scan (Chow F)")
    plt.xlabel("Candidate Split Year")
    plt.ylabel("F-statistic")
    plt.grid(alpha=0.3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return True


def _write_figure_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["figure", "status", "source", "output"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--input", type=Path, default=Path("data/processed"), help="Input analysis artifacts directory.")
    parser.add_argument("--fig-dir", type=Path, default=Path("docs/figures"), help="Figure output directory.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/figures/figure_manifest.csv"),
        help="CSV manifest of generated figures.",
    )
    args = parser.parse_args()

    entropy_src = args.input / "diachronic_series.csv"
    cca_src = args.input / "cca_loadings.csv"
    break_src = args.input / "break_test_scan.csv"

    entropy_out = args.fig_dir / "entropy_by_year.png"
    cca_out = args.fig_dir / "cca_loadings.png"
    break_out = args.fig_dir / "breakpoint_timeline.png"

    figure_manifest_rows: list[dict[str, str]] = []

    entropy_rows = _load_rows(entropy_src)
    entropy_ok = _save_entropy_plot(entropy_rows, entropy_out) if not args.dry_run else bool(entropy_rows)
    figure_manifest_rows.append(
        {
            "figure": "entropy_by_year",
            "status": "generated" if entropy_ok else "skipped_missing_input",
            "source": str(entropy_src),
            "output": str(entropy_out),
        }
    )

    cca_rows = _load_rows(cca_src)
    cca_ok = _save_cca_loadings_plot(cca_rows, cca_out) if not args.dry_run else bool(cca_rows)
    figure_manifest_rows.append(
        {
            "figure": "cca_loadings",
            "status": "generated" if cca_ok else "skipped_missing_input",
            "source": str(cca_src),
            "output": str(cca_out),
        }
    )

    break_rows = _load_rows(break_src)
    break_ok = _save_breakpoint_plot(break_rows, break_out) if not args.dry_run else bool(break_rows)
    figure_manifest_rows.append(
        {
            "figure": "breakpoint_timeline",
            "status": "generated" if break_ok else "skipped_missing_input",
            "source": str(break_src),
            "output": str(break_out),
        }
    )

    if not args.dry_run:
        _write_figure_manifest(args.manifest, figure_manifest_rows)

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": str(args.input),
            "fig_dir": str(args.fig_dir),
            "manifest": str(args.manifest),
            "generated_figures": sum(1 for row in figure_manifest_rows if row["status"] == "generated"),
            "figure_targets": ["entropy_by_year", "cca_loadings", "breakpoint_timeline"],
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
