from scripts.clean.segment_stanzas import _split_stanzas


def test_split_stanzas_basic() -> None:
    text = "Line 1\nLine 2\n\nLine 3\n\nLine 4\nLine 5"
    stanzas = _split_stanzas(text)

    assert len(stanzas) == 3
    assert stanzas[0] == ["Line 1", "Line 2"]
    assert stanzas[1] == ["Line 3"]
    assert stanzas[2] == ["Line 4", "Line 5"]


def test_split_stanzas_ignores_extra_blank_lines() -> None:
    text = "\n\nAlpha\n\n\nBeta\n\n"
    stanzas = _split_stanzas(text)

    assert stanzas == [["Alpha"], ["Beta"]]
