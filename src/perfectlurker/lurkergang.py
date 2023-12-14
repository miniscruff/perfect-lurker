from collections.abc import Iterator
from typing import Dict, Optional
from .events import JoinRaceAttemptedEvent, LeaveRaceAttemptedEvent
from .eventstream import EventStream
from .lurker import Lurker
from logging import Logger

log = Logger("lurker_gang")
"@private"


class LurkerGang:
    """
    Track our lurkers in a single collection.

    You can loop over all lurkers using a for loop.
    ```python
    gang = LurkerGang()
    gang.add(Lurker("a", "a profile"))
    for lurker in gang:
        print(lurker.user_name)
    ```

    You can query for a single lurker using the user name.
    ```python
    gang = LurkerGang()
    gang.add(Lurker("a", "a profile"))
    from_gang = gang["a"]
    ```
    """

    def __init__(self, event_stream: EventStream):
        """
        Create a new empy lurker gang.
        We also need to register ourself as a consumer of events.
        """

        self._lurkers: Dict[str, Lurker] = {}
        self._event_stream = event_stream
        event_stream.add_consumer(self._on_join_attempt)
        event_stream.add_consumer(self._on_leave_attempt)

    def __getitem__(self, key: str) -> Optional[Lurker]:
        return self._lurkers.get(key)

    def __iter__(self) -> Iterator[Lurker]:
        return self._lurkers.values().__iter__()

    def add(self, lurker: Lurker):
        """
        Add a lurker to our gang.
        """

        log.debug("adding %s to lurker gang", lurker.user_name)
        self._lurkers[lurker.user_name.lower()] = lurker

    async def _on_join_attempt(self, ev: JoinRaceAttemptedEvent):
        lurk = self[ev.user_name]
        if not lurk:
            return
        await lurk.join_race(self._event_stream)

    async def _on_leave_attempt(self, ev: LeaveRaceAttemptedEvent):
        lurk = self[ev.user_name]
        if not lurk:
            return
        await lurk.leave_race(self._event_stream)
