"""Entry point: wires the modules together and runs until Ctrl+C."""

import argparse
import logging
import queue
import time

from gcs.core.config import load_config
from gcs.core.eventbus import EventBus
from gcs.core.events import InputState
from gcs.core.logging_setup import setup_logging
from gcs.input.devices import GamepadDevice, KeyboardDevice
from gcs.input.profiles import ProfileManager, ProfileStore
from gcs.input.sampler import InputSampler


def main():
    # R19: the config file path is chosen on the command line, not hard-coded.
    parser = argparse.ArgumentParser(description="AAST Triton ROV ground control station")
    parser.add_argument("--config", default="config/default.yaml", help="path to the YAML config")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(level=config["logging"]["level"], logfile=config["logging"]["file"])
    log = logging.getLogger(__name__)
    log.info("GCS starting")

    # The bus is the only thing the modules share.
    bus = EventBus()
    states = bus.subscribe(InputState, maxsize=500)

    # Build the parts. Nothing here talks to anything else directly.
    gamepad = GamepadDevice(bus)
    keyboard = KeyboardDevice()
    devices = [gamepad, keyboard]
    store = ProfileStore(config["profiles"]["directory"])
    profiles = ProfileManager(bus, store, config["profiles"]["default"])
    sampler = InputSampler(
        bus,
        config["input"]["rate_hz"],
        devices=devices,
        deadzone=config["input"]["deadzone"],
    )

    profiles.start()
    sampler.start()
    log.info("Running. Press Ctrl+C to stop.")

    try:
        latest = None
        while True:
            time.sleep(1.0)
            # Drain the queue so it never fills up, keeping only the newest state.
            while True:
                try:
                    latest = states.get_nowait()
                except queue.Empty:
                    break
            if latest is not None:
                log.info("Latest input: axes=%s buttons=%s", latest.axes, latest.buttons)
    except KeyboardInterrupt:
        log.info("Ctrl+C received; shutting down")
    finally:
        # Ask the threads to stop first, then wait for them, then release the devices.
        sampler.stop()
        profiles.stop()
        sampler.join(timeout=2.0)
        profiles.join(timeout=2.0)
        for device in devices:
            device.close()
        log.info("GCS stopped")


if __name__ == "__main__":
    main()