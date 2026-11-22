import time

from gcs.core.eventbus import EventBus
from gcs.core.events import InputState
from gcs.input.sampler import InputSampler


def test_sampler_publishes_at_roughly_the_configured_rate():
    bus = EventBus()
    q = bus.subscribe(InputState, maxsize=1000)
    sampler = InputSampler(bus, rate_hz=50)

    sampler.start()
    time.sleep(1.0)
    sampler.stop()
    sampler.join(timeout=1.0)

    assert not sampler.is_alive()
    assert 40 <= q.qsize() <= 60