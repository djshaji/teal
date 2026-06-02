from __future__ import annotations

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "affect.infer_affect"
DESCRIPTION = "Run trained affect model inference over stanza corpus (stub)."
DEFAULT_OUTPUT = "outputs/runs/affect_infer_affect.json"


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--input", default="data/processed", help="Stanza input table.")
    parser.add_argument("--checkpoint", default="models/checkpoints/latest", help="Model checkpoint path.")
    args = parser.parse_args()

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "input": args.input,
            "checkpoint": args.checkpoint,
            "status": "stub",
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
