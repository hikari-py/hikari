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
"""Application and entities that are used to describe voice states on Discord."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["VoiceRegion", "VoiceState"]

import typing

import attr

if typing.TYPE_CHECKING:
    from hikari.api import rest
    from hikari.models import guilds
    from hikari.utilities import snowflake


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class VoiceState:
    """Represents a user's voice connection status."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild this voice state is in, if applicable."""

    channel_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the channel this user is connected to.

    This will be `None` if they are leaving voice.
    """

    user_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the user this voice state is for."""

    member: typing.Optional[guilds.Member] = attr.ib(eq=False, hash=False, repr=False)
    """The guild member this voice state is for if the voice state is in a guild."""

    session_id: str = attr.ib(eq=True, hash=True, repr=True)
    """The string ID of this voice state's session."""

    is_guild_deafened: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is deafened by the guild."""

    is_guild_muted: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is muted by the guild."""

    is_self_deafened: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is deafened by their client."""

    is_self_muted: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is muted by their client."""

    is_streaming: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is streaming using "Go Live"."""

    is_video_enabled: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user's camera is enabled."""

    is_suppressed: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is muted by the current user."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class VoiceRegion:
    """Represents a voice region server."""

    id: str = attr.ib(eq=True, hash=True, repr=True)
    """The string ID of this region.

    !!! note
        Unlike most parts of this API, this ID will always be a string type.
        This is intentional.
    """

    name: str = attr.ib(eq=False, hash=False, repr=True)
    """The name of this region."""

    is_vip: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this region is vip-only."""

    is_optimal_location: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this region's server is closest to the current user's client."""

    is_deprecated: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this region is deprecated."""

    is_custom: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether this region is custom (e.g. used for events)."""

    def __str__(self) -> str:
        return self.id
