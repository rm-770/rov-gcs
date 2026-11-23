"""Dead-zone maths for analogue axes (R5). Pure functions: no threads, no hardware."""


def apply_deadzone(value, deadzone):
    """Zero small values and rescale the rest so the output still spans 0..1 smoothly."""
    # A dead-zone of 1.0 or more would zero every input; a negative one makes no sense.
    if not 0.0 <= deadzone < 1.0:
        raise ValueError("deadzone must be in [0, 1)")

    # Inside the dead-zone the stick counts as "at rest", so the vehicle must not move.
    if abs(value) < deadzone:
        return 0.0

    # abs() throws away the direction, so remember it separately.
    sign = 1.0 if value > 0 else -1.0

    # Rescale the remaining range: just outside the zone gives ~0, full deflection gives 1.
    # Without this, the output would jump from 0.0 straight to the dead-zone size.
    # min() guards against a driver that reports slightly more than 1.0.
    magnitude = min(1.0, (abs(value) - deadzone) / (1.0 - deadzone))
    return sign * magnitude


def apply_deadzone_to_axes(axes, deadzone):
    """Return a NEW dict with the dead-zone applied to every axis value."""
    return {name: apply_deadzone(value, deadzone) for name, value in axes.items()}