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

from __future__ import annotations

__all__ = ["VoiceRegion", "VoiceState"]

import typing

import attr

from hikari import bases
from hikari import guilds
from hikari.internal import marshaller


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class VoiceState(bases.Entity, marshaller.Deserializable):
    """Represents a user's voice connection status."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_undefined=None, default=None, eq=False, hash=False, repr=True
    )
    """The ID of the guild this voice state is in, if applicable."""

    channel_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_none=None, eq=False, hash=False, repr=True
    )
    """The ID of the channel this user is connected to.

    This will be `None` if they are leaving voice.
    """

    user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, eq=False, hash=False, repr=True)
    """The ID of the user this voice state is for."""

    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None, default=None, eq=False, hash=False,
    )
    """The guild member this voice state is for if the voice state is in a guild."""

    session_id: str = marshaller.attrib(deserializer=str, eq=True, hash=True, repr=True)
    """The string ID of this voice state's session."""

    is_guild_deafened: bool = marshaller.attrib(raw_name="deaf", deserializer=bool, eq=False, hash=False)
    """Whether this user is deafened by the guild."""

    is_guild_muted: bool = marshaller.attrib(raw_name="mute", deserializer=bool, eq=False, hash=False)
    """Whether this user is muted by the guild."""

    is_self_deafened: bool = marshaller.attrib(raw_name="self_deaf", deserializer=bool, eq=False, hash=False)
    """Whether this user is deafened by their client."""

    is_self_muted: bool = marshaller.attrib(raw_name="self_mute", deserializer=bool, eq=False, hash=False)
    """Whether this user is muted by their client."""

    is_streaming: bool = marshaller.attrib(
        raw_name="self_stream", deserializer=bool, if_undefined=False, default=False, eq=False, hash=False
    )
    """Whether this user is streaming using "Go Live"."""

    is_suppressed: bool = marshaller.attrib(raw_name="suppress", deserializer=bool, eq=False, hash=False)
    """Whether this user is muted by the current user."""


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class VoiceRegion(bases.Entity, marshaller.Deserializable):
    """Represents a voice region server."""

    id: str = marshaller.attrib(deserializer=str, eq=True, hash=True, repr=True)
    """The string ID of this region.

    !!! note
        Unlike most parts of this API, this ID will always be a string type.
        This is intentional.
    """

    name: str = marshaller.attrib(deserializer=str, eq=False, hash=False, repr=True)
    """The name of this region."""

    is_vip: bool = marshaller.attrib(raw_name="vip", deserializer=bool, eq=False, hash=False)
    """Whether this region is vip-only."""

    is_optimal_location: bool = marshaller.attrib(raw_name="optimal", deserializer=bool, eq=False, hash=False)
    """Whether this region's server is closest to the current user's client."""

    is_deprecated: bool = marshaller.attrib(raw_name="deprecated", deserializer=bool, eq=False, hash=False)
    """Whether this region is deprecated."""

    is_custom: bool = marshaller.attrib(raw_name="custom", deserializer=bool, eq=False, hash=False)
    """Whether this region is custom (e.g. used for events)."""
