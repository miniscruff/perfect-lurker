from typing import List
from src.perfectlurker.events import Event


class MockEventStreamConsumer:
    def __init__(self):
        self.events: List[Event] = []

    async def consume(self, ev: Event):
        self.events.append(ev)
