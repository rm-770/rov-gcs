import logging
import threading
import time

from gcs.core.events import InputState

log = logging.getLogger(__name__)


class InputSampler(threading.Thread):
    def __init__(self, bus, rate_hz, device):
        super().__init__(name="InputSampler", daemon=True)
        self._bus = bus
        self._period = 1.0 / rate_hz
        self._stop_event = threading.Event()
        self._device = device

    def _read_input(self):
        state = self._device.read()
        return InputState(axes=state["axes"], buttons=state["buttons"], hat=state["hat"])

    def stop(self):
        self._stop_event.set()

    def _read_input(self):
        """Stub for now: pretend nothing is pressed."""
        return InputState(axes={"left_x": 0.0}, buttons={})

    def run(self):
        log.info("Sampler started at %.1f Hz", 1.0 / self._period)
        next_tick = time.monotonic()
        while not self._stop_event.is_set():
            input_state = self._read_input()
            self._bus.publish(input_state)

            next_tick += self._period


            delay = next_tick - time.monotonic()
            if delay > 0: 
                self._stop_event.wait(delay)
            else: 
                next_tick = time.monotonic()

        log.info("Sampler stopped")