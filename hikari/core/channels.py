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
"""Components and entities that are used to describe both DMs and guild
channels on Discord.
"""

__all__ = [
    "Channel",
    "ChannelType",
    "DMChannel",
    "PartialChannel",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "GroupDMChannel",
]

import enum
import typing

from hikari.core import entities
from hikari.core import snowflakes
from hikari.core import permissions
from hikari.internal_utilities import marshaller


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


@marshaller.attrs(slots=True)
class PartialChannel(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents a channel where we've only received it's basic information,
    commonly received in rest responses.
    """

    #: This channel's name.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str)

    #: This channel's type.
    #:
    #: :type: :obj:`ChannelType`
    type: ChannelType = marshaller.attrib(deserializer=ChannelType)


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
    #: :type: :obj:`permissions.Permission`
    allow: permissions.Permission = marshaller.attrib(deserializer=permissions.Permission)

    #: The permissions this overwrite denies.
    #:
    #: :type: :obj:`permissions.Permission`
    deny: permissions.Permission = marshaller.attrib(deserializer=permissions.Permission)

    @property
    def unset(self) -> permissions.Permission:
        return typing.cast(permissions.Permission, (self.allow | self.deny))


@marshaller.attrs(slots=True)
class Channel(PartialChannel):
    ...


@marshaller.attrs(slots=True)
class DMChannel(Channel):
    ...


@marshaller.attrs(slots=True)
class GroupDMChannel(DMChannel):
    ...
