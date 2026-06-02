from scripts.stats.run_robustness import _corr, _period_label


def test_period_label_boundaries() -> None:
    assert _period_label(1850) == "victorian"
    assert _period_label(1891) == "transition"
    assert _period_label(1914) == "modernist"


def test_corr_basic() -> None:
    x = [1.0, 2.0, 3.0, 4.0]
    y = [2.0, 4.0, 6.0, 8.0]
    assert round(_corr(x, y), 6) == 1.0
