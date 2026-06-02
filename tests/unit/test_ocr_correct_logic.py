from scripts.clean.ocr_correct import _apply_replacements, _strip_paratext_lines


def test_strip_paratext_lines_removes_page_markers() -> None:
    text = "Page 12\n1\nA real poetic line\n[23]\n"
    cleaned, removed = _strip_paratext_lines(text)
    assert removed == 3
    assert "A real poetic line" in cleaned


def test_apply_replacements_normalizes_ligatures_and_quotes() -> None:
    text = "\"ﬁre\" and “ﬂame”\n"
    cleaned, audit = _apply_replacements(text, {"ﬁ": "fi", "ﬂ": "fl", "“": '"', "”": '"'})
    assert '"fire" and "flame"' in cleaned
    assert len(audit) >= 2
