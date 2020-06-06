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
"""Application and entities that are used to describe guilds on Discord."""

from __future__ import annotations

__all__ = [
    "OwnActivity",
    "ActivityAssets",
    "ActivityFlag",
    "ActivitySecret",
    "ActivityTimestamps",
    "ActivityType",
    "ActivityParty",
    "ClientStatus",
    "MemberPresence",
    "RichActivity",
    "PresenceStatus",
    "PresenceUser",
]

import enum
import typing

import attr

from hikari.models import bases
from hikari.models import users
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari.models import emojis as emojis_
    from hikari.utilities import snowflake


@enum.unique
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

    current_size: typing.Optional[int] = attr.ib(eq=False, hash=False)
    """Current size of this party, if applicable."""

    max_size: typing.Optional[int] = attr.ib(eq=False, hash=False)
    """Maximum size of this party, if applicable."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class ActivityAssets:
    """Used to represent possible assets for an activity."""

    large_image: typing.Optional[str] = attr.ib()
    """The ID of the asset's large image, if set."""

    large_text: typing.Optional[str] = attr.ib()
    """The text that'll appear when hovering over the large image, if set."""

    small_image: typing.Optional[str] = attr.ib()
    """The ID of the asset's small image, if set."""

    small_text: typing.Optional[str] = attr.ib()
    """The text that'll appear when hovering over the small image, if set."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class ActivitySecret:
    """The secrets used for interacting with an activity party."""

    join: typing.Optional[str] = attr.ib()
    """The secret used for joining a party, if applicable."""

    spectate: typing.Optional[str] = attr.ib()
    """The secret used for spectating a party, if applicable."""

    match: typing.Optional[str] = attr.ib()
    """The secret used for joining a party, if applicable."""


@enum.unique
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


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class RichActivity:
    """Represents an activity that will be attached to a member's presence."""

    name: str = attr.ib(repr=True)
    """The activity's name."""

    type: ActivityType = attr.ib(repr=True)
    """The activity's type."""

    url: typing.Optional[str] = attr.ib()
    """The URL for a `STREAM` type activity, if applicable."""

    created_at: datetime.datetime = attr.ib()
    """When this activity was added to the user's session."""

    timestamps: typing.Optional[ActivityTimestamps] = attr.ib()
    """The timestamps for when this activity's current state will start and
    end, if applicable.
    """

    application_id: typing.Optional[snowflake.Snowflake] = attr.ib()
    """The ID of the application this activity is for, if applicable."""

    details: typing.Optional[str] = attr.ib()
    """The text that describes what the activity's target is doing, if set."""

    state: typing.Optional[str] = attr.ib()
    """The current status of this activity's target, if set."""

    emoji: typing.Union[None, emojis_.UnicodeEmoji, emojis_.CustomEmoji] = attr.ib()
    """The emoji of this activity, if it is a custom status and set."""

    party: typing.Optional[ActivityParty] = attr.ib()
    """Information about the party associated with this activity, if set."""

    assets: typing.Optional[ActivityAssets] = attr.ib()
    """Images and their hover over text for the activity."""

    secrets: typing.Optional[ActivitySecret] = attr.ib()
    """Secrets for Rich Presence joining and spectating."""

    is_instance: typing.Optional[bool] = attr.ib()
    """Whether this activity is an instanced game session."""

    flags: ActivityFlag = attr.ib()
    """Flags that describe what the activity includes."""


class PresenceStatus(str, enum.Enum):
    """The status of a member."""

    ONLINE = "online"
    """Online/green."""

    IDLE = "idle"
    """Idle/yellow."""

    DND = "dnd"
    """Do not disturb/red."""

    DO_NOT_DISTURB = DND
    """An alias for `PresenceStatus.DND`"""

    OFFLINE = "offline"
    """Offline or invisible/grey."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class ClientStatus:
    """The client statuses for this member."""

    desktop: PresenceStatus = attr.ib(repr=True)
    """The status of the target user's desktop session."""

    mobile: PresenceStatus = attr.ib(repr=True)
    """The status of the target user's mobile session."""

    web: PresenceStatus = attr.ib(repr=True)
    """The status of the target user's web session."""


