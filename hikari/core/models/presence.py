#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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

from hikari.core.models import base
from hikari.core.utils import date_utils, auto_repr, custom_types
from hikari.core.utils import transform


class Status(base.NamedEnum, enum.Enum):
    """
    The status of a member.
    """

    ONLINE = enum.auto()
    IDLE = enum.auto()
    DND = enum.auto()
    OFFLINE = enum.auto()


@dataclasses.dataclass()
class Presence(base.HikariModel):
    """
    The presence of a member. This includes their status and info on what they are doing currently.
    """

    __slots__ = ("activities", "status", "web_status", "desktop_status", "mobile_status")

    #: The activities the member currently is doing.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.core.models.presence.PresenceActivity`
    activities: typing.Sequence[PresenceActivity]

    #: Overall account status.
    #:
    #: :type: :class:`hikari.core.models.presence.Status`
    status: Status

    #: The web client status for the member.
    #:
    #: :type: :class:`hikari.core.models.presence.Status`
    web_status: Status

    #: The desktop client status for the member.
    #:
    #: :type: :class:`hikari.core.models.presence.Status`
    desktop_status: Status

    #: The mobile client status for the member.
    #:
    #: :type: :class:`hikari.core.models.presence.Status`
    mobile_status: Status

    __repr__ = auto_repr.repr_of("status")

    def __init__(self, payload):
        client_status = payload.get("client_status", custom_types.EMPTY_DICT)
        self.activities = [PresenceActivity(a) for a in payload["activities"]]
        self.status = transform.try_cast(payload["status"], Status.from_discord_name, Status.OFFLINE)
        self.web_status = transform.try_cast(client_status.get("web"), Status.from_discord_name, Status.OFFLINE)
        self.desktop_status = transform.try_cast(client_status.get("desktop"), Status.from_discord_name, Status.OFFLINE)
        self.mobile_status = transform.try_cast(client_status.get("mobile"), Status.from_discord_name, Status.OFFLINE)


@dataclasses.dataclass()
class PresenceActivity(base.HikariModel):
    """
    Rich presence-style activity.

    Note:
        This can only be received from the gateway, not sent to it.
    """

    __slots__ = (
        "id",
        "name",
        "type",
        "url",
        "timestamps",
        "application_id",
        "details",
        "state",
        "party",
        "assets",
        "secrets",
        "flags",
    )

    #: The ID of the activity.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike most IDs in this API, this is a :class:`str`, and *NOT* an :class:`int`
    id: str

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

    #: The start and end timestamps for the activity, if applicable, else `None`
    #:
    #: :type: :class:`hikari.core.models.presence.ActivityTimestamps` or `None`
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
    #: :type: :class:`hikari.core.models.presence.ActivityParty` or `None`
    party: typing.Optional[ActivityParty]

    #: Any assets provided with the activity, or `None`
    #:
    #: :type: :class:`hikari.core.models.presence.ActivityAssets` or `None`
    assets: typing.Optional[ActivityAssets]

    #: Any flags on the activity.
    #:
    #: :type: :class:`hikari.core.models.presence.ActivityFlag`
    flags: ActivityFlag

    __repr__ = auto_repr.repr_of("id", "name", "type")

    def __init__(self, payload):
        self.id = payload.get("id")
        self.name = payload.get("name")
        self.type = transform.try_cast(payload.get("type"), ActivityType)
        self.url = payload.get("url")
        self.timestamps = transform.nullable_cast(payload.get("timestamps"), ActivityTimestamps)
        self.application_id = transform.nullable_cast(payload.get("application_id"), int)
        self.details = payload.get("details")
        self.state = payload.get("state")
        self.party = transform.nullable_cast(payload.get("party"), ActivityParty)
        self.assets = transform.nullable_cast(payload.get("assets"), ActivityAssets)
        self.flags = transform.nullable_cast(payload.get("flags"), ActivityFlag) or 0


class ActivityType(enum.IntEnum):
    UNKNOWN = -1
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3


class ActivityFlag(enum.IntFlag):
    INSTANCE = 0x1
    JOIN = 0x2
    SPECTATE = 0x4
    JOIN_REQUEST = 0x8
    SYNC = 0x10
    PLAY = 0x20


@dataclasses.dataclass()
class ActivityParty(base.HikariModel):
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

    def __init__(self, payload):
        self.id = payload.get("id")
        self.current_size = transform.nullable_cast(payload.get("current_size"), int)
        self.max_size = transform.nullable_cast(payload.get("max_size"), int)


@dataclasses.dataclass()
class ActivityAssets(base.HikariModel):
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

    def __init__(self, payload):
        self.large_image = payload.get("large_image")
        self.large_text = payload.get("large_text")
        self.small_image = payload.get("small_image")
        self.small_text = payload.get("small_text")


@dataclasses.dataclass()
class ActivityTimestamps(base.HikariModel):
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

    @property
    def duration(self) -> typing.Optional[datetime.timedelta]:
        """
        Returns:
              a timedelta if both the start and end is specified, else `None`
        """
        return self.end - self.start if self.start is not None and self.end is not None else None

    def __init__(self, payload):
        self.start = transform.nullable_cast(payload.get("start"), date_utils.unix_epoch_to_ts)
        self.end = transform.nullable_cast(payload.get("end"), date_utils.unix_epoch_to_ts)


__all__ = [
    "Status",
    "Presence",
    "PresenceActivity",
    "ActivityType",
    "ActivityFlag",
    "ActivityAssets",
    "ActivityTimestamps",
]
