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
"""Components and entities that are used to describe voice states on Discord."""
__all__ = ["VoiceRegion", "VoiceState"]

import typing

from hikari.internal import marshaller
from hikari import entities
from hikari import guilds
from hikari import snowflakes


@marshaller.attrs(slots=True)
class VoiceState(entities.HikariEntity, entities.Deserializable):
    """Represents a user's voice connection status."""

    #: The ID of the guild this voice state is in, if applicable.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    guild_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_undefined=None
    )

    #: The ID of the channel this user is connected to.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    channel_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize, if_none=None)

    #: The ID of the user this voice state is for.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    user_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The guild member this voice state is for if the voice state is in a
    #: guild.
    #:
    #: :type: :obj:`hikari.guilds.GuildMember`, optional
    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None
    )

    #: The ID of this voice state's session.
    #:
    #: :type: :obj:`str`
    session_id: str = marshaller.attrib(deserializer=str)

    #: Whether this user is deafened by the guild.
    #:
    #: :type: :obj:`bool`
    is_guild_deafened: bool = marshaller.attrib(raw_name="deaf", deserializer=bool)

    #: Whether this user is muted by the guild.
    #:
    #: :type: :obj:`bool`
    is_guild_muted: bool = marshaller.attrib(raw_name="mute", deserializer=bool)

    #: Whether this user is deafened by their client.
    #:
    #: :type: :obj:`bool`
    is_self_deafened: bool = marshaller.attrib(raw_name="self_deaf", deserializer=bool)

    #: Whether this user is muted by their client.
    #:
    #: :type: :obj:`bool`
    is_self_muted: bool = marshaller.attrib(raw_name="self_mute", deserializer=bool)

    #: Whether this user is streaming using "Go Live".
    #:
    #: :type: :obj:`bool`
    is_streaming: bool = marshaller.attrib(raw_name="self_stream", deserializer=bool, if_undefined=False)

    #: Whether this user is muted by the current user.
    #:
    #: :type: :obj:`bool`
    is_suppressed: bool = marshaller.attrib(raw_name="suppress", deserializer=bool)


@marshaller.attrs(slots=True)
class VoiceRegion(entities.HikariEntity, entities.Deserializable):
    """Represent's a voice region server."""

    #: The ID of this region
    #:
    #: :type: :obj:`str`
    id: str = marshaller.attrib(deserializer=str)

    #: The name of this region
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str)

    #: Whether this region is vip-only.
    #:
    #: :type: :obj:`bool`
    is_vip: bool = marshaller.attrib(raw_name="vip", deserializer=bool)

    #: Whether this region's server is closest to the current user's client.
    #:
    #: :type: :obj:`bool`
    is_optimal_location: bool = marshaller.attrib(raw_name="optimal", deserializer=bool)

    #: Whether this region is deprecated.
    #:
    #: :type: :obj:`bool`
    is_deprecated: bool = marshaller.attrib(raw_name="deprecated", deserializer=bool)

    #: Whether this region is custom (e.g. used for events).
    #:
    #: :type: :obj:`bool`
    is_custom: bool = marshaller.attrib(raw_name="custom", deserializer=bool)
