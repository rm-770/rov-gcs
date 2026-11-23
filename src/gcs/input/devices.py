from abc import ABC, abstractmethod

import pygame


class InputDevice(ABC):
    """Anything that can be asked for its current state."""

    @abstractmethod
    def read(self):
        """Return a dict: {"axes": {...}, "buttons": {...}, "hat": (x, y)}."""


class GamepadDevice(InputDevice):
    def __init__(self, index=0):
        pygame.joystick.init()
        self._joy = pygame.joystick.Joystick(index)
        self.name = self._joy.get_name()

    def read(self):
        pygame.event.pump()   # lets pygame refresh joystick state
        axes = {f"axis_{i}": self._joy.get_axis(i) for i in range(self._joy.get_numaxes())}
        buttons = {f"button_{i}": bool(self._joy.get_button(i)) for i in range(self._joy.get_numbuttons())}
        hat = self._joy.get_hat(0) if self._joy.get_numhats() > 0 else (0, 0)
        return {"axes": axes, "buttons": buttons, "hat": hat}