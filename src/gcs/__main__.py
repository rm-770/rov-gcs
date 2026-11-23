import logging
import time

from gcs.core.config import load_config
from gcs.core.eventbus import EventBus
from gcs.core.events import InputState
from gcs.core.logging_setup import setup_logging
from gcs.input.devices import GamepadDevice
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

    device = GamepadDevice()
    log.info("Using controller: %s", device.name)

    sampler = InputSampler(bus, config["input"]["rate_hz"], device)
    sampler.start()
    try:
        time.sleep(2)
    finally:
        sampler.stop()
        sampler.join()

    log.info("Received %d input states in 2 s", q.qsize())


if __name__ == "__main__":
    main()