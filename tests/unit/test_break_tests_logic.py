import numpy as np

from scripts.stats.run_break_tests import _chow_statistic


def test_chow_statistic_detects_break() -> None:
    x = np.arange(20, dtype=float)
    y = np.array([v * 0.2 for v in x[:10]] + [5 + v * 1.2 for v in x[10:]], dtype=float)

    stat = _chow_statistic(x, y, split_idx=10)
    assert stat > 0.0


def test_chow_statistic_invalid_split_returns_zero() -> None:
    x = np.arange(8, dtype=float)
    y = x * 0.5
    assert _chow_statistic(x, y, split_idx=1) == 0.0
