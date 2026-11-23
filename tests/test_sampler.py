import time

from gcs.core.eventbus import EventBus
from gcs.core.events import InputState, ProfileChanged
from gcs.input.sampler import InputSampler


class FakeDevice:
    """Stands in for a real gamepad so tests need no hardware."""

    def read(self):
        return {"axes": {"axis_0": 0.0}, "buttons": {}, "hat": (0, 0)}


class BrokenDevice:
    """Simulates a device that raises on every read (for example, a driver error)."""

    def read(self):
        raise RuntimeError("device exploded")


def _drain(q):
    """Collect everything currently in a queue into a list."""
    items = []
    while not q.empty():
        items.append(q.get_nowait())
    return items


def test_sampler_publishes_at_roughly_the_configured_rate():
    bus = EventBus()
    q = bus.subscribe(InputState, maxsize=1000)
    sampler = InputSampler(bus, rate_hz=50, devices=[FakeDevice()])
    sampler.start()
    time.sleep(1.0)
    sampler.stop()
    sampler.join(timeout=1.0)
    assert not sampler.is_alive()
    assert 40 <= q.qsize() <= 60   # wide tolerance: timing tests must not be brittle


def test_sampler_survives_a_failing_device():
    bus = EventBus()
    q = bus.subscribe(InputState, maxsize=1000)
    sampler = InputSampler(bus, rate_hz=50, devices=[BrokenDevice(), FakeDevice()])
    sampler.start()
    time.sleep(0.5)
    still_running = sampler.is_alive()
    sampler.stop()
    sampler.join(timeout=1.0)
    assert still_running
    assert q.qsize() > 10          # the healthy device kept producing states


def test_sampler_applies_a_new_profile_without_restarting():
    bus = EventBus()
    q = bus.subscribe(InputState, maxsize=1000)
    sampler = InputSampler(bus, rate_hz=50, devices=[FakeDevice()])
    sampler.start()
    time.sleep(0.2)
    profile = {"name": "p", "axes": {"axis_0": {"action": "yaw"}}}
    bus.publish(ProfileChanged(name="p", data=profile))
    time.sleep(0.3)
    sampler.stop()
    sampler.join(timeout=1.0)
    states = _drain(q)
    assert "axis_0" in states[0].axes     # before: the raw name
    assert "yaw" in states[-1].axes       # after: the mapped action name