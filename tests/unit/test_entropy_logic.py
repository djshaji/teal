from scripts.prosody.compute_entropy import _bit_entropy, _extract_year, _shannon_entropy, _transition_entropy


def test_shannon_entropy_uniform_bits() -> None:
    entropy = _shannon_entropy(["0", "1", "0", "1"])
    assert round(entropy, 4) == 1.0


def test_bit_entropy_and_transition_entropy() -> None:
    pattern = "010101"
    b = _bit_entropy(pattern)
    t = _transition_entropy(pattern)
    assert b > 0.0
    assert t > 0.0


def test_extract_year() -> None:
    assert _extract_year("archive/poem_1914.txt") == 1914
    assert _extract_year("no_year_here") is None
