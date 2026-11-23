import pytest

from gcs.input.deadzone import apply_deadzone, apply_deadzone_to_axes


def test_value_inside_deadzone_is_zero():
    assert apply_deadzone(0.05, 0.10) == 0.0
    assert apply_deadzone(-0.05, 0.10) == 0.0


def test_full_deflection_still_reaches_one():
    assert apply_deadzone(1.0, 0.10) == pytest.approx(1.0)
    assert apply_deadzone(-1.0, 0.10) == pytest.approx(-1.0)


def test_value_is_rescaled_outside_deadzone():
    assert apply_deadzone(0.55, 0.10) == pytest.approx(0.5)
    assert apply_deadzone(-0.55, 0.10) == pytest.approx(-0.5)


def test_invalid_deadzone_raises():
    with pytest.raises(ValueError):
        apply_deadzone(0.5, 1.0)