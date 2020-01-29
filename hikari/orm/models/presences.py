#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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

import dataclasses
import datetime
import enum
import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import dates
from hikari.internal_utilities import reprs
from hikari.internal_utilities import transformations
from hikari.orm.models import bases

if typing.TYPE_CHECKING:
    from hikari.internal_utilities import type_hints


class Status(bases.NamedEnumMixin, enum.Enum):
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


@dataclasses.dataclass()
class Presence:
    since: type_hints.Nullable[typing.Union[float, datetime.datetime]] = None
    is_afk: bool = False
    status: Status = Status.ONLINE
    activity: type_hints.Nullable[Activity] = None

    __repr__ = reprs.repr_of("since", "is_afk", "status", "activity")

    def to_dict(self):
        return {
            "since": int(1_000 * self.since.timestamp()) if isinstance(self.since, datetime.datetime) else self.since,
            "afk": self.is_afk,
            "status": self.status.name.lower(),
            "activity": self.activity.to_dict() if self.activity is not None else None,
        }


class MemberPresence(bases.BaseModel):
    """
    The presence of a member. This includes their status and info on what they are doing currently.
    """

    __slots__ = ("activities", "status", "web_status", "desktop_status", "mobile_status")

    #: The activities the member currently is doing.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.orm.models.presences.PresenceActivity`
    activities: typing.Sequence[Activity]

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

    __repr__ = reprs.repr_of("status")

    def __init__(self, payload: containers.JSONObject) -> None:
        self.activities = containers.EMPTY_SEQUENCE
        self.status = Status.OFFLINE
        self.web_status = Status.OFFLINE
        self.desktop_status = Status.OFFLINE
        self.mobile_status = Status.OFFLINE
        self.update_state(payload)

    def update_state(self, payload: containers.JSONObject) -> None:
        client_status = payload.get("client_status", containers.EMPTY_DICT)

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


class ActivityType(bases.BestEffortEnumMixin, enum.IntEnum):
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


@dataclasses.dataclass()
class Activity(bases.BaseModel, bases.MarshalMixin):
    """
    A non-rich presence-style activity.
    """

    __slots__ = ("name", "type", "url")

    #: The name of the activity.
    #:
    #: :type: :class:`str`
    name: str

    #: The type of the activity.
    #:
    #: :type: :class:`str`
    type: ActivityType

    #: The URL of the activity, if applicable
    #:
    #: :type: :class:`str` or `None`
    url: type_hints.Nullable[str]

    def __init__(
        self, *, name: str, type: ActivityType = ActivityType.CUSTOM, url: type_hints.Nullable[str] = None
    ) -> None:
        self.name = name
        self.type = ActivityType.get_best_effort_from_value(type)
        self.url = url

    update_state = NotImplemented


class RichActivity(Activity):
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
    timestamps: type_hints.Nullable[ActivityTimestamps]

    #: The ID of the application, or `None`
    #:
    #: :type: :class:`int` or `None`
    application_id: type_hints.Nullable[int]

    #: Details of the activity, or `None`
    #:
    #: :type: :class:`str` or `None`
    details: type_hints.Nullable[str]

    #: The state of the activity, or `None`
    #:
    #: :type: :class:`str` or `None`
    state: type_hints.Nullable[str]

    #: The party in the activity, or `None`
    #:
    #: :type: :class:`hikari.orm.models.presences.ActivityParty` or `None`
    party: type_hints.Nullable[ActivityParty]

    #: Any assets provided with the activity, or `None`
    #:
    #: :type: :class:`hikari.orm.models.presences.ActivityAssets` or `None`
    assets: type_hints.Nullable[ActivityAssets]

    #: Any flags on the activity.
    #:
    #: :type: :class:`hikari.orm.models.presences.ActivityFlag`
    flags: typing.Union[ActivityFlag, int]

    __repr__ = reprs.repr_of("id", "name", "type")

    def __init__(self, payload: containers.JSONObject) -> None:
        super().__init__(
            name=payload.get("name"),
            type=ActivityType.get_best_effort_from_value(payload.get("type", 0)),
            url=payload.get("url"),
        )
        self.id = payload.get("id")
        self.timestamps = transformations.nullable_cast(payload.get("timestamps"), ActivityTimestamps)
        self.application_id = transformations.nullable_cast(payload.get("application_id"), int)
        self.details = payload.get("details")
        self.state = payload.get("state")
        self.party = transformations.nullable_cast(payload.get("party"), ActivityParty)
        self.assets = transformations.nullable_cast(payload.get("assets"), ActivityAssets)
        self.flags = transformations.nullable_cast(payload.get("flags"), ActivityFlag) or 0


