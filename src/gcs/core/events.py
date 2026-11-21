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