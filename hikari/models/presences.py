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
"""Application and entities that are used to describe guilds on Discord."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "Activity",
    "ActivityAssets",
    "ActivityFlag",
    "ActivitySecret",
    "ActivityTimestamps",
    "ActivityType",
    "ActivityParty",
    "ClientStatus",
    "MemberPresence",
    "RichActivity",
    "Status",
]

import enum
import typing

import attr

from hikari.models import users
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import rest
    from hikari.models import emojis as emojis_


@enum.unique
@typing.final
class ActivityType(int, enum.Enum):
    """The activity type."""

    PLAYING = 0
    """Shows up as `Playing <name>`"""

    STREAMING = 1

    LISTENING = 2
    """Shows up as `Listening to <name>`."""

    WATCHING = 3
    """Shows up as `Watching <name>`.

    !!! note
        this is not officially documented, so will be likely removed in the near
        future.
    """

    CUSTOM = 4
    """A custom status.

    To set an emoji with the status, place a unicode emoji or Discord emoji
    (`:smiley:`) as the first part of the status activity name.
    """

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class ActivityTimestamps:
    """The datetimes for the start and/or end of an activity session."""

    start: typing.Optional[datetime.datetime] = attr.ib(repr=True)
    """When this activity's session was started, if applicable."""

    end: typing.Optional[datetime.datetime] = attr.ib(repr=True)
    """When this activity's session will end, if applicable."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class ActivityParty:
    """Used to represent activity groups of users."""

    id: typing.Optional[str] = attr.ib(eq=True, hash=True, repr=True)
    """The string id of this party instance, if set."""

    current_size: typing.Optional[int] = attr.ib(eq=False, hash=False, repr=False)
    """Current size of this party, if applicable."""

    max_size: typing.Optional[int] = attr.ib(eq=False, hash=False, repr=False)
    """Maximum size of this party, if applicable."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class ActivityAssets:
    """Used to represent possible assets for an activity."""

    large_image: typing.Optional[str] = attr.ib(repr=False)
    """The ID of the asset's large image, if set."""

    large_text: typing.Optional[str] = attr.ib(repr=False)
    """The text that'll appear when hovering over the large image, if set."""

    small_image: typing.Optional[str] = attr.ib(repr=False)
    """The ID of the asset's small image, if set."""

    small_text: typing.Optional[str] = attr.ib(repr=False)
    """The text that'll appear when hovering over the small image, if set."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class ActivitySecret:
    """The secrets used for interacting with an activity party."""

    join: typing.Optional[str] = attr.ib(repr=False)
    """The secret used for joining a party, if applicable."""

    spectate: typing.Optional[str] = attr.ib(repr=False)
    """The secret used for spectating a party, if applicable."""

    match: typing.Optional[str] = attr.ib(repr=False)
    """The secret used for joining a party, if applicable."""


@enum.unique
@typing.final
class ActivityFlag(enum.IntFlag):
    """Flags that describe what an activity includes.

    This can be more than one using bitwise-combinations.
    """

    INSTANCE = 1 << 0
    """Instance"""

    JOIN = 1 << 1
    """Join"""

    SPECTATE = 1 << 2
    """Spectate"""

    JOIN_REQUEST = 1 << 3
    """Join Request"""

    SYNC = 1 << 4
    """Sync"""

    PLAY = 1 << 5
    """Play"""

    def __str__(self) -> str:
        return self.name


# TODO: add strict type checking to gateway for this type in an invariant way.
@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class Activity:
    """An activity that the bot can set for one or more shards.

    !!! note
        Bots cannot currently set custom presence statuses.

    !!! warning
        Other activity types may derive from this one, but only their
        name, url and type will be passed if used in a presence update
        request. Passing a `RichActivity` or similar may cause an
        `INVALID_OPCODE` to be raised which will result in the shard shutting
        down.
    """

    name: str = attr.ib()
    """The activity name."""

    url: typing.Optional[str] = attr.ib(default=None, repr=False)
    """The activity URL. Only valid for `STREAMING` activities."""

    type: ActivityType = attr.ib(converter=ActivityType, default=ActivityType.PLAYING)
    """The activity type."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class RichActivity(Activity):
    """Represents an activity that will be attached to a member's presence.

    !!! warning
        You can NOT use this in presence update requests.
    """

    created_at: datetime.datetime = attr.ib(repr=False)
    """When this activity was added to the user's session."""

    timestamps: typing.Optional[ActivityTimestamps] = attr.ib(repr=False)
    """The timestamps for when this activity's current state will start and
    end, if applicable.
    """

    application_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=False)
    """The ID of the application this activity is for, if applicable."""

    details: typing.Optional[str] = attr.ib(repr=False)
    """The text that describes what the activity's target is doing, if set."""

    state: typing.Optional[str] = attr.ib(repr=False)
    """The current status of this activity's target, if set."""

    emoji: typing.Union[None, emojis_.UnicodeEmoji, emojis_.CustomEmoji] = attr.ib(repr=False)
    """The emoji of this activity, if it is a custom status and set."""

    party: typing.Optional[ActivityParty] = attr.ib(repr=False)
    """Information about the party associated with this activity, if set."""

    assets: typing.Optional[ActivityAssets] = attr.ib(repr=False)
    """Images and their hover over text for the activity."""

    secrets: typing.Optional[ActivitySecret] = attr.ib(repr=False)
    """Secrets for Rich Presence joining and spectating."""

    is_instance: typing.Optional[bool] = attr.ib(repr=False)
    """Whether this activity is an instanced game session."""

    flags: typing.Optional[ActivityFlag] = attr.ib(repr=False)
    """Flags that describe what the activity includes, if present."""


