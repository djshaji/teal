from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from sklearn.cross_decomposition import CCA
from sklearn.preprocessing import StandardScaler

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "stats.run_cca"
DESCRIPTION = "Run canonical correlation analysis on prosody + affect features."
DEFAULT_OUTPUT = "outputs/runs/stats_run_cca.json"


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


def _zscore(values: list[float]) -> list[float]:
    if not values:
        return []
    mu = sum(values) / len(values)
    var = sum((v - mu) ** 2 for v in values) / len(values)
    std = var ** 0.5
    if std == 0:
        return [0.0 for _ in values]
    return [(v - mu) / std for v in values]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument(
        "--prosody",
        type=Path,
        default=Path("data/processed/prosody_entropy_stanzas.csv"),
        help="Prosody feature CSV input.",
    )
    parser.add_argument(
        "--affect",
        type=Path,
        default=Path("data/processed/affect_features.csv"),
        help="Affect feature CSV input.",
    )
    parser.add_argument("--components", type=int, default=1, help="Number of CCA components.")
    parser.add_argument(
        "--allow-proxy-affect",
        action="store_true",
        help="Use proxy affect computed from prosody when affect CSV is absent.",
    )
    parser.add_argument(
        "--scores-output",
        type=Path,
        default=Path("data/processed/cca_scores.csv"),
        help="Output CSV with canonical scores.",
    )
    parser.add_argument(
        "--loadings-output",
        type=Path,
        default=Path("data/processed/cca_loadings.csv"),
        help="Output CSV with canonical loadings/weights.",
    )
    args = parser.parse_args()

    prosody_rows = _load_rows(args.prosody)
    affect_rows = _load_rows(args.affect)

    key_fields = ["poem_id", "stanza_index"]
    prosody_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in prosody_rows:
        key = (str(row.get("poem_id", "")), str(row.get("stanza_index", "")))
        prosody_map[key] = row

    affect_map: dict[tuple[str, str], dict[str, str]] = {}
    if affect_rows:
        for row in affect_rows:
            key = (str(row.get("poem_id", "")), str(row.get("stanza_index", "")))
            affect_map[key] = row

    # Proxy affect for bootstrap runs before a trained affect model exists.
    if not affect_map and args.allow_proxy_affect:
        entropy_values = [_to_float(row.get("prosodic_entropy", "0")) for row in prosody_rows]
        sync_values = [_to_float(row.get("syncopation_rate", "0")) for row in prosody_rows]
        latvar_values = [_to_float(row.get("latency_variance", "0")) for row in prosody_rows]

        entropy_z = _zscore(entropy_values)
        sync_z = _zscore(sync_values)
        latvar_z = _zscore(latvar_values)

        for idx, row in enumerate(prosody_rows):
            key = (str(row.get("poem_id", "")), str(row.get("stanza_index", "")))
            arousal = 0.6 * sync_z[idx] + 0.4 * latvar_z[idx]
            valence = -0.7 * entropy_z[idx] - 0.3 * sync_z[idx]
            affect_map[key] = {
                "poem_id": key[0],
                "stanza_index": key[1],
                "valence": str(valence),
                "arousal": str(arousal),
                "affect_source": "proxy_from_prosody",
            }

    aligned: list[dict[str, str | float]] = []
    for key, prow in prosody_map.items():
        arow = affect_map.get(key)
        if not arow:
            continue
        aligned.append(
            {
                "poem_id": key[0],
                "stanza_index": float(key[1] or 0),
                "prosodic_entropy": _to_float(prow.get("prosodic_entropy", "0")),
                "latency_mean": _to_float(prow.get("latency_mean", "0")),
                "latency_variance": _to_float(prow.get("latency_variance", "0")),
                "syncopation_rate": _to_float(prow.get("syncopation_rate", "0")),
                "valence": _to_float(arow.get("valence", "0")),
                "arousal": _to_float(arow.get("arousal", "0")),
            }
        )

    canonical_corr = 0.0
    scores_rows: list[dict[str, str | int | float]] = []
    loadings_rows: list[dict[str, str | int | float]] = []
    used_proxy_affect = bool(aligned and not affect_rows)

    if len(aligned) >= 3:
        x_features = ["prosodic_entropy", "latency_mean", "latency_variance", "syncopation_rate"]
        y_features = ["valence", "arousal"]

        x = np.array([[float(row[f]) for f in x_features] for row in aligned], dtype=float)
        y = np.array([[float(row[f]) for f in y_features] for row in aligned], dtype=float)

        x = StandardScaler().fit_transform(x)
        y = StandardScaler().fit_transform(y)

        n_components = max(1, min(args.components, x.shape[1], y.shape[1]))
        model = CCA(n_components=n_components)
        x_c, y_c = model.fit_transform(x, y)

        if x_c.shape[1] > 0:
            corr_matrix = np.corrcoef(x_c[:, 0], y_c[:, 0])
            canonical_corr = float(corr_matrix[0, 1]) if corr_matrix.shape == (2, 2) else 0.0

        for idx, row in enumerate(aligned):
            scores_rows.append(
                {
                    "poem_id": str(row["poem_id"]),
                    "stanza_index": int(row["stanza_index"]),
                    "x_c1": round(float(x_c[idx, 0]), 6),
                    "y_c1": round(float(y_c[idx, 0]), 6),
                }
            )

        # x_weights_ and y_weights_ correspond to canonical loadings for each feature.
        for i, feature in enumerate(x_features):
            loadings_rows.append(
                {
                    "set": "prosody",
                    "feature": feature,
                    "component": 1,
                    "weight": round(float(model.x_weights_[i, 0]), 6),
                }
            )
        for i, feature in enumerate(y_features):
            loadings_rows.append(
                {
                    "set": "affect",
                    "feature": feature,
                    "component": 1,
                    "weight": round(float(model.y_weights_[i, 0]), 6),
                }
            )

    if not args.dry_run:
        _write_csv(
            args.scores_output,
            ["poem_id", "stanza_index", "x_c1", "y_c1"],
            scores_rows,
        )
        _write_csv(
            args.loadings_output,
            ["set", "feature", "component", "weight"],
            loadings_rows,
        )

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "prosody": str(args.prosody),
            "affect": str(args.affect),
            "allow_proxy_affect": args.allow_proxy_affect,
            "used_proxy_affect": used_proxy_affect,
            "method": "CCA",
            "aligned_rows": len(aligned),
            "canonical_correlation": round(canonical_corr, 6),
            "scores_output": str(args.scores_output),
            "loadings_output": str(args.loadings_output),
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
