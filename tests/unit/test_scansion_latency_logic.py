from scripts.prosody.compute_latency import _compute_deltas, _stress_positions, _syncopation_rate
from scripts.prosody.run_scansion import _infer_meter, _line_stress_pattern


def test_stress_positions_and_deltas() -> None:
    observed = _stress_positions("01010")
    expected = _stress_positions("00101")
    assert observed == [1, 3]
    assert expected == [2, 4]
    assert _compute_deltas(observed, expected) == [-1, -1]


def test_syncopation_rate() -> None:
    assert _syncopation_rate("0101", "0101") == 0.0
    assert _syncopation_rate("0101", "1010") == 1.0


def test_infer_meter_auto() -> None:
    meter, expected = _infer_meter("010101", "auto")
    assert meter in {"iambic", "trochaic", "anapestic", "dactylic"}
    assert len(expected) == 6


def test_line_stress_pattern_nonempty() -> None:
    pattern = _line_stress_pattern("The meter bends and breaks")
    assert len(pattern) > 0
