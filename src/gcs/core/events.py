import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ControllerConnected:
    name: str


@dataclass(frozen=True)
class ControllerDisconnected:
    name: str


@dataclass(frozen=True)
class InputState:
    """One snapshot of all input, produced at every sampling tick."""
    axes: dict          # e.g. {"left_x": 0.0, "left_y": -0.4}
    buttons: dict       # e.g. {"a": True}
    hat: tuple = (0, 0)
    timestamp: float = field(default_factory=time.monotonic)

@dataclass(frozen=True)
class LoadProfileRequest:
    """Ask the profile manager to switch to the named profile (from the GUI, a script, ...)."""

    name: str


@dataclass(frozen=True)
class ProfileChanged:
    """A profile became active. `data` is the profile as a plain dict (JSON-compatible)."""

    name: str
    data: dict