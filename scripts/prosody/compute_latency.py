from __future__ import annotations

import csv
from pathlib import Path

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "prosody.compute_latency"
DESCRIPTION = "Compute rhythmic latency features from scansion outputs."
DEFAULT_OUTPUT = "outputs/runs/prosody_compute_latency.json"


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def _stress_positions(pattern: str) -> list[int]:
    return [idx for idx, ch in enumerate(pattern) if ch == "1"]


def _compute_deltas(observed: list[int], expected: list[int]) -> list[int]:
    n = min(len(observed), len(expected))
    if n == 0:
        return []
    return [observed[i] - expected[i] for i in range(n)]


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mu = _mean(values)
    return sum((v - mu) ** 2 for v in values) / len(values)


def _syncopation_rate(pattern: str, expected: str) -> float:
    n = max(len(pattern), len(expected))
    if n == 0:
        return 0.0
    mismatches = 0
    for i in range(n):
        a = pattern[i] if i < len(pattern) else "0"
        b = expected[i] if i < len(expected) else "0"
        if a != b:
            mismatches += 1
    return mismatches / n


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/scansion_lines.csv"),
        help="Input scansion line table.",
    )
    parser.add_argument(
        "--line-output",
        type=Path,
        default=Path("data/processed/latency_lines.csv"),
        help="Line-level latency output.",
    )
    parser.add_argument(
        "--stanza-output",
        type=Path,
        default=Path("data/processed/latency_stanzas.csv"),
        help="Stanza-level latency aggregate output.",
    )
    args = parser.parse_args()

    rows = _load_rows(args.input)
    line_rows: list[dict[str, str | int | float]] = []
    stanza_buckets: dict[tuple[str, int], list[dict[str, str | int | float]]] = {}

    for row in rows:
        poem_id = row.get("poem_id", "")
        relative_path = row.get("relative_path", "")
        stanza_index = int(row.get("stanza_index", "0") or 0)
        line_index = int(row.get("line_index", "0") or 0)
        pattern = row.get("stress_pattern", "")
        expected = row.get("expected_pattern", "")
        meter_guess = row.get("meter_guess", "free")

        observed_positions = _stress_positions(pattern)
        expected_positions = _stress_positions(expected)
        deltas = _compute_deltas(observed_positions, expected_positions)

        latency_mean = _mean([float(d) for d in deltas])
        latency_variance = _variance([float(d) for d in deltas])
        syncopation = _syncopation_rate(pattern, expected)

        line_record: dict[str, str | int | float] = {
            "poem_id": poem_id,
            "relative_path": relative_path,
            "stanza_index": stanza_index,
            "line_index": line_index,
            "meter_guess": meter_guess,
            "stress_pattern": pattern,
            "expected_pattern": expected,
            "delta_t_series": ";".join(str(d) for d in deltas),
            "latency_mean": round(latency_mean, 4),
            "latency_variance": round(latency_variance, 4),
            "syncopation_rate": round(syncopation, 4),
        }
        line_rows.append(line_record)

        bucket_key = (poem_id, stanza_index)
        stanza_buckets.setdefault(bucket_key, []).append(line_record)

    stanza_rows: list[dict[str, str | int | float]] = []
    for (poem_id, stanza_index), bucket in stanza_buckets.items():
        relative_path = str(bucket[0].get("relative_path", "")) if bucket else ""
        latency_means = [float(row["latency_mean"]) for row in bucket]
        latency_variances = [float(row["latency_variance"]) for row in bucket]
        syncopations = [float(row["syncopation_rate"]) for row in bucket]
        stanza_rows.append(
            {
                "poem_id": poem_id,
                "relative_path": relative_path,
                "stanza_index": stanza_index,
                "line_count": len(bucket),
                "latency_mean": round(_mean(latency_means), 4),
                "latency_variance": round(_mean(latency_variances), 4),
                "syncopation_rate": round(_mean(syncopations), 4),
            }
        )

    if not args.dry_run:
        _write_csv(
            args.line_output,
            [
                "poem_id",
                "relative_path",
                "stanza_index",
                "line_index",
                "meter_guess",
                "stress_pattern",
                "expected_pattern",
                "delta_t_series",
                "latency_mean",
                "latency_variance",
                "syncopation_rate",
            ],
            line_rows,
        )
        _write_csv(
            args.stanza_output,
            [
                "poem_id",
                "relative_path",
                "stanza_index",
                "line_count",
                "latency_mean",
                "latency_variance",
                "syncopation_rate",
            ],
            stanza_rows,
        )

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": str(args.input),
            "line_output": str(args.line_output),
            "stanza_output": str(args.stanza_output),
            "line_rows": len(line_rows),
            "stanza_rows": len(stanza_rows),
            "features": ["delta_t", "latency_mean", "latency_variance"],
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
