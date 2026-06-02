from __future__ import annotations

import csv
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from scripts.utils.common import RunContext, build_parser, emit_manifest, write_stub_output


STAGE = "ingest.fetch_sources"
DESCRIPTION = "Fetch source corpora from configured repositories."
DEFAULT_OUTPUT = "outputs/runs/ingest_fetch_sources.json"
DEFAULT_REGISTRY = "data/metadata/sources.csv"
DEFAULT_DEST_DIR = "data/raw"


def _write_registry_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_id",
                "url",
                "filename",
                "author",
                "title",
                "year",
                "source_repository",
            ],
        )
        writer.writeheader()


def _infer_filename(url: str, fallback_stem: str) -> str:
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name
    if not name:
        return f"{fallback_stem}.txt"
    return name


def _download_file(url: str, destination: Path, timeout: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        data = response.read()
    destination.write_bytes(data)


def _copy_local_file(src: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, destination)


def main() -> None:
    parser = build_parser(STAGE, DESCRIPTION, DEFAULT_OUTPUT)
    parser.add_argument("--source", default="project_gutenberg", help="Source filter (from registry source_repository).")
    parser.add_argument("--registry", type=Path, default=Path(DEFAULT_REGISTRY), help="CSV registry of sources.")
    parser.add_argument("--dest-dir", type=Path, default=Path(DEFAULT_DEST_DIR), help="Destination directory for fetched files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit for number of files to fetch.")
    parser.add_argument("--timeout", type=int, default=30, help="Network timeout in seconds.")
    args = parser.parse_args()

    registry_created = False
    if not args.registry.exists():
        if not args.dry_run:
            _write_registry_template(args.registry)
        registry_created = True

    fetched: list[str] = []
    skipped: list[str] = []
    failed: list[dict] = []
    selected = 0

    if args.registry.exists():
        with args.registry.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                source_repository = (row.get("source_repository") or "").strip()
                if args.source and source_repository and source_repository != args.source:
                    continue

                source_id = (row.get("source_id") or "unknown").strip() or "unknown"
                url = (row.get("url") or "").strip()
                filename = (row.get("filename") or "").strip()

                if not url:
                    failed.append({"source_id": source_id, "reason": "missing_url"})
                    continue

                if args.limit and selected >= args.limit:
                    break

                if not filename:
                    filename = _infer_filename(url, source_id)

                destination = args.dest_dir / filename
                if destination.exists() and not args.force:
                    skipped.append(str(destination))
                    selected += 1
                    continue

                if args.dry_run:
                    fetched.append(str(destination))
                    selected += 1
                    continue

                try:
                    parsed = urllib.parse.urlparse(url)
                    if parsed.scheme in {"", "file"}:
                        local_source = Path(parsed.path) if parsed.scheme == "file" else Path(url)
                        _copy_local_file(local_source, destination)
                    else:
                        _download_file(url, destination, timeout=args.timeout)
                    fetched.append(str(destination))
                    selected += 1
                except (FileNotFoundError, PermissionError) as exc:
                    failed.append({"source_id": source_id, "url": url, "reason": str(exc)})
                except urllib.error.URLError as exc:
                    failed.append({"source_id": source_id, "url": url, "reason": f"network_error: {exc}"})

    ctx = RunContext(stage=STAGE, description=DESCRIPTION, output_path=args.output)
    payload = emit_manifest(
        ctx,
        {
            "source": args.source,
            "registry": str(args.registry),
            "registry_created": registry_created,
            "dest_dir": str(args.dest_dir),
            "fetched_count": len(fetched),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "fetched": fetched,
            "skipped": skipped,
            "failed": failed,
        },
    )
    write_stub_output(ctx, payload, args.dry_run)


if __name__ == "__main__":
    main()
