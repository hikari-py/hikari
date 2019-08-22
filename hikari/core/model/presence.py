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

from hikari.core.utils import dateutils

__all__ = (
    "Status",
    "Presence",
    "UserActivity",
    "ActivityType",
    "ActivityFlag",
    "ActivityAssets",
    "ActivityTimestamps",
)

import datetime
import enum
import typing

from hikari.core.model import base
from hikari.core.utils import transform


class Status(base.NamedEnumMixin, enum.Enum):
    ONLINE = enum.auto()
    IDLE = enum.auto()
    DND = enum.auto()
    OFFLINE = enum.auto()


@base.dataclass()
class Presence:
    """
    The presence of a member.
    """

    __slots__ = ("activities", "status", "web_status", "desktop_status", "mobile_status")

    activities: typing.List[UserActivity]
    #: Overall account status.
    status: Status
    web_status: Status
    desktop_status: Status
    mobile_status: Status

    @staticmethod
    def from_dict(payload):
        activities = transform.get_sequence(payload, "activities", UserActivity.from_dict)
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
class UserActivity:
    """
    Rich presence-style activity.

    Note:
        This can only be received from the gateway, not sent to it.
    """

    __slots__ = (
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
        "instance",
        "flags"
    )

    name: str
    type: str
    url: typing.Optional[str]
    timestamps: typing.Optional[ActivityTimestamps]
    application_id: typing.Optional[int]
    details: typing.Optional[str]
    state: typing.Optional[str]
    party: typing.Optional[ActivityParty]
    assets: typing.Optional[ActivityAssets]
    instance: bool
    flags: ActivityFlag

    @staticmethod
    def from_dict(payload):
        return UserActivity(
            name=transform.get_cast(payload, "name", str),
            type=transform.get_cast_or_raw(payload, "type", ActivityType),
            url=transform.get_cast(payload, "url", str),
            timestamps=transform.get_cast(payload, "timestamps", ActivityTimestamps.from_dict),
            application_id=transform.get_cast(payload, "application_id", int),
            details=transform.get_cast(payload, "details", str),
            state=transform.get_cast(payload, "state", str),
            party=transform.get_cast(payload, "party", ActivityParty.from_dict),
            assets=transform.get_cast(payload, "assets", ActivityAssets.from_dict),
            instance=transform.get_cast(payload, "instance", bool, default=False),
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

    id: typing.Optional[str]
    current_size: typing.Optional[int]
    max_size: typing.Optional[int]

    @staticmethod
    def from_dict(payload):
        ...


@base.dataclass()
class ActivityAssets:
    __slots__ = ("large_image", "large_text", "small_image", "small_text")

    large_image: typing.Optional[str]
    large_text: typing.Optional[str]
    small_image: typing.Optional[str]
    small_text: typing.Optional[str]

    @staticmethod
    def from_dict(payload):
        ...


@base.dataclass()
class ActivityTimestamps:
    __slots__ = ("start", "end")

    start: typing.Optional[datetime.datetime]
    end: typing.Optional[datetime.datetime]

    @property
    def duration(self) -> typing.Optional[datetime.timedelta]:
        return self.end - self.start if self.start is not None and self.end is not None else None

    @staticmethod
    def from_dict(payload):
        return ActivityTimestamps(
            start=transform.get_cast(payload, "start", dateutils.unix_epoch_to_datetime),
            end=transform.get_cast(payload, "end", dateutils.unix_epoch_to_datetime)
        )