# TODO: should this be an event instead?
@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class PresenceUser(users.User):
    """A user representation specifically used for presence updates.

    !!! warning
        Every attribute except `PresenceUser.id` may be as
        `hikari.utilities.undefined.Undefined` unless it is specifically being modified
        for this update.
    """

    discriminator: typing.Union[str, undefined.Undefined] = attr.ib(eq=False, hash=False, repr=True)
    """This user's discriminator."""

    username: typing.Union[str, undefined.Undefined] = attr.ib(eq=False, hash=False, repr=True)
    """This user's username."""

    avatar_hash: typing.Union[None, str, undefined.Undefined] = attr.ib(
        eq=False, hash=False, repr=True,
    )
    """This user's avatar hash, if set."""

    is_bot: typing.Union[bool, undefined.Undefined] = attr.ib(
        eq=False, hash=False, repr=True,
    )
    """Whether this user is a bot account."""

    is_system: typing.Union[bool, undefined.Undefined] = attr.ib(
        eq=False, hash=False,
    )
    """Whether this user is a system account."""

    flags: typing.Union[users.UserFlag, undefined.Undefined] = attr.ib(eq=False, hash=False)
    """The public flags for this user."""

    @property
    def avatar_url(self) -> typing.Union[str, undefined.Undefined]:
        """URL for this user's avatar if the relevant info is available.

        !!! note
            This will be `hikari.models.undefined.Undefined` if both `PresenceUser.avatar_hash`
            and `PresenceUser.discriminator` are `hikari.models.undefined.Undefined`.
        """
        return self.format_avatar_url()

    def format_avatar_url(
        self, *, format_: typing.Optional[str] = None, size: int = 4096
    ) -> typing.Union[str, undefined.Undefined]:
        """Generate the avatar URL for this user's avatar if available.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png` or `gif`.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when animated).
            Will be ignored for default avatars which can only be `png`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        hikari.models.undefined.Undefined or str
            The string URL of the user's custom avatar if
            either `PresenceUser.avatar_hash` is set or their default avatar if
            `PresenceUser.discriminator` is set, else `hikari.models.undefined.Undefined`.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.discriminator is not undefined.Undefined() or self.avatar_hash is not undefined.Undefined():
            return super().format_avatar_url(format_=format_, size=size)
        return undefined.Undefined()

    @property
    def default_avatar_index(self) -> typing.Union[int, undefined.Undefined]:
        """Integer representation of this user's default avatar.

        !!! note
            This will be `hikari.models.undefined.Undefined` if `PresenceUser.discriminator` is
            `hikari.models.undefined.Undefined`.
        """
        if self.discriminator is not undefined.Undefined():
            return super().default_avatar_index
        return undefined.Undefined()

    @property
    def default_avatar_url(self) -> typing.Union[str, undefined.Undefined]:
        """URL for this user's default avatar.

        !!! note
            This will be `hikari.models.undefined.Undefined` if `PresenceUser.discriminator` is
            `hikari.models.undefined.Undefined`.
        """
        if self.discriminator is not undefined.Undefined():
            return super().default_avatar_url
        return undefined.Undefined()


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class MemberPresence(bases.Entity):
    """Used to represent a guild member's presence."""

    user: PresenceUser = attr.ib(eq=True, hash=True, repr=True)
    """The object of the user who this presence is for.

    !!! info
        Only `PresenceUser.id` is guaranteed for this partial object,
        with other attributes only being included when when they are being
        changed in an event.
    """

    role_ids: typing.Optional[typing.Sequence[snowflake.Snowflake]] = attr.ib(
        eq=False, hash=False,
    )
    """The ids of the user's current roles in the guild this presence belongs to.

    !!! info
        If this is `None` then this information wasn't provided and is unknown.
    """

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=True, hash=True, repr=True)
    """The ID of the guild this presence belongs to.

    This will be `None` when received in an array of members attached to a guild
    object (e.g on Guild Create).
    """

    visible_status: PresenceStatus = attr.ib(eq=False, hash=False, repr=True)
    """This user's current status being displayed by the client."""

    activities: typing.Sequence[RichActivity] = attr.ib(eq=False, hash=False)
    """An array of the user's activities, with the top one will being
    prioritised by the client.
    """

    client_status: ClientStatus = attr.ib(
        eq=False, hash=False,
    )
    """An object of the target user's client statuses."""

    premium_since: typing.Optional[datetime.datetime] = attr.ib(
        eq=False, hash=False,
    )
    """The datetime of when this member started "boosting" this guild.

    This will be `None` if they aren't boosting.
    """

    nickname: typing.Optional[str] = attr.ib(
        eq=False, hash=False, repr=True,
    )
    """This member's nickname, if set."""


@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class OwnActivity:
    """An activity that the bot can set for one or more shards.

    This will show the activity as the bot's presence.
    """

    name: str = attr.ib()
    """The activity name."""

    url: typing.Optional[str] = attr.ib(default=None)
    """The activity URL. Only valid for `STREAMING` activities."""

    type: ActivityType = attr.ib(converter=ActivityType)
    """The activity type."""
