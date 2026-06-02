from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "prosody.compute_entropy"
DESCRIPTION = "Compute prosodic entropy by stanza and period."
DEFAULT_OUTPUT = "outputs/runs/prosody_compute_entropy.json"


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


def _shannon_entropy(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = sum(counts.values())
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def _bit_entropy(stress_pattern: str) -> float:
    bits = [ch for ch in stress_pattern if ch in {"0", "1"}]
    return _shannon_entropy(bits)


def _transition_entropy(stress_pattern: str) -> float:
    bits = [ch for ch in stress_pattern if ch in {"0", "1"}]
    transitions = [f"{bits[i]}{bits[i + 1]}" for i in range(len(bits) - 1)]
    return _shannon_entropy(transitions)


def _extract_year(text: str) -> int | None:
    match = re.search(r"(18\d{2}|19\d{2})", text)
    if not match:
        return None
    return int(match.group(1))


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


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
        help="Line-level scansion CSV input.",
    )
    parser.add_argument(
        "--latency",
        type=Path,
        default=Path("data/processed/latency_stanzas.csv"),
        help="Optional stanza-level latency CSV for merged prosody features.",
    )
    parser.add_argument(
        "--stanza-output",
        type=Path,
        default=Path("data/processed/prosody_entropy_stanzas.csv"),
        help="Stanza-level entropy output CSV.",
    )
    parser.add_argument(
        "--diachronic-output",
        type=Path,
        default=Path("data/processed/diachronic_series.csv"),
        help="Year-level aggregated prosody series output CSV.",
    )
    args = parser.parse_args()

    line_rows = _load_rows(args.input)
    latency_rows = _load_rows(args.latency)

    latency_by_key: dict[tuple[str, int], dict[str, str]] = {}
    for row in latency_rows:
        poem_id = row.get("poem_id", "")
        stanza_index = int(row.get("stanza_index", "0") or 0)
        latency_by_key[(poem_id, stanza_index)] = row

    stanza_buckets: dict[tuple[str, int], list[dict[str, str]]] = {}
    for row in line_rows:
        poem_id = row.get("poem_id", "")
        stanza_index = int(row.get("stanza_index", "0") or 0)
        stanza_buckets.setdefault((poem_id, stanza_index), []).append(row)

    stanza_rows: list[dict[str, str | int | float]] = []
    for (poem_id, stanza_index), bucket in stanza_buckets.items():
        relative_path = str(bucket[0].get("relative_path", "")) if bucket else ""
        year = _extract_year(relative_path) or _extract_year(poem_id)

        bit_entropies: list[float] = []
        transition_entropies: list[float] = []
        syllable_counts: list[float] = []

        for row in bucket:
            pattern = row.get("stress_pattern", "")
            bit_entropies.append(_bit_entropy(pattern))
            transition_entropies.append(_transition_entropy(pattern))
            syllable_counts.append(_to_float(row.get("syllable_count", "0")))

        latency = latency_by_key.get((poem_id, stanza_index), {})
        latency_mean = _to_float(str(latency.get("latency_mean", "0")))
        latency_variance = _to_float(str(latency.get("latency_variance", "0")))
        syncopation_rate = _to_float(str(latency.get("syncopation_rate", "0")))

        stanza_rows.append(
            {
                "poem_id": poem_id,
                "relative_path": relative_path,
                "year": year if year is not None else "",
                "stanza_index": stanza_index,
                "line_count": len(bucket),
                "syllable_count_mean": round(_mean(syllable_counts), 4),
                "bit_entropy_mean": round(_mean(bit_entropies), 6),
                "transition_entropy_mean": round(_mean(transition_entropies), 6),
                "prosodic_entropy": round((_mean(bit_entropies) + _mean(transition_entropies)) / 2.0, 6),
                "latency_mean": round(latency_mean, 6),
                "latency_variance": round(latency_variance, 6),
                "syncopation_rate": round(syncopation_rate, 6),
            }
        )

    year_buckets: dict[int, list[dict[str, str | int | float]]] = {}
    for row in stanza_rows:
        year_value = row.get("year", "")
        if year_value == "":
            continue
        year_buckets.setdefault(int(year_value), []).append(row)

    diachronic_rows: list[dict[str, str | int | float]] = []
    for year in sorted(year_buckets):
        rows = year_buckets[year]
        diachronic_rows.append(
            {
                "year": year,
                "stanza_count": len(rows),
                "prosodic_entropy": round(_mean([float(r["prosodic_entropy"]) for r in rows]), 6),
                "bit_entropy_mean": round(_mean([float(r["bit_entropy_mean"]) for r in rows]), 6),
                "transition_entropy_mean": round(_mean([float(r["transition_entropy_mean"]) for r in rows]), 6),
                "latency_mean": round(_mean([float(r["latency_mean"]) for r in rows]), 6),
                "latency_variance": round(_mean([float(r["latency_variance"]) for r in rows]), 6),
                "syncopation_rate": round(_mean([float(r["syncopation_rate"]) for r in rows]), 6),
            }
        )

    if not args.dry_run:
        _write_csv(
            args.stanza_output,
            [
                "poem_id",
                "relative_path",
                "year",
                "stanza_index",
                "line_count",
                "syllable_count_mean",
                "bit_entropy_mean",
                "transition_entropy_mean",
                "prosodic_entropy",
                "latency_mean",
                "latency_variance",
                "syncopation_rate",
            ],
            stanza_rows,
        )
        _write_csv(
            args.diachronic_output,
            [
                "year",
                "stanza_count",
                "prosodic_entropy",
                "bit_entropy_mean",
                "transition_entropy_mean",
                "latency_mean",
                "latency_variance",
                "syncopation_rate",
            ],
            diachronic_rows,
        )

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": str(args.input),
            "latency": str(args.latency),
            "stanza_output": str(args.stanza_output),
            "diachronic_output": str(args.diachronic_output),
            "stanza_rows": len(stanza_rows),
            "diachronic_rows": len(diachronic_rows),
            "entropy_formula": "Shannon",
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
