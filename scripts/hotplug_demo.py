"""Manual hot-plug check. Run it, then unplug and replug the controller."""

import time

from gcs.core.eventbus import EventBus
from gcs.core.logging_setup import setup_logging
from gcs.input.devices import GamepadDevice
from gcs.input.sampler import InputSampler

setup_logging(logfile="logs/hotplug_demo.log")

bus = EventBus()
# Nobody subscribes to InputState here, so published states are simply discarded.
sampler = InputSampler(bus, 50, devices=[GamepadDevice(bus)])
sampler.start()

print("Unplug and replug the controller. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(0.5)       # the main thread just waits; the sampler thread does the work
except KeyboardInterrupt:
    pass
finally:
    sampler.stop()
    sampler.join()