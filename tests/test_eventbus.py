
from gcs.core.eventbus import EventBus
from gcs.core.events import ControllerConnected, ControllerDisconnected


def test_subscriber_receives_matching_event():
    bus = EventBus()
    q = bus.subscribe(ControllerConnected)
    bus.publish(ControllerConnected(name="pad"))
    assert q.get_nowait() == ControllerConnected(name="pad")


def test_subscriber_ignores_other_event_types():
    bus = EventBus()
    q = bus.subscribe(ControllerConnected)
    bus.publish(ControllerDisconnected(name="pad"))
    assert q.empty()


def test_full_queue_does_not_block_publisher():
    bus = EventBus()
    bus.subscribe(ControllerConnected, maxsize=1)
    bus.publish(ControllerConnected(name="a"))
    bus.publish(ControllerConnected(name="b"))   # must return, not hang

def test_full_queue_logs_warning(caplog):
    bus = EventBus()
    bus.subscribe(ControllerConnected, maxsize=1)
    bus.publish(ControllerConnected(name="a"))
    with caplog.at_level("WARNING"):
        bus.publish(ControllerConnected(name="b"))
    assert any("Event queue for ControllerConnected is full" in msg for msg in caplog.messages)

def test_multiple_subscribers_receive_event():
    bus = EventBus()
    q1 = bus.subscribe(ControllerConnected)
    q2 = bus.subscribe(ControllerConnected)
    bus.publish(ControllerConnected(name="pad"))
    assert q1.get_nowait() == ControllerConnected(name="pad")
    assert q2.get_nowait() == ControllerConnected(name="pad")
    
def test_subscriber_receives_multiple_events():
    bus = EventBus()
    q = bus.subscribe(ControllerConnected)
    bus.publish(ControllerConnected(name="pad1"))
    bus.publish(ControllerConnected(name="pad2"))
    assert q.get_nowait() == ControllerConnected(name="pad1")
    assert q.get_nowait() == ControllerConnected(name="pad2")

def test_two_subscribers_receive_event():
    bus = EventBus()
    q1 = bus.subscribe(ControllerConnected)
    q2 = bus.subscribe(ControllerConnected)
    bus.publish(ControllerConnected(name="pad"))
    assert q1.get_nowait() == ControllerConnected(name="pad")
    assert q2.get_nowait() == ControllerConnected(name="pad")