def parse_presence_activity(payload: containers.JSONObject,) -> typing.Union[Activity, RichActivity]:
    """
    Consumes a payload and decides the type of activity it represents. A corresponding object is then
    constructed and returned as appropriate.

    Returns:
        Returns a :class:`RichActivity`
    """
    return RichActivity(payload)


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


class ActivityParty(bases.BaseModel):
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
    id: type_hints.Nullable[str]

    #: The size of the party, if applicable, else `None`.
    #:
    #: :type: :class:`int` or `None`
    current_size: type_hints.Nullable[int]

    #: The maximum size of the party, if applicable, else `None`.
    #:
    #: :type: :class:`int` or `None`
    max_size: type_hints.Nullable[int]

    __repr__ = reprs.repr_of("id", "current_size", "max_size")

    def __init__(self, payload: containers.JSONObject) -> None:
        self.id = payload.get("id")
        self.current_size = transformations.nullable_cast(payload.get("current_size"), int)
        self.max_size = transformations.nullable_cast(payload.get("max_size"), int)


class ActivityAssets(bases.BaseModel):
    """
    Any rich assets such as tooltip data and image/icon data for a rich presence activity.
    """

    __slots__ = ("large_image", "large_text", "small_image", "small_text")

    #: Large image asset, or `None`.
    #:
    #: :type: :class:`str` or `None`
    large_image: type_hints.Nullable[str]

    #: Large image text, or `None`.
    #:
    #: :type: :class:`str` or `None`
    large_text: type_hints.Nullable[str]

    #: Small image asset, or `None`.
    #:
    #: :type: :class:`str` or `None`
    small_image: type_hints.Nullable[str]

    #: Small image text, or `None`.
    #:
    #: :type: :class:`str` or `None`
    small_text: type_hints.Nullable[str]

    __repr__ = reprs.repr_of()

    def __init__(self, payload: containers.JSONObject) -> None:
        self.large_image = payload.get("large_image")
        self.large_text = payload.get("large_text")
        self.small_image = payload.get("small_image")
        self.small_text = payload.get("small_text")


class ActivityTimestamps(bases.BaseModel):
    """
    Timestamps for a rich presence activity object that define when and for how long the
    user has been undergoing an activity.
    """

    __slots__ = ("start", "end")

    #: The start timestamp, or `None` if not specified.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    start: type_hints.Nullable[datetime.datetime]

    #: The end timestamp, or `None` if not specified.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    end: type_hints.Nullable[datetime.datetime]

    __repr__ = reprs.repr_of("start", "end", "duration")

    def __init__(self, payload: containers.JSONObject) -> None:
        self.start = transformations.nullable_cast(payload.get("start"), dates.unix_epoch_to_ts)
        self.end = transformations.nullable_cast(payload.get("end"), dates.unix_epoch_to_ts)

    @property
    def duration(self) -> type_hints.Nullable[datetime.timedelta]:
        """
        Returns:
              a timedelta if both the start and end is specified, else `None`
        """
        return self.end - self.start if self.start is not None and self.end is not None else None


__all__ = [
    "Status",
    "Presence",
    "MemberPresence",
    "Activity",
    "RichActivity",
    "parse_presence_activity",
    "ActivityType",
    "ActivityFlag",
    "ActivityAssets",
    "ActivityTimestamps",
]
