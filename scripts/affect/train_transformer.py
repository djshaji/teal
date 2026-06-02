from __future__ import annotations

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "affect.train_transformer"
DESCRIPTION = "Fine-tune transformer model for stanza-level affect (stub)."
DEFAULT_OUTPUT = "outputs/runs/affect_train_transformer.json"


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--model", default="bert-base-uncased", help="Transformer checkpoint.")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs.")
    args = parser.parse_args()

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "model": args.model,
            "epochs": args.epochs,
            "targets": ["valence", "arousal"],
            "status": "stub",
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
