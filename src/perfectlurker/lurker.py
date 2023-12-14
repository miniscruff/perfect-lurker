from .eventstream import EventStream
from .events import (
    ChatMessageEvent,
    JoinedRaceEvent,
    LeftRaceEvent,
    SetPointsEvent,
)
from logging import Logger

log = Logger("lurker")
"@private"

status_in_race = "in_race"
"Lurker state indicating we are actively in the race"
status_out_race = "out_race"
"Lurker state indicating we are not yet in the race"
status_removed_race = "left_race"
"Lurker state indicating we have left the race, and can not re-enter"


class Lurker:
    """
    Lurker manages all the data and state for our lurkers in the race.
    It changes when our lurker functionality is expanded.
    """

    def __init__(self, user_name: str, image_url: str):
        """
        Create a new lurker with a name and profile image.
        """

        self.image_url = image_url
        "URL of our lurkers profile image that we use on our field"

        self.user_name = user_name
        "Twitch user name of our lurker"

        self.race_status = status_out_race
        "Current race status of our lurker"

        self.points = 0
        "How many points we have"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Lurker):
            return False
        return self.user_name == other.user_name

    def __repr__(self):
        return f"name:{self.user_name} race:{self.race_status} points:{self.points}"

    async def join_race(self, event_stream: EventStream):
        """
        Adds our lurker to the race.
        Lurkers must not already be in the race, and must not have left the race before.

        Events Emitted:
        1. `.events.ChatMessageEvent` when lurker already in the race
        1. `.events.ChatMessageEvent` when lurker already left the race
        1. `.events.JoinedRaceEvent` if we successfully joined
        1. `.events.ChatMessageEvent` when lurker joined
        """

        if self.race_status == status_in_race:
            log.debug(
                "lurker %s tried to join the race but is already in it", self.user_name
            )
            await event_stream.send(
                ChatMessageEvent(f"@{self.user_name} you are already in the race")
            )
            return

        if self.race_status == status_removed_race:
            log.debug(
                "lurker %s tried to join the race but already left", self.user_name
            )
            await event_stream.send(
                ChatMessageEvent(f"@{self.user_name} you already left the race")
            )
            return

        log.debug("lurker %s joined the race", self.user_name)
        self.race_status = status_in_race
        await event_stream.send(JoinedRaceEvent(self))
        await event_stream.send(
            ChatMessageEvent(f"LET'S GO! @{self.user_name} IS IN THIS")
        )

    async def leave_race(self, event_stream: EventStream):
        """
        Moves our lurker out of the race.
        Lurker must be in the race in order to leave.

        Events Emitted:
        1. `.events.ChatMessageEvent` when lurker is not in race
        1. `.events.LeftRaceEvent` if we successfully left
        1. `.events.ChatMessageEvent` when lurker is removed
        """

        if self.race_status != status_in_race:
            log.debug("lurker %s tried to leave the race", self.user_name)
            await event_stream.send(
                ChatMessageEvent(f"@{self.user_name} you aint even in the race")
            )
            return

        log.debug("lurker %s left the race", self.user_name)
        self.race_status = status_removed_race
        await event_stream.send(LeftRaceEvent(self))
        await event_stream.send(
            ChatMessageEvent(f"Ok then, @{self.user_name} ditched us")
        )

    async def add_points(self, event_stream: EventStream, delta: int):
        """
        Add or remove points from our lurker.
        To remove points pass a negative value for delta.

        Events Emitted:
        1. `.events.SetPointsEvent` with our updated points value
        """

        if self.race_status != status_in_race:
            log.debug(
                "%s tried to get %d points without being in the race",
                self.user_name,
                delta,
            )
            return

        new_points = max(self.points + delta, 0)
        if new_points == self.points:
            log.debug(
                "%s tried to get %d points but there was no change",
                self.user_name,
                delta,
            )
            return

        self.points = new_points
        await event_stream.send(SetPointsEvent(self, new_points))

    @property
    def position(self) -> int:
        """
        What position we are on in the minimap accounting for laps around.
        """

        return self.points % 60

    @property
    def in_race(self) -> bool:
        """
        Whether or not our lurker is currently in the race.
        """

        return self.race_status == status_in_race

    # def set_shield(self, value: int):
    # self.shield_points = value

    # Take some damage, if we have a shield, that will be used first.
    # Returns whether or not we took any damage.
    # def take_damage(self, value: int) -> bool:
    # if self.shield_points >= value:
    # self.shield_points -= value
    # return False
    # self.shield_points = 0
    # return True
