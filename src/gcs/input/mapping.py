"""Translate raw input names (axis_1, key_w) into action names (surge, light_toggle)."""

from dataclasses import asdict, dataclass, field

from gcs.input.deadzone import apply_deadzone


@dataclass(frozen=True)
class AxisBinding:
    """How one raw axis becomes an action."""

    action: str                    # the name this axis is published under, e.g. "surge"
    invert: bool = False           # flip the sign (stick "up" reads negative, for example)
    scale: float = 1.0             # sensitivity: 0.5 halves the output
    deadzone: float | None = None  # None means "use the profile's default"
    trigger: bool = False          # True for L2/R2: rescale -1..1 into 0..1 first

    def __post_init__(self):
        # Reject bad values when the profile loads, not later at 50 Hz in the sampler.
        if self.deadzone is not None and not 0.0 <= self.deadzone < 1.0:
            raise ValueError(f"deadzone for {self.action!r} must be in [0, 1)")


@dataclass(frozen=True)
class Mapping:
    """A complete, immutable set of bindings. Immutable means it is safe to hand around."""

    name: str = "raw"
    controllers: tuple = ()          # controller names this profile is for (auto-load)
    default_deadzone: float = 0.10
    axes: dict = field(default_factory=dict)     # raw axis name -> AxisBinding
    buttons: dict = field(default_factory=dict)  # raw button/key name -> action name

    def __post_init__(self):
        if not 0.0 <= self.default_deadzone < 1.0:
            raise ValueError("default_deadzone must be in [0, 1)")

    def apply(self, raw_axes, raw_buttons):
        """Return (axes, buttons) keyed by action name instead of raw name."""
        axes = {}
        for raw_name, value in raw_axes.items():
            binding = self.axes.get(raw_name)
            if binding is None:
                # Unmapped: keep the raw name, but still protect against stick drift.
                axes[raw_name] = apply_deadzone(value, self.default_deadzone)
                continue

            # Triggers rest at -1.0 and reach +1.0 when fully pressed. Shift and halve the
            # range so that rest becomes 0.0 and fully pressed becomes 1.0.
            if binding.trigger:
                value = (value + 1.0) / 2.0

            # A per-axis dead-zone wins over the profile default.
            zone = binding.deadzone if binding.deadzone is not None else self.default_deadzone
            result = apply_deadzone(value, zone)
            if binding.invert:
                result = 0.0 - result  # "0.0 - x" avoids producing -0.0 for a resting stick
            # Clamp to [-1, 1] so a large scale factor cannot exceed full deflection.
            result = max(-1.0, min(1.0, result * binding.scale))

            # If two raw axes feed one action, the one pushed hardest wins.
            if abs(result) >= abs(axes.get(binding.action, 0.0)):
                axes[binding.action] = result

        buttons = {}
        for raw_name, pressed in raw_buttons.items():
            action = self.buttons.get(raw_name, raw_name)
            # If a gamepad button and a key share an action, either one triggers it (OR).
            buttons[action] = buttons.get(action, False) or pressed
        return axes, buttons

    @classmethod
    def from_dict(cls, data):
        """Build a Mapping from plain data (as loaded from JSON). Raises ValueError if bad."""
        try:
            axes = {raw: AxisBinding(**b) for raw, b in data.get("axes", {}).items()}
            return cls(
                name=data["name"],
                controllers=tuple(data.get("controllers", [])),
                default_deadzone=data.get("default_deadzone", 0.10),
                axes=axes,
                buttons=dict(data.get("buttons", {})),
            )
        except (KeyError, TypeError, AttributeError) as exc:
            # Turn "missing key" / "unknown field" into one clear error type for callers.
            raise ValueError(f"invalid profile: {exc!r}") from exc

    def to_dict(self):
        """The inverse of from_dict: plain data that json.dumps can write."""
        return {
            "name": self.name,
            "controllers": list(self.controllers),
            "default_deadzone": self.default_deadzone,
            "axes": {raw: asdict(binding) for raw, binding in self.axes.items()},
            "buttons": dict(self.buttons),
        }