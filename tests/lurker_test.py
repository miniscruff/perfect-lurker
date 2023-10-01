import pytest
from src.perfectlurker.lurker import Lurker
from src.perfectlurker.eventstream import EventStream
from src.perfectlurker.events import (
    ChatMessageEvent,
    JoinedRaceEvent,
    LeftRaceEvent,
    SetPointsEvent,
)
from . import MockEventStreamConsumer


class TestLurker:
    def test_can_compare_lurkers(self):
        lurk_a1 = Lurker("a", "image_a")
        lurk_a2 = Lurker("a", "image_a")
        assert lurk_a1 == lurk_a2

    def test_can_compare_non_lurkers(self):
        lurk = Lurker("c", "image_c")
        assert lurk != 15

    @pytest.mark.asyncio
    async def test_can_not_add_points_if_not_in_race(
        self,
        event_stream: EventStream,
        event_consumer: MockEventStreamConsumer,
    ):
        l = Lurker("not_in_race_lurker", "my_image")
        await l.add_points(event_stream, 2)
        await l.leave_race(event_stream)
        assert l.points == 0
        assert not l.in_race
        assert event_consumer.events == [
            ChatMessageEvent("@not_in_race_lurker you aint even in the race"),
        ]

    @pytest.mark.asyncio
    async def test_can_add_points_if_in_race(
        self,
        event_stream: EventStream,
        event_consumer: MockEventStreamConsumer,
    ):
        l = Lurker("pts_lurker", "my_image")
        await l.join_race(event_stream)
        await l.add_points(event_stream, 2)
        assert l.in_race
        assert l.points == 2
        assert event_consumer.events == [
            JoinedRaceEvent(l),
            ChatMessageEvent("LET'S GO! @pts_lurker IS IN THIS"),
            SetPointsEvent(l, 2),
        ]

    @pytest.mark.asyncio
    async def test_can_lose_points(
        self,
        event_stream: EventStream,
        event_consumer: MockEventStreamConsumer,
    ):
        l = Lurker("lose_lurker", "my_image")
        await l.join_race(event_stream)
        await l.add_points(event_stream, 2)
        await l.add_points(event_stream, -1)
        await l.add_points(event_stream, 0)
        assert l.in_race
        assert l.points == 1
        assert event_consumer.events == [
            JoinedRaceEvent(l),
            ChatMessageEvent("LET'S GO! @lose_lurker IS IN THIS"),
            SetPointsEvent(l, 2),
            SetPointsEvent(l, 1),
        ]

    @pytest.mark.asyncio
    async def test_can_not_rejoin_race_if_left(
        self,
        event_stream: EventStream,
        event_consumer: MockEventStreamConsumer,
    ):
        l = Lurker("leave_lurker", "my_image")
        await l.join_race(event_stream)
        await l.join_race(event_stream)
        await l.add_points(event_stream, 2)
        await l.leave_race(event_stream)
        await l.join_race(event_stream)
        assert not l.in_race
        assert event_consumer.events == [
            JoinedRaceEvent(l),
            ChatMessageEvent("LET'S GO! @leave_lurker IS IN THIS"),
            ChatMessageEvent("@leave_lurker you are already in the race"),
            SetPointsEvent(l, 2),
            LeftRaceEvent(l),
            ChatMessageEvent("Ok then, @leave_lurker ditched us"),
            ChatMessageEvent("@leave_lurker you already left the race"),
        ]

    @pytest.mark.asyncio
    async def test_position_wraps_track(
        self,
        event_stream: EventStream,
    ):
        l = Lurker("wrap_lurker", "my_image")
        await l.join_race(event_stream)
        await l.add_points(event_stream, 65)
        assert l.position == 5
