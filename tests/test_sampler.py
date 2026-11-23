import time

from gcs.core.eventbus import EventBus
from gcs.core.events import InputState
from gcs.input.sampler import InputSampler


class FakeDevice:
    """Stands in for a real gamepad so the test needs no hardware."""

    def read(self):
        return {"axes": {"axis_0": 0.0}, "buttons": {}, "hat": (0, 0)}


def test_sampler_publishes_at_roughly_the_configured_rate():
    bus = EventBus()
    q = bus.subscribe(InputState, maxsize=1000)
    sampler = InputSampler(bus, rate_hz=50, devices=[FakeDevice()])

    sampler.start()
    time.sleep(1.0)
    sampler.stop()
    sampler.join(timeout=1.0)

    assert not sampler.is_alive()
    assert 40 <= q.qsize() <= 60