import pytest
import asyncio
from src.perfectlurker.events import DropBananaEvent
from src.perfectlurker.eventstream import EventStream
from src.perfectlurker.lurker import Lurker
from src.perfectlurker.lurkergang import LurkerGang
from src.perfectlurker.field import Field


class TestField:
    @pytest.mark.asyncio
    async def test_banana_can_hit_lurker_already_in_position(
        self, event_stream: EventStream
    ):
        lg = LurkerGang(event_stream)
        Field(lg, event_stream)
        hit_lurker = Lurker("hit", "hit_image")
        attack_lurker = Lurker("attack", "attack_image")
        lg.add(hit_lurker)
        lg.add(attack_lurker)

        await hit_lurker.join_race(event_stream)
        await attack_lurker.join_race(event_stream)
        await attack_lurker.add_points(event_stream, 10)
        await hit_lurker.add_points(event_stream, 9)

        # if we drop a banana from 10, it is placed on 9
        # where our hit lurker already is, causing them to go to 8
        await event_stream.send(DropBananaEvent(attack_lurker))
        assert hit_lurker.points == 8

    @pytest.mark.asyncio
    async def test_banana_can_hit_lurker_when_they_move(
        self, event_stream: EventStream
    ):
        lg = LurkerGang(event_stream)
        Field(lg, event_stream)
        hit_lurker = Lurker("hit", "hit_image")
        attack_lurker = Lurker("attack", "attack_image")
        lg.add(hit_lurker)
        lg.add(attack_lurker)

        await hit_lurker.join_race(event_stream)
        await attack_lurker.join_race(event_stream)
        await attack_lurker.add_points(event_stream, 15)

        # drop a banana and then move our hit lurker on to it
        await event_stream.send(DropBananaEvent(attack_lurker))
        await hit_lurker.add_points(event_stream, 14)
        assert hit_lurker.points == 13

    @pytest.mark.asyncio
    async def test_banana_ignores_lurker_not_in_race(self, event_stream: EventStream):
        lg = LurkerGang(event_stream)
        field = Field(lg, event_stream)
        hit_lurker = Lurker("hit", "hit_image")
        attack_lurker = Lurker("attack", "attack_image")
        lg.add(hit_lurker)
        lg.add(attack_lurker)

        # move our hit lurker to 14 but not in the race
        await hit_lurker.join_race(event_stream)
        await hit_lurker.add_points(event_stream, 14)
        await hit_lurker.leave_race(event_stream)
        await attack_lurker.join_race(event_stream)
        await attack_lurker.add_points(event_stream, 15)

        # we drop a banana at 14, but no one in the race is there
        await event_stream.send(DropBananaEvent(attack_lurker))

        assert hit_lurker.points == 14
        assert len(field._bananas) == 1

    @pytest.mark.asyncio
    async def test_hitting_own_banana_loses_more(self, event_stream: EventStream):
        lg = LurkerGang(event_stream)
        Field(lg, event_stream)
        dumb_lurker = Lurker("dumb", "image_url")
        lg.add(dumb_lurker)

        await dumb_lurker.join_race(event_stream)
        await dumb_lurker.add_points(event_stream, 18)
        await event_stream.send(DropBananaEvent(dumb_lurker))
        await dumb_lurker.add_points(event_stream, -1)

        assert dumb_lurker.points == 15

    @pytest.mark.asyncio
    async def test_bananas_only_work_once(self, event_stream: EventStream):
        lg = LurkerGang(event_stream)
        field = Field(lg, event_stream)
        hit_lurker = Lurker("hit", "hit_image")
        attack_lurker = Lurker("attack", "attack_image")
        lg.add(hit_lurker)
        lg.add(attack_lurker)

        # move our hit lurker to 14 but not in the race
        await hit_lurker.join_race(event_stream)
        await hit_lurker.add_points(event_stream, 14)
        await attack_lurker.join_race(event_stream)
        await attack_lurker.add_points(event_stream, 15)

        await event_stream.send(DropBananaEvent(attack_lurker))
        # move back to 14 where we should stay
        await hit_lurker.add_points(event_stream, 1)

        assert hit_lurker.points == 14
        assert len(field._bananas) == 0

    @pytest.mark.asyncio
    async def test_can_stack_bananas(self, event_stream: EventStream):
        lg = LurkerGang(event_stream)
        field = Field(lg, event_stream)
        hit_lurker = Lurker("hit", "hit_image")
        attack_lurker = Lurker("attack", "attack_image")
        lg.add(hit_lurker)
        lg.add(attack_lurker)

        await attack_lurker.join_race(event_stream)
        await attack_lurker.add_points(event_stream, 15)
        await event_stream.send(DropBananaEvent(attack_lurker))
        await event_stream.send(DropBananaEvent(attack_lurker))

        # try to move to 14, but get hit twice
        await hit_lurker.join_race(event_stream)
        await hit_lurker.add_points(event_stream, 14)
        assert hit_lurker.points == 13
        await hit_lurker.add_points(event_stream, 1)
        assert hit_lurker.points == 13

        assert len(field._bananas) == 0
