from pathlib import Path

from scripts.ingest.build_metadata import _extract_header_metadata, _infer_from_filename, _record_for_file


def test_extract_header_metadata() -> None:
    text = """Title: Night Ledger
Author: Test Poet
Year: 1917
Other: Ignored
"""
    meta = _extract_header_metadata(text)
    assert meta["title"] == "Night Ledger"
    assert meta["author"] == "Test Poet"
    assert meta["year"] == "1917"
    assert "other" not in meta


def test_infer_from_filename_year_and_title() -> None:
    inferred = _infer_from_filename(Path("browning_iron_city_1898.txt"))
    assert inferred["publication_year"] == "1898"
    assert inferred["author"] == "browning"
    assert "iron" in inferred["title"]


def test_record_for_file(tmp_path: Path) -> None:
    poem = tmp_path / "sample_1905.txt"
    poem.write_text("Title: Smoke\nAuthor: A. Poet\nYear: 1905\n\nLine one.", encoding="utf-8")

    record = _record_for_file(poem, tmp_path, "project_gutenberg")

    assert record["title"] == "Smoke"
    assert record["author"] == "A. Poet"
    assert record["publication_year"] == "1905"
    assert record["source_repository"] in {"project_gutenberg", ""}
    assert len(str(record["id"])) == 12
