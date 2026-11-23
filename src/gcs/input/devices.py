import threading
from abc import ABC, abstractmethod

import pygame
from pynput import keyboard


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




class KeyboardDevice(InputDevice):
    def __init__(self):
        self.name = "keyboard"
        self._pressed = set()
        self._lock = threading.Lock()
        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.start()

    @staticmethod
    def _key_name(key):
        """Letters give key.char; special keys (space, shift) give key.name."""
        char = getattr(key, "char", None)
        if char:
            return char.lower()
        return getattr(key, "name", str(key))

    def _on_press(self, key):
        with self._lock:
            self._pressed.add(self._key_name(key))

    def _on_release(self, key):
        with self._lock:
            self._pressed.discard(self._key_name(key))

    def read(self):
        with self._lock:
            pressed_copy = set(self._pressed)
        return {"axes": {}, "buttons": {f"key_{k}": True for k in pressed_copy}, "hat": (0, 0)}

    def close(self):
        self._listener.stop()