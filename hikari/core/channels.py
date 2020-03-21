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
__all__ = ["Channel", "ChannelType", "DMChannel", "PartialChannel", "GroupDMChannel"]

import enum

from hikari.core import entities
from hikari.core import snowflakes
from hikari.internal_utilities import marshaller


@enum.unique
class ChannelType(enum.IntEnum):
    """The known channel types that are exposed to us by the api."""

    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_NEWS = 5
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


@marshaller.attrs(slots=True)
class Channel(PartialChannel):
    ...


@marshaller.attrs(slots=True)
class DMChannel(Channel):
    ...


@marshaller.attrs(slots=True)
class GroupDMChannel(DMChannel):
    ...
