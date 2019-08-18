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

__all__ = (
    "Status",
    "Presence",
    "ActivityType",
    "ActivityFlag",
    "Activity",
    "ReceivedActivity",
    "ReceivedRichActivity",
    "ActivityAssets",
    "ActivitySecrets",
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

    activities: typing.List[typing.Union[ReceivedActivity, ReceivedRichActivity]]
    #: Overall account status.
    status: Status
    web_status: Status
    desktop_status: Status
    mobile_status: Status

    @property
    def primary_activity(self) -> typing.Optional[typing.Union[ReceivedActivity, ReceivedRichActivity]]:
        """
        The activity that is being displayed on Discord as the user's main activity, or None if there are no activities.
        """
        return self.activities[0] if self.activities else None

    @staticmethod
    def from_dict(payload):

        # We shift the game to the front of the activities list and use that fact to determine which activity is the
        # "active" activity for the user (the one Discord shows on the profile of a user)
        game = payload.get("game")
        activities = payload.get("activities")

        if game is not None and activities:
            # There is no concrete guarantee this is at the front of the list, annoyingly...
            activities.remove(game)
            activities.insert(0, game)

        if activities:
            activities = [transform.try_cast(activity, activity_from_dict, None) for activity in activities]
        else:
            activities = []

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
class Activity:
    """
    Base for any activity.

    This is a type that is able to be sent to the gateway in a presence update, and have subclasses received as
    presence updates.

    Note:
        The :attr:`url` field is only applicable to the :attr:`ActivityType.STREAMING` activity type. For anything
        else, it will be `None`. If the activity type is set to the former, then this URL will be validated and must be
        a Twitch URL for the request to be valid.
    """

    type: Activity
    name: str
    url: typing.Optional[str]

    @staticmethod
    def from_dict(payload):
        ...


@base.dataclass()
class ReceivedActivity(Activity):
    """
    An old-style activity that is not linked to a rich presence.

    Note:
        This can only be received from the gateway, not sent to it.
    """

    __slots__ = ("id", "created_at")

    id: str
    created_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        ...


@base.dataclass()
class ReceivedRichActivity(Activity):
    """
    Rich presence-style activity.

    Note:
        This can only be received from the gateway, not sent to it.
    """

    __slots__ = (
        "sync_id",
        "state",
        "session_id",
        "party",
        "id",
        "flags",
        "details",
        "created_at",
        "assets",
        "secrets",
        "timestamps",
    )

    sync_id: str
    state: str
    session_id: str
    party: ActivityParty
    id: str
    flags: ActivityFlag
    timestamps: ActivityTimestamps

    @staticmethod
    def from_dict(payload):
        ...


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
class ActivitySecrets:
    __slots__ = ("join", "spectate", "match")

    join: typing.Optional[str]
    spectate: typing.Optional[str]
    match: typing.Optional[str]

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
        ...


def activity_from_dict(payload):
    # ¯\_(ツ)_/¯
    if "created_at" in payload:
        return ReceivedActivity.from_dict(payload)

    return ReceivedRichActivity.from_dict(payload)
