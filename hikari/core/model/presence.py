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

import datetime
import enum

import typing

from hikari.core.model import base
from hikari.core.utils import dateutils
from hikari.core.utils import transform


class Status(base.NamedEnum, enum.Enum):
    """
    The status of a member.
    """

    ONLINE = enum.auto()
    IDLE = enum.auto()
    DND = enum.auto()
    OFFLINE = enum.auto()


@base.dataclass()
class Presence:
    """
    The presence of a member. This includes their status and info on what they are doing currently.
    """

    __slots__ = ("activities", "status", "web_status", "desktop_status", "mobile_status")

    #: The activities the member currently is doing.
    #:
    #: :type: :class:`list` of :class:`hikari.core.model.presence.PresenceActivity`
    activities: typing.List[PresenceActivity]

    #: Overall account status.
    #:
    #: :type: :class:`hikari.core.model.presence.Status`
    status: Status

    #: The web client status for the member.
    #:
    #: :type: :class:`hikari.core.model.presence.Status`
    web_status: Status

    #: The desktop client status for the member.
    #:
    #: :type: :class:`hikari.core.model.presence.Status`
    desktop_status: Status

    #: The mobile client status for the member.
    #:
    #: :type: :class:`hikari.core.model.presence.Status`
    mobile_status: Status

    @staticmethod
    def from_dict(payload):
        activities = transform.get_sequence(payload, "activities", PresenceActivity.from_dict)
        status = transform.get_cast(payload, "status", Status.from_discord_name, Status.OFFLINE)
        client_status = payload.get("client_status", {})
        web_status = transform.get_cast(client_status, "web", Status.from_discord_name, Status.OFFLINE)
        desktop_status = transform.get_cast(client_status, "desktop", Status.from_discord_name, Status.OFFLINE)
        mobile_status = transform.get_cast(client_status, "mobile", Status.from_discord_name, Status.OFFLINE)

        return Presence(
            activities=activities,
            status=status,
            web_status=web_status,
            desktop_status=desktop_status,
            mobile_status=mobile_status,
        )


@base.dataclass()
class PresenceActivity:
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
    #: :type: :class:`hikari.core.model.presence.ActivityTimestamps` or `None`
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
    #: :type: :class:`hikari.core.model.presence.ActivityParty` or `None`
    party: typing.Optional[ActivityParty]

    #: Any assets provided with the activity, or `None`
    #:
    #: :type: :class:`hikari.core.model.presence.ActivityAssets` or `None`
    assets: typing.Optional[ActivityAssets]

    #: Any flags on the activity.
    #:
    #: :type: :class:`hikari.core.model.presence.ActivityFlag`
    flags: ActivityFlag

    @staticmethod
    def from_dict(payload):
        return PresenceActivity(
            id=transform.get_cast(payload, "id", str),
            name=transform.get_cast(payload, "name", str),
            type=transform.get_cast_or_raw(payload, "type", ActivityType),
            url=transform.get_cast(payload, "url", str),
            timestamps=transform.get_cast(payload, "timestamps", ActivityTimestamps.from_dict),
            application_id=transform.get_cast(payload, "application_id", int),
            details=transform.get_cast(payload, "details", str),
            state=transform.get_cast(payload, "state", str),
            party=transform.get_cast(payload, "party", ActivityParty.from_dict),
            assets=transform.get_cast(payload, "assets", ActivityAssets.from_dict),
            flags=transform.get_cast(payload, "flags", ActivityFlag, default=0),
        )


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


@base.dataclass()
class ActivityParty:
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

    @staticmethod
    def from_dict(payload):
        return ActivityParty(
            id=transform.get_cast(payload, "id", str),
            current_size=transform.get_cast(payload, "current_size", int),
            max_size=transform.get_cast(payload, "max_size", int),
        )


@base.dataclass()
class ActivityAssets:
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

    @staticmethod
    def from_dict(payload):
        return ActivityAssets(
            large_image=transform.get_cast(payload, "large_image", str),
            large_text=transform.get_cast(payload, "large_text", str),
            small_image=transform.get_cast(payload, "small_image", str),
            small_text=transform.get_cast(payload, "small_text", str),
        )


@base.dataclass()
class ActivityTimestamps:
    __slots__ = ("start", "end")

    #: The start timestamp, or `None` if not specified.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    start: typing.Optional[datetime.datetime]

    #: The end timestamp, or `None` if not specified.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    end: typing.Optional[datetime.datetime]

    @property
    def duration(self) -> typing.Optional[datetime.timedelta]:
        """
        Returns:
              a timedelta if both the start and end is specified, else `None`
        """
        return self.end - self.start if self.start is not None and self.end is not None else None

    @staticmethod
    def from_dict(payload):
        return ActivityTimestamps(
            start=transform.get_cast(payload, "start", dateutils.unix_epoch_to_datetime),
            end=transform.get_cast(payload, "end", dateutils.unix_epoch_to_datetime),
        )


__all__ = [
    "Status",
    "Presence",
    "PresenceActivity",
    "ActivityType",
    "ActivityFlag",
    "ActivityAssets",
    "ActivityTimestamps",
]