@typing.final
class Status(str, enum.Enum):
    """The status of a member."""

    ONLINE = "online"
    """Online/green."""

    IDLE = "idle"
    """Idle/yellow."""

    DND = "dnd"
    """Do not disturb/red."""

    DO_NOT_DISTURB = DND
    """An alias for `Status.DND`"""

    OFFLINE = "offline"
    """Offline or invisible/grey."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class ClientStatus:
    """The client statuses for this member."""

    desktop: Status = attr.ib(repr=True)
    """The status of the target user's desktop session."""

    mobile: Status = attr.ib(repr=True)
    """The status of the target user's mobile session."""

    web: Status = attr.ib(repr=True)
    """The status of the target user's web session."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class MemberPresence:
    """Used to represent a guild member's presence."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    user: users.PartialUser = attr.ib(eq=True, hash=True, repr=True)
    """The object of the user who this presence is for.

    !!! info
        Only `PresenceUser.id` is guaranteed for this partial object,
        with other attributes only being included when when they are being
        changed in an event.
    """

    role_ids: typing.Optional[typing.Set[snowflake.Snowflake]] = attr.ib(eq=False, hash=False, repr=False)
    """The ids of the user's current roles in the guild this presence belongs to.

    !!! info
        If this is `None` then this information wasn't provided and is unknown.
    """

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=True, hash=True, repr=True)
    """The ID of the guild this presence belongs to.

    This will be `None` when received in an array of members attached to a guild
    object (e.g on Guild Create).
    """

    visible_status: Status = attr.ib(eq=False, hash=False, repr=True)
    """This user's current status being displayed by the client."""

    activities: typing.Sequence[RichActivity] = attr.ib(eq=False, hash=False, repr=False)
    """An array of the user's activities, with the top one will being
    prioritised by the client.
    """

    client_status: ClientStatus = attr.ib(eq=False, hash=False, repr=False)
    """An object of the target user's client statuses."""

    premium_since: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False, repr=False)
    """The datetime of when this member started "boosting" this guild.

    This will be `None` if they aren't boosting.
    """

    nickname: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """This member's nickname, if set."""
