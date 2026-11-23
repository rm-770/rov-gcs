def apply_deadzone(value, deadzone):
    """Zero small values and rescale the rest so the output spans 0..1 smoothly."""
    if not 0.0 <= deadzone < 1.0:
        raise ValueError("deadzone must be in [0, 1)")
    if abs(value) < deadzone:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - deadzone) / (1.0 - deadzone)


def apply_deadzone_to_axes(axes, deadzone):
    """Return a new dict with the dead-zone applied to every axis value."""
    return {name: apply_deadzone(v, deadzone) for name, v in axes.items()}