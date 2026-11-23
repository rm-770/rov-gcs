import logging
import time

from gcs.core.config import load_config
from gcs.core.eventbus import EventBus
from gcs.core.events import InputState
from gcs.core.logging_setup import setup_logging
from gcs.input.devices import GamepadDevice, KeyboardDevice
from gcs.input.sampler import InputSampler


def main():
    config = load_config()
    setup_logging(
        level=config["logging"]["level"],
        logfile=config["logging"]["file"],
    )
    log = logging.getLogger(__name__)
    log.info("GCS starting")

    bus = EventBus()
    q = bus.subscribe(InputState, maxsize=500)

    gamepad = GamepadDevice()                                  # CHANGED
    keyboard = KeyboardDevice()                                # CHANGED
    log.info("Using controller: %s", gamepad.name)

    sampler = InputSampler(
        bus,
        config["input"]["rate_hz"],
        devices=[gamepad, keyboard],
        deadzone=config["input"]["deadzone"],
    )
    sampler.start()
    try:
        time.sleep(2)
    finally:
        sampler.stop()
        sampler.join()
        keyboard.close()                
        last = None
        while not q.empty():
            last = q.get_nowait()
            log.info("Last state: %s", last)                       # stop pynput's thread

    log.info("Received %d input states in 2 s", q.qsize())


if __name__ == "__main__":
    main()