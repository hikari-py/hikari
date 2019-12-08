#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
Presences for members.
"""

from __future__ import annotations

import datetime
import enum
import typing

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import transformations
from hikari.orm.models import interfaces


class Status(interfaces.INamedEnum, enum.Enum):
    """
    The status of a member.
    """

    #: Online/green.
    ONLINE = enum.auto()
    #: Idle/yellow.
    IDLE = enum.auto()
    #: Do not disturb/red.
    DND = enum.auto()
    #: Offline/grey.
    OFFLINE = enum.auto()


class Presence(interfaces.IModel):
    """
    The presence of a member. This includes their status and info on what they are doing currently.
    """

    __slots__ = ("activities", "status", "web_status", "desktop_status", "mobile_status")

    #: The activities the member currently is doing.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.orm.models.presences.PresenceActivity`
    activities: typing.Sequence[PresenceActivity]

    #: Overall account status.
    #:
    #: :type: :class:`hikari.orm.models.presences.Status`
    status: Status

    #: The web client status for the member.
    #:
    #: :type: :class:`hikari.orm.models.presences.Status`
    web_status: Status

    #: The desktop client status for the member.
    #:
    #: :type: :class:`hikari.orm.models.presences.Status`
    desktop_status: Status

    #: The mobile client status for the member.
    #:
    #: :type: :class:`hikari.orm.models.presences.Status`
    mobile_status: Status

    __repr__ = auto_repr.repr_of("status")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.activities = data_structures.EMPTY_SEQUENCE
        self.status = Status.OFFLINE
        self.web_status = Status.OFFLINE
        self.desktop_status = Status.OFFLINE
        self.mobile_status = Status.OFFLINE
        self.update_state(payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        client_status = payload.get("client_status", data_structures.EMPTY_DICT)

        if "activities" in payload:
            self.activities = [parse_presence_activity(a) for a in payload["activities"]]

        if "status" in payload:
            self.status = transformations.try_cast(payload["status"], Status.from_discord_name, Status.OFFLINE)

        if "web" in client_status:
            self.web_status = transformations.try_cast(
                client_status.get("web"), Status.from_discord_name, Status.OFFLINE
            )

        if "desktop" in client_status:
            self.desktop_status = transformations.try_cast(
                client_status.get("desktop"), Status.from_discord_name, Status.OFFLINE
            )

        if "mobile" in client_status:
            self.mobile_status = transformations.try_cast(
                client_status.get("mobile"), Status.from_discord_name, Status.OFFLINE
            )


class PresenceActivity(interfaces.IModel):
    """
    A non-rich presence-style activity.

    Note:
        This can only be received from the gateway, not sent to it.
    """

    __slots__ = ("name", "type", "url")

    #: The name of the activity.
    #:
    #: :type: :class:`str`
    name: str

    #: The type of the activity.
    #:
    #: :type: :class:`str`
    type: str

    #: The URL of the activity, if applicable
    #:
    #: :type: :class:`str` or `None`
    url: typing.Optional[str]

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.name = payload.get("name")
        self.type = transformations.try_cast(payload.get("type"), ActivityType)
        self.url = payload.get("url")

    update_state = NotImplemented


class RichPresenceActivity(PresenceActivity):
    """
    Rich presence-style activity.

    Note:
        This can only be received from the gateway, not sent to it.
    """

    __slots__ = ("id", "timestamps", "application_id", "details", "state", "party", "assets", "secrets", "flags")

    #: The ID of the activity.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike most IDs in this API, this is a :class:`str`, and *NOT* an :class:`int`
    id: str

    #: The start and end timestamps for the activity, if applicable, else `None`
    #:
    #: :type: :class:`hikari.orm.models.presences.ActivityTimestamps` or `None`
    timestamps: typing.Optional[ActivityTimestamps]

    #: The ID of the application, or `None`
    #:
    #: :type: :class:`int` or `None`
    application_id: typing.Optional[int]

    #: Details of the activity, or `None`
    #:
    #: :type: :class:`str` or `None`
    details: typing.Optional[str]

    #: The state of the activity, or `None`
    #:
    #: :type: :class:`str` or `None`
    state: typing.Optional[str]

    #: The party in the activity, or `None`
    #:
    #: :type: :class:`hikari.orm.models.presences.ActivityParty` or `None`
    party: typing.Optional[ActivityParty]

    #: Any assets provided with the activity, or `None`
    #:
    #: :type: :class:`hikari.orm.models.presences.ActivityAssets` or `None`
    assets: typing.Optional[ActivityAssets]

    #: Any flags on the activity.
    #:
    #: :type: :class:`hikari.orm.models.presences.ActivityFlag`
    flags: ActivityFlag

    __repr__ = auto_repr.repr_of("id", "name", "type")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(payload)
        self.id = payload.get("id")
        self.timestamps = transformations.nullable_cast(payload.get("timestamps"), ActivityTimestamps)
        self.application_id = transformations.nullable_cast(payload.get("application_id"), int)
        self.details = payload.get("details")
        self.state = payload.get("state")
        self.party = transformations.nullable_cast(payload.get("party"), ActivityParty)
        self.assets = transformations.nullable_cast(payload.get("assets"), ActivityAssets)
        self.flags = transformations.nullable_cast(payload.get("flags"), ActivityFlag) or 0


def parse_presence_activity(
    payload: data_structures.DiscordObjectT,
) -> typing.Union[PresenceActivity, RichPresenceActivity]:
    """
    Consumes a payload and decides the type of activity it represents. A corresponding object is then
    constructed and returned as appropriate.

    Returns:
        either a :class:`PresenceActivity` or a :class:`RichPresenceActivity` depending on the
        implementation details provided.
    """
    impl = RichPresenceActivity if any(slot in payload for slot in RichPresenceActivity.__slots__) else PresenceActivity
    return impl(payload)


class ActivityType(enum.IntEnum):
    """
    The activity state. Can be more than one using bitwise-combinations.
    """

    #: Shows up as `Playing <name>`
    PLAYING = 0
    #: Shows up as `Streaming <name>`.
    #:
    #: Warning:
    #:     Corresponding presences must be associated with VALID Twitch or YouTube stream URLS!
    STREAMING = 1
    #: Shows up as `Listening to <name>`.
    LISTENING = 2
    #: Shows up as `Watching <name>`. Note that this is not officially documented, so will be likely removed
    #: in the near future.
    WATCHING = 3
    #: A custom status. 
    #: 
    #: To set an emoji with the status, place a unicode emoji or Discord emoji (`:smiley:`) as the first
    #: part of the status activity name.
    CUSTOM = 4


class ActivityFlag(enum.IntFlag):
    """
    The activity state. Can be more than one using bitwise-combinations.
    """

    INSTANCE = 0x1
    JOIN = 0x2
    SPECTATE = 0x4
    JOIN_REQUEST = 0x8
    SYNC = 0x10
    PLAY = 0x20


class ActivityParty(interfaces.IModel):
    """
    A description of a party of players in the same rich-presence activity. This
    is used to describe multiplayer sessions, and the likes.
    """

    __slots__ = ("id", "current_size", "max_size")

    #: The ID of the party, if applicable, else `None`
    #:
    #: :type: :class:`str` or `None`
    #:
    #: Warning:
    #:     Unlike most IDs in this API, this is a :class:`str`, and *NOT* an :class:`int`, also unlike other IDs, this
    #:     may or may not be specified at all.
    id: typing.Optional[str]

    #: The size of the party, if applicable, else `None`.
    #:
    #: :type: :class:`int` or `None`
    current_size: typing.Optional[int]

    #: The maximum size of the party, if applicable, else `None`.
    #:
    #: :type: :class:`int` or `None`
    max_size: typing.Optional[int]

    __repr__ = auto_repr.repr_of("id", "current_size", "max_size")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.id = payload.get("id")
        self.current_size = transformations.nullable_cast(payload.get("current_size"), int)
        self.max_size = transformations.nullable_cast(payload.get("max_size"), int)


class ActivityAssets(interfaces.IModel):
    """
    Any rich assets such as tooltip data and image/icon data for a rich presence activity.
    """

    __slots__ = ("large_image", "large_text", "small_image", "small_text")

    #: Large image asset, or `None`.
    #:
    #: :type: :class:`str` or `None`
    large_image: typing.Optional[str]

    #: Large image text, or `None`.
    #:
    #: :type: :class:`str` or `None`
    large_text: typing.Optional[str]

    #: Small image asset, or `None`.
    #:
    #: :type: :class:`str` or `None`
    small_image: typing.Optional[str]

    #: Small image text, or `None`.
    #:
    #: :type: :class:`str` or `None`
    small_text: typing.Optional[str]

    __repr__ = auto_repr.repr_of()

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.large_image = payload.get("large_image")
        self.large_text = payload.get("large_text")
        self.small_image = payload.get("small_image")
        self.small_text = payload.get("small_text")


class ActivityTimestamps(interfaces.IModel):
    """
    Timestamps for a rich presence activity object that define when and for how long the
    user has been undergoing an activity.
    """

    __slots__ = ("start", "end")

    #: The start timestamp, or `None` if not specified.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    start: typing.Optional[datetime.datetime]

    #: The end timestamp, or `None` if not specified.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    end: typing.Optional[datetime.datetime]

    __repr__ = auto_repr.repr_of("start", "end", "duration")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.start = transformations.nullable_cast(payload.get("start"), date_helpers.unix_epoch_to_ts)
        self.end = transformations.nullable_cast(payload.get("end"), date_helpers.unix_epoch_to_ts)

    @property
    def duration(self) -> typing.Optional[datetime.timedelta]:
        """
        Returns:
              a timedelta if both the start and end is specified, else `None`
        """
        return self.end - self.start if self.start is not None and self.end is not None else None


__all__ = [
    "Status",
    "Presence",
    "PresenceActivity",
    "RichPresenceActivity",
    "parse_presence_activity",
    "ActivityType",
    "ActivityFlag",
    "ActivityAssets",
    "ActivityTimestamps",
]
