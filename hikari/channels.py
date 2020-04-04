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
"""Components and entities that are used to describe both DMs and guild channels on Discord.

.. inheritance-diagram::
    hikari.channels
    enum.IntEnum
    hikari.entities.HikariEntity
    hikari.entities.Deserializable
    hikari.entities.Serializable
    hikari.snowflakes.UniqueEntity
    :parts: 1
"""

__all__ = [
    "Channel",
    "ChannelType",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "PartialChannel",
    "DMChannel",
    "GroupDMChannel",
    "GuildCategory",
    "GuildTextChannel",
    "GuildNewsChannel",
    "GuildStoreChannel",
    "GuildVoiceChannel",
]

import datetime
import enum
import typing

from hikari.internal import marshaller
from hikari import entities
from hikari import permissions
from hikari import users
from hikari import snowflakes


@enum.unique
class ChannelType(enum.IntEnum):
    """The known channel types that are exposed to us by the api."""

    #: A text channel in a guild.
    GUILD_TEXT = 0
    #: A direct channel between two users.
    DM = 1
    #: A voice channel in a guild.
    GUILD_VOICE = 2
    #: A direct channel between multiple users.
    GROUP_DM = 3
    #: An category used for organizing channels in a guild.
    GUILD_CATEGORY = 4
    #: A channel that can be followed and can crosspost.
    GUILD_NEWS = 5
    #: A channel that show's a game's store page.
    GUILD_STORE = 6


@enum.unique
class PermissionOverwriteType(str, enum.Enum):
    """The type of entity a Permission Overwrite targets."""

    #: A permission overwrite that targets all the members with a specific
    #: guild role.
    ROLE = "role"
    #: A permission overwrite that targets a specific guild member.
    MEMBER = "member"


@marshaller.attrs(slots=True)
class PermissionOverwrite(snowflakes.UniqueEntity, entities.Deserializable, entities.Serializable):
    """Represents permission overwrites for a channel or role in a channel."""

    #: The type of entity this overwrite targets.
    #:
    #: :type: :obj:`PermissionOverwriteType`
    type: PermissionOverwriteType = marshaller.attrib(deserializer=PermissionOverwriteType)

    #: The permissions this overwrite allows.
    #:
    #: :type: :obj:`hikari.permissions.Permission`
    allow: permissions.Permission = marshaller.attrib(deserializer=permissions.Permission)

    #: The permissions this overwrite denies.
    #:
    #: :type: :obj:`hikari.permissions.Permission`
    deny: permissions.Permission = marshaller.attrib(deserializer=permissions.Permission)

    @property
    def unset(self) -> permissions.Permission:
        """Bitfield of all permissions not explicitly allowed or denied by this overwrite."""
        return typing.cast(permissions.Permission, (self.allow | self.deny))


def register_channel_type(type_: ChannelType) -> typing.Callable[[typing.Type["Channel"]], typing.Type["Channel"]]:
    """Generate a decorator for channel classes defined in this library.

    This allows them to associate themselves with a given channel type.

    Parameters
    ----------
    type_ : :obj:`ChannelType`
        The channel type to associate with.

    Returns
    -------
    ``decorator``
        The decorator to decorate the class with.
    """

    def decorator(cls):
        mapping = getattr(register_channel_type, "types", {})
        mapping[type_] = cls
        setattr(register_channel_type, "types", mapping)
        return cls

    return decorator


@marshaller.attrs(slots=True)
class Channel(snowflakes.UniqueEntity, entities.Deserializable):
    """Base class for all channels."""

    #: The channel's type.
    #:
    #: :type: :obj:`ChannelType`
    type: ChannelType = marshaller.attrib(deserializer=ChannelType)


@marshaller.attrs(slots=True)
class PartialChannel(Channel):
    """Represents a channel where we've only received it's basic information.

    This is commonly received in REST responses.
    """

    #: The channel's name.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str)


@register_channel_type(ChannelType.DM)
@marshaller.attrs(slots=True)
class DMChannel(Channel):
    """Represents a DM channel."""

    #: The ID of the last message sent in this channel.
    #:
    #: Note
    #: ----
    #: This might point to an invalid or deleted message.
    #:
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    last_message_id: snowflakes.Snowflake = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_none=None
    )

    #: The recipients of the DM.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`hikari.users.User` ]
    recipients: typing.Mapping[snowflakes.Snowflake, users.User] = marshaller.attrib(
        deserializer=lambda recipients: {user.id: user for user in map(users.User.deserialize, recipients)}
    )


