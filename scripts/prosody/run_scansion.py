from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

try:
    import pronouncing  # type: ignore
except ImportError:  # pragma: no cover - optional runtime dependency.
    pronouncing = None

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "prosody.run_scansion"
DESCRIPTION = "Run algorithmic scansion over processed corpus."
DEFAULT_OUTPUT = "outputs/runs/prosody_run_scansion.json"
WORD_PATTERN = re.compile(r"[A-Za-z']+")


def _load_stanza_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def _estimate_syllables(word: str) -> int:
    lowered = re.sub(r"[^a-z]", "", word.lower())
    if not lowered:
        return 1
    groups = re.findall(r"[aeiouy]+", lowered)
    count = len(groups)
    if lowered.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _word_stress(word: str) -> str:
    token = word.lower()
    if pronouncing is not None:
        phones = pronouncing.phones_for_word(token)
        if phones:
            stresses = pronouncing.stresses(phones[0])
            if stresses:
                return stresses.replace("2", "1")

    syllables = _estimate_syllables(token)
    # Fallback heuristic: alternating stress starting unstressed.
    return "".join("1" if i % 2 else "0" for i in range(syllables))


def _line_stress_pattern(line: str) -> str:
    words = WORD_PATTERN.findall(line)
    if not words:
        return ""
    return "".join(_word_stress(word) for word in words)


def _meter_template(name: str, length: int) -> str:
    if length <= 0:
        return ""
    patterns = {
        "iambic": "01",
        "trochaic": "10",
        "anapestic": "001",
        "dactylic": "100",
    }
    base = patterns.get(name, "01")
    repeated = (base * ((length // len(base)) + 1))[:length]
    return repeated


def _hamming(a: str, b: str) -> int:
    n = min(len(a), len(b))
    mismatches = sum(1 for i in range(n) if a[i] != b[i])
    mismatches += abs(len(a) - len(b))
    return mismatches


def _infer_meter(pattern: str, meter_mode: str) -> tuple[str, str]:
    if not pattern:
        return "free", ""

    if meter_mode in {"iambic", "trochaic", "anapestic", "dactylic"}:
        template = _meter_template(meter_mode, len(pattern))
        return meter_mode, template

    candidates = ["iambic", "trochaic", "anapestic", "dactylic"]
    best_meter = "free"
    best_template = ""
    best_score = float("inf")
    for candidate in candidates:
        template = _meter_template(candidate, len(pattern))
        score = _hamming(pattern, template)
        if score < best_score:
            best_score = score
            best_meter = candidate
            best_template = template
    return best_meter, best_template


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
        default=Path("data/processed/stanza_units.csv"),
        help="Stanza unit CSV input.",
    )
    parser.add_argument("--meter", default="auto", help="Meter inference mode (auto/iambic/trochaic/anapestic/dactylic).")
    parser.add_argument(
        "--line-output",
        type=Path,
        default=Path("data/processed/scansion_lines.csv"),
        help="Output CSV path for line-level scansion.",
    )
    parser.add_argument(
        "--stanza-output",
        type=Path,
        default=Path("data/processed/scansion_stanzas.csv"),
        help="Output CSV path for stanza-level scansion summary.",
    )
    args = parser.parse_args()

    stanza_rows = _load_stanza_rows(args.input)
    line_rows: list[dict[str, str | int | float]] = []
    stanza_summary_rows: list[dict[str, str | int | float]] = []

    for stanza in stanza_rows:
        poem_id = stanza.get("poem_id", "")
        relative_path = stanza.get("relative_path", "")
        stanza_index = int(stanza.get("stanza_index", "0") or 0)
        stanza_text = stanza.get("stanza_text", "")
        raw_lines = [ln for ln in stanza_text.split("\n") if ln.strip()]

        meter_counts: Counter[str] = Counter()
        stress_density_values: list[float] = []
        syllable_values: list[int] = []

        for line_index, line_text in enumerate(raw_lines, start=1):
            pattern = _line_stress_pattern(line_text)
            meter_guess, expected_pattern = _infer_meter(pattern, args.meter)
            syllable_count = len(pattern)
            stressed = pattern.count("1")
            stress_density = (stressed / syllable_count) if syllable_count else 0.0

            meter_counts[meter_guess] += 1
            stress_density_values.append(stress_density)
            syllable_values.append(syllable_count)

            line_rows.append(
                {
                    "poem_id": poem_id,
                    "relative_path": relative_path,
                    "stanza_index": stanza_index,
                    "line_index": line_index,
                    "line_text": line_text,
                    "stress_pattern": pattern,
                    "expected_pattern": expected_pattern,
                    "meter_guess": meter_guess,
                    "syllable_count": syllable_count,
                    "stressed_count": stressed,
                    "stress_density": round(stress_density, 4),
                }
            )

        dominant_meter = meter_counts.most_common(1)[0][0] if meter_counts else "free"
        mean_stress_density = sum(stress_density_values) / len(stress_density_values) if stress_density_values else 0.0
        mean_syllables = sum(syllable_values) / len(syllable_values) if syllable_values else 0.0

        stanza_summary_rows.append(
            {
                "poem_id": poem_id,
                "relative_path": relative_path,
                "stanza_index": stanza_index,
                "line_count": len(raw_lines),
                "dominant_meter": dominant_meter,
                "mean_stress_density": round(mean_stress_density, 4),
                "mean_syllable_count": round(mean_syllables, 2),
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
                "line_text",
                "stress_pattern",
                "expected_pattern",
                "meter_guess",
                "syllable_count",
                "stressed_count",
                "stress_density",
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
                "dominant_meter",
                "mean_stress_density",
                "mean_syllable_count",
            ],
            stanza_summary_rows,
        )

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": str(args.input),
            "meter": args.meter,
            "line_output": str(args.line_output),
            "stanza_output": str(args.stanza_output),
            "line_rows": len(line_rows),
            "stanza_rows": len(stanza_summary_rows),
            "pronouncing_available": pronouncing is not None,
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
