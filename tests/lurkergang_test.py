import pytest
from src.perfectlurker.events import JoinRaceAttemptedEvent, LeaveRaceAttemptedEvent
from src.perfectlurker.eventstream import EventStream
from src.perfectlurker.lurker import Lurker
from src.perfectlurker.lurkergang import LurkerGang


class TestLurkerGang:
    def test_basic_collection_operations(self, event_stream: EventStream):
        lurk_a = Lurker("a", "a_image")
        lurk_b = Lurker("b", "b_image")
        gang = LurkerGang(event_stream)
        gang.add(lurk_a)
        gang.add(lurk_b)
        assert list(gang) == [lurk_a, lurk_b]
        assert gang["a"] == lurk_a
        assert gang["b"] == lurk_b

    @pytest.mark.asyncio
    async def test_can_join_and_leave_race(self, event_stream: EventStream):
        lurk = Lurker("c", "c_image")
        gang = LurkerGang(event_stream)
        gang.add(lurk)

        await event_stream.send(JoinRaceAttemptedEvent("c"))
        assert lurk.in_race

        await event_stream.send(LeaveRaceAttemptedEvent("c"))
        assert not lurk.in_race

    @pytest.mark.asyncio
    async def test_join_leave_when_not_existing_no_ops(self, event_stream: EventStream):
        "this mostly tests we don't crash on missing lurkers"
        gang = LurkerGang(event_stream)

        await event_stream.send(JoinRaceAttemptedEvent("c"))
        await event_stream.send(LeaveRaceAttemptedEvent("c"))
        assert gang["a"] is None