@register_channel_type(ChannelType.GROUP_DM)
@marshaller.attrs(slots=True)
class GroupDMChannel(DMChannel):
    """Represents a DM group channel."""

    #: The group's name.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str)

    #: The ID of the owner of the group.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    owner_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The hash of the icon of the group.
    #:
    #: :type: :obj:`str`, optional
    icon_hash: typing.Optional[str] = marshaller.attrib(raw_name="icon", deserializer=str, if_none=None)

    #: The ID of the application that created the group DM, if it's a
    #: bot based group DM.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    application_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_undefined=None
    )


@marshaller.attrs(slots=True)
class GuildChannel(Channel):
    """The base for anything that is a guild channel."""

    #: The ID of the guild the channel belongs to.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    guild_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The sorting position of the channel.
    #:
    #: :type: :obj:`int`
    position: int = marshaller.attrib(deserializer=int)

    #: The permission overwrites for the channel.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`PermissionOverwrite` ]
    permission_overwrites: PermissionOverwrite = marshaller.attrib(
        deserializer=lambda overwrites: {o.id: o for o in map(PermissionOverwrite.deserialize, overwrites)}
    )

    #: The name of the channel.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str)

    #: Wheter the channel is marked as NSFW.
    #:
    #: :type: :obj:`bool`
    is_nsfw: bool = marshaller.attrib(raw_name="nsfw", deserializer=bool)

    #: The ID of the parent category the channel belongs to.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    parent_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize, if_none=None)


@register_channel_type(ChannelType.GUILD_CATEGORY)
@marshaller.attrs(slots=True)
class GuildCategory(GuildChannel):
    """Represents a guild category."""


@register_channel_type(ChannelType.GUILD_TEXT)
@marshaller.attrs(slots=True)
class GuildTextChannel(GuildChannel):
    """Represents a guild text channel."""

    #: The topic of the channel.
    #:
    #: :type: :obj:`str`, optional
    topic: str = marshaller.attrib(deserializer=str, if_none=None)

    #: The ID of the last message sent in this channel.
    #:
    #: Note
    #: ----
    #: This might point to an invalid or deleted message.
    #:
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    last_message_id: snowflakes.Snowflake = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_none=None
    )

    #: The delay (in seconds) between a user can send a message
    #: to this channel.
    #:
    #: Note
    #: ----
    #: Bots, as well as users with ``MANAGE_MESSAGES`` or
    #: ``MANAGE_CHANNEL``, are not afected by this.
    #:
    #: :type: :obj:`datetime.timedelta`
    rate_limit_per_user: datetime.timedelta = marshaller.attrib(
        deserializer=lambda payload: datetime.timedelta(seconds=payload)
    )


@register_channel_type(ChannelType.GUILD_NEWS)
@marshaller.attrs(slots=True)
class GuildNewsChannel(GuildChannel):
    """Represents an news channel."""

    #: The topic of the channel.
    #:
    #: :type: :obj:`str`, optional
    topic: str = marshaller.attrib(deserializer=str, if_none=None)

    #: The ID of the last message sent in this channel.
    #:
    #: Note
    #: ----
    #: This might point to an invalid or deleted message.
    #:
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    last_message_id: snowflakes.Snowflake = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_none=None
    )


@register_channel_type(ChannelType.GUILD_STORE)
@marshaller.attrs(slots=True)
class GuildStoreChannel(GuildChannel):
    """Represents a store channel."""


@register_channel_type(ChannelType.GUILD_VOICE)
@marshaller.attrs(slots=True)
class GuildVoiceChannel(GuildChannel):
    """Represents an voice channel."""

    #: The bitrate for the voice channel (in bits).
    #:
    #: :type: :obj:`int`
    bitrate: int = marshaller.attrib(deserializer=int)

    #: The user limit for the voice channel.
    #:
    #: :type: :obj:`int`
    user_limit: int = marshaller.attrib(deserializer=int)


def deserialize_channel(payload: typing.Dict[str, typing.Any]) -> typing.Union[GuildChannel, DMChannel]:
    """Deserialize a channel object into the corresponding class.

    Warning
    -------
    This can only be used to deserialize full channel objects. To deserialize a
    partial object, use ``PartialChannel.deserialize()``.
    """
    type_id = payload["type"]
    channel_type = register_channel_type.types[type_id]
    return channel_type.deserialize(payload)
