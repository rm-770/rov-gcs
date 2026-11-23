"""The fixed-rate input sampling thread (R3). It touches only devices and the bus."""

import logging
import queue
import threading
import time

from gcs.core.events import InputState, ProfileChanged
from gcs.input.mapping import Mapping

log = logging.getLogger(__name__)


class InputSampler(threading.Thread):
    """Reads all devices at a fixed rate, applies the mapping, publishes InputState."""

    def __init__(self, bus, rate_hz, devices, deadzone=0.0):
        # daemon=True: this thread will not keep the program alive if the main thread exits.
        super().__init__(name="InputSampler", daemon=True)
        self._bus = bus
        self._period = 1.0 / rate_hz       # seconds between samples
        self._devices = devices            # list of objects with a read() method
        # NOT named _stop: threading.Thread already has an internal _stop method.
        self._stop_event = threading.Event()
        # Until a profile arrives, use a "raw" mapping: raw names with a plain dead-zone.
        self._mapping = Mapping(default_deadzone=deadzone)
        # Subscribe here (main thread) so a profile published right after start() is not lost.
        self._profile_queue = bus.subscribe(ProfileChanged, maxsize=10)
        self._failed = set()               # devices currently failing, so we log only once

    def stop(self):
        """Ask the thread to finish. Safe to call from any thread."""
        self._stop_event.set()

    def _apply_pending_profiles(self):
        """Switch to the newest profile announced on the bus, if any (non-blocking)."""
        while True:
            try:
                event = self._profile_queue.get_nowait()
            except queue.Empty:
                return
            try:
                # Only this thread ever uses self._mapping, so no lock is needed.
                self._mapping = Mapping.from_dict(event.data)
            except ValueError:
                log.exception("Ignoring invalid profile %r", event.name)
            else:
                log.info("Mapping switched to profile %r", event.name)

    def _read_input(self):
        """Read every device, merge the raw readings, then apply the mapping."""
        raw_axes, raw_buttons, hat = {}, {}, (0, 0)
        for device in self._devices:
            try:
                state = device.read()
            except Exception:
                # One broken device must never kill the sampler (R4). Log it once, not 50x/s.
                if device not in self._failed:
                    log.exception("Device %r failed; treating it as neutral", device)
                    self._failed.add(device)
                continue
            self._failed.discard(device)  # it works again, so log a future failure afresh
            # Axis and button names from different devices cannot clash, so update() is safe.
            raw_axes.update(state["axes"])
            raw_buttons.update(state["buttons"])
            if state["hat"] != (0, 0):
                hat = state["hat"]
        axes, buttons = self._mapping.apply(raw_axes, raw_buttons)
        return InputState(axes=axes, buttons=buttons, hat=hat)

    def run(self):
        log.info("Sampler started at %.1f Hz", 1.0 / self._period)
        next_tick = time.monotonic()   # monotonic never jumps when the system clock changes
        while not self._stop_event.is_set():
            self._apply_pending_profiles()
            self._bus.publish(self._read_input())

            # Advance the deadline by exactly one period, so the rate does not drift.
            next_tick += self._period
            delay = next_tick - time.monotonic()
            if delay > 0:
                # Like sleep(), but wakes immediately if stop() is called.
                self._stop_event.wait(delay)
            else:
                # We fell behind. Forget the backlog instead of firing a burst of stale ticks.
                next_tick = time.monotonic()
        log.info("Sampler stopped")