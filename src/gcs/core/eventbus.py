import logging
import queue
import threading

log = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers = {}          # event type -> list of queues
        self._lock = threading.Lock()   # protects _subscribers

    def subscribe(self, event_type, maxsize=100):
        """Return a new Queue that will receive every event of event_type."""
        
        q = queue.Queue(maxsize=maxsize)
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(q)
        return q

    def publish(self, event):
        """Put the event into the queue of every subscriber of its type."""

        with self._lock:
            queues = list(self._subscribers.get(type(event), []))
  
        for q in queues:
            try:
                q.put_nowait(event)
            except queue.Full:
                log.warning("Event queue for %s is full; dropping event", type(event).__name__)