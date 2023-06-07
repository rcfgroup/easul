
from easul.visual import element as E


def test_positive_swatch_produces_correct_indexes_for_values():
    swatch = E.TrafficLightSwatch(0,100,10)
    assert swatch.range_size == 100
    assert len(swatch.patches) == 10
    assert swatch.get_step_idx_to_show(57) == 4
    assert swatch.get_step_idx_to_show(5) == 9
    assert swatch.get_step_idx_to_show(99) == 0

    assert swatch.get_step_idx_to_show(100) == 0
    assert swatch.get_step_idx_to_show(1) == 9
    assert swatch.get_step_idx_to_show(0) == 9

def test_non_zero_swatch_produces_correct_indexes_for_values():
    swatch = E.TrafficLightSwatch(1,11,1)
    assert swatch.range_size == 10
    assert len(swatch.patches) == 10
    assert swatch.get_step_idx_to_show(1) == 9
    assert swatch.get_step_idx_to_show(11) == 0
    assert swatch.get_step_idx_to_show(2) == 8
    assert swatch.get_step_idx_to_show(10) == 0

def test_negative_swatch_produces_correct_indexes_for_values():
    swatch = E.TrafficLightSwatch(-1,1,0.1)
    assert swatch.range_size == 2
    assert len(swatch.patches) == 20
    assert swatch.get_step_idx_to_show(0) == 9
    assert swatch.get_step_idx_to_show(-1) == 19
    assert swatch.get_step_idx_to_show(1) == 0
    assert swatch.get_step_idx_to_show(0.1) == 8
    assert swatch.get_step_idx_to_show(-0.1) == 10
    assert swatch.get_step_idx_to_show(0.5) == 4
    assert swatch.get_step_idx_to_show(-0.5) == 14
