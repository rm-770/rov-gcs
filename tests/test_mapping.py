import pytest

from gcs.input.mapping import AxisBinding, Mapping


def test_axis_is_renamed_inverted_and_scaled():
    mapping = Mapping(default_deadzone=0.1, axes={"axis_1": AxisBinding("surge", invert=True)})
    axes, _ = mapping.apply({"axis_1": 1.0}, {})
    assert axes["surge"] == pytest.approx(-1.0)


def test_unmapped_axis_keeps_its_raw_name():
    axes, _ = Mapping(default_deadzone=0.1).apply({"axis_9": 1.0}, {})
    assert axes["axis_9"] == pytest.approx(1.0)


def test_resting_stick_is_zero_and_never_negative_zero():
    mapping = Mapping(default_deadzone=0.1, axes={"axis_1": AxisBinding("surge", invert=True)})
    axes, _ = mapping.apply({"axis_1": 0.03}, {})
    assert str(axes["surge"]) == "0.0"


def test_per_axis_deadzone_overrides_default():
    mapping = Mapping(default_deadzone=0.05, axes={"axis_0": AxisBinding("yaw", deadzone=0.3)})
    axes, _ = mapping.apply({"axis_0": 0.2}, {})
    assert axes["yaw"] == 0.0


def test_scale_is_clamped_to_one():
    mapping = Mapping(default_deadzone=0.0, axes={"axis_0": AxisBinding("yaw", scale=5.0)})
    axes, _ = mapping.apply({"axis_0": 0.9}, {})
    assert axes["yaw"] == 1.0


def test_two_buttons_on_one_action_are_ored():
    mapping = Mapping(buttons={"button_0": "light", "key_space": "light"})
    _, buttons = mapping.apply({}, {"button_0": False, "key_space": True})
    assert buttons == {"light": True}


def test_dict_round_trip():
    original = Mapping(
        name="p",
        controllers=("Pad X",),
        axes={"axis_0": AxisBinding("yaw", invert=True, deadzone=0.2)},
        buttons={"button_0": "light"},
    )
    assert Mapping.from_dict(original.to_dict()) == original


def test_bad_profiles_raise_value_error():
    with pytest.raises(ValueError):
        Mapping.from_dict({})                                         # no name
    with pytest.raises(ValueError):
        Mapping.from_dict({"name": "x", "default_deadzone": 2})       # dead-zone out of range
    with pytest.raises(ValueError):
        Mapping.from_dict({"name": "x", "axes": {"a": {"nope": 1}}})  # unknown field


def test_trigger_rests_at_zero_and_reaches_one():
    mapping = Mapping(
        default_deadzone=0.0,
        axes={"axis_5": AxisBinding("tilt_up", trigger=True)},
    )
    resting, _ = mapping.apply({"axis_5": -1.0}, {})   # trigger untouched
    half, _ = mapping.apply({"axis_5": 0.0}, {})       # trigger halfway
    full, _ = mapping.apply({"axis_5": 1.0}, {})       # trigger fully pressed
    assert resting["tilt_up"] == 0.0
    assert half["tilt_up"] == pytest.approx(0.5)
    assert full["tilt_up"] == pytest.approx(1.0)


def test_trigger_flag_survives_a_save_and_load():
    original = Mapping(name="p", axes={"axis_4": AxisBinding("tilt_down", trigger=True)})
    assert Mapping.from_dict(original.to_dict()) == original