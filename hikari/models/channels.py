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

import enum
import typing

import attr

from hikari.models import bases
from hikari.models import permissions
from hikari.net import urls

if typing.TYPE_CHECKING:
    import datetime

    from hikari.models import users
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
    """Represents permission overwrites for a channel or role in a channel."""

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


class TextChannel:
    # This is a mixin, do not add slotted fields.
    __slots__ = ()


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class PartialChannel(bases.Entity, bases.Unique):
    """Represents a channel where we've only received it's basic information.

    This is commonly received in RESTSession responses.
    """

    name: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """The channel's name. This will be missing for DM channels."""

    type: ChannelType = attr.ib(eq=False, hash=False, repr=True)
    """The channel's type."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class DMChannel(PartialChannel, TextChannel):
    """Represents a DM channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the last message sent in this channel.

    !!! note
        This might point to an invalid or deleted message.
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
    """The hash of the icon of the group."""

    application_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the application that created the group DM, if it's a bot based group DM."""

    @property
    def icon_url(self) -> typing.Optional[str]:
        """URL for this DM channel's icon, if set."""
        return self.format_icon_url()

    def format_icon_url(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the URL for this group DM's icon, if set.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        str | None
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash:
            return urls.generate_cdn_url("channel-icons", str(self.id), self.icon_hash, format_=format_, size=size)
        return None


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildChannel(PartialChannel):
    """The base for anything that is a guild channel."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild the channel belongs to.

    This will be `None` when received over the gateway in certain events (e.g.
    Guild Create).
    """

    position: int = attr.ib(eq=False, hash=False)
    """The sorting position of the channel."""

    permission_overwrites: typing.Mapping[snowflake.Snowflake, PermissionOverwrite] = attr.ib(eq=False, hash=False)
    """The permission overwrites for the channel."""

    is_nsfw: typing.Optional[bool] = attr.ib(eq=False, hash=False)
    """Whether the channel is marked as NSFW.

    This will be `None` when received over the gateway in certain events (e.g
    Guild Create).
    """

    parent_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the parent category the channel belongs to."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildCategory(GuildChannel):
    """Represents a guild category."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildTextChannel(GuildChannel, TextChannel):
    """Represents a guild text channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the last message sent in this channel.

    !!! note
        This might point to an invalid or deleted message.
    """

    rate_limit_per_user: datetime.timedelta = attr.ib(eq=False, hash=False)
    """The delay (in seconds) between a user can send a message to this channel.

    !!! note
        Bots, as well as users with `MANAGE_MESSAGES` or `MANAGE_CHANNEL`,
        are not affected by this.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False)
    """The timestamp of the last-pinned message.

    This may be `None` in several cases (currently undocumented clearly by
    Discord).
    """


@attr.s(eq=True, hash=True, init=False, slots=True, kw_only=True)
class GuildNewsChannel(GuildChannel, TextChannel):
    """Represents an news channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the last message sent in this channel.

    !!! note
        This might point to an invalid or deleted message.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False)
    """The timestamp of the last-pinned message.

    This may be `None` in several cases (currently undocumented clearly by
    Discord).
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildStoreChannel(GuildChannel):
    """Represents a store channel."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildVoiceChannel(GuildChannel):
    """Represents an voice channel."""

    bitrate: int = attr.ib(eq=False, hash=False, repr=True)
    """The bitrate for the voice channel (in bits)."""

    user_limit: int = attr.ib(eq=False, hash=False, repr=True)
    """The user limit for the voice channel."""
