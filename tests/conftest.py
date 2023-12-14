import pytest
from src.perfectlurker.eventstream import EventStream
from . import MockEventStreamConsumer


@pytest.fixture
def event_stream():
    es = EventStream()
    return es


@pytest.fixture
def event_consumer(event_stream: EventStream):
    watcher = MockEventStreamConsumer()
    event_stream.add_consumer(watcher.consume)
    return watcher
