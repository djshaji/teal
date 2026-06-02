from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RunContext:
    stage: str
    description: str
    output_path: Path


def build_parser(stage: str, description: str, default_output: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(default_output),
        help=f"Output file path for {stage} stage artifacts.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned work without writing outputs.",
    )
    return parser


def emit_manifest(ctx: RunContext, params: dict) -> dict:
    return {
        "stage": ctx.stage,
        "description": ctx.description,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "output_path": str(ctx.output_path),
        "params": params,
    }


def write_stub_output(ctx: RunContext, payload: dict, dry_run: bool) -> None:
    if dry_run:
        print(json.dumps(payload, indent=2))
        return

    ctx.output_path.parent.mkdir(parents=True, exist_ok=True)
    with ctx.output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[{ctx.stage}] wrote {ctx.output_path}")
