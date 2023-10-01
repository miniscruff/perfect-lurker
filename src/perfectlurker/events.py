from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .lurker import Lurker

event_separator = ","
"how our event code and values are separated in our websocket packets"


class Event:
    """
    Base class of any event, completely empty.
    """

    def __repr__(self) -> str:
        return str(self.__dict__)


class LurkerEvent(Event):
    """
    Base class of any event that simply indicates the lurker did, or attempted to do something.
    We source the event by the lurkers name as it may or may not be a valid lurker yet.
    """

    def __init__(self, user_name: str):
        self.user_name = user_name
        """ Username of the lurker who caused the event """

    def __eq__(self, other: object):
        return (
            self.__class__.__name__ != other.__class__.__name__
            and isinstance(other, LurkerEvent)
            and self.user_name == other.user_name
        )


class SocketEvent(Event):
    """
    Base class of any socket event that occurs in our system.
    Socket events are ones where we expect to send this value over a websocket
    to any downstream listener.
    """

    def __init__(self, code: int, values: List[str]):
        """
        Create a new event with a code and some values.
        In most cases you would likely be creating an event using an inherited class.
        """

        self.code = code
        "A unique numbered code for each event for indexing."
        self.values = values
        "Any extra values for each event such as lurker name, unique per event."

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SocketEvent) and self.packet() == other.packet()

    def packet(self) -> str:
        """
        Stringified representation of our event data that will be sent as a web socket packet.
        """
        return event_separator.join([str(self.code), *self.values])


class ChatMessageEvent(Event):
    """
    Event used to send a message to twitch chat.
    """

    def __init__(self, message: str):
        self.message = message
        "Message we want to send to our chat."

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ChatMessageEvent) and self.message == other.message


class JoinRaceAttemptedEvent(LurkerEvent):
    """
    Event used when a chatter attempts to join the race
    """


class LeaveRaceAttemptedEvent(LurkerEvent):
    """
    Event used when a chatter attempts to leave the race
    """


class JoinedRaceEvent(SocketEvent):
    """
    Event for when a lurker joins the race.
    """

    def __init__(self, lurker: "Lurker"):
        super().__init__(1, [lurker.user_name])
        self.lurker = lurker
        "Lurker who joined the race"


class LeftRaceEvent(SocketEvent):
    """
    Event for when a lurker leaves the race.
    """

    def __init__(self, lurker: "Lurker"):
        super().__init__(2, [lurker.user_name])
        self.lurker = lurker
        "Lurker who joined the race"


class SetPointsEvent(SocketEvent):
    """
    Event used to update the points of a lurker.
    """

    def __init__(self, lurker: "Lurker", points: int):
        super().__init__(3, [lurker.user_name, str(points)])
        self.lurker = lurker
        "Lurker who joined the race"
        self.points = points
        "Current points of our lurker"


class DropBananaEvent(SocketEvent):
    def __init__(self, lurker: "Lurker"):
        one_position_back = (lurker.position + 59) % 60
        super().__init__(4, [lurker.user_name, str(one_position_back)])
        self.lurker = lurker
        "Lurker who joined the race"
        self.position = one_position_back
        "Where the banana was dropped on the field"


class HitBananaEvent(SocketEvent):
    def __init__(self, position: int, hit_lurker: "Lurker", attack_lurker: "Lurker"):
        super().__init__(
            5, [str(position), hit_lurker.user_name, attack_lurker.user_name]
        )
        self.hit_lurker = hit_lurker
        "Lurker who got hit by the banana"
        self.attack_lurker = attack_lurker
        "Lurker who dropped the banana, may by the same as hit_lurker"
        self.position = position
        "Where the banana was dropped on the field"
