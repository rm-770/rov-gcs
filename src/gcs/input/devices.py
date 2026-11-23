"""Input devices: anything that can report its current state through read()."""

import logging
import os
import threading
from abc import ABC, abstractmethod

import pygame
from pynput import keyboard

# These are the shared "contract" types, so importing them does not couple us to other modules.
from gcs.core.events import ControllerConnected, ControllerDisconnected

log = logging.getLogger(__name__)


def _neutral_state():
    """A 'nothing pressed, sticks centred' reading. A fresh dict each call, so no sharing."""
    return {"axes": {}, "buttons": {}, "hat": (0, 0)}


class InputDevice(ABC):
    """Anything that can be asked for its current state."""

    @abstractmethod
    def read(self):
        """Return a dict: {"axes": {...}, "buttons": {...}, "hat": (x, y)}."""

    def close(self):
        """Release resources. The default does nothing, because many devices hold none."""


class GamepadDevice(InputDevice):
    """A game controller that tolerates being unplugged and replugged at any time."""

    def __init__(self, bus=None):
        # The bus is optional so tests and scripts can use the device without one.
        self._bus = bus
        self._joy = None            # the currently open pygame Joystick, or None
        self._instance_id = None    # SDL's id for that joystick, used to match remove events
        self._name = ""
        self._initialised = False   # pygame is initialised lazily, on the sampler thread

    def _ensure_initialised(self):
        """Start pygame's joystick system the first time read() is called."""
        if self._initialised:
            return
        # "dummy" means SDL does not open a real window. setdefault respects a value the
        # user has already set in their environment.
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.display.init()       # the event system needs the display subsystem
        pygame.joystick.init()
        self._initialised = True
        # A controller that was already plugged in at startup: open it straight away.
        if pygame.joystick.get_count() > 0:
            self._open(0)

    def _open(self, device_index):
        """Open the joystick at device_index and tell everyone it is connected."""
        try:
            joy = pygame.joystick.Joystick(device_index)
        except pygame.error:
            log.warning("Controller %d appeared but could not be opened", device_index)
            return
        self._joy = joy
        self._instance_id = joy.get_instance_id()
        self._name = joy.get_name()
        log.info("Controller connected: %s", self._name)
        if self._bus is not None:
            self._bus.publish(ControllerConnected(name=self._name))

    def _close(self):
        """Forget the joystick and tell everyone it is gone."""
        name = self._name
        self._joy = None
        self._instance_id = None
        self._name = ""
        # WARNING level because the operator has lost control and should notice.
        log.warning("Controller disconnected: %s", name)
        if self._bus is not None:
            self._bus.publish(ControllerDisconnected(name=name))
            
    def _recover(self):
        """Reset pygame's joystick subsystem after an internal error, then re-scan."""
        log.warning("pygame joystick error; resetting the joystick subsystem")
        if self._joy is not None:
            self._close()                # announce the loss, as for a normal unplug
        pygame.joystick.quit()           # throw away pygame's (possibly corrupt) joystick table
        pygame.joystick.init()
        # If a controller is still attached after the reset, open it again.
        if pygame.joystick.get_count() > 0:
            self._open(0)

    def read(self):
        self._ensure_initialised()

        try:
            # Drain pygame's event queue. This also refreshes the joystick state.
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED and self._joy is None:
                    self._open(event.device_index)
                elif (
                    event.type == pygame.JOYDEVICEREMOVED
                    and self._joy is not None
                    and event.instance_id == self._instance_id
                ):
                    self._close()
        except (pygame.error, SystemError, KeyError):
            # pygame's internal joystick table got out of step (seen with Bluetooth pads
            # that drop and reconnect). Recover instead of crashing the sampler.
            self._recover()
            return _neutral_state()

        # No controller: report neutral, so the vehicle is told "no input" (the safe value).
        if self._joy is None:
            return _neutral_state()

        try:
            axes = {f"axis_{i}": self._joy.get_axis(i) for i in range(self._joy.get_numaxes())}
            buttons = {
                f"button_{i}": bool(self._joy.get_button(i))
                for i in range(self._joy.get_numbuttons())
            }
            hat = self._joy.get_hat(0) if self._joy.get_numhats() > 0 else (0, 0)
        except (pygame.error, SystemError, KeyError):
            # The device vanished between the event check and the read. Treat as unplugged.
            self._close()
            return _neutral_state()
        return {"axes": axes, "buttons": buttons, "hat": hat}
    

class KeyboardDevice(InputDevice):
    """Keyboard state, collected by pynput's listener thread."""

    def __init__(self):
        self._pressed = set()            # names of keys currently held down
        self._lock = threading.Lock()    # protects _pressed: two threads touch it
        # The Listener runs in its own thread and calls our two methods on key events.
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
        # Runs on pynput's thread. The lock stops it colliding with read().
        with self._lock:
            self._pressed.add(self._key_name(key))

    def _on_release(self, key):
        # discard() does not raise if the key is not in the set.
        with self._lock:
            self._pressed.discard(self._key_name(key))

    def read(self):
        # Copy under the lock, build the result outside it: hold locks as briefly as possible.
        with self._lock:
            pressed = set(self._pressed)
        return {"axes": {}, "buttons": {f"key_{k}": True for k in pressed}, "hat": (0, 0)}

    def close(self):
        # Stops pynput's listener thread so the program can exit cleanly.
        self._listener.stop()