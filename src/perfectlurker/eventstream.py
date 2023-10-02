from collections.abc import Callable, Awaitable
import inspect
from typing import List, TypeVar, Tuple
from .events import Event
from logging import Logger

log = Logger("event_stream")
"@private"

_E = TypeVar("_E", bound=Event)
TypedConsumerDelegate = Tuple[_E, Callable[[_E], Awaitable[None]]]
"""
Kinda magic type of storing a list of consumers based on what subclassed event
they are listening for.
"""


class EventStream:
    """
    EventStream allows producers of events to add events, and for consumers of the events
    to read events and handle them.
    Any number of consumers can be added and events will be sent to all of them.
    For producers, anything that should produce events for the game should send an event.
    """

    def __init__(self):
        """
        Create a new event stream that stores our consumers and will route events to them.
        """

        self._consumers: List[TypedConsumerDelegate[Event]] = []

    def add_consumer(self, consumer: Callable[[_E], Awaitable[None]]):
        """
        Register a consumer delegate to listen for events as they come in.
        Consumers must be async handlers.
        You are able to listen for the exact event type by using the type annotation
        for the subclassed event.

        ```python
        def handle_only_join_events(ev: JoinedRaceEvent):
            print(ev.user_name, "joined the race")
        ```
        """

        # Do some fancy work to grab our event type from the callable signature
        # this is probably a little slow but only happens once on startup.
        sig = inspect.signature(consumer)
        param = list(sig.parameters.values())[0]

        log.debug("adding consumer: %s", sig)
        self._consumers.append((param.annotation, consumer))  # type: ignore

    async def send(self, ev: Event):
        """
        Send a new event to all our consumers.
        """
        log.debug("sending event: %s", ev)

        for con in self._consumers:
            if isinstance(ev, con[0]):  # type: ignore
                await con[1](ev)
