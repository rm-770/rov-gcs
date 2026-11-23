import pytest

from gcs.input.deadzone import apply_deadzone, apply_deadzone_to_axes


def test_value_inside_deadzone_is_zero():
    # Both directions: stick drift can be positive or negative.
    assert apply_deadzone(0.05, 0.10) == 0.0
    assert apply_deadzone(-0.05, 0.10) == 0.0


def test_value_exactly_at_the_edge_is_zero():
    # The rescaled output starts at 0, so there is no sudden lurch when leaving the zone.
    assert apply_deadzone(0.10, 0.10) == 0.0


def test_full_deflection_still_reaches_one():
    # approx() is needed because floating-point results can be 0.9999999.
    assert apply_deadzone(1.0, 0.10) == pytest.approx(1.0)
    assert apply_deadzone(-1.0, 0.10) == pytest.approx(-1.0)


def test_value_is_rescaled_outside_deadzone():
    # (0.55 - 0.10) / 0.90 = 0.5
    assert apply_deadzone(0.55, 0.10) == pytest.approx(0.5)
    assert apply_deadzone(-0.55, 0.10) == pytest.approx(-0.5)


def test_zero_deadzone_changes_nothing():
    assert apply_deadzone(0.37, 0.0) == pytest.approx(0.37)


def test_invalid_deadzone_raises():
    with pytest.raises(ValueError):
        apply_deadzone(0.5, 1.0)
    with pytest.raises(ValueError):
        apply_deadzone(0.5, -0.1)


def test_axes_helper_applies_to_every_axis():
    result = apply_deadzone_to_axes({"axis_0": 0.05, "axis_1": 1.0}, 0.10)
    assert result["axis_0"] == 0.0
    assert result["axis_1"] == pytest.approx(1.0)