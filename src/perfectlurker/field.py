from typing import Dict, List
from .events import (
    ChatMessageEvent,
    DropBananaEvent,
    HitBananaEvent,
    SetPointsEvent,
)
from .eventstream import EventStream
from .lurker import Lurker
from .lurkergang import LurkerGang
from logging import Logger

log = Logger("field")
"@private"


class Field:
    """
    Field manages any race wide events such as items dropped.
    """

    def __init__(self, lurker_gang: LurkerGang, event_stream: EventStream):
        """
        Create a new field.
        """

        self._lurker_gang = lurker_gang
        event_stream.add_consumer(self._on_set_points)
        event_stream.add_consumer(self._on_drop_banana)
        self._event_stream = event_stream

        # we may want to create a base Item class, but for now just bananas is fine.
        self._bananas: Dict[int, List[Lurker]] = {}

    async def _on_set_points(self, ev: SetPointsEvent):
        """
        When a lurker has there points updated, they may have hit a banana
        Events Emitted:
        1. `.events.SetPointsEvent` when a banana is hit and a lurker loses points
        1. `.events.ChatMessageEvent` when a banana is hit
        1. `.events.HitBananaEvent` for who hit the banana
        """

        if ev.lurker.position in self._bananas:
            attacking_lurker = self._bananas[ev.lurker.position].pop(0)
            # if we have no more bananas here then we can delete it
            if not self._bananas[ev.lurker.position]:
                del self._bananas[ev.lurker.position]

            if ev.lurker == attacking_lurker:
                log.debug("lurker %s hit there own banana", ev.lurker.user_name)
                await ev.lurker.add_points(self._event_stream, -2)
                await self._event_stream.send(
                    HitBananaEvent(ev.lurker.position, ev.lurker, ev.lurker)
                )
                await self._event_stream.send(
                    ChatMessageEvent(
                        f"@{ev.lurker.user_name} hit there own banana, oof"
                    )
                )
            else:
                log.debug(
                    "lurker %s hit %s's banana",
                    ev.lurker.user_name,
                    attacking_lurker.user_name,
                )
                await ev.lurker.add_points(self._event_stream, -1)
                await self._event_stream.send(
                    HitBananaEvent(ev.lurker.position, ev.lurker, attacking_lurker)
                )
                await self._event_stream.send(
                    ChatMessageEvent(
                        f"@{ev.lurker.user_name} hit the banana set by @{attacking_lurker.user_name}"
                    )
                )

    async def _on_drop_banana(self, ev: DropBananaEvent):
        """
        When a banana is dropped, check to see if any lurker is immediately hit by it
        and if not, save it for later.
        Bananas can stack on at the same position of two lurkers drop them from the same point.

        Events Emitted:
        1. `.events.SetPointsEvent` when a banana is hit immediately and a lurker loses points
        1. `.events.ChatMessageEvent` when a banana is hit immediately
        1. `.events.HitBananaEvent` for who hit the banana
        """
        for lurker in self._lurker_gang:
            if not lurker.in_race:
                continue

            if lurker.position == ev.position:
                log.debug(
                    "lurker %s hit %s's banana that was just dropped",
                    lurker.user_name,
                    ev.lurker.user_name,
                )
                await lurker.add_points(self._event_stream, -1)
                await self._event_stream.send(
                    HitBananaEvent(ev.lurker.position, lurker, ev.lurker)
                )
                await self._event_stream.send(
                    ChatMessageEvent(
                        f"@{lurker.user_name} hit the banana just set by @{ev.lurker.user_name}"
                    )
                )
                return

        log.debug("banana dropped at %d by %s", ev.position, ev.lurker.user_name)

        if ev.position not in self._bananas:
            self._bananas[ev.position] = []
        self._bananas[ev.position].append(ev.lurker)
