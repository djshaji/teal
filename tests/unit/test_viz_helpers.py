from scripts.viz.build_figures import _to_float, _to_int


def test_to_int_and_to_float_defaults() -> None:
    assert _to_int("1914") == 1914
    assert _to_int("bad", 7) == 7
    assert _to_float("1.25") == 1.25
    assert _to_float("bad", 2.5) == 2.5
