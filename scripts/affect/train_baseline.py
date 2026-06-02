from __future__ import annotations

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "affect.train_baseline"
DESCRIPTION = "Train baseline affect model for comparison (stub)."
DEFAULT_OUTPUT = "outputs/runs/affect_train_baseline.json"


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--input", default="data/processed", help="Stanza table for training.")
    args = parser.parse_args()

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": args.input,
            "baseline": "lexicon_or_linear",
            "targets": ["valence", "arousal"],
            "status": "stub",
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
