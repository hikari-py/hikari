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
"""Application and entities that are used to describe both DMs and guild channels on Discord."""

from __future__ import annotations

__all__ = [
    "ChannelType",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "PartialChannel",
    "TextChannel",
    "DMChannel",
    "GroupDMChannel",
    "GuildCategory",
    "GuildChannel",
    "GuildTextChannel",
    "GuildNewsChannel",
    "GuildStoreChannel",
    "GuildVoiceChannel",
]

import abc
import enum
import typing

import attr

from hikari.models import bases
from hikari.models import permissions
from hikari.models import users

from hikari.utilities import cdn

if typing.TYPE_CHECKING:
    import datetime
    from hikari.utilities import snowflake


@enum.unique
class ChannelType(int, enum.Enum):
    """The known channel types that are exposed to us by the API."""

    GUILD_TEXT = 0
    """A text channel in a guild."""

    DM = 1
    """A direct channel between two users."""

    GUILD_VOICE = 2
    """A voice channel in a guild."""

    GROUP_DM = 3
    """A direct channel between multiple users."""

    GUILD_CATEGORY = 4
    """An category used for organizing channels in a guild."""

    GUILD_NEWS = 5
    """A channel that can be followed and can crosspost."""

    GUILD_STORE = 6
    """A channel that show's a game's store page."""


@enum.unique
class PermissionOverwriteType(str, enum.Enum):
    """The type of entity a Permission Overwrite targets."""

    ROLE = "role"
    """A permission overwrite that targets all the members with a specific role."""

    MEMBER = "member"
    """A permission overwrite that targets a specific guild member."""

    def __str__(self) -> str:
        return self.value


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True)
class PermissionOverwrite(bases.Unique):
    """Represents permission overwrites for a channel or role in a channel.

    You may sometimes need to make instances of this object to add/edit
    permission overwrites on channels.

    Example
    -------
    Creating a permission overwrite.

    ```py
    overwrite = PermissionOverwrite(
        type=PermissionOverwriteType.MEMBER,
        allow=(
            Permissions.VIEW_CHANNEL
            | Permissions.READ_MESSAGE_HISTORY
            | Permissions.SEND_MESSAGES
        ),
        deny=(
            Permissions.MANAGE_MESSAGES
            | Permissions.SPEAK
        ),
    )
    ```
    """

    type: PermissionOverwriteType = attr.ib(converter=PermissionOverwriteType, eq=True, hash=True)
    """The type of entity this overwrite targets."""

    allow: permissions.Permission = attr.ib(converter=permissions.Permission, default=0, eq=False, hash=False)
    """The permissions this overwrite allows."""

    deny: permissions.Permission = attr.ib(converter=permissions.Permission, default=0, eq=False, hash=False)
    """The permissions this overwrite denies."""

    @property
    def unset(self) -> permissions.Permission:
        """Bitfield of all permissions not explicitly allowed or denied by this overwrite."""
        return typing.cast(permissions.Permission, (self.allow | self.deny))


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class PartialChannel(bases.Entity, bases.Unique):
    """Channel representation for cases where further detail is not provided.

    This is commonly received in REST API responses where full information is
    not available from Discord.
    """

    name: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """The channel's name. This will be missing for DM channels."""

    type: ChannelType = attr.ib(eq=False, hash=False, repr=True)
    """The channel's type."""


class TextChannel(PartialChannel, abc.ABC):
    """A channel that can have text messages in it."""

    # This is a mixin, do not add slotted fields.
    __slots__ = ()


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class DMChannel(TextChannel):
    """Represents a DM channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    recipients: typing.Mapping[snowflake.Snowflake, users.User] = attr.ib(
        eq=False, hash=False,
    )
    """The recipients of the DM."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GroupDMChannel(DMChannel):
    """Represents a DM group channel."""

    owner_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the owner of the group."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The CDN hash of the icon of the group, if an icon is set."""

    nicknames: typing.MutableMapping[snowflake.Snowflake, str] = attr.ib(eq=False, hash=False)
    """A mapping of set nicknames within this group DMs to user IDs."""

    application_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the application that created the group DM.

    If the group DM was not created by a bot, this will be `None`.
    """

    @property
    def icon_url(self) -> typing.Optional[str]:
        """URL for this DM channel's icon, if set."""
        return self.format_icon_url()

    # noinspection PyShadowingBuiltins
    def format_icon_url(self, *, format: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the URL for this group DM's icon, if set.

        Parameters
        ----------
        format : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        str or None
            The string URL, or `None` if no icon is present.

        Raises
        ------
        ValueError
            If `size` is not a power of two between 16 and 4096 (inclusive).
        """
        if self.icon_hash:
            return cdn.generate_cdn_url("channel-icons", str(self.id), self.icon_hash, format_=format, size=size)
        return None


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildChannel(PartialChannel):
    """The base for anything that is a guild channel."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild the channel belongs to.

    !!! warning
        This will be `None` when received over the gateway in certain events
        (e.g Guild Create).
    """

    position: int = attr.ib(eq=False, hash=False)
    """The sorting position of the channel.

    Higher numbers appear further down the channel list.
    """

    permission_overwrites: typing.Mapping[snowflake.Snowflake, PermissionOverwrite] = attr.ib(eq=False, hash=False)
    """The permission overwrites for the channel.

    This maps the ID of the entity in the overwrite to the overwrite data.
    """

    is_nsfw: typing.Optional[bool] = attr.ib(eq=False, hash=False)
    """Whether the channel is marked as NSFW.

    !!! warning
        This will be `None` when received over the gateway in certain events
        (e.g Guild Create).
    """

    parent_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the parent category the channel belongs to.

    If no parent category is set for the channel, this will be `None`.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildCategory(GuildChannel):
    """Represents a guild category channel.

    These can contain other channels inside, and act as a method for
    organisation.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildTextChannel(GuildChannel, TextChannel):
    """Represents a guild text channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    rate_limit_per_user: datetime.timedelta = attr.ib(eq=False, hash=False)
    """The delay (in seconds) between a user can send a message to this channel.

    !!! note
        Any user that has permissions allowing `MANAGE_MESSAGES`,
        `MANAGE_CHANNEL`, `ADMINISTRATOR` will not be limited. Likewise, bots
        will not be affected by this rate limit.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be `None` in several cases; Discord does not document what
        these cases are. Trust no one!
    """


@attr.s(eq=True, hash=True, init=False, slots=True, kw_only=True)
class GuildNewsChannel(GuildChannel, TextChannel):
    """Represents an news channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be `None` in several cases; Discord does not document what
        these cases are. Trust no one!
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildStoreChannel(GuildChannel):
    """Represents a store channel.

    These were originally used to sell games when Discord had a game store. This
    was scrapped at the end of 2019, so these may disappear from the platform
    eventually.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildVoiceChannel(GuildChannel):
    """Represents an voice channel."""

    bitrate: int = attr.ib(eq=False, hash=False, repr=True)
    """The bitrate for the voice channel (in bits per second)."""

    user_limit: int = attr.ib(eq=False, hash=False, repr=True)
    """The user limit for the voice channel.

    If this is `0`, then assume no limit.
    """
