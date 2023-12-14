import pytest
from src.perfectlurker.eventstream import EventStream
from src.perfectlurker.events import Event, SocketEvent
from tests import MockEventStreamConsumer


class TestEventStream:
    @pytest.mark.asyncio
    async def test_can_consume_async_event(self, event_stream: EventStream):
        async def consumer(ev: Event):
            if not isinstance(ev, SocketEvent):
                return
            assert ev.packet() == "555,some_data"

        event_stream.add_consumer(consumer)
        await event_stream.send(SocketEvent(555, ["some_data"]))

    @pytest.mark.asyncio
    async def test_can_produce_while_consuming(
        self,
        event_stream: EventStream,
        event_consumer: MockEventStreamConsumer,
    ):
        class RecursiveConsumer:
            def __init__(self, es: EventStream):
                self.es = es

            async def consumer(self, ev: Event):
                if not isinstance(ev, SocketEvent):
                    return
                # this creates a chain of events were we consume an event we sent,
                # and then send another event.
                if ev.code == 500:
                    await self.es.send(SocketEvent(501, ["second"]))
                elif ev.code == 501:
                    await self.es.send(SocketEvent(502, ["third"]))

        event_stream.add_consumer(RecursiveConsumer(event_stream).consumer)
        await event_stream.send(SocketEvent(500, ["first"]))
        assert event_consumer.events == [
            SocketEvent(500, ["first"]),
            SocketEvent(501, ["second"]),
            SocketEvent(502, ["third"]),
        ]
